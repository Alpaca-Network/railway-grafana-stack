"""
JSON API Proxy for Grafana Simple JSON Datasource

This proxy translates Grafana's SimpleJSON datasource queries into
direct REST API calls to the GatewayZ backend and returns properly
formatted responses.

Endpoints:
- GET / - Health check
- POST /search - Return available metrics
- POST /query - Query metrics data
- POST /annotations - Query annotations (not implemented)
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for Grafana

# Backend API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.gatewayz.ai")

# Metric definitions - maps simple names to backend endpoints
METRIC_ENDPOINTS = {
    "avg_health_score": {
        "url": "/api/monitoring/stats/realtime",
        "params": {"hours": 1},
        "path": "avg_health_score",
    },
    "total_requests": {
        "url": "/api/monitoring/stats/realtime",
        "params": {"hours": 1},
        "path": "total_requests",
    },
    "total_cost": {
        "url": "/api/monitoring/stats/realtime",
        "params": {"hours": 1},
        "path": "total_cost",
    },
    "error_rate": {
        "url": "/api/monitoring/error-rates",
        "params": {"hours": 24},
        "path": "overall_error_rate",
    },
}


@app.route("/")
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "JSON API Proxy is running"})


@app.route("/search", methods=["POST"])
def search():
    """
    Return list of available metrics.
    Called by Grafana to populate metric selection dropdown.
    """
    logger.info("Search request received")

    # Return list of available metrics
    metrics = list(METRIC_ENDPOINTS.keys())

    return jsonify(metrics)


@app.route("/query", methods=["POST"])
def query():
    """
    Query endpoint for fetching metric data.

    Expected request format from Grafana:
    {
        "targets": [
            {"target": "avg_health_score", "refId": "A", "type": "timeserie"}
        ],
        "range": {
            "from": "2024-01-01T00:00:00.000Z",
            "to": "2024-01-01T12:00:00.000Z"
        }
    }

    Response format:
    [
        {
            "target": "avg_health_score",
            "datapoints": [[value, timestamp_ms], ...]
        }
    ]
    """
    try:
        data = request.json
        logger.info(f"Query request: {data}")

        targets = data.get("targets", [])
        range_data = data.get("range", {})

        results = []

        for target in targets:
            metric_name = target.get("target")

            if metric_name not in METRIC_ENDPOINTS:
                logger.warning(f"Unknown metric: {metric_name}")
                continue

            metric_config = METRIC_ENDPOINTS[metric_name]

            # Build API URL
            url = f"{API_BASE_URL}{metric_config['url']}"
            params = metric_config.get("params", {})

            # Make request to backend
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                backend_data = response.json()

                # Extract value using path
                value = backend_data
                for key in metric_config["path"].split("."):
                    value = value.get(key, 0)

                # Convert to float
                value = float(value) if value is not None else 0.0

                # Create datapoint with current timestamp
                timestamp_ms = int(datetime.now().timestamp() * 1000)

                results.append(
                    {"target": metric_name, "datapoints": [[value, timestamp_ms]]}
                )

                logger.info(f"Metric {metric_name}: {value}")

            except Exception as e:
                logger.error(f"Error fetching {metric_name}: {e}")
                # Return 0 on error
                timestamp_ms = int(datetime.now().timestamp() * 1000)
                results.append(
                    {"target": metric_name, "datapoints": [[0.0, timestamp_ms]]}
                )

        return jsonify(results)

    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/annotations", methods=["POST"])
def annotations():
    """
    Annotations endpoint (not implemented).
    Returns empty list.
    """
    return jsonify([])


@app.route("/tag-keys", methods=["POST"])
def tag_keys():
    """
    Return available tag keys (not implemented).
    Returns empty list.
    """
    return jsonify([])


@app.route("/tag-values", methods=["POST"])
def tag_values():
    """
    Return available tag values (not implemented).
    Returns empty list.
    """
    return jsonify([])


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
