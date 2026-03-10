# Backend Trace Integration - Complete Implementation Guide

> **Branch:** `feature/feature-availability` (observability fixes)
> **Backend Branch:** Create new branch for backend changes (e.g., `feat/enhanced-trace-attributes`)
> **Status:** ⚠️ Implementation Required
> **Impact:** Enables full dashboard visibility of LLM metrics

---

## Executive Summary

**Problem:** Traces are reaching Tempo, but dashboards show no data because traces lack the OpenTelemetry semantic convention attributes needed for span metrics generation.

**Solution:** Enhance backend's OpenTelemetry instrumentation to tag LLM spans with standardized `gen_ai.*` attributes.

**Result:** Dashboards will populate with model usage, provider performance, latency breakdowns, and cost metrics.

---

## Current vs. Required State

### Current State ✅
- OpenTelemetry SDK is installed and configured
- OTLP traces are being exported to Tempo
- FastAPI routes are auto-instrumented
- Individual traces visible in Tempo

### Missing ❌
- LLM provider calls lack `gen_ai.*` semantic convention attributes
- Spans missing `gen_ai.request.model`, `gen_ai.system`, `ai.provider`
- No customer/user identification on spans
- Result: Tempo's metrics generator cannot create span metrics

---

## OpenTelemetry Semantic Conventions for LLM Tracing

### Required Span Attributes

| Attribute Name | Type | Example Value | Purpose |
|----------------|------|---------------|---------|
| `gen_ai.system` | string | `"anthropic"`, `"openai"` | Identifies the LLM provider system |
| `gen_ai.request.model` | string | `"anthropic/claude-opus-4.5"` | Full model identifier |
| `gen_ai.usage.prompt_tokens` | int | `450` | Input tokens consumed |
| `gen_ai.usage.completion_tokens` | int | `823` | Output tokens generated |
| `gen_ai.usage.total_tokens` | int | `1273` | Total tokens (prompt + completion) |
| `ai.provider` | string | `"openrouter"`, `"direct"` | Gateway provider used |
| `customer.id` | string | `"cust_abc123"` | Customer/user identifier |
| `span.http.route` | string | `"/v1/chat/completions"` | API endpoint (auto-set by FastAPI instrumentation) |
| `span.http.status_code` | int | `200`, `500` | HTTP response code (auto-set) |

### How Tempo Uses These Attributes

Tempo's **metrics_generator** converts span attributes into Prometheus metrics:

```yaml
# From tempo/tempo.yml
dimensions:
  - gen_ai.request.model    # → becomes label: gen_ai_request_model
  - gen_ai.system           # → becomes label: gen_ai_system
  - ai.provider             # → becomes label: ai_provider
  - customer.id             # → becomes label: customer_id
```

**Result Metrics:**
```promql
# Span call rate by model
traces_spanmetrics_calls_total{gen_ai_request_model="anthropic/claude-opus-4.5", gen_ai_system="anthropic"}

# Span latency by provider
traces_spanmetrics_latency_bucket{ai_provider="openrouter", le="2.5"}
```

---

## Implementation Guide

### Step 1: Install Required Packages

```bash
# If not already installed:
pip install opentelemetry-api
pip install opentelemetry-sdk
pip install opentelemetry-exporter-otlp-proto-http
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-httpx  # For provider API calls
```

### Step 2: Configure OpenTelemetry Tracer

