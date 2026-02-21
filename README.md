# GatewayZ Observability Stack

**Production-ready observability platform for GatewayZ AI Backend** - Centralized metrics, logs, traces, and visualization with horizontal scaling via Grafana Mimir.

[![Railway Deploy](https://railway.app/button.svg)](https://railway.app)

---

## 🚀 Quick Start

### Production Access
- **Grafana Dashboard:** [https://logs.gatewayz.ai](https://logs.gatewayz.ai)

### Local Development (Docker Compose)

```bash
# 1. Clone and navigate to the stack
git clone <repo-url>
cd railway-grafana-stack

# 2. Configure backend metrics scraping (REQUIRED for data to show)
export FASTAPI_TARGET="host.docker.internal:8000"  # If backend runs on host
# OR
export FASTAPI_TARGET="gatewayz-backend:8000"       # If backend is in Docker network

# 3. Start all services
docker compose up --build

# 4. Access services
open http://localhost:3000  # Grafana (admin/yourpassword123)
open http://localhost:9090  # Prometheus
open http://localhost:9009  # Mimir
```

**📖 Documentation:**
- **[Complete Documentation Index](docs/docs-index.md)** - Start here for all guides and references
- Quick Links:
  - **[Cheatsheet](docs/cheatsheet.md)** - Common commands and queries
  - **[Troubleshooting](docs/troubleshooting/REMOTE_WRITE_DEBUG.md)** - Fix common issues
  - **[Architecture](docs/architecture/MIMIR.md)** - System design and components

---

## 📊 Architecture Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GatewayZ Backend API                                 │
│                      (FastAPI: api.gatewayz.ai)                             │
└───────────┬─────────────────────┬─────────────────────┬─────────────────────┘
            │                     │                     │
      Metrics (Pull)        Logs (Push)           Traces (Push)
        /metrics           :3100/loki/push         :4317 (gRPC)
                                                   :4318 (HTTP)
            │                     │                     │
            ▼                     ▼                     ▼
    ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
    │  Prometheus   │     │     Loki      │     │    Tempo      │
    │    :9090      │     │    :3100      │     │    :3200      │
    │               │     │               │     │               │
    │ Scrapes every │     │  Log Storage  │     │ Trace Storage │
    │   15-30s      │     │  30d Retain   │     │  48h Retain   │
    └───────┬───────┘     └───────────────┘     └───────┬───────┘
            │                     │                     │
            │ remote_write        │ (no connection)     │ metrics_generator
            │ /api/v1/push        │                     │ remote_write
            ▼                     │                     ▼
    ┌───────────────┐             │             ┌───────────────┐
    │               │◄────────────┘             │               │
    │     Mimir     │         (Loki stores      │     Mimir     │
    │    :9009      │          LOGS, not        │  (span metrics│
    │               │          metrics - this   │   from traces)│
    │  Long-term    │          is BY DESIGN)    │               │
    │  30d Retain   │                           │               │
    └───────┬───────┘                           └───────┬───────┘
            │                                           │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                          ┌───────────────┐
                          │    Grafana    │
                          │     :3000     │
                          │               │
                          │ Queries each  │
                          │ source for    │
                          │ its data type │
                          └───────────────┘
                                  │
                    ┌─────────────┼─────────────┐─────────────┐
                    ▼             ▼             ▼             ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
              │Prometheus│ │  Mimir   │ │   Loki   │ │  Tempo   │
              │(metrics) │ │(metrics) │ │  (logs)  │ │ (traces) │
              │short-term│ │long-term │ │          │ │          │
              └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Important: Data Type Separation

| Component | Stores | Writes To | Notes |
|-----------|--------|-----------|-------|
| **Prometheus** | Metrics (time-series) | **Mimir** via remote_write | Short-term storage, scrapes every 15-30s |
| **Mimir** | Metrics (time-series) | Local filesystem | Long-term storage, 30-day retention |
| **Loki** | Logs (text lines) | Local filesystem | **Does NOT write to Mimir** - logs ≠ metrics |
| **Tempo** | Traces (spans) | Local filesystem + **Mimir** (span metrics only) | Traces stored locally, derived metrics to Mimir |

> **Why Loki doesn't write to Mimir:** Loki stores **log lines** (text data), while Mimir stores **metrics** (numeric time-series). These are fundamentally different data types. Grafana queries Loki directly for logs.

### Key Components

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Grafana 11.5.2** | 3000 | Visualization & dashboards | ✅ 5 dashboard folders |
| **Prometheus 3.2.1** | 9090 | Metrics collection + alerting | ✅ 6 scrape jobs |
| **Mimir 2.11.0** | 9009, 9095 | Long-term metrics storage | ✅ 30-day retention |
| **Loki 3.4** | 3100 | Log aggregation | ✅ 30-day retention |
| **Tempo** | 3200, 4317, 4318 | Distributed tracing | ✅ OTLP endpoints |
| **Redis Exporter** | 9121 | Redis metrics | ✅ Integrated |

---

## 🎯 Dashboard Folders

All dashboards use **real API endpoints** with live data from Prometheus/Mimir - no mock data.

| Folder | Purpose | Key Metrics | Status |
|--------|---------|-------------|--------|
| **Four Golden Signals** | SRE observability hub | Latency P50/P95/P99, Traffic RPS, Error rate, Saturation, Service Graph | ✅ Ready |
| **Model Performance** | AI model metrics | Request rates, latency, token usage, error rates | ✅ Ready |
| **Loki** | Log aggregation | Log search, streaming, volume by level/service | ✅ Ready |
| **Prometheus** | Short-term metrics | Scrape targets, query stats, self-monitoring | ✅ Ready |
| **Tempo** | Distributed tracing | Service graph, span metrics, trace search | ✅ Ready |
| **Mimir** | Long-term metrics | Historical queries, retention stats | ✅ Ready |

### Dashboard Features

#### Model Performance
- **AI Provider Metrics**: Request rates by provider/model
- **Latency Analysis**: P50/P95/P99 percentiles
- **Token Usage**: Input/output token tracking
- **Error Rates**: By provider, model, and error type

#### Loki Logs Dashboard
- **Pure log data** from Loki datasource
- **Log Search**: Real-time filtering and search
- **Log Volume**: Count by level, service, severity

#### 3. Tempo (Tracing)
- **Pure trace data** from Tempo datasource
- **Service Graph**: Distributed tracing visualization
- **Span Metrics**: Request duration, error rates by service

#### Mimir Long-term Storage
- **Historical Queries**: 30-day retention for trend analysis
- **Consistent Results**: No data loss on Prometheus restarts

---

## ⚙️ Configuration

### Prometheus Scrape Jobs

**File:** `prometheus/prometheus.yml`

| Job Name | Target | Interval | Purpose |
|----------|--------|----------|---------|
| `prometheus` | localhost:9090 | 15s | Self-monitoring |
| `gatewayz_production` | `${FASTAPI_TARGET}` | 15s | **Production API metrics** |
| `redis_exporter` | redis-exporter:9121 | 30s | Redis metrics |
| `gatewayz_data_metrics_production` | `${FASTAPI_TARGET}` | 30s | Provider health, circuit breakers |
| `mimir` | mimir:9009 | 30s | Mimir self-monitoring |

#### ⚠️ **IMPORTANT: `FASTAPI_TARGET` Configuration**

The `${FASTAPI_TARGET}` placeholder **MUST be set** for local development:

```bash
# For backend on host machine (most common)
export FASTAPI_TARGET="host.docker.internal:8000"

# For backend in same Docker network
export FASTAPI_TARGET="gatewayz-backend:8000"

# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets
```

**Without this variable, the Backend Services dashboard will show no API data.**

### Grafana Datasources

**Directory:** `grafana/datasources/datasources.yml`

| Datasource | UID | Type | URL | Purpose |
|------------|-----|------|-----|---------|
| **Prometheus** | `grafana_prometheus` | prometheus | `${PROMETHEUS_INTERNAL_URL}` | Short-term metrics |
| **Mimir** | `grafana_mimir` | prometheus | `${MIMIR_INTERNAL_URL}/prometheus` | Long-term metrics |
| **Loki** | `grafana_loki` | loki | `${LOKI_URL}` | Logs |
| **Tempo** | `grafana_tempo` | tempo | `${TEMPO_INTERNAL_URL}` | Traces |

### Data Retention

| Service | Retention | Compaction | Notes |
|---------|-----------|------------|-------|
| **Prometheus** | 15 days | N/A | Short-term, remote writes to Mimir |
| **Mimir** | 30 days | Every 2h | Horizontal scaling, HA-ready |
| **Loki** | 30 days | Every 10m | TSDB index, filesystem storage |
| **Tempo** | 7 days | 5m blocks | Local filesystem |

---

## 🔌 Backend Integration

### 1. Expose Metrics Endpoint

**Python (FastAPI):**
```python
from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define custom metrics
request_counter = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'env']
)

latency_histogram = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'env']
)

# Use in your routes
@app.get("/v1/models")
async def list_models():
    request_counter.labels(
        method="GET",
        endpoint="/v1/models",
        status_code="200",
        env="production"
    ).inc()
    return {"models": [...]}
```

### 2. Send Logs to Loki

**Python with python-logging-loki:**
```python
import logging
from logging_loki import LokiHandler

loki_handler = LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"app": "gatewayz", "env": "production"},
    version="1"
)

logger = logging.getLogger("gatewayz")
logger.addHandler(loki_handler)
logger.setLevel(logging.INFO)

# Use structured logging
logger.info("Request processed", extra={
    "user_id": "123",
    "duration_ms": 45,
    "model": "gpt-4"
})
```

### 3. Send Traces to Tempo

**Python with OpenTelemetry:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Tempo exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo:4318/v1/traces"
)

# Setup tracing
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Instrument your code
with tracer.start_as_current_span("model_inference") as span:
    span.set_attribute("model", "gpt-4")
    span.set_attribute("provider", "openai")
    result = await call_model_api()
```

**📖 Complete Integration Guide:** [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)

---

## 🔧 Troubleshooting

### Issue: Backend Services Dashboard Shows "No Data"

**Symptom:** All Redis and API panels show "No data"

**Root Cause:** `FASTAPI_TARGET` environment variable not set for local builds

**Solution:**
```bash
# Set the environment variable
export FASTAPI_TARGET="host.docker.internal:8000"

# Restart Prometheus
docker compose restart prometheus

# Verify targets are UP
open http://localhost:9090/targets
```

### Issue: Loki Dashboard Shows "Bad Request"

**Cause:** Query syntax issues or no logs ingested

**Fix:**
1. Verify Loki is receiving logs:
   ```bash
   curl http://localhost:3100/metrics | grep loki_distributor_lines_received_total
   ```
2. Test log ingestion:
   ```bash
   curl -X POST http://localhost:3100/loki/api/v1/push \
     -H "Content-Type: application/json" \
     -d '{"streams":[{"stream":{"app":"test"},"values":[["'$(date +%s%N)'","test message"]]}]}'
   ```
3. Check query syntax in dashboard (LogQL, not PromQL)

**📖 More Solutions:** [docs/troubleshooting/](docs/troubleshooting/)

### Issue: Grafana Datasource Connection Failed

**Cause:** Datasource UID mismatch or incorrect URLs

**Fix:**
1. Check datasource health:
   ```bash
   # Prometheus
   curl http://localhost:9090/-/healthy
   
   # Mimir
   curl http://localhost:9009/ready
   
   # Loki
   curl http://localhost:3100/ready
   
   # Tempo
   curl http://localhost:3200/ready
   ```

2. Verify datasource UIDs in Grafana:
   - Prometheus: `grafana_prometheus`
   - Mimir: `grafana_mimir`
   - Loki: `grafana_loki`
   - Tempo: `grafana_tempo`

3. Check environment variables in `docker-compose.yml`

### Issue: Mimir Not Receiving Data from Prometheus

**Symptom:** Prometheus is scraping metrics but Mimir shows no data, or Grafana's Mimir datasource returns empty results.

**Root Cause:** Missing `X-Scope-OrgID` header in Prometheus remote_write or Grafana datasource configuration.

**Why This Happens:** Even with `multitenancy_enabled: false` in Mimir, both writes (from Prometheus) and reads (from Grafana) require the `X-Scope-OrgID` header. When multi-tenancy is disabled, Mimir uses `anonymous` as the default tenant.

**Solution:**

1. **Verify Prometheus remote_write has the header** (`prometheus/prometheus.yml`):
   ```yaml
   remote_write:
     - url: http://mimir:9009/api/v1/push
       headers:
         X-Scope-OrgID: anonymous
   ```

2. **Verify Grafana Mimir datasource has the header** (`grafana/datasources/datasources.yml`):
   ```yaml
   - name: Mimir
     type: prometheus
     url: ${MIMIR_INTERNAL_URL}/prometheus
     jsonData:
       httpHeaderName1: X-Scope-OrgID
     secureJsonData:
       httpHeaderValue1: anonymous
   ```

3. **Restart services after configuration changes:**
   ```bash
   docker compose restart prometheus grafana
   ```

4. **Verify Mimir is receiving data:**
   ```bash
   # Check Mimir ingester status
   curl http://localhost:9009/ingester/ring

   # Check remote write metrics in Prometheus
   curl http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_total

   # Test Mimir query directly
   curl -H "X-Scope-OrgID: anonymous" "http://localhost:9009/prometheus/api/v1/query?query=up"
   ```

**📖 More Solutions:** [docs/troubleshooting/REMOTE_WRITE_DEBUG.md](docs/troubleshooting/REMOTE_WRITE_DEBUG.md)

---

## ✨ Key Features

### 🚀 Horizontal Scaling with Mimir
- Long-term metrics storage with 30-day retention.
- Horizontally scalable architecture.
- Remote write from Prometheus.

### 📊 Golden Signals Monitoring
- **Latency**: P50/P95/P99 percentiles + trends.
- **Traffic**: Request volume and rates.
- **Errors**: Error rate gauge + trends.
- **Saturation**: CPU/Memory/Redis utilization.

### 🔍 Specialized Dashboards
- **Executive Overview**: High-level KPIs and alerts.
- **Backend Services**: Redis cache hit rates, API performance.
- **Loki Logs**: Deep log search without metrics noise.
- **Tempo Traces**: Distributed tracing and service graphs.

### 🛡️ Production Grade
- **Alerting**: Email notifications for health scores and SLO breaches.
- **Testing**: Comprehensive integration test suite (90+ tests).
- **Security**: No hardcoded credentials; fully environment-variable driven.

---

## 📊 Mimir Long-term Storage Setup

Mimir provides **30-day metric retention** with horizontal scaling. This is critical for:
- Historical trend analysis
- Consistent query results across page refreshes
- No data loss on Prometheus restarts

### How Prometheus → Mimir Works

```
┌────────────┐    remote_write     ┌─────────────┐
│ Prometheus │ ────────────────────▶│    Mimir    │
│   :9090    │   /api/v1/push      │   :9009     │
│            │   X-Scope-OrgID:    │             │
│  (15d)     │   anonymous         │  (30d)      │
└────────────┘                     └─────────────┘
      │                                   │
      │ scrapes                           │ stores
      ▼                                   ▼
 ┌──────────┐                     ┌──────────────┐
 │ Backend  │                     │ /data/mimir/ │
 │ /metrics │                     │   blocks/    │
 └──────────┘                     │   tsdb/      │
                                  └──────────────┘
```

### Verifying Mimir is Working

```bash
# 1. Check Mimir is ready
curl http://localhost:9009/ready
# Expected: "ready"

# 2. Check Mimir ingester ring (must show ACTIVE)
curl http://localhost:9009/ingester/ring | jq '.shards[].state'
# Expected: "ACTIVE"

# 3. Check Prometheus remote_write metrics
curl -s http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_total | jq '.data.result[].value[1]'
# Expected: increasing number (samples sent)

# 4. Check for remote_write failures
curl -s http://localhost:9090/api/v1/query?query=prometheus_remote_storage_samples_failed_total | jq '.data.result[].value[1]'
# Expected: 0 or very low

# 5. Query Mimir directly
curl -H "X-Scope-OrgID: anonymous" \
  "http://localhost:9009/prometheus/api/v1/query?query=up"
# Expected: JSON with metric data

# 6. Check Mimir logs for write activity
docker compose logs mimir 2>&1 | grep -i "push" | tail -5
```

### Key Configuration Files

| File | Purpose |
|------|---------|
| `prometheus/prometheus.yml` | `remote_write` config with `X-Scope-OrgID: anonymous` header |
| `mimir/mimir.yml` | Local development config (30d retention) |
| `mimir/mimir-railway.yml` | Railway production config |
| `grafana/datasources/datasources.yml` | Mimir datasource with `X-Scope-OrgID` header |

### Mimir Configuration (mimir.yml)

```yaml
# Key settings for 30-day retention
multitenancy_enabled: false  # Uses "anonymous" tenant
limits:
  compactor_blocks_retention_period: 720h  # 30 days
  max_query_lookback: 720h                 # 30 days
  ingestion_rate: 50000                    # samples/sec
  max_global_series_per_user: 500000       # total series
```

---

## 🔔 Alerting Setup

GatewayZ uses **Prometheus Alert Rules** with Grafana for visualization. Alerts are defined in `prometheus/alert.rules.yml` with a focus on actionability and reducing alert fatigue.

### Alert Philosophy

1. **Every alert MUST be actionable** - if you can't fix it, don't alert on it
2. **Fewer high-quality alerts** - 14 essential alerts instead of 25+ noisy ones
3. **Warning vs Critical** - warning = investigate soon, critical = wake someone up
4. **No duplicates** - consolidated overlapping alerts into single actionable items

### Alert Groups (14 Total)

| Group | Alerts | Purpose |
|-------|--------|---------|
| **service_health** | 3 | Is the service up and responding? |
| **api_performance** | 3 | Are API responses healthy? |
| **provider_health** | 3 | Are upstream AI providers working? |
| **infrastructure** | 5 | Is the monitoring stack itself healthy? |

### Current Alerts

#### Service Health (Critical)
| Alert | Trigger | Action |
|-------|---------|--------|
| `GatewayZAPIDown` | Prometheus can't scrape API for 2m | Check Railway deployment |
| `HighErrorRate` | >10% error rate for 5m | Check Loki logs, recent deployments |
| `AvailabilitySLOBreach` | <99.5% success rate over 1h | Initiate incident response |

#### API Performance (Warning)
| Alert | Trigger | Action |
|-------|---------|--------|
| `HighAPILatency` | P95 > 3s for 5m | Check slow endpoints, providers |
| `LatencyDegradation` | 50% latency increase vs 1h ago | Check recent changes, resources |
| `TrafficSpike` | 3x traffic increase for 10m | Analyze traffic, check for abuse |

#### Provider Health (Critical/Warning)
| Alert | Trigger | Action |
|-------|---------|--------|
| `ProviderHighErrorRate` | >20% errors per provider for 5m | Check provider status, failover |
| `SlowProviderResponse` | P95 > 5s per provider for 10m | Monitor provider, adjust timeouts |
| `LowModelHealthScore` | <80% success rate for 5m | Review errors across providers |

#### Infrastructure (Critical/Warning)
| Alert | Trigger | Action |
|-------|---------|--------|
| `ScrapeTargetDown` | Any scrape target down for 5m | Check target health, network |
| `MimirRemoteWriteFailures` | Failed samples to Mimir | Check Mimir health, storage |
| `MimirDown` | Mimir unreachable for 2m | Check container, storage volume |
| `TempoNoTraces` | No traces for 15m | Check OTLP endpoint, backend config |
| `LokiNoLogs` | No logs for 15m | Check Loki health, log shipping |

### Removed Alerts (Noise Reduction)

The following alerts were removed to reduce alert fatigue:

| Removed Alert | Reason |
|---------------|--------|
| `LowAPIRequestRate` | Fires during off-hours/weekends, not actionable |
| `CriticalAPILatency` | Duplicate of HighAPILatency (consolidated) |
| `APIErrorRateIncreasing` | Trend detection causes fatigue with absolute threshold |
| Redis alerts (6) | redis_exporter not reliably scraped; re-add when fixed |
| `HighModelInferenceLatency` | Per-model alerting too noisy for 100+ models |
| `SLOLatencyBreach` (500ms) | Too aggressive for AI inference (2-5s typical) |

### Contact Points Configuration

**File:** `grafana/provisioning/alerting/contact_points.yml`

```yaml
contactPoints:
  - name: ops-email
    receivers:
      - type: email
        settings:
          addresses: your-team@company.com
          singleEmail: false

  - name: critical-email
    receivers:
      - type: email
        settings:
          addresses: oncall@company.com
          singleEmail: false

  - name: observatory-pool-critical
    receivers:
      - type: email
        settings:
          addresses: alerts@company.com
```

### Notification Policies

**File:** `grafana/provisioning/alerting/notification_policies.yml`

Routes alerts to appropriate contact points based on labels:

| Matcher | Contact Point | Group Interval |
|---------|---------------|----------------|
| `severity=critical` | critical-email | 5m |
| `category=traffic_spike, severity=critical` | observatory-pool-critical | 5m |
| `category=error_rate_spike` | observatory-pool-critical/warning | 3-5m |
| `component=redis, severity=critical` | critical-email | 2m |
| `component=slo` | critical-email | 5m |

### Alert Rules

**Directory:** `grafana/provisioning/alerting/rules/`

| File | Alerts |
|------|--------|
| `traffic_anomalies.yml` | Traffic spikes, drops |
| `error_rate_anomalies.yml` | Error rate spikes by provider |
| `latency_anomalies.yml` | P99 latency spikes |
| `availability_anomalies.yml` | Provider availability drops |
| `redis_alerts.yml` | Redis cache issues |
| `slo_burn_rate_alerts.yml` | SLO violation alerts |
| `backend_alerts.yml` | Backend service health |
| `model_alerts.yml` | Model-specific issues |

### Setting Up Email Alerts

1. **Configure SMTP in docker-compose.yml:**
   ```yaml
   grafana:
     environment:
       - GF_SMTP_ENABLED=true
       - GF_SMTP_HOST=smtp.gmail.com:587
       - GF_SMTP_USER=your-email@gmail.com
       - GF_SMTP_PASSWORD=your-app-password
       - GF_SMTP_FROM_ADDRESS=grafana@gatewayz.ai
   ```

2. **Update contact_points.yml with your email addresses:**
   ```yaml
   contactPoints:
     - name: ops-email
       receivers:
         - type: email
           settings:
             addresses: your-team@company.com
   ```

3. **Test email delivery:**
   - Go to Grafana → Alerting → Contact points
   - Click "Test" on any contact point
   - Verify email is received

### Viewing Alerts

- **Grafana UI:** Alerting → Alert rules
- **Prometheus UI:** http://localhost:9090/alerts
- **API:**
  ```bash
  # List firing alerts
  curl http://localhost:3000/api/alertmanager/grafana/api/v2/alerts \
    -H "Authorization: Bearer $GRAFANA_API_KEY"
  ```

---

## 🧪 Testing & Quality Assurance

### Test Coverage

- **25+ Real API Endpoints** - Integration tests with performance validation
- **7 Production Dashboards** - Schema validation and configuration checks
- **90+ Test Methods** - Comprehensive coverage across all components
- **GitHub Actions Workflows** - Automated validation on every deployment

### Quick Testing Commands

```bash
# Setup (required once)
cp .env.example .env
# Edit .env and add your API keys

# Run all tests
pytest tests/ -v

# Dashboard validation
./scripts/validate_dashboards.sh strict

# Endpoint testing
export API_KEY="your_api_key"
./scripts/test_all_endpoints.sh "$API_KEY" https://api.gatewayz.ai

# Specific test categories
pytest tests/test_dashboards.py -v -m dashboard
pytest tests/test_api_endpoints.py -v -m endpoint
```

---

## 🚀 Deployment

### Railway Deployment

```bash
# 1. Push to Railway
git push railway main

# 2. Or use Railway CLI
railway up

# 3. Configure environment variables in Railway dashboard
FASTAPI_TARGET=api.gatewayz.ai:443
PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
LOKI_URL=http://loki.railway.internal:3100
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
```

### Docker Compose (Local)

```bash
# Start all services
docker compose up --build

# Start specific services
docker compose up grafana prometheus mimir

# View logs
docker compose logs -f grafana

# Stop all services
docker compose down

# Clean volumes (WARNING: deletes all data)
docker compose down -v
```

**📖 Deployment Guide:** [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

---

## 📚 Documentation

### Core Documentation

- **[Documentation Index](docs/docs-index.md)** - Start here for all docs
- **[Backend Integration](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)** - Required metrics and instrumentation
- **[Railway Deployment](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)** - Deploy to Railway
- **[Mimir Integration](MIMIR_INTEGRATION_SUMMARY.md)** - Horizontal scaling guide
- **[Troubleshooting](docs/troubleshooting/)** - Service-specific fix guides



---

## 🛠️ Development

### Project Structure

```
railway-grafana-stack/
├── grafana/
│   ├── Dockerfile
│   ├── dashboards/
│   │   ├── model_performance/  # Model Performance metrics
│   │   ├── loki/               # Loki logs (pure logs)
│   │   ├── prometheus/         # Prometheus metrics
│   │   ├── tempo/              # Tempo traces (pure traces)
│   │   └── mimir/              # Mimir long-term metrics
│   ├── datasources/
│   │   └── datasources.yml     # Prometheus, Mimir, Loki, Tempo
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── alerting/
│           ├── rules/
│           │   └── redis_alerts.yml
│           └── notification_policies.yml
├── prometheus/
│   ├── Dockerfile
│   ├── entrypoint.sh         # Environment-based configuration
│   ├── prometheus.yml        # Scrape jobs + remote_write to Mimir
│   └── alert.rules.yml       # Alert rules
├── mimir/
│   ├── Dockerfile
│   └── mimir.yml             # Mimir configuration (30d retention)
├── loki/
│   ├── Dockerfile
│   └── loki.yml              # Loki configuration
├── tempo/
│   ├── Dockerfile
│   ├── entrypoint.sh         # Environment-based configuration
│   └── tempo.yml             # Tempo configuration
├── scripts/
│   ├── pre-build-cleanup.sh  # Railway pre-deploy cleanup
│   └── ...                   # Other validation scripts
├── tests/                    # Pytest test suite
├── docs/                     # Documentation
├── railway.toml              # Railway deployment configuration
├── docker-compose.yml        # Local development
└── README.md                 # This file
```

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally with `docker compose up`
3. Run tests: `pytest tests/ -v`
4. Create pull request to `main`

---

## 🔗 Cross-Signal Navigation (Breaking Down the Silos)

The biggest mistake in any LGTM observability setup is treating each panel as a silo. The stack is configured for end-to-end click-through navigation so you always move toward the root cause rather than copy-pasting IDs between tabs.

### How the links are wired

| From | To | Mechanism | How to trigger |
|------|-----|-----------|---------------|
| **Metric graph** | **Tempo trace** | Exemplar (blue ◆ dot on latency graphs) | Click the blue dot on any histogram panel |
| **Loki log line** | **Tempo trace** | Derived Field on `trace_id` JSON field | Click **"View Trace"** button next to any log entry |
| **Loki log label** | **Tempo trace** | Derived Field on `trace_id` Loki label | Click **"View Trace"** button in label sidebar |
| **Tempo span** | **Mimir metric** | `tracesToMetrics` → `grafana_mimir` | In Tempo, click a span → "Related metrics" |
| **Tempo span** | **Loki logs** | `tracesToLogs` → `grafana_loki` | In Tempo, click a span → "Related logs" |
| **Tempo service graph** | **Node topology** | `serviceMap` → `grafana_mimir` | Service Graph & Topology section in dashboard |

### Implementation details

**Exemplars (Mimir + Prometheus → Tempo):** Both datasources have `exemplarTraceIdDestinations` set to `trace_id` (underscore, matching the OpenTelemetry field name the backend emits). The field names are now consistent — previously Mimir was using `traceId` (camelCase), which would have silently failed.

**Derived Fields (Loki → Tempo):** Two matchers are configured — one for JSON-structured log lines (`"trace_id": "..."`) and one for Loki labels. Both resolve to the Tempo datasource so the button appears regardless of how the backend emits the ID.

**Service Graph (Tempo → Mimir):** Tempo's `metrics_generator` with the `service-graphs` processor generates `traces_service_graph_*` metrics and remote-writes them **directly to Mimir** — they are never in Prometheus. The `serviceMap` datasource is correctly set to `grafana_mimir`. Similarly, `tracesToMetrics` points to Mimir because span metrics (`traces_spanmetrics_*`) are also Mimir-only.

### Resource attribute consistency requirement

For the `$service` template variable and cross-signal filtering to work reliably, the backend must emit consistent resource attributes across all four signals:

```
service.name  = "gatewayz-backend"   # must match in spans, logs, and metrics
instance.id   = "<pod-or-host-id>"   # must match for per-instance filtering
```

Configure this once in the OpenTelemetry SDK resource at process startup — it propagates to Tempo (spans), Loki (log labels via the OTEL log handler), and Prometheus (target labels via relabeling).

---

## 🔬 Continuous Profiling (Pyroscope — self-hosted on Railway)

The stack is **LGTMP**: Loki · Grafana · Tempo · Mimir · **Pyroscope**. Pyroscope runs as a service inside the Railway project — no external accounts, no public ports, everything stays internal.

### Why profiling matters for GatewayZ

The Four Golden Signals tell you **what** is wrong. Profiling tells you **which line of code** is causing it.

| Four Golden Signals say | Profiling adds |
|-------------------------|---------------|
| CPU saturation at 90% | Which function is burning the cycles? Token counter? JSON streaming serializer? |
| Memory growing 50 MB/hour | Which object accumulates? A model-catalog cache entry with no TTL? An open SSE connection? |
| P99 latency spiked to 8 s | What was the thread doing during those 8 seconds? Waiting on a Redis lock? A slow provider response? |

### Architecture

```
gatewayz-backend (Railway service)
  └─ pyroscope-io SDK (in-process, 100 Hz sampler)
       └─ HTTP push every 15 s ──→ pyroscope.railway.internal:4040
                                          │
                              Pyroscope (Railway service)
                              /data/pyroscope volume
                                          │
                              Grafana datasource reads ←──────────
                              (grafana_pyroscope → internal:4040)
```

### How to activate

**1. Set one env var on the Railway backend service:**
```
PYROSCOPE_ENABLED=true
PYROSCOPE_SERVER_ADDRESS=http://pyroscope.railway.internal:4040
```
No auth credentials needed — the endpoint is internal only.

**2. Set one env var on the Railway Grafana service:**
```
PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040
```

**3. Deploy the Pyroscope Railway service** from the `pyroscope/` directory in this repo (uses `pyroscope/Dockerfile`). Railway will assign it the internal DNS name `pyroscope.railway.internal`.

That's it. Profiles appear in Grafana within ~30 seconds of the first request hitting the backend.

### What you get

- **CPU flamegraphs** per endpoint — see if `/v1/chat/completions` burns cycles in the token estimator, the SSE chunker, or the routing logic
- **Memory flamegraphs** — find objects that survive GC; useful for diagnosing slow memory growth visible in the Saturation pillar
- **Trace → Profile drill-down** — click any slow span in Tempo → **"View Profile"** button opens the flamegraph recorded at that exact time window for that request

---

## 📞 Support & Resources

### External Documentation

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Railway Documentation](https://docs.railway.app/)

### Getting Help

- **Documentation Issues:** Check [docs/troubleshooting/](docs/troubleshooting/)
- **Backend Integration:** See [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)
- **Deployment Help:** Review [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

---

## 📄 License

Proprietary - GatewayZ Network

---

**GatewayZ Observability Stack** · Enterprise-grade monitoring for AI infrastructure · Powered by Prometheus, Mimir, Loki, Tempo, and Grafana
