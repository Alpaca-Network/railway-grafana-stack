# 📖 GatewayZ Backend Monitoring - Complete Guide

**Document Purpose**: Comprehensive guide for monitoring GatewayZ backend providers with real-time health tracking, performance analytics, and automated anomaly detection.

---

## 📊 Overview

The GatewayZ Backend Monitoring system provides comprehensive visibility into 17+ provider backends, tracking health scores, performance metrics, costs, and anomalies in real-time.

### Key Features

- **Real-time Health Monitoring**: Health scores (0-100) for all providers
- **Anomaly Detection**: Automatic detection of cost spikes, latency issues, and error rate anomalies
- **Cost Analysis**: Provider cost breakdown and trends
- **Performance Trends**: Request volume, latency, and error rates over time
- **Interactive Dashboard**: Embedded Grafana dashboard with comprehensive analytics
- **Alert System**: Severity-based alerts (WARNING, CRITICAL)

---

## 🌐 Monitoring Endpoints

### Base URL
```
https://api.gatewayz.ai/api/monitoring
```

### Authentication
All monitoring endpoints require Bearer token authentication:
```bash
Authorization: Bearer YOUR_API_KEY
```

---

## 📋 Endpoint Specifications

### Tier 1: Core Monitoring Endpoints

#### 1. Health Endpoint
**GET** `/api/monitoring/health`

Returns real-time health status for all providers.

**Response:**
```json
{
  "providers": [
    {
      "provider": "openrouter",
      "health_score": 95,
      "status": "healthy",
      "requests": 15234,
      "errors": 23,
      "avg_latency": 245,
      "last_updated": "2025-12-28T10:30:00Z"
    },
    {
      "provider": "portkey",
      "health_score": 88,
      "status": "healthy",
      "requests": 12456,
      "errors": 145,
      "avg_latency": 312,
      "last_updated": "2025-12-28T10:30:00Z"
    },
    {
      "provider": "featherless",
      "health_score": 72,
      "status": "warning",
      "requests": 8923,
      "errors": 892,
      "avg_latency": 567,
      "last_updated": "2025-12-28T10:30:00Z"
    }
  ],
  "timestamp": "2025-12-28T10:30:00Z"
}
```

**Health Score Interpretation:**
- **80-100**: Healthy (✅ Green)
- **50-79**: Warning (⚠️ Yellow)
- **0-49**: Critical (🔴 Red)

---

#### 2. Real-time Stats Endpoint
**GET** `/api/monitoring/stats/realtime`

Returns real-time performance metrics for all providers.

**Response:**
```json
{
  "openrouter": {
    "requests_per_second": 45.32,
    "errors_per_second": 0.23,
    "cost_per_request": 0.000145,
    "p50_latency": 120,
    "p95_latency": 345,
    "p99_latency": 567,
    "total_cost_24h": 2345.67,
    "error_rate": 0.5
  },
  "portkey": {
    "requests_per_second": 32.15,
    "errors_per_second": 0.45,
    "cost_per_request": 0.000234,
    "p50_latency": 156,
    "p95_latency": 412,
    "p99_latency": 689,
    "total_cost_24h": 1876.54,
    "error_rate": 1.4
  },
  "timestamp": "2025-12-28T10:30:00Z"
}
```

---

#### 3. Latency Metrics Endpoint
**GET** `/api/monitoring/latency/{provider}/{model}`

Returns detailed latency percentiles for a specific provider/model combination.

**Example Request:**
```bash
GET /api/monitoring/latency/openrouter/gpt-4o-mini
```

**Response:**
```json
{
  "provider": "openrouter",
  "model": "gpt-4o-mini",
  "p50": 124,
  "p75": 234,
  "p95": 456,
  "p99": 678,
  "p999": 1234,
  "min": 45,
  "max": 2345,
  "mean": 234,
  "median": 124,
  "stddev": 145,
  "timestamp": "2025-12-28T10:30:00Z"
}
```

---

### Tier 2: Advanced Monitoring Endpoints

#### 4. Error Details Endpoint
**GET** `/api/monitoring/errors/{provider}`

