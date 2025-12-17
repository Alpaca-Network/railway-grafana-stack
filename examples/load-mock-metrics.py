#!/usr/bin/env python3
"""
Load Mock Provider Metrics into Prometheus
Directly pushes mock provider metrics to Prometheus using the push gateway approach
"""

import requests
import time
import json

PROMETHEUS_URL = "http://localhost:9090"
MOCK_PROVIDERS = [
    {"name": "OpenAI", "slug": "openai", "health_status": "healthy", "is_active": True, "response_time_ms": 245},
    {"name": "Anthropic", "slug": "anthropic", "health_status": "healthy", "is_active": True, "response_time_ms": 320},
    {"name": "Google", "slug": "google", "health_status": "degraded", "is_active": True, "response_time_ms": 450},
    {"name": "Cohere", "slug": "cohere", "health_status": "healthy", "is_active": True, "response_time_ms": 280},
    {"name": "Mistral", "slug": "mistral", "health_status": "down", "is_active": False, "response_time_ms": 0},
]

def health_status_to_code(status):
    status_map = {'healthy': 1, 'degraded': 2, 'down': 3, 'unknown': 0}
    return status_map.get(status.lower(), 0)

def push_metrics():
    """Push metrics to Prometheus"""
    # Count stats
    total = len(MOCK_PROVIDERS)
    active = sum(1 for p in MOCK_PROVIDERS if p['is_active'])
    inactive = total - active
    healthy = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'healthy')
    degraded = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'degraded')
    down = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'down')
    
    # Build metrics text
    metrics = f"""# HELP gatewayz_providers_total Total number of providers
# TYPE gatewayz_providers_total gauge
gatewayz_providers_total {total}

# HELP gatewayz_providers_active Number of active providers
# TYPE gatewayz_providers_active gauge
gatewayz_providers_active {active}

# HELP gatewayz_providers_inactive Number of inactive providers
# TYPE gatewayz_providers_inactive gauge
gatewayz_providers_inactive {inactive}

# HELP gatewayz_providers_healthy Number of healthy providers
# TYPE gatewayz_providers_healthy gauge
gatewayz_providers_healthy {healthy}

# HELP gatewayz_providers_degraded Number of degraded providers
# TYPE gatewayz_providers_degraded gauge
gatewayz_providers_degraded {degraded}

# HELP gatewayz_providers_down Number of down providers
# TYPE gatewayz_providers_down gauge
gatewayz_providers_down {down}

# HELP gatewayz_provider_response_time_ms Average response time in milliseconds
# TYPE gatewayz_provider_response_time_ms gauge
"""
    
    for provider in MOCK_PROVIDERS:
        metrics += f'gatewayz_provider_response_time_ms{{provider="{provider["slug"]}"}} {provider["response_time_ms"]}\n'
    
    metrics += "\n# HELP gatewayz_provider_is_active Provider is active\n# TYPE gatewayz_provider_is_active gauge\n"
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['is_active'] else 0
        metrics += f'gatewayz_provider_is_active{{provider="{provider["slug"]}"}} {value}\n'
    
    metrics += "\n# HELP gatewayz_provider_health_status Provider health status\n# TYPE gatewayz_provider_health_status gauge\n"
    for provider in MOCK_PROVIDERS:
        code = health_status_to_code(provider['health_status'])
        metrics += f'gatewayz_provider_health_status{{provider="{provider["slug"]}"}} {code}\n'
    
    # Write to file that Prometheus can read
    with open('/tmp/mock_provider_metrics.txt', 'w') as f:
        f.write(metrics)
    
    print("✅ Mock provider metrics generated and saved to /tmp/mock_provider_metrics.txt")
    print("\nMetrics summary:")
    print(f"  Total Providers: {total}")
    print(f"  Active: {active}, Inactive: {inactive}")
    print(f"  Healthy: {healthy}, Degraded: {degraded}, Down: {down}")
    print("\n📊 Provider details:")
    for p in MOCK_PROVIDERS:
        status = "✓" if p['is_active'] else "✗"
        print(f"  {status} {p['name']:12} - {p['health_status']:10} ({p['response_time_ms']}ms)")

if __name__ == '__main__':
    push_metrics()
