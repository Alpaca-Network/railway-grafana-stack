# GatewayZ Monitoring Stack - Documentation Index

Start here after reading the root [README.md](../README.md).

---

## 🆕 Latest Updates (March 2026)

**Branch**: `refactor/refactor-master-markdowns`

### New Documentation (March 2026)

| Document | Description |
|----------|-------------|
| [../MASTER.md](../MASTER.md) | **NEW** Master project wiki — full architecture, dashboards, alerts, env vars, backend telemetry |
| [../ACCEPTANCE_CRITERIA.md](../ACCEPTANCE_CRITERIA.md) | **NEW** Acceptance criteria for all 25 Kanban cards |
| [architecture/PYROSCOPE.md](architecture/PYROSCOPE.md) | **NEW** Pyroscope 1.7.1 — continuous profiling setup & datasource |
| [architecture/JSON_API_PROXY.md](architecture/JSON_API_PROXY.md) | **NEW** JSON-API-Proxy — provider health data bridge to Grafana |

### Previous Updates (January 2026)

| Document | Description |
|----------|-------------|
| [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md) | Grafana Mimir for horizontal scaling & long-term storage |
| [deployment/ALERTING_SETUP.md](deployment/ALERTING_SETUP.md) | Email alert configuration & Gmail setup |
| [deployment/DEPLOYMENT_CHECKLIST.md](deployment/DEPLOYMENT_CHECKLIST.md) | Deployment procedures & verification |
| [deployment/DIAGNOSTICS_AND_FIXES.md](deployment/DIAGNOSTICS_AND_FIXES.md) | Historical troubleshooting (Jan 16, 2026 — issues resolved) |
| [deployment/QUICKSTART.md](deployment/QUICKSTART.md) | 5-minute local quick start |

---

## 🚀 Quick Start

### Getting Started
- **Main Overview**: [README.md](../README.md)
- **Local Development**: [deployment/QUICKSTART.md](deployment/QUICKSTART.md) (5 minutes)
- **Railway Deployment**: [deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)
- **Mimir Integration**: [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md)

---

## 📊 Core Guides

### Infrastructure
| Guide | Description |
|-------|-------------|
| [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md) | Mimir setup, configuration, troubleshooting |
| [REDIS_MONITORING_GUIDE.md](REDIS_MONITORING_GUIDE.md) | Redis monitoring & performance |
| [backend/BACKEND_METRICS_REQUIREMENTS.md](backend/BACKEND_METRICS_REQUIREMENTS.md) | Required metrics for dashboards |

### Deployment
| Guide | Description |
|-------|-------------|
| [deployment/QUICKSTART.md](deployment/QUICKSTART.md) | 5-minute local setup |
| [deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md) | Railway deployment |
| [deployment/DEPLOYMENT_CHECKLIST.md](deployment/DEPLOYMENT_CHECKLIST.md) | Pre/post deployment checks |
| [deployment/ALERTING_SETUP.md](deployment/ALERTING_SETUP.md) | Email alerts & monitoring |
| [deployment/HANDOFF_README.md](deployment/HANDOFF_README.md) | Loki/Tempo handoff notes |
| [deployment/implementation_plan.md](deployment/implementation_plan.md) | Implementation plan |

---

## 🐛 Troubleshooting

### Common Issues
| Guide | Description |
|-------|-------------|
| [deployment/DIAGNOSTICS_AND_FIXES.md](deployment/DIAGNOSTICS_AND_FIXES.md) | Comprehensive troubleshooting |
| [troubleshooting/GRAFANA_CONNECTIONS.md](troubleshooting/GRAFANA_CONNECTIONS.md) | Grafana datasource issues |
| [troubleshooting/LOKI_FIX_GUIDE.md](troubleshooting/LOKI_FIX_GUIDE.md) | Loki log ingestion |
| [troubleshooting/TEMPO_INTEGRATION.md](troubleshooting/TEMPO_INTEGRATION.md) | Tempo tracing issues |

