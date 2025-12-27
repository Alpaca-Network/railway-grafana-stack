# 🧪 Tests Directory

Comprehensive test suite for Observability Stack configuration validation.

## Structure

```
tests/
├── test_stack_configuration.py  # Configuration & YAML validation
└── README.md                    # This file
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-report=html

# Run specific test class
pytest tests/test_stack_configuration.py::TestYAMLConfiguration -v

# Run specific test
pytest tests/test_stack_configuration.py::TestYAMLConfiguration::test_prometheus_config_valid_yaml -v
```

## Test Files Overview

### `test_stack_configuration.py` (25+ tests)

**Configuration validation tests:**
- `TestYAMLConfiguration` - YAML syntax and structure validation
- `TestGrafanaConfiguration` - Grafana datasources and dashboards
- `TestDockerFiles` - Dockerfile port and configuration checks
- `TestConfigurationIntegrity` - Cross-service configuration validation

**What it tests:**
✅ YAML syntax validity for all config files
✅ Prometheus scrape job configuration (production + staging)
✅ Loki storage and retention setup
✅ Tempo OTLP receiver configuration
✅ Grafana datasource URLs and structure
✅ Docker service port bindings
✅ Service networking (0.0.0.0 listen addresses)
✅ Configuration consistency across services

## Running Tests

### Local Development

```bash
# All tests
pytest tests/ -v

# With coverage report (opens in browser)
pytest tests/ -v --cov=. --cov-report=html && open htmlcov/index.html

# Run specific test group
pytest tests/test_stack_configuration.py::TestYAMLConfiguration -v
pytest tests/test_stack_configuration.py::TestDockerFiles -v
pytest tests/test_stack_configuration.py::TestConfigurationIntegrity -v
```

### CI/CD

Tests run automatically on:
- **Staging:** Every push to `staging` branch
- **Production:** Every push to `main` branch + scheduled every 6 hours

View results in GitHub Actions → Your branch/commit

## Test Coverage

Validates:
- ✅ All YAML configuration files have valid syntax
- ✅ Prometheus is configured with production and staging scrape jobs
- ✅ Loki has proper storage and retention configuration
- ✅ Tempo has OTLP receivers configured for traces
- ✅ Grafana datasources point to the right services
- ✅ All required dashboards exist and are valid JSON
- ✅ Services listen on correct addresses and ports
- ✅ Configuration is consistent across services

## Success Criteria

✅ All tests pass
✅ YAML validation succeeds
✅ Service configuration verified
✅ No configuration regressions
✅ Port bindings correct

## Troubleshooting

**Tests won't run:**
```bash
# Install dependencies from requirements.txt
pip install -r requirements.txt

# Verify pytest is installed
pytest --version
```

**YAML parsing errors:**
```bash
# Verify YAML files are syntactically correct
python -c "import yaml; yaml.safe_load(open('prometheus/prom.yml'))"
python -c "import yaml; yaml.safe_load(open('loki/loki.yml'))"
python -c "import yaml; yaml.safe_load(open('tempo/tempo.yml'))"
```

**Missing configuration files:**
- Ensure all YAML configs exist in their directories
- Check that docker-compose.yml is in the root directory
- Verify Grafana provisioning files are in place

## Adding New Tests

1. Add tests to `test_stack_configuration.py`

2. Follow naming convention:
   ```python
   class TestComponentName:
       def test_action_validates_result(self):
           """Docstring explaining what's tested"""
           # Arrange
           # Act
           # Assert
   ```

3. Use fixtures for common setup:
   ```python
   @pytest.fixture
   def repo_root(self):
       return Path(__file__).parent.parent
   ```

4. Run tests to verify:
   ```bash
   pytest tests/test_stack_configuration.py -v
   ```

## CI/CD Workflows

### Staging Workflow (`.github/workflows/test-staging.yml`)
- Trigger: Push to staging
- Tests: Configuration validation
- Duration: 3-5 minutes

### Production Workflow (`.github/workflows/test-production.yml`)
- Trigger: Push to main + scheduled every 6 hours
- Tests: Full configuration validation + coverage report
- Duration: 5-10 minutes

## Documentation

- Configuration guide: See [`RAILWAY_DEPLOYMENT_GUIDE.md`](../RAILWAY_DEPLOYMENT_GUIDE.md)
- Quick start: See [`QUICK_START.md`](../QUICK_START.md)
- CI/CD workflows: See `.github/workflows/`

## Support

For test issues:
1. Run tests with `-vv` flag for verbose output: `pytest tests/ -vv`
2. Check specific test failure: `pytest tests/test_stack_configuration.py::TestYAMLConfiguration -v`
3. Check GitHub Actions logs for CI/CD failures

---

**Last Updated:** December 27, 2025
**Status:** ✅ Production Ready
**Test Count:** 25+
**Focus:** Configuration Validation
