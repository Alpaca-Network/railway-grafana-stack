ARG VERSION=11.5.2

# Stage that normalizes repository structure so the final image can be built
# regardless of whether the Railway build context is the repo root or the
# grafana/ subdirectory.
FROM alpine:3.20 AS provisioning
WORKDIR /workspace

# Copy everything in the build context so we can inspect the directory layout
# (Railway sometimes provides either the repo root or grafana/ as the context).
COPY . .

# Collect datasources and dashboards into a predictable location. If the build
# context doesn't include them (e.g., when Railway builds Tempo/Loki with the
# repo root Dockerfile), create empty placeholders so those services still build.
RUN set -euxo pipefail \
 && mkdir -p /out/datasources /out/dashboards \
 && if [ -d "./grafana/datasources" ]; then \
        cp -R ./grafana/datasources/. /out/datasources/; \
    elif [ -d "./datasources" ]; then \
        cp -R ./datasources/. /out/datasources/; \
    else \
        echo "WARNING: grafana datasources directory not found in build context; using empty directory" >&2; \
    fi \
 && if [ -d "./grafana/dashboards" ]; then \
        cp -R ./grafana/dashboards/. /out/dashboards/; \
    elif [ -d "./dashboards" ]; then \
        cp -R ./dashboards/. /out/dashboards/; \
    else \
        echo "WARNING: grafana dashboards directory not found in build context; using empty directory" >&2; \
    fi

FROM grafana/grafana-oss:${VERSION}

USER root

ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200

COPY --from=provisioning /out/datasources /etc/grafana/provisioning/datasources
COPY --from=provisioning /out/dashboards /etc/grafana/provisioning/dashboards

EXPOSE 3000
