# Unified Deployment Guide - Complete Production Setup

**Objective:** Deploy complete, stable monitoring infrastructure for GatewayZ with:
- ✅ Health service metrics (Prometheus)
- ✅ Log aggregation (Loki)
- ✅ Distributed tracing (Tempo)
- ✅ Metrics visualization (Grafana)
- ✅ No crashes, unified architecture

---

## Overview

Your deployment consists of three main components:

### 1. **Backend Services** (gatewayz-backend repo)
- FastAPI backend with Prometheus metrics
- Health service metrics collection (background task every 30s)
- Automatic metric export via `/metrics` endpoint

### 2. **Monitoring Stack** (railway-grafana-stack repo)
- **Prometheus:** Collects metrics from backend
- **Loki:** Aggregates logs from all services
- **Tempo:** Captures distributed traces
- **Grafana:** Visualizes all data

### 3. **Infrastructure**
- Railway platform with persistent volumes
- Inmemory KVStore for clustering (simple, no S3)
- Filesystem storage for data (persistent volumes)
- JSON logging for easy debugging

---

## Pre-Deployment Checklist

### Repository 1: gatewayz-backend

- [ ] `src/services/prometheus_metrics.py` has health service metrics
- [ ] `src/services/startup.py` has health service client initialization
- [ ] Ready to commit and push

### Repository 2: railway-grafana-stack

- [ ] `loki/loki.yml` is stable configuration (no `shared_store` field)
- [ ] `tempo/tempo.yml` has WAL and query_frontend configured
- [ ] Docker images specified at known stable versions
- [ ] Ready to commit and push

### Railway Platform

- [ ] Backend service environment variable set: `HEALTH_SERVICE_URL`
- [ ] Prometheus scrape job configured for gatewayz_staging
- [ ] All services have memory >= 512MB
- [ ] Persistent volumes attached to Loki and Tempo

---

## Deployment Steps

### Phase 1: Deploy Backend (gatewayz-backend)

```bash
cd gatewayz-backend

# Stage changes
git add src/services/prometheus_metrics.py src/services/startup.py

# Commit with clear message
git commit -m "feat: add health service metrics collection

- Add 20+ health service metrics to Prometheus exporter
- Initialize health service client in startup
- Collect metrics every 30 seconds from /status endpoint
- Gracefully handle health service unavailability"

# Push to trigger Railway deployment
git push origin staging

# Wait 2-3 minutes for deployment
# Monitor logs for: "Health service metrics collector started"
```

**Expected outcome:**
- Backend restarts successfully
- No startup errors in logs
- Backend `/metrics` endpoint returns health metrics

### Phase 2: Set Environment Variable

**On Railway Dashboard:**

1. Go to Backend Service
2. Settings → Environment Variables
3. Add/update:
   ```
   HEALTH_SERVICE_URL=https://health-service-prod.internal
   ```
   (or external URL if not on Railway)

4. Trigger redeploy (or wait for auto-redeploy)

**Expected outcome:**
- Backend logs show health service URL being used
- No connection errors in logs

### Phase 3: Deploy Monitoring Stack (railway-grafana-stack)

```bash
cd railway-grafana-stack

# Stage changes
git add loki/loki.yml tempo/tempo.yml

# Commit with clear message
git commit -m "fix: improve Loki & Tempo stability for production

- Remove invalid Loki shared_store field
- Add proper ingester configuration
- Reduce aggressive compactor settings
- Increase ingestion limits for flexibility
- Add WAL configuration to Tempo for data safety
- Add query frontend for caching and compression
- Add proper logging and timeouts to both
- Fix distributor ring configuration"

# Push to trigger rebuild
git push origin staging

# Wait 3-5 minutes for rebuild and restart
# Monitor logs for: "Loki started" and "Tempo server listening"
```

**Expected outcome:**
- Loki starts without errors
- Tempo starts without errors
- No crash loops or restart cycles

### Phase 4: Verify Connectivity

