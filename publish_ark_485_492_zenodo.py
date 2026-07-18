#!/usr/bin/env python3
"""Publish ARK-485 through ARK-492 (P02 Latency/Throughput/Scale) to Zenodo."""
import requests
import json
import os

ZENODO_TOKEN = "IjKV4tF4GhrsAlNpWwyGrfaCJe4BmKZWnufwoYixZAj5vTWoTMAR4HK5jE98"
ZENODO_API = "https://zenodo.org/api/deposit/depositions"
CONCEPT_DOI = "10.5281/zenodo.21398675"

COV = ("<p><em>Covenant: outcomes preserved as measured; claims bounded to the "
       "tested in-memory reference under single-threaded load. Component "
       "performance measurements — not legal, patent, security, or "
       "production-readiness proofs. Soli Deo Gloria.</em></p>")

experiments = [
    {
        "id": "ark-485",
        "title": "ARK-485 — Verification Decision · Sustained Throughput",
        "description": f"""<p><strong>ARK-485</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures sustained throughput (decisions/second over a 60-second window) of the frozen ARK-458 deployment guard under continuous single-threaded load, extending ARK-484's burst measurement.</p>
<p><strong>Verdict:</strong> PASS. V2 (Python) 1,504,355 dec/s; V1 (JavaScript) 9,521,201 dec/s; 100% accuracy over the full window. Threshold ≥50K (Py) / ≥100K (JS).</p>
{COV}""",
        "tarball": "ark-485.tar.gz",
    },
    {
        "id": "ark-486",
        "title": "ARK-486 — Verification Decision · Cost at Scale",
        "description": f"""<p><strong>ARK-486</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures marginal compute cost per verification decision. Supersedes an earlier FAIL ($0.20/M) that resulted from a cost-model category error (charging one serverless request per in-process decision). Corrected preregistration reports two scenarios and takes the verdict on the realistic running-service model.</p>
<p><strong>Verdict:</strong> PASS (Scenario B basis). Realistic running-service cost $7.47e-06/M (Python), $1.18e-06/M (JavaScript), both far below the $0.01/M threshold. Scenario A naive-serverless bound ($0.20/M) disclosed for transparency.</p>
{COV}""",
        "tarball": "ark-486.tar.gz",
    },
    {
        "id": "ark-487",
        "title": "ARK-487 — Authority Engine · Cold Start Latency",
        "description": f"""<p><strong>ARK-487</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures cold-start latency (engine construction to first correct decision) of a minimal in-process reference Authority Engine — the AUTHORITY half of Verification-Before-Execution: does a principal CURRENTLY hold the claimed authority at execution time? Reference implementation for measurement only, not a production engine.</p>
<p><strong>Verdict:</strong> PASS. Cold-start p95 9.34 ms (mean 7.87 ms) over 200 runs; threshold ≤50 ms. Correctness gate PASS: valid→ALLOW, mutated→DENY, revoked→DENY.</p>
{COV}""",
        "tarball": "ark-487.tar.gz",
    },
    {
        "id": "ark-488",
        "title": "ARK-488 — Authority Engine · P95 Decision Latency",
        "description": f"""<p><strong>ARK-488</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures warm per-decision latency of the reference Authority Engine — the latency an at-execution "does this principal still hold this authority?" check adds to the critical path.</p>
<p><strong>Verdict:</strong> PASS. Warm p95 0.32 µs, p99 0.41 µs over 200,000 decisions; threshold p95 ≤50 µs. Correctness gate PASS.</p>
{COV}""",
        "tarball": "ark-488.tar.gz",
    },
    {
        "id": "ark-489",
        "title": "ARK-489 — Authority Engine · Burst Throughput",
        "description": f"""<p><strong>ARK-489</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures peak (burst) throughput of the reference Authority Engine — current-state authority decisions/second in a short high-intensity window.</p>
<p><strong>Verdict:</strong> PASS. 3,090,730 dec/s over 10s at 100% accuracy; threshold ≥200K. Correctness gate PASS.</p>
{COV}""",
        "tarball": "ark-489.tar.gz",
    },
    {
        "id": "ark-490",
        "title": "ARK-490 — Authority Engine · Sustained Throughput",
        "description": f"""<p><strong>ARK-490</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures sustained throughput of the reference Authority Engine over a 60-second window and degradation versus burst (ARK-489).</p>
<p><strong>Verdict:</strong> PASS. 2,491,235 dec/s sustained over 60s at 100% accuracy (~81% of burst); threshold ≥100K. Correctness gate PASS.</p>
{COV}""",
        "tarball": "ark-490.tar.gz",
    },
    {
        "id": "ark-491",
        "title": "ARK-491 — Authority Engine · Cost at Scale",
        "description": f"""<p><strong>ARK-491</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures marginal compute cost per authority decision using the corrected cost basis established in ARK-486 (realistic running-service, per vCPU-second, amortized across measured throughput).</p>
<p><strong>Verdict:</strong> PASS (Scenario B basis). Realistic cost $3.59e-06/M; threshold ≤$0.01/M. Scenario A naive-serverless bound ($0.20/M) disclosed. Correctness gate PASS.</p>
{COV}""",
        "tarball": "ark-491.tar.gz",
    },
    {
        "id": "ark-492",
        "title": "ARK-492 — Evidence Engine · Cold Start Latency",
        "description": f"""<p><strong>ARK-492</strong> — ExecutionProof P02 Latency/Throughput/Scale series by Remnant Fieldworks Inc.</p>
<p>Measures cold-start latency of a minimal in-process reference Evidence Engine — the EVIDENCE half of Verification-Before-Execution: is there a complete, tamper-evident record proving the execution matched what was authorized? Builds a 10,000-record SHA-256 hash chain then verifies the first record. Reference implementation for measurement only.</p>
<p><strong>Verdict:</strong> PASS. Cold-start p95 44.0 ms (mean 43.5 ms) over 200 runs; threshold ≤100 ms. Correctness gate PASS: intact→ALLOW, tampered→DENY, broken-chain→DENY.</p>
{COV}""",
        "tarball": "ark-492.tar.gz",
    },
]

