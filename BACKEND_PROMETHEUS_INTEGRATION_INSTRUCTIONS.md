# 🚀 Backend Agent: Prometheus Metrics Integration Instructions

**For:** Backend Development Team / Other Agents
**From:** Cloud Code - Monitoring Infrastructure
**Date:** December 24, 2025
**Priority:** HIGH - Required for dashboard functionality
**Deadline:** January 4, 2026 (for staging deployment)

---

## 📋 Summary

Your backend needs to implement **8 new Prometheus metrics endpoints** that aggregate data from the Prometheus server. These endpoints will replace the deprecated `health-service-exporter` and provide structured access to all monitoring data.

**What needs to be done:**
- [ ] Copy the provided Prometheus metrics module into your codebase
- [ ] Integrate with your FastAPI application
- [ ] Test all 8 endpoints
- [ ] Deploy to staging and production

**Time estimate:** 2-4 hours for implementation and testing

---

## 📁 What You're Getting

You will receive:

1. **`PROMETHEUS_METRICS_MODULE.py`** - Complete Python module with all endpoint implementations
2. **These instructions** - Step-by-step integration guide
3. **Deprecation notice** - For the health-service-exporter (to be removed Jan 7)

**No additional coding required** - The module is ready to use. You just need to integrate it into your app.

---

## ✅ Prerequisites

Your backend must have:

- ✅ FastAPI application running on `gatewayz-staging.up.railway.app`
- ✅ Prometheus server accessible at `http://prometheus:9090` (or configurable via env var)
- ✅ Metrics being exported to Prometheus (from existing endpoints and exporters)
- ✅ Python 3.9+ with `httpx` library available

**Install if missing:**
```bash
pip install httpx
```

---

## 🔧 Integration Steps

### Step 1: Copy the Module into Your Project

```bash
# Copy the file to your backend
cp PROMETHEUS_METRICS_MODULE.py app/services/prometheus_metrics.py

# Or if in different location:
cp PROMETHEUS_METRICS_MODULE.py your_app/services/prometheus_metrics.py
```

**Expected location:** `app/services/prometheus_metrics.py`

### Step 2: Update Your FastAPI Application

**Option A: Using Lifespan (FastAPI 0.93+, RECOMMENDED)**

```python
# app/main.py or main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.prometheus_metrics import setup_prometheus_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    await setup_prometheus_routes(app)
    print("✅ Prometheus metrics endpoints initialized")
    yield
    # Shutdown event
    print("👋 Shutting down")

app = FastAPI(
    title="GatewayZ API",
    lifespan=lifespan,
    # ... other config
)

# Your existing routes here
@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Option B: Using @app.on_event (Older FastAPI)**

```python
# app/main.py
from fastapi import FastAPI
from app.services.prometheus_metrics import setup_prometheus_routes

app = FastAPI()

@app.on_event("startup")
async def startup():
    await setup_prometheus_routes(app)
    print("✅ Prometheus metrics endpoints initialized")

# Your existing routes here
```

### Step 3: Configure Prometheus URL (Optional)

By default, the module connects to `http://prometheus:9090`. If your Prometheus instance is at a different address:

```python
# Set environment variable
export PROMETHEUS_URL=http://your-prometheus:9090

# Or in .env file
PROMETHEUS_URL=http://prometheus:9090

# Or in Railway environment settings
# Add: PROMETHEUS_URL=http://prometheus-prod.internal:9090
```

### Step 4: Test Locally

Start your backend:
```bash
python -m uvicorn app.main:app --reload
```

Test the endpoints:
```bash
# Test summary endpoint (JSON)
curl http://localhost:8000/prometheus/metrics/summary | jq .

# Test system metrics (Prometheus format)
curl http://localhost:8000/prometheus/metrics/system

# Test all endpoints (Prometheus format)
curl http://localhost:8000/prometheus/metrics/all

# Test docs
curl http://localhost:8000/prometheus/metrics/docs
```

Expected responses:
- `/summary` - JSON with timestamp and metrics object
- `/system` - Prometheus text format (lines like: `metric_name 123`)
- `/docs` - Markdown documentation

### Step 5: Deploy to Staging

1. **Push to staging branch**
   ```bash
   git add app/services/prometheus_metrics.py
   git commit -m "feat: add Prometheus metrics aggregation endpoints"
   git push origin staging
   ```

