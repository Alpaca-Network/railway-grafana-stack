# Redis Monitoring Guide

## Current Redis Setup

Your infrastructure has TWO Redis configurations in Prometheus:

### 1. Local Redis Exporter (Docker Compose)
**Job Name:** `redis_exporter`
**Target:** `redis-exporter:9121`
**Purpose:** Monitors a Redis instance via the `oliver006/redis_exporter` container

**Configuration:**
```yaml
# docker-compose.yml
redis-exporter:
  image: oliver006/redis_exporter:latest
  ports:
    - "9121:9121"
  environment:
    # Set REDIS_ADDR and REDIS_PASSWORD in your .env file
    REDIS_ADDR: ${REDIS_ADDR:-redis:6379}
    REDIS_PASSWORD: ${REDIS_PASSWORD:-}
```

**Required .env Variables:**
```bash
# For Railway Redis
REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
REDIS_PASSWORD=your_redis_password

# For local Redis
REDIS_ADDR=redis:6379
# or for host machine: host.docker.internal:6379
```

**Status:** ✅ Working if Redis instance is accessible and env vars are set

---

### 2. Production Redis (Railway) - COMMENTED OUT
**Job Name:** `redis_gateway_production` (was `redis_gateway`)
**Target:** `redis-production-bb6d.up.railway.app`
**Status:** ❌ **COMMENTED OUT** in prometheus/prom.yml

**Reason:** Redis doesn't expose a `/metrics` endpoint by default. This scrape job will fail unless:
- You've configured Redis to export metrics via a module
- Or you're running a redis-exporter sidecar on Railway

---

## What is redis-exporter?

