"""
create_system_quality_dashboard.py
Generates grafana/dashboards/reliability/System-Reliability-Dashboard.json
8-pillar System Quality dashboard for GatewayZ LGTM stack.
"""
import json, os

PROM = {"type": "prometheus", "uid": "grafana_prometheus"}
LOKI = {"type": "loki", "uid": "grafana_loki"}

OUT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "grafana", "dashboards", "reliability",
    "System-Reliability-Dashboard.json"
)


def stat(pid, title, expr, unit, thresholds, x, y, w=6, h=4,
         datasource=None, instant=True, mappings=None, decimals=None):
    ds = datasource or PROM
    p = {
        "id": pid,
        "type": "stat",
        "title": title,
        "datasource": ds,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": [{
            "refId": "A",
            "datasource": ds,
            "expr": expr,
            **({"instant": True} if instant else {})
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto",
            "wideLayout": True
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": thresholds},
                "mappings": mappings or [],
                **({"decimals": decimals} if decimals is not None else {})
            },
            "overrides": []
        }
    }
    return p


def timeseries(pid, title, targets, unit, x, y, w=12, h=8, datasource=None):
    ds = datasource or PROM
    built_targets = []
    for i, (ref, expr, legend, tds) in enumerate(targets):
        built_targets.append({
            "refId": ref,
            "datasource": tds or ds,
            "expr": expr,
            "legendFormat": legend
        })
    return {
        "id": pid,
        "type": "timeseries",
        "title": title,
        "datasource": ds,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": built_targets,
        "options": {
            "tooltip": {"mode": "multi", "sort": "desc"},
            "legend": {
                "displayMode": "table",
                "placement": "right",
                "calcs": ["mean", "max", "lastNotNull"]
            }
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "palette-classic"},
                "custom": {
                    "lineWidth": 1,
                    "fillOpacity": 10,
                    "showPoints": "never",
                    "spanNulls": True
                }
            },
            "overrides": []
        }
    }


def bargauge(pid, title, targets, unit, x, y, w=12, h=8, datasource=None,
             thresholds=None):
    ds = datasource or PROM
    built_targets = []
    for i, (ref, expr, legend) in enumerate(targets):
        built_targets.append({
            "refId": ref,
            "datasource": ds,
            "expr": expr,
            "legendFormat": legend,
            "instant": True
        })
    thr = thresholds or [
        {"color": "green", "value": None},
        {"color": "yellow", "value": 60},
        {"color": "red", "value": 80}
    ]
    return {
        "id": pid,
        "type": "bargauge",
        "title": title,
        "datasource": ds,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": built_targets,
        "options": {
            "orientation": "horizontal",
            "displayMode": "gradient",
            "valueMode": "color",
            "showUnfilled": True,
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False}
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": thr}
            },
            "overrides": []
        }
    }


def row(pid, title, y):
    return {
        "id": pid,
        "type": "row",
        "title": title,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "collapsed": False
    }


def loki_stat(pid, title, expr, unit, thresholds, x, y, w=6, h=4):
    p = stat(pid, title, expr, unit, thresholds, x, y, w, h, datasource=LOKI)
    p["targets"][0]["queryType"] = "range"
    del p["targets"][0]["instant"]
    return p


def logs_panel(pid, title, expr, x, y, w=24, h=8):
    return {
        "id": pid,
        "type": "logs",
        "title": title,
        "datasource": LOKI,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": [{
            "refId": "A",
            "datasource": LOKI,
            "expr": expr,
            "queryType": "range",
            "maxLines": 25
        }],
        "options": {
            "dedupStrategy": "none",
            "showLabels": False,
            "showTime": True,
            "sortOrder": "Descending",
            "wrapLogMessage": True,
            "prettifyLogMessage": False,
            "enableLogDetails": True
        }
    }


def loki_timeseries(pid, title, targets, unit, x, y, w=12, h=8):
    built = []
    for ref, expr, legend in targets:
        built.append({
            "refId": ref,
            "datasource": LOKI,
            "expr": expr,
            "legendFormat": legend,
            "queryType": "range"
        })
    return {
        "id": pid,
        "type": "timeseries",
        "title": title,
        "datasource": LOKI,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": built,
        "options": {
            "tooltip": {"mode": "multi", "sort": "desc"},
            "legend": {
                "displayMode": "table",
                "placement": "right",
                "calcs": ["mean", "max", "lastNotNull"]
            }
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "palette-classic"},
                "custom": {
                    "lineWidth": 1,
                    "fillOpacity": 10,
                    "showPoints": "never",
                    "spanNulls": True
                }
            },
            "overrides": []
        }
    }


