# OpenTelemetry OTLP Integration Guide

## Overview

This guide explains how to integrate OpenTelemetry tracing with the GatewayZ observability stack. By following this guide, you'll send traces to Tempo, which will automatically generate metrics for model usage, latency, and errors.

## Why OpenTelemetry?

- **Automatic Metrics**: Traces are automatically converted to metrics (model popularity, latency, error rates)
- **Distributed Tracing**: Track requests across multiple services
- **Root Cause Analysis**: Debug performance issues by examining trace spans
- **Vendor Neutral**: OpenTelemetry is a CNCF standard supported by all major observability platforms

## Quick Start

### 1. Install Dependencies

```bash
pip install opentelemetry-api opentelemetry-sdk \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-exporter-otlp-proto-http \
  opentelemetry-exporter-otlp-proto-grpc
```

### 2. Configure OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Create resource with service name
resource = Resource.create({SERVICE_NAME: "gatewayz-api"})

# Create tracer provider
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Configure OTLP exporter
# Use HTTP/protobuf (port 4318) or gRPC (port 4317)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo.railway.internal:4318/v1/traces",
    # For local development:
    # endpoint="http://localhost:4318/v1/traces",
)

# Add batch span processor (batches spans before sending)
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Auto-instrument FastAPI
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
```

### 3. Add Trace Attributes to Your Code

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    # Get current span (created by FastAPI instrumentation)
    current_span = trace.get_current_span()

    # Set required attributes
    current_span.set_attribute("gen_ai.system", "openai")  # or "anthropic", "vertex_ai"
    current_span.set_attribute("gen_ai.request.model", request.model)
    current_span.set_attribute("gen_ai.operation.name", "chat")

    # Set GatewayZ-specific attributes
    current_span.set_attribute("gatewayz.provider.name", "openrouter")
    current_span.set_attribute("gatewayz.customer.id", request.customer_id)
    current_span.set_attribute("gatewayz.request.type", "chat_completion")

    try:
        # Create child span for provider API call
        with tracer.start_as_current_span("provider_api_call") as span:
            span.set_attribute("server.address", "api.openai.com")
            span.set_attribute("server.port", 443)

            # Call provider
            result = await call_provider_api(request)

            # Set response attributes
            span.set_attribute("gen_ai.response.model", result.model)
            span.set_attribute("gen_ai.usage.input_tokens", result.usage.prompt_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", result.usage.completion_tokens)
            span.set_attribute("http.response.status_code", 200)

        return result

    except ProviderError as e:
        # Record error
        current_span.set_status(Status(StatusCode.ERROR, str(e)))
        current_span.record_exception(e)
        current_span.set_attribute("http.response.status_code", e.status_code)
        raise
```

## Required Trace Attributes

These attributes **MUST** be set on every AI/ML operation span:

| Attribute | Type | Example | Description |
|-----------|------|---------|-------------|
| `gen_ai.system` | string | `"openai"` | AI system/provider identifier |
| `gen_ai.request.model` | string | `"gpt-4"` | Model requested by user |
| `gen_ai.operation.name` | string | `"chat"` | Operation type |
| `http.response.status_code` | int | `200` | HTTP status code |

**Why these are required:**
- Without `gen_ai.request.model`, metrics won't show which models are being used
- Without `gen_ai.system`, can't differentiate between OpenAI, Anthropic, etc.
- Without `http.response.status_code`, can't calculate error rates
- Without `gen_ai.operation.name`, can't separate chat vs. embedding requests

## Recommended Trace Attributes

These attributes **SHOULD** be set for better observability:

| Attribute | Type | Example | Description |
|-----------|------|---------|-------------|
| `gen_ai.response.model` | string | `"gpt-4-0613"` | Actual model used (may differ) |
| `gen_ai.usage.input_tokens` | int | `450` | Input tokens consumed |
| `gen_ai.usage.output_tokens` | int | `123` | Output tokens generated |
| `gen_ai.request.max_tokens` | int | `1000` | Max tokens requested |
| `gen_ai.request.temperature` | float | `0.7` | Temperature parameter |
| `server.address` | string | `"api.openai.com"` | Provider API endpoint |
| `server.port` | int | `443` | Provider API port |

## GatewayZ-Specific Attributes

These attributes are specific to GatewayZ:

| Attribute | Type | Example | Description |
|-----------|------|---------|-------------|
| `gatewayz.provider.name` | string | `"openrouter"` | GatewayZ provider identifier |
| `gatewayz.customer.id` | string | `"cust_123"` | Customer/tenant ID |
| `gatewayz.request.type` | string | `"chat_completion"` | Detailed request type |
| `gatewayz.fallback.occurred` | boolean | `true` | Whether fallback was used |
| `gatewayz.fallback.provider` | string | `"cerebras"` | Fallback provider |
| `gatewayz.cache.hit` | boolean | `true` | Cache hit/miss |

## Complete Example

### FastAPI Application with Full Instrumentation

