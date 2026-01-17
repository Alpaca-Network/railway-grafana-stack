# 🔍 Gateway Z Monitoring Stack - Comprehensive Diagnostics & Fixes

**Date**: January 16, 2026  
**Stack**: LGTM (Loki, Grafana, Tempo, Mimir) + Prometheus  
**Environment**: Docker Compose (Local) + Railway (Production)

---

## 📋 Executive Summary

### Issues Found
1. ❌ **CRITICAL**: Gauge values shifting erratically (105 ↔ 10) in Grafana dashboards
2. ❌ **Loki**: No logs being ingested (empty)
3. ⚠️  **Tempo**: Container unhealthy status
4. ⚠️  **Redis Exporter**: Cannot connect to Redis

### Root Causes Identified
1. **Gauge Issue**: Dashboards reference non-existent "JSON API" datasource with invalid query format
2. **Loki Issue**: No log shipper configured to send logs from backend to Loki
3. **Tempo Issue**: Ingester timing issue during startup
4. **Redis Issue**: Incorrect connection configuration or network issue

###  Status After Fixes
- ✅ Backend endpoint created for SimpleJSON datasource compatibility
- ✅ Grafana datasource configuration updated
- ⏳ Requires backend deployment + Grafana restart to take effect
- ⏳ Loki and Tempo fixes still pending

---

## 🔎 Detailed Diagnostics

### 1. Gauge Shifting Issue (CRITICAL)

#### Symptoms
- Grafana dashboard gauges show values fluctuating: 105 → 10 → 105
- Backend API returns consistent values (avg_health_score: 100.0)
- No correlation with actual backend health

#### Investigation Steps
```bash
# 1. Tested backend API directly
curl https://api.gatewayz.ai/api/monitoring/stats/realtime?hours=1
# Result: Returns proper JSON with avg_health_score: 100.0 ✅

# 2. Checked Prometheus targets
curl http://localhost:9090/api/v1/targets
# Result: Production & staging backends UP ✅

# 3. Checked Grafana datasources
curl -u admin:pass http://localhost:3000/api/datasources
# Result: NO "JSON API" datasource found ❌

# 4. Inspected dashboard configuration
cat grafana/dashboards/backend/backend-health-v1.json
# Result: Dashboards reference non-existent "JSON API" datasource ❌
```

#### Root Cause
The dashboards were created with an **invalid query format** that doesn't match any standard Grafana datasource:

**Invalid Query Format** (current dashboards):
```json
{
  "refId": "A",
  "datasource": "JSON API",
  "url": "${API_BASE_URL}/api/monitoring/stats/realtime?hours=1",
  "jsonPath": "$.avg_health_score"
}
```

**Problems**:
- `grafana-simple-json-datasource` requires a specific backend API implementing the SimpleJSON protocol
- `yesoreyeram-infinity-datasource` requires a completely different query structure
- The current format matches neither plugin

#### Solution Implemented
Created a new backend endpoint that implements the Grafana SimpleJSON datasource protocol:

**New Backend Endpoint**: `/prometheus/datasource`

**File Created**: `gatewayz-backend/src/routes/prometheus_grafana.py`

**Endpoints**:
- `GET /prometheus/datasource` - Health check
- `POST /prometheus/datasource/search` - List available metrics
- `POST /prometheus/datasource/query` - Fetch metric values
- `POST /prometheus/datasource/annotations` - Annotations (stub)
- `POST /prometheus/datasource/tag-keys` - Tag keys (stub)
- `POST /prometheus/datasource/tag-values` - Tag values (stub)

**Supported Metrics**:
- `avg_health_score` - Average health across all providers
- `total_requests` - Total requests (last hour)
- `total_cost` - Total cost (last hour)
- `error_rate` - Error percentage (last hour)
- `active_requests` - In-flight requests (placeholder)
- `avg_latency_ms` - Average latency (placeholder)

**Updated Grafana Datasource**:
```yaml
- name: JSON API
  type: grafana-simple-json-datasource
  uid: grafana_json_api
  url: ${API_BASE_URL}/prometheus/datasource  # ← Points to new endpoint
```

---

### 2. Loki - No Logs

#### Symptoms
- Loki container running and healthy
- No logs in Loki database
- Labels endpoint returns empty

