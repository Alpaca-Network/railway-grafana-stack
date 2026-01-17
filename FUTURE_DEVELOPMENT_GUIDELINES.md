# Future Development Guidelines - railway-grafana-stack

**Last Updated**: January 17, 2026  
**Repository**: railway-grafana-stack  
**Current Architecture**: Mimir-based monitoring stack

---

## 🎯 Purpose

This document provides guidelines for future development sessions and iterations on the railway-grafana-stack monitoring infrastructure. Follow these policies to maintain consistency, quality, and production-readiness.

---

## 🏗️ Architecture Policy (DO NOT CHANGE)

### Core Architecture

The current monitoring stack architecture is **LOCKED** and must be maintained:

```
Backend API → Prometheus → Mimir (long-term storage)
                ↓              ↓
             Grafana ←─────────┘
                ↑
         Loki, Tempo, Redis
```

### Stack Components (Fixed)

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| **Grafana** | 11.5.2+ | Visualization | ✅ Keep |
| **Prometheus** | 3.2.1+ | Metrics collection | ✅ Keep |
| **Mimir** | 2.11.0+ | Long-term storage | ✅ Keep (NEW, DO NOT REMOVE) |
| **Loki** | 3.4+ | Log aggregation | ✅ Keep |
| **Tempo** | Latest | Distributed tracing | ✅ Keep |
| **Redis Exporter** | Latest | Redis metrics | ✅ Keep |
| **Alertmanager** | Latest | Alert routing | ✅ Keep |

### Architecture Rules

❌ **DO NOT**:
- Remove Mimir service
- Remove Prometheus remote write to Mimir
- Change the data flow (Prometheus → Mimir)
- Remove any existing services
- Change port assignments without documentation
- Remove datasources from Grafana

✅ **DO**:
- Add new scrape jobs to Prometheus (document in prom.yml)
- Add new datasources (but keep existing ones)
- Add new dashboards
- Enhance existing services
- Optimize configurations
- Improve documentation

---

## 📁 Documentation Policy

### Directory Structure (LOCKED)

```
railway-grafana-stack/
├── README.md                    # Main overview (always update)
├── BRANCH_CHANGES_SUMMARY.md    # Document all changes here
├── FUTURE_DEVELOPMENT_GUIDELINES.md  # This file
│
├── docs/
│   ├── docs-index.md            # Always update when adding docs
│   ├── MIMIR_INTEGRATION_SUMMARY.md  # Mimir reference (DO NOT DELETE)
│   │
│   ├── deployment/              # Deployment guides
│   │   ├── QUICKSTART.md
│   │   ├── DEPLOYMENT_CHECKLIST.md
│   │   ├── ALERTING_SETUP.md
│   │   └── [other deployment docs]
│   │
│   ├── backend/                 # Backend integration
│   ├── dashboards/              # Dashboard guides
│   ├── troubleshooting/         # Troubleshooting
│   └── archive/                 # Historical docs (don't add here)
│
├── mimir/                       # Mimir config (DO NOT REMOVE)
├── prometheus/                  # Prometheus config
├── grafana/                     # Grafana config
├── loki/                        # Loki config
├── tempo/                       # Tempo config
└── [other service directories]
```

### Documentation Rules

#### When Adding New Features

**ALWAYS CREATE/UPDATE**:
1. Feature-specific doc in appropriate `docs/` subdirectory
2. Update `docs/docs-index.md` with new doc links
3. Update `README.md` "What's New" section
4. Create/update `BRANCH_CHANGES_SUMMARY.md` for the branch

**NEVER**:
- Add markdown files to root directory (except README.md, BRANCH_CHANGES_SUMMARY.md)
- Remove existing documentation without archiving
- Leave broken links
- Commit without updating documentation

#### Documentation Standards

**Format**:
```markdown
# Title - Clear and Descriptive

**Last Updated**: YYYY-MM-DD  
**Branch**: branch-name  
**Status**: Status (Draft/Ready/Production)

---

## 🎯 Purpose
[Clear purpose statement]

## Content
[Well-organized content with headers]

## Examples
[Code examples with explanations]

## Troubleshooting
[Common issues and solutions]
```

**Best Practices**:
- Use emojis for section headers (🎯, 📋, 🚀, ✅, ❌, etc.)
- Include code examples with syntax highlighting
- Add architecture diagrams where appropriate
- Link to related documentation
- Include troubleshooting sections
- Keep language clear and concise

