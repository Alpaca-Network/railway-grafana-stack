ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# Set default datasource URLs (can be overridden by env vars)
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
ENV MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009

# Clean up any old/stale dashboard folders from previous builds
# Also remove Grafana's internal database cache to ensure deleted dashboards don't persist
RUN rm -rf /etc/grafana/provisioning/dashboards/executive \
    /etc/grafana/provisioning/dashboards/backend \
    /etc/grafana/provisioning/dashboards/*.json \
    /var/lib/grafana/grafana.db \
    /var/lib/grafana/sessions \
    2>/dev/null || true

# Copy the datasources and dashboard provisioning config
COPY datasources /etc/grafana/provisioning/datasources
COPY provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml

# Copy all dashboard JSON files (flat structure - no subdirectories)
COPY dashboards/*.json /etc/grafana/provisioning/dashboards/

# ============================================================
# ALERTING PROVISIONING
# Copy alert rules, contact points, and notification policies
# ============================================================
COPY provisioning/alerting /etc/grafana/provisioning/alerting

# Expose Grafana port
EXPOSE 3000
