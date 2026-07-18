#!/usr/bin/env node
/*
 * ARK-483 — Verification Decision Latency (V1 / JavaScript component).
 *
 * Cross-implementation latency measurement of the SAME verification decision
 * measured by latency_bench.py, but against the independent V1 (JavaScript)
 * guard from ARK-458. Together the two benches answer whether the two
 * independent guard implementations are in the same latency regime
 * (concordance of order-of-magnitude), not just decision concordance.
 *
 * Integrity note: ark-458/verifiers/v1_guard.js is a LOCKED file (hashed in
 * ARK-458/MANIFEST.txt). We do NOT modify it. Instead we load its exact locked
 * bytes into a vm sandbox and extract evaluate() without executing its main()
 * stdin loop. The bytes measured are the frozen guard, unchanged.
 *
 * Methodology (preregistered), mirroring the Python bench:
 *   - Two decision paths: ALLOW (exact match, all 5 dims compared),
 *     DENY-first (first-dim mismatch, early exit),
 *     DENY-last (last-dim mismatch, worst-case DENY).
 *   - Warmup iterations discarded; cold-start (first call) recorded separately.
 *   - process.hrtime.bigint() around a single evaluate() call, repeated N times.
 *   - Environment captured for bounded-claim discipline.
 *
 * Absolute numbers are bounded to the machine reported in the results file.
 */
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const vm = require("vm");

const HERE = __dirname;
const REPO = path.resolve(HERE, "..", "..");
const GUARD_PATH = path.join(REPO, "ark-458", "verifiers", "v1_guard.js");

// Load the LOCKED guard bytes unchanged; expose evaluate() without running main().
function loadLockedEvaluate() {
  const src = fs.readFileSync(GUARD_PATH, "utf8");
  // Wrap the exact source, then export evaluate. We neutralise the trailing
  // main() invocation by shadowing it: the source defines `function main`,
  // and calls main() at the very end. We append an override that captures
  // evaluate into the sandbox scope instead of relying on that call.
  const sandbox = { module: {}, exports: {}, process: { stdin: { setEncoding() {}, on() {} }, stdout: { write() {} } }, require, console, JSON };
  sandbox.global = sandbox;
  const wrapped = src + "\n;globalThis.__ark483_evaluate = evaluate;\n";
  vm.createContext(sandbox);
  // Provide a process stub so the appended source's main() call is a no-op read.
  sandbox.globalThis = sandbox;
  vm.runInContext(wrapped, sandbox, { filename: GUARD_PATH });
  const fn = sandbox.__ark483_evaluate || (sandbox.globalThis && sandbox.globalThis.__ark483_evaluate);
  if (typeof fn !== "function") {
    throw new Error("Failed to extract evaluate() from locked v1_guard.js");
  }
  return fn;
}

const evaluate = loadLockedEvaluate();

const WARMUP = 5000;
const N = 100000;

const BASE_BINDING = {
  principal: "arn:aws:iam::100000000042:user/svc-0042",
  role: "ReadOnlyAuditor",
  account: "100000000042",
  permission_set: "ps-0123456789abcdef",
  condition: "region=us-east-1;mfa=true",
};

function scenario(mutateDim, mutateVal) {
  const binding = { ...BASE_BINDING };
  const action = { ...BASE_BINDING };
  if (mutateDim) action[mutateDim] = mutateVal || "__X__";
  return { scenario_id: "bench", arm: 0,
    authorization: { binding }, execution: { action } };
}

function timePath(sc, n, expect) {
  const d = evaluate(sc).decision;
  if (d !== expect) throw new Error(`expected ${expect} got ${d}`);
  const samples = new Array(n);
  for (let i = 0; i < n; i++) {
    const t0 = process.hrtime.bigint();
    evaluate(sc);
    const t1 = process.hrtime.bigint();
    samples[i] = Number(t1 - t0); // nanoseconds
  }
  return samples;
}

