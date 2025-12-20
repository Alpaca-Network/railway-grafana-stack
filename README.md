# GatewayZ Observability Stack

A complete observability solution deployed on **Railway**, providing centralized logging, metrics collection, distributed tracing, and visualization for the GatewayZ infrastructure.

## Stack Components

| Service | Port(s) | Purpose |
|---------|---------|---------|
| **Grafana** | 3000 | Central visualization and dashboarding |
| **Loki** | 3100 | Log aggregation system |
| **Prometheus** | 9090 | Time-series metrics collection |
| **Tempo** | 3200 (HTTP), 3201 (gRPC), 4317/4318 (Ingest) | Distributed tracing backend |

All services are pre-configured and interconnected, ready to receive and visualize telemetry data.

## Quick Start

### 1. Deploy to Railway
```bash
git clone https://github.com/Alpaca-Network/railway-grafana-stack.git
cd railway-grafana-stack
# Push to Railway or use Railway CLI
```

### 2. Set Environment Variables (Railway Dashboard)

**⚠️ Railway ignores `docker-compose.yml` environment variables. You must set these manually in the Railway Dashboard.**

**Grafana Service → Variables:**
```
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>
```

**Backend Service → Variables (to connect your app):**
```
LOKI_PUSH_URL=http://loki:3100/loki/api/v1/push
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo:4317
```

### 3. Access Grafana
Navigate to your Grafana public URL and log in with the credentials you set.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GatewayZ Backend                          │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
        Metrics (Pull)   Logs (Push)   Traces (Push)
               │              │              │
        ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
        │ Prometheus  │ │   Loki    │ │   Tempo     │
        └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
               │              │              │
               └──────────────┼──────────────┘
                              │
                       ┌──────▼──────┐
                       │   Grafana   │
                       └─────────────┘
```

## Dashboards Included

1. **FastAPI Dashboard** - API performance, error rates, resource usage
2. **Models Monitoring** - AI model throughput, latency, token usage
3. **Loki Logs** - Centralized log search and aggregation
4. **Tempo Tracing** - Distributed tracing visualization

## Service URLs

### Internal URLs (Same Railway Project)
| Service | URL |
|---------|-----|
| Loki Push | `http://loki:3100/loki/api/v1/push` |
| Loki Query | `http://loki:3100` |
| Tempo HTTP Ingest | `http://tempo:4318` |
| Tempo gRPC Ingest | `http://tempo:4317` |
| Prometheus | `http://prometheus:9090` |

### Public URLs
| Service | URL |
|---------|-----|
| Grafana | `https://logs.gatewayz.ai` |
| Prometheus | `https://prometheus-production-08db.up.railway.app` |

## Configuration Files

| File | Purpose |
|------|---------|
| `prometheus/prom.yml` | Prometheus scrape targets and intervals |
| `loki/loki.yml` | Loki storage and ingestion settings |
| `tempo/tempo.yml` | Tempo tracing configuration |
| `grafana/dashboards/*.json` | Pre-built Grafana dashboards |
| `grafana/provisioning/` | Datasource and dashboard provisioning |

## Documentation

Detailed guides are available in the repository:

| Guide | Description |
|-------|-------------|
| [RAILWAY_DEPLOYMENT_QUICK_START.md](./RAILWAY_DEPLOYMENT_QUICK_START.md) | Step-by-step Railway deployment |
| [BACKEND_RAILWAY_CONFIG.md](./BACKEND_RAILWAY_CONFIG.md) | Connect your backend to this stack |
| [RAILWAY_AUTH_FIX.md](./RAILWAY_AUTH_FIX.md) | Fix login issues on Railway |
| [STAGING_WORKFLOW.md](./STAGING_WORKFLOW.md) | Test changes before production |

## Development

### Local Testing
```bash
docker-compose up --build
```
Access Grafana at `http://localhost:3000` (default: admin/yourpassword123).

### Staging Branch
Push to `staging/models-and-fixes` to test on Railway staging before merging to `main`.

## Troubleshooting

### "Invalid Username/Password"
Set `GF_SECURITY_ADMIN_PASSWORD` in Railway **Grafana Service → Variables**.

### "No Data" in Dashboards
1. Verify backend is running and instrumented
2. Check `BACKEND_RAILWAY_CONFIG.md` for connection variables
3. Verify Prometheus targets: `http://prometheus:9090/targets`

### Tempo "Frame too large" Error
Fixed in `tempo/tempo.yml`. Ensure `frontend_address` uses port `3201` (gRPC), not `3200` (HTTP).

### Loki 400 Bad Request
Fixed in dashboard JSON. Queries now use `[5m]` instead of `$__rate_interval`.

## External Documentation

- [Grafana Docs](https://grafana.com/docs/grafana/latest/)
- [Loki Docs](https://grafana.com/docs/loki/latest/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Tempo Docs](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)

---

**GatewayZ Observability Stack** · Deployed on Railway
