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
open http://localhost:9093  # Alertmanager (alert routing UI)
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
            │                     │                     │
            │  firing alerts      │                     │
            ├────────────────►────┤                     │
            │          ┌──────────┴──────┐              │
            │          │  Alertmanager   │              │
            │          │    :9093        │              │
            │          │                 │              │
            │          │ Routes alerts → │              │
            │          │ Email (SMTP)    │              │
            │          └─────────────────┘              │
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
| **Grafana 11.5.2** | 3000 | Visualization & dashboards | ✅ 6 dashboard folders |
| **Prometheus 3.2.1** | 9090 | Metrics collection + alerting rules | ✅ 6 scrape jobs |
| **Alertmanager v0.27.0** | 9093 | Alert routing → email (ops + critical) | ✅ Mirrors Grafana notification policies |
| **Mimir 2.11.0** | 9009, 9095 | Long-term metrics storage | ✅ 30-day retention |
| **Loki 3.4** | 3100 | Log aggregation | ✅ 30-day retention |
| **Tempo** | 3200, 4317, 4318 | Distributed tracing | ✅ OTLP endpoints |
| **Pyroscope 1.7.1** | 4040 | Continuous CPU profiling | ✅ Provider/model/cache tagged flamegraphs |
| **Redis Exporter** | 9121 | Redis metrics | ✅ Integrated |

---

## 🔭 Backend Telemetry Pipeline

The `gatewayz-backend` (FastAPI) emits telemetry on **three channels** that feed this stack:

| Channel | Protocol | Destination | Grafana Datasource |
|---------|----------|-------------|-------------------|
| **Metrics** | Prometheus scrape (`/metrics`) | Prometheus → Mimir | `grafana_prometheus` / `grafana_mimir` |
| **Logs** | Async Loki push (JSON) | Loki | `grafana_loki` |
| **Traces** | OTLP HTTP (`/v1/traces`) | Tempo | `grafana_tempo` |
| **Provider health** | HTTP scrape (`/prometheus/data/metrics`) | JSON-API-Proxy | `grafana_json_api` |

### How Metrics Get to Grafana

```
gatewayz-backend /metrics
        │
        └─► Prometheus scrapes every 15s
                  │
                  ├─► Stored locally (short-term, 15d)
                  └─► Remote write → Mimir (long-term, 30d)
                                         │
                                         └─► Grafana queries Mimir for all panels
```

### How Traces Get to Grafana

```
gatewayz-backend
  ├── FastAPI / HTTPX / Redis auto-instrumented by OpenTelemetry
  ├── LLM calls traced via OpenLLMetry (gen_ai.* semantic conventions)
  └── ResilientSpanProcessor (circuit breaker) → OTLP HTTP → Tempo :4318
                                                                    │
                                                             Grafana queries Tempo
                                                             (+ Pyroscope flamegraphs
                                                              linked via service.name)
```

### How Logs Get to Grafana

```
gatewayz-backend structlog (JSON format)
  └── Async queue → Loki push :3100
        Labels: app="gatewayz", level, service
        Fields: trace_id, span_id, endpoint, model, provider, user_id
                    │
            Grafana queries Loki
            Log→Trace correlation via trace_id field → Tempo
```

### Key Backend Identifiers

| Identifier | Value | Used In |
|-----------|-------|---------|
| OTEL service name | `gatewayz-api` | Tempo trace search, Pyroscope linking |
| Loki app label | `app="gatewayz"` | All Loki dashboard queries |
| Prometheus job | `gatewayz_production` | Prometheus target filter |
| Scrape target | `$FASTAPI_TARGET` | Must be set in Railway env vars |

> **Full backend telemetry reference:** See [MASTER.md — Section 16](MASTER.md) for all metrics, OTEL config, Loki log format, health monitoring tiers, and dashboard-to-metric mapping.

---

## 🎯 Dashboard Folders

All dashboards use **real API endpoints** with live data from Prometheus/Mimir - no mock data.

