#!/usr/bin/env node
/* ARK-477 V1 Guard (JavaScript) — Production Financial Transaction · Human Escalation. */
"use strict";

function evaluate(scenario) {
  const requires_human_approval = scenario.requires_human_approval || false;
  const human_approval = scenario.human_approval || null;
  
  if (!requires_human_approval) {
    return {decision: "ALLOW", reason: "No human approval required"};
  }
  
  if (human_approval === null) {
    return {decision: "HOLD", reason: "Human approval required but not yet received (fail-safe)"};
  }
  
  if (typeof human_approval !== "object" || human_approval.valid !== true) {
    return {decision: "HOLD", reason: `Human approval invalid or incomplete (fail-safe): ${JSON.stringify(human_approval)}`};
  }
  
  return {decision: "ALLOW", reason: `Human approval received and valid (approved_by=${human_approval.approved_by})`};
}

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    const scenarios = JSON.parse(input);
    const results = scenarios.map((sc) => {
      const r = evaluate(sc);
      return {scenario_id: sc.scenario_id, arm: sc.arm, ...r};
    });
    process.stdout.write(JSON.stringify(results, null, 2));
  });
}

main();
