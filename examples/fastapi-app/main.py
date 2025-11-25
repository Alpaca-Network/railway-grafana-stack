import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, Histogram, Info, generate_latest, REGISTRY
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import time

# Configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "fastapi-app")
# Railway uses TEMPO_INTERNAL_HTTP_INGEST or TEMPO_INTERNAL_GRPC_INGEST
# For local Docker: http://tempo:4318
# For Railway: Use the internal URL provided by Railway
TEMPO_URL = os.getenv("TEMPO_URL", os.getenv("TEMPO_INTERNAL_HTTP_INGEST", "http://tempo:4318"))

# Sentry initialization
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        integrations=[
            FastApiIntegration(),
        ],
        traces_sample_rate=float(os.getenv("SENTRY_TRACE_SAMPLE_RATE", "1.0")),
        attach_stacktrace=True,
        include_local_variables=True,
    )

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup OpenTelemetry tracing
resource = Resource.create(attributes={
    "service.name": SERVICE_NAME,
})

tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

otlp_exporter = OTLPSpanExporter(
    endpoint=f"{TEMPO_URL}/v1/traces",
)

tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Instrument logging to include trace context
LoggingInstrumentor().instrument(set_logging_format=True)

# Create FastAPI app
app = FastAPI(title=SERVICE_NAME)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Prometheus metrics
# Application info metric for Grafana dashboard
APP_INFO = Info('fastapi_app', 'FastAPI application info')
APP_INFO.info({'app_name': SERVICE_NAME})

REQUEST_COUNT = Counter(
    'fastapi_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status', 'service']
)

REQUEST_DURATION = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint', 'service']
)

# Middleware for Prometheus metrics
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # Record metrics with service label
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        service=SERVICE_NAME
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path,
        service=SERVICE_NAME
    ).observe(duration)

    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

# Health check endpoint
@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"status": "healthy", "service": SERVICE_NAME}

# Example endpoints
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "FastAPI Observability Example", "service": SERVICE_NAME}

@app.get("/hello")
async def hello(name: str = "World"):
    logger.info(f"Hello endpoint called with name: {name}")

    # Create a custom span
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_hello"):
        logger.info(f"Processing hello for {name}")
        return {"message": f"Hello, {name}!", "service": SERVICE_NAME}

@app.get("/slow")
async def slow_endpoint():
    logger.info("Slow endpoint called")
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("slow_operation"):
        time.sleep(2)  # Simulate slow operation
        logger.warning("Slow operation completed")

    return {"message": "This was slow", "service": SERVICE_NAME}

@app.get("/error")
async def error_endpoint():
    logger.error("Error endpoint called - triggering error")
    raise Exception("Intentional error for testing")

if __name__ == "__main__":
    import uvicorn
    # Support Railway's PORT environment variable
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
