# GatewayZ Monitoring Stack Documentation

Complete documentation for the GatewayZ monitoring infrastructure deployed on Railway.

**Stack**: Prometheus + Mimir + Grafana + Alertmanager (planned)

---

## 📚 Documentation Index

### 🚀 Setup & Quick Start
New to the monitoring stack? Start here.

- **[NEXT_STEPS.md](setup/NEXT_STEPS.md)** - Step-by-step deployment guide for Prometheus → Mimir integration
- **[QUICK_REFERENCE.md](setup/QUICK_REFERENCE.md)** - One-page cheat sheet for common commands and queries
- **[SETUP_COMPLETE.md](setup/SETUP_COMPLETE.md)** - Complete setup summary with architecture, troubleshooting, and verification
- **[QUICK_START_PERCENTILE_FIX.md](setup/QUICK_START_PERCENTILE_FIX.md)** - Quick fix guide for percentile metrics in dashboards

**Start with**: QUICK_REFERENCE.md → NEXT_STEPS.md → SETUP_COMPLETE.md

---

### 🔧 Troubleshooting
Having issues? Check these guides.

- **[REMOTE_WRITE_DEBUG.md](troubleshooting/REMOTE_WRITE_DEBUG.md)** - Debug Prometheus → Mimir remote write connection
- **[PROMETHEUS_MIMIR_CONNECTION_FIXES.md](troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md)** - Common fixes for connection issues
- **[DATA_FLOW_VERIFICATION.md](troubleshooting/DATA_FLOW_VERIFICATION.md)** - Verify metrics flow through the pipeline
- **[RAILWAY_QUICK_FIX.md](troubleshooting/RAILWAY_QUICK_FIX.md)** - Quick fixes for Railway-specific issues

**Common Issues**:
- No data in Mimir? → REMOTE_WRITE_DEBUG.md
- Connection errors? → PROMETHEUS_MIMIR_CONNECTION_FIXES.md
- Need to verify setup? → DATA_FLOW_VERIFICATION.md

---

### 🏗️ Architecture & Design
Understanding how the system works.

- **[MIMIR.md](architecture/MIMIR.md)** - Complete Mimir architecture, API reference, and configuration guide
- **[PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md](architecture/PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md)** - Railway-specific networking and deployment
- **[RAILWAY_MIMIR_DEPLOYMENT.md](architecture/RAILWAY_MIMIR_DEPLOYMENT.md)** - Mimir deployment guide for Railway
- **[AGENTS.md](architecture/AGENTS.md)** - Information about monitoring agents and exporters

**System Flow**:
```
Prometheus (scrapes) → Prometheus (remote_write) → Mimir (stores) → Grafana (queries)
```

---

### 📊 Monitoring & Metrics
Dashboards, metrics, and monitoring best practices.

- **[DASHBOARDS_USING_PERCENTILE_METRICS.md](monitoring/DASHBOARDS_USING_PERCENTILE_METRICS.md)** - List of dashboards using percentile metrics
- **[FOUR_GOLDEN_SIGNALS_AUDIT.md](monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md)** - Audit of Four Golden Signals implementation
- **[PERCENTILE_METRICS_FIX.md](monitoring/PERCENTILE_METRICS_FIX.md)** - Fix for percentile metric calculations
- **[PROMETHEUS_SCRAPING_AUDIT.md](monitoring/PROMETHEUS_SCRAPING_AUDIT.md)** - Audit of Prometheus scrape targets

**Key Metrics**:
- Latency: P50, P95, P99
- Traffic: Request rate, RPS
- Errors: Error rate, error count
- Saturation: CPU, memory, queue depth

---

### 📝 Change Logs & History
What changed and when.

- **[BRANCH_CHANGES_SUMMARY.md](changes/BRANCH_CHANGES_SUMMARY.md)** - Summary of changes in current branch
- **[SESSION_COMPLETE_SUMMARY.md](changes/SESSION_COMPLETE_SUMMARY.md)** - Summary of completed work sessions
- **[BACKEND_SERVICES_FIX_SUMMARY.md](changes/BACKEND_SERVICES_FIX_SUMMARY.md)** - Backend services dashboard fixes
- **[BACKEND_SERVICES_INVESTIGATION.md](changes/BACKEND_SERVICES_INVESTIGATION.md)** - Investigation notes for backend issues
- **[DOCUMENTATION_UPDATE_COMPLETE.md](changes/DOCUMENTATION_UPDATE_COMPLETE.md)** - Documentation update summary

