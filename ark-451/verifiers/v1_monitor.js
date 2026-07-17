#!/usr/bin/env node
/**
 * ARK-451 V1 Execution Monitor (JavaScript, no external dependencies)
 * Independent implementation of the revocation-during-execution decision
 * procedure. Reads scenarios (JSON array) from stdin, outputs decisions
 * (ALLOW/HOLD/DENY).
 *
 * Decision procedure (re-check authority at the moment of resource contact,
 * t_execution):
 *   1. If there is no revocation -> ALLOW (authority valid throughout).
 *   2. Compute eff = t_revoke + propagation_delay (revocation fully effective).
 *   3. If a VALID re-authorization was issued after the revoke and at/before
 *      execution -> ALLOW (a new, independent decision governs).
 *   4. Else if eff <= t_execution -> DENY (authority provably revoked before
 *      resource contact; fail closed).
 *   5. Else if t_revoke <= t_execution < eff -> HOLD (revocation in-flight /
 *      unconfirmed at contact; fail safe).
 *   6. Else (t_revoke > t_execution) -> ALLOW (revocation issued only after the
 *      action already contacted the resource under valid authority).
 */

const ALLOW = "ALLOW";
const HOLD = "HOLD";
const DENY = "DENY";

function resolveScenario(scenario) {
  const tExec = scenario.t_execution;
  const rev = scenario.revocation;
  const reauth = scenario.reauthorization;

  // Rule 1: no revocation -> authority valid throughout
  if (rev === null || rev === undefined) {
    return ALLOW;
  }

  const eff = rev.t_revoke + rev.propagation_delay;

  // Rule 3: valid re-authorization after revoke and at/before execution
  if (reauth !== null && reauth !== undefined && reauth.valid === true
      && reauth.t_reauth > rev.t_revoke && reauth.t_reauth <= tExec) {
    return ALLOW;
  }

  // Rule 4: revocation provably effective before resource contact -> fail closed
  if (eff <= tExec) {
    return DENY;
  }

  // Rule 5: revocation in-flight at contact -> HOLD
  if (rev.t_revoke <= tExec && tExec < eff) {
    return HOLD;
  }

  // Rule 6: revocation issued only after execution -> ALLOW
  return ALLOW;
}

function resolveBatch(scenarios) {
  const verdicts = [];
  const counts = { [ALLOW]: 0, [HOLD]: 0, [DENY]: 0 };
  for (const scenario of scenarios) {
    const decision = resolveScenario(scenario);
    verdicts.push({ scenario_id: scenario.scenario_id, decision: decision });
    counts[decision]++;
  }
  return {
    verifier: "v1_monitor.js",
    total: scenarios.length,
    allow: counts[ALLOW],
    hold: counts[HOLD],
    deny: counts[DENY],
    verdicts: verdicts,
  };
}

function main() {
  if (process.argv.includes("--help")) {
    console.log("Usage: node v1_monitor.js < scenarios.json");
    console.log("Reads JSON array of revocation scenarios, outputs decisions.");
    process.exit(0);
  }

  const chunks = [];
  process.stdin.on("data", (chunk) => chunks.push(chunk));
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
    const result = resolveBatch(scenarios);
    console.log(JSON.stringify(result, null, 2));
  });
  process.stdin.on("error", (err) => {
    console.error(`Error reading stdin: ${err.message}`);
    process.exit(1);
  });
}

if (require.main === module) {
  main();
}

module.exports = { resolveScenario, resolveBatch };