Returns detailed error information for a provider.

**Response:**
```json
{
  "provider": "openrouter",
  "errors_24h": 234,
  "error_types": {
    "rate_limit": 45,
    "timeout": 23,
    "authentication": 8,
    "invalid_request": 12,
    "server_error": 146
  },
  "error_rate_percentage": 0.85,
  "top_error": "server_error",
  "error_trend": "decreasing",
  "timestamp": "2025-12-28T10:30:00Z"
}
```

---

#### 5. Anomalies Detection Endpoint
**GET** `/api/monitoring/anomalies`

Returns detected anomalies across all providers.

**Response:**
```json
{
  "anomalies": [
    {
      "provider": "featherless",
      "metric": "error_rate",
      "current_value": 25.5,
      "baseline_24h": 5.2,
      "deviation_percent": 390.4,
      "severity": "CRITICAL",
      "detected_at": "2025-12-28T10:15:00Z",
      "description": "Error rate 390% above 24h average"
    },
    {
      "provider": "chutes",
      "metric": "latency",
      "current_value": 1245,
      "baseline_24h": 456,
      "deviation_percent": 173.0,
      "severity": "WARNING",
      "detected_at": "2025-12-28T10:10:00Z",
      "description": "Latency 173% above 24h average"
    },
    {
      "provider": "deepinfra",
      "metric": "cost",
      "current_value": 2500.00,
      "baseline_24h": 890.50,
      "deviation_percent": 180.7,
      "severity": "WARNING",
      "detected_at": "2025-12-28T09:45:00Z",
      "description": "Cost 181% above 24h average"
    }
  ],
  "total_anomalies": 3,
  "critical_count": 1,
  "warning_count": 2,
  "timestamp": "2025-12-28T10:30:00Z"
}
```

---

#### 6. Cost Analysis Endpoint
**GET** `/api/monitoring/cost-analysis`

Returns detailed cost analysis across providers.

**Response:**
```json
{
  "total_cost_24h": 12456.78,
  "total_cost_7d": 87234.56,
  "total_cost_30d": 345678.90,
  "providers_by_cost": [
    {
      "provider": "openrouter",
      "cost_24h": 3456.78,
      "cost_per_request": 0.000145,
      "total_requests": 23000000,
      "cost_trend": "increasing",
      "percent_of_total": 27.7
    },
    {
      "provider": "portkey",
      "cost_24h": 2876.54,
      "cost_per_request": 0.000234,
      "total_requests": 12000000,
      "cost_trend": "stable",
      "percent_of_total": 23.1
    }
  ],
  "most_expensive": "openrouter",
  "most_efficient": "together",
  "average_cost_per_request": 0.000189,
  "timestamp": "2025-12-28T10:30:00Z"
}
```

---

### Tier 3: Optional Advanced Endpoints

#### 7. Trial Analytics
**GET** `/api/monitoring/trial-analytics`

Returns trial/free tier usage metrics.

---

#### 8. Token Efficiency
**GET** `/api/monitoring/token-efficiency/{provider}/{model}`

Returns token usage efficiency metrics for a specific model.

---

#### 9. Provider Comparison
**GET** `/api/monitoring/providers/comparison`

Comprehensive comparison across all providers.

---

## 🔌 Supported Providers & Models

### Provider List (17 Total)

| Provider | Slug | Status | Models |
|----------|------|--------|--------|
| OpenRouter | `openrouter` | ✅ Active | gpt-4o-mini, claude-sonnet-4-5, llama-2-70b |
| Portkey | `portkey` | ✅ Active | gpt-4o, gpt-3.5-turbo |
| Featherless | `featherless` | ✅ Active | mistral-large, neural-chat |
| Chutes | `chutes` | ✅ Active | gpt-4, gpt-3.5-turbo |
| DeepInfra | `deepinfra` | ✅ Active | llama-2-70b-chat, mistral-7b |
| Fireworks | `fireworks` | ✅ Active | llama-2-13b, accounts/fireworks/models/mixtral-8x7b |
| Together | `together` | ✅ Active | meta-llama/llama-2-70b, mistralai/Mistral-7B |
| Hugging Face | `huggingface` | ✅ Active | gpt2, distilbert-base |
| xAI | `xai` | ✅ Active | grok-1 |
| Aimo | `aimo` | ✅ Active | aimo-v1 |
| NEAR | `near` | ✅ Active | near-compute-engine |
| FAL | `fal` | ✅ Active | fal-models/llama |
| Anannas | `anannas` | ✅ Active | anannas-lm |
| Google Vertex | `google-vertex` | ✅ Active | palm-2, text-bison |
| ModelZ | `modelz` | ✅ Active | modelz-default |
| AIHubMix | `aihubmix` | ✅ Active | aihubmix-router |
| Vercel AI Gateway | `vercel-ai-gateway` | ✅ Active | vercel-gpt-4 |

