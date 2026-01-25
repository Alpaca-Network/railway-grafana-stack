# Quick Reference: Prometheus → Mimir Integration

## 🚀 Quick Start (3 Steps)

### 1. Set Environment Variable on Railway ⚠️ REQUIRED
```
Railway Dashboard → Prometheus Service → Variables → Add:
Key: RAILWAY_ENVIRONMENT
Value: production
```
**Wait 2-3 minutes for redeploy**

### 2. Check Logs
```bash
railway logs --service prometheus | grep "MIMIR_URL"
```
**Expected**: `MIMIR_URL: http://mimir.railway.internal:9009`

### 3. Verify Data Flow (after 5 minutes)
```bash
# Run diagnostic
./railway-grafana-stack/quick-setup.sh

# OR check metrics manually
# Visit: https://prometheus-{project}.railway.app
# Go to: Status → TSDB Status → Remote Write
# Samples Sent should be > 0
```

---

## 📊 Verification Queries

### On Prometheus UI (https://prometheus-{project}.railway.app)

```promql
# Check remote write is sending data
prometheus_remote_storage_samples_total

# Check if samples are failing
prometheus_remote_storage_samples_failed_total

# Check Mimir is ingesting
cortex_ingester_ingested_samples_total

# Check active series in Mimir
cortex_ingester_active_series

# Check remote write queue
prometheus_remote_storage_samples_pending
```

---

## 🔍 Diagnostic Commands

```bash
# Run full diagnostic
railway run --service prometheus bash /app/diagnose-prometheus-mimir.sh

# Test DNS resolution
railway run --service prometheus -- nslookup mimir.railway.internal

# Test Mimir health
railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready

# Check Prometheus config
railway logs --service prometheus | grep -A5 "remote_write"

# Interactive setup wizard
cd railway-grafana-stack && ./quick-setup.sh
```

---

## 🐛 Common Issues & Quick Fixes

### Issue: "MIMIR_URL shows http://mimir:9009" (WRONG)
**Fix**: Set `RAILWAY_ENVIRONMENT=production` on Prometheus service, wait 2 minutes

### Issue: "Connection refused to mimir.railway.internal:9009"
**Fix**: Check Mimir is running:
```bash
railway logs --service mimir | tail -20
```
Look for: `server listening on [::]:9009`

### Issue: "Samples Sent = 0"
**Fix**: Check Prometheus targets are UP:
- Visit: https://prometheus-{project}.railway.app/targets
- All targets should be green
- If red, check bearer tokens or target URLs

### Issue: "DNS lookup failed: mimir.railway.internal"
**Fix**: Verify Mimir service name in Railway Dashboard is exactly "mimir"
Alternative: Use external URL temporarily:
```
MIMIR_INTERNAL_URL=https://mimir-{project}.railway.app
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `prometheus/prom.yml` | Prometheus config (remote_write on lines 13-23) |
| `prometheus/entrypoint.sh` | URL substitution logic (lines 42-56) |
| `prometheus/Dockerfile` | Prometheus image build |
| `mimir/mimir-railway.yml` | Mimir single-instance config |
| `mimir/entrypoint.sh` | Mimir startup script |
| `grafana/datasources/datasources.yml` | Grafana datasources (includes Mimir) |
| `grafana/dashboards/mimir/mimir.json` | Mimir monitoring dashboard |

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| `SETUP_COMPLETE.md` | Complete summary of what was done |
| `NEXT_STEPS.md` | Detailed deployment guide |
| `MIMIR.md` | Mimir architecture and API reference |
| `PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md` | Railway-specific setup |
| `DATA_FLOW_VERIFICATION.md` | Verification procedures |
| `PROMETHEUS_MIMIR_CONNECTION_FIXES.md` | Troubleshooting guide |

---

## 🎯 Success Criteria

✅ **Working when:**
1. Prometheus logs show: `MIMIR_URL: http://mimir.railway.internal:9009`
2. Query `prometheus_remote_storage_samples_total` returns > 0 (increasing)
3. Query `cortex_ingester_ingested_samples_total` returns > 0
4. Grafana → Explore → Mimir datasource → Query `up` returns data
5. Mimir dashboard shows metrics in all panels

---

## ⏱️ Expected Timeline

| Time | Event |
|------|-------|
| T+0 | Set `RAILWAY_ENVIRONMENT=production` |
| T+30s | Railway triggers redeploy |
| T+2m | Prometheus starts with new config |
| T+2m 15s | First remote_write to Mimir |
| T+3m | Logs show successful writes |
| T+5m | Mimir metrics show ingestion |
| T+5m | Grafana can query Mimir data |

---

## 🔗 Quick Links

- **Railway Dashboard**: https://railway.app/dashboard
- **Prometheus UI**: https://prometheus-{project}.railway.app
- **Grafana**: https://grafana-{project}.railway.app
- **Mimir API**: https://mimir-{project}.railway.app

---

## 💡 Pro Tips

1. **Check logs first** - Most issues show up in logs
2. **Wait 5 minutes** - Metrics need time to accumulate
3. **Use diagnostic script** - `./quick-setup.sh` or `diagnose-prometheus-mimir.sh`
4. **Check Railway status** - https://railway.statuspage.io/
5. **Monitor resource usage** - Railway Dashboard → Service → Metrics

---

## 📞 Need Help?

1. Run: `./quick-setup.sh` (interactive troubleshooting)
2. Check: `NEXT_STEPS.md` (detailed guide)
3. Review: `PROMETHEUS_MIMIR_CONNECTION_FIXES.md` (common fixes)
4. Look at: `SETUP_COMPLETE.md` (complete summary)

---

**Last Updated**: January 25, 2026  
**Status**: Ready for deployment testing