```python
import os
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.trace import Status, StatusCode
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# OpenTelemetry Configuration
# ============================================================

def configure_tracing():
    """Configure OpenTelemetry tracing with OTLP exporter"""

    # Get Tempo endpoint from environment
    tempo_endpoint = os.getenv(
        "OTLP_EXPORTER_ENDPOINT",
        "http://tempo.railway.internal:4318/v1/traces"
    )

    # Create resource with service metadata
    resource = Resource.create({
        SERVICE_NAME: "gatewayz-api",
        SERVICE_VERSION: "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "production"),
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=tempo_endpoint,
        timeout=10,  # 10 second timeout
    )

    # Add batch span processor
    # Spans are batched and sent every 5 seconds or when 512 spans accumulate
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,
    )
    provider.add_span_processor(span_processor)

    logger.info(f"OpenTelemetry configured. Sending traces to: {tempo_endpoint}")

# Initialize tracing
configure_tracing()

# Create FastAPI app
app = FastAPI(title="GatewayZ API")

# Auto-instrument FastAPI (creates spans for all HTTP requests)
FastAPIInstrumentor.instrument_app(app)

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)

# ============================================================
# Request Models
# ============================================================

from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    model: str
    messages: list
    customer_id: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    model: str
    choices: list
    usage: dict

# ============================================================
# Provider Client (Simplified Example)
# ============================================================

class ProviderClient:
    """Simplified provider client for demonstration"""

    async def chat_completion(
        self,
        provider: str,
        model: str,
        messages: list,
        **kwargs
    ) -> ChatResponse:
        """Call provider API for chat completion"""

        # Get current span to add attributes
        current_span = trace.get_current_span()

        # Set provider-specific attributes
        current_span.set_attribute("gatewayz.provider.name", provider)
        current_span.set_attribute("server.address", self.get_provider_endpoint(provider))
        current_span.set_attribute("server.port", 443)

        try:
            # Simulate API call
            # In real code, this would be: await httpx.post(...)
            result = await self._make_request(provider, model, messages, **kwargs)

            # Set success attributes
            current_span.set_attribute("http.response.status_code", 200)
            current_span.set_attribute("gen_ai.response.model", result["model"])
            current_span.set_attribute("gen_ai.usage.input_tokens", result["usage"]["prompt_tokens"])
            current_span.set_attribute("gen_ai.usage.output_tokens", result["usage"]["completion_tokens"])

            return ChatResponse(**result)

        except Exception as e:
            # Record error
            current_span.set_status(Status(StatusCode.ERROR, str(e)))
            current_span.record_exception(e)
            current_span.set_attribute("http.response.status_code", 500)
            raise

    def get_provider_endpoint(self, provider: str) -> str:
        """Get API endpoint for provider"""
        endpoints = {
            "openrouter": "openrouter.ai",
            "openai": "api.openai.com",
            "anthropic": "api.anthropic.com",
        }
        return endpoints.get(provider, "unknown")

    async def _make_request(self, provider, model, messages, **kwargs):
        """Simulate API request (replace with real implementation)"""
        # This is a placeholder - implement actual API call here
        return {
            "model": model,
            "choices": [{"message": {"content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

provider_client = ProviderClient()

# ============================================================
# API Endpoints
# ============================================================

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    """
    Handle chat completion request with full OpenTelemetry instrumentation
    """

    # Get current span (auto-created by FastAPI instrumentation)
    current_span = trace.get_current_span()

    # Set required OpenTelemetry attributes
    current_span.set_attribute("gen_ai.system", "openai")  # or detect from model
    current_span.set_attribute("gen_ai.request.model", request.model)
    current_span.set_attribute("gen_ai.operation.name", "chat")
    current_span.set_attribute("gen_ai.request.max_tokens", request.max_tokens)
    current_span.set_attribute("gen_ai.request.temperature", request.temperature)

    # Set GatewayZ-specific attributes
    current_span.set_attribute("gatewayz.customer.id", request.customer_id)
    current_span.set_attribute("gatewayz.request.type", "chat_completion")

    # Determine provider (simplified - in real code, use routing logic)
    provider = "openrouter"

    try:
        # Create child span for provider API call
        with tracer.start_as_current_span("provider_api_call") as provider_span:
            # Set span kind
            provider_span.set_attribute("span.kind", "CLIENT")

            # Call provider
            result = await provider_client.chat_completion(
                provider=provider,
                model=request.model,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            # Success - set final attributes
            current_span.set_attribute("http.response.status_code", 200)
            current_span.set_attribute("gatewayz.fallback.occurred", False)

            logger.info(
                "Chat completion successful",
                extra={
                    "model": request.model,
                    "customer_id": request.customer_id,
                    "input_tokens": result.usage["prompt_tokens"],
                    "output_tokens": result.usage["completion_tokens"],
                }
            )

            return result

    except Exception as e:
        # Try fallback provider
        logger.warning(f"Provider {provider} failed, trying fallback: {e}")

        fallback_provider = "cerebras"
        current_span.set_attribute("gatewayz.fallback.occurred", True)
        current_span.set_attribute("gatewayz.fallback.provider", fallback_provider)

        try:
            with tracer.start_as_current_span("fallback_provider_api_call") as fallback_span:
                fallback_span.set_attribute("span.kind", "CLIENT")

                result = await provider_client.chat_completion(
                    provider=fallback_provider,
                    model=request.model,
                    messages=request.messages,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                )

                current_span.set_attribute("http.response.status_code", 200)
                return result

        except Exception as fallback_error:
            # Both providers failed
            current_span.set_status(Status(StatusCode.ERROR, str(fallback_error)))
            current_span.record_exception(fallback_error)
            current_span.set_attribute("http.response.status_code", 500)

            logger.error(
                "All providers failed",
                extra={
                    "model": request.model,
                    "customer_id": request.customer_id,
                    "error": str(fallback_error),
                },
                exc_info=True
            )

            raise HTTPException(status_code=500, detail="Service unavailable")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("GatewayZ API starting up with OpenTelemetry instrumentation")

@app.on_event("shutdown")
async def shutdown_event():
    # Flush any remaining spans
    trace.get_tracer_provider().force_flush(timeout_millis=5000)
    logger.info("GatewayZ API shutting down")
```