---

## 🚨 Anomaly Detection System

### Detection Thresholds

The system automatically monitors for anomalies using these thresholds:

#### Cost Spike Detection
```
Threshold: >200% of 24-hour average
Severity: WARNING
Action: Alert on dashboard
```

**Example:**
- 24h average cost: $500
- Current cost: $1,200
- Deviation: 240% → **ALERT (WARNING)**

---

#### Latency Spike Detection
```
Threshold: >200% of 24-hour average
Severity: WARNING
Action: Alert on dashboard
```

**Example:**
- 24h average latency: 500ms
- Current latency: 1,200ms
- Deviation: 240% → **ALERT (WARNING)**

---

#### Error Rate Anomalies
```
WARNING Threshold: >10% error rate
CRITICAL Threshold: >25% error rate
Window: Last 24 hours
Granularity: Per-provider, hourly
```

**Severity Mapping:**
- **0-10%**: Healthy (✅)
- **10-25%**: Warning (⚠️)
- **>25%**: Critical (🔴)

---

### Anomaly Data Structure

Each anomaly includes:
- Provider name
- Metric type (cost, latency, error_rate)
- Current value
- 24-hour baseline
- Deviation percentage
- Severity level (WARNING, CRITICAL)
- Timestamp
- Human-readable description

---

## 🛠️ Testing Procedures

### Test 1: Basic Health Check

```bash
curl -X GET https://api.gatewayz.ai/api/monitoring/health \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected Response:** 200 OK with health data for all providers

---

### Test 2: Real-time Stats

```bash
curl -X GET https://api.gatewayz.ai/api/monitoring/stats/realtime \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected Response:** 200 OK with current metrics

---

### Test 3: Provider-Specific Latency

```bash
curl -X GET https://api.gatewayz.ai/api/monitoring/latency/openrouter/gpt-4o-mini \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected Response:** 200 OK with latency percentiles

---

### Test 4: Anomaly Detection

```bash
curl -X GET https://api.gatewayz.ai/api/monitoring/anomalies \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected Response:** 200 OK with list of current anomalies

---

### Test 5: Cost Analysis

