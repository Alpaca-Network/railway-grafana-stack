# Backend Metrics Requirements

This document outlines the metrics that need to be exported by the GatewayZ backend to fully support all Grafana dashboards.

## ✅ Currently Exported Metrics (Working)

These metrics are already being exported by the backend and working correctly:

### FastAPI Metrics
- `fastapi_requests_total` - Total HTTP requests
- `fastapi_requests_duration_seconds` - Request latency histogram
- `fastapi_requests_in_progress` - Current in-flight requests
- `fastapi_request_size_bytes` - HTTP request body size
- `fastapi_response_size_bytes` - HTTP response body size
- `fastapi_exceptions_total` - Total exceptions

### Model Inference Metrics
- `model_inference_requests_total{model, provider, status}` - Total model requests
- `model_inference_duration_seconds{model, provider}` - Model inference latency histogram
- `tokens_used_total{model, provider}` - Total tokens consumed
- `credits_used_total{model, provider}` - Total credits used

### Database & Cache Metrics
- `database_queries_total{operation}` - Total database queries
- `database_query_duration_seconds{operation}` - Database query latency
- `cache_hits_total` - Cache hits
- `cache_misses_total` - Cache misses
- `cache_size_bytes` - Current cache size

### Performance Metrics
- `backend_ttfb_seconds` - Time to first byte histogram
- `streaming_duration_seconds` - Streaming duration histogram
- `time_to_first_chunk_seconds{model, provider}` - TTFC histogram
- `rate_limited_requests_total` - Rate-limited requests

### User Metrics
- `active_api_keys` - Active API keys count
- `api_key_usage_total{api_key}` - API key usage
- `active_connections` - Active connections
- `subscription_count` - Active subscriptions
- `trial_active` - Active trials
- `user_credit_balance{user_id}` - User credit balance

---

## ❌ Missing Metrics (Need Implementation)

These metrics are referenced in dashboards but NOT currently exported. They need to be added to the backend.

### 1. Provider Health Metrics

#### `gatewayz_provider_health_score{provider}`
- **Type:** Gauge (0.0 - 1.0)
- **Labels:** `provider` (e.g., "openrouter", "google-vertex", "cerebras")
- **Description:** Overall health score of each provider
- **Calculation:** Combine availability, error rate, and latency into a single score
- **Used in:** gatewayz-application-health.json (Panel ID 2, 7, 21)

**Implementation Suggestion:**
```python
from prometheus_client import Gauge

provider_health_score = Gauge(
    'gatewayz_provider_health_score',
    'Provider health score (0-1)',
    ['provider']
)

# Calculate based on:
# - Availability: Is provider responding?
# - Error rate: % of failed requests
# - Latency: Average response time
# Score = (availability * 0.4) + ((1 - error_rate) * 0.3) + (latency_score * 0.3)
```

---

#### `provider_availability{provider}`
- **Type:** Gauge (0 or 1)
- **Labels:** `provider`
- **Description:** Provider availability status (1=available, 0=down)
- **Note:** Metric is defined but has no data
- **Used in:** Provider monitoring dashboards

**Implementation Suggestion:**
```python
from prometheus_client import Gauge

provider_availability = Gauge(
    'provider_availability',
    'Provider availability status (1=available, 0=unavailable)',
    ['provider']
)

# Update during health checks:
# provider_availability.labels(provider="openrouter").set(1)  # Available
# provider_availability.labels(provider="cerebras").set(0)    # Down
```

---

#### `provider_error_rate{provider}`
- **Type:** Gauge (0.0 - 1.0)
- **Labels:** `provider`
- **Description:** Provider error rate (percentage of failed requests)
- **Note:** Metric is defined but has no data

**Implementation Suggestion:**
```python
# Calculate from existing model_inference_requests_total:
# error_rate = failed_requests / total_requests (last 5 minutes)

provider_error_rate = Gauge(
    'provider_error_rate',
    'Provider error rate (0-1)',
    ['provider']
)

# Update periodically (every 30 seconds):
# Calculate error rate from model_inference_requests_total{status!="success"}
```

---

#### `provider_response_time_seconds{provider}`
- **Type:** Histogram
- **Labels:** `provider`
- **Description:** Provider response time in seconds
- **Note:** Metric is defined but has no data

