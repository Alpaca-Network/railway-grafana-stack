# Backend API Instrumentation Guide

This guide provides instructions for instrumenting your GatewayZ backend API to send traces to Tempo.

## Overview

Your backend API needs to be configured to send:
1. **Logs** → Loki (already handled by Locomotive)
2. **Traces** → Tempo (distributed tracing) ← **YOU NEED TO ADD THIS**
3. **Metrics** → Prometheus (already configured at `api.gatewayz.ai`)

## Environment Variables

Set these environment variables in your backend API deployment:

### Local Development (Docker)
```bash
# Tempo Configuration (for distributed tracing)
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo:4317

# Service Identification
SERVICE_NAME=gatewayz-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
```

### Railway Deployment
```bash
# Tempo Configuration (for distributed tracing)
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo.railway.internal:4317

# Service Identification
SERVICE_NAME=gatewayz-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
```

## Logging Note

Your logs are already being sent to Loki via **Locomotive**. You don't need to add logging instrumentation - just ensure your backend logs include `trace_id` fields so they correlate with traces in Grafana.

## Python Backend Implementation

### 1. Install Dependencies

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests opentelemetry-instrumentation-sqlalchemy
```

### 2. Configure Tracing to Tempo

Add this to your main application file:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

def setup_tempo_tracing():
    """Configure tracing to send traces to Tempo"""
    
    # Get environment variables
    TEMPO_OTLP_HTTP = os.getenv(
        "TEMPO_OTLP_HTTP_ENDPOINT", 
        "http://tempo:4318"
    )
    SERVICE_NAME = os.getenv("SERVICE_NAME", "gatewayz-api")
    SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Create resource
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "deployment.environment": ENVIRONMENT,
    })
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Create OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{TEMPO_OTLP_HTTP}/v1/traces",
        timeout=10,
    )
    
    # Add span processor
    tracer_provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )
    
    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider

# Initialize tracing
tracer_provider = setup_tempo_tracing()

### 3. Instrument FastAPI Application

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = FastAPI(title="GatewayZ API")

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Instrument HTTP requests
RequestsInstrumentor().instrument()

# Instrument database (if using SQLAlchemy)
# SQLAlchemyInstrumentor().instrument(engine=your_db_engine)

### 4. Add Trace IDs to Logs (for Locomotive correlation)

Update your logging to include trace IDs so Locomotive logs correlate with Tempo traces:

```python
import logging
from opentelemetry import trace

class TraceIDFilter(logging.Filter):
    """Add trace ID to log records for correlation with Tempo traces"""
    
    def filter(self, record):
        trace_id = trace.get_current_span().get_span_context().trace_id
        record.trace_id = f"{trace_id:032x}" if trace_id else "0" * 32
        return True

# Add filter to logger
logger = logging.getLogger()
logger.addFilter(TraceIDFilter())

### 5. Example FastAPI Endpoints

```python
from fastapi import FastAPI, HTTPException
from opentelemetry import trace

app = FastAPI()
tracer = trace.get_tracer(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    with tracer.start_as_current_span("health_check"):
        logger.info("Health check called")
        return {"status": "healthy"}

@app.get("/api/monitoring/health")
async def get_provider_health():
    """Get all provider health scores"""
    with tracer.start_as_current_span("get_provider_health"):
        logger.info("Fetching provider health scores")
        # Your implementation here
        return {
            "openai": 95,
            "anthropic": 92,
            "google": 88,
        }

@app.get("/api/monitoring/health/{provider}")
async def get_provider_health_detail(provider: str):
    """Get specific provider health score"""
    with tracer.start_as_current_span("get_provider_health_detail", attributes={"provider": provider}):
        logger.info(f"Fetching health for provider: {provider}")
        # Your implementation here
        return {"provider": provider, "health_score": 95}

@app.get("/api/monitoring/errors/{provider}")
async def get_provider_errors(provider: str, limit: int = 100):
    """Get recent errors for a provider"""
    with tracer.start_as_current_span("get_provider_errors", attributes={"provider": provider, "limit": limit}):
        logger.info(f"Fetching errors for {provider}, limit: {limit}")
        # Your implementation here
        return {"provider": provider, "errors": []}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # Return Prometheus format metrics
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")
```

