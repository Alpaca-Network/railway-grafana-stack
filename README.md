# GatewayZ Observability Stack

**Production-ready observability platform for GatewayZ AI Backend** - Centralized metrics, logs, traces, and visualization with horizontal scaling via Grafana Mimir.

[![Railway Deploy](https://railway.app/button.svg)](https://railway.app)

---

## 🚀 Quick Start

### Production Access
- **Grafana Dashboard:** [https://logs.gatewayz.ai](https://logs.gatewayz.ai)
- **Staging Environment:** [gatewayz-staging.up.railway.app](https://gatewayz-staging.up.railway.app)

### Local Development (Docker Compose)

```bash
# 1. Clone and navigate to the stack
git clone <repo-url>
cd railway-grafana-stack

# 2. Configure backend metrics scraping (REQUIRED for data to show)
export FASTAPI_TARGET="host.docker.internal:8000"  # If backend runs on host
# OR
export FASTAPI_TARGET="gatewayz-backend:8000"       # If backend is in Docker network

# 3. Start all services
docker compose up --build

# 4. Access services
open http://localhost:3000  # Grafana (admin/yourpassword123)
open http://localhost:9090  # Prometheus
open http://localhost:9009  # Mimir
```

**📖 Documentation:**
- **[Complete Documentation Index](docs/README.md)** - Start here for all guides and references
- Quick Links:
  - [Setup Guide](docs/setup/NEXT_STEPS.md) - Deploy Prometheus → Mimir → Grafana
  - [Quick Reference](docs/setup/QUICK_REFERENCE.md) - Common commands and queries
  - [Troubleshooting](docs/troubleshooting/REMOTE_WRITE_DEBUG.md) - Fix common issues
  - [Architecture](docs/architecture/MIMIR.md) - System design and components
  - [Alerting Plan](docs/development/ALERTING_IMPLEMENTATION_PLAN.md) - Alerts roadmap

---

## 📊 Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│              GatewayZ Backend API                         │
│  (FastAPI: api.gatewayz.ai, staging.up.railway.app)     │
└───────┬─────────────┬──────────────┬────────────────────┘
        │             │              │
  Metrics (Pull)  Logs (Push)   Traces (Push)
   /metrics      :3100/loki    :4317/:4318
        │             │              │
  ┌─────▼─────┐ ┌─────▼─────┐ ┌──────▼──────┐
  │Prometheus │ │   Loki    │ │   Tempo     │
  │  :9090    │ │  :3100    │ │:3200/:4317/ │
  │           │ │           │ │    :4318    │
  │ Scrapes   │ │Log Storage│ │Trace Storage│
  │every 15-30s│ │30d Retain │ │Span Metrics │
  └─────┬─────┘ └─────┬─────┘ └──────┬──────┘
        │             │              │
        │Remote Write │              │
        ↓             │              │
  ┌──────────────┐   │              │
  │    Mimir     │   │              │
  │   :9009      │◄──┘              │
  │              │                  │
  │Horizontal    │                  │
  │Scaling       │                  │
  │30d Retention │                  │
  └──────┬───────┘                  │
         │                          │
         └──────────────────────────┘
                    │
             ┌──────▼──────┐
             │   Grafana   │
             │    :3000    │
             │             │
             │4 Datasources│ ← Prometheus, Mimir, Loki, Tempo
             │7 Dashboards │
             └─────────────┘
```

### Key Components

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **Grafana 11.5.2** | 3000 | Visualization & dashboards | ✅ 7 production dashboards |
| **Prometheus 3.2.1** | 9090 | Metrics collection | ✅ 6 scrape jobs |
| **Mimir 2.11.0** | 9009, 9095 | Long-term metrics storage | ✅ 30-day retention |
| **Loki 3.4** | 3100 | Log aggregation | ✅ 30-day retention |
| **Tempo** | 3200, 4317, 4318 | Distributed tracing | ✅ OTLP endpoints |
| **Redis Exporter** | 9121 | Redis metrics | ✅ Integrated |
| **Alertmanager** | 9093 | Alert routing | ✅ Email configured |

---

## 🎯 Production Dashboards

All dashboards use **real API endpoints** with live data from Prometheus/Mimir - no mock data.

| Dashboard | Folder | Panels | Refresh | Key Metrics | Status |
|-----------|--------|--------|---------|-------------|--------|
| **Executive Overview** | Executive | 10 | 30s | KPIs, Golden Signals, Request Volume | ✅ Ready |
| **Four Golden Signals** | Executive | 17 | 30s | Latency (P50/P95/P99), Traffic, Errors, Saturation | ✅ Ready |
| **Backend Services** | Backend | 14 | 10s | Redis Cache, API Performance, Health Status | ✅ Ready |
| **Gateway Comparison** | Gateway | 9 | 60s | Provider Health Grid (17 providers) | ✅ Ready |
| **Model Analytics** | Models | 8 | 60s | Top Models, Cost Analysis, Latency | ✅ Ready |
| **Loki Logs** | Logs | 6 | 10s | Log Search, Real-time Streaming | ✅ Ready |
| **Tempo Traces** | Traces | 5 | 30s | Distributed Tracing, Service Graph | ✅ Ready |

### Dashboard Features

#### Executive Overview
- **Golden Signals**: Latency, Traffic, Errors, Saturation
- **KPI Cards**: Active Requests, Avg Response Time, Daily Cost, Error Rate
- **Time Series**: Request volume trends, error distribution
- **Alerts Table**: Critical anomalies and active alerts

#### Backend Services (Prometheus/Mimir)
- **Redis Monitoring**: 6 panels (Status, Hit Rate, Memory, Clients, Keys, Ops/sec)
- **API Performance**: Total Requests, Request Rate, Error Rate %, Avg Latency
- **Trend Charts**: Cache hit rate, operations rate, memory usage, latency percentiles

#### Loki Logs Dashboard
- **Pure log data** from Loki datasource
- **NO Prometheus/Mimir panels** (separated for clarity)
- **Log Search**: Real-time filtering and search
- **Log Volume**: Count by level, service, severity

#### Tempo Traces Dashboard
- **Pure trace data** from Tempo datasource
- **NO Prometheus/Mimir panels** (separated for clarity)
- **Service Graph**: Distributed tracing visualization
- **Span Metrics**: Request duration, error rates by service

---

## ⚙️ Configuration

### Prometheus Scrape Jobs

**File:** `prometheus/prom.yml`

| Job Name | Target | Interval | Purpose |
|----------|--------|----------|---------|
| `prometheus` | localhost:9090 | 15s | Self-monitoring |
| `gatewayz_production` | `${FASTAPI_TARGET}` | 15s | **Production API metrics** |
| `gatewayz_staging` | gatewayz-staging.up.railway.app | 15s | Staging API metrics |
| `redis_exporter` | redis-exporter:9121 | 30s | Redis metrics |
| `gatewayz_data_metrics_production` | `${FASTAPI_TARGET}` | 30s | Provider health, circuit breakers |
| `mimir` | mimir:9009 | 30s | Mimir self-monitoring |

#### ⚠️ **IMPORTANT: `FASTAPI_TARGET` Configuration**

The `${FASTAPI_TARGET}` placeholder **MUST be set** for local development:

```bash
# For backend on host machine (most common)
export FASTAPI_TARGET="host.docker.internal:8000"

# For backend in same Docker network
export FASTAPI_TARGET="gatewayz-backend:8000"

# Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets
```

**Without this variable, the Backend Services dashboard will show no API data.**

### Grafana Datasources

**Directory:** `grafana/datasources/datasources.yml`

| Datasource | UID | Type | URL | Purpose |
|------------|-----|------|-----|---------|
| **Prometheus** | `grafana_prometheus` | prometheus | `${PROMETHEUS_INTERNAL_URL}` | Short-term metrics |
| **Mimir** | `grafana_mimir` | prometheus | `${MIMIR_INTERNAL_URL}/prometheus` | Long-term metrics |
| **Loki** | `grafana_loki` | loki | `${LOKI_URL}` | Logs |
| **Tempo** | `grafana_tempo` | tempo | `${TEMPO_INTERNAL_URL}` | Traces |

### Data Retention

| Service | Retention | Compaction | Notes |
|---------|-----------|------------|-------|
| **Prometheus** | 15 days | N/A | Short-term, remote writes to Mimir |
| **Mimir** | 30 days | Every 2h | Horizontal scaling, HA-ready |
| **Loki** | 30 days | Every 10m | TSDB index, filesystem storage |
| **Tempo** | 7 days | 5m blocks | Local filesystem |

---

## 🔌 Backend Integration

### 1. Expose Metrics Endpoint

**Python (FastAPI):**
```python
from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define custom metrics
request_counter = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'env']
)

latency_histogram = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'env']
)

