# Railway Deployment Guide

This guide explains how to deploy your FastAPI application with the full observability stack on Railway.

## Prerequisites

1. Railway account at https://railway.app
2. Railway CLI installed (optional): `npm i -g @railway/cli`
3. Git repository pushed to GitHub

## Architecture Overview

The observability stack consists of:
- **Grafana**: Visualization and dashboards (main service)
- **Prometheus**: Metrics collection
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing
- **FastAPI App**: Your application with observability instrumentation

## Deployment Steps

### 1. Deploy the Observability Stack

The observability stack (Grafana, Prometheus, Loki, Tempo) should already be deployed on Railway if you're using the Grafana template.

If not, deploy each service separately:

#### Deploy Grafana Service
1. Create a new service in Railway
2. Connect your GitHub repository
3. Set the root directory to `/grafana`
4. Add environment variables:
   ```
   GF_SECURITY_ADMIN_USER=admin
   GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>
   LOKI_INTERNAL_URL=${{Loki.RAILWAY_PRIVATE_DOMAIN}}:3100
   PROMETHEUS_INTERNAL_URL=${{Prometheus.RAILWAY_PRIVATE_DOMAIN}}:9090
   TEMPO_INTERNAL_URL=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:3200
   TEMPO_INTERNAL_HTTP_INGEST=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:4318
   TEMPO_INTERNAL_GRPC_INGEST=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:4317
   ```

#### Deploy Prometheus Service
1. Create a new service in Railway
2. Connect your GitHub repository
3. Set the root directory to `/prometheus`
4. Expose port 9090 (private networking only)

#### Deploy Loki Service
1. Create a new service in Railway
2. Connect your GitHub repository
3. Set the root directory to `/loki`
4. Expose port 3100 (private networking only)

#### Deploy Tempo Service
1. Create a new service in Railway
2. Connect your GitHub repository
3. Set the root directory to `/tempo`
4. Expose ports:
   - 3200 (query API)
   - 4317 (gRPC ingest)
   - 4318 (HTTP ingest)

### 2. Deploy Your FastAPI Application

#### Option A: Using Railway UI

1. **Create a new service** in your Railway project
2. **Connect your repository** and set root directory to `fastapi-app`
3. **Add environment variables**:
   ```
   SERVICE_NAME=fastapi-app
   TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
   TEMPO_INTERNAL_HTTP_INGEST=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
   LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}
   PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
   ```

4. **Deploy** - Railway will automatically:
   - Detect the Dockerfile
   - Use the `railway.json` configuration
   - Assign a PORT environment variable
   - Generate a public URL

#### Option B: Using Railway CLI

```bash
# Login to Railway
railway login

# Link to your project
railway link

# Set environment variables
railway variables set SERVICE_NAME=fastapi-app
railway variables set TEMPO_URL='${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}'
railway variables set LOKI_URL='${{Grafana.LOKI_INTERNAL_URL}}'
railway variables set PROMETHEUS_URL='${{Grafana.PROMETHEUS_INTERNAL_URL}}'

# Deploy
railway up
```

## Connecting Other Applications

To connect any other Railway application to this observability stack:

### 1. Add Environment Variables

In your application's Railway service settings, add:

```bash
# For Tempo tracing (choose HTTP or gRPC)
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
# OR
TEMPO_GRPC_URL=${{Grafana.TEMPO_INTERNAL_GRPC_INGEST}}

# For Loki logs (or use Locomotive)
LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}

# For Prometheus metrics
PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
```

### 2. Update Prometheus Scrape Config

If your application exposes a `/metrics` endpoint, add it to Prometheus scrape config (`prometheus/prom.yml`):

```yaml
scrape_configs:
  - job_name: 'your-app-name'
    scheme: http
    metrics_path: '/metrics'
    static_configs:
      - targets: ['your-service.railway.internal:8000']  # Use Railway internal domain
    scrape_interval: 15s
```

Then redeploy Prometheus.

## Using Locomotive for Loki (Recommended for Logs)

Instead of instrumenting your app for logging, use Locomotive to automatically forward Railway logs to Loki:

1. **Deploy Locomotive template** from Railway marketplace
2. **Add environment variables**:
   - `RAILWAY_API_KEY`: Your Railway API key
   - `SERVICE_IDS`: Comma-separated list of service IDs to monitor
   - `LOKI_URL`: `${{Grafana.LOKI_INTERNAL_URL}}`

