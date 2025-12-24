# Dashboard Fixes - Comprehensive Guide

## Issues Fixed

### 1. Tempo Plugin Error & HTTP/2 Frame Size
**Problem:** "Plugin Tempo not found" + HTTP/2 frame too large errors
**Root Cause:** 
- Missing metrics generator configuration
- gRPC frame size too small (default 4MB)
- Missing querier frontend worker config

**Solution:**
- Added `metrics_generator` section to generate metrics from traces
- Increased `grpc_server_max_recv_msg_size` to 16MB
- Increased `grpc_server_max_send_msg_size` to 16MB
- Added `grpc_client_config` to querier frontend worker
- Set `max_recv_msg_size_mb: 16` for OTLP gRPC receiver

### 2. Loki Parsing Errors
**Problem:** "parse error on line 0 col 56 not valid duration string"
**Root Cause:** `$__rate_interval` variable not supported in Loki queries
**Solution:** Replaced `$__rate_interval` with fixed `[5m]` duration

### 3. Missing Prometheus Metrics
**Problem:** Dashboard not populated with enough metrics
**Solution:** Adding 20+ new Prometheus metrics panels to dashboard

## Files Modified

1. `tempo/tempo.yml` - Fixed gRPC configuration
2. `grafana/dashboards/loki-logs.json` - Fixed duration parsing
3. `grafana/dashboards/gatewayz-application-health.json` - Added Prometheus metrics

## Deployment Steps

### Step 1: Deploy Tempo Fix (2 min)
```bash
git pull origin fix/dashboards-and-tempo
# On Railway: Redeploy Tempo service
```

### Step 2: Verify Tempo
```bash
curl -s http://localhost:3200/api/traces | jq 'keys'
# Should return trace data without HTTP/2 errors
```

### Step 3: Verify Loki
```bash
curl -s http://localhost:3100/loki/api/v1/label | jq '.values'
# Should return labels without parse errors
```

### Step 4: Check Dashboards
- Tempo Distributed Tracing: Should show traces without plugin error
- Loki Logs: Should show log data without parse errors
- Application Health: Should show all Prometheus metrics

## Metrics Added to Prometheus Dashboard

### Request Metrics
- Request Rate (requests/sec)
- Request Duration (p50, p95, p99)
- Request Size (bytes)
- Response Size (bytes)

### Error Metrics
- Error Rate (errors/sec)
- Error Count by Status Code
- Error Rate by Endpoint
- 4xx vs 5xx Errors

### Performance Metrics
- Response Time Distribution
- Latency Percentiles
- Throughput (requests/sec)
- Concurrent Requests

### Database Metrics
- Query Count
- Query Duration
- Connection Pool Usage
- Slow Queries

### Cache Metrics
- Cache Hit Rate
- Cache Miss Rate
- Cache Evictions
- Cache Size

### System Metrics
- CPU Usage
- Memory Usage
- Disk I/O
- Network I/O

## Status

✅ Tempo configuration fixed
✅ Loki parsing errors fixed
✅ Prometheus metrics expanded
✅ All dashboards ready for deployment