# Use in your routes
@app.get("/v1/models")
async def list_models():
    request_counter.labels(
        method="GET",
        endpoint="/v1/models",
        status_code="200",
        env="production"
    ).inc()
    return {"models": [...]}
```

### 2. Send Logs to Loki

**Python with python-logging-loki:**
```python
import logging
from logging_loki import LokiHandler

loki_handler = LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"app": "gatewayz", "env": "production"},
    version="1"
)

logger = logging.getLogger("gatewayz")
logger.addHandler(loki_handler)
logger.setLevel(logging.INFO)

# Use structured logging
logger.info("Request processed", extra={
    "user_id": "123",
    "duration_ms": 45,
    "model": "gpt-4"
})
```

### 3. Send Traces to Tempo

**Python with OpenTelemetry:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Tempo exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://tempo:4318/v1/traces"
)

# Setup tracing
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Instrument your code
with tracer.start_as_current_span("model_inference") as span:
    span.set_attribute("model", "gpt-4")
    span.set_attribute("provider", "openai")
    result = await call_model_api()
```

**📖 Complete Integration Guide:** [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)

---

## 🔧 Troubleshooting

### Issue: Backend Services Dashboard Shows "No Data"

**Symptom:** All Redis and API panels show "No data"

**Root Cause:** `FASTAPI_TARGET` environment variable not set for local builds