| Folder | Dashboard(s) | Purpose | Status |
|--------|-------------|---------|--------|
| **Four Golden Signals** | Four-Golden-Signals | Latency · Traffic · Errors · Pyroscope Profiling (Pillar IV) | ✅ Ready |
| **Model Performance** | Inference-Call-Profile, Model-Usage, Cache-Layer-Profile, Inference-Profiling, Provider-Directory | AI inference anatomy, token usage, Redis cache CPU, provider metrics | ✅ Ready |
| **Loki** | Loki dashboards | Log search, streaming, volume by level/service | ✅ Ready |
| **Prometheus** | Prometheus self-monitoring | Scrape targets, query stats, remote_write health | ✅ Ready |
| **Tempo** | Tempo dashboards | Service graph, span metrics, trace search | ✅ Ready |
| **Mimir** | Mimir dashboards | Historical queries, retention stats | ✅ Ready |

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
| **Prometheus** | `grafana_prometheus` | prometheus | `${PROMETHEUS_INTERNAL_URL}` | Short-term app metrics |
| **Mimir** | `grafana_mimir` | prometheus | `${MIMIR_INTERNAL_URL}/prometheus` | Long-term metrics + span metrics from Tempo |
| **Loki** | `grafana_loki` | loki | `${LOKI_INTERNAL_URL}` | Logs |
| **Tempo** | `grafana_tempo` | tempo | `${TEMPO_INTERNAL_URL}` | Traces |
| **Pyroscope** | `grafana_pyroscope` | grafana-pyroscope-datasource | `${PYROSCOPE_INTERNAL_URL}` | Continuous profiling / flamegraphs |

> **Datasource rule:** `grafana_prometheus` = standard app metrics. `grafana_mimir` = ONLY Tempo-generated `traces_spanmetrics_*` / `traces_service_graph_*` metrics. Never mix them in dashboards.

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
- **Traffic**: Request volume and rates by provider and model.
- **Errors**: Error rate gauge + trends per provider.
- **Profiling (Pillar IV)**: Continuous Pyroscope flamegraphs replace traditional saturation metrics — tells you *which line of code* is the bottleneck.

### 🔍 Specialized Dashboards
- **Inference Call Profile**: Per-request CPU anatomy by provider/model.
- **Cache Layer Profile**: Redis CPU cost by cache layer (`auth`, `rate_limit`, `model_catalog`, `response_cache`, `trial_analytics`) via Pyroscope tags.
- **Loki Logs**: Deep log search without metrics noise.
- **Tempo Traces**: Distributed tracing and service graphs.

### 🛡️ Production Grade
- **Two-layer alerting**: Grafana Alerting (dashboard rules) + standalone Alertmanager (Prometheus rules) — both route to ops/critical email via the same severity/category label convention.
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

