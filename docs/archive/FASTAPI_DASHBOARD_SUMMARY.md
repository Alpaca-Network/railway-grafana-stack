# FastAPI Dashboard - Complete Summary for Backend Agent

## What You Asked For

You need 8 panels on the FastAPI Dashboard:
1. Total Requests
2. Requests Per Minute
3. Errors Per Second
4. Average Response Time
5. Request Duration P60
6. CPU Usage
7. Memory Usage
8. Logger Stream

---

## What Your Backend Agent Needs to Do

### Step 1: Expose Prometheus Metrics Endpoint

**Endpoint:** `GET /metrics`

**Returns:** Prometheus-formatted metrics

**Required Metrics:**

```
# Counter: Total HTTP requests
fastapi_requests_total{method="GET",path="/api/users/1",status_code="200"} 5.0

# Histogram: Request duration in seconds
fastapi_request_duration_seconds_bucket{method="GET",path="/api/users/1",status_code="200",le="0.01"} 2.0
fastapi_request_duration_seconds_bucket{method="GET",path="/api/users/1",status_code="200",le="0.025"} 3.0
fastapi_request_duration_seconds_bucket{method="GET",path="/api/users/1",status_code="200",le="0.05"} 4.0
...
fastapi_request_duration_seconds_sum{method="GET",path="/api/users/1",status_code="200"} 0.15
fastapi_request_duration_seconds_count{method="GET",path="/api/users/1",status_code="200"} 5.0
```

**Python Implementation:**
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI, Request
import time

app = FastAPI()

requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    requests_total.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

**Install:** `pip install prometheus-client`

---

### Step 2: Output Structured JSON Logs

**Format:** JSON to STDOUT

**Required Fields:**
- `timestamp` - ISO format timestamp
- `level` - INFO, ERROR, WARNING, DEBUG
- `service` - "fastapi-backend"
- `endpoint` - Request path
- `method` - HTTP method
- `status_code` - HTTP status code
- `duration_ms` - Request duration in milliseconds
- `message` - Log message

**Example Output:**
```json
{"timestamp": "2025-12-18T01:23:45.123Z", "level": "INFO", "service": "fastapi-backend", "endpoint": "/api/users/1", "method": "GET", "status_code": 200, "duration_ms": 45, "message": "Request completed"}
```

**Python Implementation:**
```python
import logging
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request
import time

app = FastAPI()

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    logger.info(
        "Request completed",
        extra={
            "service": "fastapi-backend",
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": int(duration_ms)
        }
    )
    
    return response
```

**Install:** `pip install python-json-logger`

---

### Step 3: Send OpenTelemetry Traces to Tempo

**Endpoint:** Tempo gRPC at `localhost:4317`

**Python Implementation:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI

app = FastAPI()

otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)

trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        return {"id": user_id, "name": "John"}
```

**Install:**
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests
```

---

## Complete Working FastAPI Application

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import logging
import time

app = FastAPI(title="FastAPI Backend")

# ========== PROMETHEUS METRICS ==========
requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ========== JSON LOGGING ==========
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ========== OPENTELEMETRY TRACING ==========
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

# ========== MIDDLEWARE ==========
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    duration_ms = duration * 1000
    
    # Prometheus metrics
    requests_total.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).observe(duration)
    
    # JSON logging
    logger.info(
        "Request completed",
        extra={
            "service": "fastapi-backend",
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": int(duration_ms)
        }
    )
    
    return response

# ========== ENDPOINTS ==========
@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        return {"id": user_id, "name": "John"}

@app.post("/api/users")
async def create_user(user_data: dict):
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("user_data", str(user_data))
        return {"id": 1, **user_data}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Requirements File

```
fastapi==0.104.1
uvicorn==0.24.0
prometheus-client==0.19.0
python-json-logger==2.0.7
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-requests==0.42b0
```

---

## How It Links to Grafana

### Prometheus Metrics → Grafana Panels

| Panel | PromQL Query | Metric |
|-------|--------------|--------|
| **Total Requests** | `sum(rate(fastapi_requests_total[5m]))` | `fastapi_requests_total` |
| **Requests Per Minute** | `rate(fastapi_requests_total[1m]) * 60` | `fastapi_requests_total` |
| **Errors Per Second** | `rate(fastapi_requests_total{status_code=~"4\.\|5\."}[1s])` | `fastapi_requests_total` |
| **Average Response Time** | `rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])` | `fastapi_request_duration_seconds` |
| **Request Duration P60** | `histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))` | `fastapi_request_duration_seconds_bucket` |
| **CPU Usage** | `rate(process_cpu_seconds_total[5m]) * 100` | `process_cpu_seconds_total` (auto-exposed) |
| **Memory Usage** | `process_resident_memory_bytes / 1024 / 1024` | `process_resident_memory_bytes` (auto-exposed) |

### Loki Logs → Grafana Panel

| Panel | LogQL Query |
|-------|------------|
| **Logger Stream** | `{service="fastapi-backend"}` |

### Tempo Traces → Grafana Panel

Traces are automatically ingested from OpenTelemetry and appear in Tempo dashboard.

---

## Testing Checklist

```bash
# 1. Test Prometheus metrics endpoint
curl http://localhost:8000/metrics | grep fastapi_requests_total

# 2. Generate traffic
for i in {1..100}; do
  curl http://localhost:8000/api/users/1
done

# 3. Check Prometheus scraped metrics
curl http://localhost:9090/api/v1/query?query=fastapi_requests_total

# 4. Check Loki ingested logs
curl http://localhost:3100/loki/api/v1/label

# 5. Check Tempo received traces
curl http://localhost:3200/api/traces

# 6. View Grafana dashboard
# Open http://localhost:3000 → FastAPI Dashboard
```

---

## Deployment Steps

1. **Create FastAPI app** with code above
2. **Create requirements.txt** with dependencies
3. **Run locally:**
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
4. **Verify metrics:**
   ```bash
   curl http://localhost:8000/metrics
   ```
5. **Deploy to Railway:**
   - Push code to repository
   - Railway automatically detects FastAPI
   - Set environment: `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317`
   - Verify metrics endpoint accessible

---

## What Grafana Will Show

Once your backend is instrumented:

1. **Total Requests** - Current request rate (requests/second)
2. **Requests Per Minute** - Trend line showing RPM over time
3. **Errors Per Second** - Red alert when errors spike
4. **Average Response Time** - Mean latency per endpoint
5. **Request Duration P60** - 60th percentile latency
6. **CPU Usage** - Process CPU percentage (0-100%)
7. **Memory Usage** - Process memory in MB
8. **Logger Stream** - Real-time logs with level, endpoint, status code

All panels update every 30 seconds with live data.

---

## Files You Need to Provide

1. `main.py` - FastAPI application with instrumentation
2. `requirements.txt` - Python dependencies
3. `Dockerfile` (optional) - For containerization

---

## Summary

**What to implement:**
- ✅ Prometheus `/metrics` endpoint with 2 metrics
- ✅ JSON structured logging to STDOUT
- ✅ OpenTelemetry traces to Tempo gRPC
- ✅ Middleware to auto-track all requests

**Time estimate:** 30 minutes

**Result:** FastAPI Dashboard with 8 live panels showing all metrics, logs, and traces

**Reference files in repository:**
- `FASTAPI_DASHBOARD_INSTRUMENTATION.md` - Detailed technical guide
- `BACKEND_INSTRUMENTATION_REQUIREMENTS.md` - Complete specifications
- `BACKEND_AGENT_INSTRUCTIONS.md` - Quick-start guide
- `grafana/dashboards/fastapi-dashboard.json` - Pre-configured dashboard
