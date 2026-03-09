# Acceptance Criteria — GatewayZ LGTM Stack Kanban

> Every Kanban card on the GitHub Project board ("Logs, Graphs, Traces, and Metrics Dashboard") has explicit acceptance criteria listed here.
> **Format:** Card title → one-sentence description → measurable criteria bullet points.
> **Branch:** `refactor/refactor-master-markdowns`

---

## ✅ Done — Pre-Existing Completed Work

### DONE-1: All 15 Grafana Dashboards Complete
All Grafana dashboards are fully populated with live Prometheus/Mimir/Loki/Tempo queries — no placeholder panels.
- [ ] 15 dashboard JSON files exist in `grafana/dashboards/` subfolders
- [ ] Every panel has a valid `expr` (no empty or placeholder queries)
- [ ] All dashboards load without error in Grafana (no "No Data" on a fresh stack with backend connected)
- [ ] `dashboards.yml` provisions all 10 folders
- [ ] Total panel count exceeds 400

### DONE-2: All 7 Datasources Provisioned
All Grafana datasources are configured with correct UIDs and tested connectivity.
- [ ] `grafana/provisioning/datasources/` contains YAML for: Prometheus, Mimir, Loki, Tempo, Pyroscope, Alertmanager, JSON-API
- [ ] UIDs match exactly: `grafana_prometheus`, `grafana_mimir`, `grafana_loki`, `grafana_tempo`, `grafana_pyroscope`, `alertmanager`, `grafana_json_api`
- [ ] Grafana "Data Sources" page shows all 7 as green/healthy when stack is running
- [ ] No dashboard panel references an undefined datasource UID

### DONE-3: 16 Prometheus Alert Rules
All Prometheus alert rules are validated and firing correctly in the stack.
- [ ] `prometheus/alert.rules.yml` contains exactly 16 rules across 4 groups
- [ ] Prometheus UI `/alerts` shows all 16 rules in INACTIVE state when system is healthy
- [ ] Each rule has: `alert`, `expr`, `for`, `labels.severity`, `annotations.summary`
- [ ] Rules cover: service health, API performance, provider health, saturation/security, infrastructure

### DONE-4: 40+ Grafana Alert Rules (10 YAML Files)
All Grafana-managed alert rules are provisioned and visible in the Grafana Alerting UI.
- [ ] `grafana/provisioning/alerting/rules/` contains exactly 10 YAML files
- [ ] Grafana Alerting UI shows 40+ rules across their respective folders
- [ ] Each rule has: `uid`, `title`, `condition`, `for`, `annotations.runbook_url`, `labels.severity`
- [ ] Alert rules cover all 8 categories: availability, backend, error rate, general, latency, logs, model, redis, SLO burn rate, traffic

### DONE-5: 32 Prometheus Recording Rules
Pre-computed recording rules are registered and serving baseline metrics for anomaly detection alerts.
- [ ] `prometheus/recording_rules_baselines.yml` contains 32 rules across 6 groups
- [ ] Prometheus UI `/rules` shows all recording rule groups as healthy (green)
- [ ] Recording rules produce metrics like `job:fastapi_requests:rate5m`, `job:error_rate:avg1h` etc.
- [ ] Alert rules referencing recording rule outputs do not show "undefined metric" errors

### DONE-6: Alertmanager Two-Tier Email Routing
Critical alerts go to on-call immediately; warnings go to ops with grouping delay.
- [ ] `alertmanager/alertmanager.yml` defines two receivers: `ops-email` and `critical-email`
- [ ] `severity=critical` routes to `critical-email` with `group_wait: 0s`, `repeat_interval: 2m`
- [ ] `severity=warning` routes to `ops-email` with `group_wait: 5m`, `repeat_interval: 1h`
- [ ] SMTP configuration uses env vars: `SMTP_FROM`, `SMTP_USER`, `SMTP_PASSWORD`
- [ ] Alertmanager UI at `:9093` shows the routing tree correctly

### DONE-7: Full Docker Compose Stack (8 Services)
All 8 services start, pass healthchecks, and communicate correctly via Docker network.
- [ ] `docker-compose.yml` defines 8 services: Prometheus, Mimir, Grafana, Loki, Tempo, Alertmanager, Pyroscope, JSON-API-Proxy
- [ ] All services have `healthcheck` blocks
- [ ] `docker compose up` completes with all services in healthy state within 60s
- [ ] Services communicate via internal Docker network (no hardcoded IPs)
- [ ] Resource limits are set on memory-intensive services (Mimir, Loki, Tempo)

