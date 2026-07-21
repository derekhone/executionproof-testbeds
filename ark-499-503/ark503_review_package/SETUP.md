# ARK-503 — Setup (reproduce the series from a clean machine)

The reviewer should reproduce ARK-499–502 **before** trying to break anything,
to confirm the artifacts match what is claimed.

## Prerequisites

- Linux, Python 3.11+
- PostgreSQL **17** server binaries (`initdb`, `pg_ctl`, `postgres`) on PATH or
  at `/usr/lib/postgresql/17/bin` (ARK-499 / ARK-502)
  - Debian/Ubuntu: `sudo apt-get install -y postgresql-17`
- `git` (ARK-500)
- Python packages: see `../requirements.txt`
  - `pip install -r ../requirements.txt`
  - key ones: `psycopg2-binary`, `pyjwt`, `cryptography`, `flask`, `requests`

No Docker, no cloud account, no network egress is required. Everything runs on
loopback and local sockets.

## Verify the preregistration lock FIRST

The experiment questions, arms, metrics, thresholds and kill-conditions were
frozen *before* execution and hashed. Confirm nothing was edited after the fact:

```bash
cd ..
sha256sum -c PREREGISTRATION-MANIFEST.txt
```

Every line must print `OK`. If any line fails, the run is **not** covered by a
pre-registration and must be treated as exploratory only.

## Reproduce the experiments

```bash
cd ..
python3 run_all.py            # re-verifies the manifest, then runs 499-502
```

Or individually:

```bash
python3 experiments/run_499.py    # real PostgreSQL transaction boundary
python3 experiments/run_500.py    # real CI/CD release boundary
python3 experiments/run_501.py    # real external OIDC/IAM identity boundary
python3 experiments/run_502.py    # BOUNDED operational smoke (NOT 14-day soak)
```

Expected top-line results (subject to your independent judgement):

- ARK-499 → `EXPERIMENT-PASS`
- ARK-500 → `EXPERIMENT-PASS`
- ARK-501 → `EXPERIMENT-PASS`
- ARK-502 → `SMOKE-PASS` (with ≥14-day endurance recorded `NOT-EXECUTED`)

## Independently verify the ProofRecords

```bash
python3 ark503_review_package/independent_verifier.py proofrecords/
```

This tool imports **none** of the testbed code. It uses only the published
public key embedded in the script. A clean run prints `N OK, 0 FAIL` and exits
`0`. Tamper with any record and it must report the specific failure and exit
non-zero — try it (Task 5).