---

### 💻 Development & Contributing
Guidelines for contributing to the monitoring stack.

- **[FUTURE_DEVELOPMENT_GUIDELINES.md](development/FUTURE_DEVELOPMENT_GUIDELINES.md)** - Guidelines for future development
- **[CLAUDE.md](development/CLAUDE.md)** - Project context for AI assistants
- **[ALERTING_IMPLEMENTATION_PLAN.md](development/ALERTING_IMPLEMENTATION_PLAN.md)** - Plan for implementing alerting system

**Want to contribute?** Read FUTURE_DEVELOPMENT_GUIDELINES.md first.

---

## 🎯 Quick Navigation

### By Role

**SRE/DevOps**:
1. [SETUP_COMPLETE.md](setup/SETUP_COMPLETE.md) - Deployment overview
2. [MIMIR.md](architecture/MIMIR.md) - Storage architecture
3. [REMOTE_WRITE_DEBUG.md](troubleshooting/REMOTE_WRITE_DEBUG.md) - Troubleshooting

**Developer**:
1. [QUICK_REFERENCE.md](setup/QUICK_REFERENCE.md) - Common queries
2. [DASHBOARDS_USING_PERCENTILE_METRICS.md](monitoring/DASHBOARDS_USING_PERCENTILE_METRICS.md) - Dashboard metrics
3. [PROMETHEUS_SCRAPING_AUDIT.md](monitoring/PROMETHEUS_SCRAPING_AUDIT.md) - What metrics are collected

**Manager/Lead**:
1. [FOUR_GOLDEN_SIGNALS_AUDIT.md](monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md) - Monitoring coverage
2. [ALERTING_IMPLEMENTATION_PLAN.md](development/ALERTING_IMPLEMENTATION_PLAN.md) - Alerting roadmap
3. [BRANCH_CHANGES_SUMMARY.md](changes/BRANCH_CHANGES_SUMMARY.md) - Recent changes

---

### By Task

**Deploying the stack**:
1. [NEXT_STEPS.md](setup/NEXT_STEPS.md)
2. [PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md](architecture/PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md)
3. [DATA_FLOW_VERIFICATION.md](troubleshooting/DATA_FLOW_VERIFICATION.md)

**Fixing issues**:
1. [QUICK_REFERENCE.md](setup/QUICK_REFERENCE.md) - Quick commands
2. [REMOTE_WRITE_DEBUG.md](troubleshooting/REMOTE_WRITE_DEBUG.md) - Debug script
3. [PROMETHEUS_MIMIR_CONNECTION_FIXES.md](troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md) - Common fixes

**Understanding metrics**:
1. [FOUR_GOLDEN_SIGNALS_AUDIT.md](monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md)
2. [PERCENTILE_METRICS_FIX.md](monitoring/PERCENTILE_METRICS_FIX.md)
3. [PROMETHEUS_SCRAPING_AUDIT.md](monitoring/PROMETHEUS_SCRAPING_AUDIT.md)

**Adding features**:
1. [FUTURE_DEVELOPMENT_GUIDELINES.md](development/FUTURE_DEVELOPMENT_GUIDELINES.md)
2. [ALERTING_IMPLEMENTATION_PLAN.md](development/ALERTING_IMPLEMENTATION_PLAN.md)
3. [CLAUDE.md](development/CLAUDE.md)

---

## 🔗 External Resources

### Official Documentation
- **Prometheus**: https://prometheus.io/docs/
- **Grafana Mimir**: https://grafana.com/docs/mimir/latest/
- **Grafana**: https://grafana.com/docs/grafana/latest/
- **Railway**: https://docs.railway.app/

### Project URLs
- **Prometheus UI**: `https://prometheus-{project}.railway.app`
- **Mimir API**: `https://mimir-{project}.railway.app`
- **Grafana**: `https://grafana-{project}.railway.app`
- **Railway Dashboard**: https://railway.app/dashboard

---

## 📞 Support & Contact

### Getting Help
1. **Check documentation** - Use this index to find relevant docs
2. **Run diagnostics** - Use scripts in `railway-grafana-stack/` directory
3. **Check logs** - `railway logs --service <service-name>`
4. **Review issues** - Check known issues in troubleshooting docs

