# Summary: Missing Metrics Issue - ROOT CAUSE & FIX

## The Problem

You reported that on Railway deployment, **ALL health service metrics were missing**:
- ❌ Total requests, request per minute
- ❌ Error metrics
- ❌ Cache health
- ❌ Model health
- ❌ Provider health

Grafana showed empty dashboards while Prometheus itself was UP with data.

---

## Root Cause Analysis

**The backend's `prometheus_metrics.py` file DID NOT have health service metrics defined.**

### What the backend HAD:
- ✅ HTTP request metrics (fastapi_requests_total, duration, etc.)
- ✅ Model inference metrics
- ✅ Provider metrics
- ✅ Database metrics
- ✅ Cache metrics
- ✅ Rate limiting metrics
- ✅ Business metrics

### What the backend was MISSING:
- ❌ `gatewayz_health_service_up`
- ❌ `gatewayz_health_tracked_models`
- ❌ `gatewayz_health_tracked_providers`
- ❌ `gatewayz_health_active_incidents`
- ❌ `gatewayz_health_cache_available`
- ❌ 15+ other health service metrics

### Why These Metrics Were Missing:

1. **Backend's `prometheus_metrics.py`**: Only defined standard metrics, not health service metrics
2. **Backend's `startup.py`**: Didn't initialize a health service client to fetch and update metrics
3. **Result**: Health service data was never collected, so metrics were never set

### Why It Worked Locally (Docker Compose):

In the grafana-stack repo, we created `PROMETHEUS_METRICS_MODULE.py` which had all these metrics. But **that module is separate from the gatewayz-backend repo** and wasn't deployed to Railway.

---

## The Fix - What Was Done

### 1. Added Health Service Metrics to Backend

**File:** `gatewayz-backend/src/services/prometheus_metrics.py`

```python
# Added 20+ new metrics:
health_service_up = Gauge('gatewayz_health_service_up', ...)
health_tracked_models = Gauge('gatewayz_health_tracked_models', ...)
health_tracked_providers = Gauge('gatewayz_health_tracked_providers', ...)
health_active_incidents = Gauge('gatewayz_health_active_incidents', ...)
# ... 16 more metrics
```

### 2. Added Helper Functions to Update Metrics

**File:** `gatewayz-backend/src/services/prometheus_metrics.py`

```python
def update_health_service_metrics(health_data: dict):
    """Update all health metrics from health service response"""
    health_tracked_models.set(health_data.get("tracked_models", 0))
    health_tracked_providers.set(health_data.get("tracked_providers", 0))
    health_active_incidents.set(health_data.get("active_incidents", 0))
    # ... update remaining metrics
```

### 3. Added Health Service Client to Startup

**File:** `gatewayz-backend/src/services/startup.py`

Added background task that on startup:
- ✅ Initializes health service client
- ✅ Every 30 seconds: Fetches `/status` from health service
- ✅ Calls `update_health_service_metrics()` to update all metrics
- ✅ Handles errors gracefully (service down, network issues, etc.)
- ✅ Logs status in backend logs

---

## How It Works Now (After Fix)

```
Railway Backend Startup (every time app restarts):
    ↓
    Load prometheus_metrics.py
    ├─ Define health_tracked_models gauge
    ├─ Define health_tracked_providers gauge
    ├─ Define 18 other health metrics
    └─ Ready to accept metric updates
    ↓
    Load startup.py lifespan()
    ├─ Initialize health service collector
    └─ Start background task
    ↓
Every 30 seconds (background task):
    ├─ GET https://health-service-prod.internal/status
    ├─ Receive JSON: {"tracked_models": 42, "tracked_providers": 8, ...}
    └─ Call update_health_service_metrics(response)
       ├─ health_tracked_models.set(42)
       ├─ health_tracked_providers.set(8)
       └─ (12 more updates...)
    ↓
Every 15 seconds (Prometheus scrapes):
    ├─ GET https://gatewayz-staging.up.railway.app/metrics
    ├─ Receives Prometheus format:
    │  gatewayz_health_tracked_models 42
    │  gatewayz_health_tracked_providers 8
    │  gatewayz_health_active_incidents 0
    │  ...
    └─ Stores time-series data
    ↓
Grafana Dashboard:
    ├─ Queries Prometheus: gatewayz_health_tracked_models
    ├─ Gets value: 42
    └─ Displays on dashboard ✅
```