2. **Deploy via Railway**
   - Railway auto-deploys on push to staging
   - Check deployment status in Railway dashboard
   - Verify endpoints are accessible at:
     - `https://gatewayz-staging.up.railway.app/prometheus/metrics/summary`
     - `https://gatewayz-staging.up.railway.app/prometheus/metrics/system`
     - etc.

3. **Test in staging**
   ```bash
   # Test from anywhere
   curl https://gatewayz-staging.up.railway.app/prometheus/metrics/summary | jq .
   ```

---

## 📡 Endpoint Reference

All endpoints are prefixed with `/prometheus/metrics/`

### 1. **GET /summary** ⭐ MOST IMPORTANT FOR DASHBOARDS
- **Response:** JSON
- **Use for:** Dashboard widgets, real-time counters
- **Refresh rate:** Every 30 seconds
- **Response time:** <50ms
- **Example response:**
```json
{
  "timestamp": "2025-12-26T12:00:00Z",
  "metrics": {
    "http": {
      "total_requests": "12345",
      "request_rate_per_minute": "25.5",
      "error_rate": "2.3",
      "avg_latency_ms": "145.2",
      "in_progress": "3"
    },
    "models": { ... },
    "providers": { ... },
    "database": { ... },
    "business": { ... }
  }
}
```

### 2. **GET /system**
- **Response:** Prometheus text format
- **Use for:** Grafana dashboards querying HTTP/request metrics
- **Metrics included:**
  - `fastapi_requests_total` by status code
  - `fastapi_requests_duration_seconds` (histogram)
  - `fastapi_requests_in_progress`
  - `fastapi_exceptions_total`

### 3. **GET /providers**
- **Response:** Prometheus text format
- **Use for:** Provider health dashboards
- **Metrics included:**
  - `gatewayz_providers_total`
  - `gatewayz_providers_healthy`
  - `gatewayz_providers_degraded`
  - `gatewayz_providers_down`
  - `provider_availability{provider}`
  - `provider_error_rate{provider}`
  - `provider_response_time_seconds{provider}`
  - `gatewayz_provider_health_score{provider}`

### 4. **GET /models**
- **Response:** Prometheus text format
- **Use for:** Model performance dashboards
- **Metrics included:**
  - `model_inference_requests_total` by model, provider, status
  - `model_inference_duration_seconds` by model, provider
  - `tokens_used_total` by model, provider
  - `credits_used_total` by model, provider

### 5. **GET /business**
- **Response:** Prometheus text format
- **Use for:** Business metrics dashboards
- **Metrics included:**
  - `active_api_keys`
  - `subscription_count`
  - `trial_active`
  - `tokens_used_total`
  - `credits_used_total`

### 6. **GET /performance**
- **Response:** Prometheus text format
- **Use for:** Performance and latency dashboards
- **Metrics included:**
  - `fastapi_requests_duration_seconds` (p95)
  - `database_query_duration_seconds` (p95)
  - Cache hit rate calculations
  - `cache_size_bytes`

### 7. **GET /all**
- **Response:** Prometheus text format
- **Use for:** Complete metric export, used by Prometheus scraper
- **Metrics included:** All of the above combined

### 8. **GET /docs**
- **Response:** Markdown text
- **Use for:** API documentation

---

## 🔌 Grafana Integration

Once endpoints are live, configure Grafana to use them:

### Option 1: Add Backend as Prometheus Datasource (RECOMMENDED)

1. **In Grafana:** Data Sources → New → Prometheus
2. **Configure:**
   - Name: `GatewayZ Backend`
   - URL: `http://gatewayz-staging.up.railway.app` (or `http://backend:8000` for local)
   - HTTP Method: GET
   - Custom Header:
     - Name: `Authorization`
     - Value: `Bearer YOUR_TOKEN` (if authentication required)
3. **Test:** Click "Save & Test"

4. **Use in dashboards:**
   ```promql
   # Query examples
   sum(fastapi_requests_total)
   provider_availability{provider="openrouter"}
   sum(rate(tokens_used_total[5m])) * 60
   ```

### Option 2: Query Summary Endpoint Directly (For Widgets)

Use Grafana JSON API datasource or custom HTTP datasource to query `/prometheus/metrics/summary` and parse JSON response.

---

## 🧪 Testing Checklist

After integration, verify:

- [ ] `/prometheus/metrics/summary` returns JSON with all metric categories
- [ ] `/prometheus/metrics/system` returns valid Prometheus text format
- [ ] `/prometheus/metrics/providers` returns provider metrics
- [ ] `/prometheus/metrics/models` returns model metrics
- [ ] `/prometheus/metrics/business` returns business metrics
- [ ] `/prometheus/metrics/performance` returns performance metrics
- [ ] `/prometheus/metrics/all` combines all metrics
- [ ] `/prometheus/metrics/docs` returns documentation
- [ ] All endpoints respond in <200ms
- [ ] Prometheus is accessible from the application
- [ ] Metrics are current (timestamps are recent)

**Test script:**
```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

echo "Testing Prometheus metrics endpoints..."

echo "✓ Testing /summary..."
curl -s "$BASE_URL/prometheus/metrics/summary" | jq . > /dev/null && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /system..."
curl -s "$BASE_URL/prometheus/metrics/system" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /providers..."
curl -s "$BASE_URL/prometheus/metrics/providers" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /models..."
curl -s "$BASE_URL/prometheus/metrics/models" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /business..."
curl -s "$BASE_URL/prometheus/metrics/business" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /performance..."
curl -s "$BASE_URL/prometheus/metrics/performance" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /all..."
curl -s "$BASE_URL/prometheus/metrics/all" | wc -l && echo "  PASS" || echo "  FAIL"

echo "✓ Testing /docs..."
curl -s "$BASE_URL/prometheus/metrics/docs" | wc -l && echo "  PASS" || echo "  FAIL"

echo "All tests completed!"
```

---

## ⚠️ Important Notes

### Prometheus Connectivity

The module assumes Prometheus is accessible at:
- **Local/Docker:** `http://prometheus:9090`
- **Railway/Production:** `http://prometheus.internal:9090` or set via `PROMETHEUS_URL` env var

**If Prometheus is unreachable:**
- `/summary` returns error object
- `/system`, `/providers`, etc. return empty Prometheus format
- Check logs for connection errors

### Error Handling

The module gracefully handles errors:
- Missing metrics return "N/A" in summary
- Failed queries return empty lines in Prometheus format
- Errors are logged but don't crash the application
- Prometheus downtime doesn't take down your API

### Performance

- **Summary endpoint:** Queries 20+ metrics, typically <50ms
- **Category endpoints:** Each queries 4-8 metrics, typically <100ms
- **All endpoint:** Combines all, typically <200ms

**Optimization tips:**
- Cache responses for 5-10 seconds if needed
- Use summary endpoint for dashboards (lighter than full metrics)
- Limit refresh rate to 15-30 second intervals in Grafana

---

## 🗑️ Removing health-service-exporter

Once these endpoints are live and tested:

1. **Stop using health-service-exporter:**
   - Remove from docker-compose.yml
   - Remove from prometheus/prom.yml scrape jobs
   - Stop the service

2. **Update any code that relied on it:**
   - Health service data now comes through backend
   - Metrics format changed from exporter to backend format

3. **Deadline:** January 7, 2026

See: `health-service-exporter/DEPRECATION_NOTICE.md`

---

## 📞 Support

If you encounter issues:

1. **Prometheus connection errors:**
   - Verify `PROMETHEUS_URL` environment variable
   - Check Prometheus is running and accessible
   - Check firewall/networking rules

2. **Missing metrics:**
   - Verify metrics are being exported to Prometheus
   - Check Prometheus targets page
   - Verify PromQL queries manually in Prometheus UI

3. **Slow responses:**
   - Check Prometheus performance
   - Reduce refresh rate in Grafana
   - Cache responses in your application

4. **Module errors:**
   - Check application logs
   - Verify all dependencies installed (`httpx`)
   - Check Python version (3.9+ required)

---

## 📚 Related Documentation

- `PROMETHEUS_METRICS_MODULE.py` - Complete implementation
- `health-service-exporter/DEPRECATION_NOTICE.md` - Removal timeline
- `docs/backend/BACKEND_METRICS_REQUIREMENTS.md` - Metrics requirements
- Grafana dashboard integration guide (from other agent)

---

## ✅ Completion Checklist

- [ ] Module copied to `app/services/prometheus_metrics.py`
- [ ] FastAPI app updated with route setup
- [ ] Tested all 8 endpoints locally
- [ ] Deployed to staging
- [ ] Verified in staging environment
- [ ] Grafana updated to use new endpoints
- [ ] Dashboard panels working with new data
- [ ] Documentation updated
- [ ] Ready for production deployment

---

**Questions?** Contact the monitoring infrastructure team.

**Ready to start?** Copy `PROMETHEUS_METRICS_MODULE.py` into your backend and follow the integration steps above.

Good luck! 🚀
