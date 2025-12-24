FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY health_service_exporter.py .

ENV HEALTH_SERVICE_URL=https://health-service-production.up.railway.app
ENV SCRAPE_INTERVAL=30
ENV METRICS_PORT=8002
ENV REQUEST_TIMEOUT=10

EXPOSE 8002

CMD ["python", "health_service_exporter.py"]
