"""
Dashboard JSON Validation Tests

Tests for validating Grafana dashboard JSON files to ensure:
- Proper structure and required fields
- Valid datasource references
- Correct field naming conventions (no generic "Series A/B")
- Unique panel IDs and dashboard UIDs
- Proper configuration of all panels
"""

import json
import glob
import os
import pytest
from pathlib import Path

pytestmark = pytest.mark.dashboard

# Get dashboards directory
DASHBOARDS_DIR = Path(__file__).parent.parent / "grafana" / "dashboards"


@pytest.fixture(scope="session")
def dashboards():
    """Load all dashboard JSON files (including subdirectories)"""
    dashboard_files = sorted(DASHBOARDS_DIR.glob("**/*.json"))
    dashboards_dict = {}
    for file in dashboard_files:
        with open(file, "r") as f:
            dashboards_dict[file.name] = json.load(f)
    return dashboards_dict


@pytest.fixture(scope="session")
def dashboard_list():
    """Get list of dashboard file paths (including subdirectories)"""
    return sorted(DASHBOARDS_DIR.glob("**/*.json"))


class TestDashboardStructure:
    """Test dashboard JSON structure and required fields"""

    def test_all_dashboards_exist(self, dashboard_list):
        """Verify at least one dashboard exists"""
        assert len(list(dashboard_list)) > 0, "No dashboard files found"

    def test_all_dashboards_valid_json(self, dashboard_list):
        """Verify all dashboards are valid JSON"""
        for dashboard_file in dashboard_list:
            with open(dashboard_file, "r") as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {dashboard_file.name}: {e}")

    def test_required_fields_present(self, dashboards):
        """Verify all dashboards have required fields"""
        required_fields = ["title", "panels", "uid"]

        for dashboard_name, dashboard in dashboards.items():
            for field in required_fields:
                assert field in dashboard, f"{dashboard_name} missing '{field}'"
                assert dashboard[field] is not None, f"{dashboard_name} has null '{field}'"

    def test_all_dashboards_have_unique_uids(self, dashboards):
        """Verify all dashboard UIDs are unique"""
        uids = []
        for dashboard_name, dashboard in dashboards.items():
            uid = dashboard.get("uid")
            if uid:
                assert uid not in uids, f"Duplicate UID found: '{uid}'"
                uids.append(uid)

    def test_schema_version_reasonable(self, dashboards):
        """Verify schema versions are within reasonable range"""
        for dashboard_name, dashboard in dashboards.items():
            schema_version = dashboard.get("schemaVersion")
            if schema_version:
                assert 36 <= schema_version <= 45, \
                    f"{dashboard_name} has unreasonable schema version: {schema_version}"

    def test_title_is_string(self, dashboards):
        """Verify dashboard titles are strings"""
        for dashboard_name, dashboard in dashboards.items():
            title = dashboard.get("title")
            assert isinstance(title, str), f"{dashboard_name} title is not a string"
            assert len(title) > 0, f"{dashboard_name} has empty title"

    def test_panels_is_array(self, dashboards):
        """Verify panels field is an array"""
        for dashboard_name, dashboard in dashboards.items():
            panels = dashboard.get("panels")
            assert isinstance(panels, list), f"{dashboard_name} panels is not an array"
            assert len(panels) > 0, f"{dashboard_name} has no panels"


