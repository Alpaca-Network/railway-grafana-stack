# GatewayZ Observability Stack

**Production-ready observability platform for GatewayZ AI Backend** — Centralized metrics, logs, traces, profiles, and alerting deployed on Railway.

[![Railway Deploy](https://railway.app/button.svg)](https://railway.app)

---

## The Epic — What This Is and Why It Exists

### What is GatewayZ?

GatewayZ is an AI inference gateway. It sits between your application and the LLM providers (OpenAI, Anthropic, OpenRouter, Groq, Cerebras, and 25+ more), handling routing, load balancing, rate limiting, circuit breaking, and token tracking across all of them in one FastAPI service.

### The Observability Problem

When you route production AI traffic through 30+ providers, you quickly hit questions that standard logging can't answer:

- Which provider is degrading right now — and is it affecting only one model or all of them?
- My P99 latency spiked to 8 seconds. Is it the provider HTTP call, the token counter, or the Redis cache layer?
- A circuit breaker opened on `openrouter/claude-3-5-sonnet`. How long has it been open and when did it first fire?
- My token budget burned 40% faster this week. Which model and which user drove that?
- Is the spike in errors a transient provider blip or a real regression in my routing logic?

None of these questions have simple answers if all you have is basic application logging or a generic APM tool. You need **four separate observability signals** working together:

| Signal | What it tells you | Stored in |
|--------|------------------|-----------|
| **Metrics** | Counts, rates, and percentiles over time | Prometheus → Mimir |
| **Logs** | Detailed text events per request | Loki |
| **Traces** | The exact path and timing of each request through each service | Tempo |
| **Profiles** | Which lines of Python code are burning the CPU | Pyroscope |

### What This Stack Provides

This repository is the complete observability stack for GatewayZ — 8 services deployed together, pre-wired, pre-configured, with 17 Grafana dashboards covering every aspect of AI inference operations:

- **430+ dashboard panels** across Four Golden Signals, Model Performance, Provider Directory, Infrastructure Health, Log-Derived Metrics, and more
- **Two-tier alerting**: 40+ Grafana alert rules + 16 standalone Prometheus rules, both routing to ops/critical email
- **32 Prometheus recording rules** + **35 Loki recording rules** that pre-compute anomaly detection baselines and aggregate high-cardinality log data into bounded metrics
- **Cross-signal navigation**: click a slow metric → jump to the Tempo trace → jump to the Pyroscope flamegraph at that exact timestamp
- **Provider/model tagged CPU profiles** — every inference call in the backend is tagged with `provider` and `model` so you can filter flamegraphs to exactly the calls you care about

---

## Why This Stack? — Tool Selection Rationale

If you're new to this stack, here's why each tool was chosen over the alternatives:

| Tool | Why we use it | What we considered instead |
|------|--------------|--------------------------|
| **Grafana 11.5.2** | Industry-standard visualization with native plugins for every service in this stack. Alerting, dashboards, and datasource management in one place. | Datadog / New Relic — expensive SaaS with per-host pricing that doesn't scale for inference volume |
| **Prometheus** | De-facto standard for metrics scraping. Native `prometheus_client` integration for FastAPI. Rich PromQL ecosystem. | OpenTelemetry Collector alone — doesn't provide the same scrape model or alerting rules |
| **Mimir 2.11.0** | Long-term Prometheus-compatible storage (30-day retention). Prometheus alone only holds 15 days and loses data on restart. Mimir is drop-in compatible — same PromQL, same API. | Prometheus-only — too short retention, no HA; VictoriaMetrics — slightly different API surface |
| **Loki 3.4** | Log aggregation built for Kubernetes/container labels. No full-text indexing cost — only indexes labels (app, level, service), which is enough for correlation. Native Grafana integration. | Elasticsearch / Splunk — full-text indexing is expensive and overkill when you have trace_id correlation; self-managed ELK is heavyweight |
| **Tempo** | Distributed tracing with native OTLP receiver (the OpenTelemetry standard). Generates span metrics (`traces_spanmetrics_*`) that feed directly into Mimir. No per-span billing. | Jaeger — doesn't generate span metrics, less Grafana integration; Zipkin — limited OpenTelemetry support |
| **Pyroscope 1.7.1** | Always-on continuous profiling at 100 Hz. Catches every P99 CPU outlier, not just sampled transactions. Supports provider/model tags on flamegraphs. Links directly from Tempo spans. | py-spy / sampling profilers — miss tail latency; Sentry performance (5% sample rate, no flamegraphs) |
| **Alertmanager v0.27.0** | Standalone alert routing service. Fires even if Grafana is down. Provides inhibition rules (suppress warning floods when a critical fires). Mirrors Grafana's notification policy tree for two-tier ops/critical routing. | Grafana alerting only — single point of failure; no inhibition rules |
| **Railway** | Zero-ops container hosting with internal private DNS (`.railway.internal`) for free inter-service networking. Services in the same Railway project can reach each other without public URLs or VPNs. | AWS ECS / GCP Cloud Run — more infrastructure overhead; Fly.io — no built-in internal networking for free |

---

## New Developer Onboarding

If you just joined and have no background in any of these tools, start here:

**Step 1 — Understand the system conceptually**
Read the Architecture Overview section below. Focus on the data flow diagram and the data type separation table. The key insight: each service stores a different data type and is optimized for it. Do not try to store logs in Prometheus or metrics in Loki.

**Step 2 — Read the full architectural wiki**
Open [MASTER.md](MASTER.md) — it's the single source of truth for every architectural decision, every datasource UID, every dashboard, every alert rule, and every known gap. Pay attention to §16 (Backend Telemetry Architecture) if you're integrating the backend.

**Step 3 — Understand what the backend must expose**
Read [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md). This tells you exactly which Prometheus metrics, Loki labels, and OTLP attributes the backend must emit for the dashboards to show data.

**Step 4 — Run it locally**
```bash
export FASTAPI_TARGET="host.docker.internal:8000"  # or your backend's address
docker compose up --build
open http://localhost:3000  # Grafana — admin / yourpassword123
```
All 8 services will start. Check `http://localhost:9090/targets` to confirm Prometheus is scraping your backend.

**Step 5 — Explore the dashboards**
- **Four Golden Signals** — Start here. Latency, Traffic, Errors, Pyroscope profiling row.
- **Provider Directory** — Per-provider health scores, circuit breaker states, availability matrix.
- **Inference Call Profile** — CPU cost anatomy broken down by provider and model.
- **Infrastructure Health** — Stack health, Mimir remote write, Loki ingestion rates.

**For deployment to Railway:** Follow [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md).

**Acceptance criteria for all 25 project tasks:** See [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md).

---

## Quick Start

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

**Documentation:**
- **[Complete Documentation Index](docs/docs-index.md)** — Start here for all guides and references
- **[Cheatsheet](docs/cheatsheet.md)** — Common commands and queries
- **[Troubleshooting](docs/troubleshooting/REMOTE_WRITE_DEBUG.md)** — Fix common issues
- **[Architecture](docs/architecture/MIMIR.md)** — System design and components

---

## Architecture Overview

### How the Data Types Work Together

Before looking at the diagram, here's the conceptual model:

**Metrics** are numbers sampled over time — request counts, error rates, latency percentiles. Prometheus scrapes them from your backend's `/metrics` endpoint every 15 seconds and stores them locally (15-day retention). Prometheus then remote-writes everything to **Mimir**, which holds 30 days of history and survives Prometheus restarts.

**Logs** are text events — structured JSON lines your backend emits for every request, error, and state change. The backend pushes them directly to **Loki** over HTTP. Loki stores them for 30 days, indexed only by labels (`app`, `level`, `service`) rather than full-text, keeping storage costs low.

**Traces** are maps of a request's journey through your system — which functions ran, in what order, how long each took. The backend uses the OpenTelemetry SDK to push OTLP-format traces to **Tempo** on every request. Tempo also generates derived span metrics (`traces_spanmetrics_*`) and writes them to Mimir.

**Profiles** are CPU and memory flamegraphs — a continuous record of which functions are consuming CPU at 100Hz sampling. The backend uses the Pyroscope SDK to push profiles to **Pyroscope** every 15 seconds, tagged by provider and model. This tells you *which line of code* causes that 8-second P99 latency.

**Provider health** is computed data — health scores, circuit breaker states, and availability percentages calculated server-side by the backend and exposed via `/prometheus/data/metrics`. The **JSON-API-Proxy** (a small Flask service) polls this endpoint and translates it into the Simple JSON format that Grafana can query directly for real-time provider status panels.

The key rule: **each service stores only its own data type**. Prometheus does not store traces. Grafana queries each service for its own data type. **Exception:** Loki's ruler evaluates LogQL recording rules and remote-writes *derived metrics* (not raw logs) to Mimir — the same pattern Tempo uses for span metrics.

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
            │ remote_write        │ ruler remote_write  │ metrics_generator
            │ /api/v1/push        │ /api/v1/push        │ remote_write
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
    │     Mimir     │                            │     Mimir     │
    │    :9009      │◄───────────────────────── │  (span metrics│
    │               │  Loki ruler sends         │   from traces)│
    │  Long-term    │  log-derived metrics      │               │
    │  30d Retain   │  (recording rules)        │               │
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

### Data Type Separation

| Component | Stores | Writes To | Notes |
|-----------|--------|-----------|-------|
| **Prometheus** | Metrics (time-series) | **Mimir** via remote_write | Short-term storage, scrapes every 15-30s |
| **Mimir** | Metrics (time-series) | Local filesystem | Long-term storage, 30-day retention |
| **Loki** | Logs (text lines) | Local filesystem + **Mimir** (recording rule metrics only) | Logs stored locally; ruler aggregates log data into metrics → Mimir |
| **Tempo** | Traces (spans) | Local filesystem + **Mimir** (span metrics only) | Traces stored locally, derived metrics to Mimir |

> **Loki → Mimir flow:** Loki stores **log lines** (text data) locally. Its ruler component evaluates LogQL recording rules every 1 minute and remote-writes the resulting **derived metrics** (counts, ratios, aggregations) to Mimir — the same pattern Tempo uses for span metrics. Raw logs are never sent to Mimir; only pre-aggregated numeric time-series are.

### Key Components

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Grafana 11.5.2** | 3000 | Visualization & dashboards | ✅ 6 dashboard folders |
| **Prometheus 3.2.1** | 9090 | Metrics collection + alerting rules | ✅ 6 scrape jobs |
| **Alertmanager v0.27.0** | 9093 | Alert routing → email (ops + critical) | ✅ Mirrors Grafana notification policies |
| **Mimir 2.11.0** | 9009, 9095 | Long-term metrics storage | ✅ 30-day retention |
| **Loki 3.4** | 3100 | Log aggregation + ruler (35 recording rules → Mimir) | ✅ 30-day retention, ruler remote_write |
| **Tempo** | 3200, 4317, 4318 | Distributed tracing | ✅ OTLP endpoints |
| **Pyroscope 1.7.1** | 4040 | Continuous CPU profiling | ✅ Provider/model/cache tagged flamegraphs |
| **JSON-API-Proxy** | 5050 | Provider health bridge (Flask → Grafana Simple JSON) | ✅ Circuit breaker states, health scores |

---

## Backend Telemetry Pipeline

The `gatewayz-backend` (FastAPI) emits telemetry on **four channels** that feed this stack:

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
gatewayz-backend (JSON structured logging via LokiLogHandler)
  └── Async queue → Loki push :3100
        Stream Labels: app, environment, service, level, logger,
                       trace_id, span_id, path, method, provider,
                       model, user_id, error_type
                    │
                    ├─► Grafana queries Loki directly (query-time LogQL)
                    │     Log→Trace correlation via trace_id → Tempo
                    │
                    └─► Loki ruler evaluates 35 recording rules every 1m
                          │
                          └─► Remote write derived metrics → Mimir :9009
                                │
                                └─► Grafana queries Mimir (pre-aggregated)
                                      provider×model matrix, error ratios,
                                      anomaly baselines, streaming stats
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

## Loki Recording Rules & High-Cardinality Monitoring

### The Problem

GatewayZ routes AI inference requests across 30+ providers and 100+ models, generating log data with high-cardinality fields (request IDs, model variants, provider×model combinations, per-user sessions). Tracking every combination as a native Prometheus metric would cause cardinality explosion (~3,000+ time series from provider×model alone). Traditional metrics can't answer questions like "which provider×model combination has the highest error rate this week?"

### The Solution

Loki's **ruler** component evaluates LogQL recording rules every minute and remote-writes the resulting aggregated metrics to Mimir. This collapses high-cardinality log data into bounded, queryable metrics — the same pattern Tempo uses for span metrics.

```
Backend logs (JSON, high-cardinality stream labels)
        │
        ▼
    Loki (stores raw logs for 30 days)
        │
        └─► Ruler evaluates 35 LogQL recording rules every 1m
              │
              └─► Aggregated metrics remote-written to Mimir
                    │
                    └─► Grafana queries via grafana_mimir datasource
```

### Recording Rules: 7 Groups, 35 Rules

**File:** `loki/rules/gatewayz_log_recording_rules.yml`

| Group | Rules | What It Aggregates |
|-------|-------|--------------------|
| `loki_error_metrics` | 7 | Error counts by category: total, timeout, rate-limit, database, memory, auth, exceptions |
| `loki_provider_metrics` | 3 | Per-provider error count, timeout count, request volume |
| `loki_log_health` | 4 | Total log volume, level distribution, error-to-total ratio %, circuit breaker events |
| `loki_request_metrics` | 3 | HTTP volume by method, slow request count, token usage events |
| `loki_high_cardinality_aggregations` | 7 | **Provider×Model request matrix**, per-endpoint volume, error types, per-provider error ratio, streaming completions, slow TTFC |
| `loki_baselines` | 4 | 1h/24h averages for error rate, log volume, error ratio (anomaly detection) |
| `loki_high_cardinality_baselines` | 3 | 1h averages for provider×model volume/errors, per-provider error ratio |

All recording rule metric names use the `loki:` prefix (e.g., `loki:errors:count_per_minute`, `loki:requests:by_provider_model:count_per_5m`) to distinguish them from native Prometheus metrics.

### Infrastructure

| File | Purpose |
|------|---------|
| `loki/loki.yml` | Ruler block with remote_write to Mimir (`X-Scope-OrgID: anonymous`) |
| `loki/entrypoint.sh` | Runtime Mimir URL substitution (Railway vs Docker Compose) |
| `loki/rules/gatewayz_log_recording_rules.yml` | 35 LogQL recording rules in 7 groups |
| `loki/Dockerfile` | Copies rules + entrypoint into container |

### What This Enables

1. **Cost Optimization** — Aggregate thousands of per-request log entries into bounded provider/model metrics without overwhelming Mimir
2. **Root Cause Analysis** — Drill from a metric spike in Grafana to the exact log line using `provider`, `model`, `trace_id`, `error_type` stream labels
3. **Retroactive Business Intelligence** — Answer historical questions about provider costs, model usage trends, and token consumption from existing logs — no pre-planned instrumentation needed
4. **Anomaly Detection** — Recording rule baselines (1h/24h averages) enable alerts when current error rates exceed 2× the historical average
5. **Streaming Observability** — Track TTFC (time to first chunk), stream completions, and prompt routing across the full request lifecycle

---

## Dashboard Folders

All dashboards use **real API endpoints** with live data from Prometheus/Mimir — no mock data.

| Folder | Dashboard(s) | Purpose | Status |
|--------|-------------|---------|--------|
| **Four Golden Signals** | Four-Golden-Signals | Latency · Traffic · Errors · Pyroscope Profiling (Pillar IV) | ✅ Ready |
| **Model Performance** | Inference-Call-Profile, Model-Usage, Cache-Layer-Profile, Inference-Profiling, Provider-Directory | AI inference anatomy, token usage, Redis cache CPU, provider metrics | ✅ Ready |
| **Loki** | Live-GatewayZ-Logs, Error-Analysis, Security-RateLimit, **Log-Derived Metrics** | Log search, streaming, error patterns, **high-cardinality log-to-metrics analytics** | ✅ Ready |
| **Prometheus** | Prometheus self-monitoring | Scrape targets, query stats, remote_write health | ✅ Ready |
| **Tempo** | Tempo dashboards | Service graph, span metrics, trace search | ✅ Ready |
| **Mimir** | Mimir dashboards | Historical queries, retention stats | ✅ Ready |

### Dashboard Features

#### Model Performance
- **AI Provider Metrics**: Request rates by provider/model
- **Latency Analysis**: P50/P95/P99 percentiles
- **Token Usage**: Input/output token tracking
- **Error Rates**: By provider, model, and error type

#### Loki Dashboards (4 dashboards)
- **Live-GatewayZ-Logs**: Real-time log stream with filters by app, level, environment, free-text search
- **Error-Analysis**: Error anomaly detection, error-type distribution, reliability scoring
- **Security-RateLimit**: Auth failures, rate-limit violations, security anomaly thresholds
- **Log-Derived Metrics** *(NEW)*: 38-panel high-cardinality analytics dashboard — extracts metrics from logs at query time using LogQL and pre-aggregated Mimir recording rules:
  - Request performance by endpoint/method, slow request tracking, TTFC (time to first chunk) monitoring
  - Provider analytics: per-provider request volume, error rates, top-10 ranking, error distribution
  - Model usage: selection frequency, top-10 models, error hotspots, usage distribution pie charts
  - Provider×Model cardinality aggregation: recording rules collapse 30+ providers × 100+ models into bounded metrics
  - Anomaly detection: error rate vs 2× baseline threshold, log volume trends vs 1h averages
  - Streaming & inference: stream completion rate, prompt router selection frequency

#### Tempo (Tracing)
- **Pure trace data** from Tempo datasource
- **Service Graph**: Distributed tracing visualization
- **Span Metrics**: Request duration, error rates by service

#### Mimir Long-term Storage
- **Historical Queries**: 30-day retention for trend analysis
- **Consistent Results**: No data loss on Prometheus restarts

---

## Configuration

### Prometheus Scrape Jobs

**File:** `prometheus/prometheus.yml`

| Job Name | Target | Interval | Purpose |
|----------|--------|----------|---------|
| `prometheus` | localhost:9090 | 15s | Self-monitoring |
| `gatewayz_production` | `${FASTAPI_TARGET}` | 15s | **Production API metrics** |
| `gatewayz_data_metrics_production` | `${FASTAPI_TARGET}/prometheus/data/metrics` | 30s | Provider health, circuit breakers |
| `health_service_exporter` | :8002 | 30s | Health service exporter |
| `mimir` | mimir:9009 | 30s | Mimir self-monitoring |
| `tempo` | `${TEMPO_TARGET}` | 15s | Tempo self-monitoring |

#### IMPORTANT: `FASTAPI_TARGET` Configuration

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
| **Alertmanager** | `alertmanager` | alertmanager | `${ALERTMANAGER_INTERNAL_URL}` | Alert state visibility |
| **JSON API** | `grafana_json_api` | simplejson | `${JSON_API_URL}` | Provider health scores, circuit breaker states |

> **Datasource rule:** `grafana_prometheus` = standard app metrics. `grafana_mimir` = ONLY Tempo-generated `traces_spanmetrics_*` / `traces_service_graph_*` metrics. Never mix them in dashboards.

### Data Retention

| Service | Retention | Compaction | Notes |
|---------|-----------|------------|-------|
| **Prometheus** | 15 days | N/A | Short-term, remote writes to Mimir |
| **Mimir** | 30 days | Every 2h | Horizontal scaling, HA-ready |
| **Loki** | 30 days | Every 10m | TSDB index, filesystem storage |
| **Tempo** | 7 days | 5m blocks | Local filesystem |

---

## Backend Integration

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

**Complete Integration Guide:** [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)

---

## Troubleshooting

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

**More Solutions:** [docs/troubleshooting/](docs/troubleshooting/)

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

**More Solutions:** [docs/troubleshooting/REMOTE_WRITE_DEBUG.md](docs/troubleshooting/REMOTE_WRITE_DEBUG.md)

---

## Key Features

### Horizontal Scaling with Mimir
- Long-term metrics storage with 30-day retention.
- Horizontally scalable architecture.
- Remote write from Prometheus, Loki (recording rules), and Tempo (span metrics).

### High-Cardinality Log-to-Metrics Pipeline
- **35 Loki recording rules** aggregate high-cardinality log data (30+ providers × 100+ models) into bounded Mimir metrics.
- **Provider×Model matrix**, per-endpoint volumes, error categorization, streaming completion rates — all derived from logs without application code changes.
- **Anomaly detection baselines**: 1h/24h averages enable alerts when current rates exceed 2× historical average.
- **Retroactive BI**: Answer historical questions from existing logs without pre-planned instrumentation.

### Golden Signals Monitoring
- **Latency**: P50/P95/P99 percentiles + trends.
- **Traffic**: Request volume and rates by provider and model.
- **Errors**: Error rate gauge + trends per provider.
- **Profiling (Pillar IV)**: Continuous Pyroscope flamegraphs replace traditional saturation metrics — tells you *which line of code* is the bottleneck.

### Specialized Dashboards
- **Inference Call Profile**: Per-request CPU anatomy by provider/model.
- **Cache Layer Profile**: Redis CPU cost by cache layer (`auth`, `rate_limit`, `model_catalog`, `response_cache`, `trial_analytics`) via Pyroscope tags.
- **Loki Logs**: Deep log search, error analysis, security monitoring, and **log-derived metrics** (38-panel high-cardinality analytics dashboard).
- **Tempo Traces**: Distributed tracing and service graphs.

### Production Grade
- **Two-layer alerting**: Grafana Alerting (dashboard rules) + standalone Alertmanager (Prometheus rules) — both route to ops/critical email via the same severity/category label convention.
- **Testing**: Comprehensive integration test suite (90+ tests).
- **Security**: No hardcoded credentials; fully environment-variable driven.

---

## Mimir Long-term Storage Setup

Mimir provides **30-day metric retention** with horizontal scaling. This is critical for:
- Historical trend analysis
- Consistent query results across page refreshes
- No data loss on Prometheus restarts

### How Data Gets to Mimir (3 Sources)

```
┌────────────┐    remote_write     ┌─────────────┐
│ Prometheus │ ────────────────────▶│    Mimir    │
│   :9090    │   /api/v1/push      │   :9009     │
│  (15d)     │   X-Scope-OrgID:    │             │
└────────────┘   anonymous         │  (30d)      │
      │                            │             │
┌────────────┐    ruler            │             │
│    Loki    │    remote_write     │             │
│   :3100    │ ────────────────────▶             │
│ (35 rules) │   log-derived       │             │
└────────────┘   metrics           │             │
                                   │             │
┌────────────┐    metrics_generator│             │
│   Tempo    │    remote_write     │             │
│   :3200    │ ────────────────────▶             │
│ (spans)    │   span metrics      └─────────────┘
└────────────┘                            │
                                          │ stores
                                          ▼
                                  ┌──────────────┐
                                  │ /data/mimir/ │
                                  │   blocks/    │
                                  │   tsdb/      │
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

## Alerting Setup

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

1. **Every alert MUST be actionable** — if you can't fix it, don't alert on it
2. **Fewer high-quality alerts** — 14 essential alerts instead of 25+ noisy ones
3. **Warning vs Critical** — warning = investigate soon, critical = wake someone up
4. **No duplicates** — consolidated overlapping alerts into single actionable items

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
   ALERT_EMAIL_OPS=team@company.com
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

## Testing & Quality Assurance

### Test Coverage

- **25+ Real API Endpoints** — Integration tests with performance validation
- **7 Production Dashboards** — Schema validation and configuration checks
- **90+ Test Methods** — Comprehensive coverage across all components
- **GitHub Actions Workflows** — Automated validation on every deployment

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

## Deployment

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
JSON_API_URL=http://json-api-proxy.railway.internal:5050
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

**JSON-API-Proxy service:**
```
GATEWAYZ_API_URL=https://api.gatewayz.ai
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

**Deployment Guide:** [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

---

## Documentation

### Core Documentation

- **[Documentation Index](docs/docs-index.md)** — Start here for all docs
- **[MASTER.md](MASTER.md)** — Full architectural wiki (16 sections)
- **[ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md)** — Acceptance criteria for all 25 project tasks
- **[Backend Integration](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)** — Required metrics and instrumentation
- **[Railway Deployment](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)** — Deploy to Railway
- **[Troubleshooting](docs/troubleshooting/)** — Service-specific fix guides

### Architecture Docs

- **[Mimir Architecture](docs/architecture/MIMIR.md)** — Long-term metrics storage
- **[Pyroscope Architecture](docs/architecture/PYROSCOPE.md)** — Continuous profiling setup
- **[JSON-API-Proxy Architecture](docs/architecture/JSON_API_PROXY.md)** — Provider health bridge

---

## Development

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
│   │   └── datasources.yml     # Prometheus, Mimir, Loki, Tempo, Pyroscope, JSON API
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── alerting/
│           ├── rules/          # Grafana alert rule YAML files (Layer 1)
│           ├── contact_points.yml
│           └── notification_policies.yml
├── json-api-proxy/
│   ├── Dockerfile
│   ├── app.py                  # Flask service translating /prometheus/data/metrics → Simple JSON
│   └── railway.toml
├── prometheus/
│   ├── Dockerfile
│   ├── entrypoint.sh           # Environment-based target resolution
│   ├── prometheus.yml          # Scrape jobs + remote_write to Mimir + alerting block
│   ├── alert.rules.yml         # Prometheus alert rules (Layer 2 — sent to Alertmanager)
│   └── recording_rules_baselines.yml  # 32 recording rules for anomaly detection
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
├── MASTER.md                   # Full architectural wiki
├── ACCEPTANCE_CRITERIA.md      # Acceptance criteria for all 25 Kanban tasks
├── railway.toml                # Railway deployment configuration
├── docker-compose.yml          # Local development
└── README.md                   # This file
```

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally with `docker compose up`
3. Run tests: `pytest tests/ -v`
4. Validate dashboards: `./scripts/validate_dashboards.sh strict`
5. Create pull request to `main`

---

## Cross-Signal Navigation (Breaking Down the Silos)

The biggest mistake in any observability setup is treating each panel as a silo. The stack is configured for end-to-end click-through navigation so you always move toward the root cause rather than copy-pasting IDs between tabs.

### How the links are wired

| From | To | Mechanism | How to trigger |
|------|-----|-----------|---------------|
| **Metric graph** | **Tempo trace** | Exemplar (blue ◆ dot on latency graphs) | Click the blue dot on any histogram panel |
| **Loki log line** | **Tempo trace** | Derived Field on `trace_id` JSON field | Click **"View Trace"** button next to any log entry |
| **Loki log label** | **Tempo trace** | Derived Field on `trace_id` Loki label | Click **"View Trace"** button in label sidebar |
| **Tempo span** | **Mimir metric** | `tracesToMetrics` → `grafana_mimir` | In Tempo, click a span → "Related metrics" |
| **Tempo span** | **Loki logs** | `tracesToLogs` → `grafana_loki` | In Tempo, click a span → "Related logs" |
| **Tempo span** | **Pyroscope flamegraph** | `tracesToProfiles` → `grafana_pyroscope` | In Tempo, click a span → "View Profile" |
| **Tempo service graph** | **Node topology** | `serviceMap` → `grafana_mimir` | Service Graph & Topology section in dashboard |

### Implementation details

**Exemplars (Mimir + Prometheus → Tempo):** Both datasources have `exemplarTraceIdDestinations` set to `trace_id` (underscore, matching the OpenTelemetry field name the backend emits). The field names are now consistent — previously Mimir was using `traceId` (camelCase), which would have silently failed.

**Derived Fields (Loki → Tempo):** Two matchers are configured — one for JSON-structured log lines (`"trace_id": "..."`) and one for Loki labels. Both resolve to the Tempo datasource so the button appears regardless of how the backend emits the ID.

**Service Graph (Tempo → Mimir):** Tempo's `metrics_generator` with the `service-graphs` processor generates `traces_service_graph_*` metrics and remote-writes them **directly to Mimir** — they are never in Prometheus. The `serviceMap` datasource is correctly set to `grafana_mimir`. Similarly, `tracesToMetrics` points to Mimir because span metrics (`traces_spanmetrics_*`) are also Mimir-only.

### Resource attribute consistency requirement

For the `$service` template variable and cross-signal filtering to work reliably, the backend must emit consistent resource attributes across all four signals:

```
service.name  = "gatewayz-api"      # must match in spans, logs, and metrics
instance.id   = "<pod-or-host-id>"  # must match for per-instance filtering
```

Configure this once in the OpenTelemetry SDK resource at process startup — it propagates to Tempo (spans), Loki (log labels via the OTEL log handler), and Prometheus (target labels via relabeling).

---

## Continuous Profiling (Self-hosted Pyroscope)

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

## Support & Resources

### External Documentation

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Pyroscope Documentation](https://grafana.com/docs/pyroscope/latest/)
- [Railway Documentation](https://docs.railway.app/)

### Getting Help

- **Documentation Issues:** Check [docs/troubleshooting/](docs/troubleshooting/)
- **Backend Integration:** See [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)
- **Deployment Help:** Review [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)
- **Architecture Questions:** See [MASTER.md](MASTER.md)

---

## License

Proprietary — GatewayZ Network

---

**GatewayZ Observability Stack** · Enterprise-grade monitoring for AI infrastructure · Powered by Prometheus, Alertmanager, Mimir, Loki, Tempo, Pyroscope, and Grafana
