# Provider Management Dashboard

This guide explains the Provider Management dashboard and how it integrates with your GatewayZ backend API to display real-time provider metrics.

## Overview

The Provider Management dashboard provides comprehensive visibility into all your LLM providers, their health status, performance metrics, and capabilities. It automatically fetches data from your backend API endpoints and displays them in interactive visualizations.

## Architecture

```
GatewayZ Backend API
    ├─ /providers (get all providers)
    └─ /providers/stats (get provider statistics)
         ↓
Provider Metrics Exporter (Python service)
    ├─ Fetches provider data every 60 seconds
    └─ Exposes as Prometheus metrics
         ↓
Prometheus (scrapes metrics every 60 seconds)
         ↓
Grafana (queries and visualizes)
         ↓
Provider Management Dashboard
```

## Components

### 1. Provider Metrics Exporter Service

**File:** `examples/provider-metrics-exporter.py`

A Python service that:
- Fetches provider data from your GatewayZ backend API
- Converts JSON responses to Prometheus metrics format
- Exposes metrics on port 8001 at `/metrics` endpoint
- Runs every 60 seconds (configurable)

**Environment Variables:**
```bash
GATEWAY_API_URL=https://api.gatewayz.ai          # Your backend API URL
ADMIN_KEY=gw_live_wTfpLJ5VB28qMXpOAhr7Uw        # Admin API key
SCRAPE_INTERVAL=60                                # Fetch interval in seconds
METRICS_PORT=8001                                 # Metrics server port
```

**Metrics Exposed:**
- `gatewayz_providers_total` - Total number of providers
- `gatewayz_providers_active` - Number of active providers
- `gatewayz_providers_inactive` - Number of inactive providers
- `gatewayz_providers_healthy` - Number of healthy providers
- `gatewayz_providers_degraded` - Number of degraded providers
- `gatewayz_providers_down` - Number of down providers
- `gatewayz_providers_unknown` - Number of providers with unknown status
- `gatewayz_provider_response_time_ms` - Average response time per provider
- `gatewayz_provider_supports_streaming` - Streaming capability (1=yes, 0=no)
- `gatewayz_provider_supports_function_calling` - Function calling capability
- `gatewayz_provider_supports_vision` - Vision capability
- `gatewayz_provider_supports_image_generation` - Image generation capability
- `gatewayz_provider_is_active` - Provider active status (1=yes, 0=no)
- `gatewayz_provider_health_status` - Health status code (0=unknown, 1=healthy, 2=degraded, 3=down)
- `gatewayz_provider_metrics_last_update` - Last successful update timestamp
- `gatewayz_provider_scrape_errors_total` - Total scrape errors

### 2. Prometheus Configuration

**File:** `prometheus/prom.yml`

Added scrape job:
```yaml
- job_name: 'provider_metrics'
  scheme: http
  metrics_path: '/metrics'
  static_configs:
    - targets: ['provider-metrics-exporter:8001']
  scrape_interval: 60s
  scrape_timeout: 10s
```

### 3. Docker Compose Service

**File:** `docker-compose.yml`

```yaml
provider-metrics-exporter:
  build:
    context: ./examples
    dockerfile: provider-exporter-Dockerfile
  ports:
    - "8001:8001"
  environment:
    GATEWAY_API_URL: ${GATEWAY_API_URL:-https://api.gatewayz.ai}
    ADMIN_KEY: ${ADMIN_KEY:-gw_live_wTfpLJ5VB28qMXpOAhr7Uw}
    SCRAPE_INTERVAL: ${PROVIDER_SCRAPE_INTERVAL:-60}
    METRICS_PORT: 8001
  depends_on:
    - prometheus
  restart: unless-stopped
```

### 4. Grafana Dashboard

**File:** `grafana/dashboards/gatewayz-provider-management.json`

Comprehensive dashboard with the following sections:

#### Provider Statistics Overview
- **Total Providers** - Total count of all providers
- **Active Providers** - Count of active providers (green)
- **Inactive Providers** - Count of inactive providers (orange)
- **Healthy Providers** - Count of healthy providers (green)

#### Provider Health Status
- **Providers by Health Status** - Pie chart showing distribution of healthy, degraded, down, and unknown providers
- **Providers by Active Status** - Pie chart showing active vs inactive distribution

#### Provider Performance Metrics
- **Average Response Time by Provider** - Time series graph showing response time trends for each provider

#### Provider Capabilities
- **Streaming Support** - Pie chart showing providers with/without streaming
- **Function Calling Support** - Pie chart showing providers with/without function calling
- **Vision Support** - Pie chart showing providers with/without vision capabilities
- **Image Generation Support** - Pie chart showing providers with/without image generation

#### Provider Details Table
- **All Providers** - Detailed table with columns:
  - Provider Name
  - Health Status
  - Active Status
  - Response Time (ms)
  - Last Health Check
  - Capabilities (streaming, function calling, vision, image generation)

