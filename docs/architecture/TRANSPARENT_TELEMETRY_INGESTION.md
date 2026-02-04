# Transparent Telemetry Ingestion Architecture

## Overview

This document describes the transparent ingestion pipeline for traces and telemetry in the GatewayZ observability stack. The goal is to make the data flow from backend to dashboards completely transparent, validated, and easy to understand.

## Architecture Principles

1. **Transparency**: Every step of the data transformation is documented and observable
2. **Validation**: Trace attributes are validated at ingestion time
3. **Semantic Conventions**: Follow OpenTelemetry semantic conventions for AI/ML workloads
4. **Completeness**: Capture full model taxonomy (provider, model, variant, version)
5. **Debuggability**: Easy to trace why metrics are missing or incorrect

## Data Flow

```
Backend Application
    │
    ├─→ OTLP Traces (4317/4318)
    │   │
    │   ├─→ Required Attributes (OpenTelemetry Semantic Conventions):
    │   │   ├─ service.name: "gatewayz-api"
    │   │   ├─ gen_ai.system: "openai" | "anthropic" | "vertex_ai" | etc.
    │   │   ├─ gen_ai.request.model: "gpt-4" | "claude-opus-4.5" | etc.
    │   │   ├─ gen_ai.operation.name: "chat" | "completion" | "embedding"
    │   │   ├─ gen_ai.response.model: (actual model used)
    │   │   ├─ server.address: Provider API endpoint
    │   │   └─ http.response.status_code: 200 | 400 | 500 | etc.
    │   │
    │   ├─→ Optional Attributes (GatewayZ-specific):
    │   │   ├─ gatewayz.provider.name: "openrouter" | "cerebras" | etc.
    │   │   ├─ gatewayz.customer.id: Customer identifier
    │   │   ├─ gatewayz.request.type: "chat_completion" | "embedding" | etc.
    │   │   ├─ gatewayz.model.version: Model version if available
    │   │   └─ gatewayz.fallback.occurred: true | false
    │   │
    │   └─→ Tempo (Distributor)
    │       │
    │       ├─→ Ingester: Store traces (vParquet4)
    │       │   └─→ Storage: /var/tempo/traces (48h retention)
    │       │
    │       └─→ Metrics Generator: Extract span metrics
    │           │
    │           ├─→ Span Metrics Processor:
    │           │   ├─ Input: Trace spans with attributes
    │           │   ├─ Process: Extract dimensions from attributes
    │           │   ├─ Generate:
    │           │   │   ├─ traces_spanmetrics_calls_total{dimensions}
    │           │   │   ├─ traces_spanmetrics_duration_seconds_bucket{dimensions}
    │           │   │   ├─ traces_spanmetrics_duration_seconds_sum{dimensions}
    │           │   │   └─ traces_spanmetrics_duration_seconds_count{dimensions}
    │           │   │
    │           │   └─ Dimensions Extracted:
    │           │       ├─ service_name (from service.name)
    │           │       ├─ span_name (from span.name)
    │           │       ├─ span_kind (from span.kind)
    │           │       ├─ status_code (from span.status.code)
    │           │       ├─ gen_ai_system (from gen_ai.system)
    │           │       ├─ gen_ai_request_model (from gen_ai.request.model)
    │           │       ├─ gen_ai_response_model (from gen_ai.response.model)
    │           │       ├─ gen_ai_operation_name (from gen_ai.operation.name)
    │           │       ├─ http_response_status_code (from http.response.status_code)
    │           │       ├─ gatewayz_provider_name (from gatewayz.provider.name)
    │           │       ├─ gatewayz_customer_id (from gatewayz.customer.id)
    │           │       └─ gatewayz_request_type (from gatewayz.request.type)
    │           │
    │           ├─→ Service Graphs Processor:
    │           │   └─ Generate service dependency metrics
    │           │
    │           └─→ Remote Write to Mimir:
    │               └─ URL: ${MIMIR_REMOTE_WRITE_URL}/api/v1/push
    │                   └─ Headers: X-Scope-OrgID: anonymous
    │
    ├─→ Prometheus Metrics (/metrics endpoint)
    │   │
    │   └─→ Prometheus (Scraper)
    │       │
    │       ├─→ Scrape Jobs:
    │       │   ├─ gatewayz_production (15s): Backend metrics
    │       │   ├─ gatewayz_data_metrics_production (30s): Provider health
    │       │   ├─ redis_exporter (30s): Redis metrics
    │       │   └─ tempo (15s): Tempo internal metrics + span metrics
    │       │
    │       └─→ Remote Write to Mimir:
    │           └─ URL: ${MIMIR_URL}/api/v1/push
    │               └─ Headers: X-Scope-OrgID: anonymous
    │
    └─→ Logs (JSON format)
        │
        └─→ Loki (Push API)
            └─ URL: http://loki:3100/loki/api/v1/push
                └─ Storage: /loki (TSDB format)

All Data Sources → Grafana → Dashboards
    │
    ├─→ Datasources:
    │   ├─ Tempo (UID: grafana_tempo): Query traces via TraceQL
    │   ├─ Prometheus (UID: grafana_prometheus): Short-term metrics (15 days)
    │   ├─ Mimir (UID: grafana_mimir): Long-term metrics (30 days) + span metrics
    │   └─ Loki (UID: grafana_loki): Logs
    │
    └─→ Correlation:
        ├─ Trace ID → Logs (via derived fields)
        ├─ Trace ID → Metrics (via exemplars)
        └─ Metrics → Traces (via trace exemplars in histograms)
```

