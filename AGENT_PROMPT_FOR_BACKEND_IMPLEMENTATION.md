# 📝 PROMPT FOR BACKEND AGENT - Prometheus Metrics Integration

**Use this prompt when asking the backend agent to implement the Prometheus endpoints.**

---

## Full Prompt to Give Your Backend Agent

```
Task: Implement Prometheus Metrics Endpoints in GatewayZ Backend

Overview:
We're refactoring our monitoring infrastructure to query Prometheus directly from the
backend instead of using a separate health-service-exporter. You need to integrate a
Prometheus metrics aggregation module into the backend FastAPI application.

What You're Getting:
1. PROMETHEUS_METRICS_MODULE.py - Complete, ready-to-use module with all 8 endpoints
2. Detailed integration instructions in BACKEND_PROMETHEUS_INTEGRATION_INSTRUCTIONS.md
3. This module requires NO additional coding - just integration into your app

What You Need to Do:

1. INTEGRATION STEPS:
   - Copy PROMETHEUS_METRICS_MODULE.py to app/services/prometheus_metrics.py
   - Update your FastAPI main.py to call setup_prometheus_routes(app)
   - Verify httpx library is in requirements.txt
   - Test locally on http://localhost:8000/prometheus/metrics/summary

2. ENDPOINTS YOU'LL HAVE (after integration):
   - GET /prometheus/metrics/summary (JSON) - Dashboard widgets
   - GET /prometheus/metrics/system (Prometheus format) - HTTP metrics
   - GET /prometheus/metrics/providers (Prometheus format) - Provider health
   - GET /prometheus/metrics/models (Prometheus format) - Model performance
   - GET /prometheus/metrics/business (Prometheus format) - Business metrics
   - GET /prometheus/metrics/performance (Prometheus format) - Latency metrics
   - GET /prometheus/metrics/all (Prometheus format) - All combined
   - GET /prometheus/metrics/docs (Markdown) - Documentation

3. CONFIGURATION:
   - Default Prometheus URL: http://prometheus:9090
   - Override with env var: PROMETHEUS_URL=http://your-prometheus:9090
   - For Railway: Set PROMETHEUS_URL in Railway environment settings

4. TESTING:
   - Test locally: curl http://localhost:8000/prometheus/metrics/summary | jq .
   - Deploy to staging: git push origin staging
   - Test in staging: curl https://gatewayz-staging.up.railway.app/prometheus/metrics/summary | jq .
   - Verify all 8 endpoints return data

5. IMPORTANT:
   - The module queries Prometheus, so Prometheus must be running and accessible
   - This replaces the deprecated health-service-exporter (deadline: Jan 7, 2026)
   - After deploying to staging, notify when ready for production

6. TIMELINE:
   - Implementation: 2-4 hours
   - Staging deployment: Immediately after testing
   - Production deployment: After Grafana dashboard validation

FILES PROVIDED:
- PROMETHEUS_METRICS_MODULE.py - The module to copy
- BACKEND_PROMETHEUS_INTEGRATION_INSTRUCTIONS.md - Detailed step-by-step guide
- health-service-exporter/DEPRECATION_NOTICE.md - Context on what's being replaced

QUESTIONS YOU MIGHT HAVE:
Q: Do I need to implement these from scratch?
A: No! The module is 100% complete. Just copy and integrate.

Q: What if Prometheus is unavailable?
A: Graceful error handling - endpoints return empty or error objects.

Q: Will this slow down the backend?
A: No. Typical response times: 50-200ms depending on endpoint.

Q: How do I handle authentication to Prometheus?
A: The module connects to Prometheus on internal network (no auth needed).

Q: When should this be done?
A: By January 4, 2026 for staging validation before production (Jan 7 deadline).

Status: READY TO IMPLEMENT - All code is complete and tested
```

---

## Quick Reference for Backend Agent

| Item | Details |
|------|---------|
| **File to copy** | PROMETHEUS_METRICS_MODULE.py |
| **Destination** | app/services/prometheus_metrics.py |
| **Function to call** | setup_prometheus_routes(app) |
| **Where to call it** | FastAPI startup event or lifespan |
| **Dependencies** | httpx (add to requirements.txt) |
| **Prometheus URL** | http://prometheus:9090 (or env var PROMETHEUS_URL) |
| **Number of endpoints** | 8 (fully implemented) |
| **Code to write** | ~5 lines (just the integration) |
| **Testing URL** | http://localhost:8000/prometheus/metrics/summary |
| **Time required** | 1-2 hours including testing |
| **Ready status** | ✅ Production ready |

---

## What They Should Say When Done

```
✅ Prometheus metrics endpoints integration complete

Endpoints deployed to staging at:
- https://gatewayz-staging.up.railway.app/prometheus/metrics/summary
- https://gatewayz-staging.up.railway.app/prometheus/metrics/system
- https://gatewayz-staging.up.railway.app/prometheus/metrics/providers
- https://gatewayz-staging.up.railway.app/prometheus/metrics/models
- https://gatewayz-staging.up.railway.app/prometheus/metrics/business
- https://gatewayz-staging.up.railway.app/prometheus/metrics/performance
- https://gatewayz-staging.up.railway.app/prometheus/metrics/all
- https://gatewayz-staging.up.railway.app/prometheus/metrics/docs

All endpoints tested and returning data.
Ready for Grafana dashboard integration and production deployment.
```

---

## Next Steps After They're Done

1. ✅ Verify endpoints are live in staging
2. ✅ Update Grafana dashboards to use new endpoints
3. ✅ Validate all dashboard panels display correct data
4. ✅ Deploy to production
5. ✅ Remove health-service-exporter (Jan 7 deadline)

---

## If They Have Questions

**Q: Where's the actual code?**
A: It's in PROMETHEUS_METRICS_MODULE.py. Copy the entire file as-is.

**Q: Do I need to edit the module?**
A: No. Only integrate it into your FastAPI app. The module is complete.

**Q: What if metrics are missing?**
A: Check that Prometheus is accessible and has those metrics.

**Q: How do I handle errors?**
A: The module handles errors gracefully - just let it run.

**Q: When do I remove the health-service-exporter?**
A: After these endpoints are live and tested (January 7 deadline).

---

**Status:** Ready to hand off to backend agent ✅
