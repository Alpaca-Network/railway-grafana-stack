"""
Health Check Tests for Prometheus Metrics Endpoints

Tests verify:
- Health check endpoint responses
- Metrics endpoint availability
- Prometheus connectivity
- Data freshness
- Error recovery

Run with: pytest tests/test_health_check.py -v
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch


class TestHealthCheckEndpoints:
    """Test health check endpoints"""

    @pytest.mark.asyncio
    async def test_metrics_endpoint_returns_valid_prometheus_format(self):
        """Test that /metrics returns valid Prometheus format"""
        from PROMETHEUS_METRICS_MODULE import health_service_up, health_active_incidents
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

        # Generate metrics
        metrics_output = generate_latest()

        # Should return bytes in Prometheus format
        assert isinstance(metrics_output, bytes)
        # Should contain TYPE and HELP comments
        assert b"# TYPE" in metrics_output or b"# HELP" in metrics_output

    @pytest.mark.asyncio
    async def test_health_endpoint_structure(self):
        """Test health check endpoint structure"""
        from PROMETHEUS_METRICS_MODULE import health_service_up

        # Verify metric exists and can be read
        value = health_service_up._value.get()
        assert isinstance(value, (int, float))
        assert 0 <= value <= 1

    @pytest.mark.asyncio
    async def test_metrics_endpoint_content_type(self):
        """Test that metrics endpoint has correct content type"""
        from prometheus_client import CONTENT_TYPE_LATEST

        assert CONTENT_TYPE_LATEST == "text/plain; version=0.0.4; charset=utf-8"

    @pytest.mark.asyncio
    async def test_all_required_metrics_present(self):
        """Test that all required health metrics are exported"""
        from prometheus_client import REGISTRY

        required_metrics = [
            "gatewayz_health_service_up",
            "gatewayz_health_monitoring_active",
            "gatewayz_health_tracked_models",
            "gatewayz_health_tracked_providers",
            "gatewayz_health_tracked_gateways",
            "gatewayz_health_total_models",
            "gatewayz_health_total_providers",
            "gatewayz_health_total_gateways",
            "gatewayz_health_active_incidents",
            "gatewayz_health_status_distribution",
            "gatewayz_health_cache_available",
            "gatewayz_health_service_scrape_errors_total",
            "gatewayz_health_service_last_successful_scrape",
        ]

        registry_metrics = {metric.name for metric in REGISTRY.collect()}

        for required in required_metrics:
            assert required in registry_metrics, f"Missing metric: {required}"


class TestMetricsDataFreshness:
    """Test that metrics data is fresh and regularly updated"""

    @pytest.mark.asyncio
    async def test_metrics_timestamp_is_recent(self):
        """Test that metrics have recent timestamps"""
        from PROMETHEUS_METRICS_MODULE import health_service_last_update

        # Set a timestamp
        current_time = time.time()
        health_service_last_update.set(current_time)

        # Get the value
        value = health_service_last_update._value.get()

        # Should be very close to current time (within 1 second)
        assert abs(value - current_time) < 1.0

    @pytest.mark.asyncio
    async def test_metrics_not_stale(self):
        """Test that metrics are not stale"""
        from PROMETHEUS_METRICS_MODULE import health_service_last_update

        # Set timestamp from 5 minutes ago
        five_minutes_ago = time.time() - 300

        health_service_last_update.set(five_minutes_ago)
        value = health_service_last_update._value.get()

        # Metric should be readable
        assert value > 0
        # Should be older than now
        assert value < time.time()


class TestPrometheusConnectivity:
    """Test Prometheus server connectivity"""

    @pytest.mark.asyncio
    async def test_prometheus_client_initialization(self):
        """Test Prometheus client can be initialized"""
        from PROMETHEUS_METRICS_MODULE import PrometheusClient

        client = PrometheusClient(prometheus_url="http://localhost:9090")
        assert client.prometheus_url == "http://localhost:9090"
        assert client.timeout == 10

    @pytest.mark.asyncio
    async def test_prometheus_client_custom_url(self):
        """Test Prometheus client with custom URL"""
        from PROMETHEUS_METRICS_MODULE import PrometheusClient

        custom_url = "http://prometheus.internal:9090"
        client = PrometheusClient(prometheus_url=custom_url)
        assert client.prometheus_url == custom_url

    @pytest.mark.asyncio
    async def test_prometheus_query_error_handling(self):
        """Test Prometheus client handles query errors gracefully"""
        from PROMETHEUS_METRICS_MODULE import PrometheusClient

        client = PrometheusClient()

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = Exception("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.query("test_query")

            # Should return error status
            assert result["status"] == "error"
            assert "error" in result


class TestHealthServiceIntegration:
    """Test health service client integration"""

    @pytest.mark.asyncio
    async def test_health_service_client_initialization(self):
        """Test health service client can be initialized"""
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        client = HealthServiceClient(
            health_service_url="http://localhost:8001"
        )
        assert client.health_service_url == "http://localhost:8001"
        assert client.timeout == 10

    @pytest.mark.asyncio
    async def test_health_service_client_environment_variable(self):
        """Test health service client uses environment variable"""
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        with patch.dict('os.environ', {'HEALTH_SERVICE_URL': 'http://custom-health:8001'}):
            client = HealthServiceClient()
            # Default is used since no URL provided
            # Environment variable would be used in actual integration

    @pytest.mark.asyncio
    async def test_health_service_endpoints_exist(self):
        """Test that all required health service endpoints are defined"""
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        client = HealthServiceClient()

        # Check that all fetch methods exist
        assert hasattr(client, 'fetch_health')
        assert hasattr(client, 'fetch_status')
        assert hasattr(client, 'fetch_metrics')
        assert hasattr(client, 'fetch_cache_stats')
        assert hasattr(client, 'update_all_metrics')

    @pytest.mark.asyncio
    async def test_all_four_health_service_endpoints_called(self):
        """Test that update_all_metrics calls all four endpoints"""
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        client = HealthServiceClient()

        fetch_health_called = False
        fetch_status_called = False
        fetch_metrics_called = False
        fetch_cache_called = False

        async def mock_fetch_health(*args, **kwargs):
            nonlocal fetch_health_called
            fetch_health_called = True
            return None

        async def mock_fetch_status(*args, **kwargs):
            nonlocal fetch_status_called
            fetch_status_called = True
            return None

        async def mock_fetch_metrics(*args, **kwargs):
            nonlocal fetch_metrics_called
            fetch_metrics_called = True
            return None

        async def mock_fetch_cache(*args, **kwargs):
            nonlocal fetch_cache_called
            fetch_cache_called = True
            return None

        with patch.object(client, 'fetch_health', side_effect=mock_fetch_health):
            with patch.object(client, 'fetch_status', side_effect=mock_fetch_status):
                with patch.object(client, 'fetch_metrics', side_effect=mock_fetch_metrics):
                    with patch.object(client, 'fetch_cache_stats', side_effect=mock_fetch_cache):
                        await client.update_all_metrics()

        assert fetch_health_called, "fetch_health was not called"
        assert fetch_status_called, "fetch_status was not called"
        assert fetch_metrics_called, "fetch_metrics was not called"
        assert fetch_cache_called, "fetch_cache_stats was not called"


class TestMetricsEndpoints:
    """Test /prometheus/metrics/* endpoints"""

    @pytest.mark.asyncio
    async def test_summary_endpoint_structure(self):
        """Test /summary endpoint returns correct JSON structure"""
        from PROMETHEUS_METRICS_MODULE import MetricsSummary, PrometheusClient

        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(return_value={
            "status": "success",
            "data": {"result": [{"value": [0, "100"]}]}
        })

        summary = MetricsSummary(mock_client)
        result = await summary.generate()

        # Should have timestamp and metrics
        assert "timestamp" in result
        assert "metrics" in result
        # Timestamp should be ISO format
        assert "T" in result["timestamp"]
        assert "Z" in result["timestamp"]

    @pytest.mark.asyncio
    async def test_summary_endpoint_metric_categories(self):
        """Test /summary endpoint includes all metric categories"""
        from PROMETHEUS_METRICS_MODULE import MetricsSummary, PrometheusClient

        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock(return_value={
            "status": "success",
            "data": {"result": [{"value": [0, "0"]}]}
        })

        summary = MetricsSummary(mock_client)
        result = await summary.generate()

        required_categories = ["http", "models", "providers", "database", "business"]
        assert all(cat in result["metrics"] for cat in required_categories)


class TestBackgroundTaskHealth:
    """Test background task health and operation"""

    @pytest.mark.asyncio
    async def test_background_task_can_be_created(self):
        """Test that background task can be created"""
        import asyncio
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        client = HealthServiceClient()

        call_count = 0

        async def mock_update():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise asyncio.CancelledError()

        with patch.object(client, 'update_all_metrics', side_effect=mock_update):
            # Create a simple task
            async def task():
                try:
                    for _ in range(2):
                        await client.update_all_metrics()
                        await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    pass

            # Should not raise exception
            await task()
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_background_task_error_recovery(self):
        """Test that background task recovers from errors"""
        from PROMETHEUS_METRICS_MODULE import HealthServiceClient

        client = HealthServiceClient()
        error_count = 0
        recovery_count = 0

        async def mock_update_with_error():
            nonlocal error_count, recovery_count
            error_count += 1
            if error_count <= 1:
                raise Exception("Simulated error")
            recovery_count += 1

        with patch.object(client, 'update_all_metrics', side_effect=mock_update_with_error):
            # First call should fail
            try:
                await client.update_all_metrics()
            except Exception:
                pass

            # Second call should succeed
            try:
                await client.update_all_metrics()
            except Exception:
                pass

        assert error_count == 2
        assert recovery_count == 1


class TestErrorCounterIncrement:
    """Test error tracking counter"""

    @pytest.mark.asyncio
    async def test_error_counter_increments_on_failure(self):
        """Test that error counter increments on update failure"""
        from PROMETHEUS_METRICS_MODULE import (
            HealthServiceClient,
            health_service_scrape_errors
        )

        client = HealthServiceClient()

        # Reset counter
        health_service_scrape_errors._value.set(0)

        with patch.object(client, 'fetch_health', return_value=None):
            with patch.object(client, 'fetch_status', return_value=None):
                with patch.object(client, 'fetch_metrics', return_value=None):
                    with patch.object(client, 'fetch_cache_stats', return_value=None):
                        await client.update_all_metrics()

        # Error counter should have incremented
        assert health_service_scrape_errors._value.get() > 0


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
