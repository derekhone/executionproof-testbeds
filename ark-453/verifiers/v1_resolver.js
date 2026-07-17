#!/usr/bin/env node
/**
 * ARK-453 V1 Resolver (JavaScript, no external dependencies)
 * Independent implementation of the evidence conflict resolution procedure.
 * Reads scenarios (JSON array), outputs decisions (ALLOW/HOLD/DENY).
 */

// Decision types
const ALLOW = "ALLOW";
const HOLD = "HOLD";
const DENY = "DENY";

// Evidence signals
const ALLOW_SIGNAL = "ALLOW_SIGNAL";
const DENY_SIGNAL = "DENY_SIGNAL";
const UNKNOWN = "UNKNOWN";

/**
 * Resolve a single evidence scenario to ALLOW, HOLD, or DENY.
 * 
 * Decision procedure:
 * 1. If any source = UNKNOWN → HOLD
 * 2. Collect unique non-UNKNOWN signals
 * 3. If all sources emit ALLOW_SIGNAL → ALLOW
 * 4. If all sources emit DENY_SIGNAL → DENY
 * 5. If sources disagree (mixed ALLOW/DENY) → HOLD
 */
function resolveScenario(scenario) {
  const sources = scenario.evidence_sources;
  
  // Extract signals from all 6 sources
  const signals = [
    sources.identity.signal,
    sources.policy.signal,
    sources.risk.signal,
    sources.approval.signal,
    sources.registry.signal,
    sources.temporal.signal
  ];
  
  // Rule 1: Any UNKNOWN → HOLD
  if (signals.includes(UNKNOWN)) {
    return HOLD;
  }
  
  // Rule 2: Collect unique non-UNKNOWN signals
  const uniqueSignals = new Set(signals);
  
  // Rule 3: All ALLOW → ALLOW
  if (uniqueSignals.size === 1 && uniqueSignals.has(ALLOW_SIGNAL)) {
    return ALLOW;
  }
  
  // Rule 4: All DENY → DENY
  if (uniqueSignals.size === 1 && uniqueSignals.has(DENY_SIGNAL)) {
    return DENY;
  }
  
  // Rule 5: Mixed signals → HOLD
  return HOLD;
}

/**
 * Resolve a batch of scenarios and return summary + verdicts
 */
function resolveBatch(scenarios) {
  const verdicts = [];
  const counts = { [ALLOW]: 0, [HOLD]: 0, [DENY]: 0 };
  
  for (const scenario of scenarios) {
    const decision = resolveScenario(scenario);
    verdicts.push({
      scenario_id: scenario.scenario_id,
      decision: decision
    });
    counts[decision]++;
  }
  
  return {
    verifier: "v1_resolver.js",
    total: scenarios.length,
    allow: counts[ALLOW],
    hold: counts[HOLD],
    deny: counts[DENY],
    verdicts: verdicts
  };
}

/**
 * CLI: read JSON array of scenarios from stdin, output results
 */
function main() {
  if (process.argv.includes("--help")) {
    console.log("Usage: node v1_resolver.js < scenarios.json");
    console.log("Reads JSON array of evidence scenarios, outputs decisions.");
    process.exit(0);
  }
  
  // Read stdin
  const chunks = [];
  process.stdin.on("data", chunk => chunks.push(chunk));
  
  process.stdin.on("end", () => {
    const input = Buffer.concat(chunks).toString();
    
    let scenarios;
    try {
      scenarios = JSON.parse(input);
    } catch (e) {
      console.error(`Error: invalid JSON input: ${e.message}`);
      process.exit(1);
    }
    
    if (!Array.isArray(scenarios)) {
      console.error("Error: input must be a JSON array");
      process.exit(1);
    }
    
    // Resolve batch
    const result = resolveBatch(scenarios);
    
    // Output JSON
    console.log(JSON.stringify(result, null, 2));
  });
  
  // Handle stdin errors
  process.stdin.on("error", err => {
    console.error(`Error reading stdin: ${err.message}`);
    process.exit(1);
  });
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { resolveScenario, resolveBatch };