## Node.js Backend Implementation

### 1. Install Dependencies

```bash
npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/auto @opentelemetry/exporter-trace-otlp-http @opentelemetry/resources @opentelemetry/semantic-conventions
```

### 2. Configure Tracing to Tempo

```javascript
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: process.env.SERVICE_NAME || 'gatewayz-api',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.SERVICE_VERSION || '1.0.0',
    'deployment.environment': process.env.ENVIRONMENT || 'development',
  }),
  traceExporter: new OTLPTraceExporter({
    url: `${process.env.TEMPO_OTLP_HTTP_ENDPOINT || 'http://tempo:4318'}/v1/traces`,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

console.log('Tracing initialized');
```

## Go Backend Implementation

### 1. Install Dependencies

```bash
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp
go get go.opentelemetry.io/otel/sdk/trace
```

### 2. Configure Tracing to Tempo

```go
package main

import (
	"context"
	"os"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.17.0"
)

func setupTempoTracing(ctx context.Context) (*sdktrace.TracerProvider, error) {
	tempoEndpoint := os.Getenv("TEMPO_OTLP_HTTP_ENDPOINT")
	if tempoEndpoint == "" {
		tempoEndpoint = "http://tempo:4318"
	}

	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpoint(tempoEndpoint),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, err
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(os.Getenv("SERVICE_NAME")),
			semconv.ServiceVersion(os.Getenv("SERVICE_VERSION")),
		),
	)
	if err != nil {
		return nil, err
	}

	tp := sdktrace.NewTracerProvider(
		sdktrace.WithBatcher(exporter),
		sdktrace.WithResource(res),
	)

	otel.SetTracerProvider(tp)
	return tp, nil
}
```

## Testing the Integration

### 1. Generate Test Traces

```bash
# Make multiple requests to generate traces
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/monitoring/health"
  sleep 1
done
```

### 2. Verify in Grafana

1. Open http://localhost:3000 (admin/yourpassword123)
2. Go to **Tempo Distributed Tracing Dashboard** → Should see traces from your API
3. Go to **Loki Logs Dashboard** → Should see logs from Locomotive
4. Logs and traces should be correlated by trace ID

## Verification Commands

### Check Tempo is receiving traces
```bash
curl -s 'http://localhost:3200/api/traces?service=gatewayz-api' | jq '.traces'
```

### Check trace IDs in Locomotive logs
Logs from Locomotive should include trace IDs that match traces in Tempo.

## Troubleshooting

### Traces not appearing in Tempo
1. Verify `TEMPO_OTLP_HTTP_ENDPOINT` is correct
2. Check backend logs for OTLP export errors
3. Verify Tempo is receiving data: `curl http://tempo:3200/ready`

### Logs and traces not correlating
1. Ensure trace ID is included in Locomotive logs with key `trace_id`
2. Verify Loki derived field regex matches: `trace_id=(\w+)`
3. Check Grafana datasource correlation settings

## Production Deployment (Railway)

When deploying to Railway:

1. Set environment variables in Railway dashboard:
   ```
   TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318
   SERVICE_NAME=gatewayz-api
   ENVIRONMENT=production
   ```

2. Ensure your backend service depends on Tempo service

3. Verify connectivity in Railway logs

## Next Steps

1. ✅ Add OpenTelemetry instrumentation to your backend API
2. ✅ Set environment variables for Tempo endpoint
3. ✅ Deploy and generate test traffic
4. ✅ Verify traces appear in Tempo dashboard
5. ✅ Verify logs from Locomotive appear in Loki dashboard
6. ✅ Confirm correlation between logs and traces by trace ID
7. 📊 Create custom dashboards for your API

## Architecture Summary

```
Your Backend API
    ├─→ Metrics → Prometheus (already working)
    ├─→ Logs → Loki (via Locomotive)
    └─→ Traces → Tempo (via OpenTelemetry OTLP) ← ADD THIS
         ↓
      Grafana (correlates all three by trace ID)
```

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/instrumentation/js/)
- [OpenTelemetry Go](https://opentelemetry.io/docs/instrumentation/go/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Grafana Correlations](https://grafana.com/docs/grafana/latest/administration/correlations/)
