# GatewayZ LGTM Observability — Master Reference

> **Branch:** `refactor/refactor-master-markdowns` | **Last Updated:** March 2026
> **Purpose:** Single source of truth for any agent or engineer before taking action on this repo.

---

## 1. What This Project Is

**GatewayZ LGTM Stack** is the production observability platform for the [GatewayZ AI Inference Gateway](https://api.gatewayz.ai). It provides full-stack telemetry across metrics, logs, traces, and continuous profiling — deployed on [Railway.app](https://railway.app) and accessible at **[logs.gatewayz.ai](https://logs.gatewayz.ai)**.

**Stack acronym:** LGTM = Loki · Grafana · Tempo · Mimir (+ Prometheus, Alertmanager, Pyroscope)

**Backend being observed:** `gatewayz-backend` — a FastAPI AI gateway routing requests to 30+ LLM providers.

---

## 2. Quick Status (March 2026)

| Area | Status | Notes |
|------|--------|-------|
| Core Stack (8 services) | ✅ Production-ready | Docker Compose + Railway configs complete |
| Mimir long-term storage | ✅ Complete | Integrated January 2026, 30d retention |
| Grafana Dashboards | ✅ 15/15 complete | All panels populated with live queries |
| System Quality Dashboard | 🔄 In progress | Folder registered; JSON being built |
| Prometheus Alert Rules | ✅ 16 rules | Covering service health, performance, security |
| Grafana Alert Rules | ✅ 40+ rules | 10 YAML files, full severity coverage |
| Alertmanager | ✅ Complete | Two-tier email routing (ops + critical) |
| Recording Rules | ✅ 32 rules | Pre-computed baselines for anomaly detection |
| Datasources | ✅ 7 configured | Prometheus, Mimir, Loki, Tempo, Pyroscope, Alertmanager, JSON-API |
| Documentation | ✅ 48 files | Architecture, deployment, troubleshooting |
| Backend FASTAPI_TARGET | ⚠️ Needs verification | Env var must be set in Railway for live metrics |
| OTLP Trace Export | ⚠️ Needs verification | Backend must export to Tempo:4317 |
| Redis Exporter | ⚠️ Partial | Noted as unreliable in docs, needs validation |
| Mimir S3 storage | ⚠️ Not configured | Currently filesystem; S3 recommended for prod |

---

## 3. Architecture Overview

### Data Flow

```
GatewayZ Backend (FastAPI)
    │
    ├─── /metrics endpoint ──────────► Prometheus (scrape, 15s)
    │                                       │
    │                                       ├─► Remote Write ──► Mimir (30d storage)
    │                                       │
    │                                       └─► alert.rules.yml ──► Alertmanager ──► Email
    │
    ├─── Structured Logs (stdout) ──► Loki (30d retention, TSDB v13)
    │
    └─── OTLP Traces (4317/4318) ───► Tempo (48h retention)
                                           │
                                           └─► Span Metrics ──► Mimir

Grafana (port 3000 / logs.gatewayz.ai)
    ├─ Queries: Prometheus (real-time) + Mimir (historical)
    ├─ Queries: Loki (logs)
    ├─ Queries: Tempo (traces)
    ├─ Queries: Pyroscope (flamegraphs)
    └─ Alerts: 40+ Grafana-managed rules ──► Alertmanager ──► Email

Pyroscope (port 4040) ─── Continuous CPU/memory profiling
JSON-API-Proxy (port 5050) ─── Custom dashboard data from api.gatewayz.ai
```

### Service Map

| Service | Internal Port | External | Version |
|---------|--------------|----------|---------|
| Grafana | 3000 | logs.gatewayz.ai | 11.5.2 |
| Prometheus | 9090 | — | latest |
| Mimir | 9009 / 9095 | — | latest |
| Loki | 3100 / 9096 | — | latest |
| Tempo | 3200 / 4317 / 4318 | — | latest |
| Alertmanager | 9093 | — | latest |
| Pyroscope | 4040 | — | latest |
| JSON-API-Proxy | 5050 | — | custom Flask |

---

## 4. Stack Components & Status

### Prometheus
- **Config:** `prometheus/prometheus.yml`
- **Scrape jobs:** 6 (prometheus self, gatewayz_production, health_service_exporter, gatewayz_data_metrics_production, mimir, tempo)
- **Remote write:** → Mimir at `/api/v1/push` (10k queue, 50 shards)
- **Alert rules:** `alert.rules.yml` (16 rules) + `recording_rules_baselines.yml` (32 rules)
- **Status:** ✅ Complete

### Mimir
- **Config:** `mimir/mimir.yml`
- **Mode:** Monolithic (all-in-one)
- **Retention:** 30 days
- **Storage:** Filesystem `/data/mimir` (S3 recommended for HA)
- **Ports:** 9009 (HTTP query), 9095 (gRPC remote write)
- **Max series:** 500,000 / tenant
- **Status:** ✅ Complete (integrated Jan 2026)

### Grafana
- **Config:** `grafana/provisioning/`
- **Dashboards:** 15 provisioned (+ 1 in progress)
- **Datasources:** 7 configured
- **Alerts:** 40+ rules across 10 YAML files
- **Plugins:** Pyroscope, simple-json-datasource
- **Status:** ✅ Complete

### Loki
- **Config:** `loki/loki.yml`
- **Schema:** TSDB v13
- **Retention:** 720h (30 days) via compactor
- **Ingestion:** 10 MB/s (burst 20 MB/s), max 10,000 streams
- **Ports:** 3100 (HTTP), 9096 (gRPC)
- **Status:** ✅ Complete

### Tempo
- **Config:** `tempo/tempo.yml`
- **Format:** vParquet4 (TraceQL optimised)
- **Retention:** 48 hours
- **Receivers:** OTLP gRPC (4317), OTLP HTTP (4318)
- **Span Metrics:** → Mimir (service graphs, latency histograms)
- **Status:** ✅ Complete

### Alertmanager
- **Config:** `alertmanager/alertmanager.yml`
- **Routing:** Two-tier (ops-email: warnings, critical-email: critical)
- **SMTP:** Gmail 465 SSL (configured via env vars)
- **Status:** ✅ Complete

### Pyroscope
- **Config:** `pyroscope/pyroscope.yml`
- **Port:** 4040
- **Purpose:** Continuous CPU/memory profiling linked from Tempo traces
- **Status:** ✅ Complete

---

## 5. Grafana Dashboards — Complete Inventory

| Folder | Dashboard | Panels | Datasources | UID | Status |
|--------|-----------|--------|-------------|-----|--------|
| Developer | Developer Observability | 33 | Prometheus, Loki, Tempo | `developer-observability-v1` | ✅ |
| Four Golden Signals | Four Golden Signals (SRE) | 61 | Prometheus, Mimir, Tempo, Pyroscope | `gatewayz-four-golden-signals` | ✅ |
| Infrastructure | Infrastructure Health | 22 | Prometheus | `gatewayz-infra-health` | ✅ |
| Loki | Error-Level Logs | 13 | Loki, Prometheus | `gatewayz-error-analysis` | ✅ |
| Loki | Security & Rate Limiter Logs | 10 | Loki | `gatewayz-security-ratelimit` | ✅ |
| Loki | Live GatewayZ Logs | 9 | Loki | `gatewayz-logs-loki-v1` | ✅ |
| Model Performance | Cache Layer Profile | 7 | Pyroscope | `gatewayz-cache-layer-profile` | ✅ |
| Model Performance | Inference Call Profile | 23 | Prometheus, Mimir, Tempo, Pyroscope | `gatewayz-inference-call-profile` | ✅ |
| Model Performance | Model Usage | 32 | Prometheus, Tempo | `gatewayz-model-usage` | ✅ |
| Model Performance | Request Type Queries | 6 | Prometheus, Tempo | `gatewayz-request-analysis` | ✅ |
| Model Performance | Tiered Model Analysis | 22 | Prometheus | `gatewayz-tiered-model-analysis` | ✅ |
| Prometheus | Reliability (Sentry Replacement) | 33 | Prometheus, Loki | `gatewayz_reliability_v1` | ✅ |
| Provider Directory | Provider Directory | 100+ | Prometheus | — | ✅ |
| Streaming | Streaming Performance | ~15 | Prometheus | — | ✅ |
| Tempo | Distributed Tracing | ~10 | Tempo | — | ✅ |
| **System Quality** | **System Quality Pillars** | **~50** | **Prometheus, Loki** | `gatewayz-system-quality-pillars` | 🔄 **In progress** |

**Total panels across all dashboards: 400+**

---

## 6. Alert Rules — Complete Inventory

### Prometheus-Managed (alert.rules.yml) — 16 Rules

| Group | Alert | Severity | Condition |
|-------|-------|----------|-----------|
| Service Health | GatewayZAPIDown | CRITICAL | `up{job="gatewayz_production"} == 0` for 2m |
| Service Health | ErrorBudgetWarning | WARNING | 5xx rate > 0.5% for 5m |
| Service Health | HighErrorRate | CRITICAL | 5xx rate > 5% for 5m |
| Service Health | AvailabilitySLOBreach | CRITICAL | Success rate < 99.5% for 10m |
| API Performance | HighAPILatency | WARNING | P95 > 3s for 5m |
| API Performance | LatencyDegradation | WARNING | P95 increased 50%+ over 1h |
| API Performance | TrafficSpike | WARNING | 3× normal for 10m |
| Provider Health | ProviderHighErrorRate | CRITICAL | Per-provider error > 20% for 5m |
| Provider Health | SlowProviderResponse | WARNING | Per-provider P95 > 5s for 10m |
| Provider Health | LowModelHealthScore | CRITICAL | Success rate < 80% for 5m |
| Saturation/Security | RateLimitSaturation | WARNING | 429 rate > 10% for 5m |
| Saturation/Security | AuthFailureSpike | WARNING | 401/403 rate > 3× baseline for 10m |
| Infrastructure | ScrapeTargetDown | WARNING | `up{job!=prometheus} == 0` for 5m |
| Infrastructure | MimirRemoteWriteFailures | WARNING | Failed samples > 0 for 5m |
| Infrastructure | MimirDown | CRITICAL | Mimir `up == 0` for 2m |
| Infrastructure | TempoNoTraces / LokiNoLogs | WARNING | No data for 15m |

### Grafana-Managed (provisioning/alerting/rules/) — 40+ Rules

| File | Rules | Key Coverage |
|------|-------|-------------|
| `availability_anomalies.yml` | 5 | Provider < 90%, circuit breaker open, multi-provider degraded |
| `backend_alerts.yml` | 4 | Health score, error rate, circuit breakers |
| `error_rate_anomalies.yml` | 3 | Error rate > 10% (critical), > 5% (warning), 5xx > 5% |
| `general_alerts.yml` | 4 | Provider critical, cost anomaly, budget > $50k |
| `latency_anomalies.yml` | 4 | P95 > 5s (critical), > 2s (warning), TTFC > 3s |
| `logs_alerts.yml` | 4 | Critical errors > 10, error spike, latency degradation |
| `model_alerts.yml` | 4 | Model health, error rate, latency, availability |
| `redis_alerts.yml` | 5 | Redis down, memory > 80/90%, cache hit < 50% |
| `slo_burn_rate_alerts.yml` | 4 | Fast burn > 14.4×, slow burn > 6×, latency SLO |
| `traffic_anomalies.yml` | 3 | Spike 3× (critical), 2× (warning), drop 50% |

### Alertmanager Routing

```
All Alerts
├─ severity=critical ──────────────► critical-email (0s wait, 2m interval)
│   ├─ component=slo + critical ──► critical-email (0s wait, 5m interval)
│   ├─ traffic_spike ─────────────► critical-email (10s wait)
│   ├─ error_rate_spike ──────────► critical-email (0s wait)
│   ├─ circuit_breaker ───────────► critical-email (0s wait)
│   └─ availability_drop ─────────► critical-email (0s wait)
├─ component=slo + warning ───────► ops-email (5m wait, 1h repeat)
└─ model errors, infrastructure ──► ops-email (5m wait)
```

---

## 7. Datasources Configured

| Name | Type | UID | Purpose |
|------|------|-----|---------|
| Prometheus | prometheus | `grafana_prometheus` | Real-time metrics |
| Mimir | prometheus (Mimir) | `grafana_mimir` | Long-term metrics + span metrics |
| Loki | loki | `grafana_loki` | Log aggregation |
| Tempo | tempo | `grafana_tempo` | Distributed traces |
| Pyroscope | pyroscope | `grafana_pyroscope` | CPU/memory flamegraphs |
| Alertmanager | alertmanager | `alertmanager` | Alert state visibility |
| JSON API | simplejson | `grafana_json_api` | Custom GatewayZ API data |

**Trace → Log linking:** Loki derived field extracts `trace_id` → links to Tempo
**Trace → Profile linking:** Tempo → Pyroscope via `resource.service.name`
**Span Metrics:** Tempo → remote write → Mimir (NOT Prometheus)

---

## 8. Prometheus Scrape Jobs

| Job | Target | Interval | What It Scrapes |
|-----|--------|----------|-----------------|
| `prometheus` | localhost:9090 | 15s | Prometheus self-metrics |
| `gatewayz_production` | `$FASTAPI_TARGET` | 15s | **FastAPI metrics** — PRIMARY |
| `health_service_exporter` | health-service-exporter:8002 | 30s | Health check metrics |
| `gatewayz_data_metrics_production` | `$FASTAPI_TARGET/prometheus/data/metrics` | 30s | Provider health, circuit breakers |
| `mimir` | mimir:9009 | 30s | Mimir self-monitoring |
| `tempo` | tempo:3200 | 15s | Span metrics from Tempo |

> ⚠️ **`$FASTAPI_TARGET` must be set** — without it, Prometheus has no backend metrics to scrape.

---

## 9. Recording Rules Summary

32 pre-computed rules across 6 groups (in `prometheus/recording_rules_baselines.yml`):

| Group | Rules | What They Compute |
|-------|-------|-------------------|
| `traffic_baselines` | 5 | Request rates: 5m, 1h, 24h, 7d + by endpoint |
| `error_rate_baselines` | 6 | Error %: 4xx, 5xx, by endpoint, 1h/24h avg |
| `latency_baselines` | 7 | P50/P95/P99: current, 1h avg, 24h avg, by endpoint |
| `availability_baselines` | 4 | Availability %: per provider, per model, per gateway, system |
| `cost_baselines` | 3 | Daily cost: current, 7d avg, by provider |
| `resource_baselines` | 5 | CPU %, Memory %, Disk % |

---

## 10. Environment Variables Required

| Variable | Used By | Required | Description |
|----------|---------|----------|-------------|
| `FASTAPI_TARGET` | Prometheus | **YES** | Backend `/metrics` URL (e.g. `https://api.gatewayz.ai`) |
| `ALERTMANAGER_TARGET` | Prometheus | YES | Alertmanager URL |
| `SMTP_FROM` | Alertmanager | YES | Alert sender email |
| `SMTP_USER` | Alertmanager | YES | Gmail SMTP username |
| `SMTP_PASSWORD` | Alertmanager | YES | Gmail SMTP password / app password |
| `ALERT_EMAIL_OPS` | Alertmanager | YES | Ops team recipient email |
| `ALERT_EMAIL_CRIT` | Alertmanager | YES | Critical/on-call recipient email |
| `GF_SECURITY_ADMIN_PASSWORD` | Grafana | YES | Grafana admin login |
| `MIMIR_REMOTE_WRITE_URL` | Tempo | YES | Mimir push endpoint for span metrics |
| `GATEWAYZ_API_URL` | JSON-API-Proxy | YES | `https://api.gatewayz.ai` |

---

## 11. Eight System Quality Pillars — Coverage Analysis

| Pillar | Primary Existing Dashboard | Coverage | Key Gap |
|--------|---------------------------|----------|---------|
| 🛡️ Reliability | Four Golden Signals, Reliability (sentry-replacement) | **Strong** | No unified MTTR/MTBF stat |
| ⚡ Performance | Inference Call Profile, Streaming Performance | **Strong** | CPU/memory in separate dashboard |
| 📈 Scalability | Cache Layer Profile, Tiered Model Analysis | **Moderate** | No single scalability view |
| ✅ Availability | Four Golden Signals (SLO row), Reliability | **Strong** | SLO compliance % not a single-glance stat |
| 🔭 Observability | Developer Observability, all Loki dashboards, Tempo | **Strong** | Exception breakdown pie chart missing |
| 🔄 Fault Tolerance | Infrastructure Health (circuit breakers), Four Golden Signals | **Moderate** | No streaming failure stat |
| 🔒 Security | Security & Rate Limiter Logs | **Moderate** | No auth failure rate stat |
| 🔧 Maintainability | Infrastructure Health (Redis), Reliability | **Moderate** | No process uptime stat, no cost trend |

**Solution:** `System-Reliability-Dashboard.json` (TASK-2 through TASK-10) — one unified dashboard with a row per pillar.

---

## 12. Kanban — What Is Done vs In Progress vs Todo

### ✅ Done (Pre-existing — completed before this Kanban was created)
- All 15 Grafana dashboards (400+ panels, 100% populated)
- All 7 datasources provisioned
- 16 Prometheus alert rules
- 40+ Grafana alert rules (10 YAML files)
- 32 Prometheus recording rules
- Alertmanager two-tier email routing
- Full Docker Compose stack (8 services with healthchecks, resource limits, security hardening)
- Mimir long-term storage integration
- Railway deployment configs (`railway.toml`) for all services
- 48 documentation files
- Prometheus remote write to Mimir
- Tempo span metrics → Mimir pipeline
- Trace→Log→Profile linking in Grafana

### ✅ Done (This Session)
- TASK-1: `dashboards.yml` updated with System Quality provisioner
- `reliability/` folder created

### 🔄 In Progress
- TASK-2: `System-Reliability-Dashboard.json` — scaffolding phase

### 📋 Ready (8 Pillar Rows for System Quality Dashboard)
- TASK-3: 🛡️ Reliability row (IDs 100–107)
- TASK-4: ⚡ Performance row (IDs 200–209)
- TASK-5: 📈 Scalability row (IDs 300–308)
- TASK-6: ✅ Availability row (IDs 400–405)
- TASK-7: 🔭 Observability row (IDs 500–507)
- TASK-8: 🔄 Fault Tolerance row (IDs 600–607)
- TASK-9: 🔒 Security row (IDs 700–707)
- TASK-10: 🔧 Maintainability row (IDs 800–808)

---

## 13. Outstanding Gaps & Known Issues

| ID | Gap | Priority | Notes |
|----|-----|----------|-------|
| BACKEND-1 | `FASTAPI_TARGET` not verified in Railway | **HIGH** | Without this, zero backend metrics flow |
| BACKEND-2 | OTLP trace export from backend to Tempo unverified | **HIGH** | Traces dashboard empty without this |
| BACKEND-3 | Loki log labels — confirm `app="gatewayz"` matches Railway output | **MEDIUM** | Log dashboards may show no data |
| INFRA-1 | Redis exporter reliability — noted as unreliable in docs | **MEDIUM** | Redis alert rules may have no data |
| INFRA-2 | Mimir using filesystem storage | **LOW** | S3/GCS recommended for production HA |
| TASK-2 | System-Reliability-Dashboard.json JSON not yet written | **ACTIVE** | In progress this session |

---

## 14. Documentation Navigation Guide

| Goal | Read This |
|------|-----------|
| Get started fast | `docs/deployment/QUICKSTART.md` |
| Deploy to Railway | `docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md` |
| Understand architecture | `docs/architecture/MIMIR.md`, `docs/architecture/RAILWAY_MIMIR_DEPLOYMENT.md` |
| Add a new dashboard | `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md` → "Adding a Dashboard" |
| Add alert rules | `docs/deployment/ALERTING_SETUP.md` |
| Connect backend | `docs/backend/COMPLETE_BACKEND_INTEGRATION_GUIDE.md` |
| Troubleshoot Loki | `docs/troubleshooting/LOKI_FIX_GUIDE.md` |
| Troubleshoot Tempo | `docs/troubleshooting/TEMPO_INTEGRATION.md` |
| Troubleshoot Mimir remote write | `docs/troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md` |
| Understand all metrics | `docs/backend/BACKEND_METRICS_REQUIREMENTS.md` |
| Full doc index | `docs/docs-index.md` |
| Agent guidelines | `docs/development/CLAUDE.md` |
| Future dev rules | `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md` |

---

## 15. Key Metrics Reference

### HTTP / API
| Metric | Type | Labels | Use |
|--------|------|--------|-----|
| `fastapi_requests_total` | Counter | `method`, `path`, `status_code`, `status_class` | Traffic, error rate |
| `fastapi_requests_duration_seconds` | Histogram | `method`, `path` | Latency P50/P95/P99 |
| `fastapi_requests_in_progress` | Gauge | `method`, `path` | Active concurrency |
| `fastapi_exceptions_total` | Counter | `exception_type` | Exception breakdown |
| `fastapi_request_size_bytes` | Histogram | `method`, `path` | Request size anomalies |
| `fastapi_response_size_bytes` | Histogram | `method`, `path` | Response size |

### Model Inference
| Metric | Type | Labels | Use |
|--------|------|--------|-----|
| `model_inference_requests_total` | Counter | `provider`, `model`, `status` | Inference traffic + errors |
| `model_inference_duration_seconds` | Histogram | `provider`, `model` | Inference latency |
| `tokens_used_total` | Counter | `provider`, `model`, `token_type` | Token throughput |
| `time_to_first_chunk_seconds` | Histogram | `provider`, `model` | Streaming TTFC |

### Cost & Billing
| Metric | Type | Labels | Use |
|--------|------|--------|-----|
| `gatewayz_api_cost_usd_total` | Counter | `provider`, `model` | Cumulative spend |
| `gatewayz_credit_deduction_total` | Counter | `status`, `endpoint` | Billing reliability |
| `gatewayz_credit_refunds_total` | Counter | `reason` | Refund rate |
| `gatewayz_cache_cost_savings_usd_total` | Counter | `provider`, `model`, `cache_type` | Cache ROI |

### Cache & Infrastructure
| Metric | Type | Labels | Use |
|--------|------|--------|-----|
| `catalog_cache_hits_total` | Counter | `gateway` | Cache hit ratio |
| `catalog_cache_misses_total` | Counter | `gateway` | Cache miss ratio |
| `gatewayz_pricing_cache_hits_total` | Counter | `cache_name` | Pricing cache |
| `redis_memory_used_bytes` | Gauge | — | Redis memory |
| `redis_memory_max_bytes` | Gauge | — | Redis capacity |
| `read_replica_queries_total` | Counter | `table`, `status` | DB routing health |

### Process (auto-exported by Prometheus client)
| Metric | Use |
|--------|-----|
| `process_cpu_seconds_total` | CPU usage rate |
| `process_resident_memory_bytes` | Memory RSS |
| `process_start_time_seconds` | Uptime (`time() - value`) |

---

---

## 16. Backend Telemetry Architecture — Deep Reference

> This section maps how `gatewayz-backend` generates, ships, and exposes observability data. Read this before modifying dashboards, alert queries, or adding new metrics. Every panel in this stack ultimately depends on what the backend emits.

### 16.1 Conceptual Data Flow (Backend Internal)

```
gatewayz-backend (FastAPI, Railway)
  │
  ├── ObservabilityMiddleware (ASGI)
  │     Wraps every HTTP request:
  │     ├── Records: fastapi_requests_total, fastapi_requests_duration_seconds
  │     ├── Records: fastapi_requests_in_progress, fastapi_exceptions_total
  │     ├── Correlates Pyroscope profiling labels (endpoint, method)
  │     └── Attaches exemplars (trace_id → Tempo linkage)
  │
  ├── TraceContextMiddleware (ASGI)
  │     Injects x-trace-id, x-span-id response headers
  │     Enriches structlog context with OTel trace/span IDs
  │
  ├── SecurityMiddleware (ASGI — Layer 1 rate limiting)
  │     Velocity Mode: if error_rate > 25% in 1 min → reduce rate limits 50% for 3 min
  │     Metric: velocity_mode_activations_total
  │
  ├── OpenTelemetry SDK (opentelemetry_config.py)
  │     Service: gatewayz-api
  │     Auto-instruments: FastAPI routes, HTTPX (AI provider calls), Redis
  │     Processor: ResilientSpanProcessor (circuit breaker, 5 fail → OPEN, 60s cooldown)
  │     └── OTLP HTTP export ──────────────────────► Tempo :4318
  │
  ├── OpenLLMetry / Traceloop (traceloop_config.py)
  │     LLM SDK tracing with gen_ai.* semantic conventions
  │     Associates spans with customer.id for user-level trace filtering
  │     └── OTLP HTTP export ──────────────────────► Tempo :4318
  │
  ├── Structured Logging (logging_config.py)
  │     Format: JSON with trace_id, span_id, level, service, app labels
  │     Async queue → non-blocking Loki push ───────► Loki :3100
  │     Labels: app="gatewayz", level, service
  │
  ├── PrometheusRemoteWriter (prometheus_remote_write.py)
  │     Protobuf + Snappy compression
  │     Circuit breaker: 5 failures → OPEN, 5 min cooldown
  │     └── Remote write ──────────────────────────► Mimir (direct, bypasses Prometheus)
  │
  ├── /metrics endpoint (grafana_metrics.py + prometheus_metrics.py)
  │     Exposes all Prometheus metrics in text format
  │     └── Scraped by Prometheus every 15s ────────► Prometheus → Mimir
  │
  └── /prometheus/data/metrics endpoint (prometheus_data.py)
        Provider health scores, circuit breaker states, error rates
        └── Scraped by Prometheus every 30s ─────────► JSON-API-Proxy → Grafana
```

### 16.2 All Backend-Emitted Prometheus Metrics

#### HTTP / Request Layer
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `fastapi_requests_total` | Counter | `method`, `path`, `status_code`, `status_class` | Every HTTP request; denominator for error rate |
| `fastapi_requests_duration_seconds` | Histogram | `method`, `path` | Request latency; use for P50/P95/P99 |
| `fastapi_requests_in_progress` | Gauge | `method`, `path` | Active concurrent requests |
| `fastapi_exceptions_total` | Counter | `exception_type` | Unhandled exceptions by type |
| `fastapi_request_size_bytes` | Histogram | `method`, `path` | Incoming request payload size |
| `fastapi_response_size_bytes` | Histogram | `method`, `path` | Outgoing response size |

**Path normalization:** Dynamic segments are normalized → `{id}` (e.g. `/v1/chat/completions/abc123` → `/v1/chat/completions/{id}`) to prevent label cardinality explosion.

#### Model Inference Layer
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `model_inference_requests_total` | Counter | `provider`, `model`, `status` | Per-model traffic + error tracking |
| `model_inference_duration_seconds` | Histogram | `provider`, `model` | End-to-end AI provider latency |
| `tokens_used_total` | Counter | `provider`, `model`, `token_type` | Token consumption (prompt / completion) |
| `time_to_first_chunk_seconds` | Histogram | `provider`, `model` | Streaming time-to-first-token |

#### Cost & Billing
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gatewayz_api_cost_usd_total` | Counter | `provider`, `model` | Cumulative USD spend |
| `gatewayz_credit_deduction_total` | Counter | `status`, `endpoint` | Credit deductions (success/failure rate) |
| `gatewayz_credit_refunds_total` | Counter | `reason` | Refund events |
| `gatewayz_cache_cost_savings_usd_total` | Counter | `provider`, `model`, `cache_type` | Cache ROI in USD |

#### Provider Health (exposed via /prometheus/data/metrics)
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `provider_health_score` | Gauge | `provider` | 0–100 health score per AI provider |
| `provider_circuit_breaker_state` | Gauge | `provider` | 0=CLOSED, 1=OPEN, 2=HALF_OPEN |
| `provider_error_rate` | Gauge | `provider` | Current error rate per provider (0–1) |
| `provider_availability` | Gauge | `provider` | Availability % per provider |

#### Cache & Infrastructure
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `catalog_cache_hits_total` | Counter | `gateway` | Cache hit events |
| `catalog_cache_misses_total` | Counter | `gateway` | Cache miss events |
| `gatewayz_pricing_cache_hits_total` | Counter | `cache_name` | Pricing tier cache hits |
| `redis_memory_used_bytes` | Gauge | — | Redis memory usage |
| `redis_memory_max_bytes` | Gauge | — | Redis max memory capacity |
| `read_replica_queries_total` | Counter | `table`, `status` | PostgreSQL read replica query routing |

#### Security / Velocity Mode
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `velocity_mode_activations_total` | Counter | — | Times velocity mode was triggered |
| `rate_limit_rejections_total` | Counter | `endpoint`, `limit_type` | Layer-1 rate limit rejections |

#### Internal Observability Pipeline Health
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `loki_log_queue_size` | Gauge | — | Async Loki push queue depth |
| `prometheus_remote_write_total` | Counter | `status` | Remote write success/failure count |
| `otel_export_circuit_breaker_state` | Gauge | — | OTEL exporter circuit breaker (0/1/2) |

### 16.3 OpenTelemetry (Traces) Configuration

```python
# Service identity (resource attributes)
service.name          = "gatewayz-api"
deployment.environment = os.getenv("ENVIRONMENT", "production")
service.version       = os.getenv("SERVICE_VERSION", "1.0.0")

# Export endpoint
TEMPO_OTLP_HTTP_ENDPOINT = os.getenv("TEMPO_OTLP_HTTP_ENDPOINT")
# Example: "http://tempo:4318/v1/traces"

# Auto-instrumented libraries
- FastAPI (all routes, request/response attributes)
- HTTPX (all outbound AI provider HTTP calls)
- Redis (all cache operations)
- SQLAlchemy (if enabled)

# LLM-specific (via OpenLLMetry/Traceloop)
- gen_ai.system          (openai / anthropic / etc.)
- gen_ai.request.model   (model name)
- gen_ai.usage.prompt_tokens
- gen_ai.usage.completion_tokens
- ai.cost.usd            (cost per call)
- customer.id            (user association for per-user trace filtering)
```

**ResilientSpanProcessor** (`utils/resilient_span_processor.py`):
```
State machine: CLOSED → OPEN → HALF_OPEN → CLOSED
CLOSED:    All spans exported normally
OPEN:      Export failures exceed threshold (5) → exports dropped for 60s
HALF_OPEN: After 60s cooldown, try export — if 2 successes → CLOSED, else → OPEN
```

### 16.4 Loki Structured Log Format

Every log line from `gatewayz-backend` is JSON with this schema:

```json
{
  "timestamp": "2026-03-08T12:34:56.789Z",
  "level": "INFO",
  "service": "gatewayz",
  "message": "Inference request completed",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "endpoint": "/v1/chat/completions",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 1243,
  "user_id": "usr_abc123",
  "model": "gpt-4o",
  "provider": "openai",
  "tokens_prompt": 512,
  "tokens_completion": 128,
  "cost_usd": 0.0024
}
```

**Loki stream labels** (low cardinality — used for indexing):
- `app="gatewayz"` — primary filter for all GatewayZ log queries
- `level` — log level (INFO / WARNING / ERROR / CRITICAL)
- `service` — service name

**Loki JSON fields** (high cardinality — searchable via LogQL `| json`):
- `trace_id`, `span_id` — enables Log→Trace correlation in Grafana
- `endpoint`, `model`, `provider`, `user_id`, `status_code`

**Dashboard dependency:** All Loki dashboards filter with `{app="gatewayz"}`. If the backend is not setting this label, log panels show no data. Verify via BACKEND-3.

### 16.5 Health Monitoring Architecture

**IntelligentHealthMonitor** (`services/intelligent_health_monitor.py`):

| Tier | Traffic Share | Check Interval | Providers |
|------|-------------|---------------|-----------|
| Tier 1 | Top 5% traffic | Every 5 min | ~2–3 providers |
| Tier 2 | Frequent use | Every 15 min | ~5–8 providers |
| Tier 3 | Occasional use | Every 30 min | ~10–15 providers |
| Tier 4 | On-demand only | Only when called | remaining ~10 |

**Provider Circuit Breaker** (state tracked per provider):
```
CLOSED (normal)
  │ failure_count > threshold (default: 5)
  ▼
OPEN (blocking calls)
  │ cooldown elapsed (default: 60s)
  ▼
HALF_OPEN (test with 1 call)
  │ success ──► CLOSED
  └ failure ──► OPEN (reset timer)
```
Exposed as `provider_circuit_breaker_state{provider="openai"}` = 0/1/2

**AutonomousMonitor** (`services/autonomous_monitor.py`):
- Reads error patterns from Loki (LogQL queries)
- AI-powered root cause analysis
- Can generate auto-fix PRs for known error patterns

### 16.6 Velocity Mode (Security Circuit Breaker)

**Trigger:** Error rate > 25% in any 1-minute window
**Effect:** Rate limits reduced by 50% for 3 minutes
**Recovery:** Automatic after 3-minute window expires
**Metric:** `velocity_mode_activations_total` — spikes here indicate a security event or provider cascade failure

### 16.7 Backend Environment Variables for Observability

| Variable | Where Used | Description |
|----------|-----------|-------------|
| `TEMPO_OTLP_HTTP_ENDPOINT` | `opentelemetry_config.py` | Tempo OTLP HTTP ingest URL (e.g. `http://tempo:4318`) |
| `LOKI_URL` | `logging_config.py` | Loki push API URL (e.g. `http://loki:3100`) |
| `PROMETHEUS_REMOTE_WRITE_URL` | `prometheus_remote_write.py` | Mimir push URL (optional — Prometheus also scrapes) |
| `ENVIRONMENT` | OTEL resource attrs | Sets `deployment.environment` span attribute |
| `SERVICE_VERSION` | OTEL resource attrs | Sets `service.version` span attribute |
| `SENTRY_DSN` | Error tracking | Sentry error reporting (separate from Loki) |
| `ARIZE_API_KEY` | ML observability | Arize AI model monitoring (separate pipeline) |
| `REDIS_URL` | Redis client | Required for cache metrics |

### 16.8 Dashboard → Backend Metric Mapping

| Dashboard | Primary Metrics Used | Backend Source |
|-----------|---------------------|----------------|
| Four Golden Signals | `fastapi_requests_total`, `fastapi_requests_duration_seconds` | ObservabilityMiddleware |
| Inference Call Profile | `model_inference_requests_total`, `model_inference_duration_seconds`, `tokens_used_total` | prometheus_metrics.py |
| Model Usage | `tokens_used_total`, `gatewayz_api_cost_usd_total`, `model_inference_requests_total` | prometheus_metrics.py |
| Streaming Performance | `time_to_first_chunk_seconds`, `fastapi_requests_duration_seconds` | prometheus_metrics.py |
| Security & Rate Limiter Logs | `{app="gatewayz", level="WARNING"}` LogQL | logging_config.py → Loki |
| Error-Level Logs | `{app="gatewayz"} \| json \| level="ERROR"` | logging_config.py → Loki |
| Distributed Tracing | `service.name="gatewayz-api"` TraceQL | opentelemetry_config.py → Tempo |
| Cache Layer Profile | `catalog_cache_hits_total`, `gatewayz_pricing_cache_hits_total` | prometheus_metrics.py |
| Infrastructure Health | `provider_health_score`, `provider_circuit_breaker_state` | prometheus_data.py |
| Reliability (Sentry Replacement) | `fastapi_requests_total`, `fastapi_exceptions_total`, Loki errors | Mixed |
| Developer Observability | All of the above + Tempo service graphs + Pyroscope flamegraphs | Full stack |

---

*This document is auto-generated from a full codebase audit. Update it whenever major changes land.*
*See `CLAUDE.md` for agent quick-reference and critical rules.*
*See `ACCEPTANCE_CRITERIA.md` for acceptance criteria on every Kanban task.*
