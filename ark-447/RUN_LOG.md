# ARK-447 Run Log

**Experiment:** ARK-447 — Noise-Suppression Comparison  
**Protocol:** Field 27 (LOCK → SPAM gate → principal job → analyze → verdict)  
**Status:** STAGED (not yet executed)

---

## Execution Steps

### Step 0: LOCK Commit (Not Yet Done)
- [ ] Preregistration document committed
- [ ] All 6 code files committed
- [ ] MANIFEST.txt with SHA-256 hashes committed
- [ ] Tag `ark-447-v1.0-lock` created
- [ ] Branch `execute/ark-447` pushed to GitHub

**Note:** LOCK must be completed BEFORE any hardware job submission.

---

### Step 1: Qubit Selection (Not Yet Run)
**Command:** `python3 ark_447_select_qubits.py`

**Expected outputs:**
- `selected_qubits.json` — Q_A, Q_P, readout errors
- `calibration_snapshot_*.json` — Backend calibration data

**Criteria:** Q_A and Q_P must be connected (coupling map); lowest readout error sum preferred.

---

### Step 2: SPAM Baseline Job (Not Yet Run)
**Command:** `python3 ark_447_spam_job.py`

**Expected outputs:**
- `spam_results.json` — SPAM_A and SPAM_P counts, gate pass/fail

**Gate condition:** Both SPAM_A error ≤ 0.02 AND SPAM_P deviation from 0.5 ≤ 0.02

**If gate fails:** STOP. Do not proceed with principal job. Publish FAIL verdict.

---

### Step 3: Principal Job Submission (Not Yet Run)
**Command:** `python3 ark_447_submit_ibm.py`

**Expected outputs:**
- `principal_job_id.txt` — Job ID for retrieval
- `principal_job_meta.json` — Job metadata

**Job structure:**
- 6 circuits (arm1-arm6)
- 8192 shots per circuit
- Estimated runtime: ~25-30 seconds on backend

---

### Step 4: Results Retrieval (Not Yet Run)
**Command:** `python3 ark_447_retrieve.py`

**Wait for job completion** (check IBM Quantum dashboard or job status).

**Expected outputs:**
- `raw_results.json` — Raw counts from all 6 circuits

---

### Step 5: Analysis and Verdict (Not Yet Run)
**Command:** `python3 ark_447_analysis.py`

**Computes:**
- S_A, L_D (raw and corrected), Δ_B for each configuration
- Pass/fail per configuration
- Overall verdict (PASS strong/weak, MIXED, FAIL)

**Expected outputs:**
- `proofrecord.json` — Full analysis results and verdict
- Console output with metrics table

---

### Step 6: Documentation (Not Yet Done)
- [ ] Generate `RESULTS.md` with full scorecard
- [ ] Update this `RUN_LOG.md` with execution details
- [ ] Commit results files

---

### Step 7: Tag and Publish (Not Yet Done)
- [ ] Tag `ark-447-v1.0` at final commit
- [ ] Push to GitHub
- [ ] Open PR on `executionproof-testbeds`

---

## Preregistration Integrity

**MANIFEST.txt SHA-256 hashes** will be computed before LOCK and committed. Any modification to code files after LOCK invalidates the preregistration.

---

## Timeline

- **LOCK commit:** TBD
- **Qubit selection + SPAM:** ~5 min
- **Principal job:** ~25-30 sec (plus queue wait)
- **Retrieval + analysis:** ~2 min
- **Documentation:** ~5 min
- **Total:** ~15-20 min (excluding queue)

---

**This run log will be updated in real-time during execution.**