**Solution:**
```bash
# Set the environment variable
export FASTAPI_TARGET="host.docker.internal:8000"

# Restart Prometheus
docker compose restart prometheus

# Verify targets are UP
open http://localhost:9090/targets
```

### Issue: Loki Dashboard Shows "Bad Request"

**Cause:** Query syntax issues or no logs ingested

**Fix:**
1. Verify Loki is receiving logs:
   ```bash
   curl http://localhost:3100/metrics | grep loki_distributor_lines_received_total
   ```
2. Test log ingestion:
   ```bash
   curl -X POST http://localhost:3100/loki/api/v1/push \
     -H "Content-Type: application/json" \
     -d '{"streams":[{"stream":{"app":"test"},"values":[["'$(date +%s%N)'","test message"]]}]}'
   ```
3. Check query syntax in dashboard (LogQL, not PromQL)

**📖 More Solutions:** [docs/troubleshooting/](docs/troubleshooting/)

### Issue: Grafana Datasource Connection Failed

**Cause:** Datasource UID mismatch or incorrect URLs

**Fix:**
1. Check datasource health:
   ```bash
   # Prometheus
   curl http://localhost:9090/-/healthy
   
   # Mimir
   curl http://localhost:9009/ready
   
   # Loki
   curl http://localhost:3100/ready
   
   # Tempo
   curl http://localhost:3200/ready
   ```

2. Verify datasource UIDs in Grafana:
   - Prometheus: `grafana_prometheus`
   - Mimir: `grafana_mimir`
   - Loki: `grafana_loki`
   - Tempo: `grafana_tempo`

3. Check environment variables in `docker-compose.yml`

---

## 🆕 What's New

### January 2026 - Mimir Integration + Dashboard Separation

**Branch:** `feat/feat-mimir-took`

**✅ Grafana Mimir for Horizontal Scaling:**
- Long-term metrics storage (30+ days, configurable)
- Horizontally scalable with built-in replication
- High availability ready
- Remote write from Prometheus
- Consistent queries across dashboard refreshes

**✅ Dashboard Clarity Improvements:**
- **Loki Dashboard**: Removed all Prometheus/Mimir panels (pure logs)
- **Tempo Dashboard**: Removed all Prometheus/Mimir panels (pure traces)
- **Backend Services**: Combined Backend Health + Redis into one dashboard
- **Executive Overview**: All panels use Prometheus/Mimir datasources

**✅ Enhanced Alerting:**
- Prometheus/Alertmanager SMTP fixes
- Health score alerts (< 20% triggers email)
- Redis alerts (memory, hit rate, connection count)
- SLO breach alerts (availability, latency)
- Notification policies for critical vs operational alerts

**📖 Complete Guide:** [MIMIR_INTEGRATION_SUMMARY.md](MIMIR_INTEGRATION_SUMMARY.md)

### December 2025 - Four Golden Signals Dashboard

**✅ Google SRE Methodology Implementation:**
- **SIGNAL 1 - LATENCY:** P50/P95/P99 percentiles + 24h trends
- **SIGNAL 2 - TRAFFIC:** Request volume, rate, active requests
- **SIGNAL 3 - ERRORS:** Error rate gauge + 24h error trends
- **SIGNAL 4 - SATURATION:** CPU/Memory/Redis utilization + trends
- **17 panels total** with 30-second auto-refresh

**✅ Dashboard Organization:**
- Folder-based organization (Executive, Backend, Gateway, Models, Logs, Traces)
- Improved navigation and discovery
- Consistent naming conventions

---

## 🧪 Testing & Quality Assurance

### Test Coverage

- **25+ Real API Endpoints** - Integration tests with performance validation
- **7 Production Dashboards** - Schema validation and configuration checks
- **90+ Test Methods** - Comprehensive coverage across all components
- **GitHub Actions Workflows** - Automated validation on every deployment

### Quick Testing Commands

```bash
# Setup (required once)
cp .env.example .env
# Edit .env and add your API keys

# Run all tests
pytest tests/ -v

# Dashboard validation
./scripts/validate_dashboards.sh strict

# Endpoint testing
export API_KEY="your_api_key"
./scripts/test_all_endpoints.sh "$API_KEY" https://api.gatewayz.ai

# Specific test categories
pytest tests/test_dashboards.py -v -m dashboard
pytest tests/test_api_endpoints.py -v -m endpoint
```

**📖 Complete Testing Guide:** [docs/archive/root-md/CI_CD_TESTING_REPORT.md](docs/archive/root-md/CI_CD_TESTING_REPORT.md)

### Quality Assurance Status

✅ **All Endpoints are REAL** - No mock data  
✅ **Security Best Practices** - No hardcoded credentials  
✅ **Comprehensive Testing** - 90+ test methods  
✅ **CI/CD Integration** - Automatic validation  
✅ **Production Ready** - Approved by QA experts  

**QA Rating:** ⭐⭐⭐⭐⭐ EXCELLENT (5/5 for Test Coverage & Security)

---

## 🚀 Deployment

### Railway Deployment

```bash
# 1. Push to Railway
git push railway main

# 2. Or use Railway CLI
railway up

# 3. Configure environment variables in Railway dashboard
FASTAPI_TARGET=api.gatewayz.ai:443
PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009
LOKI_URL=http://loki.railway.internal:3100
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
```

### Docker Compose (Local)

```bash
# Start all services
docker compose up --build

# Start specific services
docker compose up grafana prometheus mimir

# View logs
docker compose logs -f grafana

# Stop all services
docker compose down

# Clean volumes (WARNING: deletes all data)
docker compose down -v
```

**📖 Deployment Guide:** [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

---

## 📚 Documentation

### Core Documentation

- **[Documentation Index](docs/docs-index.md)** - Start here for all docs
- **[Backend Integration](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)** - Required metrics and instrumentation
- **[Railway Deployment](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)** - Deploy to Railway
- **[Mimir Integration](MIMIR_INTEGRATION_SUMMARY.md)** - Horizontal scaling guide
- **[Troubleshooting](docs/troubleshooting/)** - Service-specific fix guides

### Additional Resources

- **[Endpoint Verification Report](docs/archive/root-md/ENDPOINT_VERIFICATION_REPORT.md)** - All endpoints verified as real
- **[CI/CD Testing Report](docs/archive/root-md/CI_CD_TESTING_REPORT.md)** - Complete testing breakdown
- **[QA Review Report](docs/archive/root-md/QA_REVIEW_REPORT.md)** - Expert sign-off

---

## 🛠️ Development

### Project Structure

```
railway-grafana-stack/
├── grafana/
│   ├── Dockerfile
│   ├── dashboards/
│   │   ├── executive/       # Executive dashboards
│   │   ├── backend/         # Backend Services dashboard
│   │   ├── gateway/         # Gateway comparison
│   │   ├── models/          # Model analytics
│   │   ├── logs/            # Loki logs (pure logs, no Prometheus)
│   │   └── traces/          # Tempo traces (pure traces, no Prometheus)
│   ├── datasources/
│   │   └── datasources.yml  # Prometheus, Mimir, Loki, Tempo
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── alerting/
│           ├── rules/
│           │   └── redis_alerts.yml
│           └── notification_policies.yml
├── prometheus/
│   ├── Dockerfile
│   ├── prom.yml             # Scrape jobs (FASTAPI_TARGET here)
│   └── alert.rules.yml      # Alert rules
├── mimir/
│   ├── Dockerfile
│   └── mimir.yml            # Mimir configuration
├── loki/
│   ├── Dockerfile
│   └── loki.yml             # Loki configuration
├── tempo/
│   ├── Dockerfile
│   └── tempo.yml            # Tempo configuration
├── tests/                    # Pytest test suite
├── scripts/                  # Validation scripts
├── docs/                     # Documentation
├── docker-compose.yml        # Local development
└── README.md                 # This file
```

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally with `docker compose up`
3. Run tests: `pytest tests/ -v`
4. Push to staging branch for testing
5. Create pull request to `main`

---

## 📞 Support & Resources

### External Documentation

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Railway Documentation](https://docs.railway.app/)

### Getting Help

- **Documentation Issues:** Check [docs/troubleshooting/](docs/troubleshooting/)
- **Backend Integration:** See [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)
- **Deployment Help:** Review [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)

---

## 📄 License

Proprietary - GatewayZ Network

---

**GatewayZ Observability Stack** · Enterprise-grade monitoring for AI infrastructure · Powered by Prometheus, Mimir, Loki, Tempo, and Grafana
