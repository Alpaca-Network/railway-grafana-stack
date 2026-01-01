ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# Set default datasource URLs (can be overridden by env vars)
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200

# copy the datasources and dashboard provisioning config
COPY datasources /etc/grafana/provisioning/datasources
COPY provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml

# copy dashboard subdirectories
COPY dashboards/backend /etc/grafana/provisioning/dashboards/backend
COPY dashboards/executive /etc/grafana/provisioning/dashboards/executive
COPY dashboards/gateway /etc/grafana/provisioning/dashboards/gateway
COPY dashboards/logs /etc/grafana/provisioning/dashboards/logs
COPY dashboards/models /etc/grafana/provisioning/dashboards/models

# Expose Grafana port
EXPOSE 3000