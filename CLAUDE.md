# GatewayZ LGTM Stack — Agent Quick Reference

> Read this first. Read `MASTER.md` for full detail. Read `docs/development/CLAUDE.md` for complete guidelines.

---

## TL;DR — What This Is

Production observability stack for the GatewayZ AI Inference Gateway.
**Stack:** Grafana · Prometheus · Mimir · Loki · Tempo · Alertmanager · Pyroscope
**Deployed at:** [logs.gatewayz.ai](https://logs.gatewayz.ai) via Railway.app
**Backend observed:** `gatewayz-backend` (FastAPI, 30+ AI providers)
**Active branch:** `refactor/refactor-master-markdowns`

---

## Critical Rules — DO NOT

| Rule | Why |
|------|-----|
| **DO NOT** hardcode `FASTAPI_TARGET` anywhere | It's substituted at runtime by `entrypoint.sh` |
| **DO NOT** change `schemaVersion` in dashboard JSON | Must stay at 39 for Railway Grafana compatibility |
| **DO NOT** add services to `docker-compose.yml` without updating `railway.toml` | Railway won't deploy new services without it |
| **DO NOT** modify datasource UIDs | All 13 dashboards depend on `grafana_prometheus`, `grafana_mimir`, `grafana_loki`, `grafana_tempo`, `grafana_pyroscope` |
| **DO NOT** delete recording rules | Anomaly detection alerts depend on the baseline pre-computations |
| **DO NOT** change the Mimir `X-Scope-OrgID` header | Must be `anonymous` — multitenancy is disabled |
| **DO NOT** modify `provisioning/datasources/` without testing | Breaking a UID breaks every panel using that datasource |
| **Architecture is LOCKED** | See `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md` |

---

## Current Project State (March 2026)

```
✅ DONE — Core Stack
  - 8 services running: Prometheus, Mimir, Grafana, Loki, Tempo, Alertmanager, Pyroscope, JSON-API-Proxy
  - Mimir integrated (January 2026) — long-term metrics storage (30d)
  - All 7 datasources provisioned and linked
  - All 13 Grafana dashboards complete (400+ panels, 0 placeholders)
  - 16 Prometheus alert rules
  - 46 Grafana alert rules (11 YAML files)
  - 32 Prometheus recording rules (baseline pre-computations)
  - Alertmanager two-tier routing (ops-email + critical-email)
  - Railway deployment configs for all services
  - 48 documentation files

✅ DONE — Dashboard Restructure (March 2026)
  - Renamed 7 Grafana folders to self-describing names (e.g. "Loki" → "Application Log Streams")
  - Deprecated 3 redundant dashboards (Developer Observability, Sentry Overview, Tiered Model Analysis)
  - Migrated all unique panels to canonical dashboards before deletion
  - Updated Dockerfile: removed stale COPY commands for deleted dashboard directories
  - 11 folders → 8 folders, 17 dashboards → 13 dashboards
  - Added uniform intro text panels + cross-navigation links to all 14 dashboards

✅ DONE — Tempo 2.6.1 High-Cardinality Optimization (March 2026)
  - local_blocks processor: enables TraceQL metrics queries without Mimir (panels 701–703)
  - Extended histogram buckets to 120s for large-model LLM calls (was capped at 10s)
  - Phase 2 span_metrics dimensions: finish_reason, http.route, error.type, span.kind, db.system
  - filter_policies: excludes health/metrics/probe spans from span metrics
  - peer_attributes: external API nodes (OpenAI, Anthropic) visible in service topology
  - 6 new trace-based alert rules (trace_alerts.yml): error rate, P95 latency, dark provider, truncation, route errors, content filter
  - cleanup_deprecated_grafana_folders.sh: API script to delete Developer/Prometheus/Sentry DB folders

🔄 IN PROGRESS
  - System-Reliability-Dashboard.json (Platform Quality Pillars folder) — framework exists, panels being refined

⚠️ OUTSTANDING GAPS (not yet scheduled)
  - BACKEND-1: Verify FASTAPI_TARGET env var in Railway
  - BACKEND-2: Verify OTLP traces from backend → Tempo ← SERVICE MAP SHOWS NO DATA UNTIL THIS IS DONE
  - BACKEND-3: Verify Loki log labels match app="gatewayz"
  - INFRA-1: Validate Redis exporter reliability
  - INFRA-2: Migrate Mimir storage from filesystem → S3
```

---

## Active Work — System Quality Dashboard

**File:** `grafana/dashboards/reliability/System-Reliability-Dashboard.json` (framework exists — panels being refined)
**UID:** `gatewayz-system-quality-pillars`
**Schema:** `schemaVersion: 39`, `refresh: "30s"`
**Datasource (Prometheus):** `{ "type": "prometheus", "uid": "grafana_prometheus" }`
**Datasource (Loki):** `{ "type": "loki", "uid": "grafana_loki" }`
**Panel ID blocks:** 100s=Reliability, 200s=Performance, 300s=Scalability, 400s=Availability, 500s=Observability, 600s=FaultTolerance, 700s=Security, 800s=Maintainability
**Style reference:** Same intro + row structure as `grafana/dashboards/golden-signals/Four-Golden-Signals.json`

---

## Key File Paths

```
railway-grafana-stack/
├── MASTER.md                          ← Full project wiki (see §16 for backend telemetry)
├── CLAUDE.md                          ← This file
├── ACCEPTANCE_CRITERIA.md             ← Acceptance criteria for all 25 Kanban cards
├── docker-compose.yml                 ← Service orchestration
├── prometheus/
│   ├── prometheus.yml                 ← Scrape targets + remote write
│   ├── alert.rules.yml                ← 16 Prometheus alert rules
│   └── recording_rules_baselines.yml  ← 32 recording rules
├── grafana/
│   ├── dashboards/                    ← 13 dashboard JSONs + 1 in progress (14 total)
│   │   └── reliability/               ← System Quality dashboard (in progress)
│   └── provisioning/
│       ├── dashboards/dashboards.yml  ← Folder registration (8 folders)
│       ├── datasources/               ← 7 datasource YAMLs
│       └── alerting/rules/            ← 11 alert rule YAMLs (46 rules)
│           ├── trace_alerts.yml       ← 6 trace-based alert rules (NEW March 2026)
├── mimir/mimir.yml                    ← Long-term metrics config
├── loki/loki.yml                      ← Log aggregation config
├── tempo/tempo.yml                    ← Trace storage + span metrics (Tempo 2.6.1 optimized)
├── alertmanager/alertmanager.yml      ← Alert routing
├── scripts/
│   ├── validate_dashboards.sh         ← Validate all dashboard JSON
│   ├── verify_metrics.sh              ← Verify metrics pipeline
│   └── cleanup_deprecated_grafana_folders.sh ← Delete Developer/Prometheus/Sentry DB folders
└── docs/
    ├── development/CLAUDE.md          ← Full agent guidelines (read this)
    ├── development/FUTURE_DEVELOPMENT_GUIDELINES.md ← Architecture rules
    └── docs-index.md                  ← Full doc index
```

---

## What To Read First — By Task Type

| Task | Read First |
|------|-----------|
| Add/edit a dashboard | `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md` → "Adding a Dashboard" |
| Add alert rules | `docs/deployment/ALERTING_SETUP.md` |
| Debug no data in dashboards | `docs/monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md` |
| Deploy to Railway | `docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md` |
| Connect backend | `docs/backend/COMPLETE_BACKEND_INTEGRATION_GUIDE.md` |
| Fix Loki label issues | `docs/troubleshooting/LOKI_FIX_GUIDE.md` |
| Fix Mimir remote write | `docs/troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md` |
| Understand all metrics | `docs/backend/BACKEND_METRICS_REQUIREMENTS.md` |

---

## Common Tasks

### Add a panel to an existing dashboard
1. Open the dashboard JSON in `grafana/dashboards/<folder>/`
2. Add panel object to the `panels` array — copy structure from a nearby panel
3. Use `"uid": "grafana_prometheus"` for Prometheus, `"uid": "grafana_loki"` for Loki
4. Use `instant: true` on stat panel targets, omit it for timeseries
5. Always use `clamp_min(expr, 0.001)` as denominator in division PromQL

### Add a new alert rule
1. Add to the appropriate file in `grafana/provisioning/alerting/rules/`
2. Follow existing format: `uid`, `title`, `condition`, `for`, `annotations` (include `runbook_url`), `labels` (include `severity`)
3. Test in Grafana UI before committing

### Validate dashboard JSON
```bash
cd railway-grafana-stack
bash scripts/validate_dashboards.sh
```

### Verify metrics flow
```bash
cd railway-grafana-stack
bash scripts/verify_metrics.sh
```

---

## Architecture Is LOCKED — Do Not Change

These decisions are final (per `docs/development/FUTURE_DEVELOPMENT_GUIDELINES.md`):
- **Mimir** is the primary metrics backend for Grafana (NOT direct Prometheus)
- **Loki** is the only log store (no Elasticsearch, no Splunk)
- **Tempo** is the only trace backend (no Jaeger, no Zipkin)
- **Pyroscope** is the profiling backend (linked from Tempo)
- All services run as Docker containers via Compose / Railway
- Grafana version stays at **11.5.2** until explicitly upgraded

---

*For full project detail: see `MASTER.md`*
*For complete agent guidelines: see `docs/development/CLAUDE.md`*
