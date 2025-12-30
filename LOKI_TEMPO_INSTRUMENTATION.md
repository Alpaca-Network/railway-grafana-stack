# Loki & Tempo Instrumentation Endpoints

## Overview

This document describes the real instrumentation endpoints used to populate Loki with logs and Tempo with traces. These are NOT mock data - they are actual API endpoints on the GatewayZ backend.

## Instrumentation Endpoints

### Health & Status Checks (GET)

**1. Health Check**
```bash
GET /api/instrumentation/health
```
- Purpose: Verify instrumentation system is operational
- Headers: `Authorization: Bearer {API_KEY}`
- Response: System health status
- Expected: HTTP 200

**2. Loki Status**
```bash
GET /api/instrumentation/loki/status
```
- Purpose: Check if Loki is connected and accepting logs
- Headers: `Authorization: Bearer {API_KEY}`
- Response: Loki connectivity status
- Expected: HTTP 200

**3. Tempo Status**
```bash
GET /api/instrumentation/tempo/status
```
- Purpose: Check if Tempo is connected and accepting traces
- Headers: `Authorization: Bearer {API_KEY}`
- Response: Tempo connectivity status
- Expected: HTTP 200

**4. Trace Context**
```bash
GET /api/instrumentation/trace-context
```
- Purpose: Retrieve current trace context for debugging
- Headers: `Authorization: Bearer {API_KEY}`
- Response: Active trace information
- Expected: HTTP 200

### Log Ingestion (POST)

**Test Log Endpoint**
```bash
POST /api/instrumentation/test-log
Authorization: Bearer {API_KEY}
Content-Type: application/json

{
  "message": "Log message text",
  "level": "info|warn|error|debug",
  "service": "service-name",
  "timestamp": "2025-12-29T14:30:00Z"
}
```

**Response:**
```json
{
  "status": "logged",
  "trace_id": "unique-trace-id",
  "timestamp": "2025-12-29T14:30:00Z"
}
```

**Log Levels:**
- `debug` - Detailed diagnostic information
- `info` - General informational messages
- `warn` - Warning messages for potential issues
- `error` - Error messages for failures

**Service Names:**
- `gatewayz-api` - Main API service
- `gatewayz-inference` - Model inference service
- `gatewayz-gateway` - Provider gateway service
- `gatewayz-monitoring` - Monitoring service

### Trace Ingestion (POST)

**Test Trace Endpoint**
```bash
POST /api/instrumentation/test-trace
Authorization: Bearer {API_KEY}
Content-Type: application/json

{
  "operation": "operation_name",
  "service": "service-name",
  "duration_ms": 150
}
```

**Response:**
```json
{
  "status": "traced",
  "trace_id": "unique-trace-id",
  "span_id": "unique-span-id",
  "duration_ms": 150
}
```

**Operation Examples:**
- `chat_completion_inference` - LLM inference operation
- `provider_gateway_request` - Provider request
- `cache_lookup` - Redis cache query
- `database_query` - Database operation
- `auth_validate` - Authentication check

---

## Testing With Real Endpoints

### Automated Testing Script

Use `scripts/test_loki_instrumentation.sh` to test all instrumentation endpoints:

```bash
chmod +x scripts/test_loki_instrumentation.sh
./scripts/test_loki_instrumentation.sh "YOUR_API_KEY" "https://api.gatewayz.ai"
```

**Script Flow:**
1. ✅ Checks instrumentation health
2. ✅ Verifies Loki connectivity
3. ✅ Sends 5 test logs with real payloads (dynamic timestamps)
4. ✅ Sends 3 test traces with real payloads (random durations)
5. ✅ Reports success/failure for each operation

**Expected Output:**
```
🚀 Testing Loki with REAL Instrumentation Endpoints
==================================================
Base URL: https://api.gatewayz.ai

1️⃣  Checking Instrumentation Health...
[Health check response]

2️⃣  Checking Loki Status...
[Loki status response]

3️⃣  Sending REAL test logs to Loki...
Sending test log #1...
[Response]
...

4️⃣  Sending Real Test Traces to Tempo...
Sending test trace #1...
[Response]
...

✅ Real instrumentation test complete
```

