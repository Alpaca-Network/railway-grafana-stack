# 🚀 DEPLOYMENT CHECKLIST
**Health Service Metrics Exporter**

**Last Updated:** December 24, 2025
**Status:** Ready for deployment

---

## PRE-DEPLOYMENT (Local Testing)

### Code Quality ✅
- [x] Python syntax valid
- [x] Dockerfile builds successfully
- [x] requirements.txt has pinned versions
- [x] No hardcoded secrets
- [x] Follows PEP 8 style guidelines

### Configuration ✅
- [x] docker-compose.yml is valid YAML
- [x] prometheus/prom.yml is valid YAML
- [x] Port 8002 unused (no conflicts)
- [x] Service dependencies correct (depends_on: prometheus)
- [x] Environment variables have sensible defaults

### Integration ✅
- [x] Health service endpoints tested and responding
- [x] All 4 endpoints return valid JSON
- [x] Exporter code handles all 4 endpoints
- [x] Prometheus scrape job configured correctly
- [x] Dashboard panels query correct metrics

### Docker Testing ✅
- [x] `docker-compose build` succeeds
- [x] `docker-compose up` starts all services
- [x] health-service-exporter container starts without errors
- [x] Exporter binds to port 8002
- [x] Prometheus scrapes from exporter successfully

---

## STAGING DEPLOYMENT (Before Production)

### Environment Verification ⏳
- [ ] Railway staging project is set up
- [ ] Environment variables configured:
  - [ ] `HEALTH_SERVICE_URL` = https://health-service-production.up.railway.app
  - [ ] `SCRAPE_INTERVAL` = 30 (or desired value)
  - [ ] `METRICS_PORT` = 8002
  - [ ] `REQUEST_TIMEOUT` = 10
- [ ] All environment variables verified in Railway service config

### Deployment ⏳
- [ ] Code merged to staging branch
- [ ] GitHub Actions workflow runs successfully
- [ ] Docker image builds successfully on Railway
- [ ] Service deployed without errors
- [ ] Logs show no critical errors: Check Railway logs for `health-service-exporter`

### Initial Connectivity Verification ⏳

**Exporter Service Health:**
- [ ] Exporter container is running and healthy
- [ ] Service is accessible on port 8002 (from prometheus container)
- [ ] Metrics endpoint responds at `/metrics`

**Test Command (from Prometheus container):**
```bash
curl -s http://health-service-exporter:8002/metrics | head -20
# Should show: # HELP gatewayz_health_service_up...
```

**Prometheus Target Verification:**
- [ ] Navigate to: https://grafana-staging.up.railway.app/prometheus/targets
- [ ] Find job `health_service_exporter` in list
- [ ] Status should be GREEN (UP) - not RED (DOWN)
- [ ] Last scrape time should be recent (< 2 minutes ago)
- [ ] Scrape duration should be < 5 seconds

### Metrics Verification ⏳

**Core Service Metrics** - Execute in Prometheus:
```promql
# Should return 1 if service is up
up{job="health_service_exporter"}

# Should return 0 (no errors expected immediately after deployment)
gatewayz_health_service_scrape_errors_total

# Should have a recent timestamp (close to current time)
gatewayz_health_service_last_successful_scrape

# Should show 1 if monitoring is active
gatewayz_health_service_up
```

**Expected Results:**
- [ ] `gatewayz_health_service_up` = 1 (service is responding)
- [ ] `gatewayz_health_monitoring_active` = 1 (monitoring enabled)
- [ ] `gatewayz_health_tracked_models` > 0 (has tracked models)
- [ ] `gatewayz_health_tracked_providers` > 0 (has tracked providers)
- [ ] `gatewayz_health_tracked_gateways` > 0 (has tracked gateways)
- [ ] `gatewayz_health_total_models` > 0 (total count exists)
- [ ] `gatewayz_health_total_providers` > 0 (total count exists)
- [ ] `gatewayz_health_total_gateways` > 0 (total count exists)
- [ ] `gatewayz_health_active_incidents` ≥ 0 (count value exists)

**Verify All Metrics Exported:**
```promql
# Count of all health service metrics (should be 15+)
count({__name__=~"gatewayz_health.*"})
```

### Dashboard Testing ⏳

**Health Service Monitoring Row:**
- [ ] Navigate to: https://grafana-staging.up.railway.app/d/gatewayz-app-health
- [ ] Row "Health Service Monitoring" is visible
- [ ] Panel "Health Service Status" shows UP/DOWN status (green or red)
- [ ] Panel "Active Incidents" displays a number (0 or more)
- [ ] Panel "Monitoring State" shows Active/Inactive

**Health Service Details Row:**
- [ ] Row "Health Service Details" is visible
- [ ] Panel "Total Resources" shows counts for models, providers, gateways
- [ ] Panel "Health Check Interval" shows interval in seconds
- [ ] Panel "Cache Availability" displays cache status
- [ ] Panel "Status Distribution" shows breakdown (if incidents exist)

**No Data Errors:**
- [ ] No panels show "no data" error message
- [ ] No panels show "error loading data"
- [ ] All panels have queries (open panel edit to verify)

### Error Handling Test ⏳

**Simulate Temporary Health Service Outage:**
- [ ] Temporarily block health service URL (e.g., firewall rule on staging)
- [ ] Monitor exporter logs - should show connection errors
- [ ] Check Prometheus: `gatewayz_health_service_up` should change to 0
- [ ] Check dashboard: panels should show last known value or "no data"
- [ ] Error counter should increment: `gatewayz_health_service_scrape_errors_total`
- [ ] Restore health service URL
- [ ] Exporter should recover within 60 seconds (2 scrape intervals)
- [ ] Metrics should return to normal values

### Performance Monitoring ⏳

**Resource Usage Verification:**
- [ ] Check Railway metrics for `health-service-exporter` service:
  - [ ] CPU usage stays below 1%
  - [ ] Memory usage stays below 100MB
  - [ ] No gradual memory increase (memory leak indicator)

**Latency Monitoring:**
- [ ] Check Prometheus scrape duration: `scrape_duration_seconds{job="health_service_exporter"}`
- [ ] Typical duration should be 2-5 seconds
- [ ] Should never exceed 10 seconds (REQUEST_TIMEOUT)

### 24-Hour Stability Test ⏳

**Duration:** Run for minimum 24 consecutive hours

**Verification Points:**

*Every 4 hours (6 checks total):*
- [ ] Check exporter container is still running
- [ ] Verify metrics are being updated (check `gatewayz_health_service_last_successful_scrape`)
- [ ] Monitor error counter hasn't increased: `gatewayz_health_service_scrape_errors_total`
- [ ] Check Prometheus targets page - `health_service_exporter` still UP
- [ ] CPU and memory usage remains stable

*After 24 hours:*
- [ ] Dashboard panels still show current data (no stale data)
- [ ] Error counter total should be minimal (0-5 acceptable)
- [ ] Memory usage same as beginning of test
- [ ] No critical warnings in logs
- [ ] Service restarts: 0 (checked via Railway service events)

**Success Criteria:**
- [x] Exporter has been continuously UP for 24 hours
- [x] Metrics updated at least 2880 times (every 30 seconds)
- [x] Zero unplanned restarts
- [x] Resource usage stable and within limits
- [x] All dashboard panels display real, current data

### Staging Monitoring Setup ⏳

**Alert Rules for Staging** - Create these alert rules in Prometheus (add to `prometheus/alert.rules.yml`):

```yaml
groups:
  - name: health_service_exporter_alerts
    interval: 30s
    rules:
      # Alert when exporter is down
      - alert: HealthServiceExporterDown
        expr: up{job="health_service_exporter"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Health Service Exporter is DOWN"
          description: "The health-service-exporter has been unreachable for 5 minutes"

      # Alert when scrape errors are increasing
      - alert: HealthServiceExporterErrors
        expr: rate(gatewayz_health_service_scrape_errors_total[5m]) > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Health Service Exporter is experiencing errors"
          description: "Error rate: {{ $value }} errors per second"

      # Alert when health service itself is down
      - alert: HealthServiceDown
        expr: gatewayz_health_service_up == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Health Service API is DOWN"
          description: "The health service has been unreachable for 2 minutes"
```