## OpenTelemetry Semantic Conventions for AI/ML

### Required Span Attributes

These attributes MUST be set on every AI/ML operation span:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `service.name` | string | Service name | `"gatewayz-api"` |
| `gen_ai.system` | string | AI system/provider | `"openai"`, `"anthropic"` |
| `gen_ai.request.model` | string | Requested model | `"gpt-4"`, `"claude-opus-4.5"` |
| `gen_ai.operation.name` | string | Operation type | `"chat"`, `"completion"`, `"embedding"` |
| `http.response.status_code` | int | HTTP status | `200`, `429`, `500` |

### Recommended Span Attributes

These attributes SHOULD be set for better observability:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `gen_ai.response.model` | string | Actual model used (may differ from request) | `"gpt-4-0613"` |
| `gen_ai.request.max_tokens` | int | Max tokens requested | `1000` |
| `gen_ai.usage.input_tokens` | int | Input tokens consumed | `450` |
| `gen_ai.usage.output_tokens` | int | Output tokens generated | `123` |
| `server.address` | string | Provider API endpoint | `"api.openai.com"` |
| `server.port` | int | Provider API port | `443` |

### GatewayZ-Specific Span Attributes

These attributes are specific to GatewayZ and provide additional context:

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `gatewayz.provider.name` | string | GatewayZ provider identifier | `"openrouter"`, `"cerebras"` |
| `gatewayz.customer.id` | string | Customer/tenant ID | `"cust_abc123"` |
| `gatewayz.request.type` | string | Detailed request type | `"chat_completion"`, `"text_embedding"` |
| `gatewayz.model.version` | string | Model version if known | `"4.5"`, `"0613"` |
| `gatewayz.fallback.occurred` | boolean | Whether fallback was triggered | `true`, `false` |
| `gatewayz.fallback.provider` | string | Fallback provider used | `"openrouter"` |
| `gatewayz.cache.hit` | boolean | Whether cache was hit | `true`, `false` |

## Span Metrics Configuration

### Dimensions

The metrics generator extracts these dimensions from trace attributes:

```yaml
dimensions:
  # OpenTelemetry standard attributes
  - service.name                    # Service identifier
  - span.name                       # Operation name (auto-captured)
  - span.kind                       # CLIENT, SERVER, etc. (auto-captured)
  - status.code                     # OK, ERROR (auto-captured)
  - gen_ai.system                   # AI provider (openai, anthropic, etc.)
  - gen_ai.request.model            # Requested model
  - gen_ai.response.model           # Actual model used
  - gen_ai.operation.name           # Operation type (chat, completion, etc.)
  - http.response.status_code       # HTTP status code
  - server.address                  # Provider API address

  # GatewayZ-specific attributes
  - gatewayz.provider.name          # GatewayZ provider name
  - gatewayz.customer.id            # Customer identifier
  - gatewayz.request.type           # Detailed request type
```

### Generated Metrics

For each unique combination of dimensions, the following metrics are generated:

1. **Call Counter**: `traces_spanmetrics_calls_total`
   - Type: Counter
   - Description: Total number of operations
   - Labels: All dimensions

2. **Duration Histogram**: `traces_spanmetrics_duration_seconds`
   - Type: Histogram
   - Description: Duration distribution
   - Labels: All dimensions
   - Buckets: `[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60]`

### Example Queries

**Total requests by model:**
```promql
sum by (gen_ai_request_model) (
  increase(traces_spanmetrics_calls_total[$__range])
)
```

**Average latency by provider:**
```promql
sum by (gatewayz_provider_name) (
  rate(traces_spanmetrics_duration_seconds_sum[5m])
)
/
sum by (gatewayz_provider_name) (
  rate(traces_spanmetrics_duration_seconds_count[5m])
)
```

