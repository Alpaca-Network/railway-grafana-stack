# Dashboard Configuration Summary

This document describes the complete dashboard configuration for your Grafana observability stack.

## What Was Configured

### 1. Dashboards Created

Five pre-configured dashboards have been added to automatically load when Grafana starts:

#### a. **Observability Stack Overview** (`overview`)
- **Purpose**: High-level overview of your entire observability stack
- **Features**:
  - Prometheus target status and metrics
  - Loki log volume by service
  - Tempo trace ingestion rates
  - Quick links to all other dashboards
- **Access**: This is the main landing dashboard

#### b. **Loki Logs Dashboard** (`loki-logs`)
- **Purpose**: View and search all logs aggregated by Loki
- **Features**:
  - Log volume visualization by service
  - Total log lines by service
  - Real-time log stream with search capability
  - Service filter dropdown
  - Text search filter
- **Use Case**: Troubleshooting, debugging, log analysis

#### c. **Prometheus Metrics Dashboard** (`prometheus-metrics`)
- **Purpose**: Monitor Prometheus itself and collected metrics
- **Features**:
  - Total targets and targets down count
  - Storage size and time series count
  - Target status over time
  - HTTP request rate and duration
  - TSDB (Time Series Database) statistics
- **Use Case**: Understanding metrics collection health

#### d. **Tempo Traces Dashboard** (`tempo-traces`)
- **Purpose**: View distributed tracing data
- **Features**:
  - Trace and span ingestion rates
  - Traces/spans per second by service
  - Ingestion bytes rate
  - Query request rate by status
  - Instructions for searching traces
- **Use Case**: Performance analysis, request flow tracking

#### e. **FastAPI Observability Dashboard** (`fastapi-observability`)
- **Purpose**: Comprehensive monitoring for FastAPI applications
- **Features**:
  - Total requests and request counts by endpoint
  - Average request duration
  - Total exceptions
  - Success rate (2xx) and error rate (5xx) by path
  - P99 request duration
  - Requests in progress
  - Request rate per second
  - Log type distribution
  - Complete log viewer with trace correlation
- **Use Case**: Monitoring FastAPI applications with full observability

## 2. Datasource Improvements

The datasource configurations have been enhanced with **full correlation between logs, metrics, and traces**:

### Loki Configuration
- **Trace Correlation**: Automatically detects `trace_id` in logs and creates clickable links to Tempo traces
- **Pattern**: Extracts trace IDs matching the pattern `trace_id=(\w+)`

### Prometheus Configuration
- **Exemplar Support**: Links metrics with exemplars to their corresponding traces in Tempo
- **Trace ID Field**: Configured to use `trace_id` field for correlation

### Tempo Configuration
- **Traces to Logs**: Click on a trace to see related logs in Loki
  - Searches by `service_name` and `compose_service` tags
  - Includes 1-hour time window before and after span
- **Traces to Metrics**: Click on a trace to see related metrics in Prometheus
  - Correlates by service name
- **Service Map**: Visualizes service dependencies using Prometheus data
- **Node Graph**: Shows trace topology
- **Loki Search**: Search traces using log data

## 3. Auto-Provisioning

All dashboards are automatically loaded when Grafana starts:

- **Location**: `/root/repo/grafana/dashboards/`
- **Provisioning Config**: `dashboards.yml` tells Grafana to load all JSON files
- **Dockerfile Updated**: Copies dashboard files into the Grafana container
- **Editable**: Dashboards can be modified in the UI (changes won't persist on restart unless saved to files)

## How to Use

### Starting the Stack

```bash
docker-compose up -d
```

### Accessing Grafana

1. Navigate to your Grafana URL (default: `http://localhost:3000`)
2. Log in with your configured credentials:
   - Username: From `GF_SECURITY_ADMIN_USER` env var (default: `admin`)
   - Password: From `GF_SECURITY_ADMIN_PASSWORD` env var (default: `yourpassword123`)

### Navigating Dashboards

1. **Main Menu**: Click the hamburger menu → Dashboards
2. **Quick Access**: Use the links at the top of the Overview dashboard
3. **Search**: Use Cmd/Ctrl+K to search for dashboards

### Using Correlation Features

#### From Logs to Traces
1. Open the Loki Logs dashboard
2. Find a log line with a `trace_id`
3. Click on the extracted TraceID link
4. You'll be taken to the full trace in Tempo

#### From Traces to Logs
1. Open a trace in Tempo (via Explore or Tempo dashboard)
2. Click on any span
3. Click "Logs for this span" button
4. See all related logs in Loki

#### From Metrics to Traces
1. View metrics in Prometheus dashboard
2. If exemplars are present, hover over data points
3. Click on exemplar markers to jump to traces

## Dashboard Customization

### Modifying Existing Dashboards

1. Make changes in the Grafana UI
2. Export the dashboard JSON (Share → Export)
3. Save to the corresponding file in `/root/repo/grafana/dashboards/`
4. Rebuild the Grafana container

### Adding New Dashboards

1. Create your dashboard in Grafana UI
2. Export as JSON
3. Save to `/root/repo/grafana/dashboards/your-dashboard.json`
4. Rebuild the Grafana container

## Files Modified

```
/root/repo/grafana/
├── dashboards/
│   ├── dashboards.yml                    # Dashboard provisioning config
│   ├── fastapi-observability.json        # FastAPI monitoring dashboard
│   ├── loki-logs.json                    # Logs dashboard
│   ├── overview.json                     # Overview dashboard
│   ├── prometheus-metrics.json           # Metrics dashboard
│   └── tempo-traces.json                 # Traces dashboard
├── datasources/
│   └── datasources.yml                   # Updated with correlations
└── dockerfile                            # Updated to copy dashboards
```

## Next Steps

1. **Deploy**: Rebuild and restart your Grafana service to see the new dashboards
2. **Customize**: Modify dashboards to match your specific needs
3. **Monitor**: Start sending data from your applications to see visualizations
4. **Explore**: Use the correlation features to jump between logs, metrics, and traces

## Troubleshooting

### Dashboards Not Appearing
- Check Grafana logs: `docker-compose logs grafana`
- Verify files exist: `ls -la /root/repo/grafana/dashboards/`
- Ensure Dockerfile built correctly: `docker-compose build grafana`

### Datasource Correlation Not Working
- Verify trace IDs in logs match the regex pattern `trace_id=(\w+)`
- Ensure metrics have exemplars enabled
- Check that all datasource UIDs are correct (grafana_lokiq, grafana_prometheus, grafana_tempo)

### Missing Data
- Confirm your applications are sending data to Loki/Prometheus/Tempo
- Check datasource configuration in Grafana UI
- Verify internal URLs are accessible

## Additional Resources

- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Grafana Correlations](https://grafana.com/docs/grafana/latest/administration/correlations/)
