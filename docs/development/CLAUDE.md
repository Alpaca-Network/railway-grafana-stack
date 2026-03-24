# CLAUDE.md — Full Agent Guidelines

**Project:** GatewayZ Railway Grafana Stack
**Purpose:** Monitoring and observability for GatewayZ AI Inference Gateway (30+ AI providers)
**Primary Deployment:** Railway (Production) — [logs.gatewayz.ai](https://logs.gatewayz.ai)
**Last Updated:** March 2026

> This is the full agent guidelines file. For a quick-reference version, see the root `CLAUDE.md`.

---

## ⚠️ CRITICAL RULES — READ FIRST

| Rule | Why |
|------|-----|
| **NEVER hardcode `FASTAPI_TARGET`** | Substituted at runtime by `entrypoint.sh` — hardcoding breaks Railway |
| **NEVER change `schemaVersion`** | Must stay at 39 for Railway Grafana 11.5.2 compatibility |
| **NEVER modify datasource UIDs** | `grafana_prometheus`, `grafana_mimir`, `grafana_loki`, `grafana_tempo`, `grafana_pyroscope` — 14 dashboards depend on these |
| **NEVER delete recording rules** | Anomaly detection alerts depend on baseline pre-computations in `recording_rules_baselines.yml` |
| **NEVER change Mimir `X-Scope-OrgID`** | Must be `anonymous` — multitenancy is disabled |
| **NEVER add services to `docker-compose.yml` without updating `railway.toml`** | Railway won't deploy new services |
| **NEVER modify `provisioning/datasources/` without testing** | Breaking a UID breaks every panel using that datasource |

**Architecture is LOCKED** — See `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md`. No new backends, no new trace/log stores.

---

## Current Project State (March 2026)

```
✅ Core Stack (8 services)
  Prometheus · Mimir · Grafana · Loki · Tempo · Alertmanager · Pyroscope · JSON-API-Proxy

✅ Observability Coverage
  - 14 dashboard JSON files (13 complete + System-Reliability-Dashboard in progress)
  - 8 Grafana folders (provisioned via dashboards.yml)
  - 7 datasources provisioned and cross-linked
  - 16 Prometheus alert rules (alert.rules.yml)
  - 32 recording rules (recording_rules_baselines.yml)
  - 46 Grafana alert rules across 11 YAML files
  - Alertmanager two-tier routing (ops-email + critical-email)

✅ March 2026 — Dashboard Restructure
  - 17 dashboards → 13 complete; 11 folders → 8 folders
  - Deprecated: Developer Observability, Sentry Overview, Tiered Model Analysis
  - Folders renamed to self-describing names
  - All dashboards now have uniform intro panels + cross-navigation links

✅ March 2026 — Tempo 2.6.1 Optimization
  - local_blocks processor: TraceQL metrics queries without Mimir (panels 701–703)
  - Histogram buckets extended to 120s for large-model LLM calls
  - Phase 2 span_metrics dimensions: finish_reason, http.route, error.type, span.kind, db.system
  - filter_policies: excludes health/metrics/probe spans
  - peer_attributes: external APIs (OpenAI, Anthropic) visible in service topology
  - 6 new trace alert rules in trace_alerts.yml

⚠️ Outstanding Gaps
  - BACKEND-1: Verify FASTAPI_TARGET env var in Railway
  - BACKEND-2: Verify OTLP traces from backend → Tempo  ← SERVICE MAP SHOWS NO DATA UNTIL DONE
  - BACKEND-3: Verify Loki log labels match app="gatewayz"
  - INFRA-1: Validate Redis exporter reliability
  - INFRA-2: Migrate Mimir storage from filesystem → S3
```

---

## Project Structure

```
railway-grafana-stack/
├── CLAUDE.md                              ← Quick reference (read first)
├── MASTER.md                              ← Full project wiki
├── ACCEPTANCE_CRITERIA.md                 ← Kanban card acceptance criteria
├── docker-compose.yml                     ← Local service orchestration
├── railway.toml                           ← Railway deployment config
├── prometheus/
│   ├── prometheus.yml                     ← Scrape targets + remote_write to Mimir
│   ├── alert.rules.yml                    ← 16 Prometheus alert rules
│   └── recording_rules_baselines.yml      ← 32 baseline recording rules
├── grafana/
│   ├── Dockerfile                         ← COPY commands for all dashboard dirs
│   ├── dashboards/
│   │   ├── golden-signals/                ← Four-Golden-Signals.json (reference layout)
│   │   ├── infrastructure/                ← Infrastructure-Health.json
│   │   ├── loki/                          ← 4 Loki dashboards
│   │   ├── model_performance/             ← 4 model analytics dashboards
│   │   ├── provider/                      ← Provider-Directory.json
│   │   ├── reliability/                   ← System-Reliability-Dashboard.json (in progress)
│   │   ├── streaming/                     ← Streaming-Performance.json
│   │   └── tempo/                         ← tempo.json (Distributed Tracing)
│   └── provisioning/
│       ├── dashboards/dashboards.yml      ← 8-folder registration
│       ├── datasources/                   ← 7 datasource YAMLs
│       └── alerting/
│           ├── rules/                     ← 11 YAML files, 46 rules total
│           │   ├── trace_alerts.yml       ← 6 trace-based rules (March 2026)
│           │   └── ...                    ← 10 other alert rule files
│           └── notification_policies.yml  ← Routing: ops-email + critical-email
├── mimir/mimir.yml                        ← Long-term metrics (30d retention)
├── loki/loki.yml                          ← Log aggregation
├── tempo/tempo.yml                        ← Trace storage + span metrics (Tempo 2.6.1)
├── alertmanager/alertmanager.yml          ← Alert routing configuration
├── scripts/
│   ├── validate_dashboards.sh             ← Validate all dashboard JSON
│   ├── verify_metrics.sh                  ← Verify metrics pipeline
│   └── cleanup_deprecated_grafana_folders.sh ← Delete Developer/Prometheus/Sentry DB folders
└── docs/
    ├── development/CLAUDE.md              ← This file
    ├── development/FUTURE_DEVELOPMENT_GUIDELINES.md ← Architecture constraints
    ├── docs-index.md                      ← Full documentation index
    └── ...                                ← 40+ other docs
```

---

## Datasource UIDs (DO NOT CHANGE)

| UID | Name | Type | Purpose |
|-----|------|------|---------|
| `grafana_prometheus` | Prometheus | prometheus | Live scrape metrics (15s intervals) |
| `grafana_mimir` | Mimir | prometheus | Long-term metrics (30d) + span metrics from Tempo |
| `grafana_loki` | Loki | loki | Application logs from gatewayz-backend |
| `grafana_tempo` | Tempo | tempo | Distributed traces, TraceQL, service topology |
| `grafana_pyroscope` | Pyroscope | pyroscope | Continuous CPU/memory profiling |
| `grafana_json_api` | JSON API | JSON API | External JSON endpoints |
| `alertmanager` | Alertmanager | alertmanager | Alert state and silences |

**Critical:** `traces_spanmetrics_*` and `traces_service_graph_*` metrics are remote-written by Tempo's `metrics_generator` **directly to Mimir** — NOT scraped by Prometheus. Any panel querying these metrics MUST use `grafana_mimir`, not `grafana_prometheus`.

---

## Dashboard Inventory (March 2026)

| Folder | Dashboard | UID |
|--------|-----------|-----|
| Four Golden Signals | Four-Golden-Signals.json | `gatewayz-four-golden-signals` |
| Infrastructure & Caching | Infrastructure-Health.json | `gatewayz-infrastructure` |
| Application Log Streams | GatewayZ-Error-Level Logs.json | — |
| Application Log Streams | GatewayZ-Log-Metrics.json | — |
| Application Log Streams | GatewayZ-Security-&Rate-Limiter-Log.json | — |
| Application Log Streams | Live-GatewayZ-Logs.json | — |
| AI Model Analytics | Cache-Layer-Profile.json | — |
| AI Model Analytics | Inference-Call-Profile.json | — |
| AI Model Analytics | Model-Usage.json | — |
| AI Model Analytics | Request-Type-Queries.json | — |
| AI Provider Intelligence | Provider-Directory.json | — |
| LLM Streaming Performance | Streaming-Performance.json | — |
| Distributed Tracing | tempo.json | `gatewayz-distributed-tracing` |
| Platform Quality Pillars | System-Reliability-Dashboard.json | `gatewayz-system-quality-pillars` |

**Layout standard:** All dashboards follow the Four Golden Signals pattern:
- `"links"` dropdown (tag: `gatewayz`) for cross-navigation
- Transparent intro text panel (h=6, top) with: purpose, key signals table, datasources, navigation hints
- Row headers: `[emoji]  Category — Subtitle · Subtitle`

---

## Alert Rules Inventory

### Prometheus Alert Rules (16 rules — `prometheus/alert.rules.yml`)

Groups: `performance_alerts`, `performance_trends`, `model_health_alerts`, `redis_alerts`, `infrastructure_alerts`, `rate_limiter_alerts`

### Grafana Alert Rules (46 rules — `grafana/provisioning/alerting/rules/`)

| File | Rules | Notes |
|------|-------|-------|
| `slo_burn_rate_alerts.yml` | ~8 | SLO error budget burn rate |
| `trace_alerts.yml` | 6 | Trace-based: error rate, P95 latency, dark provider, truncation, route errors, content filter |
| `redis_alerts.yml` | ~4 | Redis memory, hit rate, connection pool |
| `rate_limiter_alerts.yml` | ~5 | Rate limit abuse, 429 rate |
| `mimir_alerts.yml` | ~4 | Mimir remote write health |
| `loki_alerts.yml` | ~4 | Log pipeline health |
| `tempo_alerts.yml` | ~4 | Trace ingestion health |
| `infrastructure_alerts.yml` | ~4 | CPU, memory, process health |
| `streaming_alerts.yml` | ~4 | TTFC, stream error rate |
| `anomaly_alerts.yml` | ~3 | Anomaly detection via recording rules |
| `notification_policies.yml` | — | Routing: ops-email + critical-email |

### Recording Rules (32 rules — `prometheus/recording_rules_baselines.yml`)

Pre-computed baseline metrics for anomaly detection. **DO NOT DELETE** — anomaly alerts depend on them.

---

## Tempo 2.6.1 Configuration (March 2026 Optimization)

Key notes for working with `tempo/tempo.yml`:

- **local_blocks processor**: enables `{ } | rate()` TraceQL metrics queries directly against Tempo (panels 701–703 in tempo.json). Adds ~30–50MB RSS — monitor memory in Railway.
- **Span metrics remote-write to Mimir**: `MIMIR_REMOTE_WRITE_URL` substituted by `entrypoint.sh` at runtime
- **Phase 2 dimensions** (in `span_metrics`): `gen_ai.response.finish_reason`, `http.route`, `error.type`, `span.kind`, `db.system` — these are NEW in March 2026; panels 704–705 show no data until first traces with these attributes arrive
- **Token counts are NOT dimensions**: `gen_ai.usage.prompt_tokens` / `gen_ai.usage.completion_tokens` are numeric — read via TraceQL, not span_metrics labels
- **BACKEND-2**: Until the gatewayz-backend is confirmed sending OTLP traces to `tempo.railway.internal:4317`, all Tempo panels show "No data"

---

## Common Tasks

### Add a panel to an existing dashboard
1. Open the dashboard JSON in `grafana/dashboards/<folder>/`
2. Add panel to `panels` array — copy structure from a nearby panel of same type
3. Use `"uid": "grafana_mimir"` for span metrics (`traces_spanmetrics_*`, `traces_service_graph_*`)
4. Use `"uid": "grafana_prometheus"` for live scrape metrics (`fastapi_*`, `process_*`, etc.)
5. Use `instant: true` on stat panel targets; omit for timeseries
6. Always: `clamp_min(expr, 0.001)` as denominator in PromQL division

### Add a new Grafana alert rule
1. Add to appropriate file in `grafana/provisioning/alerting/rules/`
2. Required fields: `uid`, `title`, `condition`, `for`, `annotations.summary`, `annotations.description`, `annotations.runbook_url`, `labels.severity`
3. Two-refId pattern: refId A = PromQL/LogQL query, refId C = `classic_conditions` threshold
4. `noDataState: NoData` for new dimensions not yet in Mimir; `noDataState: Alerting` for absence-is-alert patterns

### Validate dashboard JSON
```bash
cd railway-grafana-stack
bash scripts/validate_dashboards.sh
```

### Verify metrics pipeline
```bash
cd railway-grafana-stack
bash scripts/verify_metrics.sh
```

### Clean up deprecated Grafana folders (Developer / Prometheus / Sentry)
```bash
GRAFANA_URL=https://logs.gatewayz.ai \
GRAFANA_USER=admin \
GRAFANA_PASSWORD=<your-admin-password> \
bash scripts/cleanup_deprecated_grafana_folders.sh
```

---

## Read First — By Task

| Task | File to Read |
|------|-------------|
| Add/edit a dashboard | `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md` |
| Add alert rules | `docs/deployment/ALERTING_SETUP.md` |
| Debug no data | `docs/monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md` |
| Deploy to Railway | `docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md` |
| Connect backend | `docs/backend/COMPLETE_BACKEND_INTEGRATION_GUIDE.md` |
| Fix Loki labels | `docs/troubleshooting/LOKI_FIX_GUIDE.md` |
| Fix Mimir remote write | `docs/troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md` |
| Understand all metrics | `docs/backend/BACKEND_METRICS_REQUIREMENTS.md` |

---

**Last Updated:** March 2026
**Status:** Production-ready · Railway deployment active at logs.gatewayz.ai
