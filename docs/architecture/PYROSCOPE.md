# Pyroscope — Continuous Profiling

**Version**: 1.7.1
**Port**: 4040 (internal), public Railway domain for backend push
**Grafana Datasource UID**: `grafana_pyroscope`
**Last Updated**: March 2026

---

## What Pyroscope Does

Pyroscope provides **always-on CPU and memory profiling** for `gatewayz-backend`. While metrics (Prometheus) tell you *what* is wrong and traces (Tempo) tell you *which request* was slow, Pyroscope tells you **which line of code** is burning the CPU.

The Four Golden Signals might say "P99 latency is 8s" — Pyroscope shows that 73% of CPU time in those calls was spent in the token counter, not the HTTP client.

---

## Architecture

The `gatewayz-backend` and `railway-grafana-stack` live in **two separate Railway projects**. Pyroscope runs inside the grafana-stack project. The backend pushes profiles over Pyroscope's public Railway domain.

```
gatewayz-backend  (Railway project A)
  └─ pyroscope-io SDK  →  PUSH profiles every 15s
       └──────────────────────────────────────────► https://<pyroscope-domain>.up.railway.app
                                                                    │
                                        railway-grafana-stack  (Railway project B)
                                          ├─ Pyroscope :4040  (internal DNS)
                                          │     stores profiles on /data/pyroscope
                                          └─ Grafana  READ via  http://pyroscope.railway.internal:4040
                                                datasource UID: grafana_pyroscope
```

**Local (Docker Compose):** Backend sets `PYROSCOPE_SERVER_ADDRESS=http://localhost:4040`. Grafana uses `http://pyroscope:4040` via Docker network.

---

## Grafana Integration

**Datasource configuration** (`grafana/provisioning/datasources/`):
```yaml
- name: Pyroscope
  type: grafana-pyroscope-datasource
  uid: grafana_pyroscope
  url: ${PYROSCOPE_INTERNAL_URL}
```

**Cross-signal linking (Tempo → Pyroscope):**
Tempo is configured with `tracesToProfiles` pointing to `grafana_pyroscope` using `resource.service.name`. This means: clicking any slow span in Tempo → "View Profile" → jumps to the Pyroscope flamegraph at that exact timestamp. No manual timestamp matching needed.

---

## Provider & Model Tagged Flamegraphs

Every inference call in `gatewayz-backend` is wrapped with `pyroscope.tag_wrapper()` so flamegraphs can be filtered by provider and model:

| Pyroscope Tag | Values | Purpose |
|--------------|--------|---------|
| `provider` | `openai`, `openrouter`, `anthropic`, etc. | Filter CPU usage by AI provider |
| `model` | `gpt-4o`, `claude-3-5-sonnet`, etc. | Filter by model |
| `service_name` | `gatewayz-backend` | Service identifier |
| `environment` | `production`, `staging`, `local` | Environment filter |

**Example use:** Grafana Explore → Pyroscope → filter `provider=openrouter, model=claude-3-5-sonnet` → see exact Python functions consuming CPU for those specific calls.

---

## Dashboards That Use Pyroscope

| Dashboard | Panels | Purpose |
|-----------|--------|---------|
| Cache Layer Profile | All 7 panels | CPU cost by cache layer (`auth`, `rate_limit`, `model_catalog`, `response_cache`, `trial_analytics`) |
| Inference Call Profile | Flamegraph + CPU bargauges | CPU anatomy by provider and model |
| Four Golden Signals | Profiling row | CPU saturation at P99 tail |

---

## Environment Variables

| Variable | Set On | Description |
|----------|--------|-------------|
| `PYROSCOPE_INTERNAL_URL` | Grafana service | Internal URL for Grafana → Pyroscope reads (e.g. `http://pyroscope.railway.internal:4040`) |
| `PYROSCOPE_SERVER_ADDRESS` | gatewayz-backend | Public URL for backend → Pyroscope pushes (e.g. `https://pyroscope-xxxx.up.railway.app`) |
| `PYROSCOPE_ENABLED` | gatewayz-backend | Set to `true` to enable profiling push |

---

## Setup Steps (Railway)

1. **Grafana-stack project → Pyroscope service → Settings → Generate Domain**
   Copy the generated URL (e.g. `https://pyroscope-production-xxxx.up.railway.app`)

2. **Set on the backend service (gatewayz-backend, separate project):**
   ```
   PYROSCOPE_ENABLED=true
   PYROSCOPE_SERVER_ADDRESS=https://pyroscope-production-xxxx.up.railway.app
   ```

3. **Set on the Grafana service (grafana-stack project):**
   ```
   PYROSCOPE_INTERNAL_URL=http://pyroscope.railway.internal:4040
   ```

No authentication needed — self-hosted Pyroscope has no auth by default.

---

## Verification

```bash
# 1. Check Pyroscope is ready
curl http://localhost:4040/ready
# Expected: HTTP 200

# 2. Check Grafana datasource is connected
curl -u admin:$GF_SECURITY_ADMIN_PASSWORD \
  http://localhost:3000/api/datasources/uid/grafana_pyroscope
# Expected: JSON with type: grafana-pyroscope-datasource

# 3. Verify profiles are ingesting (should show profile data)
curl "http://localhost:4040/pyroscope/render?from=now-1h&until=now&query=process_cpu:cpu:nanoseconds:cpu:nanoseconds&format=json"
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Flamegraph shows "No data" | Backend not pushing / wrong address | Check `PYROSCOPE_SERVER_ADDRESS` on backend; test with `curl $PYROSCOPE_SERVER_ADDRESS/ready` |
| Datasource "Connection refused" | `PYROSCOPE_INTERNAL_URL` wrong | Verify Railway internal DNS: `http://pyroscope.railway.internal:4040` |
| Tempo → Profile link not working | `tracesToProfiles` config missing | Check `tempo/tempo.yml` for `metrics_generator.processor.service_graphs` and `tracesToProfiles` Grafana datasource config |

> See also: `README.md` — "Continuous Profiling (Self-hosted Pyroscope)" section for full setup walkthrough.