---

## 🔄 Git Workflow Policy

### Branch Naming Convention

```
feature/[feature-name]     # New features
fix/[issue-name]           # Bug fixes
docs/[doc-update]          # Documentation only
refactor/[refactor-name]   # Code refactoring
test/[test-addition]       # Testing updates
```

### Commit Message Format

```
type: brief description (max 50 chars)

Detailed explanation:
- What changed
- Why it changed
- Impact of changes

Branch: branch-name
Status: status
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Merge Policy

1. **Feature Branch → Main**:
   ```bash
   git checkout main
   git pull origin main
   git merge feature-branch --no-ff -m "detailed merge message"
   git push origin main
   ```

2. **Always use `--no-ff`** to preserve branch history

3. **Before Merging**:
   - ✅ All documentation updated
   - ✅ Tests passing (if applicable)
   - ✅ Changes documented in BRANCH_CHANGES_SUMMARY.md
   - ✅ README.md updated
   - ✅ No hardcoded credentials

---

## 🧪 Testing Policy

### Before Committing

**ALWAYS TEST**:
1. **Local Docker Compose**:
   ```bash
   docker-compose up -d --build
   docker-compose ps  # All services should be healthy
   ```

2. **Service Health**:
   ```bash
   curl http://localhost:9009/ready   # Mimir
   curl http://localhost:9090/-/healthy  # Prometheus
   curl http://localhost:3100/ready   # Loki
   curl http://localhost:3200/ready   # Tempo
   curl http://localhost:3000/api/health  # Grafana
   ```

3. **Verification Script**:
   ```bash
   ./verify_metrics.sh
   ```

### Test Checklist

- [ ] All services start successfully
- [ ] No errors in logs (`docker-compose logs`)
- [ ] Prometheus scraping all targets
- [ ] Mimir receiving remote write
- [ ] Grafana can query all datasources
- [ ] Dashboards load correctly
- [ ] Alerts configured properly (if changed)

---

## 🔐 Security Policy

### Credentials Management

**NEVER**:
- ❌ Hardcode credentials in config files
- ❌ Commit secrets to git
- ❌ Leave default passwords
- ❌ Expose services publicly without authentication

**ALWAYS**:
- ✅ Use environment variables for credentials
- ✅ Store secrets in `.env` file (gitignored)
- ✅ Use `bearer_token_file` for tokens
- ✅ Document required environment variables in `.env.example`
- ✅ Use strong passwords for production

### Environment Variables Pattern

```yaml
# In docker-compose.yml
environment:
  - SMTP_USERNAME=${SMTP_USERNAME:-}
  - SMTP_PASSWORD=${SMTP_PASSWORD:-}

# In prometheus config
bearer_token_file: '/etc/prometheus/secrets/token_file'
```

### Required Environment Variables

Always document in `.env.example`:

```env
# Mimir
MIMIR_INTERNAL_URL=http://mimir:9009

# Alerting
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Authentication
STAGING_BEARER_TOKEN=gw_staging_xxxxx

# Grafana
GF_SECURITY_ADMIN_PASSWORD=yourpassword123
```

---

## 📊 Monitoring Configuration Policy

### Prometheus Scrape Jobs

**Current Jobs** (DO NOT REMOVE):
1. `prometheus` - Self-monitoring
2. `gatewayz_production` - Production API
3. `gatewayz_staging` - Staging API (with bearer auth)
4. `redis_exporter` - Redis metrics
5. `gatewayz_data_metrics_production` - Provider data
6. `mimir` - Mimir self-monitoring

**Adding New Jobs**:
1. Add to `prometheus/prom.yml`
2. Document in README.md
3. Test scraping: `curl http://localhost:9090/api/v1/targets`
4. Update scrape job count in documentation

### Alert Rules

**Location**: `prometheus/alert.rules.yml`

**When Adding Alerts**:
1. Use proper NaN handling (see existing examples)
2. Add OR condition for zero-traffic scenarios
3. Test alert fires correctly
4. Document alert in ALERTING_SETUP.md
5. Configure appropriate thresholds

**Alert Pattern** (NaN-safe):
```yaml
alert: YourAlert
expr: |
  (
    # Normal condition
    metric_success / metric_total < 0.2
  )
  or
  (
    # Zero traffic condition
    sum(rate(metric_total[10m])) == 0
  )
for: 5m
```

### Dashboards

**Location**: `grafana/dashboards/`

