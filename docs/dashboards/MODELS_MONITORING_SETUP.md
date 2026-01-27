# Models Monitoring Dashboard Setup

## Overview
This guide sets up a dedicated Models Monitoring Dashboard to track model throughput, latency, error rates, and availability across your AI model infrastructure.



## Dashboard Panels

### 1. Model Request Throughput
- **Metric:** `sum by (model) (rate(model_requests_total[5m]))`
- **Description:** Requests per second for each model
- **Type:** Time series line chart
- **Legend:** Model name with mean and max calculations

### 2. Model Average Latency
- **Metric:** `sum by (model) (rate(model_latency_ms_sum[5m])) / sum by (model) (rate(model_latency_ms_count[5m]))`
- **Description:** Average response time in milliseconds per model
- **Type:** Time series line chart
- **Unit:** Milliseconds

### 3. Model Error Rate
- **Metric:** `sum by (model) (rate(model_errors_total[5m])) / sum by (model) (rate(model_requests_total[5m])) * 100`
- **Description:** Error percentage for each model
- **Type:** Time series line chart
- **Thresholds:** Green <5%, Yellow 5-10%, Red >10%

### 4. Model Token Usage Rate
- **Metric:** `sum by (model) (rate(model_tokens_used_total[5m]))`
- **Description:** Tokens consumed per second by model
- **Type:** Time series line chart
- **Legend:** Model name with sum calculations

### 5-9. Model Family Distribution Gauges
Percentage of total requests by model family:
- **Claude Models %** - `model=~"claude.*"`
- **GPT Models %** - `model=~"gpt.*"`
- **Gemini Models %** - `model=~".*gemini.*"`
- **Llama Models %** - `model=~".*llama.*"`
- **Mistral Models %** - `model=~".*mistral.*"`

**Thresholds:** Red <50%, Yellow 50-80%, Green >80%

### 10. Hourly Request Distribution
- **Metric:** `sum by (model) (increase(model_requests_total[1h]))`
- **Description:** Total requests per model over the last hour
- **Type:** Stacked bar chart
- **Legend:** Model name with sum calculations

### 11. Model Availability
- **Metric:** `sum by (model) ((sum by (model) (rate(model_requests_total[5m])) - sum by (model) (rate(model_errors_total[5m]))) / sum by (model) (rate(model_requests_total[5m]))) * 100`
- **Description:** Availability percentage (successful requests / total requests)
- **Type:** Time series line chart
- **Thresholds:** Red <95%, Yellow 95-99%, Green >99%

## Required Metrics

The backend must expose the following Prometheus metrics:

```
# Model request counter
model_requests_total{model="<model_name>"}

# Model error counter
model_errors_total{model="<model_name>"}

# Model latency histogram (milliseconds)
model_latency_ms_bucket{model="<model_name>", le="<bucket>"}
model_latency_ms_count{model="<model_name>"}
model_latency_ms_sum{model="<model_name>"}

# Token usage counter
model_tokens_used_total{model="<model_name>"}
```

## Local Testing

### 1. Start the stack
```bash
docker-compose up -d
```

### 2. Access Grafana
```
http://localhost:3000
```

### 3. Navigate to Models Monitoring Dashboard
- Dashboards → Models Monitoring

### 4. Verify data is flowing
- Check that all panels show data (not "No data")
- Verify model names appear in legends
- Confirm metrics are updating (refresh every 30 seconds)

## Railway Deployment

### 1. Ensure Prometheus is configured
The `prometheus/prom.yml` file handles the configuration.

### 2. Redeploy services
```bash
# Push changes to main
git push origin main

# Railway will automatically redeploy
```

### 3. Verify on Railway
- Access Grafana at your Railway Grafana URL
- Navigate to Models Monitoring Dashboard
- Confirm metrics are being scraped

## Troubleshooting

### No data in panels
1. Check Prometheus targets: `http://prometheus:9090/targets`
2. Check metric names match exactly (case-sensitive)

### Bearer token issues
- Ensure `bearer_token` is correctly set in `prometheus/prometheus.yml` (if using token auth)
- Verify token is valid and has metrics endpoint access

## Next Steps

1. Implement metrics emission in backend (model_requests_total, model_errors_total, etc.)
2. Add alerting rules for model availability and error rates
3. Create runbooks for common model issues
4. Set up notifications for SLA violations
