"""
Tests for Observability Stack Configuration

Tests validate:
- YAML configuration syntax
- Prometheus scrape configuration
- Loki configuration
- Tempo configuration
- Docker Compose configuration

Run with: pytest tests/test_stack_configuration.py -v
"""

import pytest
import yaml
import os
from pathlib import Path


class TestYAMLConfiguration:
    """Test YAML configuration files for syntax and structure"""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory"""
        return Path(__file__).parent.parent

    def test_prometheus_config_valid_yaml(self, repo_root):
        """Test Prometheus configuration is valid YAML"""
        prom_config = repo_root / "prometheus" / "prom.yml"
        assert prom_config.exists(), "prometheus/prom.yml not found"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Prometheus config is empty"
        assert "scrape_configs" in config, "Missing scrape_configs section"

    def test_prometheus_scrape_jobs_configured(self, repo_root):
        """Test Prometheus has required scrape jobs"""
        prom_config = repo_root / "prometheus" / "prom.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        job_names = [job.get("job_name") for job in scrape_configs]

        # Check for required jobs
        assert "prometheus" in job_names, "Prometheus self-scrape job missing"
        assert "gatewayz_production" in job_names, "Production scrape job missing"
        assert "gatewayz_staging" in job_names, "Staging scrape job missing"

    def test_loki_config_valid_yaml(self, repo_root):
        """Test Loki configuration is valid YAML"""
        loki_config = repo_root / "loki" / "loki.yml"
        assert loki_config.exists(), "loki/loki.yml not found"

        with open(loki_config) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Loki config is empty"
        assert "server" in config, "Missing server section in Loki config"
        assert config["server"]["http_listen_port"] == 3100, "Loki should listen on 3100"

    def test_loki_storage_configured(self, repo_root):
        """Test Loki has storage configuration"""
        loki_config = repo_root / "loki" / "loki.yml"

        with open(loki_config) as f:
            config = yaml.safe_load(f)

        assert "storage_config" in config, "Loki missing storage configuration"
        storage = config["storage_config"]
        assert "filesystem" in storage, "Loki filesystem storage not configured"

    def test_tempo_config_valid_yaml(self, repo_root):
        """Test Tempo configuration is valid YAML"""
        tempo_config = repo_root / "tempo" / "tempo.yml"
        assert tempo_config.exists(), "tempo/tempo.yml not found"

        with open(tempo_config) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Tempo config is empty"
        assert "server" in config, "Missing server section in Tempo config"
        assert config["server"]["http_listen_port"] == 3200, "Tempo should listen on 3200"

    def test_tempo_receivers_configured(self, repo_root):
        """Test Tempo has OTLP receivers"""
        tempo_config = repo_root / "tempo" / "tempo.yml"

        with open(tempo_config) as f:
            config = yaml.safe_load(f)

        assert "distributor" in config, "Tempo missing distributor configuration"
        assert "receivers" in config["distributor"], "Tempo missing receivers"
        assert "otlp" in config["distributor"]["receivers"], "Tempo missing OTLP receiver"

    def test_docker_compose_valid_yaml(self, repo_root):
        """Test docker-compose.yml is valid YAML"""
        compose_file = repo_root / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        assert config is not None, "docker-compose.yml is empty"
        assert "services" in config, "Missing services in docker-compose"

    def test_docker_compose_has_required_services(self, repo_root):
        """Test docker-compose has all required services"""
        compose_file = repo_root / "docker-compose.yml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})
        required_services = ["prometheus", "loki", "tempo", "grafana"]

        for service in required_services:
            assert service in services, f"Missing {service} service in docker-compose"


class TestGrafanaConfiguration:
    """Test Grafana configuration and dashboards"""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory"""
        return Path(__file__).parent.parent

    def test_grafana_datasources_exist(self, repo_root):
        """Test Grafana datasource files exist"""
        datasources_dir = repo_root / "grafana" / "provisioning" / "datasources"

        assert datasources_dir.exists(), "Grafana datasources directory not found"

        required_datasources = [
            "prometheus.yml",
            "loki.yml",
            "tempo.yml"
        ]

        for datasource in required_datasources:
            ds_file = datasources_dir / datasource
            assert ds_file.exists(), f"Missing datasource: {datasource}"

    def test_grafana_datasources_valid_yaml(self, repo_root):
        """Test Grafana datasource files are valid YAML"""
        datasources_dir = repo_root / "grafana" / "provisioning" / "datasources"

        datasource_files = ["prometheus.yml", "loki.yml", "tempo.yml"]

        for datasource_file in datasource_files:
            ds_path = datasources_dir / datasource_file
            with open(ds_path) as f:
                config = yaml.safe_load(f)

            assert config is not None, f"{datasource_file} is empty or invalid"
            assert "datasources" in config, f"{datasource_file} missing datasources section"

    def test_grafana_dashboards_exist(self, repo_root):
        """Test Grafana dashboard files exist"""
        dashboards_dir = repo_root / "grafana" / "dashboards"

        assert dashboards_dir.exists(), "Grafana dashboards directory not found"

        dashboard_files = list(dashboards_dir.glob("*.json"))
        assert len(dashboard_files) > 0, "No dashboard files found"

    def test_grafana_provisioning_config_exists(self, repo_root):
        """Test Grafana provisioning configuration exists"""
        dashboards_config = repo_root / "grafana" / "provisioning" / "dashboards" / "dashboards.yml"

        assert dashboards_config.exists(), "Grafana dashboards provisioning config not found"


