# GatewayZ Grafana Observability Stack

This is the observability and monitoring stack for the GatewayZ system, deployed on Railway.

**Grafana Dashboard**: [https://logs.gatewayz.ai/login](https://logs.gatewayz.ai/login)

## Overview

This repository contains a complete Grafana observability stack with integrated services for logging, metrics, and distributed tracing:

- **Grafana**: The leading open-source analytics and monitoring solution
- **Loki**: A horizontally-scalable, highly-available log aggregation system
- **Prometheus**: A powerful metrics collection and alerting system
- **Tempo**: A high-scale distributed tracing backend
- **Sentry**: Real-time error tracking and performance monitoring (optional)

This stack provides comprehensive observability for the GatewayZ system, enabling real-time monitoring, log aggregation, metrics collection, and distributed tracing across all services.

### Key Features

- **Pre-configured Integration**: _All services come pre-connected_, so Grafana is ready to query your data immediately.
- **Persistent Storage**: All four services use Railway volumes to ensure your data, dashboards, and configurations persist between updates and deploys.
- **Version Control**: Pin specific Docker image versions for each service using environment variables.
- **Customizable**: Fork the repository to customize configuration files for any service. You can take full control and edit anything you'd need to as you scale.
- **One-Click Deploy**: Get a complete Grafana-based observability stack running in minutes.
- **Optional Sentry Integration**: Add real-time error tracking and performance monitoring to your stack for comprehensive error management.

## Accessing the Stack

**Production Dashboard**: [https://logs.gatewayz.ai/login](https://logs.gatewayz.ai/login)

To access the Grafana dashboard:
1. Navigate to [https://logs.gatewayz.ai/login](https://logs.gatewayz.ai/login)
2. Log in with your GatewayZ credentials
3. View dashboards, metrics, logs, and traces for all GatewayZ services

## Local Development

To run the stack locally using Docker Compose:

```bash
docker-compose up
```

Then access Grafana at `http://localhost:3000`

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GF_SECURITY_ADMIN_USER` | Username for the Grafana admin account | Required input |
| `GF_SECURITY_ADMIN_PASSWORD` | Password for the Grafana admin account | Auto-generated secure string |
| `GF_DEFAULT_INSTANCE_NAME` | Name of your Grafana instance | `Grafana on Railway` |
| `GF_INSTALL_PLUGINS` | Comma-separated list of Grafana plugins to install | `grafana-simple-json-datasource,grafana-piechart-panel,grafana-worldmap-panel,grafana-clock-panel,grafana-sentry-datasource` |
| `SENTRY_DSN` | (Optional) Sentry project DSN for error tracking in applications | Empty (Sentry disabled) |
| `SENTRY_AUTH_TOKEN` | (Optional) Sentry auth token for Grafana datasource | Empty |
| `SENTRY_ENVIRONMENT` | (Optional) Environment name for Sentry | `production` |
| `SENTRY_TRACE_SAMPLE_RATE` | (Optional) Fraction of transactions to sample (0-1) | `1.0` |

### Internal Service URLs

The Grafana service exposes these environment variables that you can reference in your other Railway applications to easily send data to your observability stack:

| Variable | Description | Usage |
|----------|-------------|-------|
| `LOKI_INTERNAL_URL` | Internal URL for the Loki service | Use in your applications to send logs to and query Loki |
| `PROMETHEUS_INTERNAL_URL` | Internal URL for the Prometheus service | Use in your applications to send metrics to and query Prometheus |
| `TEMPO_INTERNAL_URL` | Internal URL for the Tempo service | Use in your applications to query Tempo |

These variables make it easy to configure your other Railway services to send telemetry data to your observability stack.

Tempo also exposes a few variables to make it easier to push tracing information to the service using either HTTP or GRPC

| Variable | Description | Usage |
|----------|-------------|-------|
| `INTERNAL_HTTP_INGEST` | Internal HTTP ingest server URL for Tempo | Use in your applications to send traces to tempo via HTTP |
| `INTERNAL_GRPC_INGEST` | Internal GRPC ingest server URL for Tempo | Use in your applications to send traces to tempo via GRPC |

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

## Connecting Your Applications

### Using [Locomotive](https://railway.com/template/jP9r-f) for Loki

You can easily ingest *all* of your railway logs into Loki from *any* service using [Locomotive](https://railway.com/template/jP9r-f). Just spin up their template, drop in your Railway API key, the ID of the services you want to monitor, and a link to your new Loki instance and logs will start flowing! no code changes needed anywhere!

### Using OpenTelemetry libraries for Tempo 

Tempo is a bit different than both Prometheus and Loki in that exposes separate GRPC and HTTP servers on ports `:4317` and `:4318` respectively specifically for ingesting your tracing data or "spans".

When configuring your application to send traces to Tempo, please use one of the preconfigured variables in the Tempo service: `INTERNAL_HTTP_INGEST` or `INTERNAL_GRPC_INGEST`.

Another thing to note is that the ingest API endpoint for the HTTP server is `/v1/traces`. For a working example of this in a node.js express API, see `/examples/api/tracer.js` in our GitHub repository.

### Using Sentry for Error Tracking (Optional)

To add real-time error tracking to your applications:

1. Create a Sentry account at [sentry.io](https://sentry.io) (free tier available)
2. Create a project and copy the DSN
3. Set these environment variables in your Railway services:
   ```
   SENTRY_DSN=${{Grafana.SENTRY_DSN}}
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACE_SAMPLE_RATE=1.0
   ```
4. See [SENTRY_SETUP.md](SENTRY_SETUP.md) for complete setup instructions

The Sentry datasource plugin is pre-installed in Grafana, allowing you to query Sentry issues and view error trends in your dashboards.

### Using otherwise standard observability tooling

To send data from your other Railway applications to this observability stack:

1. In your application's Railway service, add environment variables that reference the internal URLs:
   ```
   LOKI_URL=${{Grafana.LOKI_INTERNAL_URL}}
   PROMETHEUS_URL=${{Grafana.PROMETHEUS_INTERNAL_URL}}
   TEMPO_URL=${{Grafana.TEMPO_INTERNAL_URL}}
   SENTRY_DSN=${{Grafana.SENTRY_DSN}}  # Optional
   ```
2. Configure your application's logging, metrics, tracing, or error tracking libraries to use these URLs
3. Your application data will automatically appear in your Grafana dashboards

## Configuration

To customize the configuration of Loki, Prometheus, or Tempo:

1. Modify the configuration files in their respective directories (`./loki/`, `./prometheus/`, `./tempo/`)
2. Update the corresponding Dockerfiles if needed
3. Commit and push changes to the main branch
4. Railway will automatically detect the changes and redeploy

The pre-configured Grafana connections will continue to work with your customized services.

## Additional Resources

- [Locomotive: a loki transport for railway services](https://railway.com/template/jP9r-f)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Sentry Integration Guide](SENTRY_SETUP.md)
- [Grafana Sentry Datasource Plugin](https://grafana.com/grafana/plugins/grafana-sentry-datasource/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Grafana Community Forums](https://community.grafana.com/)
- [Grafana Plugins Directory](https://grafana.com/grafana/plugins/)

---

**GatewayZ Observability Stack** - Deployed on Railway for comprehensive system monitoring and observability.
