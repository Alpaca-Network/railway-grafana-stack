FROM python:3.11-slim

WORKDIR /app

RUN pip install prometheus-client

COPY health-metrics-generator.py .

CMD ["python", "health-metrics-generator.py"]
