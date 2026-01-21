# Local Docker Setup - Fix "No Data" Issues

**Problem:** All dashboards show "No Data" when running locally with Docker Compose.

**Root Causes Identified:**

1. ❌ `FASTAPI_TARGET` is set to a literal placeholder string, not a real URL
2. ❌ `REDIS_ADDR` points to Railway internal network (won't work locally)
3. ❌ Staging API returns 401 Unauthorized (bearer token issue)
4. ❌ Backend not running locally on port 8000

---

## 🔧 Quick Fix (Local Development)

### Option 1: Point to Production/Staging APIs (Easiest)

If you just want to **visualize production data** without running the backend locally:

**Edit `.env` file:**

```bash
# Point to production API (already accessible via HTTPS)
API_BASE_URL=https://api.gatewayz.ai

# Use production backend for Prometheus scraping (no FASTAPI_TARGET needed)
# The prom.yml already has production targets configured

# For Redis - comment out local Redis or use production
# REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
# REDIS_PASSWORD=lSQJlAEInskSepAHhZTcI2GrLhtu82CjXEqFk-ErHJk
```

**Then restart:**

```bash
docker compose down
docker compose up -d
```

**Result:** You'll see data from your **production** backend.

---

### Option 2: Run Backend Locally + Monitor It (Full Local Stack)

If you want to run the **entire stack locally** including your FastAPI backend:

#### Step 1: Start Your Backend Locally

```bash
cd ../gatewayz-backend  # Navigate to your backend directory
python -m uvicorn src.main:app --reload --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/metrics
# Should return Prometheus metrics
```

#### Step 2: Update `.env` for Local Backend

```bash
# Point Prometheus to your local backend
# Use host.docker.internal to reach host machine from Docker
FASTAPI_TARGET=host.docker.internal:8000

# Point API proxy to local backend
API_BASE_URL=http://host.docker.internal:8000

# Use local Redis (or comment out to skip Redis monitoring)
# Option A: Run local Redis
# docker run -d -p 6379:6379 redis:latest
# REDIS_ADDR=host.docker.internal:6379
# REDIS_PASSWORD=

# Option B: Skip Redis monitoring (comment out)
# REDIS_ADDR=
# REDIS_PASSWORD=
```

#### Step 3: Restart Monitoring Stack

```bash
docker compose down
docker compose up -d
```

#### Step 4: Verify Prometheus is Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | python3 -m json.tool

# Should see "health": "up" for gatewayz_production
```

---

## 🔍 Current Issues in Your `.env`

### Issue 1: FASTAPI_TARGET is Literal String

**Your `.env` has:**
```bash
FASTAPI_TARGET=host.docker.internal:8000
```

But `prometheus/prom.yml` uses `FASTAPI_TARGET` as a literal string, not an environment variable!

**Check `prom.yml` line 36:**
```yaml
- targets: ['FASTAPI_TARGET']  # ❌ This is a string, not a variable!
```

**The Fix:**

The `prom.yml` needs to be templated to replace `FASTAPI_TARGET` with the actual value. However, Prometheus doesn't support environment variable substitution in the config file directly.

**Solution:** Use `envsubst` or update the Dockerfile to replace the placeholder.

Let me create a fixed Prometheus configuration:

---

## 🛠️ Permanent Fix: Update Prometheus Configuration

### Option A: Use Environment Variable Substitution (Recommended)

**Update `prometheus/Dockerfile`:**

```dockerfile
FROM prom/prometheus:latest

# Install envsubst for environment variable substitution
USER root
RUN apk add --no-cache gettext

# Copy config files
COPY prom.yml /etc/prometheus/prometheus.yml.template
COPY alert.rules.yml /etc/prometheus/alert.rules.yml
COPY alertmanager.yml /etc/prometheus/alertmanager.yml

# Create entrypoint script to substitute env vars
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'envsubst < /etc/prometheus/prometheus.yml.template > /etc/prometheus/prometheus.yml' >> /entrypoint.sh && \
    echo 'exec /bin/prometheus "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

USER nobody

ENTRYPOINT ["/entrypoint.sh"]
CMD ["--config.file=/etc/prometheus/prometheus.yml", \
     "--storage.tsdb.path=/prometheus", \
     "--web.console.libraries=/usr/share/prometheus/console_libraries", \
     "--web.console.templates=/usr/share/prometheus/consoles", \
     "--storage.tsdb.retention.time=15d", \
     "--web.enable-lifecycle"]
```

**Update `prometheus/prom.yml` line 36:**

```yaml
  # Production GatewayZ Backend API
  - job_name: 'gatewayz_production'
    scheme: http
    metrics_path: '/metrics'
    static_configs:
      - targets: ['${FASTAPI_TARGET}']  # Use ${FASTAPI_TARGET} for substitution
    scrape_interval: 15s
    scrape_timeout: 10s
    bearer_token_file: '/etc/prometheus/secrets/production_bearer_token'
    metric_relabel_configs:
      - source_labels: []
        target_label: env
        replacement: production
```

**Do the same for line 93** (gatewayz_data_metrics_production).

---

### Option B: Simpler - Just Use Production URL Directly (Quick Fix)

**Edit `prometheus/prom.yml` lines 36 and 93:**

**Change:**
```yaml
- targets: ['FASTAPI_TARGET']
```

**To:**
```yaml
- targets: ['api.gatewayz.ai']  # Production
# OR for local: ['host.docker.internal:8000']
```

Then rebuild:
```bash
docker compose down
docker compose build prometheus
docker compose up -d
```

---

## 📊 What Should Work After Fix

### 1. Backend Services Dashboard
- **Redis metrics:** ✅ If redis-exporter connects to Redis
- **API metrics:** ✅ If Prometheus scrapes `/metrics` endpoint

### 2. Four Golden Signals Dashboard
- **CPU/Memory/Redis:** ✅ From node_exporter and redis_exporter
- **Latency/Traffic/Errors:** ✅ From FastAPI metrics

### 3. Gateway Dashboard
- **Provider data:** ✅ From JSON API proxy → backend API

### 4. Prometheus Dashboard
- **Raw metrics:** ✅ All Prometheus scraped metrics

### 5. Loki Dashboard
- **Logs:** ⚠️ Only if backend sends logs to Loki at `http://loki:3100/loki/api/v1/push`

### 6. Tempo Dashboard
- **Traces:** ⚠️ Only if backend sends OTLP traces to `http://tempo:4318/v1/traces`

---

## 🚀 Recommended: Quickest Way to See Data

**For immediate results, do this:**

1. **Point to production API** (no local backend needed):

```bash
# Edit .env
API_BASE_URL=https://api.gatewayz.ai
```

2. **Fix Prometheus config** to use production directly:

```bash
# Edit prometheus/prom.yml line 36
- targets: ['api.gatewayz.ai']
```

3. **Rebuild and restart:**

```bash
docker compose down
docker compose build prometheus
docker compose up -d
```

4. **Wait 30 seconds** for Prometheus to scrape

5. **Check Grafana:** `http://localhost:3000`
   - Login: `admin` / `yourpassword123`
   - Navigate to any dashboard
   - Should see production data!

---

## 🔍 Debugging Commands

### Check if services are healthy:
```bash
docker compose ps
```

### Check Prometheus targets:
```bash
curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

### Check if Prometheus has any metrics:
```bash
curl 'http://localhost:9090/api/v1/query?query=up'
```

### Check Grafana datasource health:
```bash
# Open Grafana: http://localhost:3000
# Go to: Configuration → Data Sources
# Click "Test" on each datasource
```

### Check if backend is accessible from Docker:
```bash
docker compose exec prometheus wget -O- http://host.docker.internal:8000/metrics
```

### Check Redis exporter:
```bash
curl http://localhost:9121/metrics
```

---

## ✅ Expected Behavior After Fix

1. **Prometheus Dashboard:**
   - Shows request rate, error rate, latency metrics
   - Data from production API

2. **Backend Services Dashboard:**
   - Redis metrics (if Redis accessible)
   - API performance metrics

3. **Four Golden Signals:**
   - CPU, Memory, Redis gauges showing percentages
   - Latency, Traffic, Error trends

4. **Gateway Dashboard:**
   - Provider health, latency, cost data
   - From JSON API proxy

---

## 🆘 Still No Data?

If after the fixes you still see "No Data":

1. **Check if backend exposes Prometheus metrics:**
   ```bash
   curl https://api.gatewayz.ai/metrics
   # Should return prometheus format metrics
   ```

2. **Check if backend requires authentication:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.gatewayz.ai/metrics
   ```

3. **Check Prometheus logs:**
   ```bash
   docker compose logs prometheus
   ```

4. **Check if Mimir is receiving data:**
   ```bash
   curl http://localhost:9009/prometheus/api/v1/query?query=up
   ```

---

## 📝 Summary

**The "No Data" issue is because:**

1. Prometheus config has literal string `FASTAPI_TARGET` instead of actual URL
2. Redis is pointing to Railway internal network
3. Bearer tokens may not be configured correctly

**Quick Fix:**
- Change `FASTAPI_TARGET` in `prom.yml` to `api.gatewayz.ai`
- Rebuild Prometheus
- Restart stack

**You should see production data within 30 seconds!**
