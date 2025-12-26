# ⚠️ DEPRECATION NOTICE

**Health Service Metrics Exporter**

**Status:** DEPRECATED (Scheduled for removal)

**Deprecation Date:** December 24, 2025

**Removal Date:** January 7, 2026 (2 weeks from deprecation)

---

## What's Changing

The `health-service-exporter` service is being **deprecated** and replaced with a direct integration in the backend application.

### Why?

1. **Simplified Architecture** - Remove intermediary exporter, query Prometheus directly from backend
2. **Better Scalability** - Backend controls metric aggregation based on Loki fixes
3. **Unified Endpoints** - All metrics served from single `/prometheus/metrics/*` endpoints
4. **Reduced Overhead** - Fewer services to manage and monitor

---

## Migration Path

### Current Architecture (DEPRECATED)
```
Health Service API
    ↓ (HTTP requests every 30s)
health-service-exporter (port 8002)
    ↓ (Converts JSON → Prometheus metrics)
Prometheus (port 9090)
    ↓ (PromQL queries)
Grafana Dashboard
```

### New Architecture (ACTIVE)
```
Prometheus (port 9090)
    ↓ (PromQL queries via prometheus_client library)
Backend (gatewayz-staging.up.railway.app)
    ├── GET /prometheus/metrics/summary
    ├── GET /prometheus/metrics/providers
    ├── GET /prometheus/metrics/models
    └── ... (other endpoints)
    ↓
Grafana Dashboard
```

---

## Action Items

### For DevOps / Deployment Team

**Before January 7, 2026:**

1. **Integration Complete** - Verify `/prometheus/metrics/*` endpoints are working in production backend
2. **Grafana Migration** - Update dashboard panel queries to use new endpoints
3. **Monitoring Verified** - Confirm all dashboards display correct data
4. **Remove from docker-compose.yml** - Delete health-service-exporter service definition
5. **Remove from Prometheus config** - Delete health_service_exporter scrape job from `prometheus/prom.yml`
6. **Remove directory** - Delete `/health-service-exporter/` directory
7. **Commit & Deploy** - Push changes to main/staging branches

### For Backend Team

**Immediate Action Required:**

1. Implement the Prometheus aggregation module (provided in separate instructions)
2. Add all 8 endpoints to FastAPI application:
   - `GET /prometheus/metrics/summary`
   - `GET /prometheus/metrics/system`
   - `GET /prometheus/metrics/providers`
   - `GET /prometheus/metrics/models`
   - `GET /prometheus/metrics/business`
   - `GET /prometheus/metrics/performance`
   - `GET /prometheus/metrics/all`
   - `GET /prometheus/metrics/docs`
3. Deploy to staging and production
4. Notify when ready for removal

---

## Migration Timeline

| Date | Action | Responsible |
|------|--------|-------------|
| Dec 24 | Deprecation announced | DevOps |
| Dec 26-30 | Backend implementation & testing | Backend Team |
| Jan 1-3 | Staging validation & Grafana updates | DevOps |
| Jan 4-6 | Production deployment & monitoring | DevOps |
| Jan 7 | Service removal deadline | DevOps |

---

## Health Service Data - Where It Goes

The `health-service-exporter` currently fetches from 4 health service endpoints:
- `GET /health`
- `GET /status`
- `GET /metrics`
- `GET /cache/stats`

**Post-Migration Options:**

1. **Option A: Backend directly calls Health Service**
   - Backend adds direct HTTP client to health service
   - Exports those metrics from `/prometheus/metrics/summary`
   - Health service data now integrated with other backend metrics

2. **Option B: Prometheus queries only**
   - `/prometheus/metrics/summary` aggregates only from Prometheus
   - Health service metrics removed if not critical
   - Simpler but loses that visibility

**Recommendation:** Option A - Backend directly integrates health service calls

---

## Backward Compatibility

The `health-service-exporter` metrics will **no longer be available** after Jan 7, 2026:

| Metric | Status | Alternative |
|--------|--------|-------------|
| `gatewayz_health_service_up` | Deprecated | Query backend `/prometheus/metrics/summary` |
| `gatewayz_health_monitoring_active` | Deprecated | Query backend `/prometheus/metrics/summary` |
| `gatewayz_health_tracked_models` | Deprecated | Query backend `/prometheus/metrics/summary` |
| `gatewayz_health_active_incidents` | Deprecated | Query backend `/prometheus/metrics/summary` |
| `gatewayz_health_cache_available` | Deprecated | Query backend `/prometheus/metrics/summary` |

---

## Grafana Dashboard Updates Needed

**Current queries that will break:**
```promql
# OLD (BROKEN after removal)
gatewayz_health_service_up
gatewayz_health_active_incidents
gatewayz_health_status_distribution
gatewayz_health_cache_available

# NEW (CORRECT after migration)
# Query the backend endpoint instead:
# GET /prometheus/metrics/summary → parse JSON response
# Or if backend re-exports to Prometheus:
# Same query names but from a different scrape job
```

**Update path:**
1. Backend team implements endpoints
2. Backend exports metrics to Prometheus (if desired)
3. Update scrape job in `prometheus/prom.yml` to point to backend
4. Grafana queries remain the same

---

## Support & Questions

Questions about the migration?

- **Backend Integration:** Ask the backend team (other agent)
- **Deployment:** Ask DevOps team
- **Grafana Updates:** Ask monitoring team

---

## See Also

- `MIGRATION_INSTRUCTIONS.md` - Detailed integration guide for backend team
- `docs/backend/BACKEND_METRICS_REQUIREMENTS.md` - Complete metrics requirements
- `/prometheus/metrics/` integration guide (from other agent)

---

**Effective Date:** December 24, 2025

**Questions?** Contact your DevOps/Backend team leads.
