/**
 * ARK-478 V1 Guard (JavaScript)
 * API Rate Limit · Exact-Action Binding
 * 
 * Enforces exact byte-equality across 5 API rate limit dimensions:
 * - database_name, table_name, operation, schema_version, execution_mode
 */

function verifyRateLimit(authorizedQuery, presentedQuery) {
  // Check exact equality on all 5 dimensions
  const databaseMatch = authorizedQuery.database_name === presentedQuery.database_name;
  const tableMatch = authorizedQuery.table_name === presentedQuery.table_name;
  const operationMatch = authorizedQuery.operation === presentedQuery.operation;
  const schemaMatch = authorizedQuery.schema_version === presentedQuery.schema_version;
  const modeMatch = authorizedQuery.execution_mode === presentedQuery.execution_mode;
  
  const allMatch = databaseMatch && tableMatch && operationMatch && schemaMatch && modeMatch;
  
  if (allMatch) {
    return {
      decision: "ALLOW",
      reason: "Exact match on all 5 dimensions"
    };
  } else {
    const mismatches = [];
    if (!databaseMatch) mismatches.push("database_name");
    if (!tableMatch) mismatches.push("table_name");
    if (!operationMatch) mismatches.push("operation");
    if (!schemaMatch) mismatches.push("schema_version");
    if (!modeMatch) mismatches.push("execution_mode");
    
    return {
      decision: "DENY",
      reason: `Mismatch on: ${mismatches.join(", ")}`
    };
  }
}

module.exports = { verifyRateLimit };