class TestDockerFiles:
    """Test Dockerfile configurations"""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory"""
        return Path(__file__).parent.parent

    def test_all_dockerfiles_exist(self, repo_root):
        """Test all required Dockerfiles exist"""
        services = ["prometheus", "loki", "tempo", "grafana"]

        for service in services:
            dockerfile = repo_root / service / "Dockerfile"
            assert dockerfile.exists(), f"Missing Dockerfile for {service}"

    def test_dockerfiles_have_expose_statements(self, repo_root):
        """Test Dockerfiles have EXPOSE statements"""
        services = {
            "prometheus": "9090",
            "loki": "3100",
            "tempo": ["3200", "3201", "4317", "4318"],
            "grafana": "3000"
        }

        for service, ports in services.items():
            dockerfile = repo_root / service / "Dockerfile"
            content = dockerfile.read_text()

            if isinstance(ports, list):
                for port in ports:
                    assert f"EXPOSE {port}" in content or port in content, \
                        f"Port {port} not exposed in {service} Dockerfile"
            else:
                assert f"EXPOSE {ports}" in content or ports in content, \
                    f"Port {ports} not exposed in {service} Dockerfile"


class TestConfigurationIntegrity:
    """Test configuration integrity across services"""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory"""
        return Path(__file__).parent.parent

    def test_loki_listen_address_is_explicit(self, repo_root):
        """Test Loki is configured to listen on 0.0.0.0"""
        loki_config = repo_root / "loki" / "loki.yml"

        with open(loki_config) as f:
            content = f.read()

        assert "http_listen_address:" in content, "Loki missing explicit listen address"
        assert "0.0.0.0" in content, "Loki should listen on 0.0.0.0"

    def test_tempo_listen_address_is_explicit(self, repo_root):
        """Test Tempo is configured to listen on 0.0.0.0"""
        tempo_config = repo_root / "tempo" / "tempo.yml"

        with open(tempo_config) as f:
            content = f.read()

        assert "http_listen_address:" in content, "Tempo missing explicit listen address"
        assert "grpc_listen_address:" in content, "Tempo missing gRPC listen address"
        # Count how many times 0.0.0.0 appears (should be at least 2)
        assert content.count("0.0.0.0") >= 2, "Tempo should have multiple 0.0.0.0 bindings"

    def test_prometheus_staging_scrape_job_configured(self, repo_root):
        """Test Prometheus has staging scrape job configured"""
        prom_config = repo_root / "prometheus" / "prom.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        staging_job = next(
            (job for job in scrape_configs if job.get("job_name") == "gatewayz_staging"),
            None
        )

        assert staging_job is not None, "Staging scrape job not found"
        static_configs = staging_job.get("static_configs", [])
        assert len(static_configs) > 0, "Staging job missing static_configs"
        assert static_configs[0].get("targets") == ["gatewayz-staging.up.railway.app"], \
            "Staging job target not configured correctly"

    def test_prometheus_production_scrape_job_configured(self, repo_root):
        """Test Prometheus has production scrape job configured"""
        prom_config = repo_root / "prometheus" / "prom.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        prod_job = next(
            (job for job in scrape_configs if job.get("job_name") == "gatewayz_production"),
            None
        )

        assert prod_job is not None, "Production scrape job not found"
        static_configs = prod_job.get("static_configs", [])
        assert len(static_configs) > 0, "Production job missing static_configs"
        assert static_configs[0].get("targets") == ["api.gatewayz.ai"], \
            "Production job target not configured correctly"