---

## What You Need to Do

### Step 1: Deploy Changes to Railway

```bash
cd /Users/manjeshprasad/Desktop/November_24_2025_GatewayZ/gatewayz-backend

# Commit changes
git add src/services/prometheus_metrics.py src/services/startup.py
git commit -m "feat: add health service metrics collection

- Add 20+ health service metrics to Prometheus exporter
- Initialize health service client in startup
- Collect metrics every 30 seconds from /status endpoint
- Gracefully handle health service unavailability"

# Push to trigger Railway deployment
git push origin staging  # or main for production
```

### Step 2: Verify HEALTH_SERVICE_URL Environment Variable

**On Railway Dashboard:**
1. Go to Backend Service Settings → Environment
2. Add (or verify) this variable:

```bash
# For Railway infrastructure (recommended):
HEALTH_SERVICE_URL=https://health-service-prod.internal

# OR for external:
HEALTH_SERVICE_URL=https://health-service-production.up.railway.app
```

### Step 3: Wait for Metrics

After deployment (~2-3 min):
1. Backend startup logs will show: "Health service metrics collector started (every 30s)"
2. Check `gatewayz-staging` target in Prometheus (should be UP)
3. Query `gatewayz_health_tracked_models` in Prometheus
4. Refresh Grafana dashboard (Cmd+Shift+R)

---

## Verification

### Quick Test

```bash
# After deployment, test backend /metrics endpoint:
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://gatewayz-staging.up.railway.app/metrics | grep gatewayz_health

# Should show many lines:
gatewayz_health_service_up 1
gatewayz_health_tracked_models 42
gatewayz_health_tracked_providers 8
gatewayz_health_active_incidents 0
gatewayz_health_cache_available 1
# ... 15 more metrics
```

### In Prometheus UI

1. Go to `http://your-prometheus:9090/graph`
2. Query: `gatewayz_health_tracked_models`
3. Should return a number (e.g., 42)

### In Grafana

1. Open dashboard
2. Panels should now display health metrics
3. If still empty, clear cache and refresh

---

## Files Modified

### In gatewayz-backend repo:
- ✅ `src/services/prometheus_metrics.py` (~100 lines added)
  - Health service metric definitions
  - Update and error increment functions

- ✅ `src/services/startup.py` (~55 lines added)
  - Health service client initialization
  - Background task for collecting metrics

### In railway-grafana-stack repo:
- ✅ `HEALTH_SERVICE_METRICS_FIX.md` (deployment guide)
- ✅ `DEBUG_MISSING_METRICS.md` (troubleshooting guide)

---

## Why This Wasn't Needed Before

The PROMETHEUS_METRICS_MODULE.py we created earlier was designed for **local development** with Docker Compose. It had:
- ✅ All health service metrics
- ✅ HealthServiceClient class
- ✅ Background task to collect metrics

But **this module wasn't deployed to Railway** because:
1. It's in the `railway-grafana-stack` repo (infrastructure)
2. The backend runs from `gatewayz-backend` repo (application)
3. The backend didn't import or use the module

The fix integrates health service metrics directly into the **backend's existing prometheus_metrics.py**, which ensures they're available wherever the backend runs (local, Railway, Docker, etc.).

---

## Next Steps

1. **Commit and push changes** to backend repo
2. **Monitor Railway deployment** (2-3 minutes)
3. **Verify metrics appear** in Prometheus
4. **Check Grafana dashboard** for data
5. **Monitor logs** for "Health service metrics updated" messages

See `HEALTH_SERVICE_METRICS_FIX.md` for detailed deployment instructions.

