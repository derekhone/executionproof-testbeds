#!/usr/bin/env python3
"""
ExecutionProof Authority Engine (reference measurement implementation).

Answers the AUTHORITY half of Verification-Before-Execution:
  "Does this principal CURRENTLY hold the authority they are claiming,
   at the moment of execution — not merely at approval time?"

This is a deliberately minimal, in-process reference implementation built to
MEASURE component performance (ARK-487..491). It is NOT the production
Authority Engine; a production engine (persistent store, replication, external
IdP integration) is out of scope for these performance testbeds and belongs to
a governed customer integration.

Design (honest and bounded):
  - Grants are held in an in-memory index: principal_id -> dict of grant tuples.
  - A grant tuple is (role, account, permission_set, condition).
  - A separate revocation set holds grant keys revoked as of "now" (current state).
  - check_authority() performs:
      1. principal lookup (dict)
      2. grant-tuple membership test (set)
      3. current-state revocation test (set)  <-- the VBE "now" check
    and returns ALLOW only if the grant exists AND is not currently revoked.

No normalization, no case folding, no subset reasoning — exact, fail-closed.
Mirrors the discipline of the ARK-458 guard, applied to authority state.
"""
from typing import Dict, Any, Tuple, Set

GrantKey = Tuple[str, str, str, str]  # (role, account, permission_set, condition)


class AuthorityEngine:
    def __init__(self) -> None:
        # principal_id -> set of active GrantKey
        self._grants: Dict[str, Set[GrantKey]] = {}
        # set of (principal_id, GrantKey) revoked as of current state
        self._revoked: Set[Tuple[str, GrantKey]] = set()

    def grant(self, principal_id: str, key: GrantKey) -> None:
        self._grants.setdefault(principal_id, set()).add(key)

    def revoke(self, principal_id: str, key: GrantKey) -> None:
        self._revoked.add((principal_id, key))

    def check_authority(self, principal_id: str, key: GrantKey) -> Dict[str, Any]:
        held = self._grants.get(principal_id)
        if held is None:
            return {"decision": "DENY", "reason": f"No grants for principal {principal_id!r}"}
        if key not in held:
            return {"decision": "DENY", "reason": "Principal does not hold the claimed authority"}
        if (principal_id, key) in self._revoked:
            return {"decision": "DENY", "reason": "Authority revoked as of current state (VBE now-check)"}
        return {"decision": "ALLOW", "reason": "Principal currently holds the claimed authority"}


def build_reference_engine(n_principals: int = 1000, grants_per_principal: int = 10) -> "AuthorityEngine":
    """Populate a deterministic reference engine for measurement."""
    eng = AuthorityEngine()
    for p in range(n_principals):
        pid = f"user-{p:05d}"
        for g in range(grants_per_principal):
            key = (f"role-{g}", f"acct-{p % 100:03d}",
                   f"arn:aws:svc:::res-{g}", f"cond-{g}")
            eng.grant(pid, key)
    # Revoke a deterministic slice to exercise the current-state path
    for p in range(0, n_principals, 50):
        eng.revoke(f"user-{p:05d}", ("role-0", f"acct-{p % 100:03d}",
                                     "arn:aws:svc:::res-0", "cond-0"))
    return eng