**Implementation Suggestion:**
```python
from prometheus_client import Histogram

provider_response_time = Histogram(
    'provider_response_time_seconds',
    'Provider response time in seconds',
    ['provider'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Record during each provider API call:
# with provider_response_time.labels(provider="openrouter").time():
#     response = await call_provider_api()
```

---

### 2. Circuit Breaker Metrics

#### `gatewayz_circuit_breaker_state{provider, state}`
- **Type:** Gauge
- **Labels:** `provider`, `state` (values: "open", "closed", "half_open")
- **Description:** Circuit breaker state for each provider
- **Used in:** gatewayz-application-health.json (Panel ID 4)

**Implementation Suggestion:**
```python
from prometheus_client import Gauge

circuit_breaker_state = Gauge(
    'gatewayz_circuit_breaker_state',
    'Circuit breaker state (1=in this state, 0=not)',
    ['provider', 'state']
)

# Update when circuit breaker state changes:
# circuit_breaker_state.labels(provider="openrouter", state="closed").set(1)
# circuit_breaker_state.labels(provider="openrouter", state="open").set(0)
# circuit_breaker_state.labels(provider="openrouter", state="half_open").set(0)
```

---

### 3. Model Uptime Metrics

#### `gatewayz_model_uptime_24h{model}`
- **Type:** Gauge (0.0 - 1.0)
- **Labels:** `model`
- **Description:** Model uptime percentage over last 24 hours
- **Used in:** gatewayz-application-health.json (Panel ID 9)

**Implementation Suggestion:**
```python
from prometheus_client import Gauge

model_uptime_24h = Gauge(
    'gatewayz_model_uptime_24h',
    'Model uptime over last 24 hours (0-1)',
    ['model']
)

# Calculate from successful vs failed requests in last 24h:
# uptime = successful_requests / total_requests (last 24h)
# Update every 5 minutes
```

---

### 4. Cost Tracking Metrics

#### `gatewayz_cost_by_provider{provider}`
- **Type:** Counter
- **Labels:** `provider`
- **Description:** Total cost incurred by provider (in USD)
- **Used in:** gatewayz-application-health.json (Panel ID 27)

**Implementation Suggestion:**
```python
from prometheus_client import Counter

cost_by_provider = Counter(
    'gatewayz_cost_by_provider',
    'Total cost by provider in USD',
    ['provider']
)

# Increment after each API call:
# cost = calculate_cost(tokens_used, model_pricing)
# cost_by_provider.labels(provider="openrouter").inc(cost)
```

---

### 5. Token Efficiency Metrics

#### `gatewayz_token_efficiency{model}`
- **Type:** Gauge
- **Labels:** `model`
- **Description:** Token efficiency score (output tokens / input tokens)
- **Used in:** gatewayz-application-health.json (Panel ID 28)

**Implementation Suggestion:**
```python
from prometheus_client import Gauge

token_efficiency = Gauge(
    'gatewayz_token_efficiency',
    'Token efficiency (output/input ratio)',
    ['model']
)

# Calculate periodically:
# efficiency = total_output_tokens / total_input_tokens (last hour)
# token_efficiency.labels(model="anthropic/claude-opus-4.5").set(efficiency)
```

---

### 6. Anomaly Detection Metrics

#### `gatewayz_detected_anomalies{type}`
- **Type:** Counter
- **Labels:** `type` (e.g., "latency_spike", "error_surge", "unusual_pattern")
- **Description:** Count of detected anomalies
- **Used in:** gatewayz-application-health.json (Panel ID 24)

**Implementation Suggestion:**
```python
from prometheus_client import Counter

detected_anomalies = Counter(
    'gatewayz_detected_anomalies',
    'Detected anomalies by type',
    ['type']
)

# Increment when anomaly detected:
# if latency > threshold * 3:
#     detected_anomalies.labels(type="latency_spike").inc()
```

---

## 🔄 Metrics That Can Be Calculated (No Backend Change Needed)

These metrics are queried in dashboards but can be calculated from existing metrics using PromQL:

### `gatewayz_error_rate`
**Current Query (Wrong):**
```promql
avg(gatewayz_error_rate)
```

**Should Use:**
```promql
sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) /
sum(rate(fastapi_requests_total[5m]))
```

### `gatewayz_model_error_rate{model}`
**Current Query (Wrong):**
```promql
gatewayz_model_error_rate
```

