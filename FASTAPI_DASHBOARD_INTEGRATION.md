# FastAPI Dashboard Integration - Backend Agent Endpoints

This document integrates the backend agent's comprehensive instrumentation with the FastAPI Dashboard, Loki, and Tempo.

---

## Backend Agent Implementation

Your backend agent has implemented:

### 1. Metrics Endpoints
- **GET** `/metrics` - Prometheus format metrics
- **GET** `/api/metrics/status` - Metrics service status
- **GET** `/api/metrics/summary` - Registered metrics list
- **POST** `/api/metrics/test` - Generate test metrics
- **GET** `/api/metrics/grafana-queries` - PromQL queries for Grafana
- **GET** `/api/metrics/health` - Metrics health check

### 2. Instrumentation Endpoints
- **GET** `/api/instrumentation/health` - Overall instrumentation health
- **GET** `/api/instrumentation/trace-context` - Current trace/span IDs
- **GET** `/api/instrumentation/loki/status` - Loki configuration (Admin)
- **GET** `/api/instrumentation/tempo/status` - Tempo configuration (Admin)
- **GET** `/api/instrumentation/config` - Complete configuration (Admin)
- **POST** `/api/instrumentation/test-trace` - Generate test trace (Admin)
- **POST** `/api/instrumentation/test-log` - Generate test log (Admin)
- **GET** `/api/instrumentation/environment-variables` - Environment vars (Admin)

### 3. Admin API Key
```
gw_live_wTfpLJ5VB28qMXpOAhr7Uw
```

---

## Prometheus Metrics Exposed

### HTTP Request Metrics
```
fastapi_requests_total{app_name, method, path, status_code}
fastapi_requests_duration_seconds{app_name, method, path}
fastapi_requests_in_progress{app_name, method, path}
fastapi_request_size_bytes{app_name, method, path}
fastapi_response_size_bytes{app_name, method, path}
fastapi_exceptions_total{app_name, exception_type}
```

### Model Inference Metrics
```
model_inference_requests_total{provider, model, status}
model_inference_duration_seconds{provider, model}
tokens_used_total{provider, model, token_type}
credits_used_total{provider, model}
```

### Provider Health Metrics
```
provider_availability{provider}
provider_error_rate{provider}
provider_response_time_seconds{provider}
```

### Cache Metrics
```
cache_hits_total{cache_name}
cache_misses_total{cache_name}
cache_size_bytes{cache_name}
```

---

## Grafana Dashboard Configuration

### FastAPI Dashboard Panels

#### Panel 1: Total Requests
```json
{
  "title": "Total Requests",
  "type": "stat",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "sum(rate(fastapi_requests_total[5m]))"
    }
  ],
  "unit": "reqps"
}
```

#### Panel 2: Requests Per Minute
```json
{
  "title": "Requests Per Minute",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total[1m]) * 60",
      "legendFormat": "{{method}} {{path}}"
    }
  ]
}
```

#### Panel 3: Errors Per Second
```json
{
  "title": "Errors Per Second",
  "type": "stat",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total{status_code=~\"4..|5..\"}[1s])"
    }
  ],
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 1},
      {"color": "red", "value": 5}
    ]
  }
}
```

#### Panel 4: Average Response Time
```json
{
  "title": "Average Response Time",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_requests_duration_seconds_sum[5m]) / rate(fastapi_requests_duration_seconds_count[5m])",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "unit": "s"
}
```

#### Panel 5: Request Duration P60
```json
{
  "title": "Request Duration P60",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "histogram_quantile(0.60, rate(fastapi_requests_duration_seconds_bucket[5m]))",
      "legendFormat": "P60 {{method}} {{path}}"
    }
  ],
  "unit": "s"
}
```

#### Panel 6: CPU Usage
```json
{
  "title": "CPU Usage",
  "type": "gauge",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(process_cpu_seconds_total[5m]) * 100"
    }
  ],
  "unit": "percent",
  "min": 0,
  "max": 100,
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 50},
      {"color": "red", "value": 80}
    ]
  }
}
```

