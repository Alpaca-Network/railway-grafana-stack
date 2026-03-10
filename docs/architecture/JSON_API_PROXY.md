# JSON-API-Proxy — Provider Health Data Bridge

**Type**: Custom Flask service
**Port**: 5050 (internal)
**Grafana Datasource UID**: `grafana_json_api`
**Datasource Plugin**: `simplejson` (Simple JSON)
**Last Updated**: March 2026

---

## What JSON-API-Proxy Does

The JSON-API-Proxy is a lightweight Flask service that acts as a **bridge** between the `gatewayz-backend`'s custom provider health API and Grafana's Simple JSON datasource.

Prometheus scrapes time-series counters and gauges. But provider health data — scores, circuit breaker states, availability percentages — is computed server-side by `gatewayz-backend` and exposed via a REST endpoint (`/prometheus/data/metrics`). The JSON-API-Proxy translates these REST responses into the Simple JSON format that Grafana can natively query.

```
gatewayz-backend
  └── GET /prometheus/data/metrics
        (provider_health_score, provider_circuit_breaker_state,
         provider_error_rate, provider_availability)
              │
              └──► Prometheus scrapes every 30s ──► Available as regular metrics
              └──► JSON-API-Proxy :5050 ──► Grafana JSON API queries (real-time)
```

Both paths (Prometheus scrape + JSON-API-Proxy) expose the same underlying data. Prometheus is best for time-series alerting. JSON-API-Proxy is best for real-time table/stat panels that need non-aggregated per-provider detail.

---

## Architecture

```
Grafana (datasource: grafana_json_api)
    │
    └── Query: /api/query (Simple JSON protocol)
              │
    JSON-API-Proxy :5050 (Flask)
              │
              └── Proxies to: $GATEWAYZ_API_URL/prometheus/data/metrics
                              (gatewayz-backend FastAPI endpoint)
```

**Docker Compose:** `json-api-proxy` service, internal network only.
**Railway:** Deployed as a separate service in the grafana-stack project. Accessible via `json-api-proxy.railway.internal:5050`.

---

## Grafana Integration

**Datasource configuration** (`grafana/provisioning/datasources/`):
```yaml
- name: JSON API
  type: simplejson
  uid: grafana_json_api
  url: ${JSON_API_URL}
  # JSON_API_URL = http://json-api-proxy:5050 (local)
  # JSON_API_URL = http://json-api-proxy.railway.internal:5050 (Railway)
```

**UID:** `grafana_json_api` — do not change, all Provider Directory panels reference this UID.

---

## Data Provided

The proxy translates `/prometheus/data/metrics` output into Simple JSON format:

| Field | Type | Description |
|-------|------|-------------|
| `provider_health_score` | Float (0–100) | Health score per AI provider |
| `provider_circuit_breaker_state` | Integer (0/1/2) | CLOSED / OPEN / HALF_OPEN |
| `provider_error_rate` | Float (0–1) | Current error rate per provider |
| `provider_availability` | Float (0–100) | Availability % per provider |

---

## Dashboards That Use JSON-API-Proxy

| Dashboard | Panels | Purpose |
|-----------|--------|---------|
| Provider Directory | 100+ panels | Provider health scores, circuit breaker states, availability matrix |
| Infrastructure Health | Several | Live provider health gauges |

**Note:** These panels show real-time provider state, not historical time-series. For trending/alerting on provider health, use `grafana_prometheus` with `provider_health_score` metric from the Prometheus scrape job.

---

## Environment Variables

| Variable | Set On | Description |
|----------|--------|-------------|
| `GATEWAYZ_API_URL` | JSON-API-Proxy service | Base URL of gatewayz-backend (e.g. `https://api.gatewayz.ai`) |
| `JSON_API_URL` | Grafana service | Internal URL of JSON-API-Proxy (e.g. `http://json-api-proxy.railway.internal:5050`) |

---

## Verification

```bash
# 1. Check proxy is running (local)
curl http://localhost:5050/

# 2. Test Simple JSON protocol health
curl http://localhost:5050/

# 3. Verify provider data flows through
curl http://localhost:5050/api/query \
  -H "Content-Type: application/json" \
  -d '{"targets":[{"target":"provider_health_score"}],"range":{"from":"now-5m","to":"now"}}'

# 4. Check Grafana datasource connectivity
curl -u admin:$GF_SECURITY_ADMIN_PASSWORD \
  http://localhost:3000/api/datasources/uid/grafana_json_api
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Provider Directory shows "No data" | `GATEWAYZ_API_URL` not set or backend unreachable | Verify `GATEWAYZ_API_URL=https://api.gatewayz.ai` on the JSON-API-Proxy service |
| Grafana "Datasource not found" | `grafana_json_api` UID broken | Do not change the UID — check `grafana/provisioning/datasources/` |
| Proxy container unhealthy | Flask startup error | Check `docker compose logs json-api-proxy` |
| Data stale / not updating | Backend `/prometheus/data/metrics` down | Verify `FASTAPI_TARGET` is set and backend is reachable (BACKEND-1) |

> See also: `docs/dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md` for the provider-facing metric reference.
