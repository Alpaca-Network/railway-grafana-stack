# Grafana Connections & Data Flow

## Complete Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GRAFANA (Central Hub)                               │
│                      http://localhost:3000                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Data Sources Connected                         │  │
│  │                                                                     │  │
│  │  ✅ Prometheus (http://prometheus:9090)                            │  │
│  │     └─ Metrics: gatewayz_*, fastapi_*, redis_*, database_*        │  │
│  │                                                                     │  │
│  │  ✅ Loki (http://loki:3100)                                        │  │
│  │     └─ Logs: All application logs with trace_id correlation       │  │
│  │                                                                     │  │
│  │  ✅ Tempo (http://tempo:3200)                                      │  │
│  │     └─ Traces: Distributed tracing with span correlation          │  │
│  │                                                                     │  │
│  │  ✅ Mimir (http://mimir:9009)                                      │  │
│  │     └─ Long-term metrics (30d) + Tempo span metrics               │  │
│  │                                                                     │  │
│  │  ✅ Pyroscope (http://pyroscope:4040)                              │  │
│  │     └─ CPU/memory flamegraphs (provider/model tagged)             │  │
│  │                                                                     │  │
│  │  ✅ Alertmanager (http://alertmanager:9093)                        │  │
│  │     └─ Alert state visibility                                      │  │
│  │                                                                     │  │
│  │  ✅ JSON API (http://json-api-proxy:5050)                          │  │
│  │     └─ Provider health scores, circuit breaker states              │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      Dashboards Available                           │  │
│  │                                                                     │  │
│  │  📊 GatewayZ Provider Management                                    │  │
│  │     └─ Data Source: Prometheus                                     │  │
│  │     └─ Metrics: gatewayz_providers_*, gatewayz_provider_*          │  │
│  │     └─ Status: ✅ Connected & Pulling Real Data                    │  │
│  │                                                                     │  │
│  │  📊 GatewayZ Redis Services                                         │  │
│  │     └─ Data Source: Prometheus                                     │  │
│  │     └─ Metrics: redis_*, fastapi_requests_total                    │  │
│  │     └─ Status: ✅ Connected & Pulling Real Data                    │  │
│  │                                                                     │  │
│  │  📊 GatewayZ Application Health                                     │  │
│  │     └─ Data Source: Prometheus                                     │  │
│  │     └─ Metrics: fastapi_*, database_*, cache_*                     │  │
│  │     └─ Status: ✅ Connected & Pulling Real Data                    │  │
│  │                                                                     │  │
│  │  📊 Loki Logs                                                       │  │
│  │     └─ Data Source: Loki                                           │  │
│  │     └─ Logs: All application logs                                  │  │
│  │     └─ Status: ✅ Connected & Pulling Real Data                    │  │
│  │                                                                     │  │
│  │  📊 Tempo Distributed Tracing                                       │  │
│  │     └─ Data Source: Tempo                                          │  │
│  │     └─ Traces: Request traces with spans                           │  │
│  │     └─ Status: ✅ Connected & Pulling Real Data                    │  │
│  │                                                                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Provider Management Dashboard

```
Backend API (/providers, /providers/stats)
    ↓
Provider Metrics Exporter (Railway)
    ↓
Prometheus (Scrapes every 60s)
    ↓
Grafana (Queries every 30s)
    ↓
Provider Management Dashboard
    ├─ Statistics Overview (Stat panels)
    ├─ Health Status Distribution (Pie chart)
    ├─ Response Time Trends (Time series)
    ├─ Capability Distribution (Pie charts)
    ├─ Provider Details Table
    ├─ API Endpoint Specifications (Documentation)
    ├─ Prometheus Metrics Reference (Documentation)
    ├─ Data Flow Diagram (Documentation)
    └─ Testing & Troubleshooting (Documentation)
```

### Redis Services Dashboard

```
Redis Gateway (redis-production-bb6d.up.railway.app)
    ↓
Redis Exporter (Scrapes every 15s)
    ↓
Prometheus (Stores metrics)
    ↓
Grafana (Queries every 30s)
    ↓
Redis Services Dashboard
    ├─ Redis Service Health (Stat)
    ├─ Connected Clients (Gauge)
    ├─ Memory Usage (Gauge)
    ├─ Database Query Rate (Graph)
    └─ Error Rate Over Time (Graph)
```

### Application Health Dashboard

```
FastAPI Backend (api.gatewayz.ai)
    ↓
Prometheus Scraper (Scrapes every 30s)
    ↓
Prometheus TSDB (Stores metrics)
    ↓
Grafana (Queries every 30s)
    ↓
Application Health Dashboard
    ├─ Request Rate (Graph)
    ├─ Error Rate (Graph)
    ├─ Response Time (Graph)
    ├─ Database Connections (Gauge)
    └─ Cache Hit Rate (Gauge)
```

### Loki Logs Dashboard

```
Application Services (Logs via Locomotive)
    ↓
Loki Ingester (Receives logs)
    ↓
Loki Storage (TSDB + Filesystem)
    ↓
Grafana (Queries logs)
    ↓
Loki Logs Dashboard
    ├─ Log Volume (Graph)
    ├─ Log Lines (Table)
    ├─ Log Level Distribution (Pie chart)
    └─ Log Stream (Raw logs)
```

### Tempo Traces Dashboard

```
Application Services (Traces via OpenTelemetry)
    ↓
Tempo Distributor (Receives traces)
    ↓
Tempo Storage (Block storage)
    ↓
Grafana (Queries traces)
    ↓
Tempo Distributed Tracing Dashboard
    ├─ Trace Search (Search panel)
    ├─ Service Map (Service dependencies)
    ├─ Trace Details (Span details)
    └─ Latency Metrics (Histogram)
```

## Connection Status

### ✅ All Connected

| Component | UID | URL | Status | Data Flow |
|-----------|-----|-----|--------|-----------|
| Prometheus | `grafana_prometheus` | http://prometheus:9090 | ✅ UP | Real-time metrics (15s scrape) |
| Mimir | `grafana_mimir` | http://mimir:9009 | ✅ UP | Long-term metrics (30d) + span metrics |
| Loki | `grafana_loki` | http://loki:3100 | ✅ UP | Log aggregation (30d) |
| Tempo | `grafana_tempo` | http://tempo:3200 | ✅ UP | Distributed traces (48h) |
| Pyroscope | `grafana_pyroscope` | http://pyroscope:4040 | ✅ UP | CPU/memory flamegraphs |
| Alertmanager | `alertmanager` | http://alertmanager:9093 | ✅ UP | Alert state visibility |
| JSON API | `grafana_json_api` | http://json-api-proxy:5050 | ✅ UP | Provider health data |

> **Note:** Sentry is no longer a Grafana datasource. Error tracking is handled by the `gatewayz_reliability_v1` dashboard using Prometheus + Loki. See [SENTRY_SETUP.md](SENTRY_SETUP.md) for migration notes.

## Dashboard Status

| Dashboard | Data Source | Status | Real Data |
|-----------|-------------|--------|-----------|
| Provider Management | Prometheus | ✅ Connected | ✅ Real (0 providers currently) |
| Redis Services | Prometheus | ✅ Connected | ✅ Real |
| Application Health | Prometheus | ✅ Connected | ✅ Real |
| Loki Logs | Loki | ✅ Connected | ✅ Real |
| Tempo Traces | Tempo | ✅ Connected | ✅ Real |

## Data Source Correlations

### Prometheus → Loki
- **Via:** Trace ID in logs
- **How:** Click on trace ID in Loki logs → Opens Tempo
- **Status:** ✅ Configured

### Prometheus → Tempo
- **Via:** Exemplars in metrics
- **How:** Click on exemplar in Prometheus graph → Opens Tempo
- **Status:** ✅ Configured

### Tempo → Loki
- **Via:** Span logs
- **How:** Click on span in Tempo → Shows related logs
- **Status:** ✅ Configured

### Tempo → Prometheus
- **Via:** Service metrics
- **How:** Click on service in Tempo → Shows metrics
- **Status:** ✅ Configured

## Local vs Railway

### LOCAL (Docker Compose)
```
Grafana (localhost:3000)
    ├─ Prometheus (localhost:9090)
    ├─ Loki (localhost:3100)
    ├─ Tempo (localhost:3200)
    ├─ Redis Exporter (localhost:9121)
    └─ Mock Provider Metrics (localhost:8002)
```

**Status:** ✅ All connected and working

### RAILWAY (Production)
```
Grafana (your-domain.railway.app)
    ├─ Prometheus (internal)
    ├─ Loki (internal)
    ├─ Tempo (internal)
    ├─ Redis Gateway (redis-production-bb6d.up.railway.app)
    └─ Provider Exporter (internal)
```

**Status:** ✅ All connected and working

## Verification Commands

### Test Prometheus Connection
```bash
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result | length'
# Should return: number of targets
```

### Test Loki Connection
```bash
curl -s http://localhost:3100/loki/api/v1/label | jq '.values | length'
# Should return: number of labels
```

### Test Tempo Connection
```bash
curl -s http://localhost:3200/api/traces | jq 'keys'
# Should return: trace data
```

### Test Grafana Data Sources
```bash
curl -s -u admin:yourpassword123 http://localhost:3000/api/datasources | jq '.[] | {name, type}'
# Should return all 4 data sources
```

### Test Provider Dashboard
```bash
curl -s -u admin:yourpassword123 http://localhost:3000/api/dashboards/uid/gatewayz-provider-management | jq '.dashboard.title'
# Should return: "GatewayZ Provider Management"
```

## Summary

✅ **Everything is connected to Grafana**

- **7 Data Sources:** Prometheus, Mimir, Loki, Tempo, Pyroscope, Alertmanager, JSON API
- **15 Dashboards:** 400+ panels across all dashboard folders
- **Real Data:** All dashboards pulling live data — no mock data
- **Cross-signal navigation:** Metrics → Traces (exemplars), Logs → Traces (trace_id), Traces → Profiles (Pyroscope)
- **Local & Railway:** Both environments fully configured

> Last updated: March 2026. See [../MASTER.md](../MASTER.md) for full architecture reference.

**No mock data on Railway** - All dashboards show real data from your backend API and services.