**Organization**:
```
grafana/dashboards/
├── executive/        # Executive dashboards
├── backend/          # Backend monitoring
├── gateway/          # Gateway/provider monitoring
├── models/           # AI model performance
└── logs/             # Logging dashboards
```

**When Adding Dashboards**:
1. Use folder-based organization
2. Follow naming: `[category]-[name]-v[version].json`
3. Document in `docs/dashboards/`
4. Test all panels load data
5. Update README.md dashboard count

---

## 🚀 Deployment Policy

### Pre-Deployment Checklist

**MUST COMPLETE** before deploying:

- [ ] All tests passing locally
- [ ] Documentation updated
- [ ] BRANCH_CHANGES_SUMMARY.md created/updated
- [ ] README.md updated
- [ ] No hardcoded credentials
- [ ] Environment variables documented
- [ ] Backward compatible (existing features work)
- [ ] No breaking changes (or documented)

### Deployment Steps

1. **Test Locally**:
   ```bash
   docker-compose up -d --build
   ./verify_metrics.sh
   ```

2. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: description"
   ```

3. **Merge to Main**:
   ```bash
   git checkout main
   git pull origin main
   git merge feature-branch --no-ff
   git push origin main
   ```

4. **Deploy to Railway**:
   - Automatic deployment on push to main
   - Monitor Railway logs
   - Verify all services healthy

5. **Post-Deployment Verification**:
   - Check all services running
   - Verify Grafana dashboards
   - Test alerts (if changed)
   - Monitor for errors

---

## 📝 Change Documentation Template

### For Each Branch/Feature

Create `BRANCH_CHANGES_SUMMARY.md` with:

```markdown
# Branch Changes Summary - [branch-name]

**Branch**: branch-name
**Date**: YYYY-MM-DD
**Status**: Status

## Executive Summary
[Brief overview]

## Changes Overview
[List of changes]

## Features Added
[Detailed feature descriptions]

## Files Changed
[List files added/modified/deleted]

## Testing
[How it was tested]

## Deployment
[Deployment instructions]

## Impact
[Impact on system]
```

---

## 🛠️ Common Tasks Guide

### Adding a New Service

1. **Create Service Directory**:
   ```bash
   mkdir new-service
   cd new-service
   touch Dockerfile config.yml
   ```

2. **Add to docker-compose.yml**:
   ```yaml
   new-service:
     build:
       context: ./new-service
     ports:
       - "PORT:PORT"
     volumes:
       - new-service_data:/data
     healthcheck:
       test: ["CMD", "health-check-command"]
   ```

3. **Document**:
   - Update README.md
   - Create `docs/new-service/SETUP.md`
   - Update architecture diagram
   - Add to docs-index.md

### Adding a New Dashboard

1. **Create Dashboard JSON**:
   - Export from Grafana UI
   - Save to appropriate folder

2. **Update Provisioning**:
   ```yaml
   # grafana/provisioning/dashboards/dashboards.yml
   - name: 'New Category'
     folder: 'New Category'
     type: file
     options:
       path: /etc/grafana/dashboards/new-category
   ```

3. **Document**:
   - Create `docs/dashboards/NEW_DASHBOARD.md`
   - Update README.md dashboard count
   - Add to docs-index.md

### Updating Prometheus Config

1. **Backup Current Config**:
   ```bash
   cp prometheus/prom.yml prometheus/prom.yml.backup
   ```

2. **Make Changes**:
   - Edit `prometheus/prom.yml`
   - Validate syntax

3. **Test**:
   ```bash
   docker-compose restart prometheus
   docker-compose logs prometheus
   ```

4. **Document**:
   - Update README.md if scrape jobs changed
   - Document in commit message

---

## 🆘 Troubleshooting Guide for Future Sessions

### Common Issues

#### Issue: Service Won't Start

**Check**:
```bash
docker-compose ps
docker-compose logs [service-name]
```

**Common Causes**:
- Port already in use
- Configuration syntax error
- Volume permission issues
- Missing environment variables

**Solution**:
- Check logs for specific error
- Validate config syntax
- Free up ports or change port mapping
- Add missing env vars to `.env`

#### Issue: Mimir Not Receiving Data

**Check**:
```bash
# Check Prometheus remote write
docker-compose logs prometheus | grep -i "mimir\|remote_write"

