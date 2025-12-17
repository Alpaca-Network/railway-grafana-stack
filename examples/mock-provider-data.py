#!/usr/bin/env python3
"""
Mock Provider Data Generator
Generates realistic provider metrics for local testing
Writes metrics directly to a file that Prometheus can scrape
"""

import os
import time
from datetime import datetime

# Mock provider data
MOCK_PROVIDERS = [
    {
        "name": "OpenAI",
        "slug": "openai",
        "health_status": "healthy",
        "is_active": True,
        "response_time_ms": 245,
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_image_generation": False,
    },
    {
        "name": "Anthropic",
        "slug": "anthropic",
        "health_status": "healthy",
        "is_active": True,
        "response_time_ms": 320,
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_image_generation": False,
    },
    {
        "name": "Google",
        "slug": "google",
        "health_status": "degraded",
        "is_active": True,
        "response_time_ms": 450,
        "supports_streaming": False,
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_image_generation": True,
    },
    {
        "name": "Cohere",
        "slug": "cohere",
        "health_status": "healthy",
        "is_active": True,
        "response_time_ms": 280,
        "supports_streaming": True,
        "supports_function_calling": False,
        "supports_vision": False,
        "supports_image_generation": False,
    },
    {
        "name": "Mistral",
        "slug": "mistral",
        "health_status": "down",
        "is_active": False,
        "response_time_ms": 0,
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": False,
        "supports_image_generation": False,
    },
]

def health_status_to_code(status):
    """Convert health status to numeric code"""
    status_map = {
        'healthy': 1,
        'degraded': 2,
        'down': 3,
        'unknown': 0
    }
    return status_map.get(status.lower(), 0)

def generate_metrics():
    """Generate Prometheus metrics from mock data"""
    metrics = []
    
    # Count stats
    total = len(MOCK_PROVIDERS)
    active = sum(1 for p in MOCK_PROVIDERS if p['is_active'])
    inactive = total - active
    healthy = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'healthy')
    degraded = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'degraded')
    down = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'down')
    unknown = sum(1 for p in MOCK_PROVIDERS if p['health_status'] == 'unknown')
    
    # Aggregate metrics
    metrics.append(f"# HELP gatewayz_providers_total Total number of providers")
    metrics.append(f"# TYPE gatewayz_providers_total gauge")
    metrics.append(f"gatewayz_providers_total {total}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_active Number of active providers")
    metrics.append(f"# TYPE gatewayz_providers_active gauge")
    metrics.append(f"gatewayz_providers_active {active}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_inactive Number of inactive providers")
    metrics.append(f"# TYPE gatewayz_providers_inactive gauge")
    metrics.append(f"gatewayz_providers_inactive {inactive}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_healthy Number of healthy providers")
    metrics.append(f"# TYPE gatewayz_providers_healthy gauge")
    metrics.append(f"gatewayz_providers_healthy {healthy}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_degraded Number of degraded providers")
    metrics.append(f"# TYPE gatewayz_providers_degraded gauge")
    metrics.append(f"gatewayz_providers_degraded {degraded}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_down Number of down providers")
    metrics.append(f"# TYPE gatewayz_providers_down gauge")
    metrics.append(f"gatewayz_providers_down {down}")
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_providers_unknown Number of providers with unknown status")
    metrics.append(f"# TYPE gatewayz_providers_unknown gauge")
    metrics.append(f"gatewayz_providers_unknown {unknown}")
    metrics.append("")
    
    # Per-provider metrics
    metrics.append(f"# HELP gatewayz_provider_response_time_ms Average response time in milliseconds")
    metrics.append(f"# TYPE gatewayz_provider_response_time_ms gauge")
    for provider in MOCK_PROVIDERS:
        metrics.append(f'gatewayz_provider_response_time_ms{{provider="{provider["slug"]}"}} {provider["response_time_ms"]}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_supports_streaming Provider supports streaming")
    metrics.append(f"# TYPE gatewayz_provider_supports_streaming gauge")
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['supports_streaming'] else 0
        metrics.append(f'gatewayz_provider_supports_streaming{{provider="{provider["slug"]}"}} {value}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_supports_function_calling Provider supports function calling")
    metrics.append(f"# TYPE gatewayz_provider_supports_function_calling gauge")
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['supports_function_calling'] else 0
        metrics.append(f'gatewayz_provider_supports_function_calling{{provider="{provider["slug"]}"}} {value}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_supports_vision Provider supports vision")
    metrics.append(f"# TYPE gatewayz_provider_supports_vision gauge")
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['supports_vision'] else 0
        metrics.append(f'gatewayz_provider_supports_vision{{provider="{provider["slug"]}"}} {value}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_supports_image_generation Provider supports image generation")
    metrics.append(f"# TYPE gatewayz_provider_supports_image_generation gauge")
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['supports_image_generation'] else 0
        metrics.append(f'gatewayz_provider_supports_image_generation{{provider="{provider["slug"]}"}} {value}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_is_active Provider is active")
    metrics.append(f"# TYPE gatewayz_provider_is_active gauge")
    for provider in MOCK_PROVIDERS:
        value = 1 if provider['is_active'] else 0
        metrics.append(f'gatewayz_provider_is_active{{provider="{provider["slug"]}"}} {value}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_health_status Provider health status")
    metrics.append(f"# TYPE gatewayz_provider_health_status gauge")
    for provider in MOCK_PROVIDERS:
        code = health_status_to_code(provider['health_status'])
        metrics.append(f'gatewayz_provider_health_status{{provider="{provider["slug"]}"}} {code}')
    metrics.append("")
    
    metrics.append(f"# HELP gatewayz_provider_metrics_last_update Last update timestamp")
    metrics.append(f"# TYPE gatewayz_provider_metrics_last_update gauge")
    metrics.append(f"gatewayz_provider_metrics_last_update {int(time.time())}")
    
    return "\n".join(metrics)

def main():
    """Generate and output metrics"""
    output_file = "/tmp/mock_provider_metrics.txt"
    
    print(f"Generating mock provider metrics...")
    metrics = generate_metrics()
    
    with open(output_file, 'w') as f:
        f.write(metrics)
    
    print(f"Metrics written to {output_file}")
    print("\nGenerated metrics:")
    print(metrics)

if __name__ == '__main__':
    main()
