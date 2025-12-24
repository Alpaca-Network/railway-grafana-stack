#!/usr/bin/env python3
"""
Health Service Metrics Exporter for GatewayZ
Fetches health data from the Health Service API and exposes it as Prometheus metrics
"""

import os
import time
import requests
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter

# Configuration
HEALTH_SERVICE_URL = os.getenv("HEALTH_SERVICE_URL", "https://health-service-production.up.railway.app")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "30"))
PORT = int(os.getenv("METRICS_PORT", "8002"))
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

# Metrics - Service Status
health_service_up = Gauge(
    'gatewayz_health_service_up',
    'Health service availability (1=up, 0=down)'
)

# Metrics - Monitoring State
health_monitoring_active = Gauge(
    'gatewayz_health_monitoring_active',
    'Health monitoring state (1=active, 0=inactive)'
)

availability_monitoring_active = Gauge(
    'gatewayz_availability_monitoring_active',
    'Availability monitoring state (1=active, 0=inactive)'
)

health_check_interval = Gauge(
    'gatewayz_health_check_interval_seconds',
    'Health check interval in seconds'
)

# Metrics - Tracked Resources
health_tracked_models = Gauge(
    'gatewayz_health_tracked_models',
    'Number of models being tracked'
)

health_tracked_providers = Gauge(
    'gatewayz_health_tracked_providers',
    'Number of providers being tracked'
)

health_tracked_gateways = Gauge(
    'gatewayz_health_tracked_gateways',
    'Number of gateways being tracked'
)

availability_cache_size = Gauge(
    'gatewayz_availability_cache_size',
    'Size of availability cache'
)

# Metrics - Total Resources
health_total_models = Gauge(
    'gatewayz_health_total_models',
    'Total number of models in the system'
)

health_total_providers = Gauge(
    'gatewayz_health_total_providers',
    'Total number of providers in the system'
)

health_total_gateways = Gauge(
    'gatewayz_health_total_gateways',
    'Total number of gateways in the system'
)

tracked_models_count = Gauge(
    'gatewayz_health_tracked_models_count',
    'Number of actively tracked models'
)

# Metrics - Health Status
health_active_incidents = Gauge(
    'gatewayz_health_active_incidents',
    'Number of active incidents'
)

health_status_distribution = Gauge(
    'gatewayz_health_status_distribution',
    'Distribution of health statuses',
    ['status']
)

# Metrics - Cache
health_cache_available = Gauge(
    'gatewayz_health_cache_available',
    'Cache availability status',
    ['cache_type']
)

# Metrics - Error Tracking
scrape_errors = Counter(
    'gatewayz_health_service_scrape_errors_total',
    'Total number of scrape errors'
)

last_successful_scrape = Gauge(
    'gatewayz_health_service_last_successful_scrape',
    'Timestamp of last successful scrape'
)


def fetch_health():
    """Fetch from /health endpoint"""
    try:
        response = requests.get(
            f"{HEALTH_SERVICE_URL}/health",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching /health: {e}")
        return None


def fetch_status():
    """Fetch from /status endpoint"""
    try:
        response = requests.get(
            f"{HEALTH_SERVICE_URL}/status",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching /status: {e}")
        return None


def fetch_metrics():
    """Fetch from /metrics endpoint"""
    try:
        response = requests.get(
            f"{HEALTH_SERVICE_URL}/metrics",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching /metrics: {e}")
        return None


def fetch_cache_stats():
    """Fetch from /cache/stats endpoint"""
    try:
        response = requests.get(
            f"{HEALTH_SERVICE_URL}/cache/stats",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching /cache/stats: {e}")
        return None


def update_metrics():
    """Update all metrics from the health service"""
    print(f"[{datetime.now()}] Updating health service metrics...")

    # Track if any fetch succeeded
    any_success = False

    # Fetch /health endpoint
    health_data = fetch_health()
    if health_data:
        try:
            health_service_up.set(1)  # Service is up if we got a response
            any_success = True
            print(f"  /health: OK")
        except Exception as e:
            print(f"  Error processing /health: {e}")
            scrape_errors.inc()
    else:
        health_service_up.set(0)

    # Fetch /status endpoint
    status_data = fetch_status()
    if status_data:
        try:
            health_monitoring_active.set(1 if status_data.get("health_monitoring_active", False) else 0)
            availability_monitoring_active.set(1 if status_data.get("availability_monitoring_active", False) else 0)
            health_tracked_models.set(status_data.get("models_tracked", 0))
            health_tracked_providers.set(status_data.get("providers_tracked", 0))
            health_tracked_gateways.set(status_data.get("gateways_tracked", 0))
            availability_cache_size.set(status_data.get("availability_cache_size", 0))
            health_check_interval.set(status_data.get("health_check_interval", 300))
            any_success = True
            print(f"  /status: OK")
        except Exception as e:
            print(f"  Error processing /status: {e}")
            scrape_errors.inc()

    # Fetch /metrics endpoint
    metrics_data = fetch_metrics()
    if metrics_data:
        try:
            health_total_models.set(metrics_data.get("total_models", 0))
            health_total_providers.set(metrics_data.get("total_providers", 0))
            health_total_gateways.set(metrics_data.get("total_gateways", 0))
            tracked_models_count.set(metrics_data.get("tracked_models", 0))
            health_active_incidents.set(metrics_data.get("active_incidents", 0))

            # Process status distribution
            status_dist = metrics_data.get("status_distribution", {})
            if isinstance(status_dist, dict):
                for status, count in status_dist.items():
                    health_status_distribution.labels(status=status).set(count)
            any_success = True
            print(f"  /metrics: OK")
        except Exception as e:
            print(f"  Error processing /metrics: {e}")
            scrape_errors.inc()

    # Fetch /cache/stats endpoint
    cache_data = fetch_cache_stats()
    if cache_data:
        try:
            # Set cache availability flags
            cache_available = 1 if cache_data.get("cache_available", False) else 0
            system_health_cached = 1 if cache_data.get("system_health_cached", False) else 0
            providers_health_cached = 1 if cache_data.get("providers_health_cached", False) else 0
            models_health_cached = 1 if cache_data.get("models_health_cached", False) else 0

            health_cache_available.labels(cache_type="redis").set(cache_available)
            health_cache_available.labels(cache_type="system_health").set(system_health_cached)
            health_cache_available.labels(cache_type="providers_health").set(providers_health_cached)
            health_cache_available.labels(cache_type="models_health").set(models_health_cached)
            any_success = True
            print(f"  /cache/stats: OK")
        except Exception as e:
            print(f"  Error processing /cache/stats: {e}")
            scrape_errors.inc()

    # Update last successful scrape if at least one endpoint succeeded
    if any_success:
        last_successful_scrape.set(time.time())
        print(f"  Metrics updated successfully")
    else:
        print(f"  All endpoints failed")
        scrape_errors.inc()


def main():
    """Main function"""
    print(f"Starting Health Service Metrics Exporter")
    print(f"  Health Service URL: {HEALTH_SERVICE_URL}")
    print(f"  Scrape Interval: {SCRAPE_INTERVAL}s")
    print(f"  Metrics Port: {PORT}")

    # Start Prometheus metrics server
    start_http_server(PORT)
    print(f"Metrics server started on port {PORT}")

    # Initial update
    update_metrics()

    # Periodic updates
    while True:
        time.sleep(SCRAPE_INTERVAL)
        update_metrics()


if __name__ == '__main__':
    main()
