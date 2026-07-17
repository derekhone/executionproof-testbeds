# ARK-445b Run Log — Execution Provenance

**Experiment ID:** ARK-445b  
**Predecessor:** ARK-445 (tag `ark-445-v1.0`, VERDICT=FAIL)  
**Repository:** `executionproof-testbeds` (branch `execute/ark-445b`)

---

## Step 1 — LOCK (preregistration + code + SHA-256 MANIFEST)

**LOCK commit SHA:** _(to be recorded after commit)_  
**LOCK timestamp (UTC):** _(to be recorded after commit)_  
**MANIFEST SHA-256 checksums:**

```
# (See MANIFEST.txt)
56c25cd0ca53d345e150d7225b258092d5b89ccbd8cc91600c9b959a7e126f9c  ARK_445b_preregistration.md
1cabcf2cb715e7c7f5f2f7299b4bd04e785a0b88d9c401e0214008fe58e87ea9  README.md
1d31ad411716846860a54839e4476096cb2bb5ea037c482f4e371a05539e5cbf  ark_445b_select_qubits.py
6c80d663d892874d2d610aa6fd0a2193821928ad8da38296dce1e88d970038cf  ark_445b_circuits.py
3dc7629dea5d430b371c21796c068800192c89e6bb8cf3a34cee3978ee7984c8  ark_445b_spam_job.py
7da60b96714b0e43ee451db99508edbda1dfe66e786e2d92b704997e7b571538  ark_445b_submit_ibm.py
6b7603f64a99ec0cec2335490d1e2fb6cfe775955aa2154f34e9a38c6542ff2f  ark_445b_retrieve.py
100e5d0924de7944b29745404e788b9b9e6c89b2455b6e54ae722a172df9bd1b  ark_445b_analysis.py
```

**Pre-lock validation (local):**
- AerSimulator logic test: ✅ PASSED (ALLOW→1.0, DENY→0.0, HOLD→~0.5)
- Transpile check (ibm_marrakesh, opt3): ✅ PASSED (all 9 circuits transpile without error)

**Files frozen before any hardware job.**

---

## Step 2 — Qubit Selection

_(pending — run `ark_445b_select_qubits.py` after LOCK commit)_

---

## Step 3 — SPAM Kill-Gate

_(pending — run `ark_445b_spam_job.py` after qubit selection)_

---

## Step 4–7 — Principal Job

_(pending — run `ark_445b_submit_ibm.py` after SPAM gate PASSES)_

---

## Step 8-11 — Retrieval / Analysis / Results

_(pending)_

---

**This log will be updated in real-time during execution. Each step's completion is committed BEFORE the next step begins (Field 27 strict ordering).**
