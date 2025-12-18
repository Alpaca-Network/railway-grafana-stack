# FastAPI Dashboard - Ready for Backend Implementation

## Summary

You asked: "What exactly do you need from the other agent for the FastAPI Dashboard with 8 panels (total requests, RPM, errors/s, avg response time, P60, CPU usage, memory usage, logger stream)?"

**Answer:** Your backend agent needs to implement three things:

1. **Prometheus `/metrics` endpoint** - Expose 2 metrics
2. **Structured JSON logs** - Output to STDOUT
3. **OpenTelemetry traces** - Send to Tempo gRPC

---

## What to Tell Your Backend Agent

### Copy this exact instruction:

"Implement FastAPI instrumentation with three observability components:

**1. Prometheus Metrics Endpoint (`/metrics`)**

Expose two metrics:
- `fastapi_requests_total` (Counter) - labels: method, path, status_code
- `fastapi_request_duration_seconds` (Histogram) - labels: method, path, status_code

**2. Structured JSON Logging**

Output JSON logs to STDOUT with fields:
- timestamp (ISO format)
- level (INFO, ERROR, WARNING, DEBUG)
- service: "fastapi-backend"
- endpoint (request path)
- method (HTTP method)
- status_code
- duration_ms
- message

**3. OpenTelemetry Traces**

Send traces to Tempo gRPC endpoint at localhost:4317 with:
- Auto-instrumented FastAPI
- Manual spans for important operations

**Reference:** See FASTAPI_DASHBOARD_COMPLETE.md for complete working code example."

---

## Exact Code to Provide

Here's the complete FastAPI application your backend agent should implement:

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

# PROMETHEUS METRICS
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

# JSON LOGGING
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# OPENTELEMETRY TRACING
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)

# MIDDLEWARE
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

# ENDPOINTS
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

## Dependencies (requirements.txt)

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

| Panel | PromQL Query | Data Source |
|-------|--------------|-------------|
| Total Requests | `sum(rate(fastapi_requests_total[5m]))` | Prometheus |
| Requests Per Minute | `rate(fastapi_requests_total[1m]) * 60` | Prometheus |
| Errors Per Second | `rate(fastapi_requests_total{status_code=~"4\.\|5\."}[1s])` | Prometheus |
| Average Response Time | `rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])` | Prometheus |
| Request Duration P60 | `histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))` | Prometheus |
| CPU Usage | `rate(process_cpu_seconds_total[5m]) * 100` | Prometheus |
| Memory Usage | `process_resident_memory_bytes / 1024 / 1024` | Prometheus |
| Logger Stream | `{service="fastapi-backend"}` | Loki |

---

## Data Flow

```
FastAPI Backend
    ↓
    ├─→ /metrics endpoint
    │       ↓
    │   Prometheus scrapes every 15s
    │       ↓
    │   Grafana queries Prometheus
    │       ↓
    │   7 panels update
    │
    ├─→ STDOUT JSON logs
    │       ↓
    │   Loki ingests logs
    │       ↓
    │   Grafana queries Loki
    │       ↓
    │   Logger Stream panel updates
    │
    └─→ OpenTelemetry gRPC (localhost:4317)
            ↓
        Tempo stores traces
            ↓
        Grafana Tempo dashboard
```

---

## Testing Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run FastAPI app
python main.py

# 3. Generate traffic
for i in {1..100}; do
  curl http://localhost:8000/api/users/1
done

# 4. Verify metrics endpoint
curl http://localhost:8000/metrics | grep fastapi_requests_total

# 5. Check Prometheus scraped data
curl http://localhost:9090/api/v1/query?query=fastapi_requests_total

# 6. Check Loki ingested logs
curl http://localhost:3100/loki/api/v1/label

# 7. Check Tempo received traces
curl http://localhost:3200/api/traces

# 8. View Grafana dashboard
# Open http://localhost:3000 → FastAPI Dashboard
```

---

## What Grafana Will Show

Once your backend implements this:

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

## Deployment to Railway

1. Push FastAPI code to repository
2. Railway auto-detects FastAPI
3. Set environment variable: `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317`
4. Verify metrics endpoint: `https://your-app.railway.app/metrics`
5. Grafana dashboard automatically shows live data

---

## Reference Documentation

All detailed documentation is in the repository:

1. **FASTAPI_DASHBOARD_COMPLETE.md** - Complete implementation guide
2. **FASTAPI_DASHBOARD_INSTRUMENTATION.md** - Detailed technical guide (761 lines)
3. **BACKEND_INSTRUMENTATION_REQUIREMENTS.md** - Complete specifications (597 lines)
4. **BACKEND_AGENT_INSTRUCTIONS.md** - Quick-start guide (407 lines)
5. **FASTAPI_DASHBOARD_SUMMARY.md** - Overview for backend agent (431 lines)
6. **grafana/dashboards/fastapi-dashboard.json** - Pre-configured Grafana dashboard

---

## Summary

**What to provide to backend agent:**
- Copy-paste ready FastAPI application code above
- requirements.txt with all dependencies
- Testing commands to verify implementation
- Reference to detailed documentation files

**What backend agent needs to do:**
1. Implement the FastAPI application code
2. Install dependencies from requirements.txt
3. Run locally and test with provided commands
4. Deploy to Railway
5. Verify metrics, logs, and traces appear in Grafana

**Time to implement:** ~30 minutes

**Result:** FastAPI Dashboard with 8 live panels showing all metrics, logs, and traces
