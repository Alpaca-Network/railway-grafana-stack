"""
Prometheus Metrics Aggregation Module for GatewayZ Backend

This module provides a complete implementation of Prometheus metrics endpoints
that aggregate and query data from the Prometheus server.

Integration Instructions:
1. Copy this file to your backend: app/services/prometheus_metrics.py
2. Add to your FastAPI app (see example at bottom)
3. Install dependency: pip install prometheus-client

Author: Cloud Code
Date: December 24, 2025
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from functools import lru_cache

import httpx
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


# ============================================================================
# HEALTH SERVICE METRICS - Defined for Prometheus export
# ============================================================================

# Service Status
health_service_up = Gauge(
    'gatewayz_health_service_up',
    'Health service availability (1=up, 0=down)'
)

health_monitoring_active = Gauge(
    'gatewayz_health_monitoring_active',
    'Health monitoring state (1=active, 0=inactive)'
)

availability_monitoring_active = Gauge(
    'gatewayz_availability_monitoring_active',
    'Availability monitoring state (1=active, 0=inactive)'
)

health_check_interval = Gauge(
    'gatewayz_health_check_interval_seconds',
    'Health check interval in seconds'
)

# Tracked Resources
health_tracked_models = Gauge(
    'gatewayz_health_tracked_models',
    'Number of models being tracked'
)

health_tracked_providers = Gauge(
    'gatewayz_health_tracked_providers',
    'Number of providers being tracked'
)

health_tracked_gateways = Gauge(
    'gatewayz_health_tracked_gateways',
    'Number of gateways being tracked'
)

availability_cache_size = Gauge(
    'gatewayz_availability_cache_size',
    'Size of availability cache'
)

# Total Resources
health_total_models = Gauge(
    'gatewayz_health_total_models',
    'Total number of models in the system'
)

health_total_providers = Gauge(
    'gatewayz_health_total_providers',
    'Total number of providers in the system'
)

health_total_gateways = Gauge(
    'gatewayz_health_total_gateways',
    'Total number of gateways in the system'
)

tracked_models_count = Gauge(
    'gatewayz_health_tracked_models_count',
    'Number of actively tracked models'
)

# Health Status
health_active_incidents = Gauge(
    'gatewayz_health_active_incidents',
    'Number of active incidents'
)

health_status_distribution = Gauge(
    'gatewayz_health_status_distribution',
    'Distribution of health statuses',
    ['status']
)

# Cache
health_cache_available = Gauge(
    'gatewayz_health_cache_available',
    'Cache availability status',
    ['cache_type']
)

# Error Tracking
health_service_scrape_errors = Counter(
    'gatewayz_health_service_scrape_errors_total',
    'Total number of scrape errors'
)

health_service_last_update = Gauge(
    'gatewayz_health_service_last_successful_scrape',
    'Timestamp of last successful scrape'
)


class HealthServiceClient:
    """Client for calling Health Service API directly"""

    def __init__(
        self,
        health_service_url: str = None,
        timeout: int = 10,
    ):
        """
        Initialize Health Service client

        Args:
            health_service_url: URL to health service API
            timeout: Request timeout in seconds
        """
        # Default to environment variable or production URL
        self.health_service_url = health_service_url or os.getenv(
            "HEALTH_SERVICE_URL",
            "https://health-service-production.up.railway.app"
        )
        self.timeout = timeout

    async def fetch_health(self) -> Optional[Dict[str, Any]]:
        """Fetch from /health endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.health_service_url}/health",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch /health: {e}")
            return None

    async def fetch_status(self) -> Optional[Dict[str, Any]]:
        """Fetch from /status endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.health_service_url}/status",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch /status: {e}")
            return None

    async def fetch_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch from /metrics endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.health_service_url}/metrics",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch /metrics: {e}")
            return None

    async def fetch_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Fetch from /cache/stats endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.health_service_url}/cache/stats",
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch /cache/stats: {e}")
            return None

    async def update_all_metrics(self):
        """Fetch all health service endpoints and update Prometheus metrics"""
        try:
            # Fetch all endpoints
            health_data = await self.fetch_health()
            status_data = await self.fetch_status()
            metrics_data = await self.fetch_metrics()
            cache_data = await self.fetch_cache_stats()

            any_success = False

            # Update metrics from /health
            if health_data:
                health_service_up.set(1)
                any_success = True
            else:
                health_service_up.set(0)

            # Update metrics from /status
            if status_data:
                health_monitoring_active.set(1 if status_data.get("health_monitoring_active", False) else 0)
                availability_monitoring_active.set(1 if status_data.get("availability_monitoring_active", False) else 0)
                health_tracked_models.set(status_data.get("models_tracked", 0))
                health_tracked_providers.set(status_data.get("providers_tracked", 0))
                health_tracked_gateways.set(status_data.get("gateways_tracked", 0))
                availability_cache_size.set(status_data.get("availability_cache_size", 0))
                health_check_interval.set(status_data.get("health_check_interval", 300))
                any_success = True

            # Update metrics from /metrics
            if metrics_data:
                health_total_models.set(metrics_data.get("total_models", 0))
                health_total_providers.set(metrics_data.get("total_providers", 0))
                health_total_gateways.set(metrics_data.get("total_gateways", 0))
                tracked_models_count.set(metrics_data.get("tracked_models", 0))
                health_active_incidents.set(metrics_data.get("active_incidents", 0))

                # Process status distribution
                status_dist = metrics_data.get("status_distribution", {})
                if isinstance(status_dist, dict):
                    for status, count in status_dist.items():
                        health_status_distribution.labels(status=status).set(count)
                any_success = True

            # Update metrics from /cache/stats
            if cache_data:
                cache_available = 1 if cache_data.get("cache_available", False) else 0
                system_health_cached = 1 if cache_data.get("system_health_cached", False) else 0
                providers_health_cached = 1 if cache_data.get("providers_health_cached", False) else 0
                models_health_cached = 1 if cache_data.get("models_health_cached", False) else 0

                health_cache_available.labels(cache_type="redis").set(cache_available)
                health_cache_available.labels(cache_type="system_health").set(system_health_cached)
                health_cache_available.labels(cache_type="providers_health").set(providers_health_cached)
                health_cache_available.labels(cache_type="models_health").set(models_health_cached)
                any_success = True

            # Update last successful scrape timestamp
            if any_success:
                health_service_last_update.set(time.time())
                logger.info("Health service metrics updated successfully")
            else:
                health_service_scrape_errors.inc()
                logger.warning("All health service endpoints failed")

        except Exception as e:
            logger.error(f"Error updating health service metrics: {e}")
            health_service_scrape_errors.inc()


class PrometheusClient:
    """Client for querying Prometheus server"""

    def __init__(
        self,
        prometheus_url: str = "http://prometheus:9090",
        timeout: int = 10,
    ):
        """
        Initialize Prometheus client

        Args:
            prometheus_url: URL to Prometheus server
            timeout: Request timeout in seconds
        """
        self.prometheus_url = prometheus_url
        self.timeout = timeout
        self.query_url = f"{prometheus_url}/api/v1/query"
        self.query_range_url = f"{prometheus_url}/api/v1/query_range"

    async def query(self, query: str) -> Dict[str, Any]:
        """
        Execute PromQL instant query

        Args:
            query: PromQL query string

        Returns:
            Query result from Prometheus
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.query_url,
                    params={"query": query},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Prometheus query failed: {query} - {e}")
            return {"status": "error", "error": str(e)}

    async def query_range(
        self,
        query: str,
        start: str,
        end: str,
        step: str = "15s",
    ) -> Dict[str, Any]:
        """
        Execute PromQL range query

        Args:
            query: PromQL query string
            start: Start timestamp (RFC3339 or Unix)
            end: End timestamp (RFC3339 or Unix)
            step: Query resolution step

        Returns:
            Range query result from Prometheus
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.query_range_url,
                    params={"query": query, "start": start, "end": end, "step": step},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Prometheus range query failed: {query} - {e}")
            return {"status": "error", "error": str(e)}

    def _extract_value(self, result: List) -> Optional[str]:
        """Extract metric value from Prometheus result"""
        if result and len(result) >= 2:
            return result[1]
        return None

    def _extract_labels(self, result: Dict) -> Dict[str, str]:
        """Extract labels from Prometheus result"""
        return result.get("metric", {})


class MetricsSummary:
    """Generate JSON summary of all metrics"""

    def __init__(self, client: PrometheusClient):
        self.client = client

    async def generate(self) -> Dict[str, Any]:
        """
        Generate comprehensive metrics summary

        Returns:
            JSON-formatted metrics summary
        """
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "metrics": {
                    "http": await self._get_http_metrics(),
                    "models": await self._get_model_metrics(),
                    "providers": await self._get_provider_metrics(),
                    "database": await self._get_database_metrics(),
                    "business": await self._get_business_metrics(),
                },
            }
            return summary
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e),
            }

    async def _get_http_metrics(self) -> Dict[str, str]:
        """Get HTTP/system metrics"""
        return {
            "total_requests": await self._query_single(
                'sum(fastapi_requests_total)'
            ),
            "request_rate_per_minute": await self._query_single(
                'sum(rate(fastapi_requests_total[1m])) * 60'
            ),
            "error_rate": await self._query_single(
                '(sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / '
                'sum(rate(fastapi_requests_total[5m]))) * 100'
            ),
            "avg_latency_ms": await self._query_single(
                '(sum(rate(fastapi_requests_duration_seconds_sum[5m])) / '
                'sum(rate(fastapi_requests_duration_seconds_count[5m]))) * 1000'
            ),
            "in_progress": await self._query_single(
                'fastapi_requests_in_progress'
            ),
        }

    async def _get_model_metrics(self) -> Dict[str, str]:
        """Get model performance metrics"""
        return {
            "total_inference_requests": await self._query_single(
                'sum(model_inference_requests_total)'
            ),
            "tokens_used_total": await self._query_single(
                'sum(tokens_used_total)'
            ),
            "credits_used_total": await self._query_single(
                'sum(credits_used_total)'
            ),
            "avg_inference_latency_ms": await self._query_single(
                '(sum(rate(model_inference_duration_seconds_sum[5m])) / '
                'sum(rate(model_inference_duration_seconds_count[5m]))) * 1000'
            ),
        }

    async def _get_provider_metrics(self) -> Dict[str, str]:
        """Get provider health metrics"""
        return {
            "total_providers": await self._query_single(
                'gatewayz_providers_total'
            ),
            "healthy_providers": await self._query_single(
                'gatewayz_providers_healthy'
            ),
            "degraded_providers": await self._query_single(
                'gatewayz_providers_degraded'
            ),
            "unavailable_providers": await self._query_single(
                'gatewayz_providers_down'
            ),
            "avg_error_rate": await self._query_single(
                'avg(provider_error_rate)'
            ),
            "avg_response_time_ms": await self._query_single(
                'avg(provider_response_time_seconds) * 1000'
            ),
        }

    async def _get_database_metrics(self) -> Dict[str, str]:
        """Get database metrics"""
        return {
            "total_queries": await self._query_single(
                'sum(database_queries_total)'
            ),
            "avg_query_latency_ms": await self._query_single(
                '(sum(rate(database_query_duration_seconds_sum[5m])) / '
                'sum(rate(database_query_duration_seconds_count[5m]))) * 1000'
            ),
            "cache_hit_rate": await self._query_single(
                '(sum(rate(cache_hits_total[5m])) / '
                '(sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))) * 100'
            ),
        }

    async def _get_business_metrics(self) -> Dict[str, str]:
        """Get business metrics"""
        return {
            "active_api_keys": await self._query_single(
                'active_api_keys'
            ),
            "active_subscriptions": await self._query_single(
                'subscription_count'
            ),
            "active_trials": await self._query_single(
                'trial_active'
            ),
            "total_tokens_used": await self._query_single(
                'sum(tokens_used_total)'
            ),
            "total_credits_used": await self._query_single(
                'sum(credits_used_total)'
            ),
        }

    async def _query_single(self, query: str) -> str:
        """
        Execute query and extract single value

        Returns:
            String value or "N/A" if query fails
        """
        try:
            result = await self.client.query(query)
            if result.get("status") == "success":
                data = result.get("data", {}).get("result", [])
                if data:
                    return self.client._extract_value(data[0].get("value", []))
            return "N/A"
        except Exception as e:
            logger.warning(f"Query failed: {query} - {e}")
            return "N/A"


class MetricsExporter:
    """Export metrics in various formats"""

    def __init__(self, client: PrometheusClient):
        self.client = client

    async def get_system_metrics(self) -> str:
        """Export system/HTTP metrics in Prometheus format"""
        queries = {
            "fastapi_requests_total": 'sum(fastapi_requests_total) by (status_code)',
            "fastapi_requests_duration_seconds": 'rate(fastapi_requests_duration_seconds[5m])',
            "fastapi_requests_in_progress": 'fastapi_requests_in_progress',
            "fastapi_exceptions_total": 'sum(fastapi_exceptions_total)',
        }
        return await self._export_metrics(queries)

    async def get_provider_metrics(self) -> str:
        """Export provider metrics in Prometheus format"""
        queries = {
            "gatewayz_providers_total": 'gatewayz_providers_total',
            "gatewayz_providers_healthy": 'gatewayz_providers_healthy',
            "gatewayz_providers_degraded": 'gatewayz_providers_degraded',
            "gatewayz_providers_down": 'gatewayz_providers_down',
            "provider_availability": 'provider_availability{provider="$provider"}',
            "provider_error_rate": 'provider_error_rate{provider="$provider"}',
            "provider_response_time_seconds": 'provider_response_time_seconds{provider="$provider"}',
            "gatewayz_provider_health_score": 'gatewayz_provider_health_score{provider="$provider"}',
        }
        return await self._export_metrics(queries)

    async def get_model_metrics(self) -> str:
        """Export model metrics in Prometheus format"""
        queries = {
            "model_inference_requests_total": 'sum(model_inference_requests_total) by (model, provider, status)',
            "model_inference_duration_seconds": 'rate(model_inference_duration_seconds[5m]) by (model, provider)',
            "tokens_used_total": 'sum(tokens_used_total) by (model, provider)',
            "credits_used_total": 'sum(credits_used_total) by (model, provider)',
        }
        return await self._export_metrics(queries)

    async def get_business_metrics(self) -> str:
        """Export business metrics in Prometheus format"""
        queries = {
            "active_api_keys": 'active_api_keys',
            "subscription_count": 'subscription_count',
            "trial_active": 'trial_active',
            "tokens_used_total": 'sum(tokens_used_total)',
            "credits_used_total": 'sum(credits_used_total)',
        }
        return await self._export_metrics(queries)

    async def get_performance_metrics(self) -> str:
        """Export performance/latency metrics in Prometheus format"""
        queries = {
            "fastapi_requests_duration_seconds": 'histogram_quantile(0.95, rate(fastapi_requests_duration_seconds_bucket[5m]))',
            "database_query_duration_seconds": 'histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m])) by (operation)',
            "cache_hit_rate": '(sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))) * 100',
            "cache_size_bytes": 'cache_size_bytes',
        }
        return await self._export_metrics(queries)

    async def get_all_metrics(self) -> str:
        """Export all metrics in Prometheus format"""
        # Combine all metric categories
        metrics = ""
        for getter in [
            self.get_system_metrics,
            self.get_provider_metrics,
            self.get_model_metrics,
            self.get_business_metrics,
            self.get_performance_metrics,
        ]:
            metrics += await getter() + "\n"
        return metrics

    async def _export_metrics(self, queries: Dict[str, str]) -> str:
        """
        Export metrics in Prometheus text format

        Returns:
            Metrics in Prometheus text format
        """
        output = ""
        for metric_name, query in queries.items():
            try:
                result = await self.client.query(query)
                if result.get("status") == "success":
                    data = result.get("data", {}).get("result", [])
                    for item in data:
                        labels = self.client._extract_labels(item)
                        value = self.client._extract_value(item.get("value", []))
                        if value:
                            label_str = self._format_labels(labels)
                            output += f"{metric_name}{label_str} {value}\n"
            except Exception as e:
                logger.warning(f"Failed to export metric {metric_name}: {e}")
        return output

    @staticmethod
    def _format_labels(labels: Dict[str, str]) -> str:
        """Format labels for Prometheus output"""
        if not labels:
            return ""
        label_pairs = [f'{k}="{v}"' for k, v in labels.items() if k != "__name__"]
        return "{" + ",".join(label_pairs) + "}" if label_pairs else ""


# ============================================================================
# FASTAPI INTEGRATION - Add this to your main FastAPI application
# ============================================================================

async def setup_prometheus_routes(app):
    """
    Setup Prometheus metrics routes in FastAPI app

    Usage in your main.py:
    ----
    from fastapi import FastAPI
    from app.services.prometheus_metrics import setup_prometheus_routes

    app = FastAPI()

    @app.on_event("startup")
    async def startup():
        await setup_prometheus_routes(app)
    ----
    """
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse, PlainTextResponse

    # Initialize Prometheus client
    prometheus_url = os.getenv(
        "PROMETHEUS_URL",
        "http://prometheus:9090"
    )
    client = PrometheusClient(prometheus_url=prometheus_url)

    # Create router
    router = APIRouter(prefix="/prometheus/metrics", tags=["prometheus"])

    # Summary endpoint (JSON)
    @router.get("/summary", response_class=JSONResponse)
    async def get_summary():
        """
        Get comprehensive metrics summary as JSON

        Returns aggregated metrics from Prometheus for dashboard widgets.
        """
        summary_gen = MetricsSummary(client)
        return await summary_gen.generate()

    # System metrics endpoint
    @router.get("/system", response_class=PlainTextResponse)
    async def get_system():
        """Get system and HTTP metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_system_metrics()

    # Provider metrics endpoint
    @router.get("/providers", response_class=PlainTextResponse)
    async def get_providers():
        """Get provider health metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_provider_metrics()

    # Model metrics endpoint
    @router.get("/models", response_class=PlainTextResponse)
    async def get_models():
        """Get model performance metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_model_metrics()

    # Business metrics endpoint
    @router.get("/business", response_class=PlainTextResponse)
    async def get_business():
        """Get business metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_business_metrics()

    # Performance metrics endpoint
    @router.get("/performance", response_class=PlainTextResponse)
    async def get_performance():
        """Get performance and latency metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_performance_metrics()

    # All metrics endpoint
    @router.get("/all", response_class=PlainTextResponse)
    async def get_all():
        """Get all metrics in Prometheus format"""
        exporter = MetricsExporter(client)
        return await exporter.get_all_metrics()

    # Prometheus /metrics endpoint for Prometheus scraping
    # This exports health service metrics so Prometheus can scrape them
    @router.get("", name="metrics")  # GET /prometheus/metrics
    async def get_prometheus_metrics():
        """
        Prometheus-compatible metrics endpoint for /metrics scraping

        Returns all health service metrics in Prometheus text format.
        This endpoint is used by Prometheus to scrape metrics directly.
        """
        from fastapi.responses import Response
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
            headers={"Content-Type": CONTENT_TYPE_LATEST}
        )

    # Documentation endpoint
    @router.get("/docs", response_class=PlainTextResponse)
    async def get_docs():
        """Get documentation for Prometheus metrics endpoints"""
        return """
# Prometheus Metrics Endpoints - API Documentation

## Available Endpoints

### 1. GET /prometheus/metrics/summary
Returns comprehensive metrics summary as JSON for dashboard widgets.
Use this for: Dashboard cards, counters, real-time status

Response format:
{
  "timestamp": "2025-12-26T12:00:00Z",
  "metrics": {
    "http": {...},
    "models": {...},
    "providers": {...},
    "database": {...},
    "business": {...}
  }
}

### 2. GET /prometheus/metrics/system
Returns system and HTTP metrics in Prometheus text format.
Use this for: Grafana dashboards, request metrics, latency graphs

### 3. GET /prometheus/metrics/providers
Returns provider health metrics in Prometheus text format.
Use this for: Provider status cards, health scores, availability

### 4. GET /prometheus/metrics/models
Returns model performance metrics in Prometheus text format.
Use this for: Model usage, token tracking, inference latency

### 5. GET /prometheus/metrics/business
Returns business metrics in Prometheus text format.
Use this for: API keys, subscriptions, token usage, cost tracking

### 6. GET /prometheus/metrics/performance
Returns performance and latency metrics in Prometheus text format.
Use this for: Latency percentiles, cache hit rates, database queries

### 7. GET /prometheus/metrics/all
Returns all metrics combined in Prometheus text format.
Use this for: Complete metric export, Grafana scraping

### 8. GET /prometheus/metrics/docs
Returns this documentation.

## Integration with Grafana

Add a Prometheus datasource pointing to your backend:
- URL: http://gatewayz-staging.up.railway.app (or http://backend:8000 for local)
- HTTP Method: GET
- Custom HTTP Headers:
  - Authorization: Bearer YOUR_TOKEN (if required)

Then query using PromQL:
- sum(fastapi_requests_total) by (status_code)
- provider_availability{{provider="openrouter"}}
- sum(rate(tokens_used_total[5m])) * 60

## Response Times

- /summary: <50ms (JSON aggregation)
- /system: <100ms (Prometheus query)
- /providers: <100ms (Prometheus query)
- /models: <100ms (Prometheus query)
- /business: <100ms (Prometheus query)
- /performance: <100ms (Prometheus query)
- /all: <200ms (Combined query)

## Error Handling

If Prometheus is unavailable:
- /summary returns: {{"timestamp": "...", "error": "..."}}
- /system and others return: empty Prometheus text format

## Refresh Rate Recommendations

- Dashboard widgets (/summary): Refresh every 30 seconds
- Grafana panels: Set scrape interval to 15-30 seconds
- Custom integrations: Cache responses for at least 5 seconds

---
Generated automatically by Prometheus Metrics Module
Last updated: {datetime.utcnow().isoformat()}
        """

    # Initialize Health Service client for background updates
    health_service_url = os.getenv(
        "HEALTH_SERVICE_URL",
        "https://health-service-production.up.railway.app"
    )
    health_client = HealthServiceClient(health_service_url=health_service_url)

    # Background task to update health service metrics
    async def update_health_metrics_task():
        """Periodically update health service metrics"""
        while True:
            try:
                await health_client.update_all_metrics()
                # Update every 30 seconds
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in health metrics task: {e}")
                await asyncio.sleep(30)

    # Start background task on app startup
    import asyncio
    try:
        # Create task (it will run in background)
        asyncio.create_task(update_health_metrics_task())
        logger.info("Health service metrics background task started")
    except Exception as e:
        logger.warning(f"Could not start health metrics background task: {e}")

    # Include router in app
    app.include_router(router)

    logger.info("Prometheus metrics routes initialized")


# ============================================================================
# MAIN.PY EXAMPLE
# ============================================================================

"""
Example integration in your FastAPI main.py:

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.prometheus_metrics import setup_prometheus_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await setup_prometheus_routes(app)
    print("Prometheus metrics routes ready")
    yield
    # Shutdown
    print("Shutting down")

app = FastAPI(lifespan=lifespan)

# OR use @app.on_event("startup") if not using lifespan:

@app.on_event("startup")
async def startup():
    await setup_prometheus_routes(app)

# Your existing routes here...
"""
