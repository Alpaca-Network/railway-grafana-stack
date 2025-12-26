# Debug Missing Metrics on Railway

**Issue:** All metrics are missing on Railway deployment (request metrics, cache metrics, model health, etc.)

---

## Quick Diagnosis Checklist

### 1. Check Backend /metrics Endpoint (HIGHEST PRIORITY)

```bash
# On your local machine, test the Railway backend endpoint
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://gatewayz-staging.up.railway.app/metrics

# Expected Response:
# - Should return Prometheus text format
# - Should contain "gatewayz_health_service_up" metrics
# - Should contain "gatewayz_health_tracked_models" metrics
# - Should contain "gatewayz_health_active_incidents" metrics

# If you get 404: Module not integrated
# If you get 403: Bearer token issue
# If you get metrics but no "gatewayz_health_" entries: Health service not called
```

### 2. Check Prometheus /metrics Endpoint

```bash
# In Prometheus UI (http://your-prometheus:9090)
# Query: gatewayz_health_tracked_models

# Expected: Should show numeric value (e.g., 42)
# If empty/no results: Backend /metrics not exporting properly
```

### 3. Check Backend Integration (CRITICAL)

**Question: Is `setup_prometheus_routes(app)` called in your FastAPI main.py?**

Your backend's `main.py` should have:

```python
from fastapi import FastAPI
from app.services.prometheus_metrics import setup_prometheus_routes

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Import at startup to get HEALTH_SERVICE_URL env var
    await setup_prometheus_routes(app)

# Rest of your routes...
```

If this is missing, metrics won't be exported.

---

## Issue #1: Module Not Deployed to Backend

**Symptom:** `/metrics` endpoint returns 404

**Fix:**
1. Copy `PROMETHEUS_METRICS_MODULE.py` to your backend at `app/services/prometheus_metrics.py`
2. Add the startup code above to your `main.py`
3. Redeploy to Railway

---

## Issue #2: Missing Environment Variable

**Symptom:** Module is deployed, but health metrics are 0 or missing

**Fix:** Set environment variable on Railway

```bash
# On Railway platform:
# 1. Go to your backend service settings
# 2. Add environment variable:

HEALTH_SERVICE_URL=https://health-service-production.up.railway.app

# OR if health service is on a different URL:
HEALTH_SERVICE_URL=https://your-health-service-url.com

# Then redeploy
```

**Without this, the module uses hardcoded default:** `https://health-service-production.up.railway.app`

---

## Issue #3: Health Service Not Reachable from Railway

**Symptom:**
- Backend /metrics returns 200
- But "gatewayz_health_service_up" gauge is 0
- Logs show "Failed to fetch /health" warnings

**Diagnosis:**

```bash
# SSH into Railway backend and test connectivity:
curl -X GET https://health-service-production.up.railway.app/health

# If connection refused: Health service URL is wrong
# If 401/403: Authentication issue
# If no response: Network/firewall blocking
```

**Common Fixes:**
- ✅ Use `.internal` URL for Railway-to-Railway communication:
  ```
  HEALTH_SERVICE_URL=https://health-service-prod.internal
  ```
- ✅ If auth required, add bearer token to HealthServiceClient (currently not implemented - would need code change)
- ✅ Check firewall rules allow Railway backend → health service

---

## Issue #4: Prometheus Scrape Job Not Working

**Symptom:** Prometheus shows 0 targets for gatewayz_staging job

**Check:**
1. Go to Prometheus UI → Status → Targets
2. Look for `gatewayz_staging` job
3. Status should be "UP"

**If "DOWN":**
- Check bearer token in `prometheus/prom.yml` line 53
- Verify Railway backend is accessible
- Check response time (should be <10s)

**If "UP" but no metrics:**
- Backend `/metrics` endpoint might be returning empty

---

## Detailed Debugging Steps

### Step 1: Verify Backend Integration

Check if PROMETHEUS_METRICS_MODULE.py is actually deployed:

```bash
# SSH to Railway backend or check logs
# Look for these startup messages:
# "Prometheus metrics routes initialized"
# "Health service metrics background task started"
```

If you see these messages, module is deployed.

### Step 2: Check Background Task Errors

```bash
# Look in Railway backend logs for errors like:
# "Failed to fetch /health: ..."
# "Failed to fetch /status: ..."
# "Error in health metrics task: ..."

# These indicate connectivity issues to health service
```