class TestPanelConfiguration:
    """Test individual panel configurations"""

    def test_all_panels_have_required_fields(self, dashboards):
        """Verify all panels have required fields"""
        for dashboard_name, dashboard in dashboards.items():
            for idx, panel in enumerate(dashboard.get("panels", [])):
                assert "id" in panel, f"{dashboard_name} panel {idx} missing 'id'"
                assert "type" in panel, f"{dashboard_name} panel {idx} missing 'type'"
                assert "gridPos" in panel, f"{dashboard_name} panel {idx} missing 'gridPos'"

    def test_panel_ids_unique_within_dashboard(self, dashboards):
        """Verify panel IDs are unique within each dashboard"""
        for dashboard_name, dashboard in dashboards.items():
            panel_ids = [p.get("id") for p in dashboard.get("panels", [])]
            unique_ids = set(panel_ids)
            assert len(panel_ids) == len(unique_ids), \
                f"{dashboard_name} has duplicate panel IDs: {[id for id in panel_ids if panel_ids.count(id) > 1]}"

    def test_panel_types_valid(self, dashboards):
        """Verify all panel types are valid Grafana types"""
        valid_types = {
            "text", "gauge", "stat", "timeseries", "table", "piechart",
            "barchart", "heatmap", "scatter", "logs", "graph", "canvas",
            "alertlist", "dashlist", "nodeGraph", "traces",
            "row", "bargauge", "state-timeline", "xychart"
        }

        for dashboard_name, dashboard in dashboards.items():
            for idx, panel in enumerate(dashboard.get("panels", [])):
                panel_type = panel.get("type")
                assert panel_type in valid_types, \
                    f"{dashboard_name} panel {idx} has invalid type: {panel_type}"

    def test_refresh_interval_reasonable(self, dashboards):
        """Verify dashboard refresh intervals are reasonable"""
        for dashboard_name, dashboard in dashboards.items():
            refresh = dashboard.get("refresh", "30s")
            if refresh:
                # Check if it's a valid interval format
                import re
                assert re.match(r"^\d+(ms|s|m|h)$", str(refresh)), \
                    f"{dashboard_name} has invalid refresh format: {refresh}"


class TestDatasourceConfiguration:
    """Test datasource references and configurations"""

    def test_valid_datasource_uids(self, dashboards):
        """Verify all datasource UIDs are valid"""
        valid_uids = {"grafana_prometheus", "grafana_loki", "grafana_tempo", "grafana_mimir", "-- Grafana --", "grafana", "", None}

        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                # Check panel datasource
                if "datasource" in panel and panel["datasource"]:
                    ds_uid = panel["datasource"].get("uid")
                    assert ds_uid in valid_uids, \
                        f"{dashboard_name} panel '{panel.get('title', 'unknown')}' has invalid datasource UID: {ds_uid}"

    def test_datasource_types_match_uids(self, dashboards):
        """Verify datasource types match their UIDs"""
        type_mapping = {
            "grafana_prometheus": "prometheus",
            "grafana_loki": "loki",
            "grafana_tempo": "tempo",
            "grafana_mimir": "prometheus",
            "-- Grafana --": "datasource",
        }

        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                if "datasource" in panel and panel["datasource"]:
                    ds = panel["datasource"]
                    ds_uid = ds.get("uid")
                    ds_type = ds.get("type")

                    if ds_uid in type_mapping:
                        expected_type = type_mapping[ds_uid]
                        # Type might be "datasource" which is generic
                        if ds_type and ds_type != "datasource":
                            assert ds_type == expected_type, \
                                f"{dashboard_name} datasource type mismatch for UID {ds_uid}"