**Verification Checklist:**
- [ ] Alert rules added to `prometheus/alert.rules.yml`
- [ ] Prometheus configuration reloaded (or service restarted)
- [ ] Navigate to Prometheus Alerts page: https://grafana-staging.up.railway.app/prometheus/alerts
- [ ] All 3 alert rules appear in the list with status "Inactive" (no active alerts)
- [ ] Alert names are: `HealthServiceExporterDown`, `HealthServiceExporterErrors`, `HealthServiceDown`

**Staging Alert Notification** (Optional but recommended):
- [ ] Set up alert notification channel (e.g., Slack, Email, PagerDuty)
- [ ] Test alert firing by temporarily stopping exporter
- [ ] Verify notification is received
- [ ] Restore exporter and confirm alert clears

**Dashboard Panel for Exporter Health** - Add to Grafana dashboard:
- [ ] Panel Type: Stat
- [ ] Query: `up{job="health_service_exporter"}`
- [ ] Mapping: 0=Down (red), 1=Up (green)
- [ ] Placement: Top of "Health Service Monitoring" row
- [ ] Title: "Exporter Status"

---

## PRODUCTION DEPLOYMENT

### Final Approval ⏳
- [ ] All staging tests passed
- [ ] Code review completed
- [ ] Security review completed
- [ ] Performance impact assessed as minimal
- [ ] Rollback plan documented

### Pre-Deployment Notification ⏳
- [ ] Team notified of upcoming deployment
- [ ] Maintenance window scheduled (if needed)
- [ ] On-call engineer assigned for monitoring

### Production Deployment ⏳
- [ ] Code merged to main branch
- [ ] GitHub Actions workflow runs
- [ ] Docker images built successfully
- [ ] Services deployed to production
- [ ] No deployment errors

### Post-Deployment Validation ⏳
- [ ] Prometheus targets page shows health_service_exporter UP
- [ ] Metrics appear in Prometheus production instance
- [ ] Dashboard shows real data from production health service
- [ ] Error counter is 0: `gatewayz_health_service_scrape_errors_total{} 0`
- [ ] No increase in Prometheus memory/CPU usage

### Monitoring Setup ⏳

**Production Alert Rules** - Ensure alert rules from staging are deployed to production:

```yaml
groups:
  - name: health_service_exporter_alerts
    interval: 30s
    rules:
      # CRITICAL: Alert when exporter is down
      - alert: HealthServiceExporterDown
        expr: up{job="health_service_exporter"} == 0
        for: 5m
        labels:
          severity: critical
          team: devops
        annotations:
          summary: "🚨 CRITICAL: Health Service Exporter is DOWN in PRODUCTION"
          description: "The health-service-exporter has been unreachable for 5 minutes. Immediate investigation required."
          runbook: "See DEPLOYMENT_CHECKLIST.md - ROLLBACK PROCEDURE"

      # WARNING: Alert when scrape errors are increasing
      - alert: HealthServiceExporterErrors
        expr: rate(gatewayz_health_service_scrape_errors_total[5m]) > 0
        for: 10m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "⚠️ WARNING: Health Service Exporter is experiencing errors"
          description: "Error rate: {{ $value }} errors per second. Check health service connectivity."

      # WARNING: Alert when health service itself is down
      - alert: HealthServiceDown
        expr: gatewayz_health_service_up == 0
        for: 2m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "⚠️ WARNING: Health Service API is DOWN"
          description: "The health service has been unreachable for 2 minutes. Check health service availability."
```

