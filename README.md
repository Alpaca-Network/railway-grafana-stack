# GatewayZ Observability Stack

A production-ready observability solution for **GatewayZ AI Backend**, providing centralized logging, metrics collection, distributed tracing, and visualization. Deployed on Railway with Docker Compose support for local development.

## 🚀 Quick Links

- **Production Grafana:** [https://logs.gatewayz.ai](https://logs.gatewayz.ai)
- **Staging:** [gatewayz-staging.up.railway.app](https://gatewayz-staging.up.railway.app)
- **Quick Start:** [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md)
- **Backend Integration:** [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)

---

## 📊 Stack Components

| Service | Port(s) | Purpose | Status |
|---------|---------|---------|--------|
| **Grafana 11.5.2** | 3000 | Visualization & dashboarding | ✅ 8 dashboards |
| **Prometheus v3.2.1** | 9090 | Time-series metrics collection | ✅ 3 scrape jobs |
| **Loki 3.4** | 3100 | Log aggregation | ✅ 30-day retention |
| **Tempo** | 3200, 4317, 4318 | Distributed tracing | ✅ Metrics enabled |
| **Redis Exporter** | 9121 | Redis metrics export | ✅ Configured |

**All services are pre-configured, interconnected, and production-ready.**

---

## 📚 Documentation

### 🎯 Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start](QUICK_START.md) | Local development setup (Docker Compose) |
| [Railway Deployment](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md) | Deploy to Railway (production) |
| [Staging Workflow](docs/deployment/STAGING_WORKFLOW.md) | Test changes before production |

### 🔧 Backend Integration

| Document | Description |
|----------|-------------|
| [Backend Metrics Requirements](docs/backend/BACKEND_METRICS_REQUIREMENTS.md) | **Required metrics for dashboards** |
| [Redis Monitoring Guide](docs/REDIS_MONITORING_GUIDE.md) | Redis monitoring setup & options |

### 📈 Dashboard Guides

| Document | Description |
|----------|-------------|
| [Models Monitoring Setup](docs/dashboards/MODELS_MONITORING_SETUP.md) | AI model performance tracking |
| [Provider Management](docs/dashboards/PROVIDER_MANAGEMENT_DASHBOARD.md) | Provider health & metrics |
| [Provider Endpoints](docs/dashboards/PROVIDER_ENDPOINTS_INTEGRATION.md) | Provider API integration |
| [Prometheus Metrics](docs/dashboards/PROMETHEUS_METRICS_EXPANSION.md) | Custom metrics expansion |

### 🔍 Troubleshooting

| Document | Description |
|----------|-------------|
| [Grafana Connections](docs/troubleshooting/GRAFANA_CONNECTIONS.md) | Datasource connectivity issues |
| [Loki Fix Guide](docs/troubleshooting/LOKI_FIX_GUIDE.md) | Log ingestion troubleshooting |
| [Loki Deployment Fix](docs/troubleshooting/LOKI_DEPLOYMENT_FIX.md) | Railway deployment issues |
| [Tempo Integration](docs/troubleshooting/TEMPO_INTEGRATION.md) | Tracing setup & fixes |
| [Sentry Setup](docs/troubleshooting/SENTRY_SETUP.md) | Error tracking integration |

### 📋 Change Log

| Document | Description |
|----------|-------------|
| [Changes Summary](CHANGES_SUMMARY.md) | Recent infrastructure optimizations |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    GatewayZ Backend API                           │
│         (api.gatewayz.ai, gatewayz-staging.up.railway.app)       │
└──────────┬──────────────┬──────────────┬────────────────────────┘
           │              │              │
    Metrics (Pull)   Logs (Push)   Traces (Push OTLP)
     /metrics      :3100/loki      :4317 (gRPC)
                                   :4318 (HTTP)
           │              │              │
    ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
    │ Prometheus  │ │   Loki    │ │   Tempo     │
    │   :9090     │ │  :3100    │ │:3200/:4317/ │
    │             │ │           │ │    :4318    │
    │ 3 Jobs      │ │30d Retain │ │Metrics Gen  │
    │ 15-30s      │ │Compaction │ │Span Metrics │
    └──────┬──────┘ └─────┬─────┘ └──────┬──────┘
           │              │              │
           └──────────────┼──────────────┘
                          │
                   ┌──────▼──────┐
                   │   Grafana   │
                   │    :3000    │
                   │             │
                   │ 8 Dashboards│
                   │ 3 Datasources│
                   └─────────────┘
```

### Data Flow

1. **Metrics (Pull)**: Prometheus scrapes `/metrics` endpoints every 15-30s
2. **Logs (Push)**: Applications push JSON logs to Loki via HTTP
3. **Traces (Push)**: Applications send OTLP traces to Tempo (gRPC/HTTP)
4. **Visualization**: Grafana queries all three datasources

---

## 📊 Dashboards Available

| Dashboard | Panels | Metrics | Status |
|-----------|--------|---------|--------|
| **1. FastAPI Dashboard** | 17 | `fastapi_requests_total`, latency, errors | ✅ Working |
| **2. Model Health** | 13 | `model_inference_*`, tokens, credits | ✅ Working |
| **3. GatewayZ Application Health** | 28 | Provider health, circuit breakers | ⚠️ Needs backend metrics |
| **4. GatewayZ Backend Metrics** | 7 | HTTP metrics, database, cache | ✅ Working |
| **5. GatewayZ Redis Services** | 11 | Cache hits/misses, Redis stats | ✅ Working |
| **6. Loki Logs** | 9 | Log search, filtering, aggregation | ✅ Working |
| **7. Prometheus Metrics** | 10 | Prometheus internals | ✅ Working |
| **8. Tempo Distributed Tracing** | 6 | Trace search, span metrics | ✅ Working (after restart) |

---

## 🔌 Service URLs

### Internal URLs (Within Railway Project)

```bash
# Datasource URLs (for Grafana)
PROMETHEUS_URL=http://prometheus:9090
LOKI_URL=http://loki:3100
TEMPO_URL=http://tempo:3200

# Push URLs (for your backend)
LOKI_PUSH_URL=http://loki:3100/loki/api/v1/push
TEMPO_OTLP_HTTP=http://tempo:4318
TEMPO_OTLP_GRPC=http://tempo:4317
PROMETHEUS_SCRAPE=http://your-backend:PORT/metrics  # Pulled by Prometheus
```

### Public URLs

| Service | URL |
|---------|-----|
| Grafana Production | https://logs.gatewayz.ai |
| Prometheus Production | https://prometheus-production-08db.up.railway.app |
| Staging Environment | https://gatewayz-staging.up.railway.app |

---

## 🚀 Quick Start

### Option 1: Local Development (Docker Compose)

```bash
# Clone repository
git clone https://github.com/your-org/railway-grafana-stack.git
cd railway-grafana-stack

# Start all services
docker compose up --build

# Access services
open http://localhost:3000  # Grafana (admin/yourpassword123)
open http://localhost:9090  # Prometheus
curl http://localhost:3100/ready  # Loki health
curl http://localhost:3200/ready  # Tempo health
```

**See [QUICK_START.md](QUICK_START.md) for detailed local setup.**

### Option 2: Deploy to Railway

```bash
# Push to Railway
git push railway main

# Or use Railway CLI
railway up
```

**See [docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md](docs/deployment/RAILWAY_DEPLOYMENT_QUICK_START.md) for detailed deployment steps.**

---

## ⚙️ Configuration

### Prometheus Scrape Jobs

**File:** [prometheus/prom.yml](prometheus/prom.yml)

| Job Name | Target | Interval | Environment |
|----------|--------|----------|-------------|
| `prometheus` | localhost:9090 | 15s | Self-monitoring |
| `gatewayz_production` | api.gatewayz.ai | 15s | Production API |
| `gatewayz_staging` | gatewayz-staging.up.railway.app | 15s | Staging API |
| `redis_exporter` | redis-exporter:9121 | 30s | Redis metrics |

### Loki Configuration

**File:** [loki/loki.yml](loki/loki.yml)

- **Retention:** 30 days (720h)
- **Compaction:** Enabled (every 10 minutes)
- **Max Ingestion:** 10 MB/s (burst: 20 MB/s)
- **Storage:** Local filesystem with TSDB index

### Tempo Configuration

**File:** [tempo/tempo.yml](tempo/tempo.yml)

- **Receivers:** OTLP gRPC (:4317), OTLP HTTP (:4318)
- **Metrics Generator:** ✅ Enabled (service graphs + span metrics)
- **Storage:** Local filesystem
- **Block Duration:** 5 minutes

### Grafana Datasources

**Directory:** [grafana/provisioning/datasources/](grafana/provisioning/datasources/)

| Datasource | UID | Type | URL |
|------------|-----|------|-----|
| Prometheus | `grafana_prometheus` | prometheus | `${PROMETHEUS_INTERNAL_URL}` |
| Loki | `grafana_loki` | loki | `${LOKI_URL}` |
| Tempo | `grafana_tempo` | tempo | `${TEMPO_INTERNAL_URL}` |

---

## 📈 Metrics Exported

### ✅ Available Metrics (Backend Already Exports)

**FastAPI:**
- `fastapi_requests_total` - Total HTTP requests
- `fastapi_requests_duration_seconds` - Request latency histogram
- `fastapi_requests_in_progress` - In-flight requests
- `fastapi_request_size_bytes`, `fastapi_response_size_bytes`

**Model Inference:**
- `model_inference_requests_total{model, provider, status}`
- `model_inference_duration_seconds{model, provider}`
- `tokens_used_total{model, provider}`
- `credits_used_total{model, provider}`

**Database & Cache:**
- `database_queries_total{operation}`
- `database_query_duration_seconds{operation}`
- `cache_hits_total`, `cache_misses_total`, `cache_size_bytes`

**Performance:**
- `backend_ttfb_seconds` - Time to first byte
- `streaming_duration_seconds` - Streaming duration
- `time_to_first_chunk_seconds{model, provider}` - TTFC

**User Metrics:**
- `active_api_keys`, `subscription_count`, `trial_active`
- `user_credit_balance{user_id}`

### ⚠️ Missing Metrics (Need Backend Implementation)

See [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md) for:
- `provider_availability{provider}` - Provider health status
- `provider_error_rate{provider}` - Provider error rates
- `provider_response_time_seconds{provider}` - Provider latencies
- `gatewayz_provider_health_score{provider}` - Overall health score
- And more...

---

## 🔧 Backend Integration

### 1. Instrument Your FastAPI Backend

**Python Example:**
```python
from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Define custom metrics
model_requests = Counter(
    'model_inference_requests_total',
    'Total model requests',
    ['model', 'provider', 'status']
)

# Use in your code
@app.post("/v1/chat/completions")
async def chat_completion(request: ChatRequest):
    # Your logic here
    model_requests.labels(
        model=request.model,
        provider=provider,
        status='success'
    ).inc()
```

### 2. Send Logs to Loki

**Python with Winston-Loki equivalent:**
```python
import logging
from python_loki_handler import LokiHandler

loki_handler = LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"app": "gatewayz", "env": "production"}
)

