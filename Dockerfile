# Multi-stage Dockerfile for Railway deployment
# This Dockerfile builds and runs the complete Grafana observability stack

FROM docker:latest

WORKDIR /app

COPY docker-compose.yml .
COPY grafana/ ./grafana/
COPY loki/ ./loki/
COPY prometheus/ ./prometheus/
COPY tempo/ ./tempo/

RUN apk add --no-cache docker-compose

EXPOSE 3000 3100 3200 9090 4317 4318

CMD ["docker-compose", "up"]
