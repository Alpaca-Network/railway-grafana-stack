# Data Flow Verification: Prometheus → Mimir → Grafana

## Current Configuration Status

Based on the code review, here's what's configured:

### ✅ Prometheus → Mimir (Remote Write)
**File**: `prometheus/prom.yml`
```yaml
remote_write:
  - url: MIMIR_URL/api/v1/push  # Substituted at runtime
    name: mimir-remote-write
```

**Substitution logic** (`prometheus/entrypoint.sh`):
- If `RAILWAY_ENVIRONMENT` is set → Uses `http://mimir.railway.internal:9009`
- Otherwise → Uses `http://mimir:9009` (Docker Compose default)

**Status**: ✅ Configured, but needs `RAILWAY_ENVIRONMENT=production` env var set on Prometheus service

---

### ✅ Grafana → Mimir (Query)
**File**: `grafana/datasources/datasources.yml`
```yaml
- name: Mimir
  type: prometheus
  url: ${MIMIR_INTERNAL_URL:-http://mimir:9009}/prometheus
  uid: grafana_mimir
```

**Default** (`grafana/Dockerfile`):
```dockerfile
ENV MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
```

**Status**: ✅ Already configured to use Railway internal network

---

### ✅ Prometheus → Mimir (Scraping)
**File**: `prometheus/prom.yml`
```yaml
- job_name: 'mimir'
  static_configs:
    - targets: ['MIMIR_TARGET']  # Substituted to mimir.railway.internal:9009
```

**Status**: ✅ Configured, scrapes Mimir's own metrics

---

## What You Need to Verify

### Step 1: Set Prometheus Environment Variable

**Railway Dashboard → Prometheus Service → Variables:**

Add:
```
RAILWAY_ENVIRONMENT=production
```

This enables Prometheus to use the Railway internal network for Mimir.

---

### Step 2: Run the Test Script

I've created a comprehensive test script: `test-prometheus-mimir-grafana-flow.sh`

**On Railway**, run:
```bash
railway run --service prometheus bash test-prometheus-mimir-grafana-flow.sh
```

Or download and run locally with proper environment variables set.

**What it checks:**

1. **Service Accessibility**
   - ✓ Prometheus is up
   - ✓ Mimir is up  
   - ✓ Grafana is up

2. **Prometheus Configuration**
   - ✓ Prometheus has Mimir in remote_write config
   - ✓ Using Railway internal network
   - ✓ Sending samples to Mimir

3. **Mimir Ingestion**
   - ✓ Mimir receiving samples
   - ✓ Mimir has active time series
   - ✓ Can query metrics from Mimir

4. **Grafana → Mimir**
   - ✓ Grafana has Mimir datasource
   - ✓ Using Railway internal network
   - ✓ Can query data from Mimir

**Expected output** (when everything works):
```
==================================================
Summary Report
==================================================

Checks passed: 11 / 11

Data Flow Status:
┌─────────────┐    remote_write    ┌──────┐    query    ┌─────────┐
│ Prometheus  │ ──────────────────> │ Mimir│ <────────── │ Grafana │
└─────────────┘                     └──────┘             └─────────┘

✓ Prometheus → Mimir: Data flowing
✓ Mimir: Receiving and storing data
✓ Grafana → Mimir: Can query data

🎉 All checks passed! The data flow is working correctly.
```

---

## Manual Verification

### Check 1: Prometheus Remote Write Status

**Prometheus UI** → **Status → TSDB Status**

Look for "Remote Write" section:
- **Samples sent**: Should be thousands/millions (increasing)
- **Failed sends**: Should be 0
- **Retries**: Should be low/stable

Or query:
```promql
prometheus_remote_storage_samples_total
```

### Check 2: Mimir Ingestion

**Mimir API** (via curl or Grafana):
```bash
curl http://mimir.railway.internal:9009/prometheus/api/v1/query?query=cortex_ingester_ingested_samples_total
```

Should return increasing values.

### Check 3: Grafana Mimir Datasource

**Grafana UI** → **Connections → Data sources → Mimir**

- **Status**: Should show green check mark
- **Test**: Click "Save & test" → Should succeed

### Check 4: Query Metrics from Mimir in Grafana

**Grafana UI** → **Explore**

1. Select **Mimir** datasource (not Prometheus)
2. Query: `up`
3. Should see time series data

Compare with **Prometheus** datasource:
- Prometheus: Recent data (last 15 days)
- Mimir: All historical data (30+ days)

---

## Troubleshooting

### Issue: Prometheus not sending to Mimir

**Check**:
```bash
railway logs --service prometheus | grep -i "remote\|mimir"
```

**Look for**:
- "Using Railway internal network for Mimir"
- "Mimir URL: http://mimir.railway.internal:9009"

**If not found**:
- `RAILWAY_ENVIRONMENT` not set → Add it to Prometheus service

**Check errors**:
```promql
prometheus_remote_storage_samples_failed_total
```

If > 0:
- Mimir not accessible
- Network issue between Prometheus and Mimir
- Mimir configuration error

### Issue: Mimir not ingesting

**Check Mimir logs**:
```bash
railway logs --service mimir | grep -i "error\|ingester"
```

