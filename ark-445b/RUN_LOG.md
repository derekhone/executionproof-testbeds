# ARK-445b — RUN LOG
Remnant Fieldworks Inc. — Derek Hone

Tri-State Authorization Discrimination (ALLOW / HOLD / DENY) on ibm_marrakesh (Heron r2).

## Principal 9-arm job
- **Backend:** ibm_marrakesh
- **Instance:** open-instance
- **Physical qubits [Q_A, Q_P]:** [2, 1]
- **Shots per arm:** 8192
- **Arms:** 9 (arm1_allow_standard, arm2_deny_standard, arm3_hold_plus, arm4_hold_minus, arm5_allow_alt, arm6_deny_alt, arm7_allow_reverified, arm8_deny_expired, arm9_spam_idle)
- **Arm expectations:** {'arm1_allow_standard': 'ALLOW', 'arm2_deny_standard': 'DENY', 'arm3_hold_plus': 'HOLD', 'arm4_hold_minus': 'HOLD', 'arm5_allow_alt': 'ALLOW', 'arm6_deny_alt': 'DENY', 'arm7_allow_reverified': 'ALLOW', 'arm8_deny_expired': 'DENY', 'arm9_spam_idle': 'SPAM'}
- **Arm classes:** {'arm1_allow_standard': 'allow', 'arm2_deny_standard': 'deny', 'arm3_hold_plus': 'hold', 'arm4_hold_minus': 'hold', 'arm5_allow_alt': 'allow', 'arm6_deny_alt': 'deny', 'arm7_allow_reverified': 'allow', 'arm8_deny_expired': 'deny', 'arm9_spam_idle': 'idle_spam'}
- **Optimization level:** 3 (seed_transpiler=445, no dynamical decoupling)
- **JOB ID:** `d9couv9htsac739c230g`
- **Submission timestamp (UTC):** 2026-07-17T02:12:12.144504+00:00
- **SPAM job id:** `d9counkinv1c73ao2vng`
- **SPAM baselines:** SPAM_A=0.0007, SPAM_P=0.0012, drift=0.0005
- **Transpiled depths:** {'arm1_allow_standard': 4, 'arm2_deny_standard': 3, 'arm3_hold_plus': 6, 'arm4_hold_minus': 6, 'arm5_allow_alt': 4, 'arm6_deny_alt': 3, 'arm7_allow_reverified': 5, 'arm8_deny_expired': 4, 'arm9_spam_idle': 1}
