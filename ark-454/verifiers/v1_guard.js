#!/usr/bin/env node
/**
 * ARK-454 Guard V1 (JavaScript/Node.js)
 * Independent authorization-graph guard per preregistration Section 4.3.
 *
 * ISOLATION NOTICE: built solely from the ARK-454 prose specification; does not
 * reference Guard V2 (Python), the scenario generator, or any other implementation.
 *
 * The doctrine under test: an action may be ALLOWed only when a genuinely
 * independent principal approves it. The guard must fail closed (DENY, or HOLD
 * when independence cannot be established) whenever the approving authority
 * reduces -- directly or transitively -- to the requester.
 *
 * Decision procedure (evaluate rules in order; return the FIRST that fires;
 * DENY precedes HOLD precedes ALLOW):
 *   1. Direct self-approval:        approver === requester                     -> DENY
 *   2. Controlled / shared control: requester and approver share control       -> DENY
 *   3. Circular delegation:         a principal repeats in delegation_chain     -> DENY
 *   4. Delegation-to-self:          requester in chain, or a chain principal is
 *                                   controlled (transitively) by the requester  -> DENY
 *   5. Inherited self-initiated wf: authority_source === 'parent_workflow' and
 *                                   confers_authority and initiator === requester -> DENY
 *   6. Independence unverifiable:   controller_of(approver) === 'UNKNOWN', or
 *                                   approver absent from identities              -> HOLD
 *   7. Otherwise                                                                -> ALLOW
 */

'use strict';

const UNKNOWN = 'UNKNOWN';

function controllerOf(pid, identities) {
  const entry = identities ? identities[pid] : undefined;
  if (!entry || typeof entry !== 'object') {
    return null;
  }
  return Object.prototype.hasOwnProperty.call(entry, 'controller') ? entry.controller : null;
}

/**
 * Transitive set of controllers of `pid`, stopping at null / UNKNOWN / repeat.
 * Returned as a Set of principal ids.
 */
function controllersClosure(pid, identities) {
  const seen = new Set();
  let cur = controllerOf(pid, identities);
  let guard = 0;
  while (cur !== null && cur !== undefined && cur !== UNKNOWN && !seen.has(cur) && guard < 1000) {
    seen.add(cur);
    cur = controllerOf(cur, identities);
    guard += 1;
  }
  return seen;
}

function intersects(setA, setB) {
  for (const x of setA) {
    if (setB.has(x)) {
      return true;
    }
  }
  return false;
}

function evaluate(scenario) {
  try {
    const requester = scenario.requester;
    const approver = scenario.approver;
    const identities = scenario.identities || {};
    const chain = Array.isArray(scenario.delegation_chain) ? scenario.delegation_chain : [];
    const authoritySource = scenario.authority_source || 'independent';
    const parentWorkflow = scenario.parent_workflow || null;

    // Rule 1: direct self-approval
    if (approver === requester) {
      return 'DENY';
    }

    // Rule 2: controlled identity / shared controller
    const cR = controllersClosure(requester, identities);
    const cA = controllersClosure(approver, identities);
    if (cA.has(requester) || cR.has(approver) || intersects(cR, cA)) {
      return 'DENY';
    }

    // Rule 3: circular delegation (a principal repeats)
    if (new Set(chain).size !== chain.length) {
      return 'DENY';
    }

    // Rule 4: delegation-to-self
    if (chain.indexOf(requester) !== -1) {
      return 'DENY';
    }
    for (const p of chain) {
      if (controllersClosure(p, identities).has(requester)) {
        return 'DENY';
      }
    }

    // Rule 5: inherited self-initiated workflow authority
    if (authoritySource === 'parent_workflow' && parentWorkflow && typeof parentWorkflow === 'object') {
      if (parentWorkflow.confers_authority === true && parentWorkflow.initiator === requester) {
        return 'DENY';
      }
    }

    // Rule 6: independence unverifiable
    if (controllerOf(approver, identities) === UNKNOWN
        || !Object.prototype.hasOwnProperty.call(identities, approver)) {
      return 'HOLD';
    }

    // Rule 7: independent approval
    return 'ALLOW';

  } catch (e) {
    // Fail closed on malformed input: cannot establish independence.
    return 'HOLD';
  }
}

function batchEvaluate(scenarios) {
  let allow = 0;
  let hold = 0;
  let deny = 0;
  const verdicts = [];
  for (const s of scenarios) {
    const v = evaluate(s);
    verdicts.push(v);
    if (v === 'ALLOW') {
      allow++;
    } else if (v === 'HOLD') {
      hold++;
    } else {
      deny++;
    }
  }
  return {
    verifier: 'V1-JavaScript',
    total: scenarios.length,
    allow,
    hold,
    deny,
    verdicts,
  };
}

// CLI interface
if (require.main === module) {
  const fs = require('fs');
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node v1_guard.js <scenarios.json>');
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(args[0], 'utf8'));
  const scenarios = Array.isArray(data) ? data : [data];
  const result = batchEvaluate(scenarios);
  if (scenarios.length === 1) {
    result.verdict = result.verdicts[0];
  }
  console.log(JSON.stringify(result, null, 2));
}

module.exports = { evaluate, batchEvaluate };
