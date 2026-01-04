# Documentation Guide

This guide helps you find the right documentation for your needs.

## 📁 Documentation Structure

```
railway-grafana-stack/
├── README.md                           # Main project overview & quick start
│
├── docs/
│   ├── docs-index.md                   # Main documentation index (start here after README)
│   ├── archive/                        # Archived root-level docs moved here
│
│   ├── REDIS_MONITORING_GUIDE.md       # Redis monitoring options
│   │
│   ├── backend/                        # Backend Integration
│   │   └── BACKEND_METRICS_REQUIREMENTS.md  # Required metrics for dashboards
│   │
│   ├── deployment/                     # Deployment & Workflows
│   │   ├── RAILWAY_DEPLOYMENT_QUICK_START.md  # Deploy to Railway
│   │   └── STAGING_WORKFLOW.md         # Testing before production
│   │
│   ├── dashboards/                     # Dashboard Documentation
│   │   ├── MODELS_MONITORING_SETUP.md  # AI model monitoring
│   │   ├── PROVIDER_MANAGEMENT_DASHBOARD.md  # Provider health
│   │   ├── PROVIDER_ENDPOINTS_INTEGRATION.md  # Provider API integration
│   │   └── PROMETHEUS_METRICS_EXPANSION.md   # Custom metrics
│   │
│   ├── troubleshooting/                # Fix Guides
│   │   ├── GRAFANA_CONNECTIONS.md      # Datasource connectivity
│   │   ├── LOKI_FIX_GUIDE.md           # Log ingestion issues
│   │   ├── LOKI_DEPLOYMENT_FIX.md      # Railway deployment issues
│   │   ├── TEMPO_INTEGRATION.md        # Tracing setup
│   │   └── SENTRY_SETUP.md             # Error tracking
│   │
│   └── archive/                        # Deprecated Documentation
│       └── root-md/                    # Former root *.md files (kept for reference)
```

---

## 🎯 Quick Navigation

### I want to...

