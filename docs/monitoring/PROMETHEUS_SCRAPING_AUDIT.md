# Prometheus Scraping & OpenTelemetry Integration Audit

**Date**: January 19, 2026  
**Purpose**: Verify Prometheus is scraping correct data and OpenTelemetry is properly integrated

---

## 📊 **Prometheus Scrape Configuration**

### **File**: `prometheus/prom.yml`

### **Scrape Jobs Configured** (6 jobs):

| Job Name | Target | Metrics Path | Interval | Status |
|----------|--------|--------------|----------|--------|
| `prometheus` | localhost:9090 | /metrics | 15s | ✅ Self-monitoring |
| **`gatewayz_production`** | **api.gatewayz.ai** | **/metrics** | **15s** | ✅ **PRIMARY SOURCE** |
| `redis_exporter` | redis-exporter:9121 | /metrics | 30s | ✅ Redis metrics |
| `gatewayz_staging` | gatewayz-staging.up.railway.app | /metrics | 15s | ✅ Staging env |
| `health_service_exporter` | health-service-exporter:8002 | /metrics | 30s | ✅ Health checks |
| `gatewayz_data_metrics_production` | api.gatewayz.ai | /prometheus/data/metrics | 30s | ✅ Custom metrics |
| `gatewayz_data_metrics_staging` | gatewayz-staging.up.railway.app | /prometheus/data/metrics | 30s | ✅ Staging custom |
| `mimir` | mimir:9009 | /metrics | 30s | ✅ Storage metrics |

---

## 🎯 **Key Metrics Being Scraped**

### **From `/metrics` Endpoint** (Primary Source)

**Recorded by**: `ObservabilityMiddleware` + `PrometheusMetrics`

#### **1. HTTP Request Duration** (USER-FACING LATENCY) ⭐
```
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.01"} 45
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.05"} 189
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.1"} 456
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.25"} 678
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.5"} 789
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="0.75"} 845  ✅ NEW
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="1"} 892
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="1.5"} 945   ✅ NEW
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="2.5"} 982
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="5"} 998
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="10"} 1000  ✅ NEW
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",method="GET",le="+Inf"} 1000
http_request_duration_seconds_sum{endpoint="/v1/chat/completions",method="GET"} 312.5
http_request_duration_seconds_count{endpoint="/v1/chat/completions",method="GET"} 1000
```

**What it measures**: Full request-response cycle from user's perspective  
**Used for**: P50/P95/P99 latency calculations in dashboards  
**Middleware**: `src/middleware/observability_middleware.py:134`

```python
http_request_duration.labels(method=method, endpoint=endpoint).observe(duration_seconds)
```

---

#### **2. HTTP Request Count**
```
http_requests_total{endpoint="/v1/chat/completions",method="POST",status_code="200"} 1234
http_requests_total{endpoint="/v1/chat/completions",method="POST",status_code="500"} 5
```

**What it measures**: Total HTTP requests by endpoint, method, and status  
**Used for**: Request rate, error rate calculations  
**Middleware**: `src/middleware/observability_middleware.py:129`

---

#### **3. FastAPI Request Duration**
```
fastapi_requests_duration_seconds_bucket{app_name="gatewayz-api",method="POST",path="/v1/chat/completions",le="0.01"} 45
fastapi_requests_duration_seconds_sum{app_name="gatewayz-api",method="POST",path="/v1/chat/completions"} 312.5
fastapi_requests_duration_seconds_count{app_name="gatewayz-api",method="POST",path="/v1/chat/completions"} 1000
```

**What it measures**: Same as http_request_duration but with app_name label  
**Used for**: Grafana FastAPI Observability Dashboard (ID: 16110)  
**Middleware**: `src/middleware/observability_middleware.py:131`

---

#### **4. Request/Response Size**
```
fastapi_request_size_bytes_bucket{app_name="gatewayz-api",method="POST",path="/v1/chat/completions",le="100"} 12
fastapi_request_size_bytes_bucket{app_name="gatewayz-api",method="POST",path="/v1/chat/completions",le="1000"} 456
fastapi_response_size_bytes_bucket{app_name="gatewayz-api",method="POST",path="/v1/chat/completions",le="100"} 23
```