# Check Mimir ingester
curl http://localhost:9009/ingester/ring
```

**Solution**:
- Verify `remote_write` configured in prom.yml
- Check network connectivity
- Restart Prometheus: `docker-compose restart prometheus`

#### Issue: Grafana Can't Query Datasource

**Check**:
```bash
# Test datasource in Grafana UI
# Or check datasource config
cat grafana/provisioning/datasources/*.yml
```

**Solution**:
- Verify datasource URL correct
- Check service is running
- Verify UID matches dashboard queries
- Restart Grafana: `docker-compose restart grafana`

---

## 📞 Getting Help in Future Sessions

### Before Starting a Session

1. **Read This Document** - Understand policies and architecture
2. **Review Current Branch** - `git status`, `git log --oneline -10`
3. **Check Documentation** - Review `docs/docs-index.md`
4. **Test Current State** - Ensure everything works before changes

### When Making Changes

1. **Create Feature Branch** - Don't work directly on main
2. **Test Incrementally** - Test after each significant change
3. **Document as You Go** - Update docs in same commit
4. **Follow Patterns** - Copy existing patterns for consistency

### Before Ending Session

1. **Update Documentation** - All docs current
2. **Create Branch Summary** - Document all changes
3. **Test Everything** - Full test run
4. **Commit and Push** - Save all work
5. **Update This Guide** - If policies changed

---

## 🔗 Quick Reference Links

### Essential Documentation

| Document | Purpose |
|----------|---------|
| `README.md` | Main overview and quick start |
| `BRANCH_CHANGES_SUMMARY.md` | Latest changes |
| `docs/docs-index.md` | Complete documentation index |
| `docs/MIMIR_INTEGRATION_SUMMARY.md` | Mimir reference |
| `docs/deployment/QUICKSTART.md` | Local setup |
| `docs/deployment/DEPLOYMENT_CHECKLIST.md` | Production deployment |
| `FUTURE_DEVELOPMENT_GUIDELINES.md` | This document |

### Quick Commands

```bash
# Start services
docker-compose up -d --build

# Check health
./verify_metrics.sh

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Stop all
docker-compose down

# Clean up
docker-compose down -v
```

---

## ✅ Session Completion Checklist

Before ending any development session:

- [ ] All changes committed
- [ ] Documentation updated
- [ ] Tests passing locally
- [ ] BRANCH_CHANGES_SUMMARY.md updated
- [ ] README.md updated if needed
- [ ] No hardcoded credentials
- [ ] No broken links in docs
- [ ] Architecture policy followed
- [ ] Git pushed to remote
- [ ] Ready for deployment or review

---

## 🎯 Core Principles (ALWAYS FOLLOW)

1. **Document Everything** - If it's not documented, it doesn't exist
2. **Test Before Commit** - Never commit untested changes
3. **Follow Architecture** - Don't remove or change core components
4. **Security First** - No hardcoded credentials, ever
5. **Backward Compatible** - Existing features must keep working
6. **Clean Repository** - Organized structure, no clutter
7. **Professional Quality** - Production-ready at all times

---

## 📊 Current State Summary

### Services Running
- Grafana (7 dashboards)
- Prometheus (6 scrape jobs)
- Mimir (long-term storage)
- Loki (log aggregation)
- Tempo (distributed tracing)
- Redis Exporter
- Alertmanager
- JSON API Proxy

### Documentation Files
- 56 markdown files
- Organized in docs/ directory
- Complete coverage of all features
- Up-to-date with current implementation

### Branch
- **Current**: main
- **Latest Merge**: feat/feat-mimir-took (5 commits)
- **Status**: Clean, production-ready

---

## 🚨 Critical Reminders

### DO NOT REMOVE

These components are essential and must NOT be removed:

- ❌ Mimir service and configuration
- ❌ Prometheus remote_write to Mimir
- ❌ Any existing Grafana datasources
- ❌ Any existing scrape jobs
- ❌ Core documentation files
- ❌ Security configurations

### ALWAYS DO

For every change:

- ✅ Update documentation
- ✅ Test locally
- ✅ Follow git workflow
- ✅ Document in BRANCH_CHANGES_SUMMARY.md
- ✅ Check security (no hardcoded credentials)
- ✅ Maintain backward compatibility

---

## 📜 Version History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-17 | 1.0 | Initial creation after Mimir integration | Claude |

---

**This document is the source of truth for future development. Follow these guidelines to maintain quality and consistency.**

---

**Last Updated**: January 17, 2026  
**Repository**: railway-grafana-stack  
**Branch**: main  
**Status**: Production Ready
