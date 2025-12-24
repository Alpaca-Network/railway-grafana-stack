# Backend Integration Quick Reference

**TL;DR - What backend needs to do for full observability**

## ✅ Already Working

Your backend already exports these metrics - **no changes needed**:

- ✅ `fastapi_requests_total` - HTTP requests
- ✅ `fastapi_requests_duration_seconds` - Request latency
- ✅ `model_inference_requests_total` - Model calls
- ✅ `model_inference_duration_seconds` - Model latency
- ✅ `tokens_used_total` - Token usage
- ✅ `credits_used_total` - Credit usage
- ✅ `database_queries_total` - Database operations
- ✅ `cache_hits_total`, `cache_misses_total` - Cache metrics
- ✅ `backend_ttfb_seconds` - Time to first byte
- ✅ `time_to_first_chunk_seconds` - TTFC

**Keep these! They're perfect.**

---

## ❌ Missing - Critical Priority

These metrics are **defined but empty**. They need data:

### 1. Provider Availability
```python
from prometheus_client import Gauge

provider_availability = Gauge(
    'provider_availability',
    'Provider availability (1=up, 0=down)',
    ['provider']
)

# Update every 30-60 seconds
provider_availability.labels(provider="openrouter").set(1)  # or 0 if down
```

### 2. Provider Error Rate
```python
provider_error_rate = Gauge(
    'provider_error_rate',
    'Error rate 0-1',
    ['provider']
)

# Calculate from last 5 minutes
error_rate = errors / total_requests
provider_error_rate.labels(provider="openrouter").set(error_rate)
```

### 3. Provider Response Time
```python
from prometheus_client import Histogram

provider_response_time = Histogram(
    'provider_response_time_seconds',
    'Response time',
    ['provider'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Record on every provider API call
with provider_response_time.labels(provider="openrouter").time():
    response = await call_provider_api()
```

### 4. Provider Health Score
```python
provider_health_score = Gauge(
    'gatewayz_provider_health_score',
    'Health score 0-1',
    ['provider']
)

# Combine availability, error_rate, latency
score = (availability * 0.4) + ((1 - error_rate) * 0.3) + (latency_score * 0.3)
provider_health_score.labels(provider="openrouter").set(score)
```

### 5. Circuit Breaker State
```python
circuit_breaker_state = Gauge(
    'gatewayz_circuit_breaker_state',
    'Circuit breaker state',
    ['provider', 'state']
)

# Update when state changes
circuit_breaker_state.labels(provider="openrouter", state="closed").set(1)
circuit_breaker_state.labels(provider="openrouter", state="open").set(0)
circuit_breaker_state.labels(provider="openrouter", state="half_open").set(0)
```

---

## 🔄 Background Task Needed

Create a background task that runs every 30-60 seconds:

```python
import asyncio

async def monitor_provider_health():
    while True:
        for provider in get_all_providers():
            # Calculate from recent requests (last 5 min)
            availability = calculate_availability(provider)
            error_rate = calculate_error_rate(provider)
            health_score = calculate_health_score(provider)

            # Update metrics
            provider_availability.labels(provider=provider).set(availability)
            provider_error_rate.labels(provider=provider).set(error_rate)
            provider_health_score.labels(provider=provider).set(health_score)

        await asyncio.sleep(30)

# Start it
asyncio.create_task(monitor_provider_health())
```

---

## 📝 Logging (Recommended)

Send logs to Loki:

```bash
pip install python-logging-loki
```

```python
from logging_loki import LokiHandler

loki_handler = LokiHandler(
    url="http://loki.railway.internal:3100/loki/api/v1/push",
    tags={"app": "gatewayz-api", "env": "production"}
)

logger = logging.getLogger("gatewayz")
logger.addHandler(loki_handler)

# Use it
logger.info("Request processed", extra={
    "user_id": "123",
    "model": "claude-opus-4.5",
    "duration_ms": 1234
})
```

---

## 🔍 Tracing (Recommended)

Send traces to Tempo:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp
```

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup
trace.set_tracer_provider(TracerProvider())
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo.railway.internal:4318/v1/traces"
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Manual spans
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("model_inference"):
    result = await call_model()
```

---

## 📊 Optional Enhancements

### Cost Tracking
```python
cost_by_provider = Counter('gatewayz_cost_by_provider', 'Cost USD', ['provider'])

# After each request
cost = calculate_cost(tokens, model_pricing)
cost_by_provider.labels(provider="openrouter").inc(cost)
```

### Redis Operations
```python
redis_operations = Counter('gatewayz_redis_operations_total', 'Redis ops', ['operation'])

# On each Redis call
redis_operations.labels(operation='get').inc()
redis_operations.labels(operation='set').inc()
```

---

## 🎯 Implementation Priority

### Week 1 (Critical)
1. Provider availability metric
2. Provider error rate metric
3. Provider response time metric
4. Provider health score metric
5. Background health monitoring task

### Week 2 (Important)
6. Circuit breaker state metric
7. Logging integration (Loki)
8. Tracing integration (Tempo)

### Week 3 (Nice to have)
9. Cost tracking
10. Redis instrumentation
11. Provider health endpoint (`GET /health/dashboard`)

---

## 🧪 Testing

```bash
# Test metrics endpoint
curl https://api.gatewayz.ai/metrics | grep provider_

# Should see:
# provider_availability{provider="openrouter"} 1.0
# provider_error_rate{provider="openrouter"} 0.02
# gatewayz_provider_health_score{provider="openrouter"} 0.95

# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# Check logs in Loki
# Go to Grafana → Explore → Loki → {app="gatewayz-api"}

# Check traces in Tempo
# Go to Grafana → Explore → Tempo → Search
```

---

## 📚 Full Details

See [COMPLETE_BACKEND_INTEGRATION_GUIDE.md](COMPLETE_BACKEND_INTEGRATION_GUIDE.md) for:
- Detailed implementation examples
- Code snippets for every metric
- Logging best practices
- Tracing configuration
- Redis monitoring options
- Testing procedures

---

## ❓ Questions?

- **How do I calculate error rate?** → Count failed requests / total requests in last 5 minutes
- **Where do I run the background task?** → In your FastAPI startup event or worker process
- **What if provider has no recent requests?** → Return default values (availability=1.0, error_rate=0.0)
- **How do I test locally?** → Use `docker compose up` to run observability stack locally

**Need help?** Check the full guide or existing examples in `examples/` directory.
