"""
Patch dashboards for Loki incident response enhancement:
  A. Infrastructure-Health.json — add Loki Ingestion Health row
  B. Four-Golden-Signals.json — add Incident Response row
  C. GatewayZ-Error-Level Logs.json — add Consistency & Reliability row
"""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), "..")

LOKI = {"type": "loki", "uid": "grafana_loki"}
PROMETHEUS = {"type": "prometheus", "uid": "grafana_prometheus"}

# ── A. Infrastructure-Health.json ─────────────────────────────────────────────
INFRA_PATH = os.path.join(ROOT, "grafana", "dashboards", "infrastructure", "Infrastructure-Health.json")
with open(INFRA_PATH, "r", encoding="utf-8") as f:
    infra = json.load(f)

Y_START = 80  # After last panel (max y+h was 74)

loki_health_panels = [
    {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": Y_START},
        "id": 28,
        "title": "Loki Log Ingestion Health",
        "type": "row"
    },
    # 29 — Log Ingestion Rate (lines/s)
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 2, "fillOpacity": 10},
                "unit": "short"
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "INFO"},
                    "properties": [{"id": "color", "value": {"fixedColor": "green", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "ERROR"},
                    "properties": [{"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "WARNING"},
                    "properties": [{"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}}]
                }
            ]
        },
        "gridPos": {"h": 7, "w": 14, "x": 0, "y": Y_START + 1},
        "id": 29,
        "options": {
            "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum by (level) (rate({app=~"gatewayz.*"}[5m]))',
            "legendFormat": "{{level}}",
            "refId": "A"
        }],
        "title": "Log Ingestion Rate by Level (lines/s)",
        "description": "If this panel shows no data, the backend is not pushing logs to Loki. Check LOKI_URL env var on the gatewayz-backend service.",
        "type": "timeseries"
    },
    # 30 — Log Streams Active (stat)
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "red", "value": None},
                    {"color": "yellow", "value": 1},
                    {"color": "green", "value": 2}
                ]},
                "unit": "none",
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 3, "w": 5, "x": 14, "y": Y_START + 1},
        "id": 30,
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'count(count by (app) (rate({app=~"gatewayz.*"}[5m])))',
            "legendFormat": "Active Streams",
            "refId": "A"
        }],
        "title": "Active Log Streams",
        "type": "stat"
    },
    # 31 — ERROR log rate stat
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 0.1},
                    {"color": "red", "value": 1.0}
                ]},
                "unit": "short",
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 5, "x": 14, "y": Y_START + 4},
        "id": 31,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum(rate({app=~"gatewayz.*"} |= "ERROR" [1m]))',
            "legendFormat": "ERROR lines/s",
            "refId": "A"
        }],
        "title": "ERROR Rate (1m window)",
        "type": "stat"
    },
    # 32 — Minutes since last log (gap detector)
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 2},
                    {"color": "red", "value": 5}
                ]},
                "unit": "none",
                "mappings": [{"type": "special", "options": {"match": "null", "result": {"text": "No logs", "color": "red"}}}]
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 5, "x": 19, "y": Y_START + 1},
        "id": 32,
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "value_and_name"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'count_over_time({app=~"gatewayz.*"}[5m])',
            "legendFormat": "Log lines (5m)",
            "refId": "A"
        }],
        "title": "Log Lines Received (5m)",
        "description": "Should be non-zero when backend is running. Zero = ingestion broken.",
        "type": "stat"
    },
    # 33 — Log volume 24h heatmap-style as barchart by hour
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 7, "w": 24, "x": 0, "y": Y_START + 8},
        "id": 33,
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level="INFO" [5m]))',
                "legendFormat": "INFO (good path)",
                "refId": "A"
            },
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level="WARNING" [5m]))',
                "legendFormat": "WARNING",
                "refId": "B"
            },
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" [5m]))',
                "legendFormat": "ERROR / CRITICAL",
                "refId": "C"
            }
        ],
        "title": "Log Volume Trend -- Positive vs Negative Signals (INFO / WARNING / ERROR)",
        "description": "A healthy system shows a high INFO baseline with minimal ERROR/CRITICAL. Growing ERROR lines relative to INFO indicate systemic degradation.",
        "type": "timeseries"
    }
]

