# Dashboards Using Percentile Metrics - Complete Reference

**Last Updated**: January 19, 2026  
**Commits**: `102ca5bf`, `83844215`, `71d92462`

---

## 📊 **Dashboards Affected**

### **1. 🎯 The Four Golden Signals** (`latency-analytics-v1.json`)

**Location**: `grafana/dashboards/executive/latency-analytics-v1.json`

**API Endpoint**: `/api/monitoring/stats/realtime?hours=1`

**Panels Using Percentile Metrics**:

| Panel ID | Title | JSONPath | Expected Value |
|----------|-------|----------|----------------|
| 2 | P50 Latency (Median User Experience) | `$.p50_latency` | e.g., 145.5ms |
| 3 | P95 Latency (95% of Users) | `$.p95_latency` | e.g., 523.75ms |
| 4 | P99 Latency (Tail Latency) | `$.p99_latency` | e.g., 1247.2ms |
| 5 | Latency Percentiles Trend (24h) | `$.p50_latency`, `$.p95_latency`, `$.p99_latency` | Time series chart |

**What It Shows**:
- User-facing latency percentiles
- Full request-response cycle from user's perspective
- Calculated from Prometheus `http_request_duration_seconds` histogram

---

### **2. 🚀 Executive Overview** (`executive-overview-v1.json`)

**Location**: `grafana/dashboards/executive/executive-overview-v1.json`

**API Endpoint**: `/api/monitoring/stats/realtime?hours=1`

**Panels Using Latency Metrics**:

| Panel ID | Title | JSONPath | Expected Value |
|----------|-------|----------|----------------|
| 5 | Avg Response Time | `$.avg_latency_ms` | e.g., 312.5ms |

**What It Shows**:
- Average user-facing latency across all endpoints
- Simple average (not weighted by request count)
- Background color changes based on thresholds:
  - Green: < 500ms
  - Yellow: 500-1000ms
  - Red: > 1000ms

---

## 🔄 **API Response Structure**

### **Endpoint**: `GET /api/monitoring/stats/realtime?hours={1-24}`

**Response Model** (`RealtimeStatsResponse`):

```json
{
  "timestamp": "2026-01-19T14:30:00Z",
  "providers": {
    "openrouter": {
      "total_requests": 1234,
      "total_cost": 12.50,
      "health_score": 95.5,
      "hourly_breakdown": {...}
    }
  },
  "total_requests": 5000,
  "total_cost": 45.25,
  "avg_health_score": 92.3,
  "p50_latency": 145.5,      // ✅ NEW (Commit: 102ca5bf, fixed: 83844215)
  "p95_latency": 523.75,     // ✅ NEW (Commit: 102ca5bf, fixed: 83844215)
  "p99_latency": 1247.2,     // ✅ NEW (Commit: 102ca5bf, fixed: 83844215)
  "avg_latency_ms": 312.5    // ✅ NEW (Commit: 71d92462)
}
```

---

## 📐 **How Metrics Are Calculated**

### **Data Source**: Prometheus `http_request_duration_seconds` Histogram

**Step 1: Prometheus Records**
```
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.01"} 45
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.05"} 189
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.1"} 456
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.5"} 789
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="1"} 892
http_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="+Inf"} 1000
http_request_duration_seconds_sum{endpoint="/v1/chat/completions"} 312.5
http_request_duration_seconds_count{endpoint="/v1/chat/completions"} 1000
```

**Step 2: Parser Calculates Percentiles** (`metrics_parser.py`)
```python
# For each endpoint:
- P50 = interpolate(buckets, 0.50)  → 0.145 seconds
- P95 = interpolate(buckets, 0.95)  → 0.524 seconds
- P99 = interpolate(buckets, 0.99)  → 1.247 seconds
- Avg = sum / count                 → 0.3125 seconds
```

**Step 3: Aggregation** (`monitoring.py`)
```python
# Aggregate across all endpoints:
for endpoint in all_endpoints:
    total_p50 += endpoint_p50
    total_p95 += endpoint_p95
    total_p99 += endpoint_p99
    total_avg += endpoint_avg
    total_weight += 1

# Calculate averages:
p50_latency = (total_p50 / total_weight) * 1000  # Convert to ms
p95_latency = (total_p95 / total_weight) * 1000
p99_latency = (total_p99 / total_weight) * 1000
avg_latency_ms = (total_avg / total_weight) * 1000
```

---

## 🎯 **What's Being Measured**

### **USER-FACING LATENCIES** (Current Implementation) ✅

**Source**: Prometheus `http_request_duration_seconds`  
**Tracked By**: `ObservabilityMiddleware` (all HTTP requests)