## Usage

### Local Development

1. **Start the stack:**
```bash
docker-compose up -d
```

2. **Verify the provider metrics exporter is running:**
```bash
curl http://localhost:8001/metrics | grep gatewayz_providers
```

3. **Access Grafana:**
- URL: http://localhost:3000
- Username: admin
- Password: yourpassword123

4. **Open the Provider Management dashboard:**
- Click Dashboards → GatewayZ Provider Management

### Railway Deployment

1. **Set environment variables in Railway:**
```
GATEWAY_API_URL=https://api.gatewayz.ai
ADMIN_KEY=gw_live_wTfpLJ5VB28qMXpOAhr7Uw
PROVIDER_SCRAPE_INTERVAL=60
```

2. **Deploy:**
```bash
git push origin feat/application-health-dashboard
```

3. **Verify metrics are being scraped:**
- Go to Prometheus → Targets
- Look for `provider_metrics` job
- Should show status "UP" in green

4. **Access the dashboard:**
- Open Grafana
- Navigate to Provider Management dashboard

## Troubleshooting

### Provider Metrics Not Appearing

**Check if the exporter is running:**
```bash
curl http://localhost:8001/metrics
```

**Check exporter logs:**
```bash
docker logs provider-metrics-exporter
```

**Verify API connectivity:**
```bash
curl -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" https://api.gatewayz.ai/providers
```

**Check Prometheus scrape status:**
- Go to Prometheus UI at http://localhost:9090
- Click Status → Targets
- Look for `provider_metrics` job
- Check for any error messages

### Dashboard Shows "No Data"

1. **Wait for initial scrape:** The exporter needs 60+ seconds to fetch data on first run
2. **Check time range:** Make sure dashboard time range includes recent data (default: last 6 hours)
3. **Verify providers exist:** Check if your backend has any providers configured
4. **Check Prometheus data:** Query `gatewayz_providers_total` in Prometheus Explore

### Admin Key Issues

If you get 401 errors:
1. Verify the `ADMIN_KEY` environment variable is set correctly
2. Check the key hasn't expired
3. Ensure the key has provider management permissions

## API Endpoints Reference

### GET /providers

Returns list of all providers with detailed information.

**Response:**
```json
[
  {
    "name": "OpenAI",
    "slug": "openai",
    "description": "OpenAI API provider",
    "base_url": "https://api.openai.com",
    "is_active": true,
    "health_status": "healthy",
    "average_response_time_ms": 250,
    "supports_streaming": true,
    "supports_function_calling": true,
    "supports_vision": true,
    "supports_image_generation": false,
    "last_health_check_at": "2025-12-17T04:09:11.817Z",
    "created_at": "2025-12-17T04:09:11.817Z",
    "updated_at": "2025-12-17T04:09:11.817Z"
  }
]
```

### GET /providers/stats

Returns aggregated statistics about all providers.

**Response:**
```json
{
  "total": 5,
  "active": 4,
  "inactive": 1,
  "healthy": 4,
  "degraded": 0,
  "down": 0,
  "unknown": 1
}
```

## Customization

### Changing Scrape Interval

Edit `docker-compose.yml`:
```yaml
environment:
  PROVIDER_SCRAPE_INTERVAL: 120  # Change to 120 seconds
```

Or set environment variable:
```bash
export PROVIDER_SCRAPE_INTERVAL=120
docker-compose up -d
```

### Adding Custom Metrics

Edit `examples/provider-metrics-exporter.py` to add new metrics:

```python
custom_metric = Gauge(
    'gatewayz_provider_custom_metric',
    'Custom metric description',
    ['provider']
)

# In update_metrics() function:
custom_metric.labels(provider=slug).set(value)
```

### Modifying Dashboard

1. Open Grafana
2. Go to Provider Management dashboard
3. Click Edit (pencil icon)
4. Modify panels as needed
5. Save dashboard

## Performance Considerations

- **Scrape Interval:** Default 60 seconds. Reduce for more frequent updates, increase to save resources
- **Data Retention:** Prometheus default is 15 days. Configure in `prometheus/prom.yml`
- **Dashboard Refresh:** Default 30 seconds. Adjust in dashboard settings

## Next Steps

1. ✅ Deploy provider metrics exporter
2. ✅ Verify metrics are being scraped
3. ✅ Access Provider Management dashboard
4. 📊 Create custom alerts based on provider health
5. 🔔 Set up notifications for provider status changes
6. 📈 Add more custom metrics as needed

## Resources

- [Prometheus Metrics Documentation](https://prometheus.io/docs/concepts/data_model/)
- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
- [GatewayZ API Documentation](https://api.gatewayz.ai/docs)

---

**Questions or Issues?**
- Check the troubleshooting section above
- Review service logs: `docker-compose logs provider-metrics-exporter`
- Verify API connectivity and credentials