panels = []

# ── Header ──────────────────────────────────────────────────────────────────
panels.append({
    "id": 1,
    "type": "text",
    "title": "",
    "gridPos": {"h": 3, "w": 24, "x": 0, "y": 0},
    "options": {
        "content": (
            "## GatewayZ — System Quality Dashboard\n"
            "8-pillar view of overall system health: "
            "**Reliability** · **Performance** · **Scalability** · **Availability** · "
            "**Observability** · **Fault Tolerance** · **Security** · **Maintainability**\n\n"
            "_Metrics from Prometheus/Mimir · Logs from Loki · Refresh: 30s_"
        ),
        "mode": "markdown"
    }
})

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 1 — RELIABILITY  (IDs 100–107, Y 3)
# ════════════════════════════════════════════════════════════════════════════
Y = 3
panels.append(row(100, "🛡️  Reliability — SLO Compliance · Error Rate · Exception Tracking", Y))
Y += 1

err5_expr = ('sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / '
             'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001)')
slo_expr = ('(1 - sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / '
            'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001)) * 100')
err4_expr = ('sum(rate(fastapi_requests_total{status_code=~"4.."}[5m])) / '
             'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001)')
exc_expr = 'sum(rate(fastapi_exceptions_total[5m])) * 60'

panels.append(stat(101, "5xx Error Rate", err5_expr, "percentunit",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 0.001},
     {"color": "red", "value": 0.01}], 0, Y))
panels.append(stat(102, "SLO Compliance (99.9% target)", slo_expr, "percent",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 99},
     {"color": "green", "value": 99.9}], 6, Y))
panels.append(stat(103, "4xx Client Error Rate", err4_expr, "percentunit",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 0.02},
     {"color": "red", "value": 0.1}], 12, Y))
panels.append(stat(104, "Unhandled Exceptions / min", exc_expr, "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 5}], 18, Y))
Y += 4

panels.append(timeseries(105, "5xx vs 4xx Error Rate Over Time",
    [("A", "errors:5xx:percentage", "5xx %", None),
     ("B", "errors:4xx:percentage", "4xx %", None)],
    "percent", 0, Y, w=12, h=8))
panels.append(timeseries(106, "SLO Compliance Over Time (% Successful Requests)",
    [("A", slo_expr, "SLO %", None)],
    "percent", 12, Y, w=12, h=8))
Y += 8

panels.append(bargauge(107, "Exception Volume by Type",
    [("A", 'sum by (exception_type) (rate(fastapi_exceptions_total[5m]))', "{{exception_type}}")],
    "short", 0, Y, w=24, h=6,
    thresholds=[{"color": "green", "value": None}, {"color": "yellow", "value": 0.01},
                {"color": "red", "value": 0.1}]))
Y += 6

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 2 — PERFORMANCE  (IDs 200–208, Y ~23)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(200, "⚡  Performance — Latency · Throughput · Streaming TTFC", Y))
Y += 1

p50_expr = 'histogram_quantile(0.50, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le))'
p95_expr = 'histogram_quantile(0.95, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le))'
p99_expr = 'histogram_quantile(0.99, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le))'
rps_expr = 'sum(rate(fastapi_requests_total[5m]))'
ttfc_expr = 'histogram_quantile(0.95, sum(rate(time_to_first_chunk_seconds_bucket[5m])) by (le))'

panels.append(stat(201, "P50 Latency", p50_expr, "s",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 0.2},
     {"color": "red", "value": 1}], 0, Y))
panels.append(stat(202, "P95 Latency", p95_expr, "s",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 0.5},
     {"color": "red", "value": 2}], 6, Y))
panels.append(stat(203, "P99 Latency", p99_expr, "s",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 5}], 12, Y))
panels.append(stat(204, "Throughput (req/s)", rps_expr, "reqps",
    [{"color": "green", "value": None}], 18, Y))
Y += 4

panels.append(stat(205, "TTFC P95 — Streaming First Chunk", ttfc_expr, "s",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 5}], 0, Y, w=6))
Y += 4

panels.append(timeseries(206, "Latency Percentiles Over Time (P50 / P95 / P99)",
    [("A", "latency:p50:seconds", "P50", None),
     ("B", "latency:p95:seconds", "P95", None),
     ("C", "latency:p99:seconds", "P99", None)],
    "s", 0, Y, w=12, h=8))