#### Panel 7: Memory Usage
```json
{
  "title": "Memory Usage",
  "type": "gauge",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "process_resident_memory_bytes / 1024 / 1024"
    }
  ],
  "unit": "decbytes",
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 512},
      {"color": "red", "value": 1024}
    ]
  }
}
```

#### Panel 8: Logger Stream
```json
{
  "title": "Logger Stream",
  "type": "logs",
  "datasource": "Loki",
  "targets": [
    {
      "expr": "{service=\"gatewayz-api\"}"
    }
  ],
  "options": {
    "showLabels": ["level", "endpoint", "status_code"],
    "showTime": true
  }
}
```

---

## Loki Integration

### Log Format
The backend agent outputs structured JSON logs to STDOUT:

```json
{
  "timestamp": "2025-12-18T01:23:45.123Z",
  "level": "INFO",
  "service": "gatewayz-api",
  "endpoint": "/v1/chat/completions",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 45,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Request completed"
}
```

### Loki Queries

**All Logs:**
```logql
{service="gatewayz-api"}
```

**Error Logs:**
```logql
{service="gatewayz-api", level="ERROR"}
```

**Slow Requests (>1s):**
```logql
{service="gatewayz-api"} | json | duration_ms > 1000
```

**By Endpoint:**
```logql
{service="gatewayz-api"} | json | endpoint="/v1/chat/completions"
```

**By Trace ID:**
```logql
{service="gatewayz-api"} | json | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"
```

---

## Tempo Integration

### Trace Context
The backend agent automatically instruments all requests with OpenTelemetry:

```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "service_name": "gatewayz-api",
  "operation_name": "POST /v1/chat/completions",
  "duration_ms": 45
}
```

### Tempo Queries

**Service Traces:**
```
service.name="gatewayz-api"
```

**Slow Traces (>1s):**
```
service.name="gatewayz-api" && duration > 1s
```

**Error Traces:**
```
service.name="gatewayz-api" && status.code=error
```

**By Operation:**
```
service.name="gatewayz-api" && name="/v1/chat/completions"
```

---

## Trace-Log-Metric Correlation

All three observability signals are correlated by trace ID:

1. **Request arrives** → Gets unique trace_id
2. **Prometheus metric** → Increments counter with trace_id label
3. **Loki log** → Includes trace_id in JSON
4. **Tempo trace** → Contains trace_id in root span

**In Grafana:**
- Click log entry → See all related traces
- Click trace → See all related logs
- Click metric → See related logs and traces

---

## Local Testing Setup

### 1. Start Docker Compose Stack
```bash
docker-compose up -d
```

### 2. Verify Services Running
```bash
docker-compose ps
```

Expected services:
- prometheus (port 9090)
- grafana (port 3000)
- loki (port 3100)
- tempo (port 3200)
- fastapi_backend (port 8000)

### 3. Generate Test Metrics
```bash
# Generate test metrics
curl -X POST http://localhost:8000/api/metrics/test

# Generate test trace
curl -X POST \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  http://localhost:8000/api/instrumentation/test-trace

# Generate test log
curl -X POST \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  http://localhost:8000/api/instrumentation/test-log
```

### 4. Generate Traffic
```bash
# Generate 100 requests
for i in {1..100}; do
  curl http://localhost:8000/api/users/1
done

# Check metrics updated
curl http://localhost:8000/metrics | grep fastapi_requests_total
```