```bash
curl -X GET https://api.gatewayz.ai/api/monitoring/cost-analysis \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected Response:** 200 OK with cost breakdown

---

## 📊 Dashboard Usage

### Accessing the Monitoring Dashboard

1. Open Grafana: http://localhost:3000
2. Navigate to Dashboards → GatewayZ Backend Monitoring
3. Enter your API key in the header
4. Select time range (1h, 1d, 1w, 1m, 1y)
5. Click "Load Data"

### Dashboard Components

#### Health Cards
- One card per provider
- Shows health score (0-100)
- Color-coded status (green, yellow, red)
- Displays detected anomalies
- Updates every 30 seconds in auto-refresh mode

#### Performance Analytics
- **Request Volume**: Line chart showing requests/time for top 5 providers
- **Latency Trends**: P95 latency percentile over time
- **Error Rates**: Error count trends
- **Cost Trends**: Total cost per time interval

#### Cost Analysis
- Pie chart showing provider cost breakdown
- Summary metrics:
  - Total cost (24h)
  - Highest cost provider
  - Most efficient provider
  - Total requests (24h)

#### Anomaly Alerts Table
- Real-time anomaly detection
- Columns: Provider, Metric, Current Value, 24h Avg, Deviation %, Severity, Timestamp
- Color-coded severity (yellow = WARNING, red = CRITICAL)

#### Provider Health Summary
- Table with all providers
- Columns: Provider, Health Score, Status, Requests, Errors, Avg Latency
- Health scores color-coded

---

## 🔐 Security Best Practices

### API Key Management
✅ **DO**:
- Store keys in environment variables
- Rotate keys regularly
- Use different keys for different environments
- Regenerate if compromised
- Never commit keys to git

❌ **DON'T**:
- Share API keys in messages
- Commit keys to repository
- Use same key across environments
- Log API keys
- Store in plaintext files

### Monitoring Safety
✅ **SAFE**:
- Monitor all providers simultaneously
- Use automated anomaly detection
- Set up alert thresholds
- Regular dashboard reviews
- Archive historical data

❌ **UNSAFE**:
- Ignore critical alerts
- Modify thresholds without review
- Share monitoring access widely
- Store sensitive data in metrics
- Disable anomaly detection

---

## 🔄 Integration Patterns

### Pattern 1: Standalone Monitoring Tool

The embedded monitoring tool (`grafana/monitoring-tool/index.html`) can be used independently:

```html
<iframe src="https://your-domain.com/monitoring-tool/index.html" width="100%" height="1000"></iframe>
```

**Features:**
- Real-time health visualization
- Time-series charts
- Anomaly detection display
- Cost analysis
- No Grafana dependency

---

### Pattern 2: Grafana Dashboard Integration

Embed the tool in Grafana dashboard (already configured):

1. Dashboard: `monitoring-dashboard-v1.json`
2. UID: `gatewayz-monitoring-v1`
3. Location: `grafana/dashboards/`
4. Auto-refresh: 30 seconds

---

### Pattern 3: Custom Alerting

Set up alerts based on anomaly thresholds:

```json
{
  "alert_rules": [
    {
      "provider": "*",
      "metric": "error_rate",
      "threshold": 25,
      "severity": "CRITICAL",
      "action": "page_oncall"
    },
    {
      "provider": "*",
      "metric": "cost",
      "threshold": 200,
      "severity": "WARNING",
      "action": "notify_slack"
    }
  ]
}
```

---

## 📈 Understanding Metrics

### Health Score (0-100)
Composite metric combining:
- Uptime percentage (40% weight)
- Error rate inverse (30% weight)
- Latency inverse (20% weight)
- Availability (10% weight)

**Formula:**
```
health_score = (uptime * 0.4) + (100 - error_rate * 0.3) + (100 - latency_score * 0.2) + (availability * 0.1)
```

---

### Requests Per Second (RPS)
Current request throughput to the provider.

**Good:** > 100 RPS
**Acceptable:** 50-100 RPS
**Poor:** < 50 RPS

---

### Error Rate Percentage
Percentage of failed requests (4xx, 5xx status codes).

**Good:** < 1%
**Acceptable:** 1-5%
**Poor:** > 5%

---

### Latency Percentiles
- **P50**: 50% of requests complete by this time (median)
- **P95**: 95% of requests complete by this time
- **P99**: 99% of requests complete by this time
- **P999**: 99.9% of requests complete by this time

**Good P95:** < 500ms
**Acceptable P95:** 500ms - 2s
**Poor P95:** > 2s

---

### Cost Per Request
Amount charged per API request.

**Good:** < $0.0001
**Acceptable:** $0.0001 - $0.001
**Expensive:** > $0.001

---

## 🐛 Troubleshooting

### "Failed to fetch health data"
**Causes:** Network issues, invalid API key, endpoint unreachable

**Solutions:**
1. Verify API key is correct
2. Check network connectivity
3. Verify endpoint URL
4. Check firewall rules
5. Review backend logs

---

### "No anomalies detected" but metrics show problems
**Causes:** Thresholds not triggered, baseline still calculating

**Solutions:**
1. Check threshold values
2. Verify 24h baseline has data
3. Monitor for next 24 hours
4. Adjust thresholds if needed

---

### Chart data not updating
**Causes:** Auto-refresh disabled, network latency, slow API

**Solutions:**
1. Enable auto-refresh
2. Check network performance
3. Verify API response times
4. Refresh dashboard manually
5. Check browser console for errors

---

### Missing provider data
**Causes:** Provider not provisioned, API key lacks permissions

**Solutions:**
1. Verify provider is active
2. Check API key permissions
3. Verify provider slug is correct
4. Check backend provider configuration
5. Contact support for provider access

---

## 📚 API Examples

### Python Example

```python
import requests
from datetime import datetime

