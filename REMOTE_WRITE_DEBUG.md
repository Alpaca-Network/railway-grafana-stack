# Remote Write Debugging Guide

## Issue: No HTTP Logs in Mimir

**Problem**: Prometheus remote_write configuration exists, but Mimir shows no incoming HTTP requests in logs.

**This means**: Prometheus is either:
1. Not configured properly (MIMIR_URL placeholder not replaced)
2. Not actually sending data (no active scrape targets)
3. Sending to wrong endpoint (DNS/network issue)
4. Failing silently (errors not visible in logs)

---

## 🔍 Step-by-Step Diagnosis

### Step 1: Verify Remote Write Configuration (CRITICAL)

Run this inside the Prometheus container:
```bash
railway run --service prometheus bash /app/verify-remote-write.sh
```

This script will:
- ✅ Check if `remote_write:` section exists
- ✅ Verify MIMIR_URL placeholder was replaced
- ✅ Show actual configured URL
- ✅ Query Prometheus metrics for send status
- ✅ Check if scrape targets are active
- ✅ Test Mimir endpoint accessibility

**Expected Output (Working)**:
```
✓ remote_write section found
✓ MIMIR_URL placeholder has been replaced
  Configured URL: http://mimir.railway.internal:9009/api/v1/push
✓ Using Railway internal network (correct)
✓ Prometheus is healthy
  Total samples sent: 12345
  Failed samples: 0
✓ Prometheus IS sending samples to remote storage
```

**Expected Output (NOT Working)**:
```
✗ CRITICAL: MIMIR_URL placeholder not replaced!
  Expected: url: http://mimir.railway.internal:9009/api/v1/push
  Actual:   url: MIMIR_URL/api/v1/push
```

---

### Step 2: Check Prometheus Startup Logs

```bash
railway logs --service prometheus | grep -A 15 "Prometheus Configuration"
```

Look for:
```
=========================================
Prometheus Configuration
=========================================
MIMIR_URL: http://mimir.railway.internal:9009
MIMIR_TARGET: mimir.railway.internal:9009
RAILWAY_ENVIRONMENT: production
=========================================
Configured remote_write:
remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
    name: mimir-remote-write
...
Verifying MIMIR_URL substitution:
  ✅ MIMIR_URL placeholder successfully replaced
```

**If you see**:
```
MIMIR_URL: http://mimir:9009
RAILWAY_ENVIRONMENT: not set (local mode)
❌ ERROR: MIMIR_URL placeholder NOT replaced!
```

**Then**: The `RAILWAY_ENVIRONMENT` variable is NOT set on the Prometheus service.

---

### Step 3: Check Prometheus Metrics

Visit: `https://prometheus-{project}.railway.app`

Run these queries:

#### 1. Check if ANY samples sent
```promql
prometheus_remote_storage_samples_total
```
- **If 0 or no data**: Remote write is NOT working
- **If > 0 and increasing**: Remote write IS working

#### 2. Check for failures
```promql
prometheus_remote_storage_samples_failed_total
```
- **Should be 0**: All samples successfully sent
- **If > 0**: Some samples are failing (check logs for errors)

#### 3. Check pending queue
```promql
prometheus_remote_storage_samples_pending
```
- **Should be < 1000**: Normal operation
- **If > 10000**: Queue is backing up (Mimir not keeping up or unreachable)

#### 4. Check active shards
```promql
prometheus_remote_storage_shards
```
- **Should be 1-50**: Remote write is active
- **If 0**: Remote write is not configured/active

---

### Step 4: Check Scrape Targets

Visit: `https://prometheus-{project}.railway.app/targets`

**Check**:
- Are any targets **UP** (green)?
- If all targets are **DOWN** (red), Prometheus has no data to send!

**Common issues**:
- Bearer token incorrect
- Target URL unreachable
- Firewall blocking requests

---

### Step 5: Test Mimir Manually

From Prometheus container:
```bash
# Test DNS resolution
railway run --service prometheus -- nslookup mimir.railway.internal

# Test Mimir health
railway run --service prometheus -- curl -v http://mimir.railway.internal:9009/ready

# Test push endpoint (should return 400 with empty body)
railway run --service prometheus -- curl -v -X POST http://mimir.railway.internal:9009/api/v1/push
```

**Expected**:
- DNS resolves to an IP address
- `/ready` returns HTTP 200 with "ready"
- `/api/v1/push` returns HTTP 400 (missing data, which is expected)

**If DNS fails**:
- Mimir service not named "mimir" in Railway
- Railway internal networking not enabled
- Services in different projects

---

### Step 6: Check Mimir Logs for Ingestion

```bash
railway logs --service mimir | grep -i "request\|distributor\|ingester"
```