GatewayZ uses a **two-layer alerting architecture** — both layers send email using the same routing logic, so no alert falls through whether it originates from a Grafana rule or a raw Prometheus rule.

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Grafana Alerting (dashboard-based)                    │
│  Rules in grafana/provisioning/alerting/rules/                  │
│  → contact_points.yml → notification_policies.yml → Email       │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Prometheus → Alertmanager (rule-based)                │
│  Rules in prometheus/alert.rules.yml                            │
│  → alertmanager:9093 → alertmanager/alertmanager.yml → Email    │
└─────────────────────────────────────────────────────────────────┘
```

### Alert Philosophy

1. **Every alert MUST be actionable** - if you can't fix it, don't alert on it
2. **Fewer high-quality alerts** - 14 essential alerts instead of 25+ noisy ones
3. **Warning vs Critical** - warning = investigate soon, critical = wake someone up
4. **No duplicates** - consolidated overlapping alerts into single actionable items

---

### Layer 1: Grafana Alerting

Grafana evaluates alert rules against Prometheus/Mimir queries and routes firing alerts to email contact points using a notification policy tree.

#### Alert Rules

**Directory:** `grafana/provisioning/alerting/rules/`

| File | Alert Category |
|------|---------------|
| `traffic_anomalies.yml` | Traffic spikes, traffic drops |
| `error_rate_anomalies.yml` | Error rate spikes by provider |
| `latency_anomalies.yml` | P99 latency spikes and anomalies |
| `availability_anomalies.yml` | Provider availability drops, circuit breakers |
| `slo_burn_rate_alerts.yml` | SLO violation burn-rate alerts |
| `backend_alerts.yml` | Backend service health |
| `model_alerts.yml` | Model-specific issues |

#### Contact Points

**File:** `grafana/provisioning/alerting/contact_points.yml`

Email addresses are provisioned here. Grafana reads this file at startup — update it to change recipients without touching the Railway dashboard.

#### Notification Policies

**File:** `grafana/provisioning/alerting/notification_policies.yml`

| Matcher | Receiver | Repeat |
|---------|----------|--------|
| `severity=critical` | critical-email | 15m |
| `category=traffic_spike, severity=critical` | critical-email | 15m |
| `category=error_rate_spike` | ops-email | 30m |
| `component=slo, severity=critical` | critical-email | 15m |
| `category=latency_anomaly` | ops-email | 1h |
| `category=availability_drop, severity=critical` | critical-email | 15m |
| `category=circuit_breaker` | critical-email | 15m |
| `category=model` | ops-email | 30m |
| `category=logs` | ops-email | 30m |
| _(default)_ | ops-email | 1h |

---

### Layer 2: Alertmanager Service

The `alertmanager/` directory is a **standalone Docker/Railway service** (port 9093). Prometheus forwards its firing rules to Alertmanager via the `alerting:` block in `prometheus/prometheus.yml`. Alertmanager then applies its own routing tree and delivers email.

This mirrors Layer 1 exactly — the same severity + category labels drive the same ops/critical split — so teams get alerts from both paths without reconfiguring anything.

#### Routing tree (alertmanager/alertmanager.yml)

| Category / Severity | Receiver | group_wait | repeat_interval |
|--------------------|----------|------------|-----------------|
| `severity=critical` | critical-email | 0s | 15m |
| `category=slo, severity=critical` | critical-email | 0s | 15m |
| `category=traffic_spike, severity=critical` | critical-email | 10s | 15m |
| `category=error_rate_spike, severity=critical` | critical-email | 0s | 15m |
| `category=server_errors` | critical-email | 0s | 15m |
| `category=latency_spike` | critical-email | 0s | 15m |
| `category=latency_anomaly, severity=critical` | critical-email | 10s | 15m |
| `category=availability_drop, severity=critical` | critical-email | 0s | 15m |
| `category=circuit_breaker` | critical-email | 0s | 15m |
| `category=multi_provider_degradation` | critical-email | 0s | 15m |
| _(traffic/latency/availability non-critical)_ | ops-email | 30s | 1h |
| `category=model` | ops-email | 5m | 30m |
| `category=backend` | ops-email | 5m | 30m |
| `category=logs` | ops-email | 30s | 30m |
| _(default)_ | ops-email | 30s | 1h |

#### Inhibition rules

- Suppress `warning` alerts when a `critical` fires for the same `alertname` + `instance`
- Suppress `availability_drop` alerts when `multi_provider_degradation` fires (prevents flood from individual providers)

#### Alertmanager service files

| File | Purpose |
|------|---------|
| `alertmanager/Dockerfile` | `prom/alertmanager:v0.27.0`, exposes 9093 |
| `alertmanager/alertmanager.yml` | Routing tree + email receivers (placeholders substituted at startup) |
| `alertmanager/entrypoint.sh` | Substitutes env var placeholders → hands off to alertmanager binary |
| `alertmanager/railway.toml` | Railway build + healthcheck config |

---

### Setting Up Email Alerts

Both alerting layers share the same SMTP configuration. Set these once via environment variables.

#### Required environment variables

| Variable | Example | Notes |
|----------|---------|-------|
| `SMTP_FROM` | `alerts@gatewayz.ai` | From address for Alertmanager emails |
| `SMTP_USER` | `alerts@gatewayz.ai` | SMTP auth username |
| `SMTP_PASSWORD` | `app-password-here` | SMTP app-password (not your main password) |
| `SMTP_HOST` | `smtp.gmail.com:465` | Default: `smtp.gmail.com:465` |
| `ALERT_EMAIL_OPS` | `team@company.com` | Operational alerts recipient(s) |
| `ALERT_EMAIL_CRIT` | `oncall@company.com` | Critical/pager alerts recipient(s) |

> **For Grafana email** (Layer 1), also set `GF_SMTP_ENABLED=true`, `GF_SMTP_HOST`, `GF_SMTP_USER`, `GF_SMTP_PASSWORD`, `GF_SMTP_FROM_ADDRESS` on the Grafana service — or use the shared `GF_SMTP_*` vars which `alertmanager/entrypoint.sh` will fall back to automatically.

#### Local (docker-compose.yml)

The `alertmanager` service reads `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD` from the environment or docker-compose `environment:` block. No additional configuration needed — `entrypoint.sh` substitutes placeholders at startup.

```bash
# Test alertmanager is up
curl http://localhost:9093/-/healthy

