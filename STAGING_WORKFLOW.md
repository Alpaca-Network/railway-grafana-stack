# Staging Workflow Guide

## Overview
This document outlines the staging workflow for testing changes before submitting PRs to main.

## Branch Strategy

### Branch Naming Convention
- **Feature branches:** `feature/<feature-name>`
- **Fix branches:** `fix/<issue-name>`
- **Staging branches:** `staging/<feature-set>`
- **Main branch:** `main` (production-ready)

### Current Staging Branch
**Branch:** `staging/models-and-fixes`

This branch contains:
- Models Monitoring Dashboard
- Tempo and Loki Railway configuration fixes
- Loki dashboard query fixes
- Datasource URL configuration guide
- System health check documentation

---

## Workflow Steps

### Step 1: Create Staging Branch
```bash
git checkout -b staging/models-and-fixes
```

**Status:** ✅ DONE

### Step 2: Test Locally
```bash
# Clean start
docker-compose down -v
docker-compose build --no-cache
docker-compose up

# In another terminal, verify services
curl http://localhost:9090/api/v1/targets  # Prometheus
curl http://localhost:3100/loki/api/v1/status/buildinfo  # Loki
curl http://localhost:3200/status  # Tempo
curl http://localhost:3000/api/health  # Grafana
```

**Verification Checklist:**
- [ ] All services start without errors
- [ ] Prometheus targets show UP
- [ ] Grafana datasources show "Data source is working"
- [ ] FastAPI Dashboard loads without errors
- [ ] Models Monitoring Dashboard loads without errors
- [ ] Tempo Distributed Tracing Dashboard loads without errors
- [ ] Loki Logs Dashboard loads without errors
- [ ] No console errors in browser

### Step 3: Test on Railway Staging
```bash
# Push staging branch to GitHub
git push origin staging/models-and-fixes

# In Railway dashboard:
# 1. Create a new deployment from staging/models-and-fixes branch
# 2. Set environment variables:
#    - LOKI_INTERNAL_URL=http://loki:3100
#    - PROMETHEUS_INTERNAL_URL=http://prometheus:9090
#    - TEMPO_INTERNAL_URL=http://tempo:3200
# 3. Deploy services
# 4. Wait 2-3 minutes for startup
# 5. Access Grafana and verify
```

**Verification Checklist:**
- [ ] Services deploy successfully
- [ ] Grafana is accessible
- [ ] All datasources show "Data source is working"
- [ ] Prometheus targets show UP
- [ ] Dashboards load without errors
- [ ] No Tempo query errors
- [ ] No Loki query errors

### Step 4: Document Issues Found
If issues are found during testing:
1. Create a new fix branch from staging
2. Fix the issue
3. Test locally
4. Push to staging branch
5. Test on Railway again
6. Repeat until all issues resolved

### Step 5: Create Pull Request
Once staging is verified as working:

```bash
# Push final staging branch
git push origin staging/models-and-fixes

# Create PR on GitHub
# Title: "feat: add Models Monitoring Dashboard and fix Tempo/Loki for Railway"
# Description: Include summary of changes, testing results, and verification steps
```

**PR Template:**
```markdown
## Summary
- Added Models Monitoring Dashboard with 11 panels
- Fixed Tempo frontend_address for Railway (0.0.0.0:3200)
- Fixed Loki instance_addr for Railway (0.0.0.0)
- Fixed Loki dashboard queries (replaced $__rate_interval with [5m])
- Added comprehensive documentation

## Testing
- [x] Tested locally with docker-compose
- [x] Tested on Railway staging
- [x] All datasources verified
- [x] All dashboards load without errors
- [x] No console errors

## Changes
- `grafana/dashboards/models-monitoring.json` - New dashboard
- `prometheus/prom.yml` - Added staging endpoint
- `tempo/tempo.yml` - Fixed frontend_address
- `loki/loki.yml` - Fixed instance_addr
- `grafana/dashboards/loki-logs.json` - Fixed queries
- Documentation files added

## Verification Steps
1. Run `docker-compose up`
2. Access Grafana at http://localhost:3000
3. Verify all datasources
4. Check all dashboards load
```

### Step 6: Merge to Main
After PR approval:
```bash
git checkout main
git pull origin main
git merge staging/models-and-fixes
git push origin main
```

---

## Current Status

### Staging Branch: `staging/models-and-fixes`

**Changes Included:**
1. ✅ Models Monitoring Dashboard (11 panels)
2. ✅ Prometheus staging endpoint configuration
3. ✅ Tempo Railway fixes (frontend_address)
4. ✅ Loki Railway fixes (instance_addr)
5. ✅ Loki dashboard query fixes
6. ✅ Datasource configuration documentation
7. ✅ System health check documentation
8. ✅ Tempo local debug guide

**Status:** Ready for local testing

---

## Testing Checklist

### Local Testing (Docker Compose)