**Should Use:**
```promql
sum(rate(model_inference_requests_total{status!="success"}[5m])) by (model) /
sum(rate(model_inference_requests_total[5m])) by (model)
```

### `gatewayz_model_avg_response_time_ms{model}`
**Current Query (Wrong):**
```promql
gatewayz_model_avg_response_time_ms
```

**Should Use:**
```promql
(
  rate(model_inference_duration_seconds_sum[5m]) /
  rate(model_inference_duration_seconds_count[5m])
) * 1000
```

---

## 📊 Model Health Dashboard - Token Usage Over Time

### Required Panel Configuration

**Panel Title:** Token Usage Over Time

**Metric:** Already exported as `tokens_used_total{model, provider}`

**Recommended PromQL Query:**
```promql
# Total tokens used per model over time (rate per minute)
sum(rate(tokens_used_total[5m])) by (model) * 60

# Or total cumulative tokens
sum(tokens_used_total) by (model)

# Token usage by provider
sum(rate(tokens_used_total[5m])) by (provider) * 60
```

**Panel Type:** Time series graph

**Y-Axis:** Tokens per minute (or cumulative total)

**Legend:** `{{model}}` or `{{provider}}`

---

## 📋 Implementation Priority

### High Priority (Dashboard Currently Broken)
1. `provider_availability` - Enable existing defined metric
2. `provider_error_rate` - Enable existing defined metric
3. `provider_response_time_seconds` - Enable existing defined metric
4. `gatewayz_provider_health_score` - For overall health monitoring

### Medium Priority (Nice to Have)
5. `gatewayz_circuit_breaker_state` - For reliability monitoring
6. `gatewayz_model_uptime_24h` - For SLA tracking
7. `gatewayz_cost_by_provider` - For cost optimization

### Low Priority (Future Enhancement)
8. `gatewayz_token_efficiency` - For efficiency analysis
9. `gatewayz_detected_anomalies` - For advanced monitoring

---

## 🔧 Dashboard Query Fixes (No Backend Changes)

These dashboard panels can be fixed by updating queries to use existing metrics:

1. **Overall Error Rate** - Use calculation from `fastapi_requests_total`
2. **Model Error Rates** - Use calculation from `model_inference_requests_total`
3. **Average Response Time** - Use histogram calculation
4. **Latency Percentiles** - Fix histogram_quantile usage

---

## 📝 Notes for Backend Agent

### Provider Metrics Implementation
The three provider metrics (`provider_availability`, `provider_error_rate`, `provider_response_time_seconds`) are already defined in your metrics endpoint but have no data. You need to:

1. Implement a background task that runs every 30-60 seconds
2. For each provider in your system:
   - Check if provider is responding (health check) → Update `provider_availability`
   - Calculate error rate from recent requests → Update `provider_error_rate`
   - Calculate average response time → Update `provider_response_time_seconds`

### Recommended Implementation Location
Add provider health monitoring in your existing provider management code, likely in:
- `app/services/provider_health_checker.py` (new file)
- Called from background tasks or scheduled jobs

### Example Provider Health Check Task
```python
import asyncio
from prometheus_client import Gauge

provider_availability = Gauge('provider_availability', 'Provider availability', ['provider'])
provider_error_rate = Gauge('provider_error_rate', 'Provider error rate', ['provider'])

async def monitor_provider_health():
    while True:
        for provider in get_all_providers():
            # Check availability
            is_available = await check_provider_health(provider.name)
            provider_availability.labels(provider=provider.name).set(1 if is_available else 0)

            # Calculate error rate (from last 5 minutes of requests)
            error_rate = calculate_provider_error_rate(provider.name, window="5m")
            provider_error_rate.labels(provider=provider.name).set(error_rate)

        await asyncio.sleep(30)  # Run every 30 seconds
```

---

## Questions for Clarification

1. **Redis Metrics**: Do you want to monitor:
   - Redis exporter metrics (memory, connections, commands/sec)?
   - Or your application's Redis usage (cache hit rate, operation latency)?
   - Currently the redis-exporter is configured but not being queried effectively

2. **Aggregative Format Endpoint**: You mentioned providing an endpoint once everything is accurate. What aggregated data should this endpoint provide?
   - Summary statistics (total requests, tokens, costs)?
   - Time-series data in a specific format?
   - Provider/model rankings?