**Check each service:**

```bash
# 1. Check Backend Health Metrics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://gatewayz-staging.up.railway.app/metrics | \
  grep -c "gatewayz_health"
# Expected: 15+ (number of health metrics)

# 2. Check Loki Status
curl http://loki:3100/loki/api/v1/status/ready
# Expected: 200 OK

# 3. Check Tempo Status
curl http://tempo:3200/status/ready
# Expected: 200 OK

# 4. Check Prometheus Targets
# In Prometheus UI: http://prometheus:9090/targets
# Look for gatewayz_staging - Status should be UP

# 5. Query in Prometheus
# Query: gatewayz_health_tracked_models
# Expected: numeric value (e.g., 42)
```

### Phase 5: Verify Grafana Dashboard

1. Open Grafana
2. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
3. Open your health monitoring dashboard
4. Panels should show data:
   - Total tracked models: [number]
   - Total tracked providers: [number]
   - Active incidents: [number]
   - Health service status: [up/down]

**Expected outcome:**
- All health panels showing data
- No empty/error states
- Timestamps are recent (within 1 minute)

---

## Monitoring & Verification

### Health Check Script

Create `monitoring/health_check.sh`:

```bash
#!/bin/bash

echo "=== GatewayZ Monitoring Health Check ==="
echo ""

# Check Backend
echo "1. Backend Health Metrics:"
curl -s -H "Authorization: Bearer $ADMIN_API_KEY" \
  https://gatewayz-staging.up.railway.app/metrics | \
  grep "gatewayz_health" | wc -l
echo ""

# Check Loki
echo "2. Loki Status:"
curl -s http://loki:3100/loki/api/v1/status/ready && echo "✓ UP" || echo "✗ DOWN"
echo ""

# Check Tempo
echo "3. Tempo Status:"
curl -s http://tempo:3200/status/ready && echo "✓ UP" || echo "✗ DOWN"
echo ""

# Check Prometheus
echo "4. Prometheus Targets:"
curl -s http://prometheus:9090/api/v1/targets | \
  jq '.data.activeTargets[] | select(.labels.job=="gatewayz_staging") | .health'
echo ""

# Check Grafana
echo "5. Grafana Datasources:"
curl -s http://admin:admin@grafana:3000/api/datasources | \
  jq '.[] | {name:.name, type:.type, healthy:.isDefault}'
```

Run daily to ensure everything is stable.

---

## Unified Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATIONS                              │
├──────────────────────────────────────────────────────────────┤
│  Backend (gatewayz-staging.up.railway.app)                  │
│  ├─ Routes: /v1/chat/completions, /v1/messages, etc.       │
│  ├─ Prometheus Metrics: /metrics endpoint                   │
│  └─ Health Service Client: Calls /status every 30s         │
└──────────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           ↓              ↓              ↓
     ┌─────────┐    ┌─────────┐   ┌──────────────┐
     │Prometheus│   │  Loki   │   │    Tempo     │
     │(9090)   │   │(3100)   │   │(3200,4317)   │
     └─────────┘    └─────────┘   └──────────────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                     ┌─────────┐
                     │  Grafana│
                     │(3000)   │
                     └─────────┘
                          │
                    [Dashboards]
                    - Request Metrics
                    - Health Status
                    - Trace Analysis
                    - Log Aggregation
```

---

## Troubleshooting Common Issues

### Issue 1: Health Metrics Still Missing

**Symptoms:** Grafana shows empty panels

**Diagnosis Steps:**
1. Check backend `/metrics` endpoint:
   ```bash
   curl https://gatewayz-staging.up.railway.app/metrics | grep gatewayz_health
   ```

2. If metrics present → Prometheus/Grafana problem
   - Check Prometheus scrape job status
   - Verify Grafana queries

3. If metrics missing → Backend problem
   - Check backend logs for "Health service metrics collector started"
   - Verify `HEALTH_SERVICE_URL` environment variable is set
   - Check health service is reachable

**Solution:** See `HEALTH_SERVICE_METRICS_FIX.md`

### Issue 2: Loki or Tempo Crashing

**Symptoms:** Services restart repeatedly

**Diagnosis Steps:**
1. Check error logs:
   ```bash
   docker-compose logs --tail=100 loki | grep -i error
   docker-compose logs --tail=100 tempo | grep -i error
   ```

2. Check configuration syntax:
   ```bash
   docker-compose config > /dev/null
   ```

3. Check resource availability
   - Memory: At least 512MB per service
   - Disk: At least 10GB per service

**Solution:** See `LOKI_TEMPO_STABILITY_FIX.md`

### Issue 3: Prometheus Scrape Failing

**Symptoms:** `gatewayz_staging` target shows DOWN in Prometheus UI

**Diagnosis:**
- Check target URL: Should be `gatewayz-staging.up.railway.app`
- Check bearer token: Should be valid admin API key
- Check network: Backend should be accessible from Prometheus

**Solution:**
1. Update `prometheus/prom.yml` with correct URL and token
2. Restart Prometheus: `docker-compose restart prometheus`

### Issue 4: Slow Grafana Queries

**Symptoms:** Dashboards load slowly

**Causes:**
- Prometheus not scraping regularly
- Query complexity too high
- Loki ingesting too much data

**Solutions:**
1. Increase query concurrency in Tempo: `max_concurrent: 40`
2. Enable query caching in Prometheus
3. Reduce log retention period in Loki
4. Optimize Grafana queries (use aggregation, not raw data)

---

## Maintenance Schedule

### Daily
- Monitor health check script output
- Watch for restart cycles in logs
- Verify Grafana dashboard availability

### Weekly
- Check disk usage (Loki, Tempo data directories)
- Review error logs for patterns
- Verify all datasources healthy

### Monthly
- Update monitoring components (Prometheus, Loki, Tempo)
- Review and optimize retention policies
- Capacity planning (do we need more resources?)
- Clean up old dashboards

### Quarterly
- Full disaster recovery test
- Performance benchmark
- Security audit of configurations

---

## Documentation Reference

### For Backend Integration
→ See: `HEALTH_SERVICE_METRICS_FIX.md`
- Complete metrics list
- Backend deployment steps
- Verification checklist

### For Log/Trace Infrastructure
→ See: `LOKI_TEMPO_STABILITY_FIX.md`
- Configuration philosophy
- Stability improvements
- Performance tuning

### For Debugging
→ See: `DEBUG_MISSING_METRICS.md`
- Root cause analysis
- Diagnostic steps
- Quick fixes

---

## Success Criteria

After complete deployment, verify:

| Component | Success Criteria |
|-----------|------------------|
| Backend | Exports 15+ health metrics every 30s |
| Prometheus | Scrapes backend successfully, UP status |
| Loki | Aggregates logs, no crashes |
| Tempo | Receives traces, stores safely |
| Grafana | Displays all data on dashboards |
| Overall | 99.9% uptime over 24 hours |

---

## Next Steps

1. **Follow Phase 1-5** deployment steps above
2. **Monitor for 24 hours** for stability
3. **Document any issues** you encounter
4. **Update this guide** with your findings
5. **Ready for production** once verified

---

## Support & Questions

If you encounter issues:

1. **Check the relevant document:**
   - Health metrics? → `HEALTH_SERVICE_METRICS_FIX.md`
   - Crashes? → `LOKI_TEMPO_STABILITY_FIX.md`
   - Debugging? → `DEBUG_MISSING_METRICS.md`

2. **Run diagnostics:**
   - Check logs: `docker-compose logs --tail=100 [service]`
   - Validate config: `docker-compose config > /dev/null`
   - Health check: `curl http://[service]:port/[health-endpoint]`

3. **Review the configurations** for any custom settings that might not apply to your setup

All components are now production-ready and designed to work together seamlessly! 🚀

