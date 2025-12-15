# FastAPI Observability Example

A production-ready FastAPI application with full observability instrumentation for Grafana, Prometheus, Tempo, and Loki.

## Features

✅ **OpenTelemetry Tracing** - Distributed tracing to Tempo
✅ **Prometheus Metrics** - Request metrics with `app_name` label for Grafana dashboard
✅ **Structured Logging** - Log correlation with traces
✅ **Health Checks** - `/health` endpoint for monitoring
✅ **Railway Ready** - Automatic PORT configuration and internal networking
✅ **Docker Ready** - Works locally with Docker Compose

## Quick Start

### Local Development

```bash
# From repo root
docker compose up -d

# Test the app
curl http://localhost:8000/
curl http://localhost:8000/hello?name=World
curl http://localhost:8000/metrics
```

### Railway Deployment

#### Method 1: Railway UI (Recommended)

1. **Create new service** in your Railway project
2. **Connect repository** and set root directory to `fastapi-app`
3. **Add environment variables**:
   ```
   SERVICE_NAME=fastapi-app
   TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
   ```
4. **Deploy** ✅

#### Method 2: Railway CLI

```bash
railway login
railway link
railway up
```

## Environment Variables

### Required
- `SERVICE_NAME` - Application name (default: `fastapi-app`)

### Optional (Auto-configured on Railway)
- `PORT` - Server port (Railway assigns automatically)
- `TEMPO_URL` - Tempo HTTP ingest endpoint for traces
- `TEMPO_INTERNAL_HTTP_INGEST` - Alternative Tempo URL
- `LOKI_URL` - Loki endpoint for logs
- `PROMETHEUS_URL` - Prometheus endpoint for metrics

### Railway Setup Example

```bash
# In Railway UI, add these variables:
SERVICE_NAME=fastapi-app
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}
PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
```

The app will automatically:
- Use Railway's `PORT` environment variable
- Connect to Tempo via Railway's internal networking
- Expose metrics for Prometheus scraping
- Send traces to Tempo
- Log with trace correlation

## API Endpoints

### Health Check
```bash
GET /health
```
Returns application health status. Used by Railway for health checks.

### Root
```bash
GET /
```
Basic hello endpoint with service info.

### Hello Endpoint
```bash
GET /hello?name=World
```
Example endpoint with:
- OpenTelemetry custom span
- Structured logging
- Request metrics

### Slow Endpoint
```bash
GET /slow
```
Simulates slow operation (2s delay) for testing:
- High-latency traces
- Performance monitoring
- Timeout handling

### Error Endpoint
```bash
GET /error
```
Intentionally throws exception for testing:
- Error tracking
- Exception logging
- Error rate metrics

### Metrics Endpoint
```bash
GET /metrics
```
Prometheus metrics endpoint exposing:
- `fastapi_app_info{app_name}` - Critical for Grafana dashboard
- `fastapi_requests_total` - Request counter
- `fastapi_request_duration_seconds` - Request latency histogram

## Metrics Explained

### fastapi_app_info
**Critical for Grafana Dashboard**

```python
APP_INFO = Info('fastapi_app', 'FastAPI application info')
APP_INFO.info({'app_name': SERVICE_NAME})
```

This metric populates the `app_name` dropdown in the FastAPI Observability dashboard (ID: 16110).

Example output:
```
fastapi_app_info{app_name="fastapi-app"} 1.0
```

### Request Metrics

```python
REQUEST_COUNT.labels(
    method="GET",
    endpoint="/hello",
    status="200",
    service="fastapi-app"
).inc()
```

Tracks:
- Request count by method, endpoint, status
- Request duration histograms
- Service identification

## Observability Integration

### Traces (Tempo)

```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint=f"{TEMPO_URL}/v1/traces"
)
```

- Automatic FastAPI instrumentation
- Custom spans for business logic
- Distributed tracing across services

### Metrics (Prometheus)

```python
from prometheus_client import Counter, Histogram, Info

# Expose at /metrics endpoint
```