# Check active alerts
curl http://localhost:9093/api/v2/alerts

# Send a test alert via Prometheus API (fires for 1 minute)
curl -X POST http://localhost:9090/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"}}]'
```

#### Railway (Production)

Deploy Alertmanager as a separate Railway service in the **same project** as Prometheus and Grafana so it shares the private `railway.internal` network.

1. In the Railway dashboard, add a new service sourced from this repository
2. Set the root directory to `alertmanager/` (or use the `alertmanager/railway.toml` config)
3. Set required env vars on the **Alertmanager** service:
   ```
   SMTP_FROM=alerts@gatewayz.ai
   SMTP_USER=alerts@gatewayz.ai
   SMTP_PASSWORD=<app-password>
   ALERT_EMAIL_OPS=team@company.com,oncall@company.com
   ALERT_EMAIL_CRIT=oncall@company.com
   ```
4. Set the following env var on the **Prometheus** service so it routes alerts to Alertmanager:
   ```
   ALERTMANAGER_INTERNAL_URL=http://alertmanager.railway.internal:9093
   ```
   _(If not set, `prometheus/entrypoint.sh` auto-detects Railway environment and uses `alertmanager.railway.internal:9093` as the default.)_

---

### Prometheus Alert Rules

**File:** `prometheus/alert.rules.yml`

| Group | Alerts | Purpose |
|-------|--------|---------|
| **service_health** | 3 | Is the service up and responding? |
| **api_performance** | 3 | Are API responses healthy? |
| **provider_health** | 3 | Are upstream AI providers working? |
| **infrastructure** | 5 | Is the monitoring stack itself healthy? |

#### Current Alerts

| Alert | Severity | Trigger | Action |
|-------|----------|---------|--------|
| `GatewayZAPIDown` | critical | Prometheus can't scrape API for 2m | Check Railway deployment |
| `HighErrorRate` | critical | >10% error rate for 5m | Check Loki logs, recent deployments |
| `AvailabilitySLOBreach` | critical | <99.5% success rate over 1h | Initiate incident response |
| `HighAPILatency` | warning | P95 > 3s for 5m | Check slow endpoints, providers |
| `LatencyDegradation` | warning | 50% latency increase vs 1h ago | Check recent changes, resources |
| `TrafficSpike` | warning | 3x traffic increase for 10m | Analyze traffic, check for abuse |
| `ProviderHighErrorRate` | critical | >20% errors per provider for 5m | Check provider status, failover |
| `SlowProviderResponse` | warning | P95 > 5s per provider for 10m | Monitor provider, adjust timeouts |
| `LowModelHealthScore` | warning | <80% success rate for 5m | Review errors across providers |
| `ScrapeTargetDown` | warning | Any scrape target down for 5m | Check target health, network |
| `MimirRemoteWriteFailures` | warning | Failed samples to Mimir | Check Mimir health, storage |
| `MimirDown` | critical | Mimir unreachable for 2m | Check container, storage volume |
| `TempoNoTraces` | warning | No traces for 15m | Check OTLP endpoint, backend config |
| `LokiNoLogs` | warning | No logs for 15m | Check Loki health, log shipping |

---

### Viewing Alerts

- **Grafana Alerting UI:** Alerting → Alert rules → firing/pending
- **Prometheus UI:** http://localhost:9090/alerts
- **Alertmanager UI:** http://localhost:9093 (silence management, active alerts)
- **API:**
  ```bash
  # Firing alerts from Alertmanager
  curl http://localhost:9093/api/v2/alerts | jq '.[].labels'

  # Firing alerts from Grafana
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
```

**Environment variables — set per service in the Railway dashboard:**

**Grafana service:**
```
PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
LOKI_INTERNAL_URL=http://loki.railway.internal:3100
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040
GF_SMTP_ENABLED=true
GF_SMTP_HOST=smtp.gmail.com:465
GF_SMTP_USER=alerts@gatewayz.ai
GF_SMTP_PASSWORD=<app-password>
GF_SMTP_FROM_ADDRESS=alerts@gatewayz.ai
```

**Prometheus service:**
```
FASTAPI_TARGET=api.gatewayz.ai:443
MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
ALERTMANAGER_INTERNAL_URL=http://alertmanager.railway.internal:9093
```

**Alertmanager service** (deploy `alertmanager/` as a separate Railway service):
```
SMTP_FROM=alerts@gatewayz.ai
SMTP_USER=alerts@gatewayz.ai
SMTP_PASSWORD=<app-password>
SMTP_HOST=smtp.gmail.com:465
ALERT_EMAIL_OPS=team@company.com
ALERT_EMAIL_CRIT=oncall@company.com
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
├── alertmanager/
│   ├── Dockerfile              # prom/alertmanager:v0.27.0, port 9093
│   ├── alertmanager.yml        # Routing tree + email receivers (placeholders)
│   ├── entrypoint.sh           # Substitutes env vars → execs alertmanager
│   └── railway.toml            # Railway build + healthcheck config
├── grafana/
│   ├── Dockerfile
│   ├── dashboards/
│   │   ├── golden-signals/     # Four Golden Signals (Latency/Traffic/Errors/Profiling)
│   │   ├── model_performance/  # Inference-Call-Profile, Model-Usage, Cache-Layer-Profile
│   │   ├── loki/               # Loki logs (pure logs)
│   │   ├── prometheus/         # Prometheus self-monitoring
│   │   ├── tempo/              # Tempo traces (pure traces)
│   │   └── mimir/              # Mimir long-term metrics
│   ├── datasources/
│   │   └── datasources.yml     # Prometheus, Mimir, Loki, Tempo, Pyroscope
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── alerting/
│           ├── rules/          # Grafana alert rule YAML files (Layer 1)
│           ├── contact_points.yml
│           └── notification_policies.yml
├── prometheus/
│   ├── Dockerfile
│   ├── entrypoint.sh           # Environment-based target resolution
│   ├── prometheus.yml          # Scrape jobs + remote_write to Mimir + alerting block
│   └── alert.rules.yml         # Prometheus alert rules (Layer 2 — sent to Alertmanager)
├── pyroscope/
│   ├── Dockerfile
│   └── pyroscope.yml           # Self-hosted Pyroscope configuration
├── mimir/
│   ├── Dockerfile
│   └── mimir.yml               # Mimir configuration (30d retention)
├── loki/
│   ├── Dockerfile
│   └── loki.yml                # Loki configuration
├── tempo/
│   ├── Dockerfile
│   ├── entrypoint.sh           # Environment-based configuration
│   └── tempo.yml               # Tempo configuration
├── scripts/
│   ├── pre-build-cleanup.sh    # Railway pre-deploy cleanup
│   └── ...                     # Other validation scripts
├── tests/                      # Pytest test suite
├── docs/                       # Documentation
├── railway.toml                # Railway deployment configuration
├── docker-compose.yml          # Local development
└── README.md                   # This file
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

