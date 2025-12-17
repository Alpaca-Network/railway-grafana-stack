# Provider Management Endpoints Integration Guide

This document describes the new Provider Management endpoints and how they integrate with the Prometheus, Grafana, Loki, and Tempo observability stack.

## Overview

The Provider Management system exposes two REST API endpoints that provide real-time provider health, status, and capability information. These endpoints are scraped by a metrics exporter service that converts the data into Prometheus metrics, which are then visualized in Grafana dashboards.

## Endpoints

### 1. GET /providers

**Purpose:** Retrieve a complete list of all providers with detailed information.

**Authentication:** Bearer token in `Authorization` header

**Request:**
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://api.gatewayz.ai/providers
```

**Response:** Array of provider objects

**Expected Payload:**
```json
[
  {
    "id": 1,
    "name": "OpenAI",
    "slug": "openai",
    "description": "OpenAI API provider for GPT models",
    "base_url": "https://api.openai.com",
    "api_key_env_var": "OPENAI_API_KEY",
    "logo_url": "https://example.com/openai-logo.png",
    "site_url": "https://openai.com",
    "privacy_policy_url": "https://openai.com/privacy",
    "terms_of_service_url": "https://openai.com/terms",
    "status_page_url": "https://status.openai.com",
    "is_active": true,
    "supports_streaming": true,
    "supports_function_calling": true,
    "supports_vision": true,
    "supports_image_generation": false,
    "metadata": {
      "rate_limit": 3500,
      "max_tokens": 128000,
      "supported_models": ["gpt-4", "gpt-3.5-turbo"]
    },
    "average_response_time_ms": 245,
    "health_status": "healthy",
    "last_health_check_at": "2025-12-17T04:09:11.817Z",
    "created_at": "2025-12-17T04:09:11.817Z",
    "updated_at": "2025-12-17T04:09:11.817Z"
  },
  {
    "id": 2,
    "name": "Anthropic",
    "slug": "anthropic",
    "description": "Anthropic Claude API provider",
    "base_url": "https://api.anthropic.com",
    "api_key_env_var": "ANTHROPIC_API_KEY",
    "logo_url": "https://example.com/anthropic-logo.png",
    "site_url": "https://anthropic.com",
    "privacy_policy_url": "https://anthropic.com/privacy",
    "terms_of_service_url": "https://anthropic.com/terms",
    "status_page_url": "https://status.anthropic.com",
    "is_active": true,
    "supports_streaming": true,
    "supports_function_calling": true,
    "supports_vision": true,
    "supports_image_generation": false,
    "metadata": {
      "rate_limit": 50000,
      "max_tokens": 200000
    },
    "average_response_time_ms": 320,
    "health_status": "healthy",
    "last_health_check_at": "2025-12-17T04:08:45.123Z",
    "created_at": "2025-12-17T04:09:11.817Z",
    "updated_at": "2025-12-17T04:09:11.817Z"
  }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique provider identifier |
| `name` | string | Human-readable provider name (e.g., "OpenAI") |
| `slug` | string | URL-friendly identifier (e.g., "openai") |
| `description` | string | Provider description |
| `base_url` | string | Provider's API base URL |
| `api_key_env_var` | string | Environment variable name for API key |
| `logo_url` | string | URL to provider's logo |
| `site_url` | string | Provider's website URL |
| `privacy_policy_url` | string | Link to privacy policy |
| `terms_of_service_url` | string | Link to terms of service |
| `status_page_url` | string | Link to status page |
| `is_active` | boolean | Whether provider is currently active |
| `supports_streaming` | boolean | Whether provider supports streaming responses |
| `supports_function_calling` | boolean | Whether provider supports function calling |
| `supports_vision` | boolean | Whether provider supports vision/image input |
| `supports_image_generation` | boolean | Whether provider supports image generation |
| `metadata` | object | Additional provider-specific metadata |
| `average_response_time_ms` | number | Average response time in milliseconds |
| `health_status` | string | Current health status: "healthy", "degraded", "down", "unknown" |
| `last_health_check_at` | string | ISO 8601 timestamp of last health check |
| `created_at` | string | ISO 8601 timestamp of creation |
| `updated_at` | string | ISO 8601 timestamp of last update |

---

### 2. GET /providers/stats

**Purpose:** Retrieve aggregated statistics about all providers.

**Authentication:** Bearer token in `Authorization` header

**Request:**
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://api.gatewayz.ai/providers/stats
```

**Response:** Statistics object

**Expected Payload:**
```json
{
  "total": 5,
  "active": 4,
  "inactive": 1,
  "healthy": 3,
  "degraded": 1,
  "down": 1,
  "unknown": 0
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of providers |
| `active` | integer | Number of active providers |
| `inactive` | integer | Number of inactive providers |
| `healthy` | integer | Number of healthy providers |
| `degraded` | integer | Number of degraded providers |
| `down` | integer | Number of down providers |
| `unknown` | integer | Number of providers with unknown status |

---

## Prometheus Metrics Conversion

The `provider-metrics-exporter.py` service converts the REST API responses into Prometheus metrics. These metrics are scraped by Prometheus every 60 seconds.

### Generated Metrics

**Gauge Metrics (Aggregate):**
```
gatewayz_providers_total{} = 5
gatewayz_providers_active{} = 4
gatewayz_providers_inactive{} = 1
gatewayz_providers_healthy{} = 3
gatewayz_providers_degraded{} = 1
gatewayz_providers_down{} = 1
gatewayz_providers_unknown{} = 0
```

**Gauge Metrics (Per-Provider):**
```
gatewayz_provider_response_time_ms{provider="openai"} = 245
gatewayz_provider_response_time_ms{provider="anthropic"} = 320

gatewayz_provider_is_active{provider="openai"} = 1
gatewayz_provider_is_active{provider="anthropic"} = 1
gatewayz_provider_is_active{provider="mistral"} = 0

gatewayz_provider_health_status{provider="openai"} = 1
gatewayz_provider_health_status{provider="anthropic"} = 1
gatewayz_provider_health_status{provider="google"} = 2
gatewayz_provider_health_status{provider="mistral"} = 3

gatewayz_provider_supports_streaming{provider="openai"} = 1
gatewayz_provider_supports_function_calling{provider="openai"} = 1
gatewayz_provider_supports_vision{provider="openai"} = 1
gatewayz_provider_supports_image_generation{provider="openai"} = 0
```

**Health Status Codes:**
- `0` = unknown
- `1` = healthy
- `2` = degraded
- `3` = down

---

## Integration with Observability Stack

### Prometheus

**Scrape Configuration** (`prometheus/prom.yml`):
```yaml
- job_name: 'provider_metrics'
  scheme: http
  metrics_path: '/metrics'
  static_configs:
    - targets: ['provider-metrics-exporter:8001']
  scrape_interval: 60s
  scrape_timeout: 10s
```

**Scrape Behavior:**
- Prometheus scrapes the exporter every 60 seconds
- Exporter fetches from `/providers` and `/providers/stats` endpoints
- Metrics are stored in Prometheus TSDB with 15-day retention (default)

### Grafana

**Dashboard:** `gatewayz-provider-management.json`

**Panels:**
1. **Statistics Overview** - Stat panels showing total, active, inactive, healthy counts
2. **Health Status Distribution** - Pie chart of health status breakdown
3. **Active Status Distribution** - Pie chart of active vs inactive
4. **Response Time Trends** - Time series graph of provider response times
5. **Capability Distribution** - Pie charts for streaming, function calling, vision, image generation
6. **Provider Details Table** - Table with all provider information

**Data Source:** Prometheus

**Queries:**
```promql
# Total providers
gatewayz_providers_total

# Active providers
gatewayz_providers_active

# Provider response times
gatewayz_provider_response_time_ms

# Health status by provider
gatewayz_provider_health_status

# Capability support
gatewayz_provider_supports_streaming
gatewayz_provider_supports_function_calling
gatewayz_provider_supports_vision
gatewayz_provider_supports_image_generation
```

### Loki (Optional)

Provider metrics can be correlated with logs if the exporter service sends structured logs to Loki:

**Log Format:**
```json
{
  "timestamp": "2025-12-17T04:09:11.817Z",
  "level": "info",
  "service": "provider-metrics-exporter",
  "message": "Updated provider metrics",
  "providers_total": 5,
  "providers_active": 4,
  "providers_healthy": 3,
  "trace_id": "abc123def456"
}
```

**Loki Query:**
```logql
{service="provider-metrics-exporter"} | json | providers_total > 0
```

### Tempo (Optional)

Provider metrics exporter can send distributed traces to Tempo for performance analysis:

**Instrumentation Points:**
- API request to `/providers` endpoint
- API request to `/providers/stats` endpoint
- Metrics conversion and aggregation
- Prometheus scrape response

**Trace Attributes:**
```
service.name: "provider-metrics-exporter"
http.method: "GET"
http.url: "https://api.gatewayz.ai/providers"
http.status_code: 200
duration_ms: 245
provider_count: 5
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GatewayZ Backend API                      │
│  ┌──────────────────┐          ┌──────────────────────┐     │
│  │ GET /providers   │          │ GET /providers/stats │     │
│  │ (returns array)  │          │ (returns stats)      │     │
│  └──────────────────┘          └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│         Provider Metrics Exporter Service (Railway)          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Fetches /providers and /providers/stats every 60s      │ │
│  │ Converts JSON to Prometheus metrics format             │ │
│  │ Exposes metrics on :8001/metrics                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│              Prometheus (Railway)                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Scrapes provider-metrics-exporter:8001/metrics         │ │
│  │ Stores metrics in TSDB (15-day retention)              │ │
│  │ Exposes metrics API on :9090                           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────┐
│              Grafana (Railway)                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Provider Management Dashboard                          │ │
│  │ ├─ Statistics Overview                                 │ │
│  │ ├─ Health Status Distribution                          │ │
│  │ ├─ Response Time Trends                                │ │
│  │ ├─ Capability Distribution                             │ │
│  │ └─ Provider Details Table                              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

**Provider Metrics Exporter:**
```bash
GATEWAY_API_URL=https://api.gatewayz.ai
ADMIN_KEY=gw_live_wTfpLJ5VB28qMXpOAhr7Uw
SCRAPE_INTERVAL=60
METRICS_PORT=8001
```

---

## Error Handling

**API Errors:**
- 401 Unauthorized: Invalid or expired admin key
- 502 Bad Gateway: Backend service unavailable
- 503 Service Unavailable: Temporary service issue

**Metrics Exporter Errors:**
- Failed API requests increment `gatewayz_provider_scrape_errors_total` counter
- Exporter continues running and retries on next interval
- Check logs for detailed error messages

---

## Testing

**Test Backend Connectivity:**
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  https://api.gatewayz.ai/providers/stats
```

**Test Metrics Exporter:**
```bash
curl http://provider-metrics-exporter:8001/metrics | grep gatewayz_providers
```

**Test Prometheus Scraping:**
```bash
curl 'http://prometheus:9090/api/v1/query?query=gatewayz_providers_total'
```

**Test Grafana Dashboard:**
1. Navigate to Grafana
2. Go to Dashboards → GatewayZ Provider Management
3. Verify metrics are displayed

---

## Troubleshooting

### No Data in Dashboard

1. **Check API connectivity:**
   ```bash
   curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
     https://api.gatewayz.ai/providers/stats
   ```

2. **Check exporter logs:**
   ```bash
   docker logs provider-metrics-exporter
   ```

3. **Check Prometheus targets:**
   - Go to Prometheus UI → Status → Targets
   - Look for `provider_metrics` job
   - Verify health status is "UP"

4. **Check metrics in Prometheus:**
   ```bash
   curl 'http://prometheus:9090/api/v1/query?query=gatewayz_providers_total'
   ```

### Stale Data

- Exporter scrape interval is 60 seconds
- Prometheus scrape interval is 60 seconds
- Dashboard refresh interval is 30 seconds
- Allow 2+ minutes for new data to appear

### Authentication Errors

- Verify admin key is correct
- Check key hasn't expired
- Ensure key has provider management permissions

---

## Next Steps

1. ✅ Deploy provider metrics exporter to Railway
2. ✅ Configure Prometheus scraping
3. ✅ Create Grafana dashboard
4. 📊 Add test providers to backend
5. 🔔 Set up alerts for provider health
6. 📱 Configure notifications (Slack, email, etc.)
7. 🔐 Implement RBAC for dashboard access

---

## References

- [Prometheus Metrics Documentation](https://prometheus.io/docs/concepts/data_model/)
- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
- [GatewayZ API Documentation](https://api.gatewayz.ai/docs)
- [Provider Management Dashboard](./PROVIDER_MANAGEMENT_DASHBOARD.md)
