# Tempo Local Debugging Guide

## Current Issue
Tempo dashboard showing "No data" and console errors with `$_rate_interval` variable parsing.

## Root Causes to Investigate

### 1. Tempo Dashboard Query Syntax Error
**Error:** "Error: parse error at line 8, col 56: not a valid duration string: `$_rate_interval`"
**Issue:** Tempo dashboard panels are using `$_rate_interval` which is a Prometheus variable, not valid for Tempo
**Location:** `grafana/dashboards/tempo-distributed-tracing.json`

### 2. Tempo Datasource Configuration
**Possible Issues:**
- Datasource URL incorrect
- Tempo not receiving traces
- Tempo frontend worker misconfiguration

### 3. Tempo Service Connectivity
**Possible Issues:**
- Tempo not starting properly
- Port conflicts
- Volume mount issues

## Local Testing Steps

### Step 1: Clean Start
```bash
cd /Users/manjeshprasad/Desktop/November_24_2025_GatewayZ/railway-grafana-stack

# Stop all containers
docker-compose down

# Remove volumes to start fresh
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

### Step 2: Start Services with Logging
```bash
# Start with verbose output
docker-compose up

# In another terminal, monitor Tempo logs
docker-compose logs -f tempo
```

### Step 3: Verify Tempo is Running
```bash
# Check Tempo health endpoint
curl http://localhost:3200/status

# Expected response:
# {"status":"ok"}
```

### Step 4: Check Tempo Receivers
```bash
# Verify OTLP gRPC receiver
curl -v http://localhost:4317/

# Verify OTLP HTTP receiver
curl -v http://localhost:4318/

# Both should be listening (connection refused is OK, means port is listening)
```

### Step 5: Verify Grafana Datasource
1. Open Grafana: `http://localhost:3000`
2. Go to **Configuration → Data Sources**
3. Click **Tempo**
4. Verify URL shows: `http://tempo:3200`
5. Click **Save & Test**
6. Check for "Data source is working" message

### Step 6: Check Tempo Dashboard Queries
1. Go to **Dashboards → Tempo Distributed Tracing**
2. Open browser console (F12)
3. Look for query errors
4. Check if panels are using `$_rate_interval` (invalid for Tempo)

## Tempo Dashboard Query Issues

The Tempo dashboard likely has queries using Prometheus variables. Check `grafana/dashboards/tempo-distributed-tracing.json` for:

**Invalid patterns:**
- `$__rate_interval` - Prometheus only
- `rate()` function - Prometheus only
- `increase()` function - Prometheus only

**Valid Tempo queries:**
- `{service.name="<service>"}` - Search by service
- `{span.http.status_code=500}` - Search by span attributes
- `{resource.service.name="<service>"}` - Search by resource

## Quick Fixes to Try

### Fix 1: Verify Tempo Configuration
Check if `frontend_address: 0.0.0.0:3200` is correct. Try changing to:
```yaml
querier:
  frontend_worker:
    frontend_address: tempo:3200  # Use service name instead
```

### Fix 2: Simplify Tempo Dashboard
If dashboard queries are complex, simplify them:
- Remove `$_rate_interval` references
- Use simple trace search queries
- Remove metric-based panels from Tempo dashboard

### Fix 3: Check Docker Network
```bash
# Verify services can communicate
docker-compose exec grafana ping tempo
docker-compose exec tempo ping grafana

# Both should succeed
```

### Fix 4: Check Tempo Logs
```bash
docker-compose logs tempo | grep -i error
docker-compose logs tempo | grep -i "frontend"
```

## Expected Behavior

### When Tempo is Working Correctly:
1. Tempo health endpoint returns `{"status":"ok"}`
2. Grafana datasource shows "Data source is working"
3. Tempo dashboard loads without console errors
4. Trace search works (even if no traces exist)
5. Logs show no errors about frontend connectivity

### When Traces are Being Received:
1. Tempo logs show OTLP spans being received
2. Dashboard panels show data
3. Trace search returns results

## Debugging Commands

```bash
# Check Tempo container status
docker ps | grep tempo

# View Tempo logs
docker-compose logs tempo

# Check Tempo resource usage
docker stats tempo

# Verify Tempo port bindings
docker port tempo

# Check if Tempo is listening on ports
netstat -an | grep 3200
netstat -an | grep 4317
netstat -an | grep 4318

# Test Tempo API
curl -s http://localhost:3200/api/traces | jq .

# Test OTLP HTTP endpoint
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/protobuf" \
  -d ""
```

## Common Issues and Solutions

### Issue: "connection error: desc = \"error reading server preface: http2: frame too large"
**Cause:** HTTP/2 frame size mismatch
**Status:** Non-blocking - Tempo still functions
**Solution:** Already configured with `grpc_server_max_recv_msg_size: 16777216`

### Issue: "Error contacting frontend"
**Cause:** Frontend worker can't reach frontend on `0.0.0.0:3200`
**Solution:** Change `frontend_address` to `tempo:3200` (service name)

### Issue: "No data" in Tempo dashboard
**Cause:** 
1. No traces being sent
2. Dashboard queries invalid
3. Datasource URL incorrect
**Solution:**
- Verify backend is sending traces
- Fix dashboard queries (remove Prometheus variables)
- Verify datasource URL is `http://tempo:3200`

## Next Steps

1. **Run locally with `docker-compose up`**
2. **Check Tempo health: `curl http://localhost:3200/status`**
3. **Verify Grafana datasource connection**
4. **Check Tempo dashboard for query errors**
5. **Review Tempo logs for errors**
6. **Fix dashboard queries if needed**
7. **Test with sample traces once working**

## Files to Check/Modify

- `tempo/tempo.yml` - Tempo configuration
- `grafana/dashboards/tempo-distributed-tracing.json` - Dashboard queries
- `grafana/datasources/datasources.yml` - Datasource configuration
- `docker-compose.yml` - Service configuration

## Do NOT Push to Main

Keep all local changes in working directory. Once Tempo is working locally:
1. Document the fix
2. Create a separate branch if needed
3. Then push to main

This allows testing before affecting the main branch.
