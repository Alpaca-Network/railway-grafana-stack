# GatewayZ Monitoring Stack - Documentation Index

Start here after reading the root [README.md](../README.md).

---

## 🆕 Latest Updates (January 2026)

**Branch**: `feat/feat-mimir-took`

### New Features & Documentation

| Document | Description |
|----------|-------------|
| [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md) | **NEW** Grafana Mimir for horizontal scaling & long-term storage |
| [../BRANCH_CHANGES_SUMMARY.md](../BRANCH_CHANGES_SUMMARY.md) | **NEW** Complete summary of all branch changes |
| [deployment/ALERTING_SETUP.md](deployment/ALERTING_SETUP.md) | **NEW** Email alert configuration & Gmail setup |
| [deployment/DEPLOYMENT_CHECKLIST.md](deployment/DEPLOYMENT_CHECKLIST.md) | **NEW** Deployment procedures & verification |
| [deployment/DIAGNOSTICS_AND_FIXES.md](deployment/DIAGNOSTICS_AND_FIXES.md) | **NEW** Comprehensive troubleshooting guide |
| [deployment/QUICKSTART.md](deployment/QUICKSTART.md) | **NEW** 5-minute local quick start |

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

### Stack Components
- **Grafana 11.5.2** - Visualization (7 dashboards)
- **Prometheus 3.2.1** - Metrics collection (6 scrape jobs)
- **Mimir 2.11.0** - Long-term storage (NEW)
- **Loki 3.4** - Log aggregation
- **Tempo** - Distributed tracing
- **Redis Exporter** - Redis metrics
- **Alertmanager** - Alert routing

### Data Flow
```
Backend API → Prometheus → Mimir (long-term)
                ↓
             Grafana (visualization)
                ↑
         Loki, Tempo
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

**Last Updated**: January 17, 2026  
**Branch**: `feat/feat-mimir-took`  
**Status**: ✅ Documentation Complete