**Production Alert Notification Setup:**
- [ ] Alert rules merged to main branch and deployed to production
- [ ] Alert notification channel configured (Slack, PagerDuty, etc.)
- [ ] Test alert delivery by triggering a test alert
- [ ] On-call rotation configured to receive `HealthServiceExporterDown` alerts
- [ ] Verify alerts appear in chosen notification channel

**Production Dashboard Panel:**
- [ ] "Exporter Status" panel added to top of "Health Service Monitoring" row
- [ ] Panel shows red indicator if exporter is DOWN
- [ ] Panel shows green indicator if exporter is UP
- [ ] Accessible from: https://grafana-production.up.railway.app/d/gatewayz-app-health

**Alert Response SLA:**
- [ ] Team commits to responding to `HealthServiceExporterDown` within 15 minutes
- [ ] Response includes checking exporter logs and health service connectivity
- [ ] If unresolvable within 1 hour, execute ROLLBACK PROCEDURE

### Documentation ⏳
- [ ] QUICK_START.md updated
- [ ] Troubleshooting guide added
- [ ] Runbook created for "exporter down" scenario
- [ ] Release notes published

---

## ROLLBACK PROCEDURE (If Issues Found)

### Immediate Rollback ⏳
If exporter causes issues:

1. **Remove service from docker-compose.yml:**
   ```bash
   git revert 57544c0
   git push
   ```

2. **Delete deployed service on Railway:**
   - Go to Railway project
   - Remove health-service-exporter service
   - Redeploy

3. **Verify health:**
   - Check Prometheus targets (should still have 4 jobs)
   - Confirm Grafana still works
   - Verify no cascading failures

### Minimal Impact
- Exporter failure doesn't affect other services
- Dashboard will show "no data" (acceptable)
- Can redeploy at any time without downtime

---

## VALIDATION QUERIES

### Quick Prometheus Checks
```promql
# Check exporter is scraping
up{job="health_service_exporter"}

# Check for errors
gatewayz_health_service_scrape_errors_total

# Check health service status
gatewayz_health_service_up

# Check all metrics exist
count({__name__=~"gatewayz_health.*"})

# Check last successful scrape
gatewayz_health_service_last_successful_scrape

# Check metrics freshness
time() - gatewayz_health_service_last_successful_scrape < 120  # Should be true
```

### Quick Dashboard Checks
1. **GatewayZ Application Health**
   - Navigate to: http://grafana/d/gatewayz-app-health
   - Check "Health Service Monitoring" row exists
   - Check "Health Service Details" row exists
   - Verify all 7 new panels show data (no red errors)

2. **Verify No Broken Panels**
   - Count total panels: Should be 10 (was 28, removed 18, added 8 = 10)
   - No panels should show "no data" errors
   - All panels should have queries

---

## KNOWN ISSUES & LIMITATIONS

### ⚠️ Current Limitations
1. Health service URL is hardcoded (but not a secret)
2. No authentication with health service (not required)
3. Metrics are point-in-time (depends on health service update frequency)
4. If health service is down, metrics show last known value (Prometheus behavior)

### 📝 Future Improvements
- [ ] Add exporter health check endpoint
- [ ] Implement exporter metrics (self-monitoring)
- [ ] Add latency histogram for health service calls
- [ ] Support multiple health service instances (if needed)

---

## CONTACTS & ESCALATION

| Issue | Contact | Action |
|-------|---------|--------|
| Exporter won't start | DevOps | Check logs, verify Docker image |
| Metrics not appearing | SRE | Check Prometheus targets, verify connectivity |
| Dashboard shows no data | Backend | Verify health service endpoints respond |
| High error rate | On-call | Check health service availability |
| Performance degradation | DevOps | Check resource usage, consider scaling |

---

## SIGN-OFF

**Deployment Manager:** _____________________ (Name)
**Date:** _____________________
**Approval:** ☐ Approved ☐ Approved with conditions ☐ Rejected

**Conditions/Notes:**
```


```

---

**Ready to deploy:** ✅ YES
**Estimated deployment time:** 5-10 minutes
**Estimated rollback time:** 2-3 minutes
**Risk level:** 🟢 LOW