infra["panels"].extend(loki_health_panels)

with open(INFRA_PATH, "w", encoding="utf-8") as f:
    json.dump(infra, f, indent=2, ensure_ascii=False)
print(f"Infrastructure-Health: {len(infra['panels'])} panels total")

# ── B. Four-Golden-Signals.json ───────────────────────────────────────────────
FGS_PATH = os.path.join(ROOT, "grafana", "dashboards", "golden-signals", "Four-Golden-Signals.json")
with open(FGS_PATH, "r", encoding="utf-8") as f:
    fgs = json.load(f)

INCIDENT_Y = 220  # After model availability row (which ends around y=217)

incident_panels = [
    {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": INCIDENT_Y},
        "id": 209,
        "title": "Incident Response -- Dual Log + Metric Signals",
        "type": "row"
    },
    # 210 — ERROR Log Rate (1m) stat
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 0.1},
                    {"color": "red", "value": 1.0}
                ]},
                "unit": "short",
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 4, "x": 0, "y": INCIDENT_Y + 1},
        "id": 210,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum(rate({app=~"gatewayz.*"} |= "ERROR" [1m]))',
            "legendFormat": "ERROR/s",
            "refId": "A"
        }],
        "title": "ERROR Log Rate (1m)",
        "type": "stat"
    },
    # 211 — CRITICAL Log Rate (1m) stat
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "green", "value": None},
                    {"color": "red", "value": 0.01}
                ]},
                "unit": "short",
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 4, "x": 4, "y": INCIDENT_Y + 1},
        "id": 211,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum(rate({app=~"gatewayz.*"} |= "CRITICAL" [1m]))',
            "legendFormat": "CRITICAL/s",
            "refId": "A"
        }],
        "title": "CRITICAL Log Rate (1m)",
        "type": "stat"
    },
    # 212 — Dual signal: Log error rate vs Metric error rate
    {
        "datasource": {"type": "datasource", "uid": "-- Mixed --"},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 2, "fillOpacity": 5},
                "unit": "short"
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Log ERROR rate"},
                    "properties": [{"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "HTTP 5xx rate"},
                    "properties": [{"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}}]
                }
            ]
        },
        "gridPos": {"h": 8, "w": 16, "x": 8, "y": INCIDENT_Y + 1},
        "id": 212,
        "options": {
            "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" [5m]))',
                "legendFormat": "Log ERROR rate",
                "refId": "A"
            },
            {
                "datasource": PROMETHEUS,
                "expr": 'sum(rate(fastapi_requests_total{status_code=~"5.."}[5m]))',
                "legendFormat": "HTTP 5xx rate",
                "refId": "B"
            }
        ],
        "title": "Error Log Rate vs HTTP 5xx Rate -- Dual Signal Correlation",
        "description": "Both signals should spike together during an incident. A gap between them means either: (a) backend errors not reaching HTTP layer, or (b) log push to Loki is delayed.",
        "type": "timeseries"
    },
    # 213 — Error Pattern Frequency barchart
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "yellow", "value": None},
                    {"color": "orange", "value": 5},
                    {"color": "red", "value": 20}
                ]},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 8, "x": 0, "y": INCIDENT_Y + 5},
        "id": 213,
        "options": {
            "barWidth": 0.7,
            "groupWidth": 0.7,
            "legend": {"displayMode": "list", "placement": "bottom"},
            "orientation": "horizontal",
            "xTickLabelRotation": 0
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'topk(8, sum by (error_type) (count_over_time({app=~"gatewayz.*"} | logfmt | error_type != "" [15m])))',
            "legendFormat": "{{error_type}}",
            "refId": "A",
            "instant": True
        }],
        "title": "Error Pattern Frequency (15m)",
        "description": "Most frequent error types in the last 15 minutes. Ranked horizontally — longest bar = most common failure pattern.",
        "type": "barchart"
    },
    # 214 — Live Error Stream
    {
        "datasource": LOKI,
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": INCIDENT_Y + 9},
        "id": 214,
        "options": {
            "dedupStrategy": "none",
            "enableLogDetails": True,
            "prettifyLogMessage": True,
            "showCommonLabels": False,
            "showLabels": False,
            "showTime": True,
            "sortOrder": "Descending",
            "wrapLogMessage": True
        },
        "targets": [{
            "datasource": LOKI,
            "expr": '{app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" | logfmt',
            "refId": "A"
        }],
        "title": "Live Error Stream -- Real-time ERROR and CRITICAL Logs",
        "description": "Real-time view of all ERROR and CRITICAL log lines. Use this during an active incident to see error messages as they arrive.",
        "type": "logs"
    }
]

