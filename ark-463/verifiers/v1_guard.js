/**
 * ARK-463 V1 Guard (JavaScript)
 * Production Deployment · Exact-Action Binding
 * 
 * Enforces exact byte-equality across all 5 deployment tuple dimensions.
 * No normalization, no fuzzy matching.
 */

function verifyDeployment(authorized, presented) {
  // Exact string equality on all 5 dimensions
  const serviceMatch = authorized.service_name === presented.service_name;
  const environmentMatch = authorized.environment === presented.environment;
  const versionMatch = authorized.version === presented.version;
  const regionMatch = authorized.region === presented.region;
  const methodMatch = authorized.deployment_method === presented.deployment_method;
  
  if (serviceMatch && environmentMatch && versionMatch && regionMatch && methodMatch) {
    return {
      decision: "ALLOW",
      reason: "All 5 deployment dimensions match exactly"
    };
  }
  
  // Build detailed mismatch reason
  const mismatches = [];
  if (!serviceMatch) mismatches.push(`service_name: '${authorized.service_name}' vs '${presented.service_name}'`);
  if (!environmentMatch) mismatches.push(`environment: '${authorized.environment}' vs '${presented.environment}'`);
  if (!versionMatch) mismatches.push(`version: '${authorized.version}' vs '${presented.version}'`);
  if (!regionMatch) mismatches.push(`region: '${authorized.region}' vs '${presented.region}'`);
  if (!methodMatch) mismatches.push(`deployment_method: '${authorized.deployment_method}' vs '${presented.deployment_method}'`);
  
  return {
    decision: "DENY",
    reason: `Deployment tuple mismatch: ${mismatches.join("; ")}`
  };
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { verifyDeployment };
}
