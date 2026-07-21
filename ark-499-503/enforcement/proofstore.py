"""
enforcement/proofstore.py — Hash-chained ProofRecord store.

Writes both the append-only chain (proofrecords/proofrecord_chain.jsonl) and one
individual JSON file per record (proofrecords/<case_id>_<id>.json). Orchestrates
the dual-guard verification:
  - signs the record (ed25519) over the signed fields,
  - computes this_record_hash (excluding the verification block),
  - runs Guard-A in-process,
  - runs Guard-B in an isolated subprocess reading the file from disk,
  - fills the verification block (dual_guard_agreement / disagreement fields),
  - re-writes the individual file and appends to the chain.

Because this_record_hash is computed over the record MINUS the verification
block, filling the guards' results afterwards does not invalidate the hash, and
both guards independently apply the identical rule.
"""
import os
import json
import copy
import threading
import subprocess

from gate.core import (
    sign_record, compute_record_hash, signing_key, SIGNED_FIELDS,
)
from guards.guard_a import GuardA

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROOFRECORD_DIR = os.path.join(_HERE, "proofrecords")
CHAIN_PATH = os.path.join(PROOFRECORD_DIR, "proofrecord_chain.jsonl")
GUARD_B = os.path.join(_HERE, "guards", "guard_b_verifier.py")


class ProofStore:
    def __init__(self, guard_b_mode="inline"):
        os.makedirs(PROOFRECORD_DIR, exist_ok=True)
        self.last_hash = "GENESIS"
        self.guard_b_mode = guard_b_mode           # 'inline' | 'deferred'
        self._guard_a = GuardA()
        self._pub = signing_key().public_key()
        self._lock = threading.Lock()
        self.deferred = []                         # [(path, expected_prior_hash)]
        self.last_self_import_analysis = None

    # ------------------------------------------------------------------
    def load_tail(self):
        """Resume the chain from an existing chain file (used by the ARK-498 server)."""
        if not os.path.exists(CHAIN_PATH):
            return
        last = None
        with open(CHAIN_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    last = json.loads(line)
        if last:
            self.last_hash = last["chain"]["this_record_hash"]

    # ------------------------------------------------------------------
    def _individual_path(self, record):
        return os.path.join(
            PROOFRECORD_DIR,
            f"{record['case_id']}_{record['proofrecord_id']}.json")

    def _write_individual(self, record):
        path = self._individual_path(record)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
        return path

    def _append_chain(self, record):
        with open(CHAIN_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    def _empty_verification(self):
        return {
            "guard_a_result": "PENDING",
            "guard_a_fields_checked": [],
            "guard_a_canonical_hash_computed": "",
            "guard_b_result": "PENDING",
            "guard_b_fields_checked": [],
            "guard_b_canonical_hash_computed": "",
            "dual_guard_agreement": False,
            "dual_guard_disagreement_fields": [],
        }

    def _run_guard_b_single(self, path, expected_prior_hash):
        proc = subprocess.run(
            ["python3", GUARD_B, path, expected_prior_hash],
            capture_output=True, text=True, cwd=_HERE)
        out = json.loads(proc.stdout)
        self.last_self_import_analysis = out["self_import_analysis"]
        return out["results"][0]

    # ------------------------------------------------------------------
    def store(self, record):
        """Finalize (sign + hash + guards) and persist a ProofRecord."""
        with self._lock:
            expected_prior = self.last_hash
            record["chain"]["prior_record_hash"] = expected_prior
            record["signature"]["signature_hex"] = sign_record(record)
            record["chain"]["this_record_hash"] = compute_record_hash(record)
            record["verification"] = self._empty_verification()

            # Guard-A (in-process, independent)
            ga = self._guard_a.verify(record, expected_prior, self._pub)
            record["verification"].update(ga)

            # write individual file so Guard-B can read from disk
            path = self._write_individual(record)

            if self.guard_b_mode == "inline":
                gb = self._run_guard_b_single(path, expected_prior)
                self._merge_guard_b(record, gb)
                self._write_individual(record)
                self._append_chain(record)
            else:
                # deferred: Guard-B run in one batch later; append now, rewrite later
                self.deferred.append((path, expected_prior))
                self._append_chain(record)

            self.last_hash = record["chain"]["this_record_hash"]
            return record

    def _merge_guard_b(self, record, gb):
        v = record["verification"]
        v["guard_b_result"] = gb["guard_b_result"]
        v["guard_b_fields_checked"] = gb["guard_b_fields_checked"]
        v["guard_b_canonical_hash_computed"] = gb["guard_b_canonical_hash_computed"]
        disagree = []
        if v["guard_a_result"] != v["guard_b_result"]:
            disagree.append("result")
        if v["guard_a_canonical_hash_computed"] != v["guard_b_canonical_hash_computed"]:
            disagree.append("canonical_hash")
        v["dual_guard_disagreement_fields"] = disagree
        v["dual_guard_agreement"] = (len(disagree) == 0)

    # ------------------------------------------------------------------
    def flush_deferred_guard_b(self):
        """Run Guard-B once over all deferred records, then rewrite them."""
        if not self.deferred:
            return
        job = [{"path": p, "expected_prior_hash": h} for p, h in self.deferred]
        jobfile = os.path.join(PROOFRECORD_DIR, "_guard_b_job.json")
        with open(jobfile, "w", encoding="utf-8") as fh:
            json.dump(job, fh)
        proc = subprocess.run(
            ["python3", GUARD_B, "--job", jobfile],
            capture_output=True, text=True, cwd=_HERE)
        out = json.loads(proc.stdout)
        self.last_self_import_analysis = out["self_import_analysis"]
        by_path = {r["path"]: r for r in out["results"]}

        # rewrite individual files and rebuild chain file with updated verification
        chain_records = []
        with open(CHAIN_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    chain_records.append(json.loads(line))
        for rec in chain_records:
            path = self._individual_path(rec)
            if path in by_path:
                self._merge_guard_b(rec, by_path[path])
                self._write_individual(rec)
        with open(CHAIN_PATH, "w", encoding="utf-8") as fh:
            for rec in chain_records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.deferred = []
        os.remove(jobfile)
