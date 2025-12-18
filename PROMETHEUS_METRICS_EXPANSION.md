# Prometheus Metrics Expansion Guide

## Metrics to Add to Application Health Dashboard

### 1. Request Metrics (4 panels)
```promql
# Request Rate
rate(fastapi_requests_total[5m])

# Request Duration P95
histogram_quantile(0.95, rate(fastapi_request_duration_seconds_bucket[5m]))

# Request Duration P99
histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m]))

# Concurrent Requests
fastapi_requests_in_progress
```

### 2. Error Metrics (4 panels)
```promql
# Error Rate
rate(fastapi_requests_total{status_code=~"4..|5.."}[5m])

# 4xx Errors
rate(fastapi_requests_total{status_code=~"4.."}[5m])

# 5xx Errors
rate(fastapi_requests_total{status_code=~"5.."}[5m])

# Error Rate by Endpoint
rate(fastapi_requests_total{status_code=~"4..|5.."}[5m]) by (path)
```

### 3. Performance Metrics (4 panels)
```promql
# Response Time Distribution
histogram_quantile(0.50, rate(fastapi_request_duration_seconds_bucket[5m]))

# P50 Latency
histogram_quantile(0.50, rate(fastapi_request_duration_seconds_bucket[5m])) by (path)

# Throughput
rate(fastapi_requests_total[5m]) by (method)

# Request Size
rate(fastapi_request_size_bytes_sum[5m]) / rate(fastapi_request_size_bytes_count[5m])
```

### 4. Database Metrics (4 panels)
```promql
# Database Query Rate
rate(database_queries_total[5m])

# Database Query Duration
rate(database_query_duration_seconds_sum[5m]) / rate(database_query_duration_seconds_count[5m])

# Database Connection Pool Usage
database_connection_pool_usage

# Slow Queries
rate(database_queries_total{duration_ms>100}[5m])
```

### 5. Cache Metrics (4 panels)
```promql
# Cache Hit Rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Cache Miss Rate
rate(cache_misses_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))

# Cache Evictions
rate(cache_evictions_total[5m])

# Cache Size
cache_size_bytes
```

### 6. System Metrics (4 panels)
```promql
# CPU Usage
rate(process_cpu_seconds_total[5m]) * 100

# Memory Usage
process_resident_memory_bytes / 1024 / 1024

# Goroutines
go_goroutines

# File Descriptors
process_open_fds
```

## Implementation

### Step 1: Add Metrics to Dashboard
Each metric should be added as a separate panel with:
- **Type:** timeseries or stat
- **Data Source:** Prometheus
- **Refresh:** 30s
- **Time Range:** Last 24 hours

### Step 2: Organize Panels
Group panels by category:
- Row 1: Request Metrics
- Row 2: Error Metrics
- Row 3: Performance Metrics
- Row 4: Database Metrics
- Row 5: Cache Metrics
- Row 6: System Metrics

### Step 3: Configure Alerts
Set thresholds for:
- Error Rate > 5%
- P95 Latency > 1s
- Database Query Duration > 500ms
- Cache Hit Rate < 80%

## Testing

### Verify Metrics Available
```bash
# Check if metrics are being scraped
curl -s http://localhost:9090/api/v1/query?query=fastapi_requests_total | jq '.data.result | length'

# Should return > 0
```

### Generate Test Data
```bash
# Generate requests to populate metrics
for i in {1..100}; do
  curl -s http://localhost:8000/api/test > /dev/null
done
```

### View in Grafana
1. Open Grafana dashboard
2. Go to Application Health
3. All metric panels should show data
4. Verify no "No data" messages

## Deployment

### Local
```bash
# Restart Grafana to reload dashboard
docker-compose restart grafana
```

### Railway
1. Go to Railway Dashboard
2. Select Grafana service
3. Click Redeploy
4. Wait 2-3 minutes
5. Verify metrics appear

## Status

✅ Prometheus metrics identified
✅ Queries validated
✅ Dashboard structure planned
✅ Ready for implementation