### Step 3: Test Health Service Connectivity from Backend

If you have access to Railway backend shell:

```bash
python3 << 'EOF'
import asyncio
import httpx
import os

async def test():
    health_url = os.getenv("HEALTH_SERVICE_URL",
        "https://health-service-production.up.railway.app")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{health_url}/health", timeout=10)
            print(f"✅ /health: {resp.status_code}")
        except Exception as e:
            print(f"❌ /health: {e}")

asyncio.run(test())
EOF
```

### Step 4: Check Grafana Query

Verify Grafana is querying the right datasource:

```bash
# In Grafana dashboard panel settings
# Data Source should be: "Prometheus"
# Query example: gatewayz_health_tracked_models

# If query returns "No data":
# - Check Prometheus datasource URL points to correct Prometheus
# - Verify Prometheus has the metric (test in Prometheus UI first)
```

---

## The Data Flow (Should Look Like This)

```
Railway Backend
  ↓
  └─ setup_prometheus_routes() on startup
     ├─ Creates HealthServiceClient
     └─ Starts background task
        ├─ Every 30s: fetch /health, /status, /metrics, /cache/stats
        └─ Update Prometheus metrics in memory
  ↓
  GET /metrics endpoint
  └─ Returns: generate_latest() (all metrics in Prometheus format)
     ├─ gatewayz_health_service_up 1
     ├─ gatewayz_health_tracked_models 42
     ├─ gatewayz_health_tracked_providers 8
     └─ gatewayz_health_active_incidents 0
  ↓
Prometheus (scrapes /metrics every 15s)
  ├─ gatewayz_staging job: https://gatewayz-staging.up.railway.app/metrics
  └─ Stores time-series: gatewayz_health_tracked_models 42 [timestamp]
  ↓
Grafana
  └─ Queries Prometheus: gatewayz_health_tracked_models
     ├─ Returns: 42
     └─ Displays on dashboard ✅
```

---

## Most Likely Culprits (In Order)

1. **✋ MOST LIKELY:** `setup_prometheus_routes(app)` NOT called in backend main.py
   - **Fix:** Add it to startup code and redeploy

2. **SECOND MOST LIKELY:** `HEALTH_SERVICE_URL` environment variable not set
   - **Fix:** Add to Railway environment variables

3. **THIRD:** Health service not reachable from Railway
   - **Fix:** Use `.internal` URL or check network/firewall

4. **FOURTH:** Prometheus scrape job failing (bearer token wrong)
   - **Fix:** Check token in `prometheus/prom.yml` line 53

---

## Quick Fix Checklist

```markdown
- [ ] Verify PROMETHEUS_METRICS_MODULE.py is at app/services/prometheus_metrics.py on backend
- [ ] Verify setup_prometheus_routes(app) is called in backend's main.py on startup
- [ ] Verify HEALTH_SERVICE_URL environment variable is set on Railway
- [ ] Test backend /metrics endpoint returns health metrics
- [ ] Check Prometheus can scrape backend /metrics (Status → Targets → gatewayz_staging UP)
- [ ] Verify Prometheus has metrics (query gatewayz_health_tracked_models)
- [ ] Verify Grafana datasource points to Prometheus
- [ ] Test Grafana query on one panel
```

---

## Next Steps

1. **Check the backend `/metrics` endpoint first** (using curl with bearer token)
   - This tells us if the module is deployed and working

2. **If `/metrics` returns data:** Problem is in Prometheus/Grafana query side
   - Check Prometheus scrape job status
   - Verify Grafana datasource configuration

3. **If `/metrics` returns empty or 404:**
   - Module not deployed OR not getting called on startup
   - Need to add integration code to backend main.py

4. **If `/metrics` returns metrics but health values are 0:**
   - Health service not reachable
   - Check HEALTH_SERVICE_URL environment variable
   - Check network/firewall between backend and health service

---

## Still Stuck?

Provide these details:

1. What does `curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" https://gatewayz-staging.up.railway.app/metrics` return?

2. In Prometheus UI (Status → Targets), what is the status of `gatewayz_staging` job?

3. Do you see "gatewayz_health_*" in backend startup logs?

4. Is `setup_prometheus_routes(app)` called in your backend's FastAPI main.py?

