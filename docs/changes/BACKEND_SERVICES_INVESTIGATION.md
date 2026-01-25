# Backend Services Dashboard Investigation

**Branch:** `fix/backend-services-schema`  
**Date:** January 21, 2026  
**Issue:** User reports "schema unsupported" error

---

## Investigation Results

### Dashboard Status: ✅ Configuration Appears Correct

**File:** `grafana/dashboards/backend/backend-services-v1.json`

### Verified Items:

#### 1. Datasource Configuration ✅
- **All panels use:** `grafana_mimir` (type: prometheus)
- **Count:** 40 datasource references
- **UID:** `grafana_mimir`
- **Type:** `prometheus`

**Example:**
```json
{
  "datasource": {
    "type": "prometheus",
    "uid": "grafana_mimir"
  }
}
```

#### 2. PromQL Queries ✅

**Redis Metrics:**
```promql
redis_up
(redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)) * 100
(redis_memory_used_bytes / redis_memory_max_bytes) * 100
redis_connected_clients
sum(redis_db_keys)
rate(redis_commands_processed_total[5m])
```

**API Metrics:**
```promql
sum(increase(http_requests_total{env=~"$environment"}[$__range]))
sum(rate(http_requests_total{env=~"$environment"}[5m]))
sum(rate(http_requests_total{env=~"$environment", status_code=~"4..|5.."}[5m])) / sum(rate(http_requests_total{env=~"$environment"}[5m])) * 100
```

**All queries are valid PromQL syntax ✅**

#### 3. Schema Version ✅
- **schemaVersion:** 39
- **Compatible with:** Grafana 11.5.2
- **Status:** Valid

#### 4. JSON Syntax ✅
- **Validation:** Passed `python3 -m json.tool`
- **File size:** 1,753 lines
- **Status:** Well-formed JSON

#### 5. Dashboard Metadata ✅
```json
{
  "title": "Backend Services - Prometheus/Mimir",
  "uid": "backend-services-v1",
  "version": 1,
  "refresh": "10s",
  "schemaVersion": 39,
  "tags": ["gatewayz", "backend", "redis", "api", "prometheus", "mimir"]
}
```

#### 6. Variables Configuration ✅
```json
{
  "name": "environment",
  "type": "query",
  "datasource": {
    "type": "prometheus",
    "uid": "grafana_mimir"
  },
  "query": "label_values(http_requests_total, env)"
}
```

---

## Datasource Verification

### Mimir Datasource Configuration

**File:** `grafana/datasources/datasources.yml`

```yaml
- name: Mimir
  type: prometheus
  access: proxy
  orgId: 1
  uid: grafana_mimir
  url: ${MIMIR_INTERNAL_URL:-http://mimir:9009}/prometheus
  jsonData:
    httpMethod: POST
    manageAlerts: false
    prometheusType: Mimir
    prometheusVersion: 2.11.0
    timeout: 60
    exemplarTraceIdDestinations:
      - datasourceUid: grafana_tempo
        name: traceId
```

**Status:** ✅ Correctly configured

---

## Possible Causes of "Schema Unsupported" Error

### 1. Grafana Version Mismatch
**Check:** What version of Grafana is running?
```bash
# In Grafana UI: Configuration → About
# Or via API:
curl http://localhost:3000/api/health
```

**Expected:** Grafana 11.5.2 (matches pluginVersion in dashboard)

### 2. Mimir Not Running
**Check:** Is Mimir service healthy?
```bash
curl http://localhost:9009/ready
# Should return: "ready"
```

### 3. Mimir URL Incorrect
**Check:** Environment variable
```bash
echo $MIMIR_INTERNAL_URL
# Expected: http://mimir:9009 (Docker) or http://mimir.railway.internal:9009 (Railway)
```

### 4. Prometheus Remote Write Not Working
**Check:** Is Prometheus writing to Mimir?
```bash
# Check Prometheus logs
docker logs railway-grafana-stack-prometheus-1 | grep -i mimir

# Check Mimir metrics
curl http://localhost:9009/prometheus/api/v1/query?query=up
```

### 5. Dashboard Import Issue
**Possible:** Dashboard was manually imported and lost some metadata

**Solution:** Re-provision the dashboard
```bash
# Restart Grafana to re-provision
docker compose restart grafana
```

---

## Debugging Steps

### Step 1: Verify Datasource Health in Grafana

1. Open Grafana: `http://localhost:3000`
2. Go to: **Configuration** → **Data Sources**
3. Click on **Mimir**
4. Click **Test** button
5. **Expected:** "Data source is working"

### Step 2: Check Query Inspector

1. Open Backend Services dashboard
2. Click on any panel
3. Click **Inspect** → **Query**
4. Check for errors in the query response

### Step 3: Verify Metrics Exist

```bash
# Check if Redis metrics exist in Mimir
curl 'http://localhost:9009/prometheus/api/v1/query?query=redis_up'

# Check if API metrics exist
curl 'http://localhost:9009/prometheus/api/v1/query?query=http_requests_total'
```

### Step 4: Check Grafana Logs

```bash
docker logs railway-grafana-stack-grafana-1 | tail -50
# Look for datasource or panel errors
```

---

## Quick Fixes to Try

### Fix 1: Restart All Services
```bash
docker compose down
docker compose up -d
```

### Fix 2: Clear Grafana Cache
```bash
# Remove Grafana data volume (WARNING: loses custom dashboards)
docker compose down -v
docker compose up -d
```

### Fix 3: Re-import Dashboard

1. Delete current Backend Services dashboard in Grafana UI
2. Restart Grafana: `docker compose restart grafana`
3. Dashboard will be re-provisioned automatically

### Fix 4: Use Prometheus Instead of Mimir Temporarily

If Mimir is not working, we can switch back to Prometheus:

```bash
sed -i 's/"uid": "grafana_mimir"/"uid": "grafana_prometheus"/g' \
  grafana/dashboards/backend/backend-services-v1.json
```

---

## Data Flow Check

**Expected data flow:**

```
1. Backend API exposes /metrics
2. Prometheus scrapes /metrics every 15s
3. Prometheus writes to Mimir via remote_write
4. Grafana queries Mimir for dashboard panels
5. Backend Services dashboard shows data
```

**Check each step:**

```bash
# 1. Backend API has metrics
curl https://api.gatewayz.ai/metrics | head -20

# 2. Prometheus is scraping
curl http://localhost:9090/api/v1/targets | grep -A5 "gatewayz_production"

# 3. Prometheus writing to Mimir
curl http://localhost:9090/api/v1/status/config | grep -A3 "remote_write"

# 4. Mimir has data
curl 'http://localhost:9009/prometheus/api/v1/query?query=up'

# 5. Grafana can reach Mimir
# (Test in Grafana UI → Data Sources → Mimir → Test)
```

---

## Next Steps

**Please provide:**

1. **Exact error message** - Screenshot or copy-paste from Grafana
2. **Where you see the error** - Dashboard UI, panel, or logs?
3. **Grafana version** - Check in UI or via API
4. **Are you on Railway or local Docker?** - Different setup

**With this information, I can provide a specific fix.**

---

## Status

**Dashboard Configuration:** ✅ All correct  
**Datasource References:** ✅ All using `grafana_mimir`  
**PromQL Queries:** ✅ Valid syntax  
**JSON Schema:** ✅ Valid (schemaVersion 39)  

**Likely Issue:** Environment or service connectivity, not dashboard configuration

---

**Awaiting more details about the specific error to proceed with targeted fix.**