**File: `opentelemetry_config.py`** (create if doesn't exist)

```python
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import logging

logger = logging.getLogger(__name__)

def configure_telemetry():
    """Configure OpenTelemetry tracing for GatewayZ backend"""

    # Get configuration from environment
    tempo_endpoint = os.getenv("TEMPO_OTLP_HTTP_ENDPOINT", "http://tempo:4318/v1/traces")
    service_version = os.getenv("SERVICE_VERSION", "1.0.0")
    environment = os.getenv("ENVIRONMENT", "production")

    logger.info(f"Configuring OpenTelemetry: endpoint={tempo_endpoint}, env={environment}")

    # Define service resource attributes
    resource = Resource.create({
        SERVICE_NAME: "gatewayz-api",
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=tempo_endpoint,
        timeout=10,  # 10 second timeout
    )

    # Add batch span processor (exports spans in batches for efficiency)
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,  # Export every 5 seconds
    )
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    logger.info("OpenTelemetry configured successfully")

    return tracer_provider

def instrument_fastapi(app):
    """Auto-instrument FastAPI application"""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI auto-instrumentation enabled")

def instrument_httpx():
    """Auto-instrument HTTPX client (for provider API calls)"""
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX auto-instrumentation enabled")
```

### Step 3: Initialize Tracing on App Startup

**File: `main.py`** (or wherever your FastAPI app is created)

```python
from fastapi import FastAPI
from opentelemetry_config import configure_telemetry, instrument_fastapi, instrument_httpx

# Configure OpenTelemetry BEFORE creating FastAPI app
configure_telemetry()
instrument_httpx()

# Create FastAPI app
app = FastAPI(title="GatewayZ AI Gateway")

# Instrument FastAPI app
instrument_fastapi(app)

@app.on_event("startup")
async def startup_event():
    logger.info("GatewayZ backend starting up...")
    # Other startup tasks...
```

### Step 4: Instrument LLM Provider Calls

**File: `llm_provider.py`** (or wherever you make LLM API calls)

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

tracer = trace.get_tracer(__name__)

async def call_llm_provider(
    provider: str,  # "openrouter", "openai-direct", etc.
    model: str,     # "anthropic/claude-opus-4.5"
    messages: list,
    customer_id: str,
    **kwargs
):
    """
    Call LLM provider with full OpenTelemetry tracing
    """

    # Extract provider system from model string
    # Examples:
    # "anthropic/claude-opus-4.5" → system="anthropic"
    # "openai/gpt-4" → system="openai"
    # "google/gemini-pro" → system="google"
    gen_ai_system = model.split("/")[0] if "/" in model else "unknown"

    # Start a span for this LLM call
    with tracer.start_as_current_span(
        "llm_inference",
        kind=trace.SpanKind.CLIENT  # This is an external API call
    ) as span:

        # Set standardized Gen AI attributes
        span.set_attribute("gen_ai.system", gen_ai_system)
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.operation.name", "chat.completion")

        # Set GatewayZ-specific attributes
        span.set_attribute("ai.provider", provider)
        span.set_attribute("customer.id", customer_id)

        # Set request details
        span.set_attribute("gen_ai.request.messages_count", len(messages))

        try:
            # Make the actual API call
            start_time = time.time()
            response = await _make_provider_api_call(provider, model, messages, **kwargs)
            duration = time.time() - start_time

            # Set response attributes
            if hasattr(response, "usage"):
                span.set_attribute("gen_ai.usage.prompt_tokens", response.usage.prompt_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", response.usage.completion_tokens)
                span.set_attribute("gen_ai.usage.total_tokens", response.usage.total_tokens)

            # Set success status
            span.set_status(Status(StatusCode.OK))

            # Add performance metrics
            span.set_attribute("llm.response.duration_seconds", duration)

            return response

        except Exception as e:
            # Record error on span
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

async def _make_provider_api_call(provider: str, model: str, messages: list, **kwargs):
    """
    Actual API call logic (HTTPX auto-instrumentation will add HTTP span attributes)
    """
    # Your existing provider call logic here
    ...
```

### Step 5: Instrument Specific Endpoints

**File: `api/routes/chat.py`** (or your chat completion endpoint)

```python
from fastapi import APIRouter, Depends
from opentelemetry import trace

router = APIRouter()
tracer = trace.get_tracer(__name__)

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, user: User = Depends(get_current_user)):
    """
    Chat completions endpoint with enhanced tracing
    """

    # Get current span (created by FastAPI auto-instrumentation)
    current_span = trace.get_current_span()

    # Add business context to the span
    if current_span.is_recording():
        current_span.set_attribute("customer.id", user.id)
        current_span.set_attribute("request.model", request.model)
        current_span.set_attribute("request.provider", request.provider or "auto")

    # Create a nested span for the inference operation
    with tracer.start_as_current_span("model_inference") as inference_span:
        inference_span.set_attribute("customer.id", user.id)

        # Call LLM provider (which creates its own nested span)
        response = await call_llm_provider(
            provider=request.provider or "openrouter",
            model=request.model,
            messages=request.messages,
            customer_id=user.id,
        )

        # Add response metadata to span
        if response.usage:
            inference_span.set_attribute("tokens.total", response.usage.total_tokens)

        return response
```

### Step 6: Add Database and Cache Span Attributes

**File: `database.py`** (optional but recommended)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def query_database(query: str):
    """Execute database query with tracing"""
    with tracer.start_as_current_span(
        "database.query",
        kind=trace.SpanKind.CLIENT
    ) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.operation", "SELECT")  # or INSERT, UPDATE, etc.
        span.set_attribute("db.statement", query[:200])  # First 200 chars only

        result = await _execute_query(query)
        span.set_attribute("db.rows_affected", len(result))

        return result
```

**File: `cache.py`** (optional but recommended)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def get_from_cache(key: str):
    """Get value from Redis cache with tracing"""
    with tracer.start_as_current_span(
        "cache.get",
        kind=trace.SpanKind.CLIENT
    ) as span:
        span.set_attribute("cache.system", "redis")
        span.set_attribute("cache.operation", "get")
        span.set_attribute("cache.key", key)

        value = await redis_client.get(key)
        span.set_attribute("cache.hit", value is not None)

        return value
```

---

## Environment Variables

### Required in Railway Backend Service

```bash
# CRITICAL - Tempo endpoint for trace export
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318/v1/traces

# Service identification
SERVICE_VERSION=1.0.0
ENVIRONMENT=production

# Optional - for sampling (start with 100% in staging)
OTEL_TRACES_SAMPLER=always_on
# Or for production with high traffic:
# OTEL_TRACES_SAMPLER=traceidratio
# OTEL_TRACES_SAMPLER_ARG=0.1  # Sample 10% of traces
```

### Local Development (.env)

```bash
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318/v1/traces
SERVICE_VERSION=dev
ENVIRONMENT=development
OTEL_TRACES_SAMPLER=always_on
```

---

## Verification Steps

### 1. Check Traces Have Required Attributes

**In Grafana Explore → Tempo datasource:**

Run this TraceQL query:
```
{resource.service.name="gatewayz-api"}
```

Click on any trace → Expand the `llm_inference` span → Check for these attributes:
- ✅ `gen_ai.system` = "anthropic" (or "openai", etc.)
- ✅ `gen_ai.request.model` = "anthropic/claude-opus-4.5"
- ✅ `gen_ai.usage.prompt_tokens` = (some number)
- ✅ `gen_ai.usage.completion_tokens` = (some number)
- ✅ `ai.provider` = "openrouter"
- ✅ `customer.id` = "cust_..."

### 2. Check Span Metrics Are Generated

**In Grafana Explore → Mimir datasource:**

Run this query:
```promql
traces_spanmetrics_calls_total
```

Should return metrics with labels like:
```
traces_spanmetrics_calls_total{
  service_name="gatewayz-api",
  gen_ai_request_model="anthropic/claude-opus-4.5",
  gen_ai_system="anthropic",
  ai_provider="openrouter"
}
```

### 3. Verify Dashboard Data Appears

**Go to Dashboards → Distributed Tracing:**

Check these panels:
- "Span Calls Rate" (Panel 202) — should show non-zero value
- "Most Popular Models" (Panel 209) — should show bar chart with model names
- "P95 Latency by Provider" (Panel 210) — should show provider breakdown

---

## Testing Procedure

### Stage 1: Local Testing

```bash
# 1. Start local observability stack
cd railway-grafana-stack
docker-compose up -d

# 2. In backend repo (on new branch):
# - Implement OpenTelemetry changes above
# - Set TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318/v1/traces

# 3. Start backend locally
python -m uvicorn main:app --reload

# 4. Send test request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-opus-4.5",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 5. Wait 30 seconds for trace ingestion

# 6. Check Grafana
# Open http://localhost:3000
# Go to Explore → Tempo
# Query: {resource.service.name="gatewayz-api"}
# Verify span attributes are present
```

### Stage 2: Staging Deployment

```bash
# 1. Merge branch to staging branch
# 2. Deploy to Railway staging environment
# 3. Set TEMPO_OTLP_HTTP_ENDPOINT in Railway staging service
# 4. Run verification queries in production Grafana (filtered by env="staging")
# 5. Monitor for 24 hours
```

### Stage 3: Production Deployment

```bash
# Only after staging verification passes:
# 1. Merge to main
# 2. Deploy to Railway production
# 3. Monitor dashboards immediately after deployment
# 4. Be ready to rollback if issues
```

---

## Common Issues & Solutions

### Issue 1: Traces Not Appearing

**Symptoms:** No traces in Tempo after sending requests

**Check:**
```bash
# In backend logs, look for:
logger.info("OpenTelemetry configured successfully")

# Check env var is set:
echo $TEMPO_OTLP_HTTP_ENDPOINT
# Should output: http://tempo.railway.internal:4318/v1/traces
```

**Solution:**
- Verify `TEMPO_OTLP_HTTP_ENDPOINT` is set in Railway
- Check backend can reach Tempo: `curl http://tempo.railway.internal:4318/v1/traces`
- Restart backend service after setting env var

### Issue 2: Traces Exist But No Span Metrics

**Symptoms:** Traces visible in Tempo, but `traces_spanmetrics_calls_total` returns no data

**Check:**
```bash
# In Grafana Explore → Tempo, inspect a trace
# Look for span with name "llm_inference" or similar
# Check if it has these attributes:
# - gen_ai.request.model
# - gen_ai.system
```

**Solution:**
- Span attributes are missing → Review span instrumentation code
- Attributes have wrong names → Use exact names from this guide
- Attributes on wrong span → Must be on the LLM API call span

### Issue 3: Wrong Label Names in Metrics

**Symptoms:** Span metrics exist but dashboard queries return no data

**Check:**
```bash
# Query: traces_spanmetrics_calls_total
# Look at the label names returned
# Expected: gen_ai_request_model (underscores)
# Not: gen_ai.request.model (dots)
```

**Solution:**
- Tempo automatically converts dots to underscores in labels
- Dashboard queries must use underscored versions: `gen_ai_request_model` not `gen_ai.request.model`

### Issue 4: High Cardinality Warning

**Symptoms:** Tempo logs show "dropping label due to cardinality"

**Cause:** Too many unique values for a dimension (e.g., customer.id with millions of users)

**Solution:**
```yaml
# In tempo/tempo.yml, adjust:
overrides:
  defaults:
    metrics_generator:
      processors: [span-metrics]
      # Increase cardinality limit
      collection_interval: 15s
      max_dimensions: 10  # Increase if needed
```

---

## Attribute Naming Reference

| Span Attribute (dots) | Prometheus Label (underscores) | Example Value |
|-----------------------|-------------------------------|---------------|
| `gen_ai.system` | `gen_ai_system` | `"anthropic"` |
| `gen_ai.request.model` | `gen_ai_request_model` | `"anthropic/claude-opus-4.5"` |
| `gen_ai.usage.prompt_tokens` | `gen_ai_usage_prompt_tokens` | `450` |
| `gen_ai.usage.completion_tokens` | `gen_ai_usage_completion_tokens` | `823` |
| `ai.provider` | `ai_provider` | `"openrouter"` |
| `customer.id` | `customer_id` | `"cust_abc123"` |
| `resource.service.name` | `service_name` | `"gatewayz-api"` |

---

## Next Steps

1. ✅ Read this guide thoroughly
2. ⚠️ Create new backend branch: `feat/enhanced-trace-attributes`
3. ⚠️ Implement OpenTelemetry instrumentation (Steps 1-6 above)
4. ⚠️ Test locally using testing procedure
5. ⚠️ Deploy to staging and verify
6. ⚠️ Deploy to production after 24h staging validation
7. ✅ Monitor dashboards for data population

---

**Questions?** See `TRACE_DATA_VERIFICATION_CHECKLIST.md` for step-by-step validation.
**Reference:** See `OPENTELEMETRY_LLM_CONVENTIONS.md` for complete semantic conventions list.
