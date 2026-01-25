# Prometheus → Mimir Connection Issues - Quick Fixes

## Symptom
"No writes onto Mimir internally" - Prometheus is not sending data to Mimir

---

## Most Likely Causes (in order)

### 1. ❌ Environment Variable Not Set (90% probability)

**Issue**: `RAILWAY_ENVIRONMENT` is not set on the Prometheus service

**Why this matters**: Without this variable, Prometheus uses `http://mimir:9009` (Docker Compose default) instead of `http://mimir.railway.internal:9009` (Railway internal network)

**Fix**:

Railway Dashboard → Prometheus service → Variables → Add:
```
RAILWAY_ENVIRONMENT=production
```

Wait 2-3 minutes for redeploy.

**Verify**:
```bash
railway logs --service prometheus | grep "MIMIR"

# Should see:
# MIMIR_URL: http://mimir.railway.internal:9009
# MIMIR_TARGET: mimir.railway.internal:9009
```

---

### 2. ❌ Services in Different Railway Projects (5% probability)

**Issue**: Prometheus and Mimir are in different Railway projects

**Why this matters**: Railway internal networking (`.railway.internal`) only works within the same project

**Check**:
```bash
# From Prometheus service
railway run --service prometheus -- nslookup mimir.railway.internal

# Should resolve to an IP
# If "server can't find mimir.railway.internal", they're in different projects
```

**Fix**: Move both services to the same Railway project

---

### 3. ❌ Mimir Not Listening on Correct Port (3% probability)

**Issue**: Mimir is not listening on port 9009

**Check Mimir logs**:
```bash
railway logs --service mimir | grep "listening\|started"

# Should see:
# "Server listening on 0.0.0.0:9009"
```

**Fix**: Check `mimir/mimir-railway.yml`:
```yaml
server:
  http_listen_port: 9009
  http_listen_address: 0.0.0.0  # Important: 0.0.0.0, not 127.0.0.1
```

---

### 4. ❌ Mimir Push Endpoint Not Working (2% probability)

**Issue**: Mimir's `/api/v1/push` endpoint returns 404 or 500

**Test from Prometheus**:
```bash
railway run --service prometheus -- curl -X POST http://mimir.railway.internal:9009/api/v1/push

# Should get: HTTP 400 (empty body) or HTTP 200
# Should NOT get: HTTP 404 or connection refused
```

**Fix**: Check Mimir configuration for `distributor` section:
```yaml
distributor:
  pool:
    health_check_ingesters: true
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory  # Important for single-instance
```

---

## Diagnostic Script

Run this to pinpoint the exact issue:

```bash
# From Railway CLI
railway run --service prometheus bash diagnose-prometheus-mimir.sh
```

Or copy the script to the Prometheus container and run it.

**What it checks**:
1. Environment variables (RAILWAY_ENVIRONMENT, MIMIR_INTERNAL_URL)
2. Prometheus configuration (remote_write URL)
3. DNS resolution (can Prometheus find mimir.railway.internal?)
4. TCP connection (can Prometheus connect to port 9009?)
5. HTTP endpoints (/ready, /api/v1/push, /prometheus/api/v1/query)
6. Prometheus remote write metrics

---

## Quick Tests

### Test 1: DNS Resolution
```bash
# From Prometheus service
railway run --service prometheus -- nslookup mimir.railway.internal

# Expected: Resolves to an internal IP (e.g., 10.x.x.x)
# If fails: Services in different projects OR Mimir not running
```

### Test 2: TCP Connection
```bash
# From Prometheus service
railway run --service prometheus -- timeout 5 bash -c 'echo > /dev/tcp/mimir.railway.internal/9009' && echo "Connected" || echo "Failed"

# Expected: "Connected"
# If fails: Mimir not listening on 9009 OR firewall issue
```

### Test 3: HTTP Ready Check
```bash
# From Prometheus service
railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready

# Expected: HTTP 200 OK
# If fails: Mimir not healthy
```

### Test 4: Push Endpoint
```bash
# From Prometheus service
railway run --service prometheus -- curl -X POST http://mimir.railway.internal:9009/api/v1/push

# Expected: HTTP 400 (empty body rejected)
# If 404: Mimir not configured correctly
# If connection refused: Mimir not running
```

### Test 5: Check Prometheus Logs
```bash
railway logs --service prometheus | tail -50

# Look for:
# ✓ "MIMIR_URL: http://mimir.railway.internal:9009"
# ✗ "MIMIR_URL: http://mimir:9009" (wrong - Docker default)
# ✗ Remote write errors
```

