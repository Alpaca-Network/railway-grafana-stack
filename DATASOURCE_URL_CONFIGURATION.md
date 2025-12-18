# Datasource URL Configuration Guide

## Issues Identified

### 1. Loki Dashboard Query Errors
**Error:** "not a valid duration string: `$_rate_interval`"
**Cause:** Loki dashboard was using `$__rate_interval` (Prometheus variable) instead of valid Loki time ranges
**Status:** FIXED - Changed to `[5m]` time range

### 2. Tempo Dashboard "No Data"
**Cause:** Datasource URL may be incorrect on Railway
**Solution:** Verify environment variables are set correctly

### 3. 400 Errors on Loki Queries
**Cause:** Invalid query syntax or missing labels
**Status:** Requires proper log shipping from backend

## Datasource Configuration

### Environment Variables Required on Railway

```bash
# Prometheus
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_INTERNAL_URL=http://prometheus:9090

# Loki
LOKI_URL=http://loki:3100
LOKI_INTERNAL_URL=http://loki:3100

# Tempo
TEMPO_URL=http://tempo:3200
TEMPO_INTERNAL_URL=http://tempo:3200
TEMPO_INTERNAL_HTTP_INGEST=http://tempo:4318
TEMPO_INTERNAL_GRPC_INGEST=http://tempo:4317

# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<secure-password>
GF_DEFAULT_INSTANCE_NAME=Grafana
```

## Datasource Provisioning File

Location: `grafana/datasources/datasources.yml`

### Loki Datasource
```yaml
- name: Loki
  type: loki
  access: direct
  uid: grafana_lokiq
  url: ${LOKI_INTERNAL_URL}
  jsonData:
    derivedFields:
      - datasourceUid: grafana_tempo
        matcherRegex: "trace_id=(\\w+)"
        name: TraceID
        url: '$${__value.raw}'
```

**Key Points:**
- `access: direct` - Grafana queries Loki directly
- `uid: grafana_lokiq` - Used in dashboard references
- `url` uses `${LOKI_INTERNAL_URL}` environment variable
- Derived fields link logs to traces via `trace_id`

### Prometheus Datasource
```yaml
- name: Prometheus
  type: prometheus
  access: proxy
  uid: grafana_prometheus
  url: ${PROMETHEUS_INTERNAL_URL}
  jsonData:
    exemplarTraceIdDestinations:
      - datasourceUid: grafana_tempo
        name: trace_id
```

**Key Points:**
- `access: proxy` - Grafana proxies requests to Prometheus
- `uid: grafana_prometheus` - Used in dashboard references
- Exemplar destinations link metrics to traces

### Tempo Datasource
```yaml
- name: Tempo
  type: tempo
  access: proxy
  uid: grafana_tempo
  url: ${TEMPO_INTERNAL_URL}
  jsonData:
    tracesToLogsV2:
      datasourceUid: 'grafana_lokiq'
      spanStartTimeShift: '-1h'
      spanEndTimeShift: '1h'
      tags: ['service_name', 'compose_service']
      filterByTraceID: true
    tracesToMetrics:
      datasourceUid: 'grafana_prometheus'
      spanStartTimeShift: '-1h'
      spanEndTimeShift: '1h'
      tags:
        - key: 'service.name'
          value: 'service_name'
    serviceMap:
      datasourceUid: 'grafana_prometheus'
    nodeGraph:
      enabled: true
    search:
      hide: false
    lokiSearch:
      datasourceUid: 'grafana_lokiq'
```

**Key Points:**
- `access: proxy` - Grafana proxies requests to Tempo
- `uid: grafana_tempo` - Used in dashboard references
- `tracesToLogsV2` - Links traces to logs in Loki
- `tracesToMetrics` - Links traces to metrics in Prometheus
- `serviceMap` - Shows service dependencies
- `lokiSearch` - Search traces via Loki logs

## Verification Steps

