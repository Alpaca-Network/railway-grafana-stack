ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

USER root

ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200

COPY grafana/datasources /etc/grafana/provisioning/datasources
COPY grafana/dashboards /etc/grafana/provisioning/dashboards

EXPOSE 3000
