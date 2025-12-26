"""
Comprehensive tests for Prometheus Metrics Module

Tests cover:
- Unit tests for metric updates
- Integration tests for health service client
- Performance tests
- Health check endpoints
- Error handling

Run with: pytest tests/test_prometheus_metrics.py -v
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PROMETHEUS_METRICS_MODULE import (
    HealthServiceClient,
    PrometheusClient,
    MetricsSummary,
    MetricsExporter,
    health_service_up,
    health_active_incidents,
    health_tracked_models,
    health_status_distribution,
    health_cache_available,
)


class TestHealthServiceClient:
    """Test HealthServiceClient class"""

    @pytest.fixture
    def client(self):
        """Create a test client"""
        return HealthServiceClient(
            health_service_url="http://localhost:8001",
            timeout=5
        )

    @pytest.mark.asyncio
    async def test_fetch_health_success(self, client):
        """Test successful /health endpoint fetch"""
        mock_response = {"status": "healthy"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_health()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_fetch_health_timeout(self, client):
        """Test /health endpoint timeout handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = asyncio.TimeoutError("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_health()
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_status_success(self, client):
        """Test successful /status endpoint fetch"""
        mock_response = {
            "health_monitoring_active": True,
            "models_tracked": 50,
            "providers_tracked": 16,
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_status()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_fetch_metrics_success(self, client):
        """Test successful /metrics endpoint fetch"""
        mock_response = {
            "total_models": 100,
            "active_incidents": 2,
            "status_distribution": {"healthy": 14, "degraded": 1, "down": 1}
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_metrics()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_fetch_cache_stats_success(self, client):
        """Test successful /cache/stats endpoint fetch"""
        mock_response = {
            "cache_available": True,
            "system_health_cached": True,
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = Mock()
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_cache_stats()
            assert result == mock_response

    @pytest.mark.asyncio
    async def test_update_all_metrics_success(self, client):
        """Test successful update of all metrics"""
        mock_health = {"status": "healthy"}
        mock_status = {
            "health_monitoring_active": True,
            "availability_monitoring_active": True,
            "models_tracked": 50,
            "providers_tracked": 16,
            "gateways_tracked": 8,
            "availability_cache_size": 1000,
            "health_check_interval": 300,
        }
        mock_metrics = {
            "total_models": 100,
            "total_providers": 20,
            "total_gateways": 15,
            "tracked_models": 50,
            "active_incidents": 2,
            "status_distribution": {"healthy": 14, "degraded": 1, "down": 1}
        }
        mock_cache = {
            "cache_available": True,
            "system_health_cached": True,
            "providers_health_cached": True,
            "models_health_cached": True,
        }

        with patch.object(client, 'fetch_health', return_value=mock_health):
            with patch.object(client, 'fetch_status', return_value=mock_status):
                with patch.object(client, 'fetch_metrics', return_value=mock_metrics):
                    with patch.object(client, 'fetch_cache_stats', return_value=mock_cache):
                        await client.update_all_metrics()

                        # Verify metrics were updated
                        assert health_service_up._value.get() == 1.0
                        assert health_tracked_models._value.get() == 50.0

    @pytest.mark.asyncio
    async def test_update_all_metrics_partial_failure(self, client):
        """Test metric updates with partial endpoint failures"""
        mock_status = {
            "health_monitoring_active": True,
            "models_tracked": 50,
        }

        with patch.object(client, 'fetch_health', return_value=None):
            with patch.object(client, 'fetch_status', return_value=mock_status):
                with patch.object(client, 'fetch_metrics', return_value=None):
                    with patch.object(client, 'fetch_cache_stats', return_value=None):
                        await client.update_all_metrics()

                        # Service should be down (fetch_health returned None)
                        assert health_service_up._value.get() == 0.0
                        # But status metrics should be updated
                        assert health_tracked_models._value.get() == 50.0


class TestPrometheusClient:
    """Test PrometheusClient class"""

    @pytest.fixture
    def client(self):
        """Create a test Prometheus client"""
        return PrometheusClient(prometheus_url="http://localhost:9090")

    @pytest.mark.asyncio
    async def test_query_success(self, client):
        """Test successful Prometheus query"""
        mock_response = {
            "status": "success",
            "data": {
                "resultType": "instant",
                "result": [
                    {
                        "metric": {"__name__": "test_metric"},
                        "value": [1234567890, "42"]
                    }
                ]
            }
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.query("up")
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_query_failure(self, client):
        """Test failed Prometheus query"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = Exception("Connection failed")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.query("up")
            assert result["status"] == "error"

    def test_extract_value(self, client):
        """Test value extraction from result"""
        result = [1234567890, "42.5"]
        value = client._extract_value(result)
        assert value == "42.5"

    def test_extract_labels(self, client):
        """Test label extraction from metric"""
        metric_dict = {
            "metric": {
                "__name__": "test_metric",
                "instance": "localhost:9090",
                "job": "prometheus"
            }
        }
        labels = client._extract_labels(metric_dict)
        assert labels["job"] == "prometheus"
        assert labels["instance"] == "localhost:9090"


class TestMetricsExporter:
    """Test MetricsExporter class"""

    @pytest.fixture
    def client(self):
        """Create a mock Prometheus client"""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock()
        mock_client._extract_value = Mock(return_value="100")
        mock_client._extract_labels = Mock(return_value={})
        return mock_client

    @pytest.fixture
    def exporter(self, client):
        """Create metrics exporter"""
        return MetricsExporter(client)

    @pytest.mark.asyncio
    async def test_get_system_metrics(self, exporter):
        """Test system metrics export"""
        exporter.client.query = AsyncMock(return_value={
            "status": "success",
            "data": {"result": []}
        })

        result = await exporter.get_system_metrics()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_provider_metrics(self, exporter):
        """Test provider metrics export"""
        exporter.client.query = AsyncMock(return_value={
            "status": "success",
            "data": {"result": []}
        })

        result = await exporter.get_provider_metrics()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_format_labels(self, exporter):
        """Test Prometheus label formatting"""
        labels = {"provider": "openrouter", "status": "healthy"}
        formatted = exporter._format_labels(labels)
        assert "provider" in formatted
        assert "openrouter" in formatted


class TestMetricsSummary:
    """Test MetricsSummary class"""

    @pytest.fixture
    def client(self):
        """Create a mock Prometheus client"""
        mock_client = Mock(spec=PrometheusClient)
        mock_client.query = AsyncMock()
        return mock_client

    @pytest.fixture
    def summary(self, client):
        """Create metrics summary generator"""
        return MetricsSummary(client)

    @pytest.mark.asyncio
    async def test_generate_summary(self, summary):
        """Test summary generation"""
        summary.client.query = AsyncMock(return_value={
            "status": "success",
            "data": {"result": [{"value": [0, "100"]}]}
        })

        result = await summary.generate()
        assert "timestamp" in result
        assert "metrics" in result
        assert isinstance(result["timestamp"], str)


class TestPerformance:
    """Performance tests for Prometheus metrics"""

    @pytest.mark.asyncio
    async def test_health_client_response_time(self):
        """Test that health service client is responsive"""
        client = HealthServiceClient(health_service_url="http://localhost:8001")

        start_time = time.time()
        with patch.object(client, 'fetch_health', return_value={"status": "healthy"}):
            with patch.object(client, 'fetch_status', return_value={}):
                with patch.object(client, 'fetch_metrics', return_value={}):
                    with patch.object(client, 'fetch_cache_stats', return_value={}):
                        await client.update_all_metrics()

        elapsed = time.time() - start_time
        # Should complete in less than 1 second
        assert elapsed < 1.0, f"Metric update took {elapsed}s (should be <1s)"

    @pytest.mark.asyncio
    async def test_prometheus_query_performance(self):
        """Test that Prometheus queries are fast"""
        client = PrometheusClient()

        start_time = time.time()
        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = {
                "status": "success",
                "data": {"result": []}
            }
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            await client.query("up")

        elapsed = time.time() - start_time
        # Query should complete in less than 100ms
        assert elapsed < 0.1, f"Query took {elapsed}s (should be <0.1s)"


class TestErrorHandling:
    """Test error handling and resilience"""

    @pytest.mark.asyncio
    async def test_health_client_handles_connection_error(self):
        """Test graceful handling of connection errors"""
        client = HealthServiceClient()

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.get.side_effect = ConnectionError("Host unreachable")
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_health()
            assert result is None

    @pytest.mark.asyncio
    async def test_health_client_handles_invalid_json(self):
        """Test handling of invalid JSON responses"""
        client = HealthServiceClient()

        with patch('httpx.AsyncClient') as mock_client:
            mock_async_client = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.side_effect = ValueError("Invalid JSON")
            mock_async_client.get.return_value = mock_response_obj
            mock_client.return_value.__aenter__.return_value = mock_async_client

            result = await client.fetch_health()
            assert result is None

    @pytest.mark.asyncio
    async def test_metrics_update_continues_on_failure(self):
        """Test that metric update continues even if one endpoint fails"""
        client = HealthServiceClient()

        with patch.object(client, 'fetch_health', return_value=None):
            with patch.object(client, 'fetch_status', return_value={"models_tracked": 50}):
                with patch.object(client, 'fetch_metrics', return_value=None):
                    with patch.object(client, 'fetch_cache_stats', return_value=None):
                        # Should not raise exception
                        await client.update_all_metrics()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
