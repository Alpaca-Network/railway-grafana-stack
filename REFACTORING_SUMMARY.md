# Model Directory Refactoring: Transparent Telemetry Ingestion

## Overview

This refactoring transforms the GatewayZ observability stack to provide **transparent ingestion of traces and telemetry** with automatic metrics generation. The goal is to make the entire data flow from backend to dashboards completely transparent, validated, and easy to understand.

## What Changed

### 1. Architecture Documentation

**New Files:**
- `/docs/architecture/TRANSPARENT_TELEMETRY_INGESTION.md` - Complete architecture overview
- `/docs/backend/OTLP_INTEGRATION_GUIDE.md` - Step-by-step OpenTelemetry integration guide

**Purpose:**
- Provides clear data flow diagrams
- Documents OpenTelemetry semantic conventions for AI/ML
- Explains how traces automatically become metrics
- Includes debugging and validation procedures

### 2. Tempo Configuration (`/tempo/tempo.yml`)

**Changes:**
- ✅ Added comprehensive inline documentation explaining every section
- ✅ Adopted OpenTelemetry Gen AI semantic conventions
- ✅ Expanded span metrics dimensions to include:
  - `gen_ai.system` - AI provider (openai, anthropic, etc.)
  - `gen_ai.request.model` - Requested model name
  - `gen_ai.response.model` - Actual model used
  - `gen_ai.operation.name` - Operation type (chat, embedding, etc.)
  - `http.response.status_code` - For error tracking
  - `server.address` - Provider API endpoint
  - `gatewayz.*` - Custom business logic attributes
- ✅ Extended histogram buckets to cover AI/ML latency ranges (10ms to 60s)
- ✅ Added performance tuning parameters (dimensions_cache_size, queue_config)
- ✅ Improved remote write configuration with better batching

**Benefits:**
- Clear mapping between trace attributes and generated metrics
- Better model taxonomy (provider/model/operation)
- Supports both OpenTelemetry standard and GatewayZ-specific attributes
- Easier to debug missing metrics

### 3. Tempo Entrypoint Script (`/tempo/entrypoint.sh`)

**Changes:**
- ✅ Added configuration validation on startup
- ✅ Displays key configuration sections for transparency
- ✅ Lists required trace attributes
- ✅ Tests Mimir connectivity before starting
- ✅ Provides helpful monitoring commands
- ✅ Better error messages and visual indicators (✅ ❌ ⚠️)

**Benefits:**
- Immediate feedback if configuration is incorrect
- Clear indication of what attributes backend should send
- Easier troubleshooting during deployment

### 4. Prometheus Configuration (`/prometheus/prometheus.yml`)

**Changes:**
- ✅ Added comprehensive documentation for each scrape job
- ✅ Explained remote write configuration in detail
- ✅ Documented expected metrics for each job
- ✅ Clarified the purpose of scraping Tempo (span metrics)
- ✅ Added component labels for better metric organization
- ✅ Improved comments on queue configuration and batching

**Benefits:**
- Clear understanding of what each job collects
- Easier to debug missing metrics from specific jobs
- Better organization with component labels

### 5. Grafana Datasources (`/grafana/datasources/datasources.yml`)

**Changes:**
- ✅ Added detailed purpose and use case documentation for each datasource
- ✅ Enhanced trace-to-metrics correlation configuration
- ✅ Added custom queries in `tracesToMetrics` for better correlation
- ✅ Documented when to use Prometheus vs. Mimir
- ✅ Improved exemplar configuration for metrics-to-traces linking
- ✅ Added alternative regex patterns for trace ID extraction

**Key Improvements:**
- **Loki**: Better derived fields for log-to-trace correlation
- **Prometheus**: Clear explanation of 15-day retention
- **Mimir**: Emphasized as primary datasource for dashboards
- **Tempo**: Enhanced correlation queries showing related metrics

**Benefits:**
- Seamless navigation between traces, metrics, and logs
- Clear guidance on which datasource to use when
- Better correlation queries automatically run

### 6. Backend Integration Guide Updates

**Changes:**
- ✅ Updated `/docs/backend/COMPLETE_BACKEND_INTEGRATION_GUIDE.md`
- ✅ Added prominent links to new OTLP Integration Guide
- ✅ Highlighted required vs. optional trace attributes
- ✅ Simplified examples focusing on semantic conventions

## Key Concepts

### Transparent Ingestion

The refactored stack makes the entire data flow transparent:

```
Backend sends OTLP traces with attributes
    ↓
Tempo ingests traces (ports 4317/4318)
    ↓
Metrics Generator extracts dimensions from trace attributes
    ↓
Generates span metrics: traces_spanmetrics_calls_total, traces_spanmetrics_duration_seconds
    ↓
Remote writes to Mimir
    ↓
Grafana queries Mimir for dashboards
    ↓
Model Popularity, Latency, Error Rate dashboards auto-populate
```

