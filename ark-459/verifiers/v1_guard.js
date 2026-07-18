#!/usr/bin/env node
/*
 * ARK-459 V1 Guard (JavaScript) — Cloud IAM Role Grant · Revocation At Execution.
 *
 * Decision logic at t_execution (re-check at moment of grant attempt):
 *   1. If revocation is null → ALLOW (authority valid throughout)
 *   2. Compute eff = t_revoke + propagation_delay
 *   3. If reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
 *   4. Else if eff ≤ t_execution → DENY (revoked before execution, fail-closed)
 *   5. Else if t_revoke ≤ t_execution < eff → HOLD (in-flight, fail-safe)
 *   6. Else (t_revoke > t_execution) → ALLOW (revoked after execution)
 *
 * Independent re-implementation of the same procedure as v2_guard.py.
 */
"use strict";

function evaluate(scenario) {
  const t_execution = scenario.execution.t_execution;
  const revocation = scenario.revocation || null;
  const reauth = scenario.reauthorization || null;
  
  // Rule 1: No revocation → ALLOW
  if (revocation === null) {
    return {
      decision: "ALLOW",
      reason: "Authority valid throughout (no revocation)"
    };
  }
  
  const t_revoke = revocation.t_revoke;
  const propagation_delay = revocation.propagation_delay;
  const eff = t_revoke + propagation_delay;
  
  // Rule 3: Reauth exists, valid, and t_revoke < t_reauth ≤ t_execution → ALLOW
  if (reauth !== null && reauth.valid === true) {
    const t_reauth = reauth.t_reauth;
    if (t_revoke < t_reauth && t_reauth <= t_execution) {
      return {
        decision: "ALLOW",
        reason: `Reauthorized at t=${t_reauth.toFixed(3)} (after revoke t=${t_revoke.toFixed(3)}, before execution t=${t_execution.toFixed(3)})`
      };
    }
  }
  
  // Rule 4: eff ≤ t_execution → DENY (revoked before execution)
  if (eff <= t_execution) {
    return {
      decision: "DENY",
      reason: `Authority revoked before execution (eff=${eff.toFixed(3)} ≤ t_exec=${t_execution.toFixed(3)}); ${revocation.reason || "no-reason"}`
    };
  }
  
  // Rule 5: t_revoke ≤ t_execution < eff → HOLD (in-flight)
  if (t_revoke <= t_execution && t_execution < eff) {
    return {
      decision: "HOLD",
      reason: `Revocation in-flight at execution (t_revoke=${t_revoke.toFixed(3)}, t_exec=${t_execution.toFixed(3)}, eff=${eff.toFixed(3)}); cannot confirm validity`
    };
  }
  
  // Rule 6: t_revoke > t_execution → ALLOW (revoked after execution)
  if (t_revoke > t_execution) {
    return {
      decision: "ALLOW",
      reason: `Revoked after execution (t_revoke=${t_revoke.toFixed(3)} > t_exec=${t_execution.toFixed(3)}); authority was valid at contact`
    };
  }
  
  // Fallback (should not reach here if logic is exhaustive)
  return {
    decision: "HOLD",
    reason: "Unexpected timeline state (logic gap)"
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