### DONE-8: Mimir Long-Term Storage Integration
Prometheus remote-writes to Mimir; Grafana queries Mimir for historical dashboards.
- [ ] `mimir/mimir.yml` configures monolithic mode with 30d retention
- [ ] `prometheus/prometheus.yml` has `remote_write` block pointing to Mimir at `/api/v1/push`
- [ ] Grafana datasource `grafana_mimir` returns data for queries beyond Prometheus retention
- [ ] Mimir API at `:9009/api/v1/query` responds to PromQL correctly
- [ ] `X-Scope-OrgID: anonymous` header is set on all Mimir requests

### DONE-9: Railway Deployment Configs for All Services
Each service has a `railway.toml` (or equivalent) so Railway can deploy independently.
- [ ] Each service directory has a `railway.toml` file
- [ ] All services are listed in the Railway project with correct start commands
- [ ] `FASTAPI_TARGET` env var is documented in Railway service settings
- [ ] Grafana is accessible at `logs.gatewayz.ai` (custom domain configured)

### DONE-10: 48 Documentation Files
Comprehensive documentation exists for architecture, deployment, troubleshooting, and backend integration.
- [ ] `docs/docs-index.md` lists all 48 files with brief descriptions
- [ ] At minimum these files exist: `QUICKSTART.md`, `RAILWAY_DEPLOYMENT_QUICK_START.md`, `COMPLETE_BACKEND_INTEGRATION_GUIDE.md`, `ALERTING_SETUP.md`, `LOKI_FIX_GUIDE.md`, `BACKEND_METRICS_REQUIREMENTS.md`
- [ ] `MASTER.md` exists at repo root (comprehensive wiki)
- [ ] `CLAUDE.md` exists at repo root (agent quick-reference)

---

## ✅ Done — This Session

### TASK-1: Register System Quality Folder in dashboards.yml
Add the `reliability/` provisioner to `grafana/provisioning/dashboards/dashboards.yml` so Grafana auto-loads the new System Quality dashboard.
- [x] `dashboards.yml` contains a provider entry named `System Quality`
- [x] The provider maps to path `/etc/grafana/provisioning/dashboards/reliability`
- [x] Grafana shows a "System Quality" folder in the dashboard browser after restart
- [x] No existing provider entries were modified
- [x] File is valid YAML (passes `yamllint`)

---

## 🔄 In Progress

### TASK-2: System Quality Dashboard — Scaffold
Create the base `System-Reliability-Dashboard.json` file with correct schema, UID, metadata, and 8 empty rows (one per pillar).
- [ ] File exists at `grafana/dashboards/reliability/System-Reliability-Dashboard.json`
- [ ] `"uid": "gatewayz-system-quality-pillars"`
- [ ] `"schemaVersion": 39` (must not be changed — Railway compatibility)
- [ ] `"refresh": "30s"`
- [ ] 8 row panels present: Reliability (IDs 100s), Performance (200s), Scalability (300s), Availability (400s), Observability (500s), Fault Tolerance (600s), Security (700s), Maintainability (800s)
- [ ] Dashboard loads in Grafana without JSON parse errors
- [ ] All datasource references use correct UIDs: `grafana_prometheus`, `grafana_loki`

---

## 📋 Ready — System Quality Dashboard Pillar Rows

### TASK-3: Reliability Row (Panel IDs 100–107)
Add the Reliability pillar row to the System Quality dashboard with 6–8 panels covering MTTR, MTBF, error budget, SLO compliance.
- [ ] Row panel with `"title": "🛡️ Reliability"`, `"collapsed": false`
- [ ] Stat panel: Current error rate (`rate(fastapi_requests_total{status_code=~"5.."}[5m]) / rate(fastapi_requests_total[5m])`)
- [ ] Stat panel: SLO compliance % (1 - error rate, thresholds: green > 99.9%, yellow > 99%, red below)
- [ ] Timeseries panel: Error rate over time (7d range)
- [ ] Stat panel: Availability uptime % (from recording rule or direct calculation)
- [ ] All panels have `"instant": true` on stat targets, omitted on timeseries
- [ ] All division expressions use `clamp_min(expr, 0.001)` as denominator

### TASK-4: Performance Row (Panel IDs 200–209)
Add the Performance pillar row with panels covering P50/P95/P99 latency, throughput, and TTFC.
- [ ] Row panel with `"title": "⚡ Performance"`, `"collapsed": false`
- [ ] Stat panel: Current P95 latency (`histogram_quantile(0.95, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le))`)
- [ ] Stat panel: Current P99 latency
- [ ] Stat panel: Requests per second (throughput)
- [ ] Stat panel: Streaming time-to-first-chunk P95 (`time_to_first_chunk_seconds`)
- [ ] Timeseries panel: Latency percentiles over time (P50 / P95 / P99)
- [ ] Thresholds: green < 0.5s, yellow < 1s, red > 1s

