# Implementation Plan

[Overview]
Make the Grafana **Loki** and **Tempo** dashboards (grafana/dashboards/loki/loki.json and grafana/dashboards/tempo/tempo.json) reliably show live data in production and local environments, while keeping dashboard UIDs/panel IDs unique and staying compatible with the repository dashboard validation tests.

Currently the Loki/Tempo dashboards are provisioned and their datasource UIDs match provisioning (grafana_loki / grafana_tempo), but the dashboards can still show “No data” depending on whether the expected labels exist in Loki (e.g., `env="production"`) and whether Tempo has traces for `{resource.service.name="gatewayz"}` in the selected time range. The fix is primarily **query/label robustness** (align queries to actual ingested labels) plus **validation/uniqueness enforcement**.

The high-level approach:
1) Audit the labels that exist in Loki/Tempo (both local and Railway).
2) Update loki.json and tempo.json queries so they match real labels/fields, with safe defaults.
3) Add optional dashboard variables (templating) so users can select `env`, `service_name`, etc., without hardcoding a single label value that may not exist.
4) Ensure no duplicates:
   - Dashboard `uid` values are unique across all dashboards.
   - Panel `id` values are unique within each dashboard.
   - Datasource UIDs used in panels are limited to the allowed set in tests.
5) Validate via `scripts/validate_dashboards.sh strict` and `pytest`.

[Types]
No application type-system changes; only Grafana dashboard JSON/YAML configuration structures are adjusted.

[Files]
Update dashboard and provisioning files to ensure the Loki/Tempo dashboards render real data.

Files to modify:
- `grafana/dashboards/loki/loki.json`
  - Update the log stream query to avoid hardcoding `env="production"` when that label may not exist.
  - Add templating variables (`env`, `level`, `service_name`/`compose_service`) with sensible defaults.
  - Ensure panel datasource references use `{ type: "loki", uid: "grafana_loki" }`.

- `grafana/dashboards/tempo/tempo.json`
  - Ensure trace search query matches actual attributes in Tempo (`resource.service.name` vs `service.name` vs `service_name`).
  - Add a variable for service name and optional `status` filter.
  - Keep panel types compatible with tests (currently `traces` and `timeseries` are allowed).

- `grafana/datasources/datasources.yml` (if needed)
  - Confirm Loki datasource `access` mode is correct for deployments (local docker network typically needs `proxy`; Railway may differ).
  - Confirm derived fields matcher regex aligns to your log format.

Files to read/validate during implementation:
- `tests/test_dashboards.py` (defines allowed panel types and allowed datasource UIDs)
- `scripts/validate_dashboards.sh`

No files are deleted in this scope.

[Functions]
No code functions are added/changed; only configuration values in JSON/YAML.

[Classes]
No classes are added/changed.

[Dependencies]
No new dependencies.

[Testing]
Run:
- `./scripts/validate_dashboards.sh strict`
- `python3 -m pytest -q`

Additionally, validate live data:
- Push a test log line to Loki with and without `env` label and confirm it appears in the Loki dashboard.
- Push a test trace to Tempo and confirm it appears in the Tempo dashboard.

[Implementation Order]
1. Inspect Loki labels in the current environment (local + Railway) by querying Loki for `{app="gatewayz"}` and reading returned stream labels.
2. Inspect Tempo attributes by querying Tempo search API for recent traces and checking which resource keys exist.
3. Update `grafana/dashboards/loki/loki.json`:
   - Replace hard-coded `{app="gatewayz", env="production"}` with a variable-driven query like `{app="gatewayz", env="$env"}` and default `$env` to `production` but allow `.*`/`local`.
   - Add variables for `env` and `level`.
4. Update `grafana/dashboards/tempo/tempo.json`:
   - Replace hard-coded `{resource.service.name="gatewayz"}` with variable-driven query based on discovered attribute key.
   - Ensure error query uses the correct TraceQL syntax for your Tempo version.
5. Ensure dashboard UIDs are unique across all dashboards and panel IDs are unique within each.
6. Run validators/tests.
7. Deploy and verify Loki/Tempo dashboards no longer show “No data”.
