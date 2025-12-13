# GatewayZ Observability Stack

A complete observability solution deployed on Railway, providing centralized logging, metrics collection, distributed tracing, and visualization for the GatewayZ infrastructure.

## Stack Components

The stack includes four integrated services:

- **Grafana**: Central visualization and dashboarding platform
- **Loki**: Log aggregation system for centralized log management
- **Prometheus**: Time-series metrics collection and alerting
- **Tempo**: Distributed tracing backend for request tracing

All services are pre-configured and interconnected, ready to receive and visualize telemetry data from your applications.

### Key Features

- **Pre-configured Integration**: _All services come pre-connected_, so Grafana is ready to query your data immediately.
- **Persistent Storage**: All four services use Railway volumes to ensure your data, dashboards, and configurations persist between updates and deploys.
- **Version Control**: Pin specific Docker image versions for each service using environment variables.
- **Customizable**: Fork the repository to customize configuration files for any service. You can take full control and edit anything you'd need to as you scale.
- **One-Click Deploy**: Get a complete Grafana-based observability stack running in minutes.
- **Optional Sentry Integration**: Add real-time error tracking and performance monitoring to your stack for comprehensive error management.

## Accessing the Stack

All services are publicly accessible via Railway's public URLs:

| Service | URL |
|---------|-----|
| **Grafana** | https://logs.gatewayz.ai |
| **Tempo** | https://tempo.up.railway.app |
| **Loki** | https://loki.up.railway.app |
| **Prometheus** | https://prometheus-production-08db.up.railway.app |

### Getting Started

1. Navigate to **Grafana** at https://logs.gatewayz.ai
2. Log in with your admin credentials
3. All datasources (Loki, Prometheus, Tempo) are pre-configured and ready to use
4. Start creating dashboards and exploring your observability data
5. Configure your applications to send logs, metrics, and traces to the respective services

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GatewayZ Applications                     │
└──────────────┬──────────────┬──────────────┬────────────────┘
               │              │              │
        ┌──────▼──┐    ┌──────▼──┐   ┌──────▼──┐
        │   Logs  │    │ Metrics │   │ Traces  │
        └──────┬──┘    └──────┬──┘   └──────┬──┘
               │              │              │
        ┌──────▼──────────────▼──────────────▼──────┐
        │                                           │
        │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
        │  │  Loki   │  │Prometheus│  │ Tempo  │  │
        │  └────┬────┘  └────┬─────┘  └───┬────┘  │
        │       │            │            │       │
        │       └────────────┬────────────┘       │
        │                    │                    │
        │              ┌─────▼──────┐             │
        │              │  Grafana   │             │
        │              └────────────┘             │
        │                                        │
        └────────────────────────────────────────┘
```

## Sending Data to the Stack

### From Your Applications

Your applications can send telemetry data to the observability stack using these internal Railway URLs:

| Service | Internal URL | Purpose |
|---------|--------------|---------|
| **Loki** | `http://loki.railway.internal:3100` | Send and query logs |
| **Prometheus** | `http://prometheus.railway.internal:9090` | Send and query metrics |
| **Tempo** | `http://tempo.railway.internal:3200` | Query traces |
| **Tempo (HTTP Ingest)** | `http://tempo.railway.internal:4318` | Send traces via HTTP |
| **Tempo (GRPC Ingest)** | `http://tempo.railway.internal:4317` | Send traces via GRPC |

### Configuration Example

In your Railway service environment variables, reference the Grafana service to access these URLs:

