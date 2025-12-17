#!/usr/bin/env python3
"""
Health Metrics Generator for GatewayZ Application Health Dashboard
Generates mock health metrics that match the dashboard expectations
"""

import time
import random
from datetime import datetime
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Provider health scores (0-100)
provider_health_score = Gauge(
    'gatewayz_provider_health_score',
    'Provider health score (0-100)',
    ['provider']
)

# Model-specific metrics
model_uptime_24h = Gauge(
    'gatewayz_model_uptime_24h',
    'Model uptime in last 24 hours (%)',
    ['provider', 'model']
)

model_uptime_7d = Gauge(
    'gatewayz_model_uptime_7d',
    'Model uptime in last 7 days (%)',
    ['provider', 'model']
)

model_uptime_30d = Gauge(
    'gatewayz_model_uptime_30d',
    'Model uptime in last 30 days (%)',
    ['provider', 'model']
)

model_error_rate = Gauge(
    'gatewayz_model_error_rate',
    'Model error rate',
    ['provider', 'model']
)

model_avg_response_time_ms = Gauge(
    'gatewayz_model_avg_response_time_ms',
    'Model average response time (ms)',
    ['provider', 'model']
)

model_latency_p95_ms = Histogram(
    'gatewayz_model_latency_p95_ms',
    'Model P95 latency (ms)',
    ['provider', 'model']
)

model_latency_p99_ms = Histogram(
    'gatewayz_model_latency_p99_ms',
    'Model P99 latency (ms)',
    ['provider', 'model']
)

model_call_count = Gauge(
    'gatewayz_model_call_count',
    'Model call count',
    ['provider', 'model']
)

# Error metrics
error_rate_by_model = Gauge(
    'gatewayz_error_rate_by_model',
    'Error rate by model',
    ['provider', 'model']
)

recent_errors_by_provider = Gauge(
    'gatewayz_recent_errors_by_provider',
    'Recent error count by provider',
    ['provider']
)

# Circuit breaker states
circuit_breaker_state = Gauge(
    'gatewayz_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['provider']
)

# Uptime metrics
uptime_24h = Gauge(
    'gatewayz_uptime_24h',
    'Provider uptime in last 24 hours (%)',
    ['provider']
)

uptime_7d = Gauge(
    'gatewayz_uptime_7d',
    'Provider uptime in last 7 days (%)',
    ['provider']
)

uptime_30d = Gauge(
    'gatewayz_uptime_30d',
    'Provider uptime in last 30 days (%)',
    ['provider']
)

# Anomalies
detected_anomalies = Gauge(
    'gatewayz_detected_anomalies',
    'Detected anomalies count',
    ['type']
)

# Latency trends
latency_trends = Gauge(
    'gatewayz_latency_trends',
    'Latency trends over time',
    ['provider', 'model']
)

# Cost analysis
cost_by_provider = Gauge(
    'gatewayz_cost_by_provider',
    'Cost breakdown by provider (USD)',
    ['provider']
)

# Token efficiency
token_efficiency = Gauge(
    'gatewayz_token_efficiency',
    'Token efficiency (tokens per request)',
    ['provider', 'model']
)

# Overall error rate
overall_error_rate = Gauge(
    'gatewayz_error_rate',
    'Overall system error rate'
)


def generate_metrics():
    """Generate realistic mock metrics"""
    
    providers = ['openai', 'anthropic', 'google', 'cohere', 'mistral']
    models = {
        'openai': ['gpt-4', 'gpt-3.5-turbo', 'gpt-4-turbo'],
        'anthropic': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
        'google': ['gemini-pro', 'gemini-1.5-pro'],
        'cohere': ['command-r', 'command-r-plus'],
        'mistral': ['mistral-large', 'mistral-medium']
    }
    
    # Generate provider health scores
    for provider in providers:
        # Health scores trend around 85-98 with some variation
        health = max(50, min(100, random.gauss(92, 5)))
        provider_health_score.labels(provider=provider).set(health)
        
        # Circuit breaker states (mostly closed, occasionally open)
        state = random.choices([0, 1, 2], weights=[0.9, 0.05, 0.05])[0]
        circuit_breaker_state.labels(provider=provider).set(state)
        
        # Uptime metrics
        uptime_24h.labels(provider=provider).set(random.gauss(99.5, 0.3))
        uptime_7d.labels(provider=provider).set(random.gauss(99.2, 0.5))
        uptime_30d.labels(provider=provider).set(random.gauss(99.0, 0.7))
        
        # Cost metrics (random between $10-500 per day)
        cost_by_provider.labels(provider=provider).set(random.uniform(10, 500))
        
        # Recent errors
        recent_errors_by_provider.labels(provider=provider).set(
            max(0, int(random.gauss(5, 3)))
        )
        
        # Generate model-specific metrics
        for model in models.get(provider, []):
            # Uptime metrics
            model_uptime_24h.labels(provider=provider, model=model).set(
                random.gauss(99.7, 0.2)
            )
            model_uptime_7d.labels(provider=provider, model=model).set(
                random.gauss(99.5, 0.3)
            )
            model_uptime_30d.labels(provider=provider, model=model).set(
                random.gauss(99.3, 0.5)
            )
            
            # Error rates (0-2%)
            error_rate = max(0, random.gauss(0.008, 0.003))
            model_error_rate.labels(provider=provider, model=model).set(error_rate)
            error_rate_by_model.labels(provider=provider, model=model).set(error_rate)
            
            # Response times (100-500ms)
            response_time = max(50, random.gauss(250, 80))
            model_avg_response_time_ms.labels(provider=provider, model=model).set(
                response_time
            )
            
            # Latency percentiles
            p95 = response_time * random.uniform(1.2, 1.5)
            p99 = response_time * random.uniform(1.5, 2.0)
            model_latency_p95_ms.labels(provider=provider, model=model).observe(p95)
            model_latency_p99_ms.labels(provider=provider, model=model).observe(p99)
            
            # Call counts (1000-100000)
            call_count = random.randint(1000, 100000)
            model_call_count.labels(provider=provider, model=model).set(call_count)
            
            # Token efficiency (200-1000 tokens per request)
            token_eff = random.uniform(200, 1000)
            token_efficiency.labels(provider=provider, model=model).set(token_eff)
            
            # Latency trends
            latency_trends.labels(provider=provider, model=model).set(
                max(50, random.gauss(250, 80))
            )
    
    # Overall error rate
    overall_error_rate.set(random.gauss(0.008, 0.002))
    
    # Anomalies
    detected_anomalies.labels(type='latency_spike').set(
        max(0, int(random.gauss(1, 1)))
    )
    detected_anomalies.labels(type='error_rate_increase').set(
        max(0, int(random.gauss(0.5, 0.5)))
    )
    detected_anomalies.labels(type='availability_drop').set(
        max(0, int(random.gauss(0.2, 0.3)))
    )


def main():
    """Start metrics server and generate metrics"""
    # Start Prometheus metrics server on port 8000
    start_http_server(8000)
    print("Health metrics generator started on http://localhost:8000/metrics")
    
    # Generate metrics every 15 seconds
    while True:
        try:
            generate_metrics()
            time.sleep(15)
        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"Error generating metrics: {e}")
            time.sleep(5)


if __name__ == '__main__':
    main()
