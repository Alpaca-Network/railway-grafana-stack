# Connecting Prometheus to Mimir on Railway

## Issue
Prometheus is not connecting to Mimir via the Railway internal link (`mimir.railway.internal:9009`).

## Root Cause
The Prometheus service needs the `RAILWAY_ENVIRONMENT` environment variable set to detect it's running on Railway and use the internal link.

---

## Solution: Set Environment Variables in Railway

### Option 1: Set RAILWAY_ENVIRONMENT (Recommended)

**Railway Dashboard → Prometheus Service → Variables → Add:**

```
RAILWAY_ENVIRONMENT=production
```

This will make the entrypoint script automatically use:
- Remote write URL: `http://mimir.railway.internal:9009/api/v1/push`
- Scrape target: `mimir.railway.internal:9009`

### Option 2: Explicitly Set Mimir URL

**Railway Dashboard → Prometheus Service → Variables → Add:**

```
MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
```

This directly sets the Mimir endpoint, bypassing auto-detection.

---

## How It Works

The `prometheus/entrypoint.sh` script substitutes placeholders in `prom.yml`:

```sh
# Priority order:
1. MIMIR_INTERNAL_URL (if explicitly set)
2. RAILWAY_ENVIRONMENT (uses mimir.railway.internal:9009)
3. Default (uses mimir:9009 for Docker Compose)
```

**Before substitution** (prom.yml):
```yaml
remote_write:
  - url: MIMIR_URL/api/v1/push

- job_name: 'mimir'
  static_configs:
    - targets: ['MIMIR_TARGET']
```

**After substitution** (on Railway with RAILWAY_ENVIRONMENT set):
```yaml
remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push

- job_name: 'mimir'
  static_configs:
    - targets: ['mimir.railway.internal:9009']
```

---

## Verification Steps

### 1. Set the Environment Variable

In Railway Dashboard:
1. Go to your Prometheus service
2. Click **Variables** tab
3. Add `RAILWAY_ENVIRONMENT=production`
4. Wait for automatic redeploy (2-3 minutes)

### 2. Check Prometheus Logs

```bash
railway logs --service prometheus | grep -i "mimir"

# Should see:
# "Using Railway internal network for Mimir"
# "Mimir URL: http://mimir.railway.internal:9009"
```

### 3. Verify in Prometheus UI

Open Prometheus: `https://prometheus-production-xxxx.up.railway.app`

**Check Configuration:**
- Go to **Status → Configuration**
- Search for `remote_write`
- Should see: `url: http://mimir.railway.internal:9009/api/v1/push`

**Check Targets:**
- Go to **Status → Targets**
- Find job: `mimir`
- Target should be: `mimir.railway.internal:9009`
- State should be: **UP** (green)

**Check Remote Write Status:**
- Go to **Status → TSDB Status**
- Look for "Remote Write" section
- Should show successful writes to Mimir

### 4. Verify in Mimir

Open Mimir: `https://mimir-production-xxxx.up.railway.app`

**Check Ingestion:**
```bash
# Query Mimir's metrics endpoint
curl https://mimir-production-xxxx.up.railway.app/metrics | grep "cortex_ingester_ingested_samples_total"

# Should show increasing sample count
```

### 5. Query Metrics from Mimir

In Prometheus or Grafana, query:
```promql
# Check if Prometheus is writing to Mimir
prometheus_remote_storage_samples_total{url=~".*mimir.*"}

# Should show increasing values
```

---

## Troubleshooting

### Issue: Prometheus still using localhost or Docker service name

**Check:**
```bash
railway logs --service prometheus | grep "Mimir URL"
```

**If it shows** `http://mimir:9009` or `http://localhost:9009`:
- RAILWAY_ENVIRONMENT is not set
- Add the variable in Railway Dashboard

### Issue: Connection refused to mimir.railway.internal

**Causes:**
1. Mimir service not running
2. Services in different Railway projects
3. Mimir not exposing port 9009

**Fix:**
```bash
# Check Mimir is running
railway logs --service mimir | tail -20

# Should see:
# "Server listening on 0.0.0.0:9009"
# "Mimir started successfully"

# Verify both services in same project
railway status
```