### TASK-5: Scalability Row (Panel IDs 300–308)
Add the Scalability pillar row covering concurrency, cache hit ratio, token throughput, and DB read replica routing.
- [ ] Row panel with `"title": "📈 Scalability"`, `"collapsed": false`
- [ ] Stat panel: Active concurrent requests (`sum(fastapi_requests_in_progress)`)
- [ ] Stat panel: Cache hit ratio (`catalog_cache_hits_total / (catalog_cache_hits_total + catalog_cache_misses_total)`)
- [ ] Stat panel: Token throughput (tokens/min from `rate(tokens_used_total[5m]) * 60`)
- [ ] Gauge panel: Read replica routing ratio (`read_replica_queries_total{status="success"}`)
- [ ] Timeseries panel: Request concurrency over time

### TASK-6: Availability Row (Panel IDs 400–405)
Add the Availability pillar row with SLO burn rate indicators and provider availability matrix.
- [ ] Row panel with `"title": "✅ Availability"`, `"collapsed": false`
- [ ] Stat panel: Overall availability % (complement of error rate, instant)
- [ ] Stat panel: SLO burn rate (current error rate / 0.001 budget)
- [ ] Stat panel: Count of providers with health score > 80
- [ ] Gauge panel: Lowest provider health score (min over all `provider_health_score`)
- [ ] Timeseries panel: Provider availability over 24h

### TASK-7: Observability Row (Panel IDs 500–507)
Add the Observability pillar row covering trace coverage, log volume, exception breakdown, and active Grafana alerts.
- [ ] Row panel with `"title": "🔭 Observability"`, `"collapsed": false`
- [ ] Stat panel: Log error volume (Loki query: `sum(count_over_time({app="gatewayz", level="ERROR"}[5m]))`)
- [ ] Stat panel: Exception count (`sum(rate(fastapi_exceptions_total[5m])) * 300`)
- [ ] Piechart panel: Exceptions by type (`fastapi_exceptions_total` by `exception_type`)
- [ ] Stat panel: Active Grafana firing alerts (Alertmanager datasource query)
- [ ] Logs panel: Recent ERROR logs (Loki, last 20 lines, `{app="gatewayz"} | json | level="ERROR"`)

### TASK-8: Fault Tolerance Row (Panel IDs 600–607)
Add the Fault Tolerance / Resilience pillar row covering circuit breaker states, provider failover events, and velocity mode.
- [ ] Row panel with `"title": "🔄 Fault Tolerance / Resilience"`, `"collapsed": false`
- [ ] Stat panel: Circuit breakers OPEN (`sum(provider_circuit_breaker_state == 1)`) — red if > 0
- [ ] Stat panel: Velocity mode activations (`increase(velocity_mode_activations_total[1h])`)
- [ ] Timeseries panel: Provider health scores over 24h (all providers)
- [ ] Stat panel: OTEL export circuit breaker state (`otel_export_circuit_breaker_state`)
- [ ] Gauge panel: Prometheus remote write success rate (`rate(prometheus_remote_write_total{status="success"}[5m])`)

### TASK-9: Security Row (Panel IDs 700–707)
Add the Security pillar row covering auth failures, rate limit rejections, 4xx rate, and velocity mode state.
- [ ] Row panel with `"title": "🔒 Security"`, `"collapsed": false`
- [ ] Stat panel: 4xx rate (`rate(fastapi_requests_total{status_code=~"4.."}[5m]) / rate(fastapi_requests_total[5m])`)
- [ ] Stat panel: 401/403 auth failure rate (filtered to `status_code=~"401|403"`)
- [ ] Stat panel: 429 rate limit rejection rate (filtered to `status_code="429"`)
- [ ] Stat panel: Velocity mode active (1 = active, 0 = not) — red if 1
- [ ] Logs panel: Recent security log lines (`{app="gatewayz"} | json | level="WARNING"`, last 15 lines)
- [ ] Timeseries panel: Auth failure rate over time (7d)