**With HTTP logging enabled** (recent change), you should see:
```
level=info method=POST path=/api/v1/push status=200 duration=0.05s
level=info msg="ingested samples" samples=1234
```

**If you see nothing**:
- Prometheus is not sending requests
- Requests are being sent to wrong endpoint
- Network connectivity issue

---

## 🔧 Common Fixes

### Fix 1: MIMIR_URL Placeholder Not Replaced

**Symptom**: Config shows `url: MIMIR_URL/api/v1/push`

**Cause**: `RAILWAY_ENVIRONMENT` not set on Prometheus service

**Solution**:
1. Railway Dashboard → Prometheus service → Variables
2. Add: `RAILWAY_ENVIRONMENT=production`
3. Wait 2-3 minutes for redeploy
4. Check logs: Should show "MIMIR_URL placeholder successfully replaced"

---

### Fix 2: No Scrape Targets Active

**Symptom**: All targets DOWN, `prometheus_remote_storage_samples_total = 0`

**Cause**: Targets unreachable or misconfigured

**Solution**:
1. Check bearer tokens in `/etc/prometheus/secrets/`
2. Verify target URLs are accessible
3. Test manually:
   ```bash
   railway run --service prometheus -- curl -H "Authorization: Bearer YOUR_TOKEN" https://api.gatewayz.ai/metrics
   ```

---

### Fix 3: Mimir Not Accessible

**Symptom**: `Connection refused to mimir.railway.internal:9009`

**Cause**: Mimir not running or wrong service name

**Solution**:
1. Check Mimir is running: `railway logs --service mimir | tail -20`
2. Look for: `server listening on [::]:9009`
3. If not found, check Mimir startup errors
4. Verify service name in Railway is exactly "mimir"

---

### Fix 4: DNS Resolution Fails

**Symptom**: `lookup mimir.railway.internal: no such host`

**Cause**: Railway internal networking issue or wrong service name

**Solution**:
1. Verify Mimir service name: Railway → Mimir → Settings → Service Name
2. Should be exactly: `mimir` (lowercase, no spaces)
3. If different, either:
   - Rename service to "mimir"
   - OR update `MIMIR_INTERNAL_URL=http://actual-name.railway.internal:9009`

**Temporary workaround** (use external URL):
```bash
# Set on Prometheus service
MIMIR_INTERNAL_URL=https://mimir-production-1234.up.railway.app
```

---

### Fix 5: Remote Write Working But Mimir Not Ingesting

**Symptom**: `prometheus_remote_storage_samples_total > 0` BUT `cortex_ingester_ingested_samples_total = 0`

**Cause**: Mimir configuration issue or storage full

**Solution**:
1. Check Mimir logs for errors:
   ```bash
   railway logs --service mimir | grep -i "error\|fail\|warn"
   ```
2. Check disk space:
   ```bash
   railway run --service mimir -- df -h /data/mimir
   ```
3. Check Mimir limits in `mimir-railway.yml`:
   ```yaml
   limits:
     ingestion_rate: 50000  # Increase if hitting limit
     ingestion_burst_size: 100000
   ```

---

## 🎯 Expected Behavior (When Working)

### Prometheus Logs
```
level=info msg="Starting prometheus" version="..."
...
MIMIR_URL: http://mimir.railway.internal:9009
✅ MIMIR_URL placeholder successfully replaced
Configured remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
...
level=info msg="Server is ready to receive web requests"
```

### Prometheus Metrics (after 1 minute)
```promql
prometheus_remote_storage_samples_total > 0      # Increasing
prometheus_remote_storage_samples_failed_total = 0  # Should be 0
prometheus_remote_storage_shards > 0            # Usually 1-10
prometheus_remote_storage_samples_pending < 1000  # Low queue
```

### Mimir Logs (with HTTP logging)
```
level=info msg="server listening on [::]:9009"
...
level=info method=POST path=/api/v1/push status=200 duration=0.05s
level=info msg="distributor received samples" samples=1234
level=info msg="ingester persisted samples" samples=1234
```

### Mimir Metrics (query on Prometheus)
```promql
cortex_distributor_received_samples_total > 0   # Increasing
cortex_ingester_ingested_samples_total > 0      # Increasing
cortex_ingester_active_series > 1000            # Growing
```

### Grafana
- Explore → Mimir datasource → Query: `up`
- Should return time series data with graph
- Mimir dashboard shows metrics in all panels

---

## 🧪 Manual Test: Send Sample Data to Mimir

If you want to test Mimir is accepting data without Prometheus:

