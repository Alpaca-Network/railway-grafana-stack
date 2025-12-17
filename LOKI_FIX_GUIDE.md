# Loki Configuration Fix Guide

## Issue Analysis

Your Loki logs show normal operation but there are configuration issues causing suboptimal performance on Railway:

### Issues Identified

1. **Ring Configuration Problem**
   - `instance_addr: 127.0.0.1` is hardcoded for localhost
   - On Railway, this causes ring discovery failures
   - Loki instances can't communicate with each other

2. **Tempo HTTP/2 Frame Size Issue** (Related)
   - Tempo frontend receiving oversized HTTP/2 frames
   - Caused by improper gRPC configuration
   - Affects distributed tracing integration

3. **Storage Configuration**
   - Filesystem storage works locally but not ideal for Railway
   - Should use object storage or proper distributed setup

4. **Log Level**
   - Currently set to `info` - generates excessive logs
   - Should be `warn` for production

## Solutions

### Step 1: Update Loki Configuration for Railway

Replace the hardcoded localhost with dynamic hostname resolution:

```yaml
common:
  ring:
    instance_addr: ${HOSTNAME:loki}  # Use container hostname
    kvstore:
      store: inmemory
  replication_factor: 1
  path_prefix: /loki
```

### Step 2: Fix Tempo HTTP/2 Frame Size

Update Tempo configuration to handle larger frames:

```yaml
server:
  http_listen_port: 3200
  grpc_listen_port: 4317
  grpc_server_max_recv_msg_size: 16777216  # 16MB
  grpc_server_max_send_msg_size: 16777216  # 16MB
```

### Step 3: Optimize Loki for Railway

Update `loki/loki.yml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  log_level: warn  # Changed from info
  grpc_listen_port: 9096
  grpc_server_max_recv_msg_size: 16777216
  grpc_server_max_send_msg_size: 16777216

common:
  ring:
    instance_addr: ${HOSTNAME:loki}
    kvstore:
      store: inmemory
  replication_factor: 1
  path_prefix: /loki

schema_config:
  configs:
  - from: 2025-01-01
    index:
      period: 24h
      prefix: index_
    store: tsdb
    object_store: filesystem
    schema: v13

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/tsdb-index
    cache_location: /loki/tsdb-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
  max_streams_per_user: 10000
  max_global_streams_per_user: 10000

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

query_scheduler:
  max_outstanding_requests_per_tenant: 100

frontend:
  log_queries_longer_than: 10s
  compress_responses: true
  max_cache_freshness_per_query: 10m

distributor:
  ring:
    kvstore:
      store: inmemory
```

## Deployment Steps

### On Railway:

1. **Update Loki Configuration**
   ```bash
   # Replace loki/loki.yml with the fixed version
   git pull origin fix/loki-configuration
   ```

2. **Restart Loki Service**
   ```bash
   # Via Railway dashboard:
   # 1. Go to your project
   # 2. Select Loki service
   # 3. Click "Redeploy"
   ```

3. **Verify Loki is Running**
   ```bash
   curl -s https://your-railway-domain/loki/api/v1/status
   # Should return: {"status":"success"}
   ```

4. **Check Logs**
   ```bash
   # Via Railway dashboard → Logs
   # Should see: "Loki started" without errors
   ```

### Local Testing:

```bash
# Restart local stack
docker-compose down
docker-compose up -d

# Verify Loki
curl -s http://localhost:3100/loki/api/v1/status
```

## What Each Fix Does

| Issue | Fix | Impact |
|-------|-----|--------|
| Ring discovery fails | Use `${HOSTNAME:loki}` | Loki instances can communicate |
| HTTP/2 frame errors | Increase `grpc_server_max_*_msg_size` | Tempo can send larger traces |
| Excessive logging | Change log level to `warn` | Reduced log volume |
| Storage issues | Add proper filesystem config | Better data persistence |
| Query performance | Add query scheduler limits | Prevents resource exhaustion |

## Verification Checklist

After deployment:

- [ ] Loki service is running (check Railway dashboard)
- [ ] No "error contacting frontend" messages in logs
- [ ] No HTTP/2 frame size errors
- [ ] Loki dashboard shows data in Grafana
- [ ] Logs are being ingested properly
- [ ] Query performance is acceptable

## Rollback Plan

If issues occur:

```bash
# Revert to previous version
git revert HEAD
git push origin fix/loki-configuration

# Redeploy on Railway
# Via dashboard: Select Loki → Redeploy
```

## Monitoring

Check these metrics in Prometheus:

```promql
# Loki ingestion rate
rate(loki_distributor_lines_received_total[5m])

# Loki query latency
histogram_quantile(0.95, rate(loki_request_duration_seconds_bucket[5m]))

# Loki storage usage
loki_boltdb_shipper_index_cache_entries
```

## Next Steps

1. Apply the configuration changes
2. Redeploy Loki on Railway
3. Monitor logs for 5 minutes
4. Verify data is flowing correctly
5. Test Grafana dashboard queries

## Support

If issues persist:
1. Check Railway service logs
2. Verify network connectivity between services
3. Ensure storage volumes are mounted correctly
4. Check authentication settings