### TASK-10: Maintainability Row (Panel IDs 800–808)
Add the Maintainability pillar row covering process uptime, memory usage, cost trends, Redis health, and Loki queue.
- [ ] Row panel with `"title": "🔧 Maintainability"`, `"collapsed": false`
- [ ] Stat panel: Process uptime (`time() - process_start_time_seconds`)
- [ ] Stat panel: Memory RSS (`process_resident_memory_bytes`)
- [ ] Stat panel: Loki log queue depth (`loki_log_queue_size`) — yellow if > 100, red if > 500
- [ ] Stat panel: Redis memory usage % (`redis_memory_used_bytes / clamp_min(redis_memory_max_bytes, 0.001) * 100`)
- [ ] Timeseries panel: Cumulative API cost over 7d (`increase(gatewayz_api_cost_usd_total[7d])`)
- [ ] Stat panel: Daily cost (`increase(gatewayz_api_cost_usd_total[24h])`)

---

## ⚠️ Outstanding Gaps — Needs Future Work

### BACKEND-1: Verify FASTAPI_TARGET in Railway
Confirm the `FASTAPI_TARGET` environment variable is correctly set in the Railway Prometheus service so backend metrics flow into the stack.
- [ ] Railway Prometheus service environment variables include `FASTAPI_TARGET=https://api.gatewayz.ai`
- [ ] Prometheus UI `/targets` shows `gatewayz_production` job with state UP
- [ ] `fastapi_requests_total` metric exists in Prometheus (verify via `/graph?g0.expr=fastapi_requests_total`)
- [ ] At least one dashboard panel shows non-zero data (e.g., Four Golden Signals — Request Rate)
- [ ] If target is DOWN: check Railway internal networking, service name resolution, and auth headers

### BACKEND-2: Verify OTLP Trace Export from Backend to Tempo
Confirm that `gatewayz-backend` is successfully exporting OpenTelemetry traces to Tempo via OTLP HTTP.
- [ ] `TEMPO_OTLP_HTTP_ENDPOINT` env var is set in the Railway backend service (e.g. `http://tempo:4318`)
- [ ] Tempo `/ready` endpoint responds 200
- [ ] A test request to `POST /v1/chat/completions` generates at least one trace visible in Grafana Explore → Tempo
- [ ] Traces contain service name `gatewayz-api`
- [ ] Traces contain `gen_ai.*` attributes on LLM spans (verify via Traceloop integration)
- [ ] `ResilientSpanProcessor` circuit breaker state = CLOSED (check `otel_export_circuit_breaker_state` metric)
- [ ] Distributed Tracing dashboard shows data for the past 1h

### BACKEND-3: Verify Loki Log Labels Match Dashboard Queries
Confirm that log lines from `gatewayz-backend` arrive in Loki with `app="gatewayz"` label so all Loki dashboards return data.
- [ ] Loki `/loki/api/v1/labels` returns `app` as a label
- [ ] LogQL query `{app="gatewayz"}` returns log lines in Grafana Explore → Loki
- [ ] `level` label is present with values: INFO, WARNING, ERROR, CRITICAL
- [ ] `trace_id` field appears in JSON-parsed log lines
- [ ] Live GatewayZ Logs dashboard shows real log lines (not empty)
- [ ] Error-Level Logs dashboard shows data when errors have occurred
- [ ] If no data: check `LOKI_URL` env var in backend; check async queue not blocked

### INFRA-1: Validate Redis Exporter Integration
Confirm the Redis exporter is reliably shipping metrics and alert rules have data.
- [ ] Redis exporter container is running and healthy (`docker compose ps`)
- [ ] Prometheus target `redis_exporter` shows state UP in `/targets`
- [ ] `redis_memory_used_bytes` metric exists in Prometheus
- [ ] `redis_memory_max_bytes` returns a non-zero value
- [ ] Redis alert rule `RedisMemoryHigh` (>80%) is in INACTIVE or PENDING state (not "No data")
- [ ] Cache Layer Profile dashboard shows Redis memory gauge with data

### INFRA-2: Migrate Mimir Storage from Filesystem to S3
Replace Mimir's local filesystem storage with S3-compatible object storage for production durability.
- [ ] `mimir/mimir.yml` updated to use S3/GCS/MinIO backend (not `filesystem`)
- [ ] S3 bucket created and IAM credentials configured
- [ ] Mimir restarts without data loss (existing series still queryable after migration)
- [ ] Historical queries (e.g. last 7d) return correct data post-migration
- [ ] Mimir `/ready` endpoint responds 200 after migration
- [ ] `MIMIR_S3_BUCKET`, `MIMIR_S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` documented in Railway env vars
- [ ] Alerting on Mimir storage errors is tested (verify no silent data loss)

---

*Last updated: March 2026. Update this file whenever Kanban card scope changes.*
*GitHub Project: "Logs, Graphs, Traces, and Metrics Dashboard" — Project #8 on Alpaca-Network/railway-grafana-stack*