### Manual cURL Commands

**Health Check**
```bash
curl -s -X GET "https://api.gatewayz.ai/api/instrumentation/health" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" | jq '.'
```

**Send Single Log**
```bash
curl -s -X POST "https://api.gatewayz.ai/api/instrumentation/test-log" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test log from manual testing",
    "level": "info",
    "service": "gatewayz-api",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }' | jq '.'
```

**Send Single Trace**
```bash
curl -s -X POST "https://api.gatewayz.ai/api/instrumentation/test-trace" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "test_operation",
    "service": "gatewayz-api",
    "duration_ms": '$((RANDOM % 500 + 50))
  }' | jq '.'
```

---

## Verifying Logs in Loki

After sending test logs:

1. **Wait 5-10 seconds** for logs to propagate through the ingestion pipeline
2. **Go to Grafana → Explore**
3. **Select Loki datasource**
4. **Run query** to find your logs:
   ```logql
   {service="gatewayz-api"}
   ```
5. **Expected results**: Should see the test logs you just sent

### Common LogQL Queries

```logql
# All logs from gatewayz-api service
{service="gatewayz-api"}

# Only error level logs
{service="gatewayz-api"} | json | level="error"

# Logs containing "Real Instrumentation"
{service="gatewayz-api"} | "Real Instrumentation"

# Last 100 logs
{service="gatewayz-api"} | tail(100)

# Logs from last 5 minutes
{service="gatewayz-api"} | since(5m)
```

---

## Verifying Traces in Tempo

After sending test traces:

1. **Wait 5-10 seconds** for traces to propagate
2. **Go to Grafana → Explore**
3. **Select Tempo datasource**
4. **Search by attributes**:
   - Service: `gatewayz-api`
   - Operation: `test_operation_*`
5. **Expected results**: Should see trace spans with duration metrics

---

## Authentication

All endpoints require Bearer token authentication:

```bash
Authorization: Bearer {API_KEY}
```

Where `{API_KEY}` is your GatewayZ API key. Set it as an environment variable:

```bash
export GATEWAYZ_API_KEY="your-actual-api-key"
./scripts/test_loki_instrumentation.sh "$GATEWAYZ_API_KEY"
```

---

## Important Notes

✅ **These are REAL endpoints** - not mock data or hardcoded responses
✅ **Dynamic data** - logs use current timestamps, traces use random durations
✅ **Real services** - logs sent with actual service names
✅ **Production-ready** - can be used for integration testing

⚠️ **API Key Required** - Keep your API key secure
⚠️ **Rate Limits** - Check with GatewayZ API documentation
⚠️ **Data Retention** - Logs/traces retained per Loki/Tempo configuration

---

## Troubleshooting

### Logs Not Appearing in Grafana

1. **Check health**: Run `./scripts/test_loki_instrumentation.sh "$API_KEY"`
2. **Check Loki status**: GET `/api/instrumentation/loki/status`
3. **Verify service name**: Make sure you're querying `{service="gatewayz-api"}`
4. **Check timestamps**: Use recent time range (last 10 minutes)
5. **Wait for propagation**: Logs may take 5-10 seconds to appear

### API Key Issues

```bash
# Verify API key is set
echo $GATEWAYZ_API_KEY

# Test authentication
curl -X GET "https://api.gatewayz.ai/api/instrumentation/health" \
  -H "Authorization: Bearer $GATEWAYZ_API_KEY" -w "\n%{http_code}\n"

# Should return HTTP 200, not 401/403
```

### Connection Errors

```bash
# Test endpoint connectivity
curl -I "https://api.gatewayz.ai/api/instrumentation/health"

# Check if API is reachable
ping api.gatewayz.ai
```

---

## Related Documentation

- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Full testing procedures
- [ENDPOINT_VERIFICATION_REPORT.md](./ENDPOINT_VERIFICATION_REPORT.md) - All endpoints verification
- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Pre-deployment checks
- [claude.md](./claude.md) - Project context and dashboard info

---

**Last Updated:** December 29, 2025
**Status:** ✅ Ready for Production Testing