```
LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}
PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
TEMPO_URL=${{Grafana.TEMPO_INTERNAL_URL}}
TEMPO_HTTP_INGEST=${{Grafana.TEMPO_INTERNAL_HTTP_INGEST}}
TEMPO_GRPC_INGEST=${{Grafana.TEMPO_INTERNAL_GRPC_INGEST}}
```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GF_SECURITY_ADMIN_USER` | Username for the Grafana admin account | `admin` |
| `GF_SECURITY_ADMIN_PASSWORD` | Password for the Grafana admin account | Auto-generated |
| `GF_DEFAULT_INSTANCE_NAME` | Name of your Grafana instance | `GatewayZ Observability` |

### Version Control

Each service has its own `VERSION` environment variable that can be set independently in each service's settings in the Railway dashboard:

- **Grafana Service**: Set `VERSION` to control the Grafana Docker image tag
- **Loki Service**: Set `VERSION` to control the Loki Docker image tag
- **Prometheus Service**: Set `VERSION` to control the Prometheus Docker image tag
- **Tempo Service**: Set `VERSION` to control the Tempo Docker image tag

By default, all services use the `latest` tag, but you can pin specific versions for stability:

Examples:
- Grafana: `VERSION=11.5.2`
- Loki: `VERSION=3.4.2`
- Prometheus: `VERSION=v3.2.1`
- Tempo: `VERSION=v2.7.1`

This allows you to update each component independently as needed.

## Project Structure & Services

This template deploys four interconnected services:

### Grafana
- The central visualization and dashboarding platform
- Pre-configured with connections to all other services
- Persistent volume for storing dashboards, users, and configurations
- Comes with useful plugins pre-installed
- Exposes internal URLs for other Railway services to connect to Loki, Prometheus, and Tempo

### Prometheus
- Time-series database for metrics collection
- Configured with sensible defaults for monitoring
- Persistent volume for metrics data

### Loki
- Log aggregation system designed to be cost-effective
- Horizontally scalable architecture
- Persistent volume for log storage

### Tempo
- Distributed tracing system for tracking requests across services
- High-performance trace storage
- Persistent volume for trace data

### Sentry (Optional)
- Real-time error tracking and performance monitoring
- Automatic error deduplication and grouping
- Performance transaction tracking
- Integrates with Grafana via the Sentry datasource plugin
- Requires separate account at [sentry.io](https://sentry.io) or self-hosted instance
- Applications automatically instrumented to send errors to Sentry

All services are deployed using official Docker images and configured to work together seamlessly.

## Integration Patterns

### Logs (Loki)

Send logs to Loki using standard logging libraries. Configure your application to send logs to:
```
http://loki.railway.internal:3100
```

Popular logging libraries with Loki support:
- Promtail (official log shipper)
- Fluent Bit
- Logstash
- Vector

### Metrics (Prometheus)

Instrument your applications with Prometheus client libraries to expose metrics:
```
http://prometheus.railway.internal:9090
```

Available client libraries:
- Go: `github.com/prometheus/client_golang`
- Python: `prometheus-client`
- Node.js: `prom-client`
- Java: `micrometer-prometheus`

### Traces (Tempo)

Use OpenTelemetry libraries to send distributed traces to Tempo via HTTP or GRPC:

**HTTP Ingest (recommended for most applications):**
```
http://tempo.railway.internal:4318/v1/traces
```

**GRPC Ingest (for high-volume tracing):**
```
http://tempo.railway.internal:4317
```

Example with OpenTelemetry Node.js:
```javascript
const { NodeTracerProvider } = require('@opentelemetry/node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const exporter = new OTLPTraceExporter({
  url: 'http://tempo.railway.internal:4318/v1/traces'
});
```

## Customizing Your Stack

To customize the configuration of Loki, Prometheus, or Tempo:

1. Fork the [GitHub repository](https://github.com/yourusername/grafana-railway-template)
2. Modify the configuration files in their respective directories
3. In Railway, disconnect the service you want to customize
4. Reconnect the service to your forked repository
5. Deploy the updated service

The pre-configured Grafana connections will continue to work with your customized services.

## Troubleshooting

### Services Not Connecting

If Grafana datasources show connection errors:

1. Verify all services are running in Railway dashboard
2. Check that internal URLs use the `.railway.internal` domain
3. Ensure services are in the same Railway project
4. Review service logs for startup errors

### Data Not Appearing

- **Logs**: Verify your application is sending logs to Loki with correct labels
- **Metrics**: Check that Prometheus scrape configs are correct and targets are reachable
- **Traces**: Ensure your application is exporting traces with correct service names

## Documentation

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)

---

**GatewayZ Observability Stack** - Deployed on Railway
