# FastAPI Dashboard Instrumentation Guide

## Overview
This guide specifies exactly what your backend needs to expose for the FastAPI Dashboard to work with Prometheus, Loki, and Tempo.

---

## Part 1: Prometheus Metrics (Required)

### 1.1 Total Requests
**Metric Name:** `fastapi_requests_total`
**Type:** Counter
**Labels:** `method`, `path`, `status_code`
**Example:**
```python
from prometheus_client import Counter

requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)

# In your middleware:
requests_total.labels(method='GET', path='/api/users', status_code=200).inc()
```

**Grafana Query:**
```promql
rate(fastapi_requests_total[5m])
```

---

### 1.2 Requests Per Minute (RPM)
**Metric Name:** `fastapi_requests_total` (same as above)
**Calculation:** Convert rate to per-minute

**Grafana Query:**
```promql
rate(fastapi_requests_total[1m]) * 60
```

**Panel Configuration:**
```json
{
  "title": "Requests Per Minute",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total[1m]) * 60",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "type": "stat",
  "unit": "reqps"
}
```

---

### 1.3 Errors Per Second
**Metric Name:** `fastapi_requests_total` (filtered by status code)
**Type:** Counter with status_code label

**Grafana Query:**
```promql
rate(fastapi_requests_total{status_code=~"4..|5.."}[1s])
```

**Panel Configuration:**
```json
{
  "title": "Errors Per Second",
  "targets": [
    {
      "expr": "rate(fastapi_requests_total{status_code=~\"4..|5..\"}[1s])",
      "legendFormat": "{{status_code}}"
    }
  ],
  "type": "stat",
  "unit": "short",
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 1},
      {"color": "red", "value": 5}
    ]
  }
}
```

---

### 1.4 Average Response Time
**Metric Name:** `fastapi_request_duration_seconds`
**Type:** Histogram
**Labels:** `method`, `path`, `status_code`
**Example:**
```python
from prometheus_client import Histogram

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# In your middleware:
with request_duration.labels(
    method='GET',
    path='/api/users',
    status_code=200
).time():
    # Your endpoint logic
    pass
```

**Grafana Query:**
```promql
rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])
```

**Panel Configuration:**
```json
{
  "title": "Average Response Time",
  "targets": [
    {
      "expr": "rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "type": "timeseries",
  "unit": "s"
}
```

---

### 1.5 Request Duration P60 (60th Percentile)
**Metric Name:** `fastapi_request_duration_seconds_bucket` (from Histogram)
**Calculation:** Use histogram_quantile

**Grafana Query:**
```promql
histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))
```

**Panel Configuration:**
```json
{
  "title": "Request Duration P60",
  "targets": [
    {
      "expr": "histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))",
      "legendFormat": "{{method}} {{path}}"
    }
  ],
  "type": "timeseries",
  "unit": "s"
}
```

---

### 1.6 CPU Usage
**Metric Name:** `process_cpu_seconds_total`
**Type:** Counter (built-in from prometheus_client)
**Note:** This is automatically exposed by prometheus_client

**Grafana Query:**
```promql
rate(process_cpu_seconds_total[5m]) * 100
```

**Panel Configuration:**
```json
{
  "title": "CPU Usage",
  "targets": [
    {
      "expr": "rate(process_cpu_seconds_total[5m]) * 100",
      "legendFormat": "CPU %"
    }
  ],
  "type": "stat",
  "unit": "percent",
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 50},
      {"color": "red", "value": 80}
    ]
  }
}
```

---

### 1.7 Memory Usage
**Metric Name:** `process_resident_memory_bytes`
**Type:** Gauge (built-in from prometheus_client)
**Note:** This is automatically exposed by prometheus_client

**Grafana Query:**
```promql
process_resident_memory_bytes / 1024 / 1024
```

**Panel Configuration:**
```json
{
  "title": "Memory Usage",
  "targets": [
    {
      "expr": "process_resident_memory_bytes / 1024 / 1024",
      "legendFormat": "Memory (MB)"
    }
  ],
  "type": "stat",
  "unit": "decbytes",
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"color": "green", "value": null},
      {"color": "yellow", "value": 512},
      {"color": "red", "value": 1024}
    ]
  }
}
```

---

## Part 2: Loki Logs (Logger Stream)

### 2.1 Log Stream Configuration
**What to send:** Structured logs from FastAPI with labels

**Example Log Format:**
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

**Backend Implementation (Python):**
```python
import logging
import json
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# In your FastAPI middleware:
logger.info("Request", extra={
    "service": "fastapi-backend",
    "endpoint": request.url.path,
    "method": request.method,
    "status_code": response.status_code,
    "duration_ms": elapsed_time * 1000
})
```