### Issue: 502 Gateway Error from Mimir

**This was fixed previously** - Mimir should be running now with:
- `kvstore: inmemory` (not memberlist)
- `instance_addr: 127.0.0.1` in all rings
- Proper entrypoint script

If still seeing 502:
```bash
# Check Mimir logs
railway logs --service mimir | grep -i "error\|failed"

# Restart Mimir
railway restart --service mimir
```

### Issue: No metrics in Mimir

**Check remote write is working:**
```bash
# In Prometheus UI
# Status → TSDB Status → Remote Write

# Should show:
# - Samples sent: increasing number
# - Failed sends: 0
# - Retries: low/stable
```

**Check Mimir ingestion:**
```bash
# Get Mimir internal metrics
curl http://mimir.railway.internal:9009/metrics | grep ingester_ingested_samples

# Or use Prometheus to query Mimir's own metrics
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  Railway Project                                        │
│                                                         │
│  ┌─────────────────┐         ┌──────────────────┐     │
│  │   Prometheus    │         │      Mimir       │     │
│  │  (prometheus    │────────▶│   (mimir.rail    │     │
│  │   .railway      │ remote  │    way.internal  │     │
│  │   .internal)    │ write   │    :9009)        │     │
│  │                 │  HTTP   │                  │     │
│  │  - Scrapes      │         │  - Stores metrics│     │
│  │    metrics      │         │  - Long-term     │     │
│  │  - Evaluates    │         │    TSDB          │     │
│  │    alerts       │         │  - Compaction    │     │
│  │  - Sends to     │         │  - Query API     │     │
│  │    Mimir        │         │                  │     │
│  └─────────────────┘         └──────────────────┘     │
│           │                           ▲                │
│           │                           │                │
│           │ scrape                    │ query          │
│           ▼                           │                │
│  ┌─────────────────┐         ┌──────────────────┐     │
│  │  Other Services │         │     Grafana      │     │
│  │  (backend, etc) │         │  (dashboards)    │     │
│  └─────────────────┘         └──────────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘

Internal Network: *.railway.internal (DNS-based service discovery)
```

---

## Expected Behavior After Fix

### Prometheus Logs
```
Using Railway internal network for Mimir
Mimir URL: http://mimir.railway.internal:9009
Mimir Target: mimir.railway.internal:9009
Substituting MIMIR_URL in config...
Substituting MIMIR_TARGET in config...
Starting Prometheus with config: /etc/prometheus/prometheus.yml
```

### Prometheus Targets Page
- **mimir** target: `mimir.railway.internal:9009` → **UP** (green)
- Last scrape: < 1m ago
- Scrape duration: ~50-200ms

### Prometheus Remote Write
- Samples sent: Thousands/millions (increasing)
- Failed sends: 0
- Current shards: 1-5
- Pending samples: Low (<100)

### Mimir Metrics
```promql
# Total samples ingested
sum(rate(cortex_ingester_ingested_samples_total[5m]))

# Active series in Mimir
cortex_ingester_active_series

# Query rate
sum(rate(cortex_query_frontend_queries_total[5m]))
```

### Grafana Mimir Dashboard
All panels showing data:
- Active Series: 1000+
- Ingestion Rate: 500+ samples/sec
- Storage Blocks: Multiple
- Query Latency: < 100ms P95

---

## Quick Fix Checklist

- [ ] Add `RAILWAY_ENVIRONMENT=production` to Prometheus service variables
- [ ] Wait for Prometheus to redeploy (2-3 min)
- [ ] Check Prometheus logs for "Using Railway internal network"
- [ ] Verify Prometheus Status → Targets shows mimir target UP
- [ ] Verify Prometheus Status → TSDB shows remote write samples
- [ ] Check Mimir dashboard in Grafana for data
- [ ] Query metrics via Mimir API to confirm storage

---

## Related Documentation
- See `MIMIR.md` for full Mimir configuration details
- See `prometheus/entrypoint.sh` for substitution logic
- See `mimir/mimir-railway.yml` for Mimir configuration

**Last Updated:** January 24, 2026