function summarize(samplesNs) {
  const s = samplesNs.slice().sort((a, b) => a - b);
  const n = s.length;
  const pct = (p) => s[Math.min(n - 1, Math.round((p / 100) * (n - 1)))];
  const us = 1000.0;
  const mean = s.reduce((a, b) => a + b, 0) / n;
  const variance = s.reduce((a, b) => a + (b - mean) * (b - mean), 0) / n;
  const r = (x) => Math.round(x * 10000) / 10000;
  return {
    n,
    mean_us: r(mean / us),
    median_us: r(pct(50) / us),
    p50_us: r(pct(50) / us),
    p95_us: r(pct(95) / us),
    p99_us: r(pct(99) / us),
    p999_us: r(pct(99.9) / us),
    min_us: r(s[0] / us),
    max_us: r(s[n - 1] / us),
    stdev_us: r(Math.sqrt(variance) / us),
    throughput_decisions_per_sec: Math.round(1e9 / mean),
  };
}

function main() {
  console.log("=".repeat(70));
  console.log("ARK-483 — Verification Decision Latency (V1 / JavaScript component)");
  console.log("=".repeat(70));

  // Cold start
  const cold = scenario();
  const c0 = process.hrtime.bigint();
  evaluate(cold);
  const c1 = process.hrtime.bigint();
  const coldStartUs = Math.round(Number(c1 - c0) / 100) / 10;
  console.log(`Cold-start (first decision): ${coldStartUs} us`);

  // Warmup
  const warm = scenario();
  for (let i = 0; i < WARMUP; i++) evaluate(warm);

  const paths = {
    allow_exact_match: [scenario(), "ALLOW"],
    deny_first_dim_mismatch: [scenario("principal", "arn:aws:iam::999:user/x"), "DENY"],
    deny_last_dim_mismatch: [scenario("condition", "region=*;mfa=false"), "DENY"],
  };

  const results = {};
  for (const [name, [sc, expect]] of Object.entries(paths)) {
    console.log(`\nMeasuring path '${name}' (expect ${expect}, n=${N})...`);
    const samples = timePath(sc, N, expect);
    const summ = summarize(samples);
    results[name] = summ;
    console.log(`  mean=${summ.mean_us}us  p50=${summ.p50_us}us  ` +
      `p95=${summ.p95_us}us  p99=${summ.p99_us}us  ` +
      `max=${summ.max_us}us  thpt=${summ.throughput_decisions_per_sec}/s`);
  }

  const cpus = os.cpus();
  const env = {
    node_version: process.version,
    v8_version: process.versions.v8,
    platform: `${os.type()} ${os.release()}`,
    arch: process.arch,
    cpu_model: cpus.length ? cpus[0].model : "unknown",
  };

  const p95CeilingUs = 1000.0;
  const worstP95 = Math.max(...Object.values(results).map((r) => r.p95_us));
  const ceilingPass = worstP95 <= p95CeilingUs;

  const out = {
    experiment: "ARK-483",
    title: "Verification Decision Latency",
    component_under_test: "ark-458/verifiers/v1_guard.js::evaluate (exact-action-binding, LOCKED bytes via vm sandbox)",
    substrate: "classical software (in-process, no I/O, no network)",
    run_time: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    warmup_iterations: WARMUP,
    timed_iterations_per_path: N,
    cold_start_us: coldStartUs,
    paths: results,
    environment: env,
    preregistered_p95_ceiling_us: p95CeilingUs,
    worst_path_p95_us: worstP95,
    ceiling_pass: ceilingPass,
    verdict: ceilingPass ? "PASS" : "FAIL",
    bounds_note:
      "Absolute latencies are bounded to the environment above. Measures the " +
      "in-process decision only; excludes network, auth-token retrieval, " +
      "evidence persistence, and process startup.",
  };

  const resultsDir = path.join(HERE, "..", "results");
  fs.mkdirSync(resultsDir, { recursive: true });
  fs.writeFileSync(path.join(resultsDir, "latency_v1_js.json"), JSON.stringify(out, null, 2));

  console.log("\n" + "=".repeat(70));
  console.log(`Worst-path P95 = ${worstP95} us  (ceiling ${p95CeilingUs} us)  -> ` +
    (ceilingPass ? "PASS" : "FAIL"));
  console.log("=".repeat(70));
}

main();