panels.append(timeseries(207, "Request Throughput Over Time",
    [("A", rps_expr, "req/s", None)],
    "reqps", 12, Y, w=12, h=8))
Y += 8

panels.append(timeseries(208, "Inference Latency P95 by Provider",
    [("A",
      'histogram_quantile(0.95, sum(rate(model_inference_duration_seconds_bucket[5m])) by (le, provider))',
      "{{provider}}", None)],
    "s", 0, Y, w=24, h=8))
Y += 8

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 3 — SCALABILITY  (IDs 300–308)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(300, "📈  Scalability — Concurrency · Cache · Token Throughput", Y))
Y += 1

inflight_expr = 'sum(fastapi_requests_in_progress)'
cache_expr = ('sum(rate(catalog_cache_hits_total[5m])) / '
              'clamp_min(sum(rate(catalog_cache_hits_total[5m])) + '
              'sum(rate(catalog_cache_misses_total[5m])), 0.001) * 100')
tokens_expr = 'sum(rate(tokens_used_total[5m])) * 60'
infer_rps = 'sum(rate(model_inference_requests_total[5m]))'
replica_expr = ('sum(rate(read_replica_queries_total{status="success"}[5m])) / '
                'clamp_min(sum(rate(read_replica_queries_total[5m])), 0.001) * 100')

panels.append(stat(301, "Active In-Flight Requests", inflight_expr, "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 200},
     {"color": "red", "value": 500}], 0, Y))
panels.append(stat(302, "Catalog Cache Hit Ratio", cache_expr, "percent",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 70},
     {"color": "green", "value": 90}], 6, Y))
panels.append(stat(303, "Token Throughput (tokens / min)", tokens_expr, "short",
    [{"color": "green", "value": None}], 12, Y))
panels.append(stat(304, "Inference Requests / s", infer_rps, "reqps",
    [{"color": "green", "value": None}], 18, Y))
Y += 4

panels.append(stat(305, "Read Replica Success Rate", replica_expr, "percent",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 95},
     {"color": "green", "value": 99}], 0, Y, w=6))
Y += 4

panels.append(timeseries(306, "In-Flight Request Concurrency Over Time",
    [("A", inflight_expr, "in-flight requests", None)],
    "short", 0, Y, w=12, h=8))
panels.append(timeseries(307, "Token Throughput by Provider (tokens/min)",
    [("A", 'sum by (provider) (rate(tokens_used_total[5m])) * 60', "{{provider}}", None)],
    "short", 12, Y, w=12, h=8))
Y += 8

panels.append(timeseries(308, "Cache Hit Ratio Over Time",
    [("A", cache_expr, "Catalog Hit %", None)],
    "percent", 0, Y, w=24, h=6))
Y += 6

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 4 — AVAILABILITY  (IDs 400–406)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(400, "✅  Availability — Provider Health · Circuit Breakers · Success Rate", Y))
Y += 1

success_rate = ('(1 - sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / '
                'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001)) * 100')

panels.append(stat(401, "Overall Request Success Rate", success_rate, "percent",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 95},
     {"color": "green", "value": 99}], 0, Y))
panels.append(stat(402, "Providers Healthy (score > 70)",
    'count(provider_health_score > 70) or vector(0)', "short",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 1},
     {"color": "green", "value": 5}], 6, Y))
panels.append(stat(403, "Circuit Breakers OPEN",
    'sum(circuit_breaker_current_state{state="open"}) or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "red", "value": 1}], 12, Y))
panels.append(stat(404, "Min Provider Health Score",
    'min(provider_health_score) or vector(0)', "short",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 50},
     {"color": "green", "value": 80}], 18, Y))
Y += 4

panels.append(timeseries(405, "Provider Health Scores Over Time",
    [("A", 'provider_health_score or vector(0)', "{{provider}}", None)],
    "short", 0, Y, w=16, h=8))
panels.append(bargauge(406, "Current Provider Health Scores",
    [("A", 'provider_health_score or vector(0)', "{{provider}}")],
    "short", 16, Y, w=8, h=8,
    thresholds=[{"color": "red", "value": None}, {"color": "yellow", "value": 50},
                {"color": "green", "value": 80}]))
Y += 8

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 5 — OBSERVABILITY  (IDs 500–507)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(500, "🔭  Observability — Logs · Exceptions · Pipeline Health", Y))
Y += 1

panels.append(loki_stat(501, "ERROR Log Rate (5m)",
    'sum(rate({app=~"gatewayz.*"} |= "ERROR" [5m]))', "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 0.1},
     {"color": "red", "value": 1}], 0, Y))
