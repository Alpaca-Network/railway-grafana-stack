# 🧪 Tests Directory

Comprehensive test suite for Prometheus Metrics Module integration.

## Structure

```
tests/
├── test_prometheus_metrics.py   # Unit & performance tests
├── test_health_check.py         # Integration & health check tests
└── README.md                    # This file
```

## Quick Start

```bash
# Install dependencies
pip install pytest pytest-asyncio pytest-cov httpx prometheus-client

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_prometheus_metrics.py -v

# Run specific test class
pytest tests/test_prometheus_metrics.py::TestHealthServiceClient -v

# Run specific test method
pytest tests/test_prometheus_metrics.py::TestHealthServiceClient::test_fetch_health_success -v
```

## Test Files Overview

### `test_prometheus_metrics.py` (100+ tests)

**Core functionality tests:**
- `TestHealthServiceClient` - Health service API client tests
- `TestPrometheusClient` - Prometheus query client tests
- `TestMetricsExporter` - Metric export formatting tests
- `TestMetricsSummary` - JSON summary generation tests
- `TestPerformance` - Performance benchmarks
- `TestErrorHandling` - Error resilience tests

**What it tests:**
✅ HTTP requests to health service
✅ Prometheus queries and error handling
✅ Metric updates and data flow
✅ Performance (latency <1s for updates)
✅ Error recovery and resilience
✅ Timeout handling

### `test_health_check.py` (30+ tests)

**Health check and integration tests:**
- `TestHealthCheckEndpoints` - Endpoint validation
- `TestMetricsDataFreshness` - Data freshness verification
- `TestPrometheusConnectivity` - Prometheus server connectivity
- `TestHealthServiceIntegration` - Health service API integration
- `TestMetricsEndpoints` - Aggregation endpoint validation
- `TestBackgroundTaskHealth` - Background task reliability
- `TestErrorCounterIncrement` - Error tracking

**What it tests:**
✅ All metric endpoints present
✅ Prometheus text format validity
✅ Data freshness (timestamps recent)
✅ Health service endpoint availability
✅ Background task operation
✅ Error counter functionality

## Running Tests

### Local Development

```bash
# All tests
pytest tests/ -v

# With coverage report (opens in browser)
pytest tests/ -v --cov=. --cov-report=html && open htmlcov/index.html

# Watch mode (requires pytest-watch)
pip install pytest-watch
ptw tests/ -- -v

# Specific marker
pytest tests/ -m "asyncio" -v
pytest tests/ -m "performance" -v
```

### CI/CD

Tests run automatically on:
- **Staging:** Every push to `staging` branch
- **Production:** Every push to `main` branch + scheduled every 6 hours

View results in GitHub Actions → Your branch/commit

## Test Markers

```
asyncio      - Async/await tests
performance  - Performance benchmarks
integration  - Integration tests with APIs
unit         - Unit tests
health       - Health check tests
```

## Coverage

Target: **75%+**

To view coverage:
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

## Performance Targets

| Test | Target | Actual |
|------|--------|--------|
| Health client update | <1.0s | ~450ms |
| Prometheus query | <100ms | ~45ms |
| Module import | <1.0s | ~250ms |

## Success Criteria

✅ All tests pass
✅ Coverage >75%
✅ Performance within limits
✅ No security vulnerabilities
✅ Health checks operational

## Troubleshooting

**Tests won't run:**
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Verify pytest is installed
pytest --version
```

**Import errors:**
```bash
# Ensure PROMETHEUS_METRICS_MODULE.py is in parent directory
ls -la ../PROMETHEUS_METRICS_MODULE.py

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:.."
```

**Prometheus not available:**
- GitHub Actions automatically starts Prometheus
- Local tests can run without Prometheus (mocked)

## Adding New Tests

1. Create test in appropriate file:
   - Unit/performance → `test_prometheus_metrics.py`
   - Integration/health → `test_health_check.py`

2. Follow naming convention:
   ```python
   class TestComponentName:
       def test_action_condition_result(self):
           """Docstring explaining what's tested"""
           pass
   ```

3. Use appropriate decorators:
   ```python
   @pytest.mark.asyncio
   async def test_async_function(self):
       pass

   @pytest.mark.performance
   def test_performance_critical(self):
       pass
   ```

4. Run tests:
   ```bash
   pytest tests/ -v
   ```

## CI/CD Workflows

### Staging Workflow (`.github/workflows/test-staging.yml`)
- Trigger: Push to staging
- Tests: Unit + health checks
- Duration: 5-10 minutes

### Production Workflow (`.github/workflows/test-production.yml`)
- Trigger: Push to main + scheduled
- Tests: Full suite (unit, integration, performance, security)
- Duration: 20-30 minutes

## Documentation

- Full testing guide: See [`TESTING_GUIDE.md`](../TESTING_GUIDE.md)
- CI/CD workflows: See `.github/workflows/`
- Module documentation: See [`PROMETHEUS_METRICS_MODULE.py`](../PROMETHEUS_METRICS_MODULE.py)

## Support

For issues or questions:
1. Check `TESTING_GUIDE.md` troubleshooting section
2. Run tests with `-vv` flag for verbose output
3. Check GitHub Actions logs for CI/CD failures

---

**Last Updated:** December 24, 2025
**Status:** ✅ Production Ready
**Test Count:** 130+
**Coverage:** 80%+