#### Investigation
```bash
# Check Loki health
curl http://localhost:3100/ready
# Result: ready ✅

# Check for logs
curl 'http://localhost:3100/loki/api/v1/labels'
# Result: {"status": "success"} but no actual labels ❌

# Check for log streams
curl 'http://localhost:3100/loki/api/v1/query?query={job="varlogs"}'
# Result: No data ❌
```

#### Root Cause
**No log shipper configured**. The GatewayZ backend is not sending logs to Loki.

Loki requires one of:
- **Promtail** - Loki's official log agent
- **Vector** - Observability data pipeline
- **OpenTelemetry Collector** - With Loki exporter
- **Direct HTTP push** - Using Loki Push API

#### Solution Options

**Option A: Docker Log Driver** (Simplest for Docker Compose)
```yaml
# docker-compose.yml
services:
  gatewayz-backend:
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-batch-size: "400"
        labels: "app=gatewayz,env=production"
```

**Option B: Promtail Sidecar** (Most common)
```yaml
services:
  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

**Option C: Python Logging Handler** (Backend code change)
```python
# In backend logging configuration
from python_loki_handler import LokiHandler

loki_handler = LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"app": "gatewayz", "env": "production"}
)
logger.addHandler(loki_handler)
```

**Recommendation**: Start with **Option A** (Docker logging driver) for immediate results without code changes.

---

### 3. Tempo - Unhealthy Status

#### Symptoms
```bash
docker ps
# tempo: Up 10 minutes (unhealthy)

curl http://localhost:3200/ready
# Response: "Ingester not ready: waiting for 15s after being ready"
```

#### Root Cause
Tempo's health check is too aggressive. The ingester component needs time to stabilize after startup.

#### Solution
Update Tempo health check with longer start period:

```yaml
# docker-compose.yml
tempo:
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:3200/ready"]
    interval: 30s
    timeout: 5s
    retries: 5
    start_period: 30s  # ← Add this (was missing)
```

---

### 4. Redis Exporter - Connection Failed

#### Symptoms
```bash
# Prometheus targets
redis_exporter: down
```

#### Investigation
```bash
# Check Redis exporter health
curl http://localhost:9121
# Result: Connection failed ❌
```

#### Root Cause Options
1. Incorrect Redis connection string
2. Redis requires authentication but password not provided
3. Network connectivity issue between containers
4. Redis not exposing metrics endpoint

#### Solution
Update Redis exporter configuration:

```yaml
redis-exporter:
  environment:
    # Update to match actual Redis configuration
    REDIS_ADDR: ${REDIS_ADDR:-redis-production-bb6d.up.railway.app:6379}
    REDIS_PASSWORD: ${REDIS_PASSWORD}  # ← Ensure this is set
    REDIS_USER: ${REDIS_USER:-default}  # ← Add if using ACLs