panels.append(loki_stat(502, "CRITICAL Log Rate (5m)",
    'sum(rate({app=~"gatewayz.*"} |= "CRITICAL" [5m]))', "short",
    [{"color": "green", "value": None}, {"color": "red", "value": 0.01}], 6, Y))
panels.append(stat(503, "Unhandled Exceptions / min", exc_expr, "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 5}], 12, Y))
panels.append(stat(504, "Loki Log Queue Depth",
    'loki_log_queue_size or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 100},
     {"color": "red", "value": 500}], 18, Y))
Y += 4

panels.append(timeseries(505, "Exception Rate Over Time by Type",
    [("A", 'sum by (exception_type) (rate(fastapi_exceptions_total[5m]))',
      "{{exception_type}}", None)],
    "short", 0, Y, w=12, h=8))

panels.append(loki_timeseries(506, "Log Volume by Level (INFO / WARNING / ERROR)",
    [("A", 'sum(rate({app=~"gatewayz.*"} | level="INFO" [5m]))', "INFO"),
     ("B", 'sum(rate({app=~"gatewayz.*"} | level="WARNING" [5m]))', "WARNING"),
     ("C", 'sum(rate({app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" [5m]))', "ERROR/CRITICAL")],
    "short", 12, Y, w=12, h=8))
Y += 8

panels.append(logs_panel(507, "Recent ERROR / CRITICAL Logs",
    '{app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" | logfmt',
    0, Y, w=24, h=8))
Y += 8

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 6 — FAULT TOLERANCE  (IDs 600–607)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(600, "🔄  Fault Tolerance — Circuit Breakers · Velocity Mode · OTEL Pipeline", Y))
Y += 1

panels.append(stat(601, "Velocity Mode Activations (1h)",
    'increase(velocity_mode_activations_total[1h]) or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 3}], 0, Y))
panels.append(stat(602, "Velocity Mode Active Now",
    'velocity_mode_active or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "red", "value": 1}], 6, Y,
    mappings=[
        {"type": "value", "options": {"0": {"text": "Normal", "color": "green"},
                                       "1": {"text": "ACTIVE", "color": "red"}}}
    ]))
panels.append(stat(603, "OTEL Circuit Breaker State",
    'otel_export_circuit_breaker_state or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 2},
     {"color": "red", "value": 1}], 12, Y,
    mappings=[
        {"type": "value", "options": {"0": {"text": "CLOSED", "color": "green"},
                                       "1": {"text": "OPEN", "color": "red"},
                                       "2": {"text": "HALF-OPEN", "color": "yellow"}}}
    ]))
panels.append(stat(604, "Remote Write Success Rate",
    ('sum(rate(prometheus_remote_write_total{status="success"}[5m])) / '
     'clamp_min(sum(rate(prometheus_remote_write_total[5m])), 0.001) * 100'),
    "percent",
    [{"color": "red", "value": None}, {"color": "yellow", "value": 95},
     {"color": "green", "value": 99}], 18, Y))
Y += 4

panels.append(timeseries(605, "Circuit Breaker State per Provider",
    [("A", 'circuit_breaker_current_state or vector(0)', "{{provider}} — {{state}}", None)],
    "short", 0, Y, w=12, h=8))
panels.append(timeseries(606, "Velocity Mode Activation History",
    [("A", 'increase(velocity_mode_activations_total[5m]) or vector(0)',
      "activations/5m", None)],
    "short", 12, Y, w=12, h=8))
Y += 8

panels.append(timeseries(607, "Rate Limit Rejections by Endpoint",
    [("A", 'sum by (endpoint) (rate(rate_limit_rejections_total[5m]))',
      "{{endpoint}}", None)],
    "short", 0, Y, w=24, h=6))
Y += 6

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 7 — SECURITY  (IDs 700–707)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(700, "🔒  Security — Auth Failures · Rate Limits · Velocity Mode", Y))
Y += 1

auth_rate = ('sum(rate(fastapi_requests_total{status_code=~"401|403"}[5m])) / '
             'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001) * 100')
rl_rate = ('sum(rate(fastapi_requests_total{status_code="429"}[5m])) / '
           'clamp_min(sum(rate(fastapi_requests_total[5m])), 0.001) * 100')
rl_rejections = 'sum(rate(rate_limit_rejections_total[5m])) or vector(0)'

