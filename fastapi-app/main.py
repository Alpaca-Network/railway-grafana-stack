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
from metrics_parser import get_metrics_parser

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

# Synthetic data generation endpoints
@app.get("/generate-synthetic-data")
async def generate_synthetic_data(count: int = 10):
    """Generate synthetic logs, metrics, and traces for testing the observability stack"""
    logger.info(f"Generating {count} synthetic data points")
    tracer = trace.get_tracer(__name__)
    
    for i in range(count):
        with tracer.start_as_current_span(f"synthetic_operation_{i}"):
            # Log at different levels
            logger.debug(f"Synthetic debug log #{i}")
            logger.info(f"Synthetic info log #{i} - Processing request")
            
            if i % 5 == 0:
                logger.warning(f"Synthetic warning log #{i} - High latency detected")
            
            if i % 10 == 0:
                logger.error(f"Synthetic error log #{i} - Recoverable error occurred")
            
            # Simulate some processing
            time.sleep(0.1)
    
    return {
        "message": f"Generated {count} synthetic data points",
        "service": SERVICE_NAME,
        "timestamp": time.time()
    }

@app.get("/generate-load")
async def generate_load(duration: int = 10, requests_per_second: int = 5):
    """Generate continuous load with logs, metrics, and traces"""
    logger.info(f"Starting load generation for {duration} seconds at {requests_per_second} req/s")
    tracer = trace.get_tracer(__name__)
    
    import asyncio
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration:
        with tracer.start_as_current_span("load_request"):
            request_count += 1
            logger.info(f"Load request #{request_count}")
            
            # Simulate variable latency
            latency = 0.05 + (request_count % 3) * 0.02
            await asyncio.sleep(latency)
            
            # Record a metric
            REQUEST_COUNT.labels(
                method="GET",
                endpoint="/generate-load",
                status=200,
                service=SERVICE_NAME
            ).inc()
        
        # Rate limiting
        await asyncio.sleep(1.0 / requests_per_second)
    
    elapsed = time.time() - start_time
    return {
        "message": "Load generation complete",
        "requests_generated": request_count,
        "duration_seconds": elapsed,
        "service": SERVICE_NAME
    }

@app.get("/simulate-errors")
async def simulate_errors(error_count: int = 5, error_type: str = "exception"):
    """Simulate various error scenarios for testing error tracking"""
    logger.info(f"Simulating {error_count} {error_type} errors")
    tracer = trace.get_tracer(__name__)
    errors_logged = 0
    
    for i in range(error_count):
        with tracer.start_as_current_span(f"error_simulation_{i}"):
            try:
                logger.warning(f"Simulating error scenario #{i+1}")
                
                if error_type == "exception":
                    raise ValueError(f"Simulated error #{i+1}: Database connection timeout")
                elif error_type == "timeout":
                    logger.error(f"Simulated timeout error #{i+1}: Request took too long")
                elif error_type == "validation":
                    logger.error(f"Simulated validation error #{i+1}: Invalid input data")
                else:
                    logger.error(f"Simulated generic error #{i+1}")
                    
                errors_logged += 1
            except Exception as e:
                logger.error(f"Caught error: {str(e)}")
                errors_logged += 1
                if error_type == "exception" and i < error_count - 1:
                    continue
    
    return {
        "message": "Error simulation complete",
        "errors_simulated": error_count,
        "errors_logged": errors_logged,
        "service": SERVICE_NAME
    }

@app.get("/trace-example")
async def trace_example(depth: int = 3):
    """Generate a distributed trace with multiple spans"""
    logger.info(f"Starting trace example with depth {depth}")
    tracer = trace.get_tracer(__name__)
    
    def create_nested_spans(current_depth: int):
        if current_depth <= 0:
            return
        
        with tracer.start_as_current_span(f"operation_level_{depth - current_depth + 1}"):
            logger.info(f"Executing operation at level {depth - current_depth + 1}")
            time.sleep(0.1)
            create_nested_spans(current_depth - 1)
    
    create_nested_spans(depth)
    
    return {
        "message": "Trace example complete",
        "trace_depth": depth,
        "service": SERVICE_NAME
    }

@app.get("/dashboard-data")
async def dashboard_data():
    """Return summary of current metrics for dashboard visualization"""
    logger.info("Dashboard data requested")
    
    return {
        "service": SERVICE_NAME,
        "uptime_seconds": time.time(),
        "endpoints": [
            {"path": "/", "description": "Root endpoint"},
            {"path": "/hello", "description": "Hello endpoint with name parameter"},
            {"path": "/slow", "description": "Slow endpoint (2s delay)"},
            {"path": "/error", "description": "Error endpoint"},
            {"path": "/metrics", "description": "Prometheus metrics"},
            {"path": "/health", "description": "Health check"},
            {"path": "/generate-synthetic-data", "description": "Generate synthetic logs/traces"},
            {"path": "/generate-load", "description": "Generate continuous load"},
            {"path": "/simulate-errors", "description": "Simulate error scenarios"},
            {"path": "/trace-example", "description": "Generate distributed traces"},
            {"path": "/dashboard-data", "description": "This endpoint"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    # Support Railway's PORT environment variable
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
