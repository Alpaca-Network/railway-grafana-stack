# FastAPI Dashboard - Complete Implementation Guide

## What You Asked For

You need to link Loki, Tempo, and Prometheus to Grafana for visualization of 8 FastAPI dashboard panels:

1. **Total Requests** - Current request rate
2. **Requests Per Minute** - RPM trend
3. **Errors Per Second** - Error rate with alerts
4. **Average Response Time** - Mean latency
5. **Request Duration P60** - 60th percentile latency
6. **CPU Usage** - Process CPU percentage
7. **Memory Usage** - Process memory usage
8. **Logger Stream** - Real-time logs

---

## What Your Backend Agent Needs to Implement

### 1. Prometheus Metrics (Expose `/metrics` endpoint)

**Two metrics required:**

```python
# Metric 1: Request Counter
fastapi_requests_total{method="GET", path="/api/users", status_code="200"} 100

# Metric 2: Request Duration Histogram
fastapi_request_duration_seconds_bucket{method="GET", path="/api/users", status_code="200", le="0.1"} 95
fastapi_request_duration_seconds_bucket{method="GET", path="/api/users", status_code="200", le="0.5"} 99
fastapi_request_duration_seconds_sum{method="GET", path="/api/users", status_code="200"} 25.5
fastapi_request_duration_seconds_count{method="GET", path="/api/users", status_code="200"} 100
```

**Implementation:**
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

---

### 2. Loki Logs (Structured JSON to STDOUT)

**Log format:**
```json
{
  "timestamp": "2025-12-18T01:23:45.123Z",
  "level": "INFO",
  "service": "fastapi-backend",
  "endpoint": "/api/users",
  "method": "GET",
  "status_code": 200,
  "duration_ms": 45,
  "message": "Request completed"
}
```

**Implementation:**
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

---

### 3. Tempo Traces (OpenTelemetry to gRPC)

**Send traces to Tempo at `localhost:4317`**

**Implementation:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI

app = FastAPI()

otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
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

---

## How Grafana Links Everything

### Data Flow Diagram

```
FastAPI Backend
    ↓
    ├─→ /metrics endpoint (Prometheus format)
    │       ↓
    │   Prometheus scrapes every 15s
    │       ↓
    │   Grafana queries Prometheus
    │       ↓
    │   Panels: Total Requests, RPM, Errors/s, Avg Response Time, P60, CPU, Memory
    │
    ├─→ STDOUT JSON logs
    │       ↓
    │   Loki ingests logs
    │       ↓
    │   Grafana queries Loki
    │       ↓
    │   Panel: Logger Stream
    │
    └─→ OpenTelemetry traces (gRPC to Tempo)
            ↓
        Tempo stores traces
            ↓
        Grafana queries Tempo
            ↓
        Panel: Trace Search (optional)
```

---

## Grafana Dashboard Panels Configuration

### Panel 1: Total Requests
```json
{
  "title": "Total Requests",
  "type": "stat",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "sum(rate(fastapi_requests_total[5m]))"
    }
  ],
  "unit": "reqps"
}
```

### Panel 2: Requests Per Minute
```json
{
  "title": "Requests Per Minute",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total[1m]) * 60",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "unit": "short"
}
```

### Panel 3: Errors Per Second
```json
{
  "title": "Errors Per Second",
  "type": "stat",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total{status_code=~\"4..|5..\"}[1s])"
    }
  ],
  "unit": "short",
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 1},
      {"color": "red", "value": 5}
    ]
  }
}
```

### Panel 4: Average Response Time
```json
{
  "title": "Average Response Time",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "unit": "s"
}
```

### Panel 5: Request Duration P60
```json
{
  "title": "Request Duration P60",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))",
      "legendFormat": "P60 {{method}} {{path}}"
    }
  ],
  "unit": "s"
}
```

### Panel 6: CPU Usage
```json
{
  "title": "CPU Usage",
  "type": "gauge",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "rate(process_cpu_seconds_total[5m]) * 100"
    }
  ],
  "unit": "percent",
  "min": 0,
  "max": 100,
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 50},
      {"color": "red", "value": 80}
    ]
  }
}
```

### Panel 7: Memory Usage
```json
{
  "title": "Memory Usage",
  "type": "gauge",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "process_resident_memory_bytes / 1024 / 1024"
    }
  ],
  "unit": "decbytes",
  "thresholds": {
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 512},
      {"color": "red", "value": 1024}
    ]
  }
}
```

### Panel 8: Logger Stream
```json
{
  "title": "Logger Stream",
  "type": "logs",
  "datasource": "Loki",
  "targets": [
    {
      "expr": "{service=\"fastapi-backend\"}"
    }
  ],
  "options": {
    "showLabels": ["level", "endpoint", "status_code"],
    "showTime": true
  }
}
```

---

## Complete FastAPI Application (Copy-Paste Ready)

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

# ========== PROMETHEUS ==========
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

# ========== LOKI ==========
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ========== TEMPO ==========
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
    
    # Loki
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

## Installation & Deployment

### requirements.txt
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

### Run Locally
```bash
pip install -r requirements.txt
python main.py
```

### Test
```bash
# Generate traffic
for i in {1..100}; do curl http://localhost:8000/api/users/1; done

# Check metrics
curl http://localhost:8000/metrics | grep fastapi_requests_total

# Check Grafana
# Open http://localhost:3000 → FastAPI Dashboard
```

### Deploy to Railway
1. Push code to repository
2. Railway auto-detects FastAPI
3. Set environment: `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317`
4. Verify metrics: `https://your-app.railway.app/metrics`

---

## What You Provide to Backend Agent

**Tell them:**

"Implement these three things in FastAPI:

1. **Prometheus Metrics** - Expose `/metrics` endpoint with:
   - `fastapi_requests_total` counter (labels: method, path, status_code)
   - `fastapi_request_duration_seconds` histogram (labels: method, path, status_code)

2. **Structured JSON Logs** - Output to STDOUT with:
   - timestamp, level, service, endpoint, method, status_code, duration_ms

3. **OpenTelemetry Traces** - Send to Tempo gRPC at localhost:4317 with:
   - Auto-instrumented FastAPI
   - Manual spans for important operations

Use the complete FastAPI application code in FASTAPI_DASHBOARD_COMPLETE.md as reference."

---

## Files in Repository

1. **FASTAPI_DASHBOARD_INSTRUMENTATION.md** - Detailed technical guide (761 lines)
2. **BACKEND_INSTRUMENTATION_REQUIREMENTS.md** - Complete specifications (597 lines)
3. **BACKEND_AGENT_INSTRUCTIONS.md** - Quick-start guide (407 lines)
4. **FASTAPI_DASHBOARD_SUMMARY.md** - Overview for backend agent (431 lines)
5. **grafana/dashboards/fastapi-dashboard.json** - Pre-configured dashboard

---

## Result

Once your backend implements this:

✅ Prometheus scrapes metrics every 15 seconds
✅ Loki ingests logs in real-time
✅ Tempo collects distributed traces
✅ Grafana displays 8 live panels
✅ All metrics, logs, and traces linked together

**Time to implement:** ~30 minutes
