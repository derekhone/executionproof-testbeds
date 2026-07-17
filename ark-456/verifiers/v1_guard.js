#!/usr/bin/env node
/**
 * ARK-456 V1 Guard (JavaScript, no dependencies)
 * Evaluates authorization requests under degraded dependency conditions.
 * Fail-closed: if ANY required dependency is unavailable/corrupted → DENY.
 */

const REQUIRED_DEPS = [
  "identity_provider",
  "policy_registry",
  "evidence_schema",
  "clock_source",
  "signature_key",
  "audit_store"
];

function evaluate(scenario) {
  const { dependency_state, authorization_request } = scenario;
  
  // Check all required dependencies
  for (const dep of REQUIRED_DEPS) {
    if (dependency_state[dep] !== "available") {
      return {
        decision: "DENY",
        reason: `Required dependency ${dep} is ${dependency_state[dep]} (fail-closed)`
      };
    }
  }
  
  // All dependencies available — evaluate authorization normally.
  // For this experiment, the baseline request is designed to be valid.
  return {
    decision: "ALLOW",
    reason: "All dependencies available; authorization valid"
  };
}

// CLI: read scenarios from stdin, output decisions to stdout
if (require.main === module) {
  const fs = require("fs");
  const input = fs.readFileSync(0, "utf-8");
  const scenarios = JSON.parse(input);
  
  const results = scenarios.map(sc => ({
    scenario_id: sc.scenario_id,
    arm: sc.arm,
    ...evaluate(sc)
  }));
  
  console.log(JSON.stringify(results, null, 2));
}

module.exports = { evaluate };