## Testing Your Integration

### 1. Verify Traces are Being Sent

```bash
# Check Tempo received traces
curl http://tempo:3200/api/search?tags=service.name=gatewayz-api | jq

# Should return traces with your service name
```

### 2. View a Specific Trace

```bash
# Get trace by ID
curl http://tempo:3200/api/traces/<trace-id> | jq

# Check that attributes are present
```

### 3. Verify Span Metrics are Generated

```bash
# Check Tempo metrics endpoint
curl http://tempo:3200/metrics | grep spanmetrics

# Should see:
# traces_spanmetrics_calls_total{...}
# traces_spanmetrics_duration_seconds_bucket{...}
```

### 4. Query Metrics in Mimir

```bash
# Query span metrics from Mimir
curl -G http://mimir:9009/prometheus/api/v1/query \
  --data-urlencode 'query=traces_spanmetrics_calls_total{gen_ai_request_model="gpt-4"}' \
  | jq
```

### 5. View in Grafana

1. Open Grafana: http://localhost:3000
2. Go to Explore
3. Select "Tempo" datasource
4. Search for traces with: `{service.name="gatewayz-api"}`
5. Click on a trace to see the span details and attributes

## Common Pitfalls

### 1. Attribute Names

❌ **Wrong:**
```python
span.set_attribute("model", "gpt-4")  # Too generic
span.set_attribute("genai.model", "gpt-4")  # Wrong namespace
```

✅ **Correct:**
```python
span.set_attribute("gen_ai.request.model", "gpt-4")
```

### 2. HTTP Status Codes

❌ **Wrong:**
```python
span.set_attribute("status_code", 200)  # Wrong attribute name
span.set_attribute("http.status_code", "200")  # Wrong type (should be int)
```

✅ **Correct:**
```python
span.set_attribute("http.response.status_code", 200)
```

### 3. Missing Attributes

If metrics are missing in Grafana, check that ALL required attributes are set:

```python
# ALL of these are required:
span.set_attribute("gen_ai.system", "openai")
span.set_attribute("gen_ai.request.model", "gpt-4")
span.set_attribute("gen_ai.operation.name", "chat")
span.set_attribute("http.response.status_code", 200)
```

### 4. High Cardinality Attributes

❌ **Don't use high-cardinality values as attributes:**
```python
span.set_attribute("trace_id", trace_id)  # Unique per request
span.set_attribute("user_message", message)  # Unique content
span.set_attribute("timestamp", timestamp)  # Unique per request
```

This will create too many unique metric series and cause performance issues.

### 5. Forgetting to Flush on Shutdown

Make sure to flush spans before application shutdown:

```python
@app.on_event("shutdown")
async def shutdown():
    # Flush remaining spans
    trace.get_tracer_provider().force_flush(timeout_millis=5000)
```

## Environment Variables

Configure your application with these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OTLP_EXPORTER_ENDPOINT` | `http://tempo.railway.internal:4318/v1/traces` | Tempo OTLP endpoint |
| `OTEL_SERVICE_NAME` | `gatewayz-api` | Service name in traces |
| `OTEL_SERVICE_VERSION` | `1.0.0` | Service version |
| `OTEL_TRACES_EXPORTER` | `otlp` | Exporter type |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | Protocol (http/protobuf or grpc) |

## Next Steps

1. ✅ Complete this integration guide
2. ✅ Deploy to staging and verify traces in Grafana
3. ✅ Add custom spans for important operations
4. ✅ Monitor span metrics in Model Performance dashboards
5. ✅ Set up alerts for error rates and latency

## References

- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Semantic Conventions for Gen AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Grafana Tempo OTLP Ingestion](https://grafana.com/docs/tempo/latest/configuration/ingestion-protocols/#otlp)
- [GatewayZ Architecture: Transparent Telemetry Ingestion](../architecture/TRANSPARENT_TELEMETRY_INGESTION.md)