results = []
for exp in experiments:
    print(f"\n{'='*70}\nPublishing {exp['id']}: {exp['title']}\n{'='*70}")
    params = {"access_token": ZENODO_TOKEN}
    headers = {"Content-Type": "application/json"}

    r = requests.post(ZENODO_API, json={}, params=params, headers=headers)
    if r.status_code != 201:
        print(f"FAIL create: {r.status_code} {r.text[:200]}")
        results.append({"id": exp["id"], "status": "failed_create", "error": r.text[:300]})
        continue
    dep_id = r.json()["id"]
    bucket = r.json()["links"]["bucket"]
    print(f"  created deposition {dep_id}")

    tb = exp["tarball"]
    if not os.path.exists(tb):
        results.append({"id": exp["id"], "status": "failed_upload", "error": "tarball missing"})
        continue
    with open(tb, "rb") as fp:
        r = requests.put(f"{bucket}/{tb}", data=fp, params=params)
    if r.status_code not in (200, 201):
        print(f"FAIL upload: {r.status_code} {r.text[:200]}")
        results.append({"id": exp["id"], "status": "failed_upload", "error": r.text[:300]})
        continue
    print(f"  uploaded {tb}")

    metadata = {"metadata": {
        "title": exp["title"],
        "upload_type": "dataset",
        "description": exp["description"],
        "creators": [{"name": "Remnant Fieldworks Inc.", "affiliation": "Remnant Fieldworks Inc."}],
        "keywords": ["ExecutionProof", "authorization", "verification latency",
                     "throughput", "performance", "P02", exp["id"]],
        "related_identifiers": [
            {"identifier": CONCEPT_DOI, "relation": "isPartOf", "scheme": "doi"}
        ],
        "access_right": "open",
        "license": "cc-by-4.0",
    }}
    r = requests.put(f"{ZENODO_API}/{dep_id}", json=metadata, params=params, headers=headers)
    if r.status_code != 200:
        print(f"FAIL metadata: {r.status_code} {r.text[:200]}")
        results.append({"id": exp["id"], "status": "failed_metadata", "error": r.text[:300]})
        continue
    print("  metadata set")

    r = requests.post(f"{ZENODO_API}/{dep_id}/actions/publish", params=params)
    if r.status_code != 202:
        print(f"FAIL publish: {r.status_code} {r.text[:200]}")
        results.append({"id": exp["id"], "status": "failed_publish", "error": r.text[:300]})
        continue
    rec = r.json()
    doi = rec["doi"]
    url = rec["links"]["record_html"]
    print(f"  PUBLISHED  DOI={doi}  {url}")
    results.append({"id": exp["id"], "status": "published", "doi": doi,
                    "url": url, "deposition_id": dep_id})

with open("zenodo_ark_485_492_results.json", "w") as f:
    json.dump(results, f, indent=2)

pub = sum(1 for r in results if r["status"] == "published")
print(f"\n{'='*70}\nPublished {pub}/{len(experiments)}. Results -> zenodo_ark_485_492_results.json")
for r in results:
    if r["status"] == "published":
        print(f"  {r['id']}: {r['doi']}")
    else:
        print(f"  {r['id']}: {r['status']}")
