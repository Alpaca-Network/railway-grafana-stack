"""
Prometheus metrics parser service.

This module reads from the Prometheus /metrics endpoint and extracts:
- Latency metrics (p50, p95, p99, average)
- Request counts by endpoint/method
- Error rates per endpoint

The metrics are parsed from Prometheus exposition format and returned
in a structured JSON format.
"""

import logging
import re
import os
from typing import Optional
from collections import defaultdict

import httpx

logger = logging.getLogger(__name__)


class PrometheusMetricsParser:
    """Parser for Prometheus metrics in exposition format."""

    def __init__(self, metrics_url: str = None):
        """
        Initialize the parser with the metrics endpoint URL.
        
        Args:
            metrics_url: URL of the Prometheus metrics endpoint.
                        Defaults to Railway internal URL or localhost
        """
        if metrics_url is None:
            # For Railway: use internal URL
            # For local Docker: use service name
            metrics_url = os.getenv(
                "PROMETHEUS_METRICS_URL",
                os.getenv(
                    "PROMETHEUS_INTERNAL_URL",
                    "http://prometheus.railway.internal:9090"
                )
            )
            # Append /metrics endpoint
            if not metrics_url.endswith("/metrics"):
                metrics_url = f"{metrics_url}/metrics"
        
        self.metrics_url = metrics_url
        self.timeout = 10.0  # 10 second timeout for metrics fetch
        logger.info(f"Initialized PrometheusMetricsParser with URL: {self.metrics_url}")

    async def fetch_metrics(self) -> Optional[str]:
        """
        Fetch raw metrics from the Prometheus endpoint.
        
        Returns:
            Raw metrics text in Prometheus exposition format, or None if fetch fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.metrics_url)
                response.raise_for_status()
                logger.debug(f"Successfully fetched metrics from {self.metrics_url}")
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch metrics from {self.metrics_url}: {e}")
            return None

    def parse_metrics(self, metrics_text: str) -> dict:
        """
        Parse Prometheus exposition format metrics and extract relevant data.
        
        Args:
            metrics_text: Raw metrics in Prometheus exposition format
            
        Returns:
            Structured metrics dict with latency, requests, and errors
        """
        latency_buckets = defaultdict(list)  # {endpoint: [(bucket, value), ...]}
        latency_sum = {}  # {endpoint: sum_value}
        latency_count = {}  # {endpoint: count_value}
        request_counts = defaultdict(lambda: defaultdict(int))  # {endpoint: {method: count}}
        error_counts = defaultdict(lambda: defaultdict(int))  # {endpoint: {method: count}}

        lines = metrics_text.split("\n")

        for line in lines:
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse fastapi_request_duration_seconds_bucket
            if "fastapi_request_duration_seconds_bucket" in line:
                match = re.match(
                    r'fastapi_request_duration_seconds_bucket\{.*?le="([^"]+)".*?endpoint="([^"]+)".*?\}\s+([\d.]+)',
                    line,
                )
                if match:
                    bucket_val = float(match.group(1)) if match.group(1) != "+Inf" else float("inf")
                    endpoint = match.group(2)
                    value = float(match.group(3))
                    latency_buckets[endpoint].append((bucket_val, value))

            # Parse fastapi_request_duration_seconds_sum
            elif "fastapi_request_duration_seconds_sum" in line and "bucket" not in line:
                match = re.match(
                    r'fastapi_request_duration_seconds_sum\{.*?endpoint="([^"]+)".*?\}\s+([\d.]+)',
                    line,
                )
                if match:
                    endpoint = match.group(1)
                    value = float(match.group(2))
                    latency_sum[endpoint] = value

            # Parse fastapi_request_duration_seconds_count
            elif "fastapi_request_duration_seconds_count" in line:
                match = re.match(
                    r'fastapi_request_duration_seconds_count\{.*?endpoint="([^"]+)".*?\}\s+([\d.]+)',
                    line,
                )
                if match:
                    endpoint = match.group(1)
                    value = float(match.group(2))
                    latency_count[endpoint] = value

            # Parse fastapi_requests_total (request counts)
            elif "fastapi_requests_total" in line and "bucket" not in line:
                match = re.match(
                    r'fastapi_requests_total\{.*?method="([^"]+)".*?endpoint="([^"]+)".*?\}\s+([\d.]+)',
                    line,
                )
                if match:
                    method = match.group(1)
                    endpoint = match.group(2)
                    value = int(float(match.group(3)))
                    request_counts[endpoint][method] += value

        # Compute latency percentiles and averages
        latency_metrics = self._compute_latency_metrics(
            latency_buckets, latency_sum, latency_count
        )

        # Build response
        return {
            "latency": latency_metrics,
            "requests": dict(request_counts),
            "errors": dict(error_counts),
        }

    def _compute_latency_metrics(
        self,
        buckets: dict,
        sums: dict,
        counts: dict,
    ) -> dict:
        """
        Compute latency percentiles and averages from histogram data.
        
        Args:
            buckets: {endpoint: [(bucket_value, count), ...]}
            sums: {endpoint: sum_value}
            counts: {endpoint: count_value}
            
        Returns:
            {
                "avg": float,
                "p50": float,
                "p95": float,
                "p99": float
            }
        """
        result = {}

        # Get all unique endpoints from buckets, sums, and counts
        all_endpoints = set(buckets.keys()) | set(sums.keys()) | set(counts.keys())

        for endpoint in all_endpoints:
            endpoint_data = {}

            # Calculate average latency
            if endpoint in sums and endpoint in counts and counts[endpoint] > 0:
                endpoint_data["avg"] = round(sums[endpoint] / counts[endpoint], 4)
            else:
                endpoint_data["avg"] = None

            # Calculate percentiles from buckets
            if endpoint in buckets:
                sorted_buckets = sorted(buckets[endpoint], key=lambda x: x[0])
                endpoint_data["p50"] = self._calculate_percentile(sorted_buckets, 0.50)
                endpoint_data["p95"] = self._calculate_percentile(sorted_buckets, 0.95)
                endpoint_data["p99"] = self._calculate_percentile(sorted_buckets, 0.99)
            else:
                endpoint_data["p50"] = None
                endpoint_data["p95"] = None
                endpoint_data["p99"] = None

            result[endpoint] = endpoint_data

        return result

    def _calculate_percentile(
        self, sorted_buckets: list[tuple[float, float]], percentile: float
    ) -> Optional[float]:
        """
        Calculate percentile from histogram buckets.
        
        Uses linear interpolation between buckets.
        
        Args:
            sorted_buckets: List of (bucket_boundary, cumulative_count) tuples, sorted by boundary
            percentile: Percentile to calculate (0.0-1.0)
            
        Returns:
            Percentile value or None if insufficient data
        """
        if not sorted_buckets:
            return None

        # Get the total count from the +Inf bucket
        total_count = sorted_buckets[-1][1] if sorted_buckets[-1][0] == float("inf") else 0
        if total_count == 0:
            return None

        # Find the target count for this percentile
        target_count = percentile * total_count

        # Find the bucket containing the percentile
        for i, (boundary, count) in enumerate(sorted_buckets):
            if count >= target_count:
                if i == 0:
                    # Percentile is in the first bucket
                    return round(boundary, 4)
                else:
                    # Linear interpolation between buckets
                    prev_boundary, prev_count = sorted_buckets[i - 1]
                    if count == prev_count:
                        # No data in this bucket, use boundary
                        return round(boundary, 4)
                    # Interpolate
                    fraction = (target_count - prev_count) / (count - prev_count)
                    result = prev_boundary + fraction * (boundary - prev_boundary)
                    return round(result, 4)

        # Percentile is beyond all buckets
        if sorted_buckets[-1][0] != float("inf"):
            return round(sorted_buckets[-1][0], 4)
        return None

    async def get_metrics(self) -> dict:
        """
        Fetch and parse metrics in one call.
        
        Returns:
            Structured metrics dict or empty structure if fetch/parse fails
        """
        metrics_text = await self.fetch_metrics()
        if not metrics_text:
            return {
                "latency": {},
                "requests": {},
                "errors": {},
            }

        return self.parse_metrics(metrics_text)


# Global parser instance
_parser: Optional[PrometheusMetricsParser] = None


def get_metrics_parser(metrics_url: str = None) -> PrometheusMetricsParser:
    """
    Get or create the global metrics parser instance.
    
    Args:
        metrics_url: URL of the Prometheus metrics endpoint.
                    If None, uses Railway internal URL or localhost
        
    Returns:
        PrometheusMetricsParser instance
    """
    global _parser
    if _parser is None:
        _parser = PrometheusMetricsParser(metrics_url)
    return _parser