### Step 1: Check Environment Variables on Railway
```bash
# In Railway dashboard, go to your project settings
# Verify these variables are set:
echo $LOKI_INTERNAL_URL
echo $PROMETHEUS_INTERNAL_URL
echo $TEMPO_INTERNAL_URL
```

### Step 2: Test Datasource Connectivity
In Grafana:
1. Go to **Configuration → Data Sources**
2. Click each datasource
3. Click **Save & Test**
4. Verify "Data source is working" message

### Step 3: Verify Loki Queries
In Grafana Explore:
1. Select **Loki** datasource
2. Try simple query: `{job="docker"}`
3. Verify logs appear (if logs are being shipped)

### Step 4: Verify Tempo Queries
In Grafana Explore:
1. Select **Tempo** datasource
2. Click **Search** tab
3. Verify trace search works (if traces are being sent)

### Step 5: Verify Prometheus Queries
In Grafana Explore:
1. Select **Prometheus** datasource
2. Try query: `up`
3. Verify metrics appear

## Common Issues and Solutions

### Issue: "Failed to load resource: the server responded with a status of 400"
**Cause:** Invalid Loki query syntax or missing labels
**Solution:** 
- Verify log labels match query filters
- Check logs are being shipped to Loki
- Use simple queries first: `{job="docker"}`

### Issue: Tempo "No data"
**Cause:** 
1. Datasource URL incorrect
2. No traces being sent to Tempo
3. Tempo not running
**Solution:**
- Verify `TEMPO_INTERNAL_URL` is set to `http://tempo:3200`
- Check Tempo is running: `curl http://tempo:3200/status`
- Verify backend is sending traces to `http://tempo:4318` (HTTP) or `tempo:4317` (gRPC)

### Issue: Loki "No data"
**Cause:**
1. Datasource URL incorrect
2. No logs being shipped
3. Loki not running
**Solution:**
- Verify `LOKI_INTERNAL_URL` is set to `http://loki:3100`
- Check Loki is running: `curl http://loki:3100/loki/api/v1/status/buildinfo`
- Verify logs are being shipped with proper labels

### Issue: Prometheus "No data"
**Cause:**
1. Datasource URL incorrect
2. Scrape targets not UP
3. Prometheus not running
**Solution:**
- Verify `PROMETHEUS_INTERNAL_URL` is set to `http://prometheus:9090`
- Check Prometheus targets: `http://prometheus:9090/targets`
- Verify all scrape jobs show "UP"

## Railway Deployment Checklist

- [ ] Set all environment variables in Railway project settings
- [ ] Redeploy all services (Prometheus, Loki, Tempo, Grafana)
- [ ] Wait 2-3 minutes for services to start
- [ ] Access Grafana at your Railway URL
- [ ] Go to Configuration → Data Sources
- [ ] Click "Save & Test" on each datasource
- [ ] Verify all datasources show "Data source is working"
- [ ] Go to Dashboards and verify data is flowing
- [ ] Check Prometheus targets are UP
- [ ] Check Loki is receiving logs (if logs are being shipped)
- [ ] Check Tempo is receiving traces (if traces are being sent)

## Local Development Checklist

- [ ] Run `docker-compose up --build`
- [ ] Access Grafana at `http://localhost:3000`
- [ ] Go to Configuration → Data Sources
- [ ] Verify all datasources show "Data source is working"
- [ ] Go to Dashboards and verify data is flowing
- [ ] Check Prometheus targets at `http://localhost:9090/targets`

## Next Steps

1. **Implement Backend Instrumentation**
   - Add Prometheus metrics emission
   - Add structured JSON logging to Loki
   - Add OpenTelemetry tracing to Tempo

2. **Configure Log Shipping**
   - Set up log forwarding from backend to Loki
   - Ensure logs include proper labels (service, job, level)

3. **Configure Trace Shipping**
   - Set up OpenTelemetry SDK in backend
   - Configure OTLP exporter to Tempo
   - Ensure traces include proper attributes

4. **Verify Data Flow**
   - Check Prometheus scrape targets
   - Check Loki log ingestion
   - Check Tempo trace ingestion
   - Verify dashboards display data