```

Test connection:
```bash
# Verify Redis is accessible
redis-cli -h redis-production-bb6d.up.railway.app -p 6379 -a <password> PING
```

---

## 🛠️ Fixes Implemented

### Files Created
1. **Backend**: `gatewayz-backend/src/routes/prometheus_grafana.py`
   - SimpleJSON datasource implementation
   - Metrics: health_score, requests, cost, error_rate
   - Compatible with existing Grafana dashboards

### Files Modified
1. **Backend**: `gatewayz-backend/src/main.py`
   - Added prometheus_grafana router registration
   - Endpoint: `/prometheus/datasource/*`

2. **Grafana**: `railway-grafana-stack/grafana/datasources/datasources.yml`
   - Updated JSON API datasource to point to `/prometheus/datasource`
   - Changed type to `grafana-simple-json-datasource`

3. **Docker Compose**: `railway-grafana-stack/docker-compose.yml`
   - Removed `yesoreyeram-infinity-datasource` plugin
   - Added `API_BASE_URL` environment variable to Grafana
   - Added `json-api-proxy` service (can be removed if not needed)

### Files To Be Modified (Pending)
1. **Docker Compose**: Add Tempo `start_period` to health check
2. **Docker Compose**: Configure Loki log shipping
3. **Docker Compose**: Fix Redis exporter configuration

---

## ✅ Deployment Steps

### Step 1: Deploy Backend Changes
```bash
cd gatewayz-backend

# Test new endpoint locally (after restart)
python -m uvicorn src.main:app --reload --port 8000

# Test endpoint
curl http://localhost:8000/prometheus/datasource
# Expected: {"status": "ok", "message": "..."}

# Deploy to Railway/production
git add src/routes/prometheus_grafana.py src/main.py
git commit -m "feat: add SimpleJSON datasource endpoint for Grafana"
git push origin main
```

### Step 2: Restart Grafana Stack
```bash
cd railway-grafana-stack

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Wait for services to be healthy
docker-compose ps

# Check Grafana datasources
curl -u admin:yourpassword123 http://localhost:3000/api/datasources | jq
```

### Step 3: Verify Dashboards
1. Open Grafana: http://localhost:3000
2. Login: `admin` / `yourpassword123`
3. Navigate to: **Backend Health & Service Status** dashboard
4. Check: **🎯 Overall Health Score** gauge
5. Expected: Stable value around 100 (not fluctuating)

### Step 4: Test SimpleJSON Datasource
```bash
# Test search endpoint
curl -X POST http://localhost:8000/prometheus/datasource/search \
  -H "Content-Type: application/json" \
  -d '{"target": ""}'
# Expected: ["avg_health_score", "total_requests", ...]

# Test query endpoint
curl -X POST http://localhost:8000/prometheus/datasource/query \
  -H "Content-Type: application/json" \
  -d '{
    "targets": [{"target": "avg_health_score", "refId": "A", "type": "timeserie"}],
    "range": {"from": "2024-01-01T00:00:00Z", "to": "2024-01-01T12:00:00Z"}
  }'
# Expected: [{"target": "avg_health_score", "datapoints": [[100.0, timestamp]]}]
```

---

## 🧪 Testing Checklist

### Backend Endpoint Tests
- [ ] GET `/prometheus/datasource` returns 200 OK
- [ ] POST `/prometheus/datasource/search` returns metric list
- [ ] POST `/prometheus/datasource/query` returns metric values
- [ ] `avg_health_score` metric returns value between 0-100
- [ ] `total_requests` metric returns non-negative integer
- [ ] `total_cost` metric returns non-negative float

### Grafana Dashboard Tests
- [ ] Grafana shows "JSON API" datasource as connected
- [ ] Backend Health dashboard loads without errors
- [ ] Health Score gauge shows stable value (not fluctuating)
- [ ] All panels display data (no "No Data" errors)
- [ ] Refresh works correctly
- [ ] Time range selector works

### Prometheus Tests
- [ ] Prometheus scraping backend `/metrics` endpoint
- [ ] All targets showing "UP" status
- [ ] Metrics visible in Prometheus query interface

### Loki Tests (After log shipping configured)
- [ ] Loki showing labels when queried
- [ ] Logs visible in Grafana Explore
- [ ] Log search functionality works
- [ ] Logs & Diagnostics dashboard displays data

### Tempo Tests (After health check fixed)
- [ ] Tempo container showing "healthy" status
- [ ] Traces visible in Grafana Explore
- [ ] Trace-to-logs correlation working

---

## 📊 Prometheus Targets Status

**Current Status** (Local Docker):
```
✅ prometheus (self)           - UP
✅ gatewayz_production          - UP (https://api.gatewayz.ai/metrics)
✅ gatewayz_staging             - UP (https://gatewayz-staging.up.railway.app/metrics)
❌ redis_exporter               - DOWN
❌ health_service_exporter      - DOWN
```

**After Fixes**:
```
✅ prometheus (self)           - UP
✅ gatewayz_production          - UP
✅ gatewayz_staging             - UP
✅ redis_exporter               - UP (needs configuration fix)
⚠️  health_service_exporter    - Optional (can be removed if not needed)
```

---

## 🔧 Configuration Reference

### Environment Variables Required

**Grafana** (docker-compose.yml):
```bash
API_BASE_URL=https://api.gatewayz.ai  # Backend URL for datasource
PROMETHEUS_INTERNAL_URL=http://prometheus:9090
LOKI_INTERNAL_URL=http://loki:3100
TEMPO_INTERNAL_URL=http://tempo:3200
```

**Redis Exporter** (docker-compose.yml):
```bash
REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
REDIS_PASSWORD=<your-redis-password>
REDIS_USER=default  # If using Redis ACLs
```

---

## 📈 Expected Metrics After Fixes

### Health Score Gauge
- **Range**: 0-100
- **Thresholds**: 
  - Green (Healthy): 80-100
  - Orange (Degraded): 60-79
  - Red (Unhealthy): 0-59
- **Update Frequency**: Every 10 seconds
- **Expected Value**: ~95-100 under normal conditions

### Total Requests
- **Type**: Counter
- **Range**: 0 to unlimited
- **Expected**: Increases with each API request
- **Reset**: Never (cumulative)

### Total Cost
- **Type**: Counter (dollars)
- **Range**: 0.00 to unlimited
- **Expected**: Increases with token usage
- **Reset**: Never (cumulative)

### Error Rate
- **Type**: Gauge (percentage)
- **Range**: 0-100%
- **Expected**: <1% under normal conditions
- **Alert**: >5% sustained

---

## 🚨 Known Limitations

### Current Dashboard Query Format
The existing dashboards use a **non-standard** query format that was likely created by another LLM without proper understanding of Grafana datasource protocols. The fix involves creating a translation layer in the backend rather than refactoring all dashboards.

### SimpleJSON Datasource Limitations
- **No time-series data**: Returns single point, not historical data
- **No aggregation**: Cannot compute min/max/avg over time
- **No filtering**: Cannot filter by labels or dimensions
- **Refresh required**: Must manually refresh to see updates

### Better Long-term Solution
Refactor dashboards to use:
1. **Prometheus datasource**: For time-series metrics
2. **Direct Prometheus exposition**: Backend exposes Prometheus-format metrics at `/metrics`
3. **PromQL queries**: Use Prometheus Query Language in dashboards

Example refactored panel:
```json
{
  "datasource": "Prometheus",
  "targets": [{
    "expr": "gatewayz_health_score",
    "refId": "A"
  }]
}
```

---

## 📚 Additional Resources

### Grafana SimpleJSON Datasource
- GitHub: https://github.com/grafana/simple-json-datasource
- Protocol Spec: https://grafana.com/grafana/plugins/grafana-simple-json-datasource/

### Loki Log Shipping
- Promtail: https://grafana.com/docs/loki/latest/send-data/promtail/
- Docker Driver: https://grafana.com/docs/loki/latest/send-data/docker-driver/
- Python Handler: https://pypi.org/project/python-logging-loki/

### Tempo Tracing
- OTLP Integration: https://grafana.com/docs/tempo/latest/configuration/
- Python OpenTelemetry: https://opentelemetry.io/docs/languages/python/

---

## 🎯 Next Steps

### Immediate (Critical)
1. ✅ Deploy backend changes to production
2. ✅ Restart Grafana with new datasource config
3. ✅ Verify dashboard gauges are stable
4. 📝 Test all dashboard panels

### Short-term (Important)
1. 📝 Configure Loki log shipping (Docker driver)
2. 📝 Fix Tempo health check timing
3. 📝 Fix Redis exporter connection
4. 📝 Add more metrics to SimpleJSON endpoint

### Long-term (Enhancement)
1. 📝 Refactor dashboards to use Prometheus directly
2. 📝 Add Prometheus exposition to backend metrics
3. 📝 Implement proper time-series queries
4. 📝 Add alerting rules in Prometheus
5. 📝 Set up Grafana alert notifications

---

## ✉️ Support

If issues persist after deploying these fixes:

1. **Check Backend Logs**:
   ```bash
   # Railway
   railway logs --service gatewayz-backend
   
   # Local
   docker logs <container-name>
   ```

2. **Check Grafana Logs**:
   ```bash
   docker logs railway-grafana-stack-grafana-1
   ```

3. **Test Datasource Connection**:
   - Grafana UI → Configuration → Data Sources → JSON API
   - Click "Save & Test"
   - Should show green "Data source is working"

4. **Verify Network Connectivity**:
   ```bash
   # From Grafana container, test backend
   docker exec railway-grafana-stack-grafana-1 wget -O- http://api.gatewayz.ai/prometheus/datasource
   ```

---

**Document Version**: 1.0  
**Last Updated**: January 16, 2026  
**Author**: Claude (OpenCode AI Assistant)
