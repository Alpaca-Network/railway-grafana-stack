# Backend API Instrumentation Guide

This guide provides instructions for instrumenting your GatewayZ backend API to send logs to Loki and traces to Tempo.

## Overview

Your backend API needs to be configured to send:
1. **Logs** → Loki (log aggregation)
2. **Traces** → Tempo (distributed tracing)
3. **Metrics** → Prometheus (already configured at `api.gatewayz.ai`)

## Environment Variables

Set these environment variables in your backend API deployment:

### Local Development (Docker)
```bash
# Loki Configuration
LOKI_URL=http://loki:3100
LOKI_PUSH_URL=http://loki:3100/loki/api/v1/push

# Tempo Configuration
TEMPO_URL=http://tempo:3200
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo:4317

# Service Identification
SERVICE_NAME=gatewayz-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=development
```

### Railway Deployment
```bash
# Loki Configuration
LOKI_URL=http://loki.railway.internal:3100
LOKI_PUSH_URL=http://loki.railway.internal:3100/loki/api/v1/push

# Tempo Configuration
TEMPO_URL=http://tempo.railway.internal:3200
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo.railway.internal:4317

# Service Identification
SERVICE_NAME=gatewayz-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=production
```

## Python Backend Implementation

### 1. Install Dependencies

```bash
pip install python-json-logger python-logging-loki opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests opentelemetry-instrumentation-sqlalchemy
```

### 2. Configure Logging to Loki

Add this to your main application file (e.g., `main.py`):

```python
import logging
import json
import os
from pythonjsonlogger import jsonlogger
from logging_loki import LokiHandler

# Get environment variables
LOKI_URL = os.getenv("LOKI_PUSH_URL", "http://loki:3100/loki/api/v1/push")
SERVICE_NAME = os.getenv("SERVICE_NAME", "gatewayz-api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

def setup_loki_logging():
    """Configure logging to send logs to Loki"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add Loki handler
    loki_handler = LokiHandler(
        url=LOKI_URL,
        tags={
            "service": SERVICE_NAME,
            "environment": ENVIRONMENT,
            "job": SERVICE_NAME,
        },
        version="1",
    )
    
    # JSON formatter for structured logging
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    loki_handler.setFormatter(formatter)
    logger.addHandler(loki_handler)
    
    # Also add console handler for local development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_loki_logging()
```

### 3. Configure Tracing to Tempo

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
```

### 4. Instrument FastAPI Application

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
```

### 5. Add Trace IDs to Logs

Update your logging to include trace IDs for correlation:

```python
import logging
from opentelemetry import trace

class TraceIDFilter(logging.Filter):
    """Add trace ID to log records"""
    
    def filter(self, record):
        trace_id = trace.get_current_span().get_span_context().trace_id
        record.trace_id = f"{trace_id:032x}" if trace_id else "0" * 32
        return True

# Add filter to logger
logger = logging.getLogger()
logger.addFilter(TraceIDFilter())
```

### 6. Example FastAPI Endpoints

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
npm install @opentelemetry/api @opentelemetry/sdk-node @opentelemetry/auto @opentelemetry/exporter-trace-otlp-http @opentelemetry/resources @opentelemetry/semantic-conventions winston winston-loki
```

### 2. Configure Logging to Loki

```javascript
const winston = require('winston');
const LokiTransport = require('winston-loki');

const lokiTransport = new LokiTransport({
  host: process.env.LOKI_URL || 'http://loki:3100',
  labels: {
    service: process.env.SERVICE_NAME || 'gatewayz-api',
    environment: process.env.ENVIRONMENT || 'development',
    job: process.env.SERVICE_NAME || 'gatewayz-api',
  },
  json: true,
});

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    lokiTransport,
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

module.exports = logger;
```

### 3. Configure Tracing to Tempo

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
go get github.com/grafana/loki-client-go/loki
```

### 2. Configure Logging to Loki

```go
package main

import (
	"github.com/grafana/loki-client-go/loki"
	"log"
	"os"
)

func setupLokiLogging() (*loki.Client, error) {
	lokiURL := os.Getenv("LOKI_PUSH_URL")
	if lokiURL == "" {
		lokiURL = "http://loki:3100/loki/api/v1/push"
	}

	config := loki.Config{
		URL:       lokiURL,
		TenantID:  "gatewayz",
		BatchSize: 100,
	}

	client, err := loki.New(config)
	if err != nil {
		log.Fatal("Failed to create Loki client:", err)
	}

	return client, nil
}
```

### 3. Configure Tracing to Tempo

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

### 1. Generate Test Logs

```bash
# Python
curl -X GET "http://localhost:8000/health"

# Node.js
curl -X GET "http://localhost:3000/health"

# Go
curl -X GET "http://localhost:8080/health"
```

### 2. Generate Test Traces

```bash
# Make multiple requests to generate traces
for i in {1..10}; do
  curl -X GET "http://localhost:8000/api/monitoring/health"
  sleep 1
done
```

### 3. Verify in Grafana

1. Open http://localhost:3000 (admin/yourpassword123)
2. Go to **Loki Logs Dashboard** → Should see logs from your API
3. Go to **Tempo Distributed Tracing Dashboard** → Should see traces
4. Logs and traces should be correlated by trace ID

## Verification Commands

### Check Loki is receiving logs
```bash
curl -s 'http://localhost:3100/loki/api/v1/query?query={job="gatewayz-api"}' | jq '.data.result'
```

### Check Tempo is receiving traces
```bash
curl -s 'http://localhost:3200/api/traces?service=gatewayz-api' | jq '.traces'
```

### Check trace IDs in logs
```bash
curl -s 'http://localhost:3100/loki/api/v1/query?query={job="gatewayz-api"}' | jq '.data.result[0].values[0]'
```

## Troubleshooting

### Logs not appearing in Loki
1. Verify `LOKI_PUSH_URL` is correct
2. Check backend logs for errors: `docker logs <backend-container>`
3. Verify network connectivity: `curl http://loki:3100/ready`

### Traces not appearing in Tempo
1. Verify `TEMPO_OTLP_HTTP_ENDPOINT` is correct
2. Check backend logs for OTLP export errors
3. Verify Tempo is receiving data: `curl http://tempo:3200/ready`

### Logs and traces not correlating
1. Ensure trace ID is included in logs with key `trace_id`
2. Verify Loki derived field regex matches: `trace_id=(\w+)`
3. Check Grafana datasource correlation settings

## Production Deployment (Railway)

When deploying to Railway:

1. Set environment variables in Railway dashboard:
   ```
   LOKI_URL=http://loki.railway.internal:3100
   LOKI_PUSH_URL=http://loki.railway.internal:3100/loki/api/v1/push
   TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318
   SERVICE_NAME=gatewayz-api
   ENVIRONMENT=production
   ```

2. Ensure your backend service depends on Loki and Tempo services

3. Verify connectivity in Railway logs

## Next Steps

1. ✅ Add instrumentation to your backend API
2. ✅ Set environment variables
3. ✅ Deploy and generate test traffic
4. ✅ Verify logs appear in Loki dashboard
5. ✅ Verify traces appear in Tempo dashboard
6. ✅ Confirm correlation between logs and traces
7. 📊 Create custom dashboards for your API

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Node.js](https://opentelemetry.io/docs/instrumentation/js/)
- [OpenTelemetry Go](https://opentelemetry.io/docs/instrumentation/go/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Grafana Correlations](https://grafana.com/docs/grafana/latest/administration/correlations/)