### 5. Verify Prometheus Scraping
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=fastapi_requests_total'
```

### 6. Verify Loki Ingestion
```bash
# Query Loki
curl 'http://localhost:3100/loki/api/v1/query?query={service="gatewayz-api"}'
```

### 7. Verify Tempo Traces
```bash
# Query Tempo
curl 'http://localhost:3200/api/traces'
```

### 8. Access Grafana Dashboard
1. Open http://localhost:3000
2. Login with admin/yourpassword123
3. Go to **Dashboards → FastAPI Dashboard**
4. Verify all 8 panels show data

---

## Verification Checklist

- [ ] Prometheus scraping backend metrics
- [ ] Loki ingesting structured logs
- [ ] Tempo receiving traces
- [ ] Grafana datasources connected
- [ ] FastAPI Dashboard loads
- [ ] All 8 panels display data
- [ ] Metrics update every 15 seconds
- [ ] Logger stream shows real-time logs
- [ ] Trace-log correlation working

---

## Troubleshooting

### Metrics Not Appearing
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | head -20

# Check Prometheus scrape config
cat prometheus/prom.yml | grep -A 5 fastapi_backend

# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="fastapi_backend")'
```

### Logs Not Appearing
```bash
# Check Loki is running
docker-compose ps loki

# Query Loki directly
curl 'http://localhost:3100/loki/api/v1/label'

# Check service label
curl 'http://localhost:3100/loki/api/v1/query?query={service="gatewayz-api"}'
```

### Traces Not Appearing
```bash
# Check Tempo is running
docker-compose ps tempo

# Verify backend is sending traces
curl -X POST \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  http://localhost:8000/api/instrumentation/test-trace

# Query Tempo
curl 'http://localhost:3200/api/traces'
```

### Grafana Panels Empty
```bash
# Generate traffic
for i in {1..100}; do curl http://localhost:8000/api/users/1; done

# Wait 30 seconds for metrics to update
sleep 30

# Refresh Grafana dashboard
# Press F5 in browser
```

---

## Environment Variables

### Backend Service
```bash
APP_NAME=gatewayz
SERVICE_NAME=gatewayz-api
ENVIRONMENT=production

# Prometheus (auto-exposed at /metrics)
# No additional config needed

# Loki
LOKI_ENABLED=true
LOKI_PUSH_URL=http://loki:3100/loki/api/v1/push

# Tempo
TEMPO_ENABLED=true
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo:4317

# Admin API Key
ADMIN_API_KEY=gw_live_wTfpLJ5VB28qMXpOAhr7Uw
```

---

## Data Flow Diagram

```
FastAPI Backend (localhost:8000)
    │
    ├─→ /metrics endpoint
    │       ↓
    │   Prometheus scrapes every 15s
    │       ↓
    │   Grafana queries Prometheus
    │       ↓
    │   7 metric panels update
    │
    ├─→ STDOUT JSON logs
    │       ↓
    │   Loki ingests logs
    │       ↓
    │   Grafana queries Loki
    │       ↓
    │   Logger Stream panel updates
    │
    ├─→ OpenTelemetry gRPC (localhost:4317)
    │       ↓
    │   Tempo stores traces
    │       ↓
    │   Grafana Tempo dashboard
    │
    └─→ Admin Endpoints (with API key)
            ├─ /api/metrics/status
            ├─ /api/metrics/summary
            ├─ /api/instrumentation/health
            ├─ /api/instrumentation/config
            └─ /api/instrumentation/test-*
```

---

## Next Steps

1. **Start local stack:** `docker-compose up -d`
2. **Generate test data:** Run test commands above
3. **Access Grafana:** http://localhost:3000
4. **Verify dashboard:** All 8 panels should show data
5. **Test correlation:** Click between logs, traces, and metrics
6. **Deploy to Railway:** Push to main branch when verified

---

## Support

For issues or questions:
1. Check Prometheus targets: http://localhost:9090/targets
2. Check Loki labels: `curl http://localhost:3100/loki/api/v1/label`
3. Check Tempo traces: `curl http://localhost:3200/api/traces`
4. Review backend logs: `docker-compose logs fastapi_backend`
5. Check Grafana datasources: http://localhost:3000/datasources