#### **Get Started**
- 🏠 Start here → [README.md](../README.md)
- 💻 Run locally → [QUICK_START.md](../QUICK_START.md)
- ☁️ Deploy to Railway → [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

#### **Integrate My Backend**
- 📊 See required metrics → [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](backend/BACKEND_METRICS_REQUIREMENTS.md)
- 🔴 Setup Redis monitoring → [docs/REDIS_MONITORING_GUIDE.md](REDIS_MONITORING_GUIDE.md)

#### **Work with Dashboards**
- 🤖 Monitor AI models → [docs/dashboards/MODELS_MONITORING_SETUP.md](dashboards/MODELS_MONITORING_SETUP.md)
- 🔌 Track providers → [docs/dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md](dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md)
- 📈 Add custom metrics → [docs/dashboards/PROMETHEUS_METRICS_EXPANSION.md](dashboards/PROMETHEUS_METRICS_EXPANSION.md)

#### **Deploy & Test**
- 🚀 Deploy to Railway → [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)
- 🧪 Test before production → [docs/deployment/STAGING_WORKFLOW.md](deployment/STAGING_WORKFLOW.md)

#### **Fix Issues**
- 🔗 Datasource problems → [docs/troubleshooting/GRAFANA_CONNECTIONS.md](troubleshooting/GRAFANA_CONNECTIONS.md)
- 📝 Logs not showing → [docs/troubleshooting/LOKI_FIX_GUIDE.md](troubleshooting/LOKI_FIX_GUIDE.md)
- 🔍 Tracing not working → [docs/troubleshooting/TEMPO_INTEGRATION.md](troubleshooting/TEMPO_INTEGRATION.md)
- 🐛 Setup error tracking → [docs/troubleshooting/SENTRY_SETUP.md](troubleshooting/SENTRY_SETUP.md)

#### **Understand Recent Changes**
- 📋 See what changed → [CHANGES_SUMMARY.md](../CHANGES_SUMMARY.md)

---

## 📚 Documentation by Role

### For **Backend Developers**

Priority reading order:
1. [README.md](../README.md) - Overview
2. [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](backend/BACKEND_METRICS_REQUIREMENTS.md) - **REQUIRED metrics**
3. [docs/REDIS_MONITORING_GUIDE.md](REDIS_MONITORING_GUIDE.md) - Redis options
4. [docs/dashboards/MODELS_MONITORING_SETUP.md](dashboards/MODELS_MONITORING_SETUP.md) - Model metrics
5. [docs/dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md](dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md) - Provider metrics

### For **DevOps / Infrastructure**

Priority reading order:
1. [QUICK_START.md](../QUICK_START.md) - Local setup
2. [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md) - Deployment
3. [docs/deployment/STAGING_WORKFLOW.md](deployment/STAGING_WORKFLOW.md) - Testing workflow
4. [CHANGES_SUMMARY.md](../CHANGES_SUMMARY.md) - Recent optimizations
5. [docs/troubleshooting/](troubleshooting/) - All fix guides

### For **Product / Managers**

Priority reading order:
1. [README.md](../README.md) - Project overview
2. Dashboard sections in README - What metrics are available
3. [CHANGES_SUMMARY.md](../CHANGES_SUMMARY.md) - What was recently improved

---

## 🔄 Documentation Lifecycle

### Active Documentation (Current)
Files in `docs/` directories are current and maintained:
- **backend/** - Backend integration requirements
- **deployment/** - Deployment and workflow guides
- **dashboards/** - Dashboard-specific documentation
- **troubleshooting/** - Active fix guides

### Archived Documentation
Files in `docs/archive/` are outdated or superseded:
- Kept for historical reference
- May contain outdated information
- See active docs for current information

**Archived files (13 total):**
- 3 backend instrumentation guides → Superseded by BACKEND_METRICS_REQUIREMENTS.md
- 5 FastAPI dashboard docs → Information consolidated into README.md
- 2 dashboard fixes docs → Consolidated into troubleshooting guides
- 3 Railway deployment docs → Kept RAILWAY_DEPLOYMENT_QUICK_START.md only

---

## 📝 Contributing to Documentation

### When to Update Documentation

**Update when:**
- Adding new features
- Changing configuration
- Fixing bugs that affect setup
- Discovering common issues

**Where to update:**
- Configuration changes → Update relevant doc in `docs/`
- New features → Add to README.md and specific guide
- Fixes → Add to `docs/troubleshooting/`
- Backend requirements → Update `docs/backend/BACKEND_METRICS_REQUIREMENTS.md`

### Documentation Standards

**File naming:**
- Use UPPERCASE_WITH_UNDERSCORES.md for root files
- Use descriptive names: `FEATURE_GUIDE.md` not `GUIDE.md`

**Structure:**
```markdown
# Title

Brief description (1-2 sentences)

## Section 1

Content...

## Section 2

Content...
```

**Code blocks:**
- Always specify language: ```python, ```bash, ```yaml
- Include comments for clarity
- Show complete, runnable examples

**Links:**
- Use relative paths: `[Guide](docs/backend/GUIDE.md)`
- Link to specific sections: `[Section](GUIDE.md#section-name)`
- Always test links after changes

---

## 🗺️ Documentation Map

### Root Level

| File | Purpose | Audience |
|------|---------|----------|
| [README.md](../README.md) | Main project documentation | Everyone |
| [QUICK_START.md](../QUICK_START.md) | Local development setup | Developers |
| [CHANGES_SUMMARY.md](../CHANGES_SUMMARY.md) | Recent changes log | Everyone |

### docs/backend/

| File | Purpose | Audience |
|------|---------|----------|
| [BACKEND_METRICS_REQUIREMENTS.md](backend/BACKEND_METRICS_REQUIREMENTS.md) | Required Prometheus metrics | Backend developers |

### docs/deployment/

| File | Purpose | Audience |
|------|---------|----------|
| [RAILWAY_DEPLOYMENT_QUICK_START.md](deployment/RAILWAY_DEPLOYMENT_QUICK_START.md) | Railway deployment guide | DevOps |
| [STAGING_WORKFLOW.md](deployment/STAGING_WORKFLOW.md) | Staging testing process | DevOps |

### docs/dashboards/

| File | Purpose | Audience |
|------|---------|----------|
| [MODELS_MONITORING_SETUP.md](dashboards/MODELS_MONITORING_SETUP.md) | AI model monitoring | Backend/Product |
| [PROVIDER_MANAGEMENT_DASHBOARD.md](dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md) | Provider health tracking | Backend/DevOps |
| [PROVIDER_ENDPOINTS_INTEGRATION.md](dashboards/PROVIDER_ENDPOINTS_INTEGRATION.md) | Provider API integration | Backend |
| [PROMETHEUS_METRICS_EXPANSION.md](dashboards/PROMETHEUS_METRICS_EXPANSION.md) | Custom metrics guide | Backend |

### docs/troubleshooting/

| File | Purpose | Audience |
|------|---------|----------|
| [GRAFANA_CONNECTIONS.md](troubleshooting/GRAFANA_CONNECTIONS.md) | Datasource connectivity fixes | DevOps |
| [LOKI_FIX_GUIDE.md](troubleshooting/LOKI_FIX_GUIDE.md) | Log ingestion issues | DevOps |
| [LOKI_DEPLOYMENT_FIX.md](troubleshooting/LOKI_DEPLOYMENT_FIX.md) | Railway deployment issues | DevOps |
| [TEMPO_INTEGRATION.md](troubleshooting/TEMPO_INTEGRATION.md) | Tracing setup & fixes | DevOps |
| [SENTRY_SETUP.md](troubleshooting/SENTRY_SETUP.md) | Error tracking setup | Backend/DevOps |

### docs/ (Root)

| File | Purpose | Audience |
|------|---------|----------|
| [REDIS_MONITORING_GUIDE.md](REDIS_MONITORING_GUIDE.md) | Redis monitoring options | Backend/DevOps |
| [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) | This file | Everyone |

---

## 🔍 Search Tips

### Find by topic:

**Deployment:**
- Search: `deployment`, `railway`, `staging`
- Location: `docs/deployment/`

**Metrics:**
- Search: `metrics`, `prometheus`, `backend`
- Location: `docs/backend/`, `docs/dashboards/`

**Logs:**
- Search: `loki`, `logs`, `winston`
- Location: `docs/troubleshooting/LOKI_*.md`

**Tracing:**
- Search: `tempo`, `traces`, `opentelemetry`
- Location: `docs/troubleshooting/TEMPO_*.md`

**Dashboards:**
- Search: `grafana`, `dashboard`, `models`, `providers`
- Location: `docs/dashboards/`

---

## 📞 Need Help?

1. **Check this guide** - Find the right document for your task
2. **Search documentation** - Use Ctrl+F or grep
3. **Check troubleshooting** - See `docs/troubleshooting/`
4. **Review recent changes** - See `CHANGES_SUMMARY.md`
5. **Check examples** - See `examples/` directory in project

---

**Last updated:** 2025-12-23
**Documentation version:** 2.0 (Reorganized structure)