class TestFieldOverrides:
    """Test field override naming conventions"""

    def test_no_generic_series_names(self, dashboards):
        """Verify no generic 'Series A/B' naming in field overrides"""
        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                overrides = panel.get("fieldConfig", {}).get("overrides", [])
                for override in overrides:
                    matcher = override.get("matcher", {})
                    field_name = matcher.get("options")

                    # Check for generic names like "Series A", "Series B", etc.
                    if field_name:
                        assert not isinstance(field_name, str) or \
                            not (field_name.startswith("Series ") and len(field_name) <= 8), \
                            f"{dashboard_name} has generic field name: '{field_name}'"

    def test_field_overrides_have_display_names(self, dashboards):
        """Verify field overrides with displayName property have non-empty values"""
        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                overrides = panel.get("fieldConfig", {}).get("overrides", [])
                for override in overrides:
                    properties = override.get("properties", [])
                    for prop in properties:
                        if prop.get("id") == "displayName":
                            value = prop.get("value", "")
                            assert isinstance(value, str) and len(value) > 0, \
                                f"{dashboard_name} panel '{panel.get('title', 'unknown')}' has empty displayName in override"

    def test_units_are_valid(self, dashboards):
        """Verify unit values are valid Grafana units"""
        valid_units = {
            "short", "percent", "currencyUSD", "ms", "s", "h",
            "bytes", "deckbytes", "decbytes", "bits", "kbytes", "mbytes",
            "ns", "us", "dateTimeAsIso", "dateTimeAsUS",
            "ops", "reqps", "rpm", "rps", "wps", "eps",
            "dps", "iops", "none", "bps", "Bps", "kops",
            "themis", "v", "mv", "a", "ma", "ohm",
            "kohm", "mohm", "farad", "uf", "nf", "pf",
            "f", "degree", "henry", "hz", "khz", "mhz",
            "ghz", "joule", "kwh", "mah", "wh", "celsius",
            "fahrenheit", "kelvin", "db", "lux", "lm",
            "cd", "lp", "ok", "bad", "critical", "percent",
            "locale", "percentunit",
        }

        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                field_config = panel.get("fieldConfig", {})

                # Check default units
                default_unit = field_config.get("defaults", {}).get("unit")
                if default_unit:
                    assert default_unit in valid_units, \
                        f"{dashboard_name} has invalid default unit: {default_unit}"

                # Check override units
                for override in field_config.get("overrides", []):
                    for prop in override.get("properties", []):
                        if prop.get("id") == "unit":
                            unit_value = prop.get("value")
                            if unit_value:
                                assert unit_value in valid_units, \
                                    f"{dashboard_name} has invalid unit: {unit_value}"

    def test_thresholds_have_valid_colors(self, dashboards):
        """Verify threshold colors are valid"""
        valid_colors = {"green", "yellow", "orange", "red", "blue", "purple", "gray", "transparent"}

        for dashboard_name, dashboard in dashboards.items():
            for panel in dashboard.get("panels", []):
                field_config = panel.get("fieldConfig", {})

                # Check default thresholds
                defaults_thresholds = field_config.get("defaults", {}).get("thresholds", {})
                for step in defaults_thresholds.get("steps", []):
                    color = step.get("color")
                    if color and isinstance(color, str):
                        # Color might be hex or named color
                        if not color.startswith("#"):
                            assert color in valid_colors, \
                                f"{dashboard_name} has invalid threshold color: {color}"


class TestVariableConfiguration:
    """Test dashboard variable/templating configuration"""

    def test_variable_names_unique(self, dashboards):
        """Verify variable names are unique within each dashboard"""
        for dashboard_name, dashboard in dashboards.items():
            templating = dashboard.get("templating", {})
            variables = templating.get("list", [])
            var_names = [v.get("name") for v in variables]
            unique_names = set(var_names)
            assert len(var_names) == len(unique_names), \
                f"{dashboard_name} has duplicate variable names"

    def test_variable_types_valid(self, dashboards):
        """Verify variable types are valid"""
        valid_types = {"custom", "query", "textbox", "constant", "datasource", "interval", "ad hoc filters"}

        for dashboard_name, dashboard in dashboards.items():
            templating = dashboard.get("templating", {})
            for variable in templating.get("list", []):
                var_type = variable.get("type")
                if var_type:
                    assert var_type in valid_types, \
                        f"{dashboard_name} variable '{variable.get('name')}' has invalid type: {var_type}"


@pytest.mark.parametrize("dashboard_file",
    glob.glob(str(DASHBOARDS_DIR / "**/*.json"), recursive=True),
    ids=lambda x: Path(x).name)
class TestIndividualDashboards:
    """Parametrized tests for each dashboard"""

    def test_dashboard_loads(self, dashboard_file):
        """Verify dashboard JSON loads without errors"""
        with open(dashboard_file, "r") as f:
            dashboard = json.load(f)
            assert dashboard is not None

    def test_dashboard_has_uid(self, dashboard_file):
        """Verify dashboard has a UID"""
        with open(dashboard_file, "r") as f:
            dashboard = json.load(f)
            assert "uid" in dashboard
            assert dashboard["uid"]

    def test_dashboard_has_panels(self, dashboard_file):
        """Verify dashboard has at least one panel"""
        with open(dashboard_file, "r") as f:
            dashboard = json.load(f)
            assert "panels" in dashboard
            assert len(dashboard["panels"]) > 0