### Test 6: Check Prometheus Remote Write Status
```bash
# Prometheus UI: http://prometheus-xxx.railway.app
# Go to: Status → TSDB Status
# Look for: "Remote Write" section
# Check:
#   - Samples sent: Should be increasing
#   - Failed sends: Should be 0
#   - Queue: Should be low (<1000)
```

---

## Common Scenarios

### Scenario A: Environment Variable Missing

**Symptoms**:
- Prometheus logs show: `MIMIR_URL: http://mimir:9009`
- DNS resolution fails for `mimir` (no such host)

**Fix**: Add `RAILWAY_ENVIRONMENT=production`

---

### Scenario B: Services in Different Projects

**Symptoms**:
- Environment variable is set
- Prometheus logs show: `MIMIR_URL: http://mimir.railway.internal:9009`
- DNS resolution fails for `mimir.railway.internal`

**Fix**: Move services to same project OR use public URL (not recommended)

---

### Scenario C: Mimir Not Running

**Symptoms**:
- DNS resolves
- TCP connection fails
- Mimir logs show errors or no "listening" message

**Fix**: Check Mimir configuration and restart:
```bash
railway restart --service mimir
railway logs --service mimir
```

---

### Scenario D: Mimir Configuration Issue

**Symptoms**:
- DNS resolves
- TCP connection succeeds
- `/ready` returns 200
- `/api/v1/push` returns 404

**Fix**: Check `mimir-railway.yml` has correct distributor config

---

## Step-by-Step Troubleshooting

1. **Run diagnostic script**:
   ```bash
   railway run --service prometheus bash diagnose-prometheus-mimir.sh
   ```

2. **If it says "Environment variables not set"**:
   - Add `RAILWAY_ENVIRONMENT=production` to Prometheus
   - Wait for redeploy
   - Run script again

3. **If it says "DNS resolution failed"**:
   - Check services are in same Railway project
   - Check Mimir service is running

4. **If it says "TCP connection failed"**:
   - Check Mimir logs for startup errors
   - Verify Mimir listening on 0.0.0.0:9009
   - Restart Mimir

5. **If it says "Push endpoint returns 404"**:
   - Check Mimir configuration file
   - Verify distributor section exists
   - Restart Mimir

6. **If all tests pass but no data**:
   - Wait 2-3 minutes (Prometheus batches writes every 30s)
   - Check Prometheus metrics: `prometheus_remote_storage_samples_total`
   - Check Mimir dashboard for ingestion metrics

---

## Expected Flow When Working

1. **Prometheus starts**:
   - Reads `RAILWAY_ENVIRONMENT=production`
   - Sets `MIMIR_URL=http://mimir.railway.internal:9009`
   - Substitutes placeholders in config
   - Starts scraping and remote write

2. **Every 30 seconds**:
   - Prometheus sends batch of samples to Mimir
   - POST to `http://mimir.railway.internal:9009/api/v1/push`
   - Mimir receives and stores in TSDB

3. **Mimir dashboard shows**:
   - Ingestion rate: 100+ samples/sec
   - Active series: 1000+
   - Storage blocks: Multiple

4. **Grafana can query**:
   - Select "Mimir" datasource
   - Query: `up`
   - See time series data

---

## If Nothing Works

**Last resort debugging**:

1. **Check Prometheus can reach ANY Railway service**:
   ```bash
   railway run --service prometheus -- curl http://grafana.railway.internal:3000/api/health
   ```
   If this fails, there's a Railway networking issue.

2. **Try using Mimir's public URL temporarily** (to test if it's a networking issue):
   ```bash
   # In Railway: Prometheus → Variables
   MIMIR_INTERNAL_URL=https://mimir-production-xxx.up.railway.app
   ```
   If this works, it confirms a Railway internal networking problem.

3. **Check Railway service linking**:
   - Railway Dashboard → Project
   - Ensure all services show as "Connected"
   - Try relinking services if needed

---

## Success Indicators

When working correctly, you'll see:

**Prometheus logs**:
```
MIMIR_URL: http://mimir.railway.internal:9009
MIMIR_TARGET: mimir.railway.internal:9009
Configured remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
```

**Prometheus metrics**:
```promql
prometheus_remote_storage_samples_total > 0
prometheus_remote_storage_samples_failed_total == 0
prometheus_remote_storage_samples_pending < 1000
```

**Mimir metrics**:
```promql
cortex_ingester_ingested_samples_total > 0
cortex_ingester_active_series > 0
```

**Grafana Mimir datasource**:
- Status: Green check
- Query `up` returns data

---

**Run the diagnostic script first - it will tell you exactly what's wrong!**

```bash
railway run --service prometheus bash diagnose-prometheus-mimir.sh
```