**Includes**:
- ✅ API Gateway processing time
- ✅ Authentication/authorization
- ✅ Backend business logic
- ✅ Database queries
- ✅ External provider API calls
- ✅ Response serialization
- ✅ Network overhead

**Example**: User requests `/v1/chat/completions`
- Total time: **450ms** ← This is what we track
  - API gateway: 20ms
  - Auth: 30ms
  - Backend logic: 50ms
  - OpenAI API call: 300ms
  - Serialization: 50ms

---

### **PROVIDER LATENCIES** (Not Used) ❌

**Source**: Redis `latency:{provider}:{model}` sorted sets  
**Tracked By**: `RedisMetrics.record_request()`

**Includes**:
- ❌ Only external provider API call time
- ❌ Does NOT include gateway overhead
- ❌ Does NOT include backend processing

**Example**: Same user request
- Provider latency: **300ms** ← This is NOT what we track for user metrics
  - Only the OpenAI API call duration

**Use Case**: Provider performance comparison, not user experience monitoring

---

## 🧪 **Testing the Metrics**

### **Step 1: Generate Traffic**
```bash
# Generate 100 requests
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null
  sleep 0.1
done
```

### **Step 2: Check Prometheus Metrics**
```bash
# View raw histogram data
curl -s http://localhost:8000/metrics | grep 'http_request_duration_seconds'
```

### **Step 3: Test API Endpoint**
```bash
# Check percentiles
curl -s 'http://localhost:8000/api/monitoring/stats/realtime?hours=1' | jq '{
  avg_latency_ms,
  p50_latency,
  p95_latency,
  p99_latency,
  valid: (.p50_latency <= .p95_latency and .p95_latency <= .p99_latency)
}'
```

**Expected Output**:
```json
{
  "avg_latency_ms": 45.2,
  "p50_latency": 38.5,
  "p95_latency": 89.3,
  "p99_latency": 145.7,
  "valid": true
}
```

### **Step 4: Verify in Grafana**
1. Open: http://localhost:3000
2. Check **Four Golden Signals**:
   - P50 card: ≈38.5ms
   - P95 card: ≈89.3ms
   - P99 card: ≈145.7ms
   - Trend chart: Shows proper ordering
3. Check **Executive Overview**:
   - Avg Response Time: ≈45.2ms

---

## 🔧 **Troubleshooting**

### **Issue: All metrics show 0**

**Cause**: No traffic or Prometheus not scraping

**Solution**:
```bash
# 1. Generate traffic
ab -n 500 -c 10 http://localhost:8000/health

# 2. Check Prometheus metrics endpoint
curl http://localhost:8000/metrics | grep http_request_duration

# 3. Wait 30 seconds for aggregation
sleep 30

# 4. Test API again
curl 'http://localhost:8000/api/monitoring/stats/realtime?hours=1' | jq .p50_latency
```

---

### **Issue: P50 > P95 anomaly still occurs**

**Cause**: Old code still running

**Solution**:
```bash
# 1. Verify latest commit
cd gatewayz-backend
git log --oneline -1  # Should show 71d92462

# 2. Clear Prometheus cache
rm -rf /tmp/prometheus/*

# 3. Restart backend
python -m uvicorn src.main:app --reload --port 8000

# 4. Generate fresh traffic
ab -n 500 -c 10 http://localhost:8000/health
```

---

### **Issue: Executive Overview shows null**

**Cause**: Dashboard cached old response or backend not running

**Solution**:
1. Refresh dashboard (Ctrl+R or Cmd+R)
2. Check browser console (F12) for errors
3. Verify backend: `curl http://localhost:8000/health`
4. Check API response: `curl http://localhost:8000/api/monitoring/stats/realtime?hours=1 | jq .avg_latency_ms`

---

## 📚 **Related Files**

### **Backend**
- `src/routes/monitoring.py:228-239` - Response model definition
- `src/routes/monitoring.py:399-459` - Percentile calculation logic
- `src/services/metrics_parser.py:196-239` - Histogram percentile interpolation
- `src/services/prometheus_metrics.py:102-108` - Histogram bucket definition
- `src/middleware/observability_middleware.py:90-135` - Latency recording

### **Frontend (Grafana)**
- `grafana/dashboards/executive/latency-analytics-v1.json` - Four Golden Signals
- `grafana/dashboards/executive/executive-overview-v1.json` - Executive Overview

### **Documentation**
- `PERCENTILE_METRICS_FIX.md` - Detailed technical guide
- `QUICK_START_PERCENTILE_FIX.md` - Quick reference
- `PERCENTILE_METRICS_FIX_SUMMARY.md` - Implementation summary (project root)

---

**Status**: ✅ All dashboards updated and working  
**Last Commit**: `71d92462` - Add avg_latency_ms for Executive Overview