**Error rate by model:**
```promql
sum by (gen_ai_request_model) (
  rate(traces_spanmetrics_calls_total{status_code="ERROR"}[5m])
)
/
sum by (gen_ai_request_model) (
  rate(traces_spanmetrics_calls_total[5m])
)
```

**P95 latency by customer:**
```promql
histogram_quantile(0.95,
  sum by (gatewayz_customer_id, le) (
    rate(traces_spanmetrics_duration_seconds_bucket[5m])
  )
)
```

## Validation and Debugging

### Trace Attribute Validation

Tempo exposes metrics about missing or invalid attributes:

```promql
# Missing attributes (resulting in empty labels)
tempo_metrics_generator_spans_discarded_total{reason="missing_required_attribute"}

# Invalid attribute types
tempo_metrics_generator_spans_discarded_total{reason="invalid_attribute_type"}
```

### Debugging Missing Metrics

If metrics are not appearing in Grafana:

1. **Check Backend is Sending Traces:**
   ```bash
   # Check Tempo received traces
   curl http://tempo:3200/api/search?tags=service.name=gatewayz-api
   ```

2. **Verify Trace Attributes:**
   ```bash
   # Query a trace by ID and check attributes
   curl http://tempo:3200/api/traces/<trace-id>
   ```

3. **Check Span Metrics Generation:**
   ```bash
   # Check Tempo metrics endpoint for span metrics
   curl http://tempo:3200/metrics | grep spanmetrics
   ```

4. **Verify Mimir Received Metrics:**
   ```bash
   # Query Mimir for span metrics
   curl -G http://mimir:9009/prometheus/api/v1/query \
     --data-urlencode 'query=traces_spanmetrics_calls_total'
   ```

5. **Check Prometheus Scraping:**
   ```bash
   # Verify Prometheus is scraping Tempo
   curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "tempo")'
   ```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Metrics missing for a model | Attribute not set in trace | Add `gen_ai.request.model` to span |
| High cardinality warning | Too many unique label combinations | Remove high-cardinality dimensions (e.g., trace IDs) |
| Metrics delayed | Slow flush to Mimir | Check Mimir write latency |
| Empty label values | Attribute name mismatch | Verify attribute names match semantic conventions |

## Performance Considerations

### Cardinality Management

High cardinality can cause performance issues. Monitor cardinality:

```promql
# Check active time series count
sum(scrape_samples_scraped{job="tempo"})

# Check by metric
count by (__name__) ({job="tempo"})
```

**Cardinality Limits:**
- Max unique combinations per dimension: ~1000
- Total active series: < 100,000
- If exceeded, consider:
  - Removing high-cardinality dimensions (customer ID, trace ID)
  - Aggregating dimensions (e.g., model family vs. specific version)
  - Using recording rules for pre-aggregation

### Resource Usage

**Tempo Metrics Generator:**
- Memory: ~256MB baseline + (series count × 1KB)
- CPU: ~0.1 core per 1000 spans/second
- Disk: ~10MB per million spans for WAL

**Prometheus/Mimir:**
- Memory: ~1KB per active series
- Disk: ~1.5 bytes per sample point

### Optimization Tips

1. **Use Recording Rules**: Pre-aggregate common queries
2. **Limit Retention**: Shorter retention = less storage
3. **Sample Traces**: Don't trace every request if volume is high
4. **Batch Writes**: Increase remote write batch size
5. **Monitor Costs**: Track resource usage per dimension

## Backend Integration Guide

See [OTLP_INTEGRATION_GUIDE.md](../backend/OTLP_INTEGRATION_GUIDE.md) for complete backend integration instructions including:

- How to install OpenTelemetry SDK
- How to configure OTLP exporters
- Code examples for setting trace attributes
- Testing and validation procedures

## Configuration Files

- **Tempo**: `/root/repo/tempo/tempo.yml` - Metrics generator configuration
- **Prometheus**: `/root/repo/prometheus/prometheus.yml` - Scrape and remote write config
- **Grafana Datasources**: `/root/repo/grafana/datasources/datasources.yml` - Data source connections
- **Docker Compose**: `/root/repo/docker-compose.yml` - Service orchestration

## References

- [OpenTelemetry Semantic Conventions for Gen AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Tempo Metrics Generator](https://grafana.com/docs/tempo/latest/metrics-generator/)
- [Prometheus Remote Write](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#remote_write)
- [Grafana Mimir](https://grafana.com/docs/mimir/latest/)
