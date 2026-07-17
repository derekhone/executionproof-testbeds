#!/usr/bin/env python3
"""
Statistical significance test for ARK-447 Pauli twirling improvement.
"""

import scipy.stats as stats

# ARK-447 results
n_shots = 8192

# Baseline configuration
baseline_allow_count = 8048  # Payload '1' outcomes
baseline_s_a = baseline_allow_count / n_shots

# Pauli twirling configuration
twirling_allow_count = 8090  # Payload '1' outcomes
twirling_s_a = twirling_allow_count / n_shots

# Difference
diff = twirling_s_a - baseline_s_a
count_diff = twirling_allow_count - baseline_allow_count

print("=" * 70)
print("ARK-447 Statistical Significance Test")
print("=" * 70)
print()
print("Configuration Comparison:")
print(f"  Baseline:        {baseline_allow_count}/{n_shots} = {baseline_s_a:.4f}")
print(f"  Pauli Twirling:  {twirling_allow_count}/{n_shots} = {twirling_s_a:.4f}")
print(f"  Difference:      {count_diff} shots = {diff:.4f}")
print()

# Two-proportion z-test (two-sided)
# H0: p_baseline = p_twirling
# H1: p_baseline ≠ p_twirling

# Pooled proportion
pooled_p = (baseline_allow_count + twirling_allow_count) / (2 * n_shots)
pooled_se = (pooled_p * (1 - pooled_p) * (1/n_shots + 1/n_shots)) ** 0.5

z_stat = (twirling_s_a - baseline_s_a) / pooled_se
p_value_two_sided = 2 * (1 - stats.norm.cdf(abs(z_stat)))

print("Two-Proportion Z-Test (two-sided):")
print(f"  Pooled proportion: {pooled_p:.4f}")
print(f"  Pooled SE:         {pooled_se:.6f}")
print(f"  Z-statistic:       {z_stat:.4f}")
print(f"  P-value:           {p_value_two_sided:.4f}")
print()

if p_value_two_sided < 0.05:
    print("  ✅ Result: STATISTICALLY SIGNIFICANT at α=0.05")
    print("     The improvement is unlikely to be due to chance.")
else:
    print("  ❌ Result: NOT statistically significant at α=0.05")
    print("     The improvement may be due to random variation.")
print()

# One-sided test (improvement direction)
p_value_one_sided = 1 - stats.norm.cdf(z_stat)
print("One-Sided Z-Test (twirling > baseline):")
print(f"  P-value:           {p_value_one_sided:.4f}")
if p_value_one_sided < 0.05:
    print("  ✅ Result: STATISTICALLY SIGNIFICANT at α=0.05")
else:
    print("  ❌ Result: NOT statistically significant at α=0.05")
print()

# 95% Confidence interval for the difference
# Using normal approximation
se_baseline = (baseline_s_a * (1 - baseline_s_a) / n_shots) ** 0.5
se_twirling = (twirling_s_a * (1 - twirling_s_a) / n_shots) ** 0.5
se_diff = (se_baseline**2 + se_twirling**2) ** 0.5

ci_lower = diff - 1.96 * se_diff
ci_upper = diff + 1.96 * se_diff

print("95% Confidence Interval for Difference:")
print(f"  Difference: {diff:.4f}")
print(f"  SE:         {se_diff:.6f}")
print(f"  95% CI:     [{ci_lower:.4f}, {ci_upper:.4f}]")
print()

if ci_lower > 0:
    print("  ✅ CI excludes zero → improvement is statistically significant")
else:
    print("  ❌ CI includes zero → improvement not statistically significant")
print()

print("=" * 70)
print("Conclusion:")
print("=" * 70)
if p_value_two_sided < 0.05:
    print("The +0.0051 improvement in S_A is STATISTICALLY SIGNIFICANT.")
    print("We can reject the null hypothesis that the two configurations")
    print("have the same success rate (p < 0.05).")
else:
    print("The +0.0051 improvement in S_A is NOT statistically significant.")
    print("We cannot reject the null hypothesis that the two configurations")
    print("have the same success rate (p > 0.05).")
    print()
    print("The observed improvement may be due to random variation.")
    print("More conservative language should be used: 'modest improvement'")
    print("or 'marginal improvement' rather than 'statistically measurable'.")
print("=" * 70)
