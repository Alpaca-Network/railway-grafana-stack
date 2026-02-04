# Complete Backend Integration Guide

This document provides **everything** the backend team needs to implement for full observability stack integration.

## 🎯 Quick Start

**NEW:** We've refactored the observability stack for transparent telemetry ingestion!

- **For OpenTelemetry tracing integration**: See [OTLP Integration Guide](OTLP_INTEGRATION_GUIDE.md) ⭐ **START HERE**
- **For architecture overview**: See [Transparent Telemetry Ingestion Architecture](../architecture/TRANSPARENT_TELEMETRY_INGESTION.md)
- **For comprehensive backend requirements**: Continue reading this document

## 📋 Table of Contents

1. [Required Endpoints](#required-endpoints)
2. [Metrics to Export](#metrics-to-export)
3. [Logging Integration](#logging-integration)
4. [Tracing Integration](#tracing-integration) - **See [OTLP_INTEGRATION_GUIDE.md](OTLP_INTEGRATION_GUIDE.md)**
5. [Redis Integration](#redis-integration)
6. [Provider Health Monitoring](#provider-health-monitoring)
7. [Implementation Checklist](#implementation-checklist)
8. [Testing & Validation](#testing--validation)

---

## 1. Required Endpoints

### 1.1 Metrics Endpoint (CRITICAL)

**Endpoint:** `GET /metrics`

**Purpose:** Prometheus scrapes this endpoint every 15 seconds to collect metrics

**Requirements:**
- Must be publicly accessible (or accessible from Prometheus)
- Must return Prometheus-formatted metrics
- Response time should be < 100ms
- Content-Type: `text/plain; version=0.0.4`

**Current Status:** ✅ Already implemented at `https://api.gatewayz.ai/metrics`

**What Prometheus Expects:**
```
# HELP metric_name Description of the metric
# TYPE metric_name counter|gauge|histogram|summary
metric_name{label1="value1",label2="value2"} 123.45
```

**Implementation (Python FastAPI):**
```python
from prometheus_client import make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

### 1.2 Health Check Endpoint (REQUIRED)

**Endpoint:** `GET /health`

**Purpose:** Used by monitoring systems to verify service is alive

**Requirements:**
- Returns HTTP 200 when healthy
- Returns HTTP 503 when unhealthy
- Response time < 50ms
- Checks critical dependencies (database, Redis, providers)

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-23T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "providers": "healthy"
  }
}
```

**Current Status:** ✅ Already implemented

---

### 1.3 Provider Health Dashboard Endpoint (HIGHLY RECOMMENDED)

**Endpoint:** `GET /health/dashboard`

**Purpose:** Provides aggregated health data for all providers in a single request

**Requirements:**
- Returns comprehensive provider status
- Includes health scores, availability, error rates
- Used by the GatewayZ Application Health dashboard
- Should cache results for 30-60 seconds to avoid overhead

**Response Format:**
```json
{
  "timestamp": "2025-12-23T10:30:00Z",
  "providers": [
    {
      "name": "openrouter",
      "status": "healthy",
      "availability": 1.0,
      "error_rate": 0.02,
      "avg_response_time_ms": 450,
      "health_score": 0.95,
      "requests_last_hour": 1523,
      "errors_last_hour": 31,
      "circuit_breaker_state": "closed"
    },
    {
      "name": "cerebras",
      "status": "degraded",
      "availability": 0.85,
      "error_rate": 0.15,
      "avg_response_time_ms": 1200,
      "health_score": 0.70,
      "requests_last_hour": 234,
      "errors_last_hour": 35,
      "circuit_breaker_state": "open"
    }
  ],
  "summary": {
    "total_providers": 12,
    "healthy": 9,
    "degraded": 2,
    "down": 1,
    "overall_health_score": 0.87
  }
}
```

**Current Status:** ⚠️ Endpoint exists but may need enhancement

**Dashboard Usage:**
- The GatewayZ Application Health dashboard can query this endpoint
- Eliminates need for multiple metric queries
- Provides real-time provider status

---

### 1.4 Model Statistics Endpoint (RECOMMENDED)

**Endpoint:** `GET /models/stats`

**Purpose:** Provides aggregated model usage statistics

**Response Format:**
```json
{
  "timestamp": "2025-12-23T10:30:00Z",
  "time_window": "24h",
  "models": [
    {
      "model": "anthropic/claude-opus-4.5",
      "provider": "openrouter",
      "total_requests": 6365,
      "successful_requests": 6320,
      "failed_requests": 45,
      "avg_latency_ms": 1234,
      "p95_latency_ms": 2100,
      "p99_latency_ms": 3500,
      "total_tokens": 12500000,
      "total_cost_usd": 125.50,
      "uptime_percentage": 99.3
    }
  ]
}
```

**Current Status:** ❓ Unknown - may need implementation

---

## 2. Metrics to Export

### 2.1 FastAPI Metrics (ALREADY EXPORTED ✅)

Your backend already exports these - great job!

```python
# These are working:
fastapi_requests_total{method, path, status_code}
fastapi_requests_duration_seconds{method, path}
fastapi_requests_in_progress{method, path}
fastapi_request_size_bytes{method, path}
fastapi_response_size_bytes{method, path}
```

**No changes needed - these are perfect!**

---

### 2.2 Model Inference Metrics (ALREADY EXPORTED ✅)

```python
# These are working:
model_inference_requests_total{model, provider, status}
model_inference_duration_seconds{model, provider}
tokens_used_total{model, provider}
credits_used_total{model, provider}
```

**No changes needed - excellent instrumentation!**

---

### 2.3 Provider Health Metrics (CRITICAL - NEEDS IMPLEMENTATION ❌)

These metrics are **defined but empty**. They need to be populated.

#### 2.3.1 Provider Availability

**Metric Name:** `provider_availability`
**Type:** Gauge (0 or 1)
**Labels:** `provider`

**Purpose:** Tracks if each provider is currently available

**Implementation:**
```python
from prometheus_client import Gauge

provider_availability = Gauge(
    'provider_availability',
    'Provider availability status (1=available, 0=unavailable)',
    ['provider']
)

# Update in background task or after each health check
async def update_provider_availability():
    for provider in get_all_providers():
        is_available = await check_provider_health(provider.name)
        provider_availability.labels(provider=provider.name).set(
            1 if is_available else 0
        )
```

**Update Frequency:** Every 30-60 seconds

**Health Check Logic:**
```python
async def check_provider_health(provider_name: str) -> bool:
    try:
        # Option 1: Make actual API call to provider
        response = await provider_client.health_check(provider_name)
        return response.status_code == 200

        # Option 2: Check last successful request timestamp
        last_success = get_last_successful_request(provider_name)
        return (datetime.now() - last_success) < timedelta(minutes=5)

        # Option 3: Check circuit breaker state
        return circuit_breaker.is_closed(provider_name)
    except Exception:
        return False
```

---

#### 2.3.2 Provider Error Rate

**Metric Name:** `provider_error_rate`
**Type:** Gauge (0.0 to 1.0)
**Labels:** `provider`

**Purpose:** Percentage of failed requests per provider

**Implementation:**
```python
from prometheus_client import Gauge

provider_error_rate = Gauge(
    'provider_error_rate',
    'Provider error rate (0-1)',
    ['provider']
)

# Calculate and update periodically
async def update_provider_error_rates():
    for provider in get_all_providers():
        # Get counts from last 5 minutes
        total = get_request_count(provider.name, minutes=5)
        errors = get_error_count(provider.name, minutes=5)

        error_rate = errors / total if total > 0 else 0
        provider_error_rate.labels(provider=provider.name).set(error_rate)
```

**Calculation Window:** Last 5 minutes (rolling)

**Update Frequency:** Every 30 seconds

**Alternative - Calculate from Existing Metrics:**
```python
# If you prefer not to maintain separate state:
# Use model_inference_requests_total with status label
def calculate_error_rate(provider: str, window: str = '5m'):
    success_count = sum(
        model_inference_requests_total.labels(
            model=m, provider=provider, status='success'
        )._value.get() for m in models
    )
    error_count = sum(
        model_inference_requests_total.labels(
            model=m, provider=provider, status='error'
        )._value.get() for m in models
    )
    total = success_count + error_count
    return error_count / total if total > 0 else 0
```

---

#### 2.3.3 Provider Response Time

**Metric Name:** `provider_response_time_seconds`
**Type:** Histogram
**Labels:** `provider`

**Purpose:** Tracks response time distribution per provider

**Implementation:**
```python
from prometheus_client import Histogram

provider_response_time = Histogram(
    'provider_response_time_seconds',
    'Provider response time in seconds',
    ['provider'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]  # Customize based on your SLAs
)

# Instrument every provider API call
async def call_provider_api(provider: str, request):
    with provider_response_time.labels(provider=provider).time():
        response = await provider_client.call(provider, request)
        return response
```

**Alternative - Track Manually:**
```python
import time

async def call_provider_api(provider: str, request):
    start = time.time()
    try:
        response = await provider_client.call(provider, request)
        duration = time.time() - start
        provider_response_time.labels(provider=provider).observe(duration)
        return response
    except Exception as e:
        duration = time.time() - start
        provider_response_time.labels(provider=provider).observe(duration)
        raise
```

---

#### 2.3.4 Provider Health Score

**Metric Name:** `gatewayz_provider_health_score`
**Type:** Gauge (0.0 to 1.0)
**Labels:** `provider`

**Purpose:** Composite health score combining availability, error rate, and latency

**Implementation:**
```python
from prometheus_client import Gauge

provider_health_score = Gauge(
    'gatewayz_provider_health_score',
    'Provider health score (0-1)',
    ['provider']
)

async def calculate_provider_health_score(provider: str) -> float:
    # Get component scores
    availability = provider_availability.labels(provider=provider)._value.get()
    error_rate = provider_error_rate.labels(provider=provider)._value.get()

    # Get average latency from histogram
    latency_stats = get_latency_percentiles(provider)
    p95_latency = latency_stats['p95']

    # Normalize latency (assume 2s is acceptable, 10s is terrible)
    latency_score = max(0, 1 - (p95_latency - 2.0) / 8.0)

    # Calculate composite score
    # Weights: availability=40%, error_rate=30%, latency=30%
    health_score = (
        availability * 0.4 +
        (1 - error_rate) * 0.3 +
        latency_score * 0.3
    )

    return max(0.0, min(1.0, health_score))

# Update periodically
async def update_provider_health_scores():
    for provider in get_all_providers():
        score = await calculate_provider_health_score(provider.name)
        provider_health_score.labels(provider=provider.name).set(score)
```

**Update Frequency:** Every 30-60 seconds

---

### 2.4 Circuit Breaker Metrics (HIGH PRIORITY - NEEDS IMPLEMENTATION ❌)

**Metric Name:** `gatewayz_circuit_breaker_state`
**Type:** Gauge
**Labels:** `provider`, `state` (values: "open", "closed", "half_open")

**Purpose:** Tracks circuit breaker state for each provider

**Implementation:**
```python
from prometheus_client import Gauge

circuit_breaker_state = Gauge(
    'gatewayz_circuit_breaker_state',
    'Circuit breaker state (1=in this state, 0=not)',
    ['provider', 'state']
)

# Update when circuit breaker state changes
def on_circuit_breaker_change(provider: str, new_state: str):
    # Set new state to 1
    circuit_breaker_state.labels(provider=provider, state=new_state).set(1)

    # Set other states to 0
    other_states = ['open', 'closed', 'half_open']
    other_states.remove(new_state)
    for state in other_states:
        circuit_breaker_state.labels(provider=provider, state=state).set(0)

# Example usage with your circuit breaker library
class ProviderCircuitBreaker:
    def __init__(self, provider: str):
        self.provider = provider
        self.state = 'closed'

    def open(self):
        self.state = 'open'
        on_circuit_breaker_change(self.provider, 'open')

    def close(self):
        self.state = 'closed'
        on_circuit_breaker_change(self.provider, 'closed')

    def half_open(self):
        self.state = 'half_open'
        on_circuit_breaker_change(self.provider, 'half_open')
```

**Dashboard Usage:**
- Shows which providers have open circuit breakers
- Helps identify failing providers quickly

---

### 2.5 Cost Tracking Metrics (MEDIUM PRIORITY - OPTIONAL ⚠️)

**Metric Name:** `gatewayz_cost_by_provider`
**Type:** Counter
**Labels:** `provider`

**Purpose:** Tracks total cost incurred per provider (in USD)

**Implementation:**
```python
from prometheus_client import Counter

cost_by_provider = Counter(
    'gatewayz_cost_by_provider',
    'Total cost by provider in USD',
    ['provider']
)

# Increment after each API call
async def process_model_request(request):
    response = await call_provider_api(request.provider, request)

    # Calculate cost based on token usage and model pricing
    cost = calculate_cost(
        model=request.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens
    )

    cost_by_provider.labels(provider=request.provider).inc(cost)

    return response

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    # Get pricing from your pricing table
    pricing = get_model_pricing(model)

    input_cost = (input_tokens / 1_000_000) * pricing['input_price_per_million']
    output_cost = (output_tokens / 1_000_000) * pricing['output_price_per_million']

    return input_cost + output_cost
```

**Dashboard Usage:**
- Track spending by provider
- Identify cost optimization opportunities

---

### 2.6 Database Metrics (ALREADY EXPORTED ✅)

```python
# These are working:
database_queries_total{operation}
database_query_duration_seconds{operation}
```

**Verify** that these are being updated on every database query.

---

### 2.7 Cache Metrics (ALREADY EXPORTED ✅)

```python
# These are working:
cache_hits_total
cache_misses_total
cache_size_bytes
```

**Perfect - no changes needed!**

**Cache Hit Rate Calculation** (done in Grafana):
```promql
rate(cache_hits_total[5m]) /
(rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

---

### 2.8 Performance Metrics (ALREADY EXPORTED ✅)

```python
# These are working:
backend_ttfb_seconds
streaming_duration_seconds
time_to_first_chunk_seconds{model, provider}
```

**Excellent instrumentation - keep these!**

---

## 3. Logging Integration

### 3.1 Send Logs to Loki

**Loki URL:** `http://loki:3100/loki/api/v1/push` (internal Railway)

**Requirements:**
- Send logs in JSON format
- Include labels for filtering (app, env, level, service)
- Use structured logging (not plain text)

**Python Implementation (using logging-loki):**

```bash
pip install python-logging-loki
```

```python
import logging
from logging_loki import LokiHandler

# Configure Loki handler
loki_handler = LokiHandler(
    url="http://loki.railway.internal:3100/loki/api/v1/push",
    tags={"app": "gatewayz-api", "env": "production"},
    version="1",
)

# Add to logger
logger = logging.getLogger("gatewayz")
logger.addHandler(loki_handler)
logger.setLevel(logging.INFO)

# Use structured logging
logger.info(
    "Model inference completed",
    extra={
        "user_id": "user_123",
        "model": "claude-opus-4.5",
        "provider": "openrouter",
        "duration_ms": 1234,
        "tokens": 450,
        "status": "success"
    }
)
```

**Log Levels:**
- `ERROR`: Exceptions, failures, critical issues
- `WARNING`: Degraded performance, retries, fallbacks
- `INFO`: Normal operations, successful requests
- `DEBUG`: Detailed debugging info (disable in production)

**Important Labels to Include:**
```python
{
    "app": "gatewayz-api",
    "env": "production|staging",
    "service": "api|worker|scheduler",
    "level": "info|warning|error",
    "user_id": "user_123",  # Optional - for user-specific debugging
    "request_id": "req_abc123",  # For request tracing
}
```

---

### 3.2 Log Format Standards

**Use JSON format for structured logs:**

```json
{
  "timestamp": "2025-12-23T10:30:00.123Z",
  "level": "info",
  "message": "Model inference completed",
  "user_id": "user_123",
  "model": "anthropic/claude-opus-4.5",
  "provider": "openrouter",
  "duration_ms": 1234,
  "tokens_used": 450,
  "cost_usd": 0.045,
  "status": "success"
}
```

**What to Log:**

**✅ DO LOG:**
- API requests/responses (without sensitive data)
- Model inference calls
- Provider API calls
- Errors and exceptions
- Performance metrics
- User actions (login, API key creation, etc.)

**❌ DON'T LOG:**
- User passwords
- API keys
- Credit card numbers
- Personal identifiable information (PII) unless necessary
- Full message content (summarize or redact)

---

### 3.3 Error Logging Best Practices

```python
import logging
import traceback

logger = logging.getLogger("gatewayz")

try:
    result = await call_provider_api(provider, request)
except ProviderTimeout as e:
    logger.error(
        "Provider timeout",
        extra={
            "provider": provider,
            "model": request.model,
            "timeout_seconds": e.timeout,
            "request_id": request.id,
            "error_type": "timeout"
        },
        exc_info=True  # Includes traceback
    )
except ProviderError as e:
    logger.error(
        "Provider API error",
        extra={
            "provider": provider,
            "status_code": e.status_code,
            "error_message": str(e),
            "request_id": request.id,
            "error_type": "provider_error"
        }
    )
```

---

## 4. Tracing Integration

### ⭐ NEW: Transparent Telemetry Ingestion

We've completely refactored our tracing stack to provide transparent ingestion with automatic metrics generation!

**👉 [Read the complete OTLP Integration Guide](OTLP_INTEGRATION_GUIDE.md)**

### Key Changes:

1. **Semantic Conventions**: Now using OpenTelemetry Gen AI semantic conventions
2. **Automatic Metrics**: Traces are automatically converted to metrics (no manual instrumentation needed)
3. **Clear Attribute Requirements**: Documented required vs. optional trace attributes
4. **Validation**: Built-in validation and monitoring for missing attributes
5. **Better Documentation**: Step-by-step integration guide with examples

### Quick Summary

**Tempo Endpoints:**
- **HTTP (recommended):** `http://tempo.railway.internal:4318/v1/traces`
- **gRPC:** `http://tempo.railway.internal:4317`

**Required Trace Attributes:**
```python
span.set_attribute("gen_ai.system", "openai")           # AI provider
span.set_attribute("gen_ai.request.model", "gpt-4")     # Model name
span.set_attribute("gen_ai.operation.name", "chat")     # Operation type
span.set_attribute("http.response.status_code", 200)    # HTTP status
```

**What You Get Automatically:**
- Request counts by model/provider
- Latency percentiles (P50, P95, P99)
- Error rates by model
- Model popularity metrics
- Provider health tracking

### 4.2 Implementation (Python FastAPI)

**See [OTLP_INTEGRATION_GUIDE.md](OTLP_INTEGRATION_GUIDE.md) for complete implementation details.**

Quick install:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp-proto-http
```

Minimal example (see full guide for complete implementation):
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Configure with service name
resource = Resource.create({SERVICE_NAME: "gatewayz-api"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# OTLP exporter to Tempo
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo.railway.internal:4318/v1/traces"
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Auto-instrument FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Set required attributes on spans
@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    span = trace.get_current_span()

    # REQUIRED attributes (following OpenTelemetry semantic conventions)
    span.set_attribute("gen_ai.system", "openai")
    span.set_attribute("gen_ai.request.model", request.model)
    span.set_attribute("gen_ai.operation.name", "chat")
    span.set_attribute("http.response.status_code", 200)

    # GatewayZ-specific attributes
    span.set_attribute("gatewayz.provider.name", "openrouter")
    span.set_attribute("gatewayz.customer.id", request.customer_id)

    result = await call_provider_api(request)
    return result
```

### 4.3 What to Trace

**Automatically traced (via auto-instrumentation):**
- ✅ HTTP requests (FastAPI)
- ✅ Database queries (if using supported ORM)
- ✅ HTTP client calls (if using supported client)

**Manually trace these operations:**
- Model inference calls
- Provider API calls
- Cache operations
- Business logic spans

**Required Span Attributes (OpenTelemetry Gen AI Conventions):**
```python
# Required for automatic metrics generation
span.set_attribute("gen_ai.system", "openai")              # AI provider
span.set_attribute("gen_ai.request.model", "gpt-4")        # Model requested
span.set_attribute("gen_ai.operation.name", "chat")        # Operation type
span.set_attribute("http.response.status_code", 200)       # HTTP status

# Recommended
span.set_attribute("gen_ai.response.model", "gpt-4-0613")  # Actual model
span.set_attribute("gen_ai.usage.input_tokens", 450)       # Input tokens
span.set_attribute("gen_ai.usage.output_tokens", 123)      # Output tokens
span.set_attribute("server.address", "api.openai.com")     # Provider endpoint
```

**📚 Complete attribute reference**: See [OTLP_INTEGRATION_GUIDE.md](OTLP_INTEGRATION_GUIDE.md#required-trace-attributes)

---

## 5. Redis Integration

### 5.1 What We Need from Backend

**Option 1: Export Redis Metrics from Application (RECOMMENDED)**

Instrument your Redis calls to track:
- Operation counts (GET, SET, DEL, etc.)
- Operation latencies
- Connection pool status

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
redis_operations = Counter(
    'gatewayz_redis_operations_total',
    'Total Redis operations',
    ['operation', 'status']  # operation: get, set, del; status: success, error
)

redis_duration = Histogram(
    'gatewayz_redis_operation_duration_seconds',
    'Redis operation duration',
    ['operation']
)

redis_pool_connections = Gauge(
    'gatewayz_redis_pool_connections',
    'Redis connection pool status',
    ['state']  # state: active, idle
)

# Instrument Redis calls
async def get_from_cache(key: str):
    start = time.time()
    try:
        result = await redis_client.get(key)
        redis_operations.labels(operation='get', status='success').inc()
        redis_duration.labels(operation='get').observe(time.time() - start)
        return result
    except Exception as e:
        redis_operations.labels(operation='get', status='error').inc()
        raise

async def set_cache(key: str, value: str, ttl: int):
    start = time.time()
    try:
        await redis_client.setex(key, ttl, value)
        redis_operations.labels(operation='set', status='success').inc()
        redis_duration.labels(operation='set').observe(time.time() - start)
    except Exception as e:
        redis_operations.labels(operation='set', status='error').inc()
        raise

# Update connection pool metrics periodically
async def update_redis_pool_metrics():
    pool = redis_client.connection_pool
    redis_pool_connections.labels(state='active').set(pool.num_active_connections)
    redis_pool_connections.labels(state='idle').set(pool.num_idle_connections)
```

**Option 2: Provide Redis Connection Info**

If you prefer infrastructure-level monitoring:

**What we need:**
- Redis host: `redis-production-bb6d.up.railway.app`
- Redis port: `6379`
- Redis password: (if any)
- Access from observability stack (network connectivity)

We'll deploy a Redis exporter that monitors:
- Memory usage
- Connected clients
- Commands per second
- Keyspace statistics

---

### 5.2 Redis Dashboard Metrics

The `gatewayz-redis-services.json` dashboard currently queries:
- `cache_hits_total` ✅ (you already export this)
- `cache_misses_total` ✅ (you already export this)
- `cache_size_bytes` ✅ (you already export this)

**Additional metrics needed for full Redis monitoring:**
```python
# Redis-specific operations
redis_get_operations_total{status}
redis_set_operations_total{status}
redis_del_operations_total{status}
redis_hget_operations_total{status}
redis_hset_operations_total{status}

# Redis latency
redis_operation_duration_seconds{operation}

# Connection pool
redis_pool_connections_current{state="active"|"idle"}
redis_pool_connections_max
```

---

## 6. Provider Health Monitoring

### 6.1 Background Health Checker

Implement a background task that runs every 30-60 seconds:

```python
import asyncio
from datetime import datetime, timedelta

class ProviderHealthMonitor:
    def __init__(self):
        self.last_check = {}
        self.check_interval = timedelta(seconds=30)

    async def start(self):
        """Start background health monitoring"""
        while True:
            await self.check_all_providers()
            await asyncio.sleep(30)

    async def check_all_providers(self):
        """Check health of all providers"""
        providers = get_all_providers()

        for provider in providers:
            try:
                # Calculate metrics from recent requests
                availability = await self.calculate_availability(provider.name)
                error_rate = await self.calculate_error_rate(provider.name)
                avg_response_time = await self.calculate_avg_response_time(provider.name)
                health_score = await self.calculate_health_score(provider.name)

                # Update Prometheus metrics
                provider_availability.labels(provider=provider.name).set(availability)
                provider_error_rate.labels(provider=provider.name).set(error_rate)
                provider_health_score.labels(provider=provider.name).set(health_score)

                # Update circuit breaker state metric
                cb_state = circuit_breaker.get_state(provider.name)
                self.update_circuit_breaker_metric(provider.name, cb_state)

            except Exception as e:
                logger.error(f"Failed to check provider {provider.name}: {e}")

    async def calculate_availability(self, provider: str) -> float:
        """Calculate provider availability (0-1)"""
        # Option 1: Based on recent requests
        recent_window = timedelta(minutes=5)
        requests = get_recent_requests(provider, recent_window)

        if not requests:
            return 1.0  # No recent requests, assume available

        successful = sum(1 for r in requests if r.status == 'success')
        return successful / len(requests) if requests else 1.0

        # Option 2: Based on health check ping
        try:
            response = await ping_provider(provider)
            return 1.0 if response.ok else 0.0
        except:
            return 0.0

    async def calculate_error_rate(self, provider: str) -> float:
        """Calculate error rate over last 5 minutes"""
        window = timedelta(minutes=5)
        requests = get_recent_requests(provider, window)

        if not requests:
            return 0.0

        errors = sum(1 for r in requests if r.status != 'success')
        return errors / len(requests)

    async def calculate_avg_response_time(self, provider: str) -> float:
        """Calculate average response time in seconds"""
        window = timedelta(minutes=5)
        requests = get_recent_requests(provider, window)

        if not requests:
            return 0.0

        total_time = sum(r.duration for r in requests)
        return total_time / len(requests)

    async def calculate_health_score(self, provider: str) -> float:
        """Calculate composite health score (0-1)"""
        availability = await self.calculate_availability(provider)
        error_rate = await self.calculate_error_rate(provider)
        avg_latency = await self.calculate_avg_response_time(provider)

        # Normalize latency (2s good, 10s bad)
        latency_score = max(0, 1 - (avg_latency - 2.0) / 8.0)

        # Weighted score
        score = (
            availability * 0.4 +
            (1 - error_rate) * 0.3 +
            latency_score * 0.3
        )

        return max(0.0, min(1.0, score))

    def update_circuit_breaker_metric(self, provider: str, state: str):
        """Update circuit breaker state metric"""
        for s in ['open', 'closed', 'half_open']:
            value = 1 if s == state else 0
            circuit_breaker_state.labels(provider=provider, state=s).set(value)

# Start the monitor
monitor = ProviderHealthMonitor()
asyncio.create_task(monitor.start())
```

---

### 6.2 Data Storage for Health Monitoring

**Options for storing recent request data:**

**Option 1: In-Memory Cache (Simple)**
```python
from collections import deque
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RequestRecord:
    provider: str
    model: str
    status: str
    duration: float
    timestamp: datetime

class RequestHistory:
    def __init__(self, max_age_minutes=5):
        self.records = deque(maxlen=10000)  # Keep last 10k requests
        self.max_age = timedelta(minutes=max_age_minutes)

    def add(self, record: RequestRecord):
        self.records.append(record)

    def get_recent(self, provider: str, window: timedelta):
        cutoff = datetime.now() - window
        return [
            r for r in self.records
            if r.provider == provider and r.timestamp > cutoff
        ]

# Global instance
request_history = RequestHistory()

# Add to every request
async def process_request(request):
    start = time.time()
    try:
        result = await call_provider_api(request)
        status = 'success'
    except Exception as e:
        status = 'error'
        raise
    finally:
        duration = time.time() - start
        request_history.add(RequestRecord(
            provider=request.provider,
            model=request.model,
            status=status,
            duration=duration,
            timestamp=datetime.now()
        ))
```

**Option 2: Redis (Scalable)**
```python
import json
from datetime import datetime

async def record_provider_request(provider: str, model: str, status: str, duration: float):
    key = f"provider_requests:{provider}"
    record = {
        "model": model,
        "status": status,
        "duration": duration,
        "timestamp": datetime.now().isoformat()
    }

    # Add to Redis list with TTL
    await redis.lpush(key, json.dumps(record))
    await redis.ltrim(key, 0, 999)  # Keep last 1000 requests
    await redis.expire(key, 300)  # 5 minute TTL
```

**Option 3: PostgreSQL (Comprehensive)**
```sql
CREATE TABLE provider_requests (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(100),
    model VARCHAR(200),
    status VARCHAR(50),
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW(),
    INDEX idx_provider_timestamp (provider, timestamp)
);

-- Query recent requests
SELECT
    provider,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
    AVG(duration_ms) as avg_duration
FROM provider_requests
WHERE provider = 'openrouter'
  AND timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY provider;
```

---

## 7. Implementation Checklist

### Phase 1: Critical (Week 1)

- [ ] **Verify `/metrics` endpoint is working**
  - [ ] Test: `curl https://api.gatewayz.ai/metrics`
  - [ ] Verify Prometheus can scrape it
  - [ ] Check response time < 100ms

- [ ] **Implement provider health metrics**
  - [ ] Add `provider_availability` metric
  - [ ] Add `provider_error_rate` metric
  - [ ] Add `provider_response_time_seconds` histogram
  - [ ] Add `gatewayz_provider_health_score` metric

- [ ] **Implement circuit breaker metrics**
  - [ ] Add `gatewayz_circuit_breaker_state` metric
  - [ ] Update on every state change

- [ ] **Set up background health monitoring**
  - [ ] Create background task
  - [ ] Update metrics every 30-60 seconds
  - [ ] Calculate health scores

### Phase 2: Important (Week 2)

- [ ] **Logging integration**
  - [ ] Install `python-logging-loki`
  - [ ] Configure Loki handler
  - [ ] Use structured logging
  - [ ] Add proper labels

- [ ] **Tracing integration**
  - [ ] Install OpenTelemetry packages
  - [ ] Configure OTLP exporter
  - [ ] Instrument FastAPI
  - [ ] Add custom spans for important operations

- [ ] **Redis instrumentation**
  - [ ] Add Redis operation metrics
  - [ ] Track connection pool
  - [ ] Monitor cache effectiveness

### Phase 3: Nice to Have (Week 3)

- [ ] **Cost tracking**
  - [ ] Add `gatewayz_cost_by_provider` metric
  - [ ] Calculate costs per request
  - [ ] Track total spending

- [ ] **Provider health endpoint**
  - [ ] Implement `GET /health/dashboard`
  - [ ] Return aggregated provider data
  - [ ] Cache results for 30-60 seconds

- [ ] **Model statistics endpoint**
  - [ ] Implement `GET /models/stats`
  - [ ] Aggregate model usage data

---

## 8. Testing & Validation

### 8.1 Testing Metrics Export

```bash
# Test metrics endpoint
curl https://api.gatewayz.ai/metrics | grep provider_availability

# Should see:
# provider_availability{provider="openrouter"} 1.0
# provider_availability{provider="cerebras"} 1.0
```

### 8.2 Testing Prometheus Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "gatewayz_prod")'

# Should show health: "up"
```

### 8.3 Testing Logs

```python
# Send test log
logger.info("Test log message", extra={"test": "value"})

# Check Loki received it
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={app="gatewayz-api"}' \
  | jq
```

### 8.4 Testing Traces

```bash
# Check Tempo received traces
curl http://localhost:3200/api/search?tags=service.name=gatewayz-api | jq
```

### 8.5 Validation Checklist

- [ ] Metrics endpoint returns data
- [ ] Prometheus shows all targets as "UP"
- [ ] Provider health metrics have values > 0
- [ ] Logs appear in Grafana Loki dashboard
- [ ] Traces appear in Grafana Tempo dashboard
- [ ] Cache metrics show hit/miss counts
- [ ] Circuit breaker states are updating

---

## 9. Code Examples Summary

### Complete Example: Instrumented Request Handler

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from opentelemetry import trace
import logging
import time

app = FastAPI()

# Metrics
model_requests = Counter('model_inference_requests_total', 'Model requests', ['model', 'provider', 'status'])
model_duration = Histogram('model_inference_duration_seconds', 'Duration', ['model', 'provider'])
provider_availability = Gauge('provider_availability', 'Availability', ['provider'])
provider_error_rate = Gauge('provider_error_rate', 'Error rate', ['provider'])
cost_by_provider = Counter('gatewayz_cost_by_provider', 'Cost in USD', ['provider'])

# Logging
logger = logging.getLogger("gatewayz")

# Tracing
tracer = trace.get_tracer(__name__)

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    # Start trace
    with tracer.start_as_current_span("chat_completion") as span:
        span.set_attribute("model", request.model)
        span.set_attribute("provider", "openrouter")

        # Record start time
        start = time.time()

        try:
            # Call provider
            with tracer.start_as_current_span("provider_api_call"):
                result = await call_provider_api(request)

            # Record metrics
            duration = time.time() - start
            model_duration.labels(model=request.model, provider="openrouter").observe(duration)
            model_requests.labels(model=request.model, provider="openrouter", status="success").inc()

            # Calculate and record cost
            cost = calculate_cost(request.model, result.usage.total_tokens)
            cost_by_provider.labels(provider="openrouter").inc(cost)

            # Log success
            logger.info(
                "Chat completion successful",
                extra={
                    "model": request.model,
                    "provider": "openrouter",
                    "duration_ms": duration * 1000,
                    "tokens": result.usage.total_tokens,
                    "cost_usd": cost,
                    "user_id": request.user_id
                }
            )

            # Update span
            span.set_attribute("tokens_used", result.usage.total_tokens)
            span.set_attribute("cost_usd", cost)

            return result

        except ProviderError as e:
            # Record error metrics
            model_requests.labels(model=request.model, provider="openrouter", status="error").inc()

            # Log error
            logger.error(
                "Provider API error",
                extra={
                    "model": request.model,
                    "provider": "openrouter",
                    "error": str(e),
                    "user_id": request.user_id
                },
                exc_info=True
            )

            # Update trace
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)

            raise
```

---

## 10. Support & Questions

If you have questions about implementing any of these requirements:

1. **Check the documentation:**
   - [BACKEND_METRICS_REQUIREMENTS.md](BACKEND_METRICS_REQUIREMENTS.md)
   - [REDIS_MONITORING_GUIDE.md](../REDIS_MONITORING_GUIDE.md)

2. **Test locally:**
   - Use `docker compose up` to run the stack locally
   - Test metrics endpoint with `curl`
   - Verify data appears in Grafana

3. **Example implementations:**
   - See `examples/api/` for Node.js example
   - See `examples/provider-metrics-exporter.py` for Python example

4. **Grafana dashboards:**
   - All dashboards are in `grafana/dashboards/`
   - Review JSON to see exact queries used

---

**This guide provides EVERYTHING needed for full integration. Start with Phase 1 (Critical) items first!**
