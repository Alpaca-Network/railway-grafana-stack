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
        prom_config = repo_root / "prometheus" / "prometheus.yml"
        assert prom_config.exists(), "prometheus/prometheus.yml not found"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Prometheus config is empty"
        assert "scrape_configs" in config, "Missing scrape_configs section"

    def test_prometheus_scrape_jobs_configured(self, repo_root):
        """Test Prometheus has required scrape jobs"""
        prom_config = repo_root / "prometheus" / "prometheus.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        job_names = [job.get("job_name") for job in scrape_configs]

        # Check for required jobs
        assert "prometheus" in job_names, "Prometheus self-scrape job missing"
        assert "gatewayz_production" in job_names, "Production scrape job missing"
        assert "gatewayz_production" in job_names, "Production scrape job missing"

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

        # Dashboards are organized into subdirectories (executive/, backend/, logs/, etc.)
        dashboard_files = list(dashboards_dir.glob("**/*.json"))
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
            "tempo": ["3200", "4317", "4318"],
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



    def test_prometheus_production_scrape_job_configured(self, repo_root):
        """Test Prometheus has production scrape job configured"""
        prom_config = repo_root / "prometheus" / "prometheus.yml"

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
        # Target can be either placeholder (raw config) or resolved value (runtime)
        target = static_configs[0].get("targets", [None])[0]
        valid_targets = ["FASTAPI_TARGET", "api.gatewayz.ai"]
        assert target in valid_targets, \
            f"Production job target '{target}' not in valid targets: {valid_targets}"


