# Tempo Distributed Tracing Integration

This guide explains how the Tempo distributed tracing service is integrated with the FastAPI application and Grafana dashboard.

## Overview

Tempo is a distributed tracing backend that collects and stores traces from the FastAPI application. The integration allows you to:

- View distributed traces across multiple services
- Analyze request flows and latencies
- Correlate traces with metrics and logs
- Debug performance issues in real-time

## Architecture

### Components

1. **FastAPI Application** - Generates traces using OpenTelemetry
2. **Tempo** - Collects and stores distributed traces
3. **Grafana** - Visualizes traces and correlates with metrics/logs

### Data Flow

```
FastAPI App (OpenTelemetry)
    ↓
OTLP Exporter (HTTP/gRPC)
    ↓
Tempo Distributor (port 4318/4317)
    ↓
Tempo Storage (local filesystem)
    ↓
Tempo Querier (port 3200)
    ↓
Grafana Dashboard
```

## Configuration

### FastAPI Application

The FastAPI app is configured to export traces to Tempo via OTLP (OpenTelemetry Protocol):

```python
TEMPO_URL = os.getenv("TEMPO_URL", os.getenv("TEMPO_INTERNAL_HTTP_INGEST", "http://tempo:4318"))

otlp_exporter = OTLPSpanExporter(
    endpoint=f"{TEMPO_URL}/v1/traces",
)

tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
```

**Environment Variables:**
- `TEMPO_URL` - Tempo HTTP ingest endpoint (default: `http://tempo:4318`)
- `TEMPO_INTERNAL_HTTP_INGEST` - Railway internal HTTP ingest endpoint
- `TEMPO_INTERNAL_GRPC_INGEST` - Railway internal gRPC ingest endpoint

### Tempo Configuration

Tempo is configured with:

- **HTTP Receiver** on port 4318 for OTLP HTTP protocol
- **gRPC Receiver** on port 4317 for OTLP gRPC protocol
- **Local Storage** at `/var/tempo/traces` with WAL support
- **Query Frontend** for efficient trace querying
- **Compactor** for trace data optimization

See `tempo/tempo.yml` for detailed configuration.

### Grafana Integration

Tempo is configured as a datasource in Grafana with:

- **Trace-to-Metrics** correlation with Prometheus
- **Trace-to-Logs** correlation with Loki
- **Span filtering** by trace ID and span ID

## Usage

### Generating Traces

The FastAPI application provides several endpoints for generating traces:

#### 1. Simple Trace Example
```bash
curl http://localhost:8000/trace-example?depth=3
```

Generates a trace with nested spans up to the specified depth.

#### 2. Generate Multiple Traces
```bash
curl http://localhost:8000/generate-traces?count=5&operations_per_trace=3
```

Generates multiple traces with specified number of operations per trace.

#### 3. Automatic Tracing
All requests to the FastAPI app are automatically traced:
- `/hello` - Simple endpoint
- `/slow` - Slow endpoint (2s delay)
- `/error` - Error endpoint
- `/generate-synthetic-data` - Synthetic data generation
- `/generate-load` - Load generation

### Viewing Traces in Grafana

1. **Open Grafana Dashboard:**
   - Navigate to `http://localhost:3000` (local) or your Railway URL
   - Login with credentials (default: admin/yourpassword123)

2. **View Tempo Dashboard:**
   - Go to Dashboards → Tempo Distributed Tracing
   - Use the trace search panel to find specific traces
   - Click on a trace to view detailed span information

3. **Search Traces:**
   - By Service Name: `service.name = "fastapi-app"`
   - By Span Name: Search for specific operation names
   - By Duration: Find slow traces
   - By Status: Find error traces

### Correlating with Metrics and Logs

The Tempo datasource is configured to correlate traces with:

- **Prometheus Metrics** - View request latencies alongside traces
- **Loki Logs** - View application logs for specific trace IDs

## Local Development

### Docker Setup

1. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

2. **Generate test traces:**
   ```bash
   curl http://localhost:8000/generate-traces?count=10
   ```

3. **View in Grafana:**
   - Open http://localhost:3000
   - Go to Tempo Distributed Tracing dashboard
   - Traces should appear within 10 seconds

### Debugging

**Check Tempo logs:**
```bash
docker-compose logs tempo
```

**Verify OTLP receiver is active:**
```bash
curl http://localhost:3200/api/traces
```

**Check FastAPI app logs:**
```bash
docker-compose logs fastapi_app
```

## Railway Deployment

### Environment Variables

Set these variables in your Railway project:

```
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
TEMPO_INTERNAL_HTTP_INGEST=http://tempo.railway.internal:4318
TEMPO_INTERNAL_GRPC_INGEST=http://tempo.railway.internal:4317
```

### Service Configuration

The FastAPI app automatically uses Railway internal URLs when deployed:

- Traces are sent to `http://tempo.railway.internal:4318/v1/traces`
- Grafana queries Tempo at `http://tempo.railway.internal:3200`

### Monitoring

1. **Check Tempo service status:**
   - Railway Dashboard → Tempo service → Logs

2. **Verify trace collection:**
   - Grafana → Tempo Dashboard → Check "Total Spans Received"

3. **Generate test traces on Railway:**
   - Call the `/generate-traces` endpoint on your Railway FastAPI app
   - Traces should appear in Grafana within 10 seconds

## Troubleshooting

### No Traces Appearing

**Issue:** Traces are not showing up in Grafana

**Solutions:**
1. Verify Tempo is running: `docker-compose ps tempo`
2. Check FastAPI app is sending traces: `docker-compose logs fastapi_app | grep "Generating"`
3. Verify OTLP endpoint is correct: Check `TEMPO_URL` environment variable
4. Check Tempo logs for errors: `docker-compose logs tempo`

### Traces Not Correlating with Logs

**Issue:** Trace-to-logs correlation not working

**Solutions:**
1. Verify Loki datasource is configured correctly
2. Ensure logs contain trace IDs in the correct format
3. Check trace time range matches log time range

### High Memory Usage

**Issue:** Tempo consuming too much memory

**Solutions:**
1. Reduce `block_retention` in `tempo/tempo.yml`
2. Increase `compaction_window` for less frequent compaction
3. Monitor with: `docker stats tempo`

## Performance Tuning

### For High-Volume Tracing

1. **Increase batch size:**
   ```python
   BatchSpanProcessor(otlp_exporter, max_export_batch_size=512)
   ```

2. **Adjust Tempo storage:**
   ```yaml
   storage:
     trace:
       local:
         wal:
           queue:
             max_queue_size: 10000
   ```

3. **Enable sampling in FastAPI:**
   ```python
   traces_sample_rate=0.1  # Sample 10% of traces
   ```

## Resources

- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Trace Integration](https://grafana.com/docs/grafana/latest/datasources/tempo/)
- [OTLP Protocol](https://opentelemetry.io/docs/reference/specification/protocol/)

## Next Steps

1. ✅ Deploy Tempo with FastAPI integration
2. ✅ Generate test traces
3. ✅ View traces in Grafana dashboard
4. 📊 Create custom dashboards for trace analysis
5. 🔔 Set up alerts based on trace metrics
6. 📈 Implement trace sampling for production
7. 🔐 Secure Tempo endpoints with authentication