### Diagnostic Scripts
Located in `railway-grafana-stack/` root:
- `diagnose-prometheus-mimir.sh` - Diagnose Prometheus → Mimir connection
- `test-prometheus-mimir-grafana-flow.sh` - Test full pipeline
- `verify-remote-write.sh` - Verify remote write configuration
- `quick-setup.sh` - Interactive setup wizard

### Contact
- **Email**: manjeshprasad21@gmail.com
- **Project**: Gateway Z Universal AI Inference Platform

---

## 🗂️ Directory Structure

```
docs/
├── README.md (this file)
├── setup/                      # Getting started guides
│   ├── NEXT_STEPS.md
│   ├── QUICK_REFERENCE.md
│   ├── SETUP_COMPLETE.md
│   └── QUICK_START_PERCENTILE_FIX.md
├── troubleshooting/            # Problem solving
│   ├── REMOTE_WRITE_DEBUG.md
│   ├── PROMETHEUS_MIMIR_CONNECTION_FIXES.md
│   ├── DATA_FLOW_VERIFICATION.md
│   └── RAILWAY_QUICK_FIX.md
├── architecture/               # System design
│   ├── MIMIR.md
│   ├── PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md
│   ├── RAILWAY_MIMIR_DEPLOYMENT.md
│   └── AGENTS.md
├── monitoring/                 # Metrics & dashboards
│   ├── DASHBOARDS_USING_PERCENTILE_METRICS.md
│   ├── FOUR_GOLDEN_SIGNALS_AUDIT.md
│   ├── PERCENTILE_METRICS_FIX.md
│   └── PROMETHEUS_SCRAPING_AUDIT.md
├── changes/                    # Change history
│   ├── BRANCH_CHANGES_SUMMARY.md
│   ├── SESSION_COMPLETE_SUMMARY.md
│   ├── BACKEND_SERVICES_FIX_SUMMARY.md
│   ├── BACKEND_SERVICES_INVESTIGATION.md
│   └── DOCUMENTATION_UPDATE_COMPLETE.md
└── development/                # Contributing
    ├── FUTURE_DEVELOPMENT_GUIDELINES.md
    ├── CLAUDE.md
    └── ALERTING_IMPLEMENTATION_PLAN.md
```

---

## 📖 Reading Order for New Users

**Day 1 - Setup**:
1. [QUICK_REFERENCE.md](setup/QUICK_REFERENCE.md) (10 min)
2. [NEXT_STEPS.md](setup/NEXT_STEPS.md) (30 min)
3. Deploy stack following NEXT_STEPS
4. Run verification: `./quick-setup.sh`

**Day 2 - Deep Dive**:
1. [SETUP_COMPLETE.md](setup/SETUP_COMPLETE.md) (30 min)
2. [MIMIR.md](architecture/MIMIR.md) (30 min)
3. [FOUR_GOLDEN_SIGNALS_AUDIT.md](monitoring/FOUR_GOLDEN_SIGNALS_AUDIT.md) (15 min)

**Day 3 - Troubleshooting**:
1. [REMOTE_WRITE_DEBUG.md](troubleshooting/REMOTE_WRITE_DEBUG.md) (20 min)
2. [PROMETHEUS_MIMIR_CONNECTION_FIXES.md](troubleshooting/PROMETHEUS_MIMIR_CONNECTION_FIXES.md) (15 min)
3. Practice: Break something, fix it using docs

**Week 2 - Advanced**:
1. [ALERTING_IMPLEMENTATION_PLAN.md](development/ALERTING_IMPLEMENTATION_PLAN.md)
2. [FUTURE_DEVELOPMENT_GUIDELINES.md](development/FUTURE_DEVELOPMENT_GUIDELINES.md)
3. Contribute: Add a dashboard or alert

---

## 🔄 Document Maintenance

### When to Update Docs
- **After deployment changes** → Update setup/ docs
- **After fixing issues** → Update troubleshooting/ docs
- **After architecture changes** → Update architecture/ docs
- **After adding features** → Update changes/ docs

### Documentation Standards
- Use Markdown format
- Include code examples
- Add diagrams for complex concepts
- Keep TOC updated
- Cross-reference related docs

---

**Last Updated**: January 25, 2026  
**Version**: 2.0  
**Status**: ✅ All docs organized and indexed