class TestMimirConfiguration:
    """Test Mimir configuration and integration"""

    @pytest.fixture
    def repo_root(self):
        """Get repository root directory"""
        return Path(__file__).parent.parent

    def test_mimir_config_exists(self, repo_root):
        """Test Mimir configuration files exist"""
        mimir_config = repo_root / "mimir" / "mimir.yml"
        mimir_railway_config = repo_root / "mimir" / "mimir-railway.yml"

        assert mimir_config.exists(), "mimir/mimir.yml not found"
        assert mimir_railway_config.exists(), "mimir/mimir-railway.yml not found"

    def test_mimir_railway_config_valid_yaml(self, repo_root):
        """Test Mimir Railway configuration is valid YAML"""
        mimir_config = repo_root / "mimir" / "mimir-railway.yml"

        with open(mimir_config) as f:
            config = yaml.safe_load(f)

        assert config is not None, "Mimir Railway config is empty"
        assert "server" in config, "Missing server section in Mimir config"
        assert config["server"]["http_listen_port"] == 9009, "Mimir should listen on 9009"

    def test_mimir_monolithic_mode(self, repo_root):
        """Test Mimir is configured for monolithic mode"""
        mimir_config = repo_root / "mimir" / "mimir-railway.yml"

        with open(mimir_config) as f:
            config = yaml.safe_load(f)

        assert config.get("target") == "all", "Mimir should be in monolithic mode (target: all)"
        assert config.get("multitenancy_enabled") is False, "Multitenancy should be disabled"

    def test_mimir_storage_configured(self, repo_root):
        """Test Mimir has storage configuration"""
        mimir_config = repo_root / "mimir" / "mimir-railway.yml"

        with open(mimir_config) as f:
            config = yaml.safe_load(f)

        assert "blocks_storage" in config, "Mimir missing blocks_storage configuration"
        blocks_storage = config["blocks_storage"]
        assert blocks_storage.get("backend") == "filesystem", "Mimir should use filesystem backend"

    def test_mimir_limits_configured(self, repo_root):
        """Test Mimir has resource limits configured"""
        mimir_config = repo_root / "mimir" / "mimir-railway.yml"

        with open(mimir_config) as f:
            config = yaml.safe_load(f)

        assert "limits" in config, "Mimir missing limits configuration"
        limits = config["limits"]
        assert "max_global_series_per_user" in limits, "Missing max_global_series_per_user"
        assert "ingestion_rate" in limits, "Missing ingestion_rate"

    def test_mimir_listens_on_all_interfaces(self, repo_root):
        """Test Mimir is configured to listen on 0.0.0.0"""
        mimir_config = repo_root / "mimir" / "mimir-railway.yml"

        with open(mimir_config) as f:
            content = f.read()

        assert "http_listen_address: 0.0.0.0" in content, "Mimir should listen on 0.0.0.0 for HTTP"
        assert "grpc_listen_address: 0.0.0.0" in content, "Mimir should listen on 0.0.0.0 for gRPC"

    def test_prometheus_remote_write_to_mimir(self, repo_root):
        """Test Prometheus has remote_write configured for Mimir"""
        prom_config = repo_root / "prometheus" / "prometheus.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        assert "remote_write" in config, "Prometheus missing remote_write configuration"
        remote_write = config["remote_write"]
        assert len(remote_write) > 0, "Prometheus remote_write is empty"

        mimir_remote_write = remote_write[0]
        assert mimir_remote_write.get("name") == "mimir-remote-write", \
            "First remote_write should be mimir-remote-write"
        # URL contains placeholder that gets substituted at runtime
        url = mimir_remote_write.get("url", "")
        assert "api/v1/push" in url, "Remote write URL should contain api/v1/push endpoint"

    def test_prometheus_mimir_scrape_job(self, repo_root):
        """Test Prometheus has Mimir scrape job configured"""
        prom_config = repo_root / "prometheus" / "prometheus.yml"

        with open(prom_config) as f:
            config = yaml.safe_load(f)

        scrape_configs = config.get("scrape_configs", [])
        mimir_job = next(
            (job for job in scrape_configs if job.get("job_name") == "mimir"),
            None
        )

        assert mimir_job is not None, "Mimir scrape job not found"
        static_configs = mimir_job.get("static_configs", [])
        assert len(static_configs) > 0, "Mimir job missing static_configs"

    def test_grafana_mimir_datasource_exists(self, repo_root):
        """Test Grafana has Mimir datasource configured"""
        datasource_file = repo_root / "grafana" / "provisioning" / "datasources" / "mimir.yml"
        assert datasource_file.exists(), "Grafana Mimir datasource not found"

        with open(datasource_file) as f:
            config = yaml.safe_load(f)

        assert "datasources" in config, "Mimir datasource file missing datasources section"
        datasources = config["datasources"]
        assert len(datasources) > 0, "No datasources defined in mimir.yml"

        mimir_ds = datasources[0]
        assert mimir_ds.get("name") == "Mimir", "Datasource should be named 'Mimir'"
        assert mimir_ds.get("type") == "prometheus", "Mimir datasource type should be prometheus"

    def test_mimir_dockerfile_exists(self, repo_root):
        """Test Mimir Dockerfile exists"""
        dockerfile = repo_root / "mimir" / "Dockerfile"
        assert dockerfile.exists(), "Mimir Dockerfile not found"

    def test_docker_compose_has_mimir_service(self, repo_root):
        """Test docker-compose includes Mimir service"""
        compose_file = repo_root / "docker-compose.yml"

        with open(compose_file) as f:
            config = yaml.safe_load(f)

        services = config.get("services", {})
        assert "mimir" in services, "Mimir service not found in docker-compose.yml"

        mimir_service = services["mimir"]
        assert "build" in mimir_service or "image" in mimir_service, \
            "Mimir service should have build or image configuration"

    def test_entrypoint_handles_mimir_substitution(self, repo_root):
        """Test Prometheus entrypoint.sh handles Mimir URL substitution"""
        entrypoint = repo_root / "prometheus" / "entrypoint.sh"
        assert entrypoint.exists(), "Prometheus entrypoint.sh not found"

        content = entrypoint.read_text()
        assert "MIMIR_URL" in content, "Entrypoint should handle MIMIR_URL substitution"
        assert "MIMIR_TARGET" in content, "Entrypoint should handle MIMIR_TARGET substitution"
        assert "mimir.railway.internal" in content, "Entrypoint should reference Railway internal URL"