logger = logging.getLogger()
logger.addHandler(loki_handler)

logger.info("Request processed", extra={"user_id": "123", "duration_ms": 45})
```

### 3. Send Traces to Tempo

**Python with OpenTelemetry:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure Tempo exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4318/v1/traces")

# Set up tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in your code
with tracer.start_as_current_span("model_inference"):
    result = await call_model_api()
```

**Full examples:** [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)

---

## 🐛 Common Issues & Fixes

### Issue: Dashboards show "No Data"

**Cause:** Backend not exporting metrics or Prometheus not scraping

**Fix:**
1. Verify backend exposes `/metrics`: `curl https://api.gatewayz.ai/metrics`
2. Check Prometheus targets: `http://localhost:9090/targets` (all should be "UP")
3. Verify job names in [prometheus/prom.yml](prometheus/prom.yml) match your backend

### Issue: Loki "400 Bad Request" in logs dashboard

**Cause:** Query syntax issues or no logs ingested

**Fix:**
1. Verify logs are being sent: `curl http://localhost:3100/metrics | grep loki_distributor_lines_received_total`
2. Check query syntax in dashboard (should use LogQL, not PromQL)
3. See [docs/troubleshooting/LOKI_FIX_GUIDE.md](docs/troubleshooting/LOKI_FIX_GUIDE.md)

### Issue: Tempo "Frame too large" error

**Cause:** Wrong port in frontend_worker config

**Fix:** Already fixed in [tempo/tempo.yml:63](tempo/tempo.yml#L63) - frontend uses port 3200 (HTTP)

### Issue: Grafana datasources not connecting

**Cause:** UID mismatch or wrong URLs

**Fix:** Datasource UIDs are now fixed:
- Prometheus: `grafana_prometheus`
- Loki: `grafana_loki`
- Tempo: `grafana_tempo`

See [docs/troubleshooting/GRAFANA_CONNECTIONS.md](docs/troubleshooting/GRAFANA_CONNECTIONS.md)

---

## 🧪 Testing & Staging

### Staging Workflow

1. Push to `staging/models-and-fixes` branch
2. Verify on staging: `https://gatewayz-staging.up.railway.app`
3. Test all dashboards load correctly
4. Merge to `main` for production

**See:** [docs/deployment/STAGING_WORKFLOW.md](docs/deployment/STAGING_WORKFLOW.md)

### Validate Configuration Locally

```bash
# Start stack
docker compose up -d

# Check service health
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3100/ready      # Loki
curl http://localhost:3200/ready      # Tempo
curl http://localhost:3000/api/health # Grafana

# Verify Prometheus scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Send test log to Loki
curl -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{"streams":[{"stream":{"app":"test"},"values":[["'$(date +%s%N)'","test log message"]]}]}'

# Generate test traffic
for i in {1..20}; do curl http://localhost:8000/metrics; sleep 0.5; done
```

---

## 📦 Recent Changes

See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for detailed change log.

### Latest Optimizations (2025-12-23)

✅ **Loki:** Enabled 30-day retention + compaction (prevents disk growth)
✅ **Tempo:** Enabled metrics generation (span metrics + service graphs)
✅ **Prometheus:** Fixed duplicate scraping, added environment labels
✅ **Grafana:** Fixed datasource UIDs for stable connectivity
✅ **Documentation:** Consolidated 30+ files into organized structure

---

## 🛠️ Development

### Project Structure

```
railway-grafana-stack/
├── grafana/
│   ├── Dockerfile
│   ├── dashboards/           # 8 pre-built dashboards (JSON)
│   └── provisioning/         # Datasource auto-configuration
├── prometheus/
│   ├── Dockerfile
│   ├── prom.yml              # Scrape configuration
│   └── alert.rules.yml       # Alert rules
├── loki/
│   ├── Dockerfile
│   └── loki.yml              # Storage & retention config
├── tempo/
│   ├── Dockerfile
│   └── tempo.yml             # Tracing & metrics config
├── examples/
│   ├── api/                  # Node.js monitoring example
│   └── provider-metrics-exporter.py  # Python exporter example
├── docs/
│   ├── backend/              # Backend integration guides
│   ├── deployment/           # Deployment guides
│   ├── dashboards/           # Dashboard documentation
│   ├── troubleshooting/      # Fix guides
│   └── archive/              # Deprecated docs
├── docker-compose.yml        # Local development setup
├── railway.toml              # Railway deployment config
└── README.md                 # This file
```

### Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally with `docker compose up`
3. Push to staging branch for testing
4. Create pull request to `main`

---

## 📚 External Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Railway Documentation](https://docs.railway.app/)

---

## 📞 Support

### Documentation Issues
- Check [docs/troubleshooting/](docs/troubleshooting/) directory
- Review [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) for recent changes
- Search existing issues in repository

### Backend Integration Help
- See [docs/backend/BACKEND_METRICS_REQUIREMENTS.md](docs/backend/BACKEND_METRICS_REQUIREMENTS.md)
- Check example implementations in [examples/](examples/) directory

---

## 📄 License

Proprietary - GatewayZ Network

---

**GatewayZ Observability Stack** · Production-ready monitoring for AI infrastructure · Deployed on Railway