## 🔬 Continuous Profiling (Self-hosted Pyroscope)

The stack is **LGTMP**: Loki · Grafana · Tempo · Mimir · **Pyroscope**.

### Architecture

The `gatewayz-backend` and `railway-grafana-stack` live in **two separate Railway projects**. Pyroscope runs as a service inside this (grafana-stack) project, so Grafana reaches it via Railway's internal DNS at zero cost. The backend, being in a different project, pushes profiles over Pyroscope's public Railway domain.

```
gatewayz-backend  (Railway project A)
  └─ pyroscope-io SDK  →  PUSH (HTTP) every 15 s
       └──────────────────────────────────────────────────────────────►
                                              https://<pyroscope-public-domain>.up.railway.app
                                                              │
                                              railway-grafana-stack  (Railway project B)
                                                ├─ Pyroscope service  (:4040, internal)
                                                │     stores profiles on /data/pyroscope
                                                └─ Grafana  READ via  http://pyroscope.railway.internal:4040
```

### Services table

| Service | Port | Notes |
|---------|------|-------|
| **Pyroscope** | 4040 | Internal only. Backend pushes via public domain. Grafana reads via `.railway.internal`. |

### Why profiling matters for GatewayZ

The Four Golden Signals tell you **what** is wrong. Profiling tells you **which line of code** is causing it.

