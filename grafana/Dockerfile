ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# Set default datasource URLs
# Railway: Uses internal DNS (*.railway.internal)
# Local docker-compose: Override via environment variables in docker-compose.yml
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
ENV MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009

# Allow embedding Grafana panels in iframes (for admin dashboard telemetry page)
# Without this, Grafana sends X-Frame-Options: deny which blocks all iframe embeds
ENV GF_SECURITY_ALLOW_EMBEDDING=true
# ENV GF_SECURITY_COOKIE_SAMESITE=none
ENV GF_AUTH_ANONYMOUS_ENABLED=true
ENV GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer

# Copy the datasources provisioning config
COPY datasources /etc/grafana/provisioning/datasources

# Copy dashboard provisioning config
COPY provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml

# Copy dashboard folders
COPY dashboards/loki /etc/grafana/provisioning/dashboards/loki
COPY dashboards/prometheus /etc/grafana/provisioning/dashboards/prometheus
COPY dashboards/tempo /etc/grafana/provisioning/dashboards/tempo
COPY dashboards/mimir /etc/grafana/provisioning/dashboards/mimir
COPY dashboards/model_performance /etc/grafana/provisioning/dashboards/model_performance
COPY dashboards/provider /etc/grafana/provisioning/dashboards/provider
COPY dashboards/developer /etc/grafana/provisioning/dashboards/developer
COPY dashboards/golden-signals /etc/grafana/provisioning/dashboards/golden-signals

# ============================================================
# ALERTING PROVISIONING
# Copy alert rules, contact points, and notification policies
# ============================================================
COPY provisioning/alerting /etc/grafana/provisioning/alerting

# Expose Grafana port
EXPOSE 3000
