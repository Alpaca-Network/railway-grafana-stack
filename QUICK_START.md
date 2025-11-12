# Quick Start Guide - FastAPI with Observability

## Local Development (Docker)

### Start Everything
```bash
docker compose up -d
```

### Generate Test Traffic
```bash
# Basic requests
for i in {1..20}; do curl http://localhost:8000/hello?name=User$i; sleep 0.5; done

# Test slow endpoint (for latency metrics)
curl http://localhost:8000/slow

# Test error tracking
curl http://localhost:8000/error
```

### Access Services
- **FastAPI App**: http://localhost:8000
- **Grafana**: http://localhost:3000 (admin/yourpassword123)
- **Prometheus**: http://localhost:9090
- **Tempo**: http://localhost:3200
- **Loki**: http://localhost:3100

### Import FastAPI Dashboard in Grafana
1. Go to http://localhost:3000
2. Navigate to **Dashboards → Import**
3. Enter Dashboard ID: **16110**
4. Select datasources:
   - Prometheus: `grafana_prometheus`
   - Tempo: `grafana_tempo`
   - Loki: `grafana_loki`
5. Click **Import**
6. Select **"fastapi-app"** from the app_name dropdown

## Railway Deployment

### Quick Deploy Your FastAPI App

1. **Create a new Railway service**
2. **Connect your GitHub repo**
3. **Set root directory**: `/examples/fastapi-app`
4. **Add environment variables**:
```bash
SERVICE_NAME=fastapi-app
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
```

5. **Deploy** - Railway handles the rest!

### Verify Deployment
```bash
# Check health
curl https://your-app.railway.app/health

# Check metrics
curl https://your-app.railway.app/metrics | grep app_name

# Expected output:
# fastapi_app_info{app_name="fastapi-app"} 1.0
```

## Key Concepts

### The Critical Metric
For the dashboard to work, your app MUST expose:
```python
APP_INFO = Info('fastapi_app', 'FastAPI application info')
APP_INFO.info({'app_name': 'your-service-name'})
```

### Environment Variables

**Local (Docker)**:
- Auto-configured via docker-compose.yml
- Uses service names: `http://tempo:4318`

**Railway**:
- Use Railway variable references: `${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}`
- Automatically resolves to internal URLs

### Observability Stack

Your app sends:
1. **Metrics** → Prometheus (via `/metrics` endpoint)
2. **Traces** → Tempo (via OpenTelemetry OTLP)
3. **Logs** → Loki (via Locomotive or log drivers)

Grafana queries all three and correlates them!

## Troubleshooting

### App name not showing?
```bash
# Check the metric exists
curl localhost:8000/metrics | grep fastapi_app_info

# Should see:
# fastapi_app_info{app_name="fastapi-app"} 1.0
```

### No traces in Tempo?
```bash
# Check TEMPO_URL is set
docker exec repo-fastapi_app-1 env | grep TEMPO

# Should see:
# TEMPO_URL=http://tempo:4318
```

### Metrics not in Prometheus?
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | grep fastapi

# Or visit: http://localhost:9090/targets
```

## Adding Your Own App

### 1. Add OpenTelemetry
```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint=f"{os.getenv('TEMPO_URL')}/v1/traces"
)
```

### 2. Add Prometheus Metrics
```python
from prometheus_client import Info, Counter

# Required for dashboard
APP_INFO = Info('fastapi_app', 'App info')
APP_INFO.info({'app_name': 'my-app'})

# Your custom metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests')
```

### 3. Expose Metrics Endpoint
```python
from prometheus_client import generate_latest

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 4. Update Prometheus Config
Add to `prometheus/prom.yml`:
```yaml
- job_name: 'my-app'
  static_configs:
    - targets: ['my-app:8000']
```

### 5. Deploy!
```bash
docker compose up -d
# or
railway up
```

## File Structure

```
/examples/fastapi-app/
├── main.py              # FastAPI app with instrumentation
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container build
└── railway.json        # Railway configuration

/grafana/
├── datasources/        # Prometheus, Loki, Tempo configs
└── dashboards/         # Pre-configured dashboards

/prometheus/
└── prom.yml           # Scrape configuration

/tempo/
└── tempo.yml          # Tracing configuration

/loki/
└── loki.yml           # Log aggregation config
```

## Next Steps

1. ✅ Start the stack: `docker compose up -d`
2. ✅ Import dashboard (ID: 16110) in Grafana
3. ✅ Generate traffic to your app
4. ✅ Explore metrics, traces, and logs
5. 📊 Create custom dashboards
6. 🚨 Set up alerts in Prometheus
7. 🚂 Deploy to Railway

## Resources

- **Full Railway Guide**: See `RAILWAY_SETUP.md`
- **FastAPI Dashboard**: https://grafana.com/grafana/dashboards/16110
- **OpenTelemetry Docs**: https://opentelemetry.io/docs/languages/python/
- **Example Code**: `/examples/fastapi-app/main.py`

---

**Need help?** Check the troubleshooting section in `RAILWAY_SETUP.md` or review the example implementations in `/examples/`.