| Four Golden Signals say | Profiling adds |
|-------------------------|---------------|
| CPU saturation at 90% | Which function burns the cycles? Token counter? JSON streaming serializer? |
| Memory growing 50 MB/hour | Which object accumulates? A model-catalog cache with no TTL? An open SSE connection? |
| P99 latency spiked to 8 s | What was the thread actually doing? Waiting on a Redis lock? A slow provider HTTP call? |

### Provider & Model tagged flamegraphs

Every inference call in `chat_handler.py` is wrapped with `pyroscope.tag_wrapper()` so flamegraphs can be filtered by the upstream provider and model:

```
Inference Profiling dashboard → filter $provider=openrouter, $model=claude-3-5-sonnet
  → see exactly which Python functions consumed CPU during those calls
```

Tags applied at the `_call_provider` / `_call_provider_stream` boundaries:
- `provider` — e.g. `openrouter`, `cerebras`, `groq`
- `model` — e.g. `claude-3-5-sonnet-20241022`
- `service_name` — always `gatewayz-backend`
- `environment` — Railway environment (`production` / `staging` / `local`)

### How to activate

**Step 1 — Generate a public domain for Pyroscope in Railway:**

Railway dashboard → grafana-stack project → **Pyroscope service** → Settings → **Generate Domain**

Copy the generated URL (e.g. `https://pyroscope-production-xxxx.up.railway.app`).

**Step 2 — Set env vars on the backend service (Project A):**

```
PYROSCOPE_ENABLED=true
PYROSCOPE_SERVER_ADDRESS=https://pyroscope-production-xxxx.up.railway.app
```

No auth variables needed — self-hosted Pyroscope has no authentication by default.

**Step 3 — Set env vars on the Grafana service (Project B):**

```
PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040
```

That's it. Grafana reaches Pyroscope via the internal network; the backend pushes over the public domain.

### Local development

With `docker compose up`, Pyroscope starts automatically. Grafana uses the `http://pyroscope:4040` default (set via the `PYROSCOPE_INTERNAL_URL` docker-compose env var). To push profiles locally, set `PYROSCOPE_SERVER_ADDRESS=http://localhost:4040` on the backend.

### What you get

- **Inference Profiling dashboard** (`model_performance/Inference-Profiling`) — flamegraph + CPU bargauges broken down by provider and model, sample rate over time
- **Trace → Profile drill-down** — click any slow span in Tempo → **"View Profile"** jumps to the Pyroscope flamegraph at that exact timestamp, no manual matching needed
- **Always-on sampling** — 100 Hz regardless of traffic, catches every P99 outlier (unlike Sentry's 5% transaction sample rate)

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

**GatewayZ Observability Stack** · Enterprise-grade monitoring for AI infrastructure · Powered by Prometheus, Alertmanager, Mimir, Loki, Tempo, Pyroscope, and Grafana
