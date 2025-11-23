ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# Set default datasource URLs (can be overridden by env vars)
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200

# copy the datasources and dashboards
COPY datasources /etc/grafana/provisioning/datasources
COPY dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml
COPY dashboards/*.json /etc/grafana/provisioning/dashboards/

# Expose Grafana port
EXPOSE 3000