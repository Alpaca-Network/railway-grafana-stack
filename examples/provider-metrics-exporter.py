#!/usr/bin/env python3
"""
Provider Metrics Exporter for GatewayZ
Fetches provider data from the GatewayZ API and exposes it as Prometheus metrics
"""

import os
import time
import requests
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter, Info

# Configuration
GATEWAY_API_URL = os.getenv("GATEWAY_API_URL", "https://api.gatewayz.ai")
ADMIN_KEY = os.getenv("ADMIN_KEY", "gw_live_wTfpLJ5VB28qMXpOAhr7Uw")
SCRAPE_INTERVAL = int(os.getenv("SCRAPE_INTERVAL", "60"))
PORT = int(os.getenv("METRICS_PORT", "8001"))

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {ADMIN_KEY}",
    "Content-Type": "application/json"
}

# Metrics
providers_total = Gauge(
    'gatewayz_providers_total',
    'Total number of providers'
)

providers_active = Gauge(
    'gatewayz_providers_active',
    'Number of active providers'
)

providers_inactive = Gauge(
    'gatewayz_providers_inactive',
    'Number of inactive providers'
)

providers_healthy = Gauge(
    'gatewayz_providers_healthy',
    'Number of healthy providers'
)

providers_degraded = Gauge(
    'gatewayz_providers_degraded',
    'Number of degraded providers'
)

providers_down = Gauge(
    'gatewayz_providers_down',
    'Number of down providers'
)

providers_unknown = Gauge(
    'gatewayz_providers_unknown',
    'Number of providers with unknown status'
)

provider_info = Info(
    'gatewayz_provider',
    'Provider information',
    ['name', 'slug', 'health_status', 'is_active']
)

provider_response_time = Gauge(
    'gatewayz_provider_response_time_ms',
    'Average response time in milliseconds',
    ['provider']
)

provider_streaming = Gauge(
    'gatewayz_provider_supports_streaming',
    'Provider supports streaming (1=yes, 0=no)',
    ['provider']
)

provider_function_calling = Gauge(
    'gatewayz_provider_supports_function_calling',
    'Provider supports function calling (1=yes, 0=no)',
    ['provider']
)

provider_vision = Gauge(
    'gatewayz_provider_supports_vision',
    'Provider supports vision (1=yes, 0=no)',
    ['provider']
)

provider_image_generation = Gauge(
    'gatewayz_provider_supports_image_generation',
    'Provider supports image generation (1=yes, 0=no)',
    ['provider']
)

provider_active_status = Gauge(
    'gatewayz_provider_is_active',
    'Provider is active (1=yes, 0=no)',
    ['provider']
)

provider_health_status = Gauge(
    'gatewayz_provider_health_status',
    'Provider health status (0=unknown, 1=healthy, 2=degraded, 3=down)',
    ['provider']
)

last_update_timestamp = Gauge(
    'gatewayz_provider_metrics_last_update',
    'Timestamp of last successful metrics update'
)

scrape_errors = Counter(
    'gatewayz_provider_scrape_errors_total',
    'Total number of scrape errors'
)


def fetch_provider_stats():
    """Fetch provider statistics from the API"""
    try:
        response = requests.get(
            f"{GATEWAY_API_URL}/providers/stats",
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching provider stats: {e}")
        scrape_errors.inc()
        return None


def fetch_providers():
    """Fetch all providers from the API"""
    try:
        response = requests.get(
            f"{GATEWAY_API_URL}/providers",
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching providers: {e}")
        scrape_errors.inc()
        return None


def health_status_to_code(status):
    """Convert health status string to numeric code"""
    status_map = {
        'healthy': 1,
        'degraded': 2,
        'down': 3,
        'unknown': 0
    }
    return status_map.get(status.lower(), 0)


def update_metrics():
    """Update all metrics from the API"""
    print(f"[{datetime.now()}] Updating provider metrics...")
    
    # Fetch and update stats
    stats = fetch_provider_stats()
    if stats:
        providers_total.set(stats.get('total', 0))
        providers_active.set(stats.get('active', 0))
        providers_inactive.set(stats.get('inactive', 0))
        providers_healthy.set(stats.get('healthy', 0))
        providers_degraded.set(stats.get('degraded', 0))
        providers_down.set(stats.get('down', 0))
        providers_unknown.set(stats.get('unknown', 0))
        print(f"  Stats updated: {stats}")
    
    # Fetch and update individual providers
    providers = fetch_providers()
    if providers:
        print(f"  Found {len(providers)} providers")
        
        for provider in providers:
            name = provider.get('name', 'unknown')
            slug = provider.get('slug', 'unknown')
            health_status = provider.get('health_status', 'unknown')
            is_active = provider.get('is_active', False)
            response_time = provider.get('average_response_time_ms', 0)
            
            # Update provider info
            provider_info.labels(
                name=name,
                slug=slug,
                health_status=health_status,
                is_active=str(is_active)
            ).info({
                'description': provider.get('description', ''),
                'base_url': provider.get('base_url', ''),
                'site_url': provider.get('site_url', ''),
                'last_health_check': provider.get('last_health_check_at', '')
            })
            
            # Update response time
            provider_response_time.labels(provider=slug).set(response_time)
            
            # Update capabilities
            provider_streaming.labels(provider=slug).set(
                1 if provider.get('supports_streaming', False) else 0
            )
            provider_function_calling.labels(provider=slug).set(
                1 if provider.get('supports_function_calling', False) else 0
            )
            provider_vision.labels(provider=slug).set(
                1 if provider.get('supports_vision', False) else 0
            )
            provider_image_generation.labels(provider=slug).set(
                1 if provider.get('supports_image_generation', False) else 0
            )
            
            # Update status
            provider_active_status.labels(provider=slug).set(
                1 if is_active else 0
            )
            provider_health_status.labels(provider=slug).set(
                health_status_to_code(health_status)
            )
        
        # Update last update timestamp
        last_update_timestamp.set(time.time())
        print(f"  Metrics updated successfully")
    else:
        print(f"  No providers found or API error")


def main():
    """Main function"""
    print(f"Starting Provider Metrics Exporter")
    print(f"  Gateway API URL: {GATEWAY_API_URL}")
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
