#!/usr/bin/env node
/*
 * ARK-475 V1 Guard (JavaScript) — Production Financial Transaction · Dependency Loss.
 *
 * Decision logic:
 *   - If ALL critical dependencies are AVAILABLE → ALLOW (can confirm validity)
 *   - If ANY critical dependency is UNAVAILABLE → HOLD (cannot confirm validity, fail-safe)
 *
 * Independent re-implementation of the same procedure as v2_guard.py.
 */
"use strict";

const CRITICAL_DEPS = ["PaymentGateway", "FraudDetector", "AccountVerifier", "Financial TransactionAuditor"];

function evaluate(scenario) {
  const dependencies = scenario.dependencies || {};
  
  const unavailable = CRITICAL_DEPS.filter(dep => dependencies[dep] === "UNAVAILABLE");
  
  if (unavailable.length > 0) {
    return {
      decision: "HOLD",
      reason: `Critical dependencies UNAVAILABLE: ${unavailable.join(", ")} — cannot confirm validity (fail-safe)`
    };
  }
  
  // All dependencies available → can confirm validity
  return {
    decision: "ALLOW",
    reason: "All critical dependencies AVAILABLE; validity confirmed"
  };
}

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    const scenarios = JSON.parse(input);
    const results = scenarios.map((sc) => {
      const r = evaluate(sc);
      return { scenario_id: sc.scenario_id, arm: sc.arm, ...r };
    });
    process.stdout.write(JSON.stringify(results, null, 2));
  });
}

main();
