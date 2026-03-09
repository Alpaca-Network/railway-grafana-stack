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
| **DO NOT** modify datasource UIDs | All 15 dashboards depend on `grafana_prometheus`, `grafana_mimir`, `grafana_loki`, `grafana_tempo`, `grafana_pyroscope` |
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
  - All 15 Grafana dashboards complete (400+ panels, 0 placeholders)
  - 16 Prometheus alert rules
  - 40+ Grafana alert rules (10 YAML files)
  - 32 Prometheus recording rules (baseline pre-computations)
  - Alertmanager two-tier routing (ops-email + critical-email)
  - Railway deployment configs for all services
  - 48 documentation files

✅ DONE — This Session
  - dashboards.yml: System Quality provisioner added
  - grafana/dashboards/reliability/ folder created
  - MASTER.md: Backend Telemetry Architecture section (section 16) added
  - README.md: Backend Telemetry Pipeline section added
  - ACCEPTANCE_CRITERIA.md: Created with criteria for all 25 Kanban cards

🔄 IN PROGRESS
  - TASK-2: System-Reliability-Dashboard.json (scaffold + 8 pillar rows)

📋 READY (Kanban)
  - TASK-3 through TASK-10: 8 pillar rows for the System Quality dashboard

⚠️ OUTSTANDING GAPS (not yet scheduled)
  - BACKEND-1: Verify FASTAPI_TARGET env var in Railway
  - BACKEND-2: Verify OTLP traces from backend → Tempo
  - BACKEND-3: Verify Loki log labels match app="gatewayz"
  - INFRA-1: Validate Redis exporter reliability
  - INFRA-2: Migrate Mimir storage from filesystem → S3
```

---

## Active Work — System Quality Dashboard

**File to create:** `grafana/dashboards/reliability/System-Reliability-Dashboard.json`
**UID:** `gatewayz-system-quality-pillars`
**Schema:** `schemaVersion: 39`, `refresh: "30s"`
**Datasource (Prometheus):** `{ "type": "prometheus", "uid": "grafana_prometheus" }`
**Datasource (Loki):** `{ "type": "loki", "uid": "grafana_loki" }`
**Panel ID blocks:** 100s=Reliability, 200s=Performance, 300s=Scalability, 400s=Availability, 500s=Observability, 600s=FaultTolerance, 700s=Security, 800s=Maintainability
**Style reference:** Copy stat/timeseries structure from `grafana/dashboards/infrastructure/Infrastructure-Health.json`

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
│   ├── dashboards/                    ← 15 dashboard JSONs + 1 in progress
│   │   └── reliability/               ← NEW — System Quality dashboard
│   └── provisioning/
│       ├── dashboards/dashboards.yml  ← Folder registration
│       ├── datasources/               ← 7 datasource YAMLs
│       └── alerting/rules/            ← 10 alert rule YAMLs (40+ rules)
├── mimir/mimir.yml                    ← Long-term metrics config
├── loki/loki.yml                      ← Log aggregation config
├── tempo/tempo.yml                    ← Trace storage + span metrics
├── alertmanager/alertmanager.yml      ← Alert routing
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
