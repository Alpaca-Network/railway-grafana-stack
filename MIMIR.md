# Grafana Mimir - Long-term Metrics Storage

**Component**: Grafana Mimir
**Version**: 2.11.0+
**Deployment**: Railway (Production)
**Status**: Active
**Last Updated**: January 25, 2026

---

## Overview

Grafana Mimir is a horizontally scalable, highly available, multi-tenant TSDB (Time Series Database) for long-term Prometheus metrics storage. In the GatewayZ monitoring stack, Mimir serves as the central metrics storage backend.

### Why Mimir?

| Feature | Prometheus Only | With Mimir |
|---------|-----------------|------------|
| Data Retention | 15 days (default) | 30+ days configurable |
| High Availability | Single instance | Replicated storage |
| Data Persistence | Lost on restart | Persistent across restarts |
| Query Consistency | May show gaps | Consistent results |
| Page Refresh | Sometimes stale | Always fresh data |

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Prometheus    │────>│      Mimir       │<────│    Grafana    │
│  (Collector)    │     │  (Storage/Query) │     │  (Dashboard)  │
└─────────────────┘     └──────────────────┘     └───────────────┘
        │                        │
        │  remote_write          │  PromQL queries
        │  (push metrics)        │  (read metrics)
        v                        v
   ┌─────────────────────────────────────┐
   │       Mimir Internal Components     │
   │  ┌───────────┐  ┌───────────────┐   │
   │  │Distributor│->│   Ingester    │   │
   │  └───────────┘  └───────────────┘   │
   │         │               │           │
   │         v               v           │
   │  ┌───────────┐  ┌───────────────┐   │
   │  │  Querier  │  │   Compactor   │   │
   │  └───────────┘  └───────────────┘   │
   │         │               │           │
   │         v               v           │
   │  ┌──────────────────────────────┐   │
   │  │      Blocks Storage          │   │
   │  │     (Filesystem/S3)          │   │
   │  └──────────────────────────────┘   │
   └─────────────────────────────────────┘
```

---

## Railway Deployment

### Service Configuration

| Setting | Value |
|---------|-------|
| **Service Name** | `mimir` |
| **Root Directory** | `/mimir` |
| **Port** | `9009` (HTTP API) |
| **Health Check Path** | `/ready` |
| **Memory** | 1024 MB (minimum) |
| **CPU** | 1 vCPU |

### URLs

| Type | URL |
|------|-----|
| **Public URL** | `https://mimir-production-1b34.up.railway.app` |
| **Internal URL** | `http://mimir.railway.internal:9009` |
| **Push Endpoint** | `http://mimir.railway.internal:9009/api/v1/push` |
| **Query Endpoint** | `http://mimir.railway.internal:9009/prometheus` |

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `CONFIG_FILE` | `/etc/mimir/mimir-railway.yml` | Config file (default) |
| `RAILWAY_ENVIRONMENT` | `production` | Auto-set by Railway |
| `PORT` | `9009` | HTTP API port |

---

## Configuration Files

### mimir-railway.yml (Production)

```yaml
# Railway-optimized configuration
target: all                    # Monolithic mode (single process)
multitenancy_enabled: false    # Single tenant

server:
  http_listen_port: 9009
  grpc_listen_port: 9095
  http_listen_address: 0.0.0.0  # Listen on all interfaces
  grpc_listen_address: 0.0.0.0

distributor:
  ring:
    kvstore:
      store: memberlist

ingester:
  ring:
    kvstore:
      store: memberlist
    replication_factor: 1

blocks_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/blocks
  tsdb:
    dir: /data/mimir/tsdb

limits:
  max_global_series_per_user: 500000
  ingestion_rate: 50000
  max_query_lookback: 30d
  compactor_blocks_retention_period: 30d
```

### mimir.yml (Local Development)

Similar configuration but uses Docker Compose networking (`mimir:9009`).

---

## Integration with Prometheus

### Remote Write Configuration

Prometheus pushes metrics to Mimir via `remote_write`:

```yaml
# prometheus/prom.yml
remote_write:
  - url: MIMIR_URL/api/v1/push      # Substituted at runtime
    name: mimir-remote-write
    remote_timeout: 30s
    queue_config:
      capacity: 10000
      max_shards: 50
      max_samples_per_send: 2000
```

**Runtime Substitution** (handled by `entrypoint.sh`):

| Environment | MIMIR_URL Value |
|-------------|-----------------|
| Railway | `http://mimir.railway.internal:9009` |
| Local Docker | `http://mimir:9009` |

### Mimir Scrape Job

Prometheus also scrapes Mimir's own metrics:

```yaml
- job_name: 'mimir'
  scheme: http
  static_configs:
    - targets: ['MIMIR_TARGET']  # Substituted at runtime
  scrape_interval: 30s
```

---

## Integration with Grafana

### Datasource Configuration

```yaml
# grafana/provisioning/datasources/mimir.yml
datasources:
  - name: Mimir
    uid: grafana_mimir
    type: prometheus
    access: proxy
    url: ${MIMIR_INTERNAL_URL:-http://mimir:9009}/prometheus
    jsonData:
      prometheusType: Mimir
```

### Using Mimir in Dashboards