### OpenTelemetry Semantic Conventions

We now follow the OpenTelemetry Gen AI semantic conventions:

**Required Attributes:**
- `gen_ai.system` - AI provider identifier
- `gen_ai.request.model` - Model requested by user
- `gen_ai.operation.name` - Operation type (chat, completion, embedding)
- `http.response.status_code` - HTTP status for error tracking

**Why this matters:**
- Industry standard attribute names
- Consistent across different AI/ML observability tools
- Clear documentation and examples available
- Future-proof as OpenTelemetry evolves

### Automatic Metrics Generation

Traces are automatically converted to metrics without backend changes:

**From one trace with attributes, Tempo generates:**
1. Counter: `traces_spanmetrics_calls_total{gen_ai_request_model="gpt-4", ...}`
2. Histogram: `traces_spanmetrics_duration_seconds_bucket{gen_ai_request_model="gpt-4", ...}`

**This enables queries like:**
- Total requests per model
- P95 latency per provider
- Error rate by customer
- Model popularity rankings

## What Backend Team Needs to Do

### Immediate Actions (High Priority)

1. **Review OpenTelemetry Integration Guide**
   - Read `/docs/backend/OTLP_INTEGRATION_GUIDE.md`
   - Understand required trace attributes

2. **Update Trace Attributes**
   - Replace `model` → `gen_ai.request.model`
   - Replace `provider` → `gen_ai.system` (for AI system) or `gatewayz.provider.name` (for GatewayZ provider)
   - Add `gen_ai.operation.name` ("chat", "completion", "embedding")
   - Ensure `http.response.status_code` is set

3. **Test Integration**
   - Deploy changes to staging
   - Verify traces appear in Grafana Explore → Tempo
   - Check that span metrics appear in Mimir
   - Validate Model Popularity dashboard shows data

### Example Migration

**Before (old attributes):**
```python
span.set_attribute("model", "gpt-4")
span.set_attribute("provider", "openrouter")
span.set_attribute("status", "success")
```

**After (OpenTelemetry semantic conventions):**
```python
# OpenTelemetry standard
span.set_attribute("gen_ai.system", "openai")
span.set_attribute("gen_ai.request.model", "gpt-4")
span.set_attribute("gen_ai.operation.name", "chat")
span.set_attribute("http.response.status_code", 200)

# GatewayZ-specific
span.set_attribute("gatewayz.provider.name", "openrouter")
span.set_attribute("gatewayz.customer.id", "cust_123")
```

## Benefits of This Refactoring

### For Backend Developers

- ✅ Clear documentation on what attributes to set
- ✅ Automatic metrics generation (no manual instrumentation needed)
- ✅ Better debugging with validation and error messages
- ✅ Industry-standard conventions (OpenTelemetry)
- ✅ Comprehensive examples and code snippets

### For Operations Team

- ✅ Transparent data flow (easy to debug)
- ✅ Configuration validation on startup
- ✅ Clear error messages when something is misconfigured
- ✅ Built-in health checks and connectivity tests
- ✅ Monitoring commands documented in entrypoint scripts

### For Product/Analytics Team

- ✅ Automatic model popularity tracking
- ✅ Latency percentiles without manual queries
- ✅ Error rate tracking per model/provider
- ✅ Customer-level metrics (when customer_id is set)
- ✅ Historical data retention (30+ days in Mimir)

## Testing the Refactored Stack

### 1. Validate Configuration Files

```bash
# Check Tempo config
docker compose up tempo

# Look for startup logs showing:
# ✅ MIMIR_REMOTE_WRITE_URL successfully substituted
# ✅ Mimir is ready at: mimir:9009
```

### 2. Send Test Traces

Use the example code in `/docs/backend/OTLP_INTEGRATION_GUIDE.md` to send test traces with proper attributes.

### 3. Verify Span Metrics

```bash
# Check Tempo generated span metrics
curl http://localhost:3200/metrics | grep spanmetrics

# Should see:
# traces_spanmetrics_calls_total{...}
# traces_spanmetrics_duration_seconds_bucket{...}
```

### 4. Query Mimir

```bash
# Check Mimir received span metrics
curl -G http://localhost:9009/prometheus/api/v1/query \
  --data-urlencode 'query=traces_spanmetrics_calls_total' \
  -H 'X-Scope-OrgID: anonymous' | jq
```

### 5. View in Grafana

1. Open Grafana: http://localhost:3000
2. Go to Explore
3. Select "Tempo" datasource
4. Search: `{service.name="gatewayz-api"}`
5. Click on a trace and verify attributes are present
6. Click "Metrics" tab to see correlated metrics
7. Switch to "Mimir" datasource
8. Query: `rate(traces_spanmetrics_calls_total[5m])`

