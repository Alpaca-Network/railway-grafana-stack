# Backend Instrumentation Requirements for FastAPI Dashboard

## Executive Summary

Your FastAPI backend needs to expose three types of observability data:
1. **Prometheus Metrics** - Performance and resource metrics
2. **Structured JSON Logs** - Application logs for debugging
3. **OpenTelemetry Traces** - Distributed tracing for request flow

This document provides exact specifications and code examples for your backend agent.

---

## Part 1: Prometheus Metrics Endpoint

### What to Implement

Your FastAPI backend must expose a `/metrics` endpoint that returns Prometheus-formatted metrics.

### Required Metrics

#### 1. Request Counter
**Name:** `fastapi_requests_total`
**Type:** Counter
**Labels:** `method`, `path`, `status_code`
**Description:** Total number of HTTP requests

```python
from prometheus_client import Counter

requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)
```

#### 2. Request Duration Histogram
**Name:** `fastapi_request_duration_seconds`
**Type:** Histogram
**Labels:** `method`, `path`, `status_code`
**Description:** HTTP request duration in seconds
**Buckets:** 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0

```python
from prometheus_client import Histogram

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)
```

### Implementation Pattern

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI()

# Initialize metrics
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

# Middleware to track all requests
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Record metrics
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

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return generate_latest()

# Example endpoint
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": "John"}
```

### Installation

```bash
pip install prometheus-client
```

### Verification

```bash
curl http://localhost:8000/metrics | grep fastapi_requests_total
```

Expected output:
```
# HELP fastapi_requests_total Total HTTP requests
# TYPE fastapi_requests_total counter
fastapi_requests_total{method="GET",path="/api/users/1",status_code="200"} 5.0
```

---

## Part 2: Structured JSON Logging

### What to Implement

Your FastAPI backend must output structured JSON logs to STDOUT that include:
- Timestamp
- Log level (INFO, ERROR, WARNING, DEBUG)
- Service name
- Endpoint path
- HTTP method
- Status code
- Duration in milliseconds
- Message

### Log Format

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

### Implementation Pattern

```python
import logging
import json
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI, Request
import time

app = FastAPI()

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Middleware to log all requests
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request
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

# Example endpoint
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    logger.info("Fetching user", extra={"user_id": user_id})
    return {"id": user_id, "name": "John"}
```

### Installation

```bash
pip install python-json-logger
```

### Verification

```bash
# Run your FastAPI app and make a request
curl http://localhost:8000/api/users/1

# Check logs (should see JSON output)
```

Expected output in logs:
```json
{"timestamp": "2025-12-18T01:23:45.123Z", "level": "INFO", "service": "fastapi-backend", "endpoint": "/api/users/1", "method": "GET", "status_code": 200, "duration_ms": 45, "message": "Request completed"}
```

---

## Part 3: OpenTelemetry Traces

### What to Implement

Your FastAPI backend must send OpenTelemetry traces to Tempo at `localhost:4317` (gRPC endpoint).

### Implementation Pattern

```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from fastapi import FastAPI

app = FastAPI()

# Configure OTLP exporter (send to Tempo)
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",  # Tempo gRPC endpoint
    insecure=True
)

# Set up tracer provider
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()

# Get tracer for manual spans
tracer = trace.get_tracer(__name__)

# Example endpoint with manual span
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("endpoint", "/api/users/{user_id}")
        
        # Your logic here
        user = {"id": user_id, "name": "John"}
        
        span.set_attribute("status", "success")
        return user

# Example endpoint with nested spans
@app.post("/api/users")
async def create_user(user_data: dict):
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("user_data", str(user_data))
        
        # Simulate database operation
        with tracer.start_as_current_span("db_insert") as db_span:
            db_span.set_attribute("table", "users")
            # Database operation
            pass
        
        return {"id": 1, **user_data}
```

### Installation

```bash
pip install opentelemetry-api
pip install opentelemetry-sdk
pip install opentelemetry-exporter-otlp
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-requests
```

### Verification

```bash
# Make requests to your FastAPI app
curl http://localhost:8000/api/users/1

# Check Tempo for traces
curl http://localhost:3200/api/traces
```

---

## Part 4: Complete FastAPI Application Example

```python
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import logging
import time
import json

# Initialize FastAPI app
app = FastAPI(title="FastAPI Backend")

# ============ PROMETHEUS METRICS ============
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

# ============ JSON LOGGING ============
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ============ OPENTELEMETRY TRACING ============
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True
)
trace_provider = TracerProvider()
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

# ============ MIDDLEWARE ============
@app.middleware("http")
async def metrics_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    duration_ms = duration * 1000
    
    # Record Prometheus metrics
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
    
    # Log to JSON
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
        logger.info("Fetching user", extra={"user_id": user_id})
        return {"id": user_id, "name": "John"}

@app.post("/api/users")
async def create_user(user_data: dict):
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("user_data", str(user_data))
        logger.info("Creating user", extra={"user_data": user_data})
        return {"id": 1, **user_data}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Part 5: Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

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

### docker-compose.yml

```yaml
version: '3.8'

services:
  fastapi-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
    depends_on:
      - tempo
      - prometheus
      - loki

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"
      - "4317:4317"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      - loki
      - tempo
```

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'fastapi-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## Part 6: Testing Checklist

- [ ] `/metrics` endpoint returns Prometheus metrics
- [ ] Metrics include `fastapi_requests_total` counter
- [ ] Metrics include `fastapi_request_duration_seconds` histogram
- [ ] JSON logs appear in STDOUT with all required fields
- [ ] Logs include: timestamp, level, service, endpoint, method, status_code, duration_ms
- [ ] Traces are sent to Tempo at localhost:4317
- [ ] Traces appear in Grafana Tempo dashboard
- [ ] Logs appear in Grafana Loki dashboard with service="fastapi-backend" label
- [ ] Prometheus scrapes metrics successfully
- [ ] CPU and memory metrics are available

### Test Commands

```bash
# Test metrics endpoint
curl http://localhost:8000/metrics | grep fastapi_requests_total

# Generate traffic
for i in {1..100}; do
  curl http://localhost:8000/api/users/1
done

# Check Prometheus
curl http://localhost:9090/api/v1/query?query=fastapi_requests_total

# Check Loki
curl http://localhost:3100/loki/api/v1/label

# Check Tempo
curl http://localhost:3200/api/traces
```

---

## Part 7: Grafana Dashboard

The FastAPI Dashboard is already configured in Grafana with 8 panels:

1. **Total Requests** - Current request rate
2. **Requests Per Minute** - RPM trend over time
3. **Errors Per Second** - Error rate with thresholds
4. **Average Response Time** - Mean latency
5. **Request Duration P60** - 60th percentile latency
6. **CPU Usage** - Process CPU percentage
7. **Memory Usage** - Process memory in MB
8. **Logger Stream** - Real-time logs from Loki

All panels automatically connect to your backend metrics once instrumentation is complete.

---

## Summary

**What to implement:**
1. ✅ Prometheus `/metrics` endpoint with 2 metrics
2. ✅ JSON structured logging to STDOUT
3. ✅ OpenTelemetry traces to Tempo gRPC
4. ✅ Middleware to auto-track all requests

**Expected result:**
- Grafana FastAPI Dashboard shows all 8 panels with live data
- Prometheus scrapes metrics every 15 seconds
- Loki ingests logs in real-time
- Tempo collects distributed traces

**Time to implement:** ~30 minutes
