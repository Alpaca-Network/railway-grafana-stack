# Next Steps: Enable Prometheus → Mimir Data Flow

## Current Status ✅
- **Mimir**: Running and healthy (502 errors fixed)
- **Prometheus**: Configured with remote_write to Mimir
- **Grafana**: Configured with Mimir datasource
- **Diagnostic Tools**: Ready to use

## Problem 🔴
Prometheus is not writing data to Mimir because the `RAILWAY_ENVIRONMENT` variable is likely not set on the Prometheus service.

---

## Step 1: Set Environment Variable (REQUIRED) ⚠️

### On Railway Dashboard:
1. Go to Railway Dashboard → **Prometheus service**
2. Click **Variables** tab
3. Add new variable:
   - **Key**: `RAILWAY_ENVIRONMENT`
   - **Value**: `production`
4. Click **Save**
5. **Wait 2-3 minutes** for automatic redeploy

### Why This Matters:
Without this variable, Prometheus uses `http://mimir:9009` (Docker Compose hostname) instead of `http://mimir.railway.internal:9009` (Railway internal network).

---

## Step 2: Verify Prometheus Logs (2 minutes after deploy)

### Check logs on Railway:
```bash
# On Railway dashboard, go to Prometheus service → Logs
# Look for these lines:
```

**Expected (CORRECT) output:**
```
===========================================
Prometheus Configuration
===========================================
FASTAPI_TARGET: fastapi-app.railway.internal:8000
FASTAPI_SCHEME: http
MIMIR_URL: http://mimir.railway.internal:9009
MIMIR_TARGET: mimir.railway.internal:9009
RAILWAY_ENVIRONMENT: production
===========================================
Configured remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
```

**Incorrect (WRONG) output:**
```
MIMIR_URL: http://mimir:9009  ← Wrong! Missing .railway.internal
RAILWAY_ENVIRONMENT: not set (local mode)  ← Variable not set
```

---

## Step 3: Run Diagnostic Script (If using Railway CLI)

### Option A: Using Railway CLI (Recommended)
```bash
# From project root
cd railway-grafana-stack

# Run diagnostic script inside Prometheus container
railway run --service prometheus bash /app/diagnose-prometheus-mimir.sh
```

### Option B: Manual Commands (If Railway CLI not available)
```bash
# 1. Check Mimir is accessible
railway run --service prometheus -- nslookup mimir.railway.internal
railway run --service prometheus -- curl -s http://mimir.railway.internal:9009/ready

# 2. Check Prometheus remote_write config
railway logs --service prometheus | grep -A5 "remote_write"

# 3. Check Prometheus remote_write metrics
railway run --service prometheus -- curl -s http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_total
```

---

## Step 4: Verify Data Flow (After 5 minutes)

### 4.1 Check Prometheus Remote Write Metrics
Visit: `https://prometheus-{your-project}.railway.app`

Navigate to: **Status → TSDB Status**

Look for: **Remote Write** section
- **Samples Sent**: Should be > 0 and increasing
- **Samples Failed**: Should be 0
- **Shards**: Should show active shards (usually 1-10)

### 4.2 Check Mimir Ingestion Metrics
On Prometheus UI, run this query:
```promql
cortex_ingester_ingested_samples_total
```

**Expected**: Should return data points showing samples ingested
**If empty**: Data is not reaching Mimir

### 4.3 Test Grafana → Mimir Connection
1. Go to Grafana: `https://grafana-{your-project}.railway.app`
2. Click **Explore** (compass icon)
3. Select **Mimir** datasource from dropdown
4. Run query: `up`
5. Should see time series data with graph

---

## Step 5: Troubleshooting (If Still Not Working)

### Issue: "MIMIR_URL still shows http://mimir:9009"
**Solution**: Environment variable not picked up
1. Verify variable is set: Railway → Prometheus → Variables
2. Force redeploy: Railway → Prometheus → Settings → Redeploy
3. Wait 2-3 minutes, check logs again

### Issue: "Error: dial tcp: lookup mimir.railway.internal: no such host"
**Solution**: Railway internal networking issue
1. Check Mimir service is running: Railway → Mimir → Logs
2. Verify Mimir is healthy: Visit `https://mimir-{project}.railway.app/ready`
3. Contact Railway support if issue persists

### Issue: "Connection refused to mimir.railway.internal:9009"
**Solution**: Mimir service not listening on port 9009
1. Check Mimir logs: Railway → Mimir → Logs
2. Look for: "server listening on [::]:9009"
3. Restart Mimir if needed: Railway → Mimir → Settings → Restart

### Issue: "401 Unauthorized" or "403 Forbidden"
**Solution**: Authentication issue (unlikely with current setup)
1. Mimir is configured without authentication
2. Check `mimir-railway.yml` has no auth settings
3. Restart Mimir service