The [oliver006/redis_exporter](https://github.com/oliver006/redis_exporter) connects to a Redis instance and exposes Prometheus metrics about:

- **Memory Usage:** `redis_memory_used_bytes`, `redis_memory_max_bytes`
- **Client Connections:** `redis_connected_clients`
- **Commands:** `redis_commands_processed_total`, `redis_commands_duration_seconds`
- **Keyspace:** `redis_db_keys`, `redis_db_expires`
- **Replication:** `redis_connected_slaves`, `redis_replication_lag_seconds`
- **Performance:** `redis_cpu_sys_seconds_total`, `redis_evicted_keys_total`

---

## Current Prometheus Configuration

**File:** [prometheus/prom.yml](prometheus/prom.yml)

```yaml
# Local Redis Exporter (Docker Compose)
- job_name: 'redis_exporter'
  scheme: http
  static_configs:
    - targets: ['redis-exporter:9121']
  scrape_interval: 30s  # Redis metrics change slowly
  scrape_timeout: 10s

# Production Redis on Railway - COMMENTED OUT
# NOTE: This endpoint doesn't exist - Redis doesn't expose /metrics
# - job_name: 'redis_gateway_production'
#   scheme: https
#   metrics_path: '/metrics'
#   static_configs:
#     - targets: ['redis-production-bb6d.up.railway.app']
#   scrape_interval: 30s
#   scrape_timeout: 10s
```

---

## ⚠️ Issue with gatewayz-redis-services.json Dashboard

**Problem:** The dashboard is titled "GatewayZ Redis Services" but queries **FastAPI metrics**, not Redis metrics.

**Current Queries:**
```promql
# Panel: Request Rate
sum(rate(fastapi_requests_total[5m]))

# Panel: Success Rate
sum(rate(fastapi_requests_total{status_code="200"}[5m])) /
sum(rate(fastapi_requests_total[5m])) * 100

# Panel: Database Activity
rate(database_queries_total{job="gatewayz_api"}[5m])
```

These queries monitor your **FastAPI application**, not Redis itself.

---

## Options for Redis Monitoring

### Option 1: Monitor Redis via Exporter (Recommended)

**Use the existing redis-exporter setup** to monitor Redis infrastructure metrics.

**What You Get:**
- Redis memory usage
- Connection count
- Command throughput
- Cache hit/miss rates (if using Redis as cache)
- Keyspace statistics

**Dashboard Queries:**
```promql
# Memory Usage
redis_memory_used_bytes{instance="redis-exporter:9121"}

# Connected Clients
redis_connected_clients{instance="redis-exporter:9121"}

# Commands Per Second
rate(redis_commands_processed_total{instance="redis-exporter:9121"}[5m])

# Cache Hit Rate (if configured)
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)
```

**What You Need:**
- Ensure `redis-exporter` can connect to your Redis instance
- Set `REDIS_ADDR` and `REDIS_PASSWORD` environment variables correctly
- Verify exporter is running: `curl http://localhost:9121/metrics`

---

### Option 2: Monitor Application's Redis Usage (Alternative)

If you want to track **how your application uses Redis**, export custom metrics from your backend:

**Metrics to Export:**
```python
from prometheus_client import Counter, Histogram

# Redis operation counts
redis_operations_total = Counter(
    'gatewayz_redis_operations_total',
    'Total Redis operations',
    ['operation', 'database']  # operation: get, set, del, etc.
)

# Redis operation latency
redis_operation_duration_seconds = Histogram(
    'gatewayz_redis_operation_duration_seconds',
    'Redis operation duration',
    ['operation']
)

# Redis connection pool
redis_pool_connections_current = Gauge(
    'gatewayz_redis_pool_connections_current',
    'Current Redis pool connections',
    ['state']  # state: idle, active
)
```

**Dashboard Queries:**
```promql
# Redis Operations Per Second
rate(gatewayz_redis_operations_total[5m])

# Redis Operation Latency P95
histogram_quantile(0.95,
  rate(gatewayz_redis_operation_duration_seconds_bucket[5m])
)

# Redis Pool Utilization
gatewayz_redis_pool_connections_current{state="active"} /
(gatewayz_redis_pool_connections_current{state="active"} +
 gatewayz_redis_pool_connections_current{state="idle"})
```

---

### Option 3: Hybrid Approach (Best of Both Worlds)

**Monitor both:**
1. **Redis infrastructure** (via redis-exporter) - memory, connections, health
2. **Application usage** (via backend metrics) - cache hit rate, operation types, latency

This gives you complete observability:
- Infrastructure health (Is Redis healthy?)
- Application performance (How efficiently are we using Redis?)

---

## Recommended Actions

### For Infrastructure Team:

**1. Verify Redis Exporter Connection**
```bash
# Check if redis-exporter is running and can connect
docker compose logs redis-exporter

# Test metrics endpoint
curl http://localhost:9121/metrics | grep redis_up
# Should show: redis_up 1
```

**2. Deploy Redis Exporter on Railway (Optional)**

If you want to monitor the production Redis instance directly on Railway:

```yaml
# Add to Railway services
redis-exporter:
  image: oliver006/redis_exporter:latest
  environment:
    REDIS_ADDR: redis-production-bb6d.up.railway.app:6379
    REDIS_PASSWORD: ${REDIS_PASSWORD}
  # Railway will assign a URL like: redis-exporter-production.up.railway.app
```

Then update Prometheus:
```yaml
- job_name: 'redis_production'
  scheme: https
  static_configs:
    - targets: ['redis-exporter-production.up.railway.app']
  scrape_interval: 30s
```

---

### For Backend Team:

**Instrument Redis Operations (If Desired)**

Add Prometheus metrics around your Redis calls:

```python
from prometheus_client import Counter, Histogram
import time

# Define metrics
redis_ops = Counter('gatewayz_redis_operations_total',
                    'Redis operations', ['operation'])
redis_latency = Histogram('gatewayz_redis_operation_duration_seconds',
                          'Redis operation latency', ['operation'])

# Instrument Redis calls
async def get_from_cache(key: str):
    start = time.time()
    try:
        result = await redis_client.get(key)
        redis_ops.labels(operation='get').inc()
        redis_latency.labels(operation='get').observe(time.time() - start)
        return result
    except Exception as e:
        redis_ops.labels(operation='get_error').inc()
        raise

async def set_cache(key: str, value: str, ttl: int):
    start = time.time()
    try:
        await redis_client.setex(key, ttl, value)
        redis_ops.labels(operation='set').inc()
        redis_latency.labels(operation='set').observe(time.time() - start)
    except Exception as e:
        redis_ops.labels(operation='set_error').inc()
        raise
```

**What Metrics to Export:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `gatewayz_redis_operations_total` | Counter | `operation` (get, set, del, hget, hset) | Total Redis operations by type |
| `gatewayz_redis_operation_duration_seconds` | Histogram | `operation` | Latency of Redis operations |
| `gatewayz_cache_hits_total` | Counter | `cache_type` | Cache hits (already exported as `cache_hits_total`) |
| `gatewayz_cache_misses_total` | Counter | `cache_type` | Cache misses (already exported as `cache_misses_total`) |
| `gatewayz_cache_size_bytes` | Gauge | `cache_type` | Cache size (already exported as `cache_size_bytes`) |

**Note:** Your backend already exports `cache_hits_total`, `cache_misses_total`, and `cache_size_bytes`. These are perfect for monitoring cache effectiveness!

---

## Fix the gatewayz-redis-services.json Dashboard

### Option A: Rename Dashboard to Match Content

Since the dashboard queries FastAPI metrics, rename it to:
- **"GatewayZ Application Metrics"**
- **"GatewayZ API Performance"**
- **"GatewayZ Backend Dashboard"**

### Option B: Replace Queries with Redis Metrics

Update dashboard to query actual Redis metrics:

**Panel: Redis Memory Usage**
```promql
redis_memory_used_bytes / redis_memory_max_bytes * 100
```

**Panel: Redis Connections**
```promql
redis_connected_clients
```

**Panel: Redis Commands/sec**
```promql
rate(redis_commands_processed_total[5m])
```

**Panel: Cache Hit Rate** (using your existing metrics)
```promql
rate(cache_hits_total[5m]) /
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100
```

### Option C: Combine Both

Create sections in the dashboard:
1. **Redis Infrastructure** - Redis exporter metrics
2. **Application Cache Usage** - Your backend's cache metrics
3. **API Performance** - FastAPI metrics (current panels)

---

## Summary

### What Works Now:
✅ `redis-exporter` container is configured in docker-compose.yml
✅ Prometheus scrapes `redis_exporter` job at `:9121`
✅ Redis-Cache.json dashboard has comprehensive panels for both Redis and application cache metrics
✅ Entrypoint.sh auto-configures local vs Railway environments

### Prerequisites:
⚠️ Set `REDIS_ADDR` and `REDIS_PASSWORD` in your `.env` file
⚠️ For Railway: Set `REDIS_EXPORTER_URL` to your Redis Exporter's public URL

### Recommendations:

**Minimum (No Backend Changes):**
1. Verify redis-exporter can connect to Redis
2. Rename or fix the dashboard to query actual Redis metrics

**Ideal (Backend Changes):**
1. Keep redis-exporter for infrastructure monitoring
2. Add Redis operation instrumentation in backend code
3. Create comprehensive Redis dashboard with both infrastructure and application metrics

---

## Questions for You

1. **Do you want to monitor Redis infrastructure** (memory, connections, throughput)?
   - If yes → Use redis-exporter (already set up)

2. **Do you want to monitor how your app uses Redis** (operation types, latencies)?
   - If yes → Backend team needs to add metrics around Redis calls

3. **What should the gatewayz-redis-services dashboard show?**
   - Option A: Rename it to match current queries (FastAPI metrics)
   - Option B: Replace queries with Redis metrics
   - Option C: Delete it (info is in other dashboards)

4. **Is the redis-exporter currently working?**
   - Check: `curl http://localhost:9121/metrics` (when Docker Compose is running)
   - Should see Redis metrics if connection is successful