fgs["panels"].extend(incident_panels)

with open(FGS_PATH, "w", encoding="utf-8") as f:
    json.dump(fgs, f, indent=2, ensure_ascii=False)
print(f"Four-Golden-Signals: {len(fgs['panels'])} panels total")

# ── C. GatewayZ-Error-Level Logs.json ─────────────────────────────────────────
ERROR_LOGS_PATH = os.path.join(ROOT, "grafana", "dashboards", "loki", "GatewayZ-Error-Level Logs.json")
with open(ERROR_LOGS_PATH, "r", encoding="utf-8") as f:
    errlogs = json.load(f)

# Find max panel ID and max y
max_id = max(p.get("id", 0) for p in errlogs["panels"])
max_y = max((p.get("gridPos", {}).get("y", 0) + p.get("gridPos", {}).get("h", 0)) for p in errlogs["panels"])
C_Y = max_y + 2
C_START_ID = max_id + 1

print(f"Error Logs dashboard: max_id={max_id}, max_y={max_y}, new panels start at y={C_Y} id={C_START_ID}")

consistency_panels = [
    {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": C_Y},
        "id": C_START_ID,
        "title": "Consistency & Reliability -- Positive vs Negative Signal Baseline",
        "type": "row"
    },
    # 24h Error Consistency — is error rate steady or spiking?
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 2, "fillOpacity": 8},
                "unit": "short"
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Positive: INFO (good path)"},
                    "properties": [{"id": "color", "value": {"fixedColor": "green", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "Negative: ERROR / CRITICAL"},
                    "properties": [{"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "Negative: WARNING"},
                    "properties": [{"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}}]
                }
            ]
        },
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": C_Y + 1},
        "id": C_START_ID + 1,
        "options": {
            "legend": {"calcs": ["mean", "max", "min"], "displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level="INFO" [5m]))',
                "legendFormat": "Positive: INFO (good path)",
                "refId": "A"
            },
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level="WARNING" [5m]))',
                "legendFormat": "Negative: WARNING",
                "refId": "B"
            },
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" [5m]))',
                "legendFormat": "Negative: ERROR / CRITICAL",
                "refId": "C"
            }
        ],
        "title": "24h Consistency -- Positive (INFO) vs Negative (WARNING / ERROR) Signal Baseline",
        "description": "A reliable system shows a stable INFO baseline with low, consistent ERROR/WARNING levels. Spikes indicate incidents; a rising ERROR baseline (relative to INFO) indicates systemic degradation.",
        "type": "timeseries"
    },
    # Negative: Error Cluster Detection by type
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 1, "fillOpacity": 10},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 7, "w": 12, "x": 0, "y": C_Y + 9},
        "id": C_START_ID + 2,
        "options": {
            "legend": {"calcs": ["max"], "displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum by (error_type) (rate({app=~"gatewayz.*"} | logfmt | error_type != "" [5m]))',
            "legendFormat": "{{error_type}}",
            "refId": "A"
        }],
        "title": "Negative Signal: Error Type Consistency -- Are the Same Errors Recurring?",
        "description": "If one error_type dominates consistently, that is an isolated fault (fix the one thing). If error types rotate, that is systemic instability.",
        "type": "timeseries"
    },
    # Fault isolation indicator stat
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "green", "value": None},
                    {"color": "yellow", "value": 3},
                    {"color": "red", "value": 6}
                ]},
                "unit": "none",
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 3, "w": 6, "x": 12, "y": C_Y + 9},
        "id": C_START_ID + 3,
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'count(count by (error_type) (count_over_time({app=~"gatewayz.*"} | logfmt | error_type != "" [15m])))',
            "legendFormat": "Distinct Error Types",
            "refId": "A"
        }],
        "title": "Distinct Error Types (15m)",
        "description": "LOW (1-2) = isolated fault. HIGH (5+) = systemic instability across multiple components.",
        "type": "stat"
    },
    # Fault tolerance: error recovery timeseries
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 1, "fillOpacity": 5},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": C_Y + 12},
        "id": C_START_ID + 4,
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level=~"ERROR|CRITICAL" [1m]))',
                "legendFormat": "Error Rate (1m)",
                "refId": "A"
            },
            {
                "datasource": LOKI,
                "expr": 'sum(rate({app=~"gatewayz.*"} | level="INFO" [1m]))',
                "legendFormat": "Recovery (INFO rate)",
                "refId": "B"
            }
        ],
        "title": "Fault Tolerance: Error Spike vs INFO Recovery",
        "description": "When errors spike, watch how fast INFO rate recovers. Fast recovery = fault-tolerant system. Slow recovery = cascading failure risk.",
        "type": "timeseries"
    },
    # Positive signal: 2xx success log rate
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"lineWidth": 2, "fillOpacity": 5},
                "unit": "short"
            },
            "overrides": []
        },
        "gridPos": {"h": 7, "w": 12, "x": 0, "y": C_Y + 16},
        "id": C_START_ID + 5,
        "options": {
            "legend": {"calcs": ["mean", "min"], "displayMode": "table", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum(rate({app=~"gatewayz.*"} | level="INFO" [5m]))',
            "legendFormat": "Successful log lines/s",
            "refId": "A"
        }],
        "title": "Positive Signal: Successful Operation Rate (INFO baseline)",
        "description": "This is the system's good-path signal. A stable, non-decreasing INFO rate means the system is reliably processing requests. A drop here (without a corresponding ERROR spike) may indicate a silent failure or backend stoppage.",
        "type": "timeseries"
    },
    # System reliability score stat
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": [
                    {"color": "red", "value": None},
                    {"color": "yellow", "value": 90},
                    {"color": "green", "value": 98}
                ]},
                "unit": "percent",
                "min": 0,
                "max": 100,
                "mappings": []
            },
            "overrides": []
        },
        "gridPos": {"h": 4, "w": 12, "x": 12, "y": C_Y + 16},
        "id": C_START_ID + 6,
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto"
        },
        "targets": [{
            "datasource": LOKI,
            "expr": '(sum(rate({app=~"gatewayz.*"} | level="INFO" [5m])) / clamp_min(sum(rate({app=~"gatewayz.*"}[5m])), 0.001)) * 100',
            "legendFormat": "Log-level Reliability %",
            "refId": "A"
        }],
        "title": "Log-Level Reliability Score (INFO / Total %)",
        "description": "Percentage of log lines that are INFO (good path) vs total log volume. 98%+ = highly reliable. Below 90% = systemic errors dominating.",
        "type": "stat"
    },
    # Functionality check: all expected services logging
    {
        "datasource": LOKI,
        "fieldConfig": {
            "defaults": {"unit": "short"},
            "overrides": []
        },
        "gridPos": {"h": 3, "w": 12, "x": 12, "y": C_Y + 20},
        "id": C_START_ID + 7,
        "options": {
            "footer": {"show": False},
            "showHeader": True,
            "sortBy": [{"desc": True, "displayName": "Log Lines (5m)"}]
        },
        "targets": [{
            "datasource": LOKI,
            "expr": 'sum by (service) (count_over_time({app=~"gatewayz.*"} | logfmt | service != "" [5m]))',
            "legendFormat": "{{service}}",
            "refId": "A",
            "instant": True
        }],
        "title": "Functionality Check: Services Generating Logs (5m)",
        "description": "Each service should be present. A missing service entry means it is either not running or not logging.",
        "transformations": [
            {"id": "organize", "options": {"renameByName": {"Value": "Log Lines (5m)", "service": "Service"}}}
        ],
        "type": "table"
    }
]

errlogs["panels"].extend(consistency_panels)

with open(ERROR_LOGS_PATH, "w", encoding="utf-8") as f:
    json.dump(errlogs, f, indent=2, ensure_ascii=False)
print(f"Error Logs dashboard: {len(errlogs['panels'])} panels total")
print("Done.")