```bash
# 1. Start services
docker-compose down -v
docker-compose build --no-cache
docker-compose up

# 2. Wait for all services to be ready (2-3 minutes)

# 3. Verify Prometheus
curl http://localhost:9090/api/v1/targets
# Expected: All targets should show "up": true

# 4. Verify Loki
curl http://localhost:3100/loki/api/v1/status/buildinfo
# Expected: Returns build info

# 5. Verify Tempo
curl http://localhost:3200/status
# Expected: {"status":"ok"}

# 6. Verify Grafana
curl http://localhost:3000/api/health
# Expected: Returns health status

# 7. Access Grafana
# Open http://localhost:3000 in browser
# Login: admin / yourpassword123

# 8. Check Datasources
# Go to Configuration → Data Sources
# Verify each shows "Data source is working"

# 9. Check Dashboards
# Go to Dashboards
# Verify each dashboard loads without errors
# Check browser console (F12) for errors
```

### Railway Testing

```bash
# 1. Push staging branch
git push origin staging/models-and-fixes

# 2. In Railway Dashboard:
#    - Create deployment from staging/models-and-fixes
#    - Set environment variables
#    - Deploy

# 3. Wait for services to start (2-3 minutes)

# 4. Access Grafana at Railway URL

# 5. Verify datasources

# 6. Check dashboards

# 7. Monitor logs for errors
```

---

## Common Issues During Testing

### Issue: Services won't start
**Solution:** 
- Check Docker is running
- Run `docker-compose down -v` to clean up
- Check port conflicts: `lsof -i :3000,3100,3200,9090`

### Issue: Datasources show "Data source is working" but no data
**Solution:**
- This is expected if backend isn't emitting metrics/logs/traces
- Verify datasource URLs are correct
- Check service logs: `docker-compose logs <service>`

### Issue: Tempo dashboard shows errors
**Solution:**
- Check browser console for specific errors
- Verify Tempo is running: `curl http://localhost:3200/status`
- Check Tempo logs: `docker-compose logs tempo`

### Issue: Loki dashboard shows errors
**Solution:**
- Check Loki is running: `curl http://localhost:3100/loki/api/v1/status/buildinfo`
- Verify queries don't use `$__rate_interval`
- Check Loki logs: `docker-compose logs loki`

---

## Merging to Main

### Before Merging
- [ ] All local tests pass
- [ ] All Railway tests pass
- [ ] No console errors in Grafana
- [ ] All datasources verified
- [ ] All dashboards load correctly
- [ ] PR reviewed and approved

### Merge Process
```bash
# 1. Ensure staging branch is up to date
git checkout staging/models-and-fixes
git pull origin staging/models-and-fixes

# 2. Create PR on GitHub
# (Use GitHub web interface)

# 3. After approval, merge to main
git checkout main
git pull origin main
git merge staging/models-and-fixes
git push origin main

# 4. Delete staging branch (optional)
git push origin --delete staging/models-and-fixes
```

---

## Documentation Files Added

1. **MODELS_MONITORING_SETUP.md** - Models monitoring dashboard setup
2. **RAILWAY_DEPLOYMENT_VERIFICATION.md** - Railway deployment guide
3. **DATASOURCE_URL_CONFIGURATION.md** - Datasource configuration
4. **SYSTEM_HEALTH_CHECK.md** - Complete system health verification
5. **TEMPO_LOCAL_DEBUG.md** - Tempo debugging guide
6. **STAGING_WORKFLOW.md** - This file

---

## Next Steps

1. **Local Testing**
   - Run `docker-compose up`
   - Verify all services and dashboards
   - Document any issues found

2. **Railway Testing**
   - Push staging branch
   - Deploy to Railway
   - Verify all services and dashboards
   - Document any issues found

3. **Fix Issues**
   - Create fixes on staging branch
   - Test locally and on Railway
   - Repeat until all issues resolved

4. **Create PR**
   - Push final staging branch
   - Create PR with summary of changes
   - Request review

5. **Merge to Main**
   - After approval, merge to main
   - Monitor main branch deployment

---

## Branch Management

### Active Branches
- `main` - Production-ready code
- `staging/models-and-fixes` - Testing branch (current)

### Branch Lifecycle
1. Create feature/fix branch from main
2. Develop and test locally
3. Create staging branch for integration testing
4. Test on Railway staging
5. Create PR from staging to main
6. After approval, merge to main
7. Delete staging branch

---

## Communication

### When Testing
- Document all findings
- Note any errors or issues
- Record verification steps
- Keep track of what works and what doesn't

### When Creating PR
- Summarize all changes
- Include testing results
- Provide verification steps
- Request specific reviewers if needed

### When Merging
- Ensure all tests pass
- Verify no conflicts
- Monitor deployment
- Check for any issues post-merge

---

## Summary

**Staging Branch:** `staging/models-and-fixes`

**Ready for:**
1. Local testing with docker-compose
2. Railway staging deployment
3. PR creation and review
4. Merge to main after verification

**Testing should verify:**
- All services start correctly
- All datasources connect
- All dashboards load
- No console errors
- Queries execute without errors
- Data flows correctly (once backend instrumentation is added)

Once all testing is complete and verified, create a PR and request review before merging to main.