```bash
# Create test data
cat > /tmp/test-samples.snappy <<'EOF'
# Snappy-compressed Prometheus remote write data
# (This is complex - easier to test via Prometheus)
EOF

# Send to Mimir
curl -X POST \
  -H 'Content-Type: application/x-protobuf' \
  -H 'Content-Encoding: snappy' \
  -H 'X-Prometheus-Remote-Write-Version: 0.1.0' \
  --data-binary @/tmp/test-samples.snappy \
  http://mimir.railway.internal:9009/api/v1/push
```

**Better approach**: Use Prometheus to send real data (it handles the complex encoding).

---

## 📊 Diagnostic Summary Checklist

Run through this checklist to identify the issue:

- [ ] **Prometheus has remote_write config**: Check `prom.yml` has `remote_write:` section
- [ ] **MIMIR_URL placeholder replaced**: Logs show "MIMIR_URL placeholder successfully replaced"
- [ ] **Environment variable set**: `RAILWAY_ENVIRONMENT=production` on Prometheus service
- [ ] **Mimir URL is correct**: `http://mimir.railway.internal:9009/api/v1/push`
- [ ] **Prometheus has active targets**: At least one target is UP (green) on /targets page
- [ ] **Prometheus is sending samples**: `prometheus_remote_storage_samples_total > 0`
- [ ] **No failed samples**: `prometheus_remote_storage_samples_failed_total = 0`
- [ ] **Mimir is accessible**: `curl http://mimir.railway.internal:9009/ready` returns 200
- [ ] **Mimir is ingesting**: `cortex_ingester_ingested_samples_total > 0`
- [ ] **Mimir logs show requests**: Logs show POST /api/v1/push requests
- [ ] **Grafana can query Mimir**: Explore → Mimir → Query `up` returns data

**If all checked**: Remote write is fully working! 🎉

**If some unchecked**: Focus on the first unchecked item - that's your issue.

---

## 🚨 Most Likely Issues (Ranked)

Based on "no HTTP logs in Mimir", here are the issues in order of likelihood:

### 1. ⚠️ MIMIR_URL Placeholder Not Replaced (90% probability)
- **Symptom**: No HTTP requests to Mimir at all
- **Cause**: `RAILWAY_ENVIRONMENT` not set
- **Check**: `railway logs --service prometheus | grep MIMIR_URL`
- **Fix**: Set `RAILWAY_ENVIRONMENT=production` on Prometheus service

### 2. ⚠️ No Active Scrape Targets (5% probability)
- **Symptom**: Prometheus has no data to send
- **Cause**: All targets DOWN
- **Check**: Visit `https://prometheus-{project}.railway.app/targets`
- **Fix**: Fix bearer tokens or target URLs

### 3. ⚠️ Mimir Not Accessible (3% probability)
- **Symptom**: DNS or network issue
- **Cause**: Wrong service name or Railway networking issue
- **Check**: `railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready`
- **Fix**: Verify service name is "mimir", check Mimir is running

### 4. ⚠️ Mimir Not Logging Requests (2% probability)
- **Symptom**: Requests arriving but not logged
- **Cause**: Log level too high
- **Check**: Recent config change enables HTTP logging
- **Fix**: Restart Mimir after deploying updated config

---

## 🔬 Advanced Debugging

### Enable Prometheus Debug Logging

Edit `prometheus/Dockerfile`, add to CMD:
```dockerfile
CMD ["--config.file=/etc/prometheus/prom.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--log.level=debug"]
```

Redeploy. Logs will show remote write details:
```
level=debug msg="remote write: sending samples" samples=1234 endpoint="http://mimir.railway.internal:9009/api/v1/push"
```

### Enable Mimir Debug Logging

Edit `mimir/mimir-railway.yml`:
```yaml
server:
  log_level: debug  # Change from info
```

Redeploy. Logs will show detailed request handling.

### Capture Network Traffic

From Prometheus container:
```bash
# Install tcpdump (if available)
apk add tcpdump

# Capture traffic to Mimir
tcpdump -i any -n 'host mimir.railway.internal and port 9009'
```

Should show TCP packets if Prometheus is sending requests.

---

## 📞 Next Steps

1. **Run verification script**:
   ```bash
   railway run --service prometheus bash /app/verify-remote-write.sh
   ```

2. **Check output** - identifies exact issue

3. **Apply fix** based on script recommendations

4. **Verify data flow**:
   ```bash
   # After 2 minutes, check Prometheus metrics
   # Query: prometheus_remote_storage_samples_total
   # Should be > 0 and increasing
   ```

5. **Confirm in Mimir logs**:
   ```bash
   railway logs --service mimir | grep -i "request\|ingester"
   ```

6. **Test in Grafana**:
   - Explore → Mimir → Query: `up`
   - Should show graph with data

---

**Last Updated**: January 25, 2026  
**Status**: Debugging tools ready, awaiting runtime verification
