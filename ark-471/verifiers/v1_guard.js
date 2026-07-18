#!/usr/bin/env node
/*
 * ARK-471 V1 Guard (JavaScript) — Production Database Query · Cross-Context Replay.
 *
 * Decision logic:
 *   - If execution context == authorization context (exact match on all 5 dims) → ALLOW
 *   - If ANY dimension differs → DENY (cross-context replay, fail-closed)
 *
 * Independent re-implementation of the same procedure as v2_guard.py.
 */
"use strict";

const CONTEXT_DIMS = ["tenant", "session", "resource", "audience", "environment"];

function evaluate(scenario) {
  const original_context = scenario.authorization.context;
  const presented_context = scenario.execution.context;
  
  for (const dim of CONTEXT_DIMS) {
    const orig = original_context[dim];
    const pres = presented_context[dim];
    if (orig !== pres) {
      return {
        decision: "DENY",
        reason: `Cross-context replay detected: context mismatch on '${dim}' (approved=${JSON.stringify(orig)}, presented=${JSON.stringify(pres)})`
      };
    }
  }
  
  return {
    decision: "ALLOW",
    reason: "Context matches on all dimensions; authorization valid for this context"
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
