# Handoff README (for next agent)

## Context
Repo: `railway-grafana-stack` (Grafana + Prometheus + Loki + Tempo on Railway)
Goal from owner: Ensure Loki + Tempo dashboards show data reliably and avoid duplicates. Also user confusion: Railway “HTTP Logs” tab for Loki only shows `/loki/api/v1/push` traffic (ingestion), not GatewayZ backend HTTP request events.

## What was done this session
### Dashboard fix shipped
- **Loki dashboard** changed to avoid hardcoding a label that often isn’t present:
  - File: `grafana/dashboards/loki/loki.json`
  - Change: `{app="gatewayz", env="production"}` → `{app="gatewayz"}`
  - This prevents Grafana Loki dashboard from showing **No data** when logs are ingested without an `env` label.
  - Error rate expression was also cleaned up.

### Tests/validation
- `./scripts/validate_dashboards.sh strict` passes (0 errors/warnings)
- `python3 -m pytest -q` passes (69 passed, 30 skipped)

### Git
- Changes were committed and pushed to `main`:
  - `f9c8e72 Fix Loki dashboard queries to avoid hardcoded env label`
  - `41e8369 Add implementation plan for Loki/Tempo dashboard robustness`

## Current open issue / user complaint
User says: “I am not getting any http event logs on that page? this is what shows on railway” and shared screenshot of Railway service **Loki → HTTP Logs**.

### Important clarification
Railway “HTTP Logs” for the **Loki service** will mostly show:
- `POST /loki/api/v1/push` (ingestion)
- occasional query requests

It will **not** show GatewayZ backend request logs (e.g. `/api/...`) unless those requests are being made directly to the Loki HTTP server, which they should not.

If user wants to see GatewayZ backend HTTP request events:
- They need the GatewayZ backend to emit HTTP request logs to stdout and have a log shipper (Promtail/Vector/Otel collector) push them to Loki, OR
- Configure OpenTelemetry logs pipeline (OTel Collector with loki exporter) from the GatewayZ service.

## What to do next (recommended)
### 1) Identify which “page” they mean
Two different pages cause confusion:
- Railway → Loki service → **HTTP Logs** tab (ingestion HTTP access logs)
- Grafana → “GatewayZ Logs - Loki” dashboard (application logs in Loki)

If they want “http event logs” in Grafana, that requires **GatewayZ** to log HTTP events and ship them into Loki.

### 2) Confirm labels actually present in Railway Loki
If the Grafana dashboard still shows no data on Railway, likely label mismatch:
- dashboard now queries `{app="gatewayz"}`
- but production streams may not include `app=gatewayz`; they might include `service_name=gatewayz` or `compose_service=gatewayz` etc.

To quickly diagnose on Railway:
- Use Grafana Explore → Loki
- Run `{}` then filter by label browser
- Identify canonical label(s) for GatewayZ logs

Then update `grafana/dashboards/loki/loki.json` query to match reality, e.g.:
- `{service_name="gatewayz"}` or `{compose_service="gatewayz"}`

(Keep tests constraints in mind; datasource UIDs must remain `grafana_loki` etc.)

### 3) Tempo robustness still pending
Tempo dashboard currently uses TraceQL:
- `{resource.service.name="gatewayz"}`
- `{resource.service.name="gatewayz" && status=error}`

If traces in Railway use different attributes, then Tempo dashboard may show “No data”. Next agent should:
- Query Tempo search, inspect actual resource attributes
- Update TraceQL queries to match, ideally using dashboard variables.

## Files of interest
- Dashboards:
  - `grafana/dashboards/loki/loki.json`
  - `grafana/dashboards/tempo/tempo.json`
- Datasources provisioning:
  - `grafana/datasources/datasources.yml`
- Dashboard provisioning:
  - `grafana/provisioning/dashboards/dashboards.yml`
- Validation:
  - `scripts/validate_dashboards.sh`
  - `tests/test_dashboards.py`

## Quick reproduction commands (local)
- Validate dashboards:
  - `./scripts/validate_dashboards.sh strict`
- Run tests:
  - `python3 -m pytest -q`
- Push a test log line to Loki:
  - `ns=$(date +%s%N); curl -s -X POST http://localhost:3100/loki/api/v1/push -H 'Content-Type: application/json' -d '{"streams":[{"stream":{"app":"gatewayz","env":"production","level":"ERROR"},"values":[["'"$ns"'","hello from dashboard label test"]]}]}'`