3. **Done!** Logs will automatically flow from your Railway services to Loki.

No code changes needed! This is the easiest way to get logs into your observability stack.

## OpenTelemetry Integration Examples

### Python/FastAPI (Already Implemented)

See `/fastapi-app/main.py` for a complete example with:
- ✅ Prometheus metrics with `app_name` label
- ✅ OpenTelemetry tracing to Tempo
- ✅ Structured logging

### Node.js/Express

See `/examples/api/tracer.js` for an example using:
```javascript
const tempoUrl = process.env.TEMPO_URL || "http://tempo:4318";
const sdk = new NodeSDK({
  resource: new Resource({
    "service.name": process.env.SERVICE_NAME || 'unknown',
  }),
  traceExporter: new OTLPTraceExporter({
    url: `${tempoUrl}/v1/traces`
  })
});
```

### Other Languages

Use OpenTelemetry SDK for your language:
- **Go**: `go.opentelemetry.io/otel`
- **Java**: `io.opentelemetry:opentelemetry-sdk`
- **Rust**: `opentelemetry` crate
- **.NET**: `OpenTelemetry` NuGet package

All should configure OTLP exporter to send to:
```
HTTP: ${TEMPO_URL}/v1/traces
gRPC: ${TEMPO_GRPC_URL}
```

## Important Notes

### Railway Private Networking

- Railway services communicate using internal domains: `service-name.railway.internal`
- Use `${{ServiceName.VARIABLE}}` syntax to reference other services
- Private networking is automatic and secure

### Service Name Label

**Critical**: For the FastAPI Observability dashboard to work, your application MUST expose a metric:

```python
from prometheus_client import Info

APP_INFO = Info('fastapi_app', 'FastAPI application info')
APP_INFO.info({'app_name': 'your-app-name'})
```

This populates the `app_name` dropdown in Grafana.

### Health Checks

The FastAPI app includes a `/health` endpoint for Railway health checks:
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME}
```

### Port Configuration

Railway automatically assigns a `PORT` environment variable. The FastAPI app is configured to use it:
```python
port = int(os.getenv("PORT", "8000"))
uvicorn.run(app, host="0.0.0.0", port=port)
```

## Verifying the Setup

1. **Check Grafana**: Open your Grafana public URL
2. **Go to Dashboards**: Navigate to "FastAPI Observability" (ID: 16110)
3. **Select Application**: Use the `app_name` dropdown to select your application
4. **Generate Traffic**: Hit your application endpoints
5. **View Data**:
   - **Metrics**: Should show request rates, latency percentiles
   - **Traces**: Click on traces to see detailed spans
   - **Logs**: View logs correlated with traces

## Troubleshooting

### Application name not showing in dropdown

1. Verify the `fastapi_app_info` metric is exposed:
   ```bash
   curl https://your-app.railway.app/metrics | grep fastapi_app_info
   ```

2. Check Prometheus is scraping your app:
   - Open Prometheus UI
   - Go to Status → Targets
   - Verify your app is listed and UP

3. Verify the `app_name` label exists:
   ```bash
   curl 'https://your-prometheus.railway.app/api/v1/label/app_name/values'
   ```

### Traces not appearing in Tempo

1. Check environment variables are set correctly:
   ```bash
   railway variables
   ```

2. Verify Tempo ingest endpoint is reachable from your app

3. Check application logs for OpenTelemetry errors

### Metrics not appearing in Prometheus

1. Verify Prometheus scrape config includes your service
2. Check your app exposes `/metrics` endpoint
3. Verify Railway private networking is enabled
4. Check Prometheus logs for scrape errors

## Example Environment Variables Summary

### Grafana Service
```
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<secure-password>
LOKI_INTERNAL_URL=${{Loki.RAILWAY_PRIVATE_DOMAIN}}:3100
PROMETHEUS_INTERNAL_URL=${{Prometheus.RAILWAY_PRIVATE_DOMAIN}}:9090
TEMPO_INTERNAL_URL=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:3200
TEMPO_INTERNAL_HTTP_INGEST=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:4318
TEMPO_INTERNAL_GRPC_INGEST=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:4317
```

### Your FastAPI Application
```
SERVICE_NAME=fastapi-app
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}
PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
```

### Other Applications (Minimal)
```
SERVICE_NAME=my-other-app
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
```

That's it! Your application is now fully observable on Railway. 🚂