api_key = "YOUR_API_KEY"
base_url = "https://api.gatewayz.ai"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Get health status
response = requests.get(
    f"{base_url}/api/monitoring/health",
    headers=headers
)
health_data = response.json()

# Get anomalies
response = requests.get(
    f"{base_url}/api/monitoring/anomalies",
    headers=headers
)
anomalies = response.json()

# Print critical anomalies
for anomaly in anomalies['anomalies']:
    if anomaly['severity'] == 'CRITICAL':
        print(f"🔴 {anomaly['provider']}: {anomaly['description']}")
```

---

### JavaScript Example

```javascript
const apiKey = "YOUR_API_KEY";
const baseUrl = "https://api.gatewayz.ai";

async function getProviderHealth(provider) {
    const response = await fetch(`${baseUrl}/api/monitoring/health`, {
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();
    return data.providers.find(p => p.provider === provider);
}

async function detectAnomalies() {
    const response = await fetch(`${baseUrl}/api/monitoring/anomalies`, {
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        }
    });

    return response.json();
}

// Usage
getProviderHealth('openrouter').then(health => {
    console.log(`OpenRouter health: ${health.health_score}`);
});
```

---

## 📞 Support & Resources

### Documentation Files
- **QUICK_START.md** - Setup instructions
- **RAILWAY_DEPLOYMENT_GUIDE.md** - Production deployment
- **API_ENDPOINT_TESTING_GUIDE.md** - Chat endpoint testing
- **DIAGNOSE_CONNECTIVITY.md** - Network troubleshooting

### External Resources
- [GatewayZ API Docs](https://api.gatewayz.ai/docs)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic API Docs](https://docs.anthropic.com)
- [Grafana Docs](https://grafana.com/docs)

### Getting Help
1. Check troubleshooting section above
2. Review error message details
3. Check backend status
4. Review logs in Grafana/Loki
5. Contact support with error details and provider information

---

## 🔄 Monitoring Workflow

### Daily Monitoring Tasks

1. **Check Dashboard** (9:00 AM)
   - Review health scores
   - Identify any critical anomalies
   - Note cost trends

2. **Review Anomalies** (2:00 PM)
   - Check for new anomalies
   - Verify threshold thresholds
   - Investigate critical alerts

3. **Cost Analysis** (4:00 PM)
   - Review daily costs
   - Identify expensive providers
   - Plan optimization

4. **Performance Review** (5:00 PM)
   - Analyze latency trends
   - Check error rates
   - Plan capacity adjustments

---

## 📊 Dashboard Variables

### api_base_url
The base URL for monitoring API calls.
- **Default:** `https://api.gatewayz.ai`
- **Typical Values:** Production or staging URLs

### time_range
Time window for historical data analysis.
- **Options:** 1h, 1d, 1w, 1m, 1y
- **Default:** 1d (Last 24 hours)
- **Affects:** All time-series charts

---

## ✅ Pre-Flight Checklist

Before going live with monitoring:

- [ ] All provider credentials configured
- [ ] API keys tested with curl
- [ ] Dashboard loads without errors
- [ ] Health scores updating in real-time
- [ ] Anomaly detection verified with test data
- [ ] Cost analysis reflecting actual usage
- [ ] Auto-refresh working (30 second interval)
- [ ] Alerts configured and tested
- [ ] Team trained on dashboard
- [ ] On-call procedure documented

---

**Generated**: December 28, 2025
**Status**: ✅ Production Ready
**Version**: 1.0
**Last Updated**: December 28, 2025