panels.append(stat(701, "Auth Failure Rate (401/403)", auth_rate, "percent",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 5}], 0, Y))
panels.append(stat(702, "Rate Limit Hit Rate (429)", rl_rate, "percent",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 2},
     {"color": "red", "value": 10}], 6, Y))
panels.append(stat(703, "Rate Limit Rejections / s", rl_rejections, "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 1},
     {"color": "red", "value": 10}], 12, Y))
panels.append(stat(704, "Velocity Mode Active",
    'velocity_mode_active or vector(0)', "short",
    [{"color": "green", "value": None}, {"color": "red", "value": 1}], 18, Y,
    mappings=[
        {"type": "value", "options": {"0": {"text": "Normal", "color": "green"},
                                       "1": {"text": "ACTIVE", "color": "red"}}}
    ]))
Y += 4

panels.append(timeseries(705, "Auth Failure Rate Over Time",
    [("A", 'sum(rate(fastapi_requests_total{status_code=~"401|403"}[5m]))',
      "401/403 failures/s", None)],
    "short", 0, Y, w=12, h=8))
panels.append(timeseries(706, "Rate Limit Rejections Over Time by Endpoint",
    [("A", 'sum by (endpoint) (rate(rate_limit_rejections_total[5m])) or vector(0)',
      "{{endpoint}}", None)],
    "short", 12, Y, w=12, h=8))
Y += 8

panels.append(logs_panel(707, "Recent Security Warnings",
    '{app=~"gatewayz.*"} | level="WARNING" | logfmt',
    0, Y, w=24, h=7))
Y += 7

# ════════════════════════════════════════════════════════════════════════════
# PILLAR 8 — MAINTAINABILITY  (IDs 800–808)
# ════════════════════════════════════════════════════════════════════════════
panels.append(row(800, "🔧  Maintainability — Process · Memory · Redis · Cost", Y))
Y += 1

uptime_expr = 'time() - process_start_time_seconds'
mem_expr = 'process_resident_memory_bytes'
redis_pct = 'redis_memory_used_bytes / clamp_min(redis_memory_max_bytes, 0.001) * 100'
loki_q = 'loki_log_queue_size or vector(0)'
cost_expr = 'sum(increase(gatewayz_api_cost_usd_total[24h]))'

panels.append(stat(801, "Process Uptime", uptime_expr, "s",
    [{"color": "green", "value": None}], 0, Y))
panels.append(stat(802, "Memory RSS", mem_expr, "bytes",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 536870912},
     {"color": "red", "value": 1073741824}], 6, Y))
panels.append(stat(803, "Redis Memory %", redis_pct, "percent",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 70},
     {"color": "red", "value": 85}], 12, Y))
panels.append(stat(804, "Loki Queue Depth", loki_q, "short",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 100},
     {"color": "red", "value": 500}], 18, Y))
Y += 4

panels.append(stat(805, "Daily API Cost (USD)", cost_expr, "currencyUSD",
    [{"color": "green", "value": None}, {"color": "yellow", "value": 50},
     {"color": "red", "value": 200}], 0, Y, w=6, decimals=2))
Y += 4

panels.append(timeseries(806, "Memory Usage Over Time",
    [("A", mem_expr, "Memory RSS", None)],
    "bytes", 0, Y, w=12, h=8))
panels.append(timeseries(807, "API Cost by Provider (24h cumulative)",
    [("A", 'sum by (provider) (increase(gatewayz_api_cost_usd_total[24h]))',
      "{{provider}}", None)],
    "currencyUSD", 12, Y, w=12, h=8))
Y += 8

panels.append(timeseries(808, "Redis Memory & Eviction Rate Over Time",
    [("A", "redis_memory_used_bytes", "Memory Used", None),
     ("B", "rate(redis_evicted_keys_total[5m])", "Evictions/s", None)],
    "short", 0, Y, w=24, h=6))

# ════════════════════════════════════════════════════════════════════════════
# Dashboard scaffold
# ════════════════════════════════════════════════════════════════════════════
dashboard = {
    "title": "GatewayZ — System Quality",
    "uid": "gatewayz-system-quality-pillars",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "30s",
    "time": {"from": "now-1h", "to": "now"},
    "timepicker": {},
    "tags": ["gatewayz", "system-quality", "reliability", "slo"],
    "panels": panels,
    "templating": {"list": []},
    "annotations": {"list": []},
    "links": []
}

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Written: {OUT_PATH}")
print(f"Total panels: {len(panels)}")
for p in panels:
    print(f"  id={p['id']:4d}  type={p['type']:<12}  title={p.get('title','')[:60]!r}")
