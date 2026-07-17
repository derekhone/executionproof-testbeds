#!/usr/bin/env node
/**
 * ARK-450 V1 Guard (JavaScript)
 * Independent implementation - zero dependencies
 * Tests exact action matching: authorization for A cannot be used for B
 */

/**
 * Deep equality check for two objects
 * Returns true only if ALL fields match exactly
 */
function deepEqual(obj1, obj2) {
  if (obj1 === obj2) return true;
  
  if (obj1 == null || obj2 == null) return false;
  if (typeof obj1 !== 'object' || typeof obj2 !== 'object') return false;
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  if (keys1.length !== keys2.length) return false;
  
  for (const key of keys1) {
    if (!keys2.includes(key)) return false;
    if (!deepEqual(obj1[key], obj2[key])) return false;
  }
  
  return true;
}

/**
 * ARK-450 Decision Function
 * 
 * Logic: Authorization proof for approved_action can ONLY be used for
 * an executed_action that matches EXACTLY in ALL fields.
 * 
 * @param {Object} scenario - Contains approved_action and executed_action
 * @returns {string} - "ALLOW" if exact match, "DENY" if any field differs
 */
function decide(scenario) {
  const approved = scenario.approved_action;
  const executed = scenario.executed_action;
  
  // Exact equality check across all fields
  if (deepEqual(approved, executed)) {
    return "ALLOW";
  } else {
    return "DENY";
  }
}

/**
 * Process a single scenario and return decision
 */
function processScenario(scenario) {
  const decision = decide(scenario);
  
  return {
    scenario_id: scenario.scenario_id,
    arm_id: scenario.arm_id,
    substitution_type: scenario.substitution_type,
    decision: decision,
    verifier: "v1_js"
  };
}

/**
 * Process all scenarios from stdin or file
 */
function main() {
  const fs = require('fs');
  
  // Read scenarios from stdin or file argument
  let input = '';
  
  if (process.argv[2]) {
    // File provided as argument
    input = fs.readFileSync(process.argv[2], 'utf8');
  } else {
    // Read from stdin (for piping)
    input = fs.readFileSync(0, 'utf8');
  }
  
  const scenarios = JSON.parse(input);
  
  console.error(`V1 Guard (JavaScript) - Processing ${scenarios.length} scenarios`);
  
  const results = scenarios.map(processScenario);
  
  // Output results as JSON
  console.log(JSON.stringify(results, null, 2));
  
  // Statistics to stderr
  const allow_count = results.filter(r => r.decision === "ALLOW").length;
  const deny_count = results.filter(r => r.decision === "DENY").length;
  
  console.error(`V1 Results: ${allow_count} ALLOW, ${deny_count} DENY`);
}

// Run if called directly
if (require.main === module) {
  main();
}

// Export for testing
module.exports = { decide, deepEqual, processScenario };