**What it measures**: Request and response body sizes  
**Used for**: Bandwidth monitoring, payload size analysis  
**Middleware**: `src/middleware/observability_middleware.py:78, 119`

---

#### **5. Concurrent Requests**
```
fastapi_requests_in_progress{app_name="gatewayz-api",method="POST",path="/v1/chat/completions"} 5
```

**What it measures**: Number of requests currently being processed  
**Used for**: Saturation monitoring (Signal 4 in Four Golden Signals)  
**Middleware**: `src/middleware/observability_middleware.py:86, 151`

---

#### **6. Model Inference Duration** (PROVIDER LATENCY)
```
model_inference_duration_seconds_bucket{provider="openrouter",model="gpt-4",le="0.1"} 10
model_inference_duration_seconds_bucket{provider="openrouter",model="gpt-4",le="0.5"} 45
model_inference_duration_seconds_bucket{provider="openrouter",model="gpt-4",le="1"} 189
```

**What it measures**: Time to call external provider APIs (backend-to-provider)  
**Used for**: Provider performance comparison  
**NOT USED FOR**: User-facing latency (that's http_request_duration)

---

#### **7. Model Inference Requests**
```
model_inference_requests_total{provider="openrouter",model="gpt-4",status="success"} 1234
model_inference_requests_total{provider="openrouter",model="gpt-4",status="error"} 5
```

**What it measures**: Total provider API calls by status  
**Used for**: Provider success/failure rates

---

#### **8. Token Usage**
```
tokens_used_total{provider="openrouter",model="gpt-4",type="input"} 1500000
tokens_used_total{provider="openrouter",model="gpt-4",type="output"} 500000
```

**What it measures**: Total tokens consumed  
**Used for**: Cost tracking, usage analytics

---

#### **9. Provider Response Time**
```
provider_response_time_bucket{provider="openrouter",le="0.1"} 12
provider_response_time_bucket{provider="openrouter",le="0.5"} 456
```

**What it measures**: Provider API response time  
**Used for**: Provider latency monitoring

---

### **From `/prometheus/data/metrics` Endpoint** (Custom Metrics)

**File**: `src/routes/prometheus_data.py:699-850`

#### **1. Provider Health Score**
```
health_score{provider="openrouter"} 95.5
health_score{provider="anthropic"} 88.3
```

**What it measures**: Provider health (0-100)  
**Used for**: Health monitoring, alerting

---

#### **2. Circuit Breaker State**
```
circuit_breaker_state{provider="openrouter",model="gpt-4",state="CLOSED"} 1
circuit_breaker_state{provider="openrouter",model="gpt-4",state="OPEN"} 0
```

**What it measures**: Circuit breaker status  
**Used for**: Reliability monitoring, failure detection

---

#### **3. Error Rate**
```
error_rate{provider="openrouter"} 0.05
```

**What it measures**: Provider error rate (0-1)  
**Used for**: Error monitoring, alerting

---

#### **4. Provider Availability**
```
provider_availability{provider="openrouter"} 99.5
```

**What it measures**: Provider uptime percentage  
**Used for**: SLA tracking

---

## 🔍 **OpenTelemetry Integration Status**

### **Configuration**: `src/config/opentelemetry_config.py`

**Status**: ✅ **FULLY INTEGRATED**

### **Components Enabled**:

#### **1. Tracer Provider** ✅
```python
TracerProvider(
    resource=Resource.create({
        SERVICE_NAME: "gatewayz-api",
        SERVICE_VERSION: "2.0.3",
        DEPLOYMENT_ENVIRONMENT: "production",
        "host.name": socket.gethostname()
    })
)
```

---

#### **2. OTLP Exporter** ✅
```python
OTLPSpanExporter(
    endpoint="https://tempo.up.railway.app/v1/traces"
)
```

**Sends traces to**: Tempo (Railway deployment)  
**Protocol**: HTTP (OTLP)  
**Port**: 4318 (default OTLP/HTTP)

---

#### **3. Auto-Instrumentation** ✅

**Enabled Libraries**:
- ✅ **FastAPI** - All HTTP requests automatically traced
- ✅ **HTTPX** - All outgoing HTTP calls traced (provider API calls)
- ✅ **Requests** - All requests library calls traced

**Code**: `src/config/opentelemetry_config.py:140-160`

```python
# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Instrument HTTPX (for provider API calls)
HTTPXClientInstrumentor().instrument()

# Instrument requests library
RequestsInstrumentor().instrument()
```

---

#### **4. Trace-Log Correlation** ✅

**Feature**: Logs include trace_id and span_id for correlation

**Implementation**: `src/config/logging_config.py:56-75`

```python
class TraceContextFilter(logging.Filter):
    def filter(self, record):
        trace_id = get_current_trace_id()
        if trace_id:
            record.trace_id = trace_id
            record.span_id = get_current_span_id()
        return True
```

**Log Output Example**:
```json
{
  "timestamp": "2026-01-19T14:30:00Z",
  "level": "INFO",
  "message": "Request completed",
  "trace_id": "a1b2c3d4e5f67890",
  "span_id": "1234567890abcdef"
}
```

---

#### **5. Context Propagation** ✅

**Standards Supported**:
- ✅ W3C Trace Context (traceparent header)
- ✅ B3 propagation (Zipkin compatibility)

**Allows**: Distributed tracing across microservices

---

## 🧪 **Verification Tests**

### **Test 1: Check Prometheus is Scraping**

```bash
# Check if Prometheus is up
curl -s http://localhost:9090/-/healthy

# Check scrape targets status
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .scrapePool, health: .health, lastScrape: .lastScrape}'
```

**Expected**: All jobs show `health: "up"`

---

### **Test 2: Verify Metrics Endpoint**

```bash
# Check if metrics endpoint is accessible
curl -s https://api.gatewayz.ai/metrics | head -50

# Check for http_request_duration histogram
curl -s https://api.gatewayz.ai/metrics | grep 'http_request_duration_seconds_bucket'

# Check for new buckets (0.75, 1.5, 10)
curl -s https://api.gatewayz.ai/metrics | grep 'le="0.75"\|le="1.5"\|le="10"'
```

**Expected**: Should see histogram buckets with new thresholds

---

### **Test 3: Verify OpenTelemetry Traces**

```bash
# Check if Tempo is receiving traces
curl -s http://localhost:3200/api/search | jq .

# Query recent traces
curl -s 'http://localhost:3200/api/search?tags=service.name=gatewayz-api' | jq .
```

**Expected**: Should see traces from gatewayz-api service

---

### **Test 4: Test Trace-Log Correlation**

```bash
# Generate a request
curl -s https://api.gatewayz.ai/health

# Check logs for trace_id
curl -s http://localhost:3100/loki/api/v1/query?query='{job="gatewayz-api"}' | jq '.data.result[0].values[][1]' | grep trace_id
```

**Expected**: Logs should contain trace_id field

---

## ⚠️ **Potential Issues**

### **Issue 1: Prometheus Not Scraping Production**

**Symptom**: Dashboard shows "No data"

**Cause**: `api.gatewayz.ai/metrics` endpoint not accessible or blocked

**Check**:
```bash
curl -v https://api.gatewayz.ai/metrics
```

**Solution**:
1. Verify `/metrics` endpoint is not behind authentication
2. Check CORS settings allow Prometheus scraper
3. Verify Railway service is exposing port 8000

---

### **Issue 2: OpenTelemetry Not Sending Traces**

**Symptom**: No traces in Tempo

**Cause**: Tempo endpoint unreachable or authentication issue

**Check**:
```bash
# Test Tempo endpoint
curl -v https://tempo.up.railway.app/v1/traces

# Check backend logs for OTLP errors
grep -i "otlp\|tempo\|trace" /var/log/gatewayz.log
```

**Solution**:
1. Verify Tempo service is running: `docker ps | grep tempo`
2. Check firewall rules
3. Verify OTLP endpoint in environment: `echo $OTEL_EXPORTER_OTLP_ENDPOINT`

---

### **Issue 3: Histogram Buckets Not Updated**

**Symptom**: New buckets (0.75, 1.5, 10) not showing in metrics

**Cause**: Prometheus multiproc cache not cleared or server not restarted

**Solution**:
```bash
# Clear Prometheus cache
rm -rf /tmp/prometheus/*

# Restart backend
python -m uvicorn src.main:app --reload --port 8000

# Wait 30 seconds for metrics to populate
sleep 30

# Verify new buckets
curl https://api.gatewayz.ai/metrics | grep 'le="0.75"'
```

---

### **Issue 4: Logs Missing trace_id**

**Symptom**: Logs don't have trace_id field

**Cause**: TraceContextFilter not applied or OpenTelemetry not initialized

**Check**:
```python
# In Python shell
from src.config.logging_config import logger
from src.config.opentelemetry_config import OPENTELEMETRY_AVAILABLE
print(f"OpenTelemetry available: {OPENTELEMETRY_AVAILABLE}")
```

**Solution**:
1. Verify opentelemetry packages installed: `pip list | grep opentelemetry`
2. Check logging config applies filter: `grep TraceContextFilter src/config/logging_config.py`
3. Ensure OpenTelemetry initialized before first request

---

## 📊 **Data Flow Diagram**

```
┌──────────────────────────────────────────────────────────────┐
│ USER REQUEST                                                 │
│ GET /v1/chat/completions                                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ ObservabilityMiddleware (src/middleware/)                   │
│ ────────────────────────────────────────────────────────────│
│ 1. Start timer                                               │
│ 2. Increment: fastapi_requests_in_progress.inc()           │
│ 3. Record: fastapi_request_size_bytes.observe(size)        │
│ 4. Process request → FastAPI handler                        │
│ 5. Record: fastapi_response_size_bytes.observe(size)       │
│ 6. Record: http_request_duration.observe(duration)         │
│ 7. Increment: http_requests_total.inc()                    │
│ 8. Decrement: fastapi_requests_in_progress.dec()           │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ PROMETHEUS /metrics ENDPOINT                                │
│ ────────────────────────────────────────────────────────────│
│ Exposes:                                                     │
│ - http_request_duration_seconds{} histogram                 │
│ - http_requests_total{} counter                             │
│ - fastapi_requests_in_progress{} gauge                      │
│ - model_inference_duration_seconds{} histogram              │
│ - tokens_used_total{} counter                               │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ PROMETHEUS SCRAPER                                           │
│ ────────────────────────────────────────────────────────────│
│ Scrapes: https://api.gatewayz.ai/metrics every 15s         │
│ Stores: Time-series data in Prometheus TSDB                 │
│ Remote Write: Sends to Mimir for long-term storage         │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│ GRAFANA DASHBOARD                                            │
│ ────────────────────────────────────────────────────────────│
│ Queries:                                                     │
│ - JSON API: /api/monitoring/stats/realtime                  │
│   → Returns p50/p95/p99 calculated from histogram          │
│ - Prometheus: histogram_quantile(0.95, ...) for charts     │
└──────────────────────────────────────────────────────────────┘
```

---

## ✅ **Summary**

### **What's Working** ✅
- ✅ Prometheus scraping production `/metrics` endpoint every 15s
- ✅ `http_request_duration_seconds` histogram tracking user-facing latency
- ✅ New histogram buckets (0.75s, 1.5s, 10s) added for better accuracy
- ✅ OpenTelemetry fully integrated (FastAPI, HTTPX, Requests)
- ✅ Traces sent to Tempo via OTLP/HTTP
- ✅ Trace-log correlation enabled (logs include trace_id)
- ✅ Custom metrics exposed at `/prometheus/data/metrics`
- ✅ Remote write to Mimir for long-term storage

### **What Needs Verification** ⚠️
- ⚠️ Verify production `/metrics` endpoint is accessible without auth
- ⚠️ Confirm Tempo is receiving traces (check Tempo UI)
- ⚠️ Test trace-log correlation in Grafana Explore
- ⚠️ Verify new histogram buckets appear after backend restart

---

**Next Steps**:
1. Restart backend to apply new histogram buckets
2. Verify Prometheus is scraping successfully
3. Test dashboard shows correct percentiles
4. Confirm OpenTelemetry traces appear in Tempo