- Standard Prometheus format
- Custom labels for filtering
- Automatic scraping by Prometheus

### Logs (Loki)

```python
from opentelemetry.instrumentation.logging import LoggingInstrumentor

LoggingInstrumentor().instrument(set_logging_format=True)
```

- Structured logging with trace context
- Automatic correlation with traces
- Use Locomotive on Railway for automatic log forwarding

## Grafana Dashboard Setup

1. **Import Dashboard**
   - Go to Grafana → Dashboards → Import
   - Enter ID: `16110`
   - Select datasources (Prometheus, Tempo, Loki)

2. **Select Application**
   - Use `app_name` dropdown
   - Select `fastapi-app`

3. **Verify Data**
   - Metrics: Request rates, latency percentiles
   - Traces: Distributed traces with spans
   - Logs: Correlated logs with trace IDs

## Adding to Prometheus

Add to `prometheus/prom.yml`:

```yaml
scrape_configs:
  - job_name: 'fastapi-app'
    scheme: http
    metrics_path: '/metrics'
    static_configs:
      - targets: ['fastapi_app:8000']  # Docker
      # OR
      - targets: ['fastapi-app.railway.internal:8000']  # Railway
    scrape_interval: 15s
```

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
# Set environment variables
export SERVICE_NAME=fastapi-app
export TEMPO_URL=http://localhost:4318

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Generate traffic
for i in {1..20}; do
  curl http://localhost:8000/hello?name=User$i
  sleep 0.5
done

# Check metrics
curl http://localhost:8000/metrics | grep fastapi_app_info

# Expected:
# fastapi_app_info{app_name="fastapi-app"} 1.0
```

## Configuration Files

### railway.json
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### App name not showing in Grafana

```bash
# Check metric is exposed
curl http://localhost:8000/metrics | grep fastapi_app_info

# Should output:
# fastapi_app_info{app_name="fastapi-app"} 1.0

# If missing, check SERVICE_NAME env var
echo $SERVICE_NAME
```

### Traces not appearing

```bash
# Check TEMPO_URL is set
env | grep TEMPO

# Should see:
# TEMPO_URL=http://tempo:4318
# or
# TEMPO_URL=https://tempo.railway.internal:4318

# Check app logs for errors
docker logs repo-fastapi_app-1  # Docker
railway logs  # Railway
```

### Metrics not in Prometheus

1. Verify Prometheus scrape config includes this app
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify app is reachable from Prometheus

## Architecture

```
FastAPI App
├── OpenTelemetry SDK
│   └── Traces → Tempo:4318/v1/traces
├── Prometheus Client
│   └── Metrics → Exposed at :8000/metrics
└── Structured Logging
    └── Logs → Loki (via Locomotive)

Prometheus scrapes → :8000/metrics
Grafana queries → Prometheus, Tempo, Loki
```

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `prometheus-client` - Metrics export
- `opentelemetry-*` - Tracing instrumentation
- See `requirements.txt` for full list

## Best Practices

1. **Always set SERVICE_NAME** - Makes identifying services easier
2. **Use health checks** - `/health` endpoint for monitoring
3. **Add custom spans** - For business logic tracing
4. **Label your metrics** - Use service labels for filtering
5. **Structure your logs** - Include context for debugging
6. **Test locally first** - Use Docker Compose before deploying

## Related Files

- `/QUICK_START.md` - Quick start guide for the whole stack
- `/RAILWAY_SETUP.md` - Detailed Railway deployment guide
- `/grafana/dashboards/fastapi-observability.json` - Dashboard config
- `/prometheus/prom.yml` - Prometheus scrape config

## Support

- FastAPI Docs: https://fastapi.tiangolo.com
- OpenTelemetry: https://opentelemetry.io/docs/languages/python/
- Grafana Dashboard: https://grafana.com/grafana/dashboards/16110
- Railway Docs: https://docs.railway.app

## License

Same as parent repository.