**Common causes**:
1. `kvstore: memberlist` (needs clustering) → Use `kvstore: inmemory`
2. Missing `instance_addr: 127.0.0.1` in rings
3. Mimir not listening on 0.0.0.0:9009

**Verify Mimir is accepting writes**:
```bash
curl -X POST http://mimir.railway.internal:9009/api/v1/push \
  -H "Content-Type: application/x-protobuf" \
  -d ""
```

Should NOT return 404.

### Issue: Grafana can't query Mimir

**Check Grafana datasource config**:

**Grafana UI** → **Connections → Data sources → Mimir**

- **URL**: Should be `http://mimir.railway.internal:9009/prometheus`
- **Access**: Should be "Server (default)" or "Proxy"

**Check Grafana logs**:
```bash
railway logs --service grafana | grep -i "mimir\|datasource"
```

**Test direct query**:
```bash
curl http://mimir.railway.internal:9009/prometheus/api/v1/query?query=up
```

Should return JSON with time series.

### Issue: Different data in Prometheus vs Mimir

**This is normal!**

- **Prometheus**: Recent data (15-day retention)
- **Mimir**: Long-term storage (30+ days)

Mimir only stores data from the time Prometheus started sending to it.

**To verify sync**:

Query same time range in both:
```promql
up{job="prometheus"}[5m]
```

Should show same recent values in both Prometheus and Mimir.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Railway Internal Network (*.railway.internal)              │
│                                                              │
│  ┌─────────────────┐                                        │
│  │   Prometheus    │                                        │
│  │   :9090         │                                        │
│  │                 │                                        │
│  │  Scrapes:       │                                        │
│  │  - Backend      │                                        │
│  │  - Redis        │                                        │
│  │  - Mimir (own)  │                                        │
│  │  - Tempo        │                                        │
│  │  - Loki         │                                        │
│  └────────┬────────┘                                        │
│           │                                                  │
│           │ remote_write                                    │
│           │ POST /api/v1/push                               │
│           │ (every 30s)                                     │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────┐                                        │
│  │     Mimir       │                                        │
│  │     :9009       │                                        │
│  │                 │                                        │
│  │  Stores:        │◄─────────────────┐                    │
│  │  - Metrics      │  query            │                    │
│  │  - Long-term    │  /prometheus/api  │                    │
│  │  - TSDB blocks  │                   │                    │
│  └─────────────────┘                   │                    │
│                                         │                    │
│                                    ┌────┴────────┐          │
│                                    │   Grafana   │          │
│                                    │    :3000    │          │
│                                    │             │          │
│                                    │  Datasources:         │
│                                    │  - Prometheus         │
│                                    │  - Mimir              │
│                                    │  - Tempo              │
│                                    │  - Loki               │
│                                    └─────────────┘          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Data flow**:
1. Prometheus scrapes metrics from all services
2. Prometheus stores recent 15 days locally
3. Prometheus forwards all metrics to Mimir via remote_write
4. Mimir stores metrics long-term (30+ days)
5. Grafana queries Prometheus for recent data
6. Grafana queries Mimir for historical data
7. Dashboards can use either datasource

---

## Expected Metrics in Mimir

After Prometheus starts sending to Mimir, you should see:

**All Prometheus metrics**, including:
- `up` - Target health
- `prometheus_*` - Prometheus internals
- `http_requests_total` - Backend metrics
- `fastapi_*` - FastAPI metrics
- `redis_*` - Redis metrics
- `cortex_*` - Mimir's own metrics
- Custom app metrics from backend

**Query in Grafana Explore**:
```promql
# See all metric names
{__name__=~".+"}

# Count unique metrics
count({__name__=~".+"})

# Should be hundreds/thousands
```

---

## Validation Checklist

- [ ] Set `RAILWAY_ENVIRONMENT=production` on Prometheus service
- [ ] Wait 2-3 minutes for Prometheus to redeploy
- [ ] Run `test-prometheus-mimir-grafana-flow.sh` script
- [ ] Verify all 11 checks pass
- [ ] Check Prometheus Status → TSDB → Remote Write shows samples sent
- [ ] Query `cortex_ingester_ingested_samples_total` in Mimir
- [ ] Test Mimir datasource in Grafana (Save & test)
- [ ] Query `up` metric from Mimir datasource in Grafana Explore
- [ ] Verify Mimir dashboard shows active series and ingestion rate
- [ ] Compare recent data in Prometheus vs Mimir (should match)

---

## Files Reference

**Configuration**:
- `prometheus/prom.yml` - Prometheus config with Mimir remote_write
- `prometheus/entrypoint.sh` - Runtime URL substitution
- `grafana/datasources/datasources.yml` - Grafana datasources including Mimir
- `grafana/Dockerfile` - Sets MIMIR_INTERNAL_URL default
- `mimir/mimir-railway.yml` - Mimir configuration

**Testing**:
- `test-prometheus-mimir-grafana-flow.sh` - Comprehensive data flow test
- `PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md` - Prometheus→Mimir setup guide

**Documentation**:
- `MIMIR.md` - Complete Mimir documentation
- `DATA_FLOW_VERIFICATION.md` - This file

---

**Last Updated**: January 24, 2026
