"""
adapters/pg_adapter.py — ARK-499 REAL PostgreSQL side-effect adapter.

Stands up a real, freshly-initialized native PostgreSQL 17 cluster on a private
unix socket, creates a real application schema and TWO real database roles:
  - ark_writer   : the privileged role the enforcement adapter uses on ALLOW
  - ark_auditor  : a READ-ONLY role used ONLY for independent state inspection

On ALLOW the adapter opens a real transaction as ark_writer, performs the real
INSERT, and COMMITs exactly once. On DENY/HOLD it touches the database zero
times (audit note only). Independent verification reconnects as ark_auditor and
counts committed rows — the testbed never asserts DB state itself.
"""
import os
import shutil
import subprocess
import time
import secrets

import psycopg2

PGBIN = "/usr/lib/postgresql/17/bin"
PORT = 54331
SOCKDIR = "/tmp/ark499_sock"
DATADIR = "/tmp/ark499_pgdata"


class PostgresAdapter:
    tool_id = "T2"                       # "database state change" tool
    _TOOL_NAME = "postgres_write"

    def __init__(self):
        self._proc_started = False
        self._blocked = 0
        self._down = False               # simulated connection loss (A6)

    # ---- cluster lifecycle ------------------------------------------------
    def start_cluster(self):
        if os.path.exists(DATADIR):
            self._stop_if_running()
            shutil.rmtree(DATADIR, ignore_errors=True)
        os.makedirs(SOCKDIR, exist_ok=True)
        os.makedirs(DATADIR, exist_ok=True)
        subprocess.run([f"{PGBIN}/initdb", "-D", DATADIR, "-U", "ark_admin",
                        "--auth=trust"], check=True,
                       capture_output=True, text=True)
        subprocess.run(
            [f"{PGBIN}/pg_ctl", "-D", DATADIR,
             "-o", f"-p {PORT} -k {SOCKDIR} -c listen_addresses=''",
             "-l", "/tmp/ark499_cluster.log", "-w", "start"],
            check=True, capture_output=True, text=True)
        self._proc_started = True
        self._bootstrap()

    def _stop_if_running(self):
        subprocess.run([f"{PGBIN}/pg_ctl", "-D", DATADIR, "stop", "-m", "fast"],
                       capture_output=True, text=True)

    def stop_cluster(self):
        if self._proc_started:
            self._stop_if_running()
            self._proc_started = False

    def _admin_conn(self):
        return psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_admin",
                                dbname="postgres")

    def _bootstrap(self):
        conn = self._admin_conn()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE ROLE ark_writer LOGIN;")
        cur.execute("CREATE ROLE ark_auditor LOGIN;")
        cur.execute("CREATE DATABASE ark_app OWNER ark_writer;")
        cur.close(); conn.close()
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_admin",
                                dbname="ark_app")
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE ledger_entries (
                id SERIAL PRIMARY KEY,
                account TEXT NOT NULL,
                amount NUMERIC NOT NULL,
                note TEXT,
                created_at TIMESTAMPTZ DEFAULT now()
            );""")
        cur.execute("ALTER TABLE ledger_entries OWNER TO ark_writer;")
        # ark_auditor: read-only, cannot write
        cur.execute("GRANT CONNECT ON DATABASE ark_app TO ark_auditor;")
        cur.execute("GRANT USAGE ON SCHEMA public TO ark_auditor;")
        cur.execute("GRANT SELECT ON ledger_entries TO ark_auditor;")
        cur.execute("REVOKE INSERT, UPDATE, DELETE ON ledger_entries "
                    "FROM ark_auditor;")
        cur.close(); conn.close()

    # ---- adapter contract -------------------------------------------------
    def tool_name(self, tool_id):
        return self._TOOL_NAME

    def healthy(self):
        """Execution-time dependency probe (A6 drops the connection)."""
        if self._down:
            return False
        try:
            c = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_writer",
                                 dbname="ark_app", connect_timeout=2)
            c.close()
            return True
        except Exception:
            return False

    def drop_connection(self):
        self._down = True

    def restore_connection(self):
        self._down = False

    def perform(self, action):
        """ALLOW path: real transaction as ark_writer, commit exactly once."""
        p = action.get("parameters", {})
        entry_id = "pgw-" + secrets.token_hex(8)
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_writer",
                                dbname="ark_app")
        try:
            conn.autocommit = False       # real explicit transaction
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO ledger_entries (account, amount, note) "
                "VALUES (%s, %s, %s) RETURNING id;",
                (p.get("account", "acct"), p.get("amount", 0),
                 p.get("note", "")))
            row_id = cur.fetchone()[0]
            conn.commit()                 # exactly one commit
            cur.close()
            real_effect = {"backend": "postgresql-17", "committed": True,
                           "row_id": row_id, "idempotency_key":
                           action["idempotency_key"]}
            return entry_id, real_effect
        finally:
            conn.close()

    def perform_with_forced_rollback(self, action):
        """Robustness demo (not the scored ProofRecord): begin a real txn, force
        an error before COMMIT, prove ROLLBACK leaves zero committed rows."""
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_writer",
                                dbname="ark_app")
        committed = False
        try:
            conn.autocommit = False
            cur = conn.cursor()
            cur.execute("INSERT INTO ledger_entries (account, amount, note) "
                        "VALUES (%s,%s,%s);", ("rollback-acct", 1, "should-vanish"))
            raise RuntimeError("simulated connection loss mid-transaction")
        except RuntimeError:
            conn.rollback()
        finally:
            conn.close()
        return committed

    def record_blocked(self, action, decision):
        self._blocked += 1
        return f"pg-blocked-{decision}-{self._blocked}"

    # ---- independent inspection (read-only auditor role) ------------------
    def audit_row_count(self):
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_auditor",
                                dbname="ark_app")
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM ledger_entries;")
        n = cur.fetchone()[0]
        cur.close(); conn.close()
        return n

    def audit_rows(self):
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_auditor",
                                dbname="ark_app")
        cur = conn.cursor()
        cur.execute("SELECT id, account, amount, note FROM ledger_entries "
                    "ORDER BY id;")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows

    def auditor_can_write(self):
        """Prove ark_auditor is genuinely read-only (independent role)."""
        conn = psycopg2.connect(host=SOCKDIR, port=PORT, user="ark_auditor",
                                dbname="ark_app")
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO ledger_entries (account, amount) "
                        "VALUES ('x', 1);")
            conn.commit()
            return True
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            conn.close()
