# Railway Deployment Verification Guide

## Overview
This guide verifies that all observability services (Prometheus, Loki, Tempo, Grafana) are properly deployed and communicating on Railway.

## Services Deployed on Railway

### 1. Prometheus
- **Port:** 9090 (HTTP)
- **Metrics Path:** `/metrics`
- **Scrape Targets:**
  - `prometheus` (self)
  - `example_api:9091`
  - `api.gatewayz.ai` (gatewayz_api)
  - `redis-exporter:9121`
  - `redis-production-bb6d.up.railway.app` (redis_gateway)
  - `api.gatewayz.ai` (fastapi_backend)
  - `gatewayz-staging.up.railway.app` (gatewayz_staging)

### 2. Loki
- **Port:** 3100 (HTTP)
- **gRPC Port:** 9096
- **Configuration:**
  - `instance_addr: 0.0.0.0` (allows Railway service communication)
  - Storage: `/loki` (persistent volume)
  - Schema: v13 with TSDB
  - Max streams: 10,000 per user

### 3. Tempo
- **HTTP Port:** 3200 (querying)
- **gRPC Port:** 3201 (querying)
- **OTLP gRPC Ingest:** 4317
- **OTLP HTTP Ingest:** 4318
- **Configuration:**
  - `frontend_address: 0.0.0.0:3200` (allows Railway service communication)
  - Storage: `/var/tempo/traces` (persistent volume)
  - Max message sizes: 16MB (send/receive)

### 4. Grafana
- **Port:** 3000 (HTTP)
- **Datasources:**
  - Prometheus: `http://prometheus:9090`
  - Loki: `http://loki:3100`
  - Tempo: `http://tempo:3200`
- **Dashboards:**
  - FastAPI Dashboard
  - Models Monitoring
  - Tempo Distributed Tracing
  - Loki Logs
  - GatewayZ Application Health
  - Provider Management

## Verification Checklist

### Step 1: Verify Service Health
```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Check Loki health
curl http://loki:3100/loki/api/v1/status/buildinfo

# Check Tempo health
curl http://tempo:3200/status

# Check Grafana health
curl http://grafana:3000/api/health
```

### Step 2: Verify Datasource Connectivity
In Grafana:
1. Go to **Configuration → Data Sources**
2. Verify each datasource shows "Data source is working"
   - Prometheus
   - Loki
   - Tempo

### Step 3: Verify Metrics Collection
In Prometheus:
1. Go to **Status → Targets**
2. Confirm all scrape jobs show "UP":
   - prometheus
   - example_api
   - gatewayz_api
   - redis
   - redis_gateway
   - fastapi_backend
   - gatewayz_staging

### Step 4: Verify Logs Ingestion
In Grafana:
1. Go to **Explore**
2. Select **Loki** datasource
3. Run query: `{job="docker"}`
4. Confirm logs are appearing

### Step 5: Verify Traces Ingestion
In Grafana:
1. Go to **Explore**
2. Select **Tempo** datasource
3. Search for traces
4. Confirm traces are appearing (if backend is sending traces)

## Common Issues and Solutions

### Issue: Tempo "frame too large" Error
**Cause:** HTTP/2 frame size mismatch between Tempo and Grafana  
**Status:** Non-blocking - Tempo still functions for trace storage and querying  
**Solution:** Already configured with `grpc_server_max_recv_msg_size: 16777216` and `grpc_server_max_send_msg_size: 16777216`

### Issue: Loki Connection Refused
**Cause:** `instance_addr: 127.0.0.1` prevents Railway service communication  
**Status:** FIXED - Changed to `instance_addr: 0.0.0.0`  
**Solution:** Updated `loki/loki.yml` to use 0.0.0.0

### Issue: Tempo Frontend Connection Error
**Cause:** `frontend_address: localhost:3200` doesn't work on Railway  
**Status:** FIXED - Changed to `frontend_address: 0.0.0.0:3200`  
**Solution:** Updated `tempo/tempo.yml` to use 0.0.0.0

### Issue: No Data in Dashboards
**Cause:** Metrics not being scraped or queries don't match metric names  
**Status:** Depends on backend instrumentation  
**Solution:** 
1. Verify backend is emitting metrics
2. Check Prometheus scrape targets are UP
3. Verify metric names in PromQL queries match actual metrics

