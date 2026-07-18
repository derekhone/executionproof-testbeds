#!/usr/bin/env node
/*
 * ARK-458 V1 Guard (JavaScript) — Cloud IAM Role Grant · Exact-Action Binding.
 *
 * An authorization is APPROVED bound to an exact IAM action tuple. At execution
 * time an IAM grant action is presented. The guard ALLOWs only if the execution
 * action matches the approved action EXACTLY on every binding dimension.
 *
 * Exact string equality (===) — NO normalization, NO case folding, NO trimming,
 * NO homoglyph mapping, NO privilege "subset" reasoning. A confusable near-match
 * is a MISMATCH.
 *
 * Independent re-implementation of the same procedure as v2_guard.py.
 */
"use strict";

const BINDING_DIMS = ["principal", "role", "account", "permission_set", "condition"];

function evaluate(scenario) {
  const binding = scenario.authorization.binding;
  const action = scenario.execution.action;

  for (const dim of BINDING_DIMS) {
    const a = binding[dim];
    const b = action[dim];
    if (typeof a !== "string" || typeof b !== "string" || a !== b) {
      return {
        decision: "DENY",
        reason:
          `Action mismatch on '${dim}': approved grant bound to ` +
          `${JSON.stringify(a)} but execution action is ${JSON.stringify(b)} ` +
          `(approval does not authorize a mutated IAM action)`,
      };
    }
  }

  return {
    decision: "ALLOW",
    reason: "Execution action matches the approved IAM grant on all binding dimensions",
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