### Issue: "Samples sent = 0, no errors shown"
**Solution**: Prometheus not scraping any metrics
1. Check scrape targets: Prometheus → Status → Targets
2. Verify targets are UP (green)
3. Check scrape interval (15s) has passed
4. Look for scrape errors in target list

---

## Expected Timeline

| Time | What Should Happen |
|------|-------------------|
| **T+0** | Set `RAILWAY_ENVIRONMENT=production` variable |
| **T+30s** | Railway triggers automatic redeploy |
| **T+2m** | Prometheus container starts with new config |
| **T+2m 15s** | First remote_write attempt to Mimir |
| **T+3m** | Prometheus logs show successful writes |
| **T+5m** | Mimir shows ingested samples in metrics |
| **T+5m** | Grafana can query data from Mimir |

---

## Verification Checklist

After setting the environment variable and waiting 5 minutes:

- [ ] Prometheus logs show `MIMIR_URL: http://mimir.railway.internal:9009`
- [ ] Prometheus logs show `RAILWAY_ENVIRONMENT: production`
- [ ] Prometheus UI → Status → TSDB → Remote Write shows samples sent > 0
- [ ] Prometheus query `prometheus_remote_storage_samples_total` returns > 0
- [ ] Prometheus query `prometheus_remote_storage_samples_failed_total` returns 0
- [ ] Prometheus query `cortex_ingester_ingested_samples_total` returns > 0
- [ ] Grafana → Explore → Mimir datasource → Query `up` returns data
- [ ] Grafana → Dashboards → Mimir Dashboard shows metrics

---

## Quick Reference: Railway CLI Commands

```bash
# Check if Railway CLI is installed
railway --version

# Link to your project (first time only)
railway link

# View logs
railway logs --service prometheus
railway logs --service mimir
railway logs --service grafana

# Run commands inside containers
railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready
railway run --service prometheus -- nslookup mimir.railway.internal

# Run diagnostic script
railway run --service prometheus bash /app/diagnose-prometheus-mimir.sh

# SSH into container (for debugging)
railway shell prometheus
railway shell mimir
```

---

## Alternative: Manual Verification (Without Railway CLI)

### 1. Check Environment Variable is Set
- Railway Dashboard → Prometheus → Variables
- Look for: `RAILWAY_ENVIRONMENT = production`

### 2. Check Logs Show Correct Configuration
- Railway Dashboard → Prometheus → Logs
- Search for: "MIMIR_URL"
- Should show: `http://mimir.railway.internal:9009`

### 3. Check Prometheus Metrics Endpoint
- Visit: `https://prometheus-{project}.railway.app/metrics`
- Search for: `prometheus_remote_storage_samples_total`
- Value should be > 0 and increasing

### 4. Check Mimir Health
- Visit: `https://mimir-{project}.railway.app/ready`
- Should return: `ready`

### 5. Check Grafana Datasource
- Visit: `https://grafana-{project}.railway.app`
- Go to: Configuration → Data Sources → Mimir
- Click: **Test** button
- Should show: ✅ Data source is working

---

## Success Criteria

✅ **Prometheus → Mimir connection is working when:**

1. Prometheus logs show Railway internal URL: `http://mimir.railway.internal:9009`
2. Prometheus remote_write metrics show samples sent > 0
3. Mimir ingestion metrics show samples received > 0
4. Grafana can query historical data from Mimir
5. No connection errors in Prometheus or Mimir logs

---

## Files to Check If Modifying Configuration

- `prometheus/prom.yml` - Prometheus config (lines 13-23: remote_write)
- `prometheus/entrypoint.sh` - URL substitution logic (lines 42-56)
- `mimir/mimir-railway.yml` - Mimir config (check limits, storage)
- `grafana/datasources/datasources.yml` - Grafana datasource config

---

## Contact & Support

If you continue to have issues after following these steps:

1. **Check Logs First**: Most issues show up in Prometheus or Mimir logs
2. **Run Diagnostic Script**: `diagnose-prometheus-mimir.sh` provides detailed output
3. **Review Documentation**:
   - `PROMETHEUS_MIMIR_CONNECTION_FIXES.md` - Common fixes
   - `DATA_FLOW_VERIFICATION.md` - Detailed verification guide
   - `MIMIR.md` - Mimir architecture and API reference

---

## Next Session Preparation

**If everything is working**, prepare for next session:
- Review Mimir dashboard in Grafana
- Check retention settings (currently 30 days)
- Monitor Mimir resource usage
- Plan compaction strategy for long-term storage

**If still not working**, gather this info:
- Prometheus logs (last 100 lines)
- Mimir logs (last 100 lines)
- Output of diagnostic script
- Screenshot of Prometheus Status → Targets page
- Screenshot of Grafana datasource test result

---

**Last Updated**: January 25, 2026
**Status**: Ready for environment variable setup
