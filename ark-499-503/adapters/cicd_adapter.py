"""
adapters/cicd_adapter.py — ARK-500 REAL CI/CD release-boundary adapter.

Uses a REAL local git repository and a REAL build step that produces a REAL
artifact tarball with a REAL SHA-256 digest. On ALLOW, a real "runner" promotes
exactly that artifact into a real on-disk deploy target (environments/<env>/)
and records the deployed digest. Independent inspection re-reads the deployed
files from disk and RECOMPUTES their SHA-256 — the testbed never asserts deploy
state itself.

Explicitly NOT claimed: Docker / Kubernetes / cloud CD. This is a local runner
and an on-disk deploy target only. The boundary property under test is:
only the exact approved artifact reaches the exact approved environment.
"""
import os
import shutil
import subprocess
import hashlib
import tarfile
import json
import secrets

ROOT = "/tmp/ark500_cicd"
REPO = os.path.join(ROOT, "repo")
ARTIFACTS = os.path.join(ROOT, "artifacts")
ENVS = os.path.join(ROOT, "environments")
DEPLOY_LOG = os.path.join(ROOT, "deploy_log.jsonl")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class CICDAdapter:
    tool_id = "T3"                        # "deploy application" tool
    _TOOL_NAME = "cicd_deploy"

    def __init__(self):
        self._blocked = 0
        self._down = False
        self.artifacts = {}               # name -> {path, digest}

    # ---- real repo + build ------------------------------------------------
    def setup(self):
        shutil.rmtree(ROOT, ignore_errors=True)
        os.makedirs(REPO); os.makedirs(ARTIFACTS)
        for env in ("staging", "production"):
            os.makedirs(os.path.join(ENVS, env))
        # real git repo
        subprocess.run(["git", "init", "-q", REPO], check=True)
        subprocess.run(["git", "-C", REPO, "config", "user.email",
                        "ci@remnantfieldworks.local"], check=True)
        subprocess.run(["git", "-C", REPO, "config", "user.name", "ARK CI"],
                       check=True)
        # a real source tree
        with open(os.path.join(REPO, "app.py"), "w") as fh:
            fh.write("def main():\n    return 'release-v1.0'\n")
        with open(os.path.join(REPO, "VERSION"), "w") as fh:
            fh.write("1.0.0\n")
        subprocess.run(["git", "-C", REPO, "add", "-A"], check=True)
        subprocess.run(["git", "-C", REPO, "commit", "-q", "-m", "release 1.0.0"],
                       check=True)
        # build the APPROVED artifact
        self.artifacts["approved"] = self._build("release-1.0.0")
        # build a DIFFERENT (unauthorized) artifact for the substitution arm
        with open(os.path.join(REPO, "app.py"), "w") as fh:
            fh.write("def main():\n    return 'BACKDOOR'\n")
        subprocess.run(["git", "-C", REPO, "add", "-A"], check=True)
        subprocess.run(["git", "-C", REPO, "commit", "-q", "-m", "tampered build"],
                       check=True)
        self.artifacts["tampered"] = self._build("release-1.0.0-tampered")

    def _build(self, name):
        art_path = os.path.join(ARTIFACTS, f"{name}.tar.gz")
        with tarfile.open(art_path, "w:gz") as tar:
            for f in ("app.py", "VERSION"):
                tar.add(os.path.join(REPO, f), arcname=f)
        return {"name": name, "path": art_path, "digest": _sha256_file(art_path)}

    # ---- adapter contract -------------------------------------------------
    def tool_name(self, tool_id):
        return self._TOOL_NAME

    def healthy(self):
        return not self._down and os.path.isdir(ENVS)

    def perform(self, action):
        """ALLOW: runner promotes the artifact whose digest matches the request
        into the requested environment, exactly once."""
        p = action["parameters"]
        digest = p["artifact_digest"]
        env = p["environment"]
        entry_id = "deploy-" + secrets.token_hex(8)
        # locate the artifact by digest (real content-addressed lookup)
        src = None
        for meta in self.artifacts.values():
            if meta["digest"] == digest:
                src = meta
                break
        if src is None:
            # no artifact with this digest exists -> nothing to deploy
            self._log({"event": "deploy_no_artifact", "digest": digest,
                       "environment": env})
            return entry_id, {"deployed": False, "reason": "no matching artifact"}
        dest_dir = os.path.join(ENVS, env)
        dest = os.path.join(dest_dir, "current.tar.gz")
        shutil.copyfile(src["path"], dest)
        deployed_digest = _sha256_file(dest)
        with open(os.path.join(dest_dir, "MANIFEST.json"), "w") as fh:
            json.dump({"artifact": src["name"], "digest": deployed_digest,
                       "idempotency_key": action["idempotency_key"]}, fh)
        self._log({"event": "deployed", "environment": env,
                   "digest": deployed_digest, "artifact": src["name"]})
        return entry_id, {"deployed": True, "environment": env,
                          "deployed_digest": deployed_digest,
                          "artifact": src["name"]}

    def record_blocked(self, action, decision):
        self._blocked += 1
        self._log({"event": "blocked", "decision": decision,
                   "environment": action["parameters"].get("environment")})
        return f"cicd-blocked-{decision}-{self._blocked}"

    def _log(self, entry):
        with open(DEPLOY_LOG, "a") as fh:
            fh.write(json.dumps(entry) + "\n")

    # ---- independent inspection (re-read from disk) -----------------------
    def inspect_env(self, env):
        """Return {deployed: bool, digest: str|None} by re-reading disk."""
        cur = os.path.join(ENVS, env, "current.tar.gz")
        if not os.path.exists(cur):
            return {"deployed": False, "digest": None}
        return {"deployed": True, "digest": _sha256_file(cur)}

    def deploy_event_count(self):
        if not os.path.exists(DEPLOY_LOG):
            return 0
        n = 0
        with open(DEPLOY_LOG) as fh:
            for line in fh:
                if line.strip() and json.loads(line)["event"] == "deployed":
                    n += 1
        return n
