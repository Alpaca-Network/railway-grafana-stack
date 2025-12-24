# Instructions for Backend Agent: FastAPI Instrumentation

## Quick Summary

Implement three types of observability in your FastAPI backend:

1. **Prometheus Metrics** - Expose `/metrics` endpoint
2. **Structured JSON Logs** - Output logs to STDOUT
3. **OpenTelemetry Traces** - Send traces to Tempo

This will enable the FastAPI Dashboard in Grafana to display:
- Total Requests
- Requests Per Minute
- Errors Per Second
- Average Response Time
- Request Duration P60
- CPU Usage
- Memory Usage
- Logger Stream

---

## What Exactly to Implement

### 1. Prometheus Metrics (2 metrics required)

**Metric 1: Request Counter**
```python
from prometheus_client import Counter

requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)
```

**Metric 2: Request Duration Histogram**
```python
from prometheus_client import Histogram

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)
```

**Middleware to Track Requests:**
```python
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
```

**Metrics Endpoint:**
```python
from prometheus_client import generate_latest

@app.get("/metrics")
async def metrics():
    return generate_latest()
```

**Install:** `pip install prometheus-client`

---

### 2. Structured JSON Logging

**Log Format (what to output):**
```json
{
  "timestamp": "2025-12-18T01:23:45.123Z",
  "level": "INFO",
  "service": "fastapi-backend",
  "endpoint": "/api/users",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45,
  "message": "Request completed successfully"
}
```

**Middleware to Log Requests:**
```python
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
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

### 3. OpenTelemetry Traces

**Setup Tracer:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure OTLP exporter (send to Tempo)
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",  # Tempo gRPC endpoint
    insecure=True
)

trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)
```

**Manual Span Example:**
```python
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("endpoint", "/api/users/{user_id}")
        # Your logic here
        return {"id": user_id, "name": "John"}
```

**Install:**
```bash
pip install opentelemetry-api
pip install opentelemetry-sdk
pip install opentelemetry-exporter-otlp
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-requests
```

---

## Complete Working Example

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

app = FastAPI()

# ============ PROMETHEUS ============
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

# ============ LOGGING ============
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ============ TRACING ============
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

# ============ MIDDLEWARE ============
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    duration_ms = duration * 1000
    
    # Prometheus
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
    
    # Logging
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

# ============ ENDPOINTS ============
@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        return {"id": user_id, "name": "John"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Installation

```bash
pip install fastapi uvicorn prometheus-client python-json-logger \
  opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests
```

Or use requirements.txt:
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

## Testing

### Test Prometheus Metrics
```bash
curl http://localhost:8000/metrics | grep fastapi_requests_total
```

Expected output:
```
fastapi_requests_total{method="GET",path="/api/users/1",status_code="200"} 1.0
```

### Test JSON Logs
```bash
curl http://localhost:8000/api/users/1
# Check your application logs - should see JSON output
```

Expected log output:
```json
{"timestamp": "2025-12-18T01:23:45.123Z", "level": "INFO", "service": "fastapi-backend", "endpoint": "/api/users/1", "method": "GET", "status_code": 200, "duration_ms": 45, "message": "Request completed"}
```

### Test Traces
```bash
# Make requests
for i in {1..10}; do curl http://localhost:8000/api/users/1; done

# Check Tempo
curl http://localhost:3200/api/traces
```

---

## Grafana Dashboard

Once implemented, the FastAPI Dashboard will automatically show:

| Panel | Data Source | Query |
|-------|-------------|-------|
| Total Requests | Prometheus | `sum(rate(fastapi_requests_total[5m]))` |
| Requests Per Minute | Prometheus | `rate(fastapi_requests_total[1m]) * 60` |
| Errors Per Second | Prometheus | `rate(fastapi_requests_total{status_code=~"4\.\|5\."}[1s])` |
| Average Response Time | Prometheus | `rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])` |
| Request Duration P60 | Prometheus | `histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))` |
| CPU Usage | Prometheus | `rate(process_cpu_seconds_total[5m]) * 100` |
| Memory Usage | Prometheus | `process_resident_memory_bytes / 1024 / 1024` |
| Logger Stream | Loki | `{service="fastapi-backend"}` |

---

## Deployment to Railway

1. Add instrumentation code to your FastAPI backend
2. Update requirements.txt with dependencies
3. Deploy to Railway
4. Set environment variable: `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317`
5. Verify metrics endpoint: `https://your-app.railway.app/metrics`
6. Check Grafana dashboard for live data

---

## Troubleshooting

**Issue: No metrics appearing**
- Verify `/metrics` endpoint is accessible
- Check Prometheus is scraping: `http://localhost:9090/targets`
- Make requests to generate metrics: `for i in {1..100}; do curl http://localhost:8000/api/users/1; done`

**Issue: No logs appearing**
- Check logs are JSON format in STDOUT
- Verify Loki is scraping logs
- Check service label is "fastapi-backend"

**Issue: No traces appearing**
- Verify Tempo endpoint is reachable: `curl http://localhost:4317`
- Check OTEL_EXPORTER_OTLP_ENDPOINT environment variable
- Verify opentelemetry packages are installed

---

## Summary

**What to do:**
1. Copy the complete example code above
2. Install dependencies: `pip install -r requirements.txt`
3. Run FastAPI app: `python main.py`
4. Make requests: `curl http://localhost:8000/api/users/1`
5. Verify metrics: `curl http://localhost:8000/metrics`
6. Check Grafana dashboard

**Time estimate:** 30 minutes

**Result:** FastAPI Dashboard with 8 live panels showing all metrics, logs, and traces