### Service-Specific
- **Mimir**: See [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md#troubleshooting)
- **Prometheus**: See [deployment/DIAGNOSTICS_AND_FIXES.md](deployment/DIAGNOSTICS_AND_FIXES.md)
- **Alertmanager**: See [deployment/ALERTING_SETUP.md](deployment/ALERTING_SETUP.md)

---

## 📈 Dashboards

| Dashboard Guide | Description |
|-----------------|-------------|
| [dashboards/MODELS_MONITORING_SETUP.md](dashboards/MODELS_MONITORING_SETUP.md) | AI model performance tracking |
| [dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md](dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md) | Provider health monitoring |

---

## 🏗️ Architecture

### Stack Components (March 2026)
- **Grafana 11.5.2** - Visualization (15 dashboards + 1 in progress)
- **Prometheus 3.2.1** - Metrics collection (6 scrape jobs)
- **Mimir 2.11.0** - Long-term metrics storage (30d retention)
- **Loki 3.4** - Log aggregation (30d retention)
- **Tempo** - Distributed tracing (48h retention)
- **Alertmanager v0.27.0** - Alert routing (two-tier email)
- **Pyroscope 1.7.1** - Continuous CPU/memory profiling
- **JSON-API-Proxy** - Provider health data bridge (:5050)

### Grafana Datasource UIDs (locked — do not change)
| UID | Type | Purpose |
|-----|------|---------|
| `grafana_prometheus` | Prometheus | Real-time metrics |
| `grafana_mimir` | Prometheus/Mimir | Long-term metrics + span metrics |
| `grafana_loki` | Loki | Logs |
| `grafana_tempo` | Tempo | Traces |
| `grafana_pyroscope` | Pyroscope | CPU/memory flamegraphs |
| `alertmanager` | Alertmanager | Alert state |
| `grafana_json_api` | Simple JSON | Provider health data |

### Architecture Docs
- [architecture/MIMIR.md](architecture/MIMIR.md) — Mimir architecture & config
- [architecture/PYROSCOPE.md](architecture/PYROSCOPE.md) — Pyroscope setup & integration
- [architecture/JSON_API_PROXY.md](architecture/JSON_API_PROXY.md) — JSON-API-Proxy & provider data
- [../MASTER.md](../MASTER.md) — Full system wiki (start here for deep understanding)

### Data Flow
```
Backend API → /metrics → Prometheus → Mimir (30d)
           → /v1/traces → Tempo (48h)
           → Loki push  → Loki (30d)
           → /prometheus/data/metrics → JSON-API-Proxy
                                              ↓
                                          Grafana (all datasources)
```

---

## 📚 Reference Documentation

### Configuration Files
- `docker-compose.yml` - Service definitions
- `prometheus/prom.yml` - Prometheus config (6 scrape jobs)
- `prometheus/alert.rules.yml` - Alert rules (NaN handling fixed)
- `prometheus/alertmanager.yml` - Alert routing & email
- `mimir/mimir.yml` - Mimir configuration
- `loki/loki.yml` - Loki configuration
- `tempo/tempo.yml` - Tempo configuration

### Environment Variables
```env
# Mimir
MIMIR_INTERNAL_URL=http://mimir:9009

# Alerting
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Authentication


# Grafana
GF_SECURITY_ADMIN_PASSWORD=yourpassword123
```

---

## 📦 Archive

Historical documentation moved to archive:
- [archive/root-md/](archive/root-md/) - Former root-level docs
- [archive/root-md/QUICK_START.md](archive/root-md/QUICK_START.md) - Legacy quick start
- [archive/root-md/ENDPOINT_VERIFICATION_REPORT.md](archive/root-md/ENDPOINT_VERIFICATION_REPORT.md) - API endpoint verification

---

## 🔗 External Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Railway Documentation](https://docs.railway.app/)

---

## 📞 Getting Help

### Quick Commands
```bash
# Verify all services
docker-compose ps

# Check Mimir health
curl http://localhost:9009/ready

# Test Prometheus
curl http://localhost:9090/-/healthy

# Verify Grafana
curl http://localhost:3000/api/health

# Run verification script
./verify_metrics.sh
```

### Documentation Structure
```
docs/
├── MIMIR_INTEGRATION_SUMMARY.md    # NEW - Mimir guide
├── REDIS_MONITORING_GUIDE.md       # Redis monitoring
├── DOCUMENTATION_GUIDE.md          # Documentation standards
├── docs-index.md                   # This file
├── backend/                        # Backend integration
├── dashboards/                     # Dashboard guides
├── deployment/                     # NEW - Deployment guides
│   ├── ALERTING_SETUP.md          # NEW
│   ├── DEPLOYMENT_CHECKLIST.md    # NEW
│   ├── DIAGNOSTICS_AND_FIXES.md   # NEW
│   ├── QUICKSTART.md              # NEW
│   └── RAILWAY_DEPLOYMENT_QUICK_START.md
├── troubleshooting/               # Troubleshooting guides
└── archive/                       # Historical docs
```

---

**Last Updated**: March 2026
**Branch**: `refactor/refactor-master-markdowns`
**Status**: ✅ Documentation Current