1. **Select Datasource**: Choose "Mimir" instead of "Prometheus"
2. **Query**: Use standard PromQL syntax
3. **Benefits**:
   - 30-day query range vs 15-day Prometheus
   - Consistent data on page refresh
   - No gaps from Prometheus restarts

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ready` | GET | Health check (returns "ready") |
| `/api/v1/push` | POST | Receive metrics from Prometheus |
| `/prometheus/api/v1/query` | GET/POST | PromQL instant query |
| `/prometheus/api/v1/query_range` | GET/POST | PromQL range query |
| `/prometheus/api/v1/labels` | GET | List all labels |
| `/prometheus/api/v1/series` | GET | List matching series |
| `/metrics` | GET | Mimir's own metrics |

### Example Queries

```bash
# Health check
curl https://mimir-production-1b34.up.railway.app/ready

# Query metrics
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/query?query=up"

# List labels
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/labels"

# Range query (last hour)
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/query_range?query=up&start=$(date -v-1H +%s)&end=$(date +%s)&step=60"
```

---

## Monitoring Mimir

### Key Metrics

| Metric | Description |
|--------|-------------|
| `cortex_ingester_active_series` | Number of active time series |
| `cortex_distributor_received_samples_total` | Total samples received |
| `cortex_request_duration_seconds` | Request latency |
| `cortex_compactor_blocks_marked_for_deletion_total` | Blocks scheduled for deletion |

### Grafana Dashboard

Mimir metrics are available in the "Infrastructure Health" dashboard:
- Ingestion rate
- Active series count
- Query latency
- Storage usage

---

## Troubleshooting

### Issue: Mimir Not Receiving Data

**Symptoms**:
- Empty queries in Grafana
- Prometheus logs show remote write errors

**Solution**:
1. Check Mimir is running:
   ```bash
   curl https://mimir-production-1b34.up.railway.app/ready
   ```

2. Verify Prometheus remote_write config:
   ```bash
   # Check Prometheus logs for:
   # "Completed remote write to mimir-remote-write"
   ```

3. Ensure internal networking:
   - Prometheus must use `mimir.railway.internal:9009`
   - Not the public URL

### Issue: Mimir Container Crashes

**Symptoms**:
- Container restarts repeatedly
- Config parsing errors in logs

**Solution**:
1. Use `mimir-railway.yml` (not `mimir.yml`)
2. Remove `query_frontend_address` (only valid in microservices mode)
3. Increase memory to 1024 MB minimum

### Issue: Slow Queries

**Symptoms**:
- Grafana dashboards timeout
- Query errors in Mimir logs

**Solution**:
1. Reduce query range (max 30 days)
2. Use recording rules for expensive queries
3. Check `max_query_parallelism` setting

### Issue: High Memory Usage

**Symptoms**:
- OOM kills
- Ingester restarts

**Solution**:
1. Increase memory allocation
2. Reduce `max_global_series_per_user`
3. Lower `ingestion_rate` limit

---

## Capacity Planning

### Current Limits

| Setting | Value | Impact |
|---------|-------|--------|
| `max_global_series_per_user` | 500,000 | Max unique metrics |
| `ingestion_rate` | 50,000/s | Max samples/second |
| `max_query_lookback` | 30d | Query range limit |
| `compactor_blocks_retention_period` | 30d | Data retention |

### Scaling Recommendations

| Series Count | Memory | CPU |
|--------------|--------|-----|
| < 100,000 | 512 MB | 0.5 |
| 100,000 - 500,000 | 1024 MB | 1 |
| 500,000 - 1,000,000 | 2048 MB | 2 |
| > 1,000,000 | Consider S3 backend | 4+ |

---

## File Structure

```
railway-grafana-stack/
├── mimir/
│   ├── Dockerfile              # Container build
│   ├── mimir.yml               # Local config
│   └── mimir-railway.yml       # Railway config
├── prometheus/
│   ├── prom.yml                # Includes remote_write to Mimir
│   └── entrypoint.sh           # Substitutes MIMIR_URL
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── mimir.yml       # Grafana datasource
└── MIMIR.md                    # This documentation
```

---

## Deployment Checklist

### Initial Setup

- [ ] Create Mimir service in Railway
- [ ] Set root directory to `/mimir`
- [ ] Configure port `9009`
- [ ] Set memory to 1024 MB minimum
- [ ] Configure health check (`/ready`, 60s initial delay)

### After Deployment

- [ ] Verify `/ready` returns "ready"
- [ ] Check Prometheus logs for successful remote write
- [ ] Test Grafana Mimir datasource
- [ ] Query metrics via API

### Updating Configuration

- [ ] Update `mimir-railway.yml` as needed
- [ ] Push changes to GitHub
- [ ] Railway auto-deploys from main branch
- [ ] Verify health after deployment

---

## Quick Commands

```bash
# Check Mimir health
curl https://mimir-production-1b34.up.railway.app/ready

# Query active series count
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/query?query=cortex_ingester_active_series"

# Check ingestion rate
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/query?query=rate(cortex_distributor_received_samples_total[5m])"

# List all metric names
curl "https://mimir-production-1b34.up.railway.app/prometheus/api/v1/labels"

# View Mimir's own metrics
curl https://mimir-production-1b34.up.railway.app/metrics | head -50
```

---

## References

- [Grafana Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Mimir Configuration Reference](https://grafana.com/docs/mimir/latest/configure/)
- [Railway Private Networking](https://docs.railway.app/reference/private-networking)
- [Prometheus Remote Write](https://prometheus.io/docs/specs/remote_write_spec/)

---

**Maintainer**: GatewayZ Team
**Contact**: Infrastructure issues via GitHub
**Last Verified**: January 25, 2026