## Instrumentation Integration

### FastAPI Backend Metrics
The FastAPI Dashboard expects these metrics from your backend:
- `http_requests_total` - Total HTTP requests
- `fastapi_requests_duration_seconds_*` - Request duration histogram
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage

### Models Monitoring Metrics
The Models Monitoring Dashboard expects:
- `model_requests_total{model="<name>"}` - Requests per model
- `model_errors_total{model="<name>"}` - Errors per model
- `model_latency_ms_*{model="<name>"}` - Latency histogram
- `model_tokens_used_total{model="<name>"}` - Token usage

### Loki Log Ingestion
Logs should be sent with labels:
- `service` - Service name (e.g., "gatewayz-api")
- `job` - Job name (e.g., "docker")
- `level` - Log level (e.g., "info", "error")

### Tempo Trace Ingestion
Traces should be sent via OTLP:
- **gRPC:** `tempo:4317`
- **HTTP:** `tempo:4318`

## Railway Environment Variables

Set these on Railway for proper configuration:

```
# Prometheus
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_INTERNAL_URL=http://prometheus:9090

# Loki
LOKI_URL=http://loki:3100
LOKI_INTERNAL_URL=http://loki:3100

# Tempo
TEMPO_URL=http://tempo:3200
TEMPO_INTERNAL_URL=http://tempo:3200
TEMPO_INTERNAL_HTTP_INGEST=http://tempo:4318
TEMPO_INTERNAL_GRPC_INGEST=http://tempo:4317

# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>

# Staging API
GATEWAYZ_STAGING_API_KEY=gw_live_wTfpLJ5VB28qMXpOAhr7Uw
```

## Deployment Steps

### 1. Push Changes to Main
```bash
git add tempo/tempo.yml loki/loki.yml RAILWAY_DEPLOYMENT_VERIFICATION.md
git commit -m "fix: configure Tempo and Loki for Railway service communication"
git push origin main
```

### 2. Redeploy on Railway
1. Go to Railway Dashboard
2. Select your project
3. For each service (Prometheus, Loki, Tempo, Grafana):
   - Click the service
   - Click "Redeploy"
   - Wait for deployment to complete

### 3. Verify Deployment
1. Access Grafana at your Railway URL
2. Go to **Configuration → Data Sources**
3. Verify all datasources show "Data source is working"
4. Go to **Dashboards** and verify data is flowing

## Testing with Staging Endpoint

### Test Anthropic API Endpoint
```bash
curl -X POST https://gatewayz-staging.up.railway.app/v1/messages \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, Claude!"}
    ]
  }'
```

### Verify Metrics are Scraped
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://gatewayz-staging.up.railway.app/metrics | grep -E "model_|http_"
```

## Monitoring Dashboard Status

### FastAPI Dashboard
- **Status:** Ready for data (awaiting backend instrumentation)
- **Panels:** 8 (Total Requests, Requests/min, Errors/sec, Response Time, P60 Duration, CPU, Memory, Logs)
- **Data Sources:** Prometheus, Loki

### Models Monitoring Dashboard
- **Status:** Ready for data (awaiting backend instrumentation)
- **Panels:** 11 (Throughput, Latency, Error Rate, Token Usage, Model Distribution, Hourly Distribution, Availability)
- **Data Sources:** Prometheus

### Tempo Distributed Tracing
- **Status:** Ready for traces (awaiting backend instrumentation)
- **Data Source:** Tempo

### Loki Logs
- **Status:** Ready for logs (awaiting log shipping)
- **Data Source:** Loki

## Next Steps

1. **Implement Backend Instrumentation**
   - Add Prometheus metrics to FastAPI backend
   - Add structured JSON logging to Loki
   - Add OpenTelemetry tracing to Tempo

2. **Configure Log Shipping**
   - Set up log forwarding from backend to Loki
   - Configure appropriate labels for filtering

3. **Set Up Alerting**
   - Create alert rules for high error rates
   - Create alert rules for low availability
   - Configure notification channels

4. **Create Runbooks**
   - Document common issues and resolutions
   - Create escalation procedures
   - Document SLA targets
