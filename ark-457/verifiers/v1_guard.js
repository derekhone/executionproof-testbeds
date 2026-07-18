#!/usr/bin/env node
/**
 * ARK-457 V1 Guard (JavaScript, no dependencies)
 * Cross-Context Authorization Replay (Confused Deputy).
 *
 * An authorization is bound to a context tuple. Execution presents its own
 * context. The guard ALLOWs only if the execution context matches the
 * authorization's bound context EXACTLY on every binding dimension.
 *
 * Exact string equality — NO normalization, NO case folding, NO whitespace
 * trimming, NO homoglyph mapping. A confusable near-match is a MISMATCH.
 */

const BINDING_DIMS = ["tenant", "session", "resource", "audience", "environment"];

function evaluate(scenario) {
  const binding = scenario.authorization.binding;
  const ctx = scenario.execution.context;

  for (const dim of BINDING_DIMS) {
    const a = binding[dim];
    const b = ctx[dim];
    // Strict, byte/codepoint-exact comparison. Also guard against type/absence.
    if (typeof a !== "string" || typeof b !== "string" || a !== b) {
      return {
        decision: "DENY",
        reason: `Context mismatch on '${dim}': authorization bound to ${JSON.stringify(a)} but execution context is ${JSON.stringify(b)} (authorization does not transfer across contexts)`
      };
    }
  }

  return {
    decision: "ALLOW",
    reason: "Execution context matches the authorization's bound context on all binding dimensions"
  };
}

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