## Migration Guide

### Phase 1: Deploy Configuration Changes (This PR)

1. ✅ Merge this PR to deploy refactored configurations
2. ✅ Verify services restart successfully
3. ✅ Check logs for configuration validation messages

### Phase 2: Backend Updates (Next Sprint)

1. Update OpenTelemetry trace attributes
2. Deploy to staging
3. Validate metrics appear in Grafana
4. Deploy to production

### Phase 3: Dashboard Updates (Optional)

1. Update dashboards to use new metric labels
2. Add new dimensions to existing queries
3. Create new dashboards leveraging expanded dimensions

## Backward Compatibility

### Legacy Attributes

The refactored Tempo configuration still supports legacy attributes for backward compatibility:

- `ai.provider` → Maps to `gatewayz.provider.name`
- `ai.model_id` → Maps to `gen_ai.request.model`
- `customer.id` → Maps to `gatewayz.customer.id`

**Action Required:**
- Legacy attributes are marked as DEPRECATED
- Plan to migrate to OpenTelemetry semantic conventions
- Both old and new attributes will work during migration

### Existing Dashboards

- ✅ Existing dashboards continue to work
- ✅ Span metrics still generated with same metric names
- ✅ Additional dimensions available for new queries

## Troubleshooting

### Metrics Not Appearing

1. **Check Backend is Sending Traces:**
   ```bash
   curl http://tempo:3200/api/search?tags=service.name=gatewayz-api
   ```

2. **Verify Trace Attributes:**
   - Query a trace by ID in Grafana
   - Check that required attributes are present
   - Look for `gen_ai.request.model`, `gen_ai.system`, etc.

3. **Check Tempo Metrics Generation:**
   ```bash
   curl http://tempo:3200/metrics | grep spans_processed
   # Should show: tempo_metrics_generator_spans_processed_total > 0
   ```

4. **Verify Mimir Remote Write:**
   ```bash
   curl http://tempo:3200/metrics | grep remote_write
   # Check for successful writes, no errors
   ```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty labels in metrics | Missing trace attributes | Add required attributes in backend |
| Metrics delayed | Slow Mimir write | Check Mimir logs and write queue |
| High cardinality warning | Too many unique labels | Remove high-cardinality dimensions |
| Exemplars not linking | Missing trace_id in exemplars | Verify OpenTelemetry instrumentation |

## File Changes Summary

### New Files
- `/docs/architecture/TRANSPARENT_TELEMETRY_INGESTION.md` (new architecture doc)
- `/docs/backend/OTLP_INTEGRATION_GUIDE.md` (new integration guide)
- `/REFACTORING_SUMMARY.md` (this file)

### Modified Files
- `/tempo/tempo.yml` - Enhanced with semantic conventions and documentation
- `/tempo/entrypoint.sh` - Added validation and monitoring
- `/prometheus/prometheus.yml` - Improved documentation and labeling
- `/grafana/datasources/datasources.yml` - Enhanced correlation configuration
- `/docs/backend/COMPLETE_BACKEND_INTEGRATION_GUIDE.md` - Updated with new references

### No Changes Required
- Dashboard JSON files (backward compatible)
- Mimir configuration
- Loki configuration
- Docker Compose file
- Existing backend code (but updates recommended)

## Next Steps

1. **For Platform Team:**
   - [ ] Review and approve this refactoring
   - [ ] Deploy to staging environment
   - [ ] Monitor for any issues
   - [ ] Deploy to production

2. **For Backend Team:**
   - [ ] Review OTLP Integration Guide
   - [ ] Plan sprint for trace attribute updates
   - [ ] Update staging backend with new attributes
   - [ ] Validate metrics in staging dashboards
   - [ ] Deploy to production

3. **For Product Team:**
   - [ ] Review new metrics capabilities
   - [ ] Identify new dashboard requirements
   - [ ] Plan analytics queries using new dimensions

## Questions?

- **Architecture**: See `/docs/architecture/TRANSPARENT_TELEMETRY_INGESTION.md`
- **Integration**: See `/docs/backend/OTLP_INTEGRATION_GUIDE.md`
- **Troubleshooting**: See sections above or check Grafana Tempo datasource

## Related Pull Requests

- This PR: Refactor Model Directory for transparent telemetry ingestion
- Backend PR (upcoming): Update trace attributes to OpenTelemetry semantic conventions
- Dashboard PR (optional): Enhance dashboards with new dimensions

---

**Refactoring completed:** 2026-02-03
**Branch:** `gatewayz-code/refactor-model-ingestion-ykt48k`
**Documentation:** Complete
**Backward Compatible:** Yes
**Breaking Changes:** None
