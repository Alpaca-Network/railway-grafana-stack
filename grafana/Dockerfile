ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# Set default datasource URLs (can be overridden by env vars)
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
ENV MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009

# copy the datasources and dashboard provisioning config
COPY datasources /etc/grafana/provisioning/datasources
COPY provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml

# copy dashboard subdirectories
COPY dashboards/backend /etc/grafana/provisioning/dashboards/backend
COPY dashboards/executive /etc/grafana/provisioning/dashboards/executive
COPY dashboards/gateway /etc/grafana/provisioning/dashboards/gateway

# copy service-specific dashboards from new architecture
# NOTE: This Dockerfile is built with context `./grafana` in Railway.
# Therefore, service dashboards must be available inside this build context.
COPY dashboards/loki /etc/grafana/provisioning/dashboards/loki
COPY dashboards/prometheus /etc/grafana/provisioning/dashboards/prometheus
COPY dashboards/tempo /etc/grafana/provisioning/dashboards/tempo
COPY dashboards/mimir /etc/grafana/provisioning/dashboards/mimir

# ============================================================
# ALERTING PROVISIONING
# Copy alert rules, contact points, and notification policies
# ============================================================
COPY provisioning/alerting /etc/grafana/provisioning/alerting

# Expose Grafana port
EXPOSE 3000