### 2.2 Loki Query for Logger Stream
**Query:** Get all logs from FastAPI service

```logql
{service="fastapi-backend"}
```

**Grafana Panel Configuration:**
```json
{
  "title": "Logger Stream",
  "targets": [
    {
      "expr": "{service=\"fastapi-backend\"}",
      "refId": "A"
    }
  ],
  "type": "logs",
  "options": {
    "showLabels": ["level", "endpoint", "status_code"],
    "showTime": true,
    "wrapLogMessage": false
  }
}
```

### 2.3 Loki Query for Error Logs
```logql
{service="fastapi-backend", level="ERROR"}
```

### 2.4 Loki Query for Slow Requests (>1s)
```logql
{service="fastapi-backend"} | json | duration_ms > 1000
```

---

## Part 3: Tempo Traces (Distributed Tracing)

### 3.1 Trace Instrumentation
**What to send:** OpenTelemetry traces from FastAPI

**Backend Implementation (Python):**
```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

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
RequestsInstrumentor().instrument()

# Manual span creation
tracer = trace.get_tracer(__name__)

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("get_user") as span:
        span.set_attribute("user_id", user_id)
        # Your logic here
        return {"id": user_id, "name": "John"}
```

### 3.2 Tempo Query in Grafana
**Trace Search Panel:**
```json
{
  "title": "Trace Search",
  "targets": [
    {
      "datasource": "Tempo",
      "queryType": "traceql",
      "query": "{ span.http.method = \"GET\" && span.http.status_code = 200 }",
      "refId": "A"
    }
  ],
  "type": "traces"
}
```

### 3.3 Trace Correlation with Logs
**In Grafana Datasource Config:**
```json
{
  "name": "Tempo",
  "type": "tempo",
  "uid": "grafana_tempo",
  "jsonData": {
    "tracesToLogsV2": {
      "datasourceUid": "loki_uid",
      "tags": ["service", "endpoint"],
      "mappedTags": [
        {
          "key": "service",
          "value": "service"
        }
      ],
      "spanStartTimeShift": "0",
      "spanEndTimeShift": "0"
    }
  }
}
```

---

## Part 4: Complete FastAPI Dashboard Panel Examples

### Panel 1: Total Requests (Stat)
```json
{
  "id": 1,
  "title": "Total Requests",
  "type": "stat",
  "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
  "targets": [
    {
      "expr": "sum(rate(fastapi_requests_total[5m]))",
      "refId": "A"
    }
  ],
  "options": {
    "textMode": "auto",
    "colorMode": "background",
    "graphMode": "area",
    "justifyMode": "auto"
  },
  "fieldConfig": {
    "defaults": {
      "unit": "reqps",
      "custom": {"hideFrom": {"tooltip": false, "viz": false, "legend": false}}
    }
  }
}
```

### Panel 2: Requests Per Minute (Timeseries)
```json
{
  "id": 2,
  "title": "Requests Per Minute",
  "type": "timeseries",
  "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0},
  "targets": [
    {
      "expr": "rate(fastapi_requests_total[1m]) * 60",
      "legendFormat": "{{method}} {{path}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "short",
      "custom": {
        "lineWidth": 1,
        "fillOpacity": 10,
        "showPoints": "auto"
      }
    }
  }
}
```

### Panel 3: Errors Per Second (Stat with Alert)
```json
{
  "id": 3,
  "title": "Errors Per Second",
  "type": "stat",
  "gridPos": {"h": 4, "w": 6, "x": 0, "y": 4},
  "targets": [
    {
      "expr": "rate(fastapi_requests_total{status_code=~\"4..|5..\"}[1s])",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "short",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 1},
          {"color": "red", "value": 5}
        ]
      }
    }
  }
}
```

### Panel 4: Average Response Time (Timeseries)
```json
{
  "id": 4,
  "title": "Average Response Time",
  "type": "timeseries",
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
  "targets": [
    {
      "expr": "rate(fastapi_request_duration_seconds_sum[5m]) / rate(fastapi_request_duration_seconds_count[5m])",
      "legendFormat": "{{method}} {{path}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "s",
      "custom": {
        "lineWidth": 2,
        "fillOpacity": 0,
        "showPoints": "never"
      }
    }
  }
}
```

### Panel 5: Request Duration P60 (Timeseries)
```json
{
  "id": 5,
  "title": "Request Duration P60",
  "type": "timeseries",
  "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
  "targets": [
    {
      "expr": "histogram_quantile(0.60, rate(fastapi_request_duration_seconds_bucket[5m]))",
      "legendFormat": "P60 {{method}} {{path}}",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "s",
      "custom": {
        "lineWidth": 2,
        "fillOpacity": 0,
        "showPoints": "never"
      }
    }
  }
}
```

### Panel 6: CPU Usage (Gauge)
```json
{
  "id": 6,
  "title": "CPU Usage",
  "type": "gauge",
  "gridPos": {"h": 8, "w": 6, "x": 0, "y": 16},
  "targets": [
    {
      "expr": "rate(process_cpu_seconds_total[5m]) * 100",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100,
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 50},
          {"color": "red", "value": 80}
        ]
      }
    }
  }
}
```

### Panel 7: Memory Usage (Gauge)
```json
{
  "id": 7,
  "title": "Memory Usage",
  "type": "gauge",
  "gridPos": {"h": 8, "w": 6, "x": 6, "y": 16},
  "targets": [
    {
      "expr": "process_resident_memory_bytes / 1024 / 1024",
      "refId": "A"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "decbytes",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 512},
          {"color": "red", "value": 1024}
        ]
      }
    }
  }
}
```

### Panel 8: Logger Stream (Logs)
```json
{
  "id": 8,
  "title": "Logger Stream",
  "type": "logs",
  "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
  "targets": [
    {
      "datasource": "Loki",
      "expr": "{service=\"fastapi-backend\"}",
      "refId": "A"
    }
  ],
  "options": {
    "showLabels": ["level", "endpoint", "status_code"],
    "showTime": true,
    "wrapLogMessage": false,
    "sortOrder": 2
  }
}
```

---

## Part 5: Backend Endpoint Summary

### What Your Backend Must Expose

| Component | Endpoint | Port | Format | Frequency |
|-----------|----------|------|--------|-----------|
| **Prometheus Metrics** | `/metrics` | 8000 | Prometheus text format | Every 15s |
| **Loki Logs** | STDOUT/STDERR | - | JSON logs | Real-time |
| **Tempo Traces** | gRPC/HTTP | 4317/4318 | OTLP | Real-time |

### Example FastAPI Setup
```python
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time
import logging

app = FastAPI()

# Prometheus metrics
requests_total = Counter(
    'fastapi_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status_code']
)

request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'path', 'status_code']
)

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
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

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return generate_latest()

# Example endpoint
@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id, "name": "John"}
```

---

## Part 6: Instructions for Your Backend Agent

### Tell Your Backend Agent:

**"I need you to implement the following instrumentation in the FastAPI backend:**

**1. Prometheus Metrics (expose at `/metrics`):**
   - `fastapi_requests_total` (Counter) - labels: method, path, status_code
   - `fastapi_request_duration_seconds` (Histogram) - labels: method, path, status_code
   - Use `prometheus_client` library
   - Middleware to track all requests automatically

**2. Structured JSON Logging (to STDOUT):**
   - Use `python-json-logger` library
   - Log format: `{"timestamp": "...", "level": "...", "service": "fastapi-backend", "endpoint": "...", "method": "...", "status_code": ..., "duration_ms": ...}`
   - Log every request with level, endpoint, status code, and duration

**3. OpenTelemetry Traces (send to Tempo at localhost:4317):**
   - Use `opentelemetry-api` and `opentelemetry-exporter-otlp`
   - Auto-instrument FastAPI with `opentelemetry-instrumentation-fastapi`
   - Create manual spans for important operations
   - Set attributes: user_id, endpoint, status_code, duration

**4. Metrics Endpoint:**
   - Expose `/metrics` endpoint that returns Prometheus format
   - Should be scraped every 15 seconds

**Reference implementations provided in FASTAPI_DASHBOARD_INSTRUMENTATION.md**"

---

## Part 7: Grafana Dashboard Integration

### Step 1: Verify Data Sources
```bash
# Check Prometheus
curl http://localhost:9090/api/v1/query?query=fastapi_requests_total

# Check Loki
curl http://localhost:3100/loki/api/v1/label

# Check Tempo
curl http://localhost:3200/api/traces
```

### Step 2: Create Dashboard
1. Go to Grafana → Dashboards → New Dashboard
2. Add panels using the configurations above
3. Set refresh rate to 30s
4. Save as "FastAPI Dashboard"

### Step 3: Link Datasources
- Prometheus → Metrics
- Loki → Logs
- Tempo → Traces

---

## Summary

**What you need from backend:**
- ✅ Prometheus `/metrics` endpoint with 2 metrics
- ✅ JSON structured logs to STDOUT
- ✅ OpenTelemetry traces to Tempo gRPC
- ✅ Middleware to auto-track all requests

**What Grafana will visualize:**
- ✅ 8 panels: Total Requests, RPM, Errors/s, Avg Response Time, P60, CPU, Memory, Logger Stream
- ✅ All connected to Prometheus, Loki, and Tempo
- ✅ Real-time updates every 30 seconds
