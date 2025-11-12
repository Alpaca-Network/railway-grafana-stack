ARG VERSION=11.5.2

FROM grafana/grafana-oss:${VERSION}

# Run as root for Railway volume permissions
USER root

# copy the datasources and dashboards
COPY datasources /etc/grafana/provisioning/datasources
COPY dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/dashboards.yml
COPY dashboards/*.json /etc/grafana/provisioning/dashboards/

# Expose Grafana port
EXPOSE 3000