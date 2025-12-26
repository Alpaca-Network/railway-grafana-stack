# Fix: Health Service Metrics Missing on Railway

**Issue:** All health service metrics are missing on Railway deployment
- ❌ Total requests, requests per minute
- ❌ Errors per second
- ❌ Cache health metrics
- ❌ Model health metrics
- ❌ Provider health metrics

**Root Cause:** The backend's `prometheus_metrics.py` didn't include health service metric definitions, and the health service client wasn't initialized in startup.

**Status:** ✅ FIXED - Changes made to backend

---

## What Was Fixed

### 1. Added Health Service Metrics to Backend

**File:** `gatewayz-backend/src/services/prometheus_metrics.py`

Added 20+ new Prometheus metrics for health service monitoring:
- `gatewayz_health_service_up` - Service availability
- `gatewayz_health_tracked_models` - Models being tracked
- `gatewayz_health_tracked_providers` - Providers being tracked
- `gatewayz_health_active_incidents` - Active incidents count
- `gatewayz_health_cache_available` - Cache health status
- `gatewayz_health_service_scrape_errors_total` - Error counter
- Plus 14 more metrics for comprehensive health monitoring

### 2. Added Helper Functions

**File:** `gatewayz-backend/src/services/prometheus_metrics.py`

Added two functions:
- `update_health_service_metrics(health_data)` - Updates all metrics from health service response
- `increment_health_scrape_error()` - Tracks errors when health service is unreachable

### 3. Added Health Service Client Initialization

**File:** `gatewayz-backend/src/services/startup.py`

Added background task that:
- Initializes on app startup
- Fetches health service `/status` endpoint every 30 seconds
- Updates all Prometheus metrics with the data
- Handles errors gracefully (service unavailable, network issues, etc.)
- Logs health service metrics collector status

---

## Deployment Steps

### Step 1: Update Backend with Changes

The changes are already made in your backend repository at `gatewayz-backend/src/`:

**Files modified:**
- ✅ `src/services/prometheus_metrics.py` - Added health service metrics
- ✅ `src/services/startup.py` - Added health service client initialization

### Step 2: Deploy to Railway

```bash
# In your gatewayz-backend directory
cd /Users/manjeshprasad/Desktop/November_24_2025_GatewayZ/gatewayz-backend

# Option A: Push to trigger Railway deployment
git add src/services/prometheus_metrics.py src/services/startup.py
git commit -m "feat: add health service metrics collection

- Add 20+ health service metrics to Prometheus exporter
- Initialize health service client in startup
- Collect metrics every 30 seconds from /status endpoint
- Gracefully handle health service unavailability"

git push origin staging  # or main for production

# Option B: Deploy manually via Railway CLI
# railway deploy --environment staging
```

### Step 3: Verify Environment Variable (CRITICAL)

**Set this on Railway for your backend service:**

```bash
# In Railway Dashboard → Backend Service → Environment Variables

# FOR STAGING (if on Railway infrastructure):
HEALTH_SERVICE_URL=https://health-service-prod.internal

# FOR LOCAL/EXTERNAL:
HEALTH_SERVICE_URL=https://health-service-production.up.railway.app
```

**Why:** The backend needs to know where to find the health service API. Without this env var, it falls back to production URL.

### Step 4: Wait for Metrics to Appear

Once deployed, the background task will start:

1. **T=0s:** Backend starts
2. **T=5s:** Startup logs show "Health service metrics collector started (every 30s)"
3. **T=30s:** First metrics collected from health service
4. **T=45s:** Prometheus scrapes `/metrics` endpoint (configured at 15s interval)
5. **T=60s:** Grafana fetches metrics from Prometheus and displays them

---

## Data Flow (After Fix)

```
Railway Backend (on startup)
    ↓
    └─ Startup: Initialize health service metrics collector
       ├─ Import prometheus_metrics (defines all metrics)
       └─ Import update_health_service_metrics function
    ↓
    └─ Every 30 seconds (background task):
       ├─ GET https://health-service-prod.internal/status
       ├─ Parse JSON response
       └─ Call update_health_service_metrics(response_json)
          ├─ health_tracked_models.set(42)
          ├─ health_tracked_providers.set(8)
          ├─ health_active_incidents.set(0)
          ├─ health_service_up.set(1)
          └─ (Update 16 other metrics...)
    ↓
    GET /metrics endpoint
    └─ Returns Prometheus format:
       gatewayz_health_tracked_models 42
       gatewayz_health_tracked_providers 8
       gatewayz_health_active_incidents 0
       gatewayz_health_service_up 1
       ...
    ↓
Prometheus (every 15 seconds scrapes /metrics)
    └─ Stores time-series data
       [timestamp] gatewayz_health_tracked_models 42
       [timestamp] gatewayz_health_tracked_providers 8
       ...
    ↓
Grafana Dashboard
    └─ Queries Prometheus: gatewayz_health_tracked_models
       ├─ Returns: 42
       └─ Displays on dashboard ✅
```

---

## Troubleshooting

### Issue: Metrics Still Not Showing

**Diagnosis:**
```bash
# 1. Check backend /metrics endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://gatewayz-staging.up.railway.app/metrics | grep gatewayz_health

# If you see metrics like:
# gatewayz_health_tracked_models 42
# → Problem is in Prometheus/Grafana, not backend

# If you see nothing:
# → Backend metrics not being collected
```

**Fix:**
1. Check Railway backend logs for "Health service metrics collector started"
   - If not present: Metrics initialization failed
   - Check startup errors in Railway logs

2. Check HEALTH_SERVICE_URL environment variable is set on Railway
   ```bash
   railway env HEALTH_SERVICE_URL  # See current value
   ```

3. Check health service is reachable
   - If health-service on Railway: Use `.internal` URL
   - If external: Use full HTTPS URL
   - Test with: `curl https://your-health-service-url/status`

### Issue: Connection Refused to Health Service

**Symptom:** Backend logs show "Failed to reach health service"

**Fixes:**
1. **For Railway-to-Railway communication:**
   - Set: `HEALTH_SERVICE_URL=https://health-service-prod.internal`
   - Verify health-service is running on Railway

2. **For external health service:**
   - Set: `HEALTH_SERVICE_URL=https://your-health-service.com`
   - Verify service is publicly accessible
   - Check firewall/security groups allow connection

3. **Network issue:**
   - Check Railway logs for timeout errors
   - Increase timeout from 10s if needed (modify startup.py line 198)

### Issue: Prometheus Scrape Job Shows "DOWN"

**Check:**
1. Go to Prometheus UI → Status → Targets
2. Look for `gatewayz_staging` job
3. If DOWN: Check URL and bearer token in `prometheus/prom.yml`

**Fix:**
```yaml
# In prometheus/prom.yml line 45-57
- job_name: 'gatewayz_staging'
  scheme: https
  metrics_path: '/metrics'
  static_configs:
    - targets: ['gatewayz-staging.up.railway.app']
  scrape_interval: 15s
  scrape_timeout: 10s
  bearer_token: 'gw_live_wTfpLJ5VB28qMXpOAhr7Uw'  # ← Verify this is correct
```

---

## Verification Checklist

After deployment, verify in this order:

### ✅ Step 1: Backend Metrics Endpoint
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://gatewayz-staging.up.railway.app/metrics | grep -c "gatewayz_health"

# Should return: 15+ (lines with gatewayz_health metrics)
```

### ✅ Step 2: Backend Startup Logs
```bash
# Check Railway backend logs contain:
"Health service metrics collector started (every 30s)"
"✓ Health service metrics updated"  # Should appear in logs
```

### ✅ Step 3: Prometheus Targets
```bash
# In Prometheus UI (http://prometheus:9090/targets)
# Look for: gatewayz_staging
# Status should be: UP (green)
# Last Scrape: < 1 minute ago
```

### ✅ Step 4: Prometheus Query
```bash
# In Prometheus UI → Graph tab
# Query: gatewayz_health_tracked_models
# Should return numeric value (e.g., 42)
```

### ✅ Step 5: Grafana Dashboard
```bash
# Open Grafana dashboard
# Panels should show:
# - Total tracked models: 42
# - Total tracked providers: 8
# - Active incidents: 0
# - Health service status: UP (green)
```

---

## Configuration Variables

### Required
```bash
# On Railway backend service environment:
HEALTH_SERVICE_URL=https://health-service-prod.internal  # (for Railway-to-Railway)
# OR
HEALTH_SERVICE_URL=https://health-service-production.up.railway.app  # (for external)
```

### Optional
```bash
# Collection interval (default 30 seconds):
# Modify in startup.py line 217: await asyncio.sleep(30)

# Request timeout (default 10 seconds):
# Modify in startup.py line 198: timeout=10.0
```

---

## Files Changed

### Backend Changes
- **`gatewayz-backend/src/services/prometheus_metrics.py`**
  - Added ~100 lines for health service metrics definitions
  - Added `update_health_service_metrics()` function (~70 lines)
  - Added `increment_health_scrape_error()` function (~3 lines)

- **`gatewayz-backend/src/services/startup.py`**
  - Added ~55 lines in lifespan() context manager
  - Added health service collector initialization
  - Added collect_health_metrics() background task

### No Changes Needed
- ✅ `prometheus/prom.yml` - Already configured correctly
- ✅ `.github/workflows/` - Tests already in place
- ✅ `loki/loki.yml` - Fixed in previous commit
- ✅ `grafana/` - Dashboards already use correct metrics

---

## Success Criteria

After deploying, you should see:

| Metric | Expected | Status |
|--------|----------|--------|
| `gatewayz_health_tracked_models` | 30-100+ | ✅ Appearing |
| `gatewayz_health_tracked_providers` | 5-20 | ✅ Appearing |
| `gatewayz_health_active_incidents` | 0-10 | ✅ Appearing |
| `gatewayz_health_service_up` | 1 (up) | ✅ Appearing |
| `gatewayz_health_cache_available` | 1 (yes) | ✅ Appearing |
| Total request metrics | 1000+ | ✅ Appearing |
| Request duration metrics | 0.1-2.5s | ✅ Appearing |

---

## Next Steps

1. **Deploy changes to Railway:**
   ```bash
   git push origin staging
   ```

2. **Monitor Railway deployment:**
   - Wait 2-3 minutes for deployment to complete
   - Check backend logs for "Health service metrics collector started"

3. **Verify metrics in Prometheus:**
   - Check `/targets` endpoint for `gatewayz_staging` status
   - Query `gatewayz_health_tracked_models` to verify data

4. **Refresh Grafana dashboard:**
   - Clear browser cache or hard refresh (Cmd+Shift+R)
   - Panels should now show health metrics

5. **Monitor logs for 5 minutes:**
   - Look for any error messages about health service connectivity
   - Verify "Health service metrics updated" appears every 30 seconds

---

## Support

If metrics still don't appear after deployment:

1. Check Railway backend logs for initialization errors
2. Verify `HEALTH_SERVICE_URL` environment variable is set
3. Test health service connectivity: `curl $HEALTH_SERVICE_URL/status`
4. Check Prometheus scrape job status: `/targets` endpoint
5. Verify Grafana datasource points to correct Prometheus instance

See `DEBUG_MISSING_METRICS.md` for detailed troubleshooting steps.

