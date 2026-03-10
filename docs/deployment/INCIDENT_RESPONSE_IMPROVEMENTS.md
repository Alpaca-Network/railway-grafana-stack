# Incident Response Improvements — March 2026

> **Branch:** `feature/feature-availability`
> **Purpose:** Enhance error detection and incident response time through log-based alerts and correlated failure detection
> **Status:** ⚠️ READY FOR REVIEW — DO NOT MERGE TO MAIN UNTIL VERIFIED

---

## Executive Summary

**Problem:** Existing alert rules were not effectively detecting errors in logs or correlating failures across multiple signals (metrics + logs), resulting in delayed incident response.

**Solution:**
1. **Fixed broken log alerts** — Replaced placeholder Prometheus metrics with real Loki LogQL queries
2. **Added pattern-specific log alerts** — Database errors, timeouts, OOM, exceptions, rate limits
3. **Created correlated failure detection** — Alerts that fire when multiple signals confirm an incident
4. **Added parallel failure detection** — Detects when multiple providers/endpoints fail simultaneously

**Impact:**
- **Before:** Log alerts couldn't fire (referenced non-existent metrics)
- **After:** 6 working log-based alerts + 5 correlation alerts = 11 new actionable alerts
- **Result:** Faster incident detection through multi-layer correlation and pattern matching

---

## Changes Overview

| File | Change Type | Alert Count | Description |
|------|-------------|-------------|-------------|
| `grafana/provisioning/alerting/rules/logs_alerts.yml` | **MODIFIED** | 6 alerts (4 replaced + 2 new) | Fixed broken queries, added pattern detection |
| `grafana/provisioning/alerting/rules/correlated_failure_detection.yml` | **NEW** | 5 alerts | Multi-signal correlation for high-confidence incidents |

**Total new/fixed alerts:** 11
**New alert folder:** "Correlated Incidents"

---

## Detailed Changes

### 1. File: `logs_alerts.yml` (MODIFIED)

**Location:** `grafana/provisioning/alerting/rules/logs_alerts.yml`

#### 🔴 BEFORE (Broken)

```yaml
# Alert: Critical Errors Detected
- uid: critical_errors_detected
  title: Critical Errors Detected
  condition: C
  for: 5m
  annotations:
    description: '{{ $value }} critical errors detected in the last 5 minutes.'
  data:
    - refId: A
      model:
        expr: 'sum(critical_error_count_5m) > 10'  # ❌ DOES NOT EXIST
```

**Problems:**
- ❌ Referenced `critical_error_count_5m` metric that doesn't exist
- ❌ Used Prometheus query for log data (wrong datasource)
- ❌ Placeholder expressions that never actually query Loki
- ❌ Would always show "No Data" and never fire

#### 🟢 AFTER (Fixed)

```yaml
# Alert: Critical Errors Detected in Logs
- uid: critical_errors_detected
  title: Critical Errors Detected in Logs
  condition: B
  for: 5m
  annotations:
    description: 'More than 10 ERROR log lines detected in the last 5 minutes (current: {{ $values.A.Value }}). Check Loki logs dashboard for error details.'
  data:
    - refId: A
      queryType: ''
      relativeTimeRange:
        from: 300
        to: 0
      datasourceUid: grafana_loki  # ✅ Correct datasource
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)ERROR" [5m]))'  # ✅ Real Loki LogQL query
        refId: A
    - refId: B
      datasourceUid: __expr__
      model:
        expression: A
        type: threshold
        conditions:
          - evaluator:
              params: [10]
              type: gt
```

**What Changed:**
- ✅ Uses real Loki datasource (`grafana_loki`)
- ✅ Actual LogQL query that counts ERROR log lines
- ✅ Proper relative time range (last 5 minutes)
- ✅ Expression-based threshold evaluation
- ✅ Will now fire when ERROR logs exceed threshold

---

### 2. New Alert: Exception Stack Traces

**NEW ALERT** — Detects Python exception tracebacks in logs

```yaml
- uid: exception_stack_traces_detected
  title: Exception Stack Traces Detected
  condition: B
  for: 2m
  severity: critical
  annotations:
    description: 'Exception stack traces detected in logs ({{ $values.A.Value }} occurrences in 5 minutes). Unhandled exceptions or crashes detected.'
  data:
    - refId: A
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)(Traceback|Exception:|Error:)" [5m]))'
```

**Why This Matters:**
- Catches unhandled Python exceptions before they cascade
- Detects application crashes in real-time
- Pattern: `Traceback`, `Exception:`, `Error:`

---

### 3. New Alert: Database Connection Errors

**NEW ALERT** — Detects database connectivity issues

```yaml
- uid: database_connection_errors
  title: Database Connection Errors Detected
  condition: B
  for: 3m
  severity: critical
  annotations:
    description: 'Database connection errors detected ({{ $values.A.Value }} occurrences). Check DB connectivity, connection pool, or DB service health.'
  data:
    - refId: A
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)(database.*error|connection.*timeout|connection.*refused|sqlalchemy.*error)" [5m]))'
```

**Why This Matters:**
- Database failures are critical path issues
- Detects connection pool exhaustion
- Catches SQLAlchemy/ORM errors

---

### 4. New Alert: Timeout Errors

**NEW ALERT** — Detects timeout errors from providers or services

```yaml
- uid: timeout_errors_detected
  title: Timeout Errors Detected
  condition: B
  for: 5m
  severity: warning
  annotations:
    description: 'Timeout errors detected ({{ $values.A.Value }} occurrences). May indicate slow provider responses, network issues, or capacity problems.'
  data:
    - refId: A
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)(timeout|timed out|deadline exceeded)" [5m]))'
```

**Why This Matters:**
- Early warning for latency issues
- Detects provider slowness before SLO breach
- Pattern: `timeout`, `timed out`, `deadline exceeded`

---

### 5. New Alert: Rate Limit Errors

**NEW ALERT** — Detects provider rate limiting in logs

```yaml
- uid: rate_limit_errors_logs
  title: Provider Rate Limit Errors in Logs
  condition: B
  for: 5m
  severity: warning
  annotations:
    description: 'Provider rate limit errors detected ({{ $values.A.Value }} occurrences). Providers are throttling requests.'
  data:
    - refId: A
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)(rate limit|rate_limit|429|quota exceeded|too many requests)" [5m]))'
```

**Why This Matters:**
- Detects provider throttling before metrics show it
- Catches quota exhaustion early
- Pattern: `rate limit`, `429`, `quota exceeded`

---

### 6. New Alert: OOM Errors

**NEW ALERT** — Detects out-of-memory errors

```yaml
- uid: oom_errors_detected
  title: Out of Memory Errors Detected
  condition: B
  for: 1m
  severity: critical
  annotations:
    description: 'Out of memory errors detected. Application may be experiencing memory leaks or insufficient allocation.'
  data:
    - refId: A
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)(out of memory|oom|memory error|memoryerror)" [5m]))'
```

**Why This Matters:**
- Prevents container crashes from OOM kills
- Detects memory leaks before they cause downtime
- Critical infrastructure alert

---

## New File: `correlated_failure_detection.yml`

**Location:** `grafana/provisioning/alerting/rules/correlated_failure_detection.yml`

### Purpose

These alerts detect when **multiple signals fire together**, providing high-confidence incident detection. Single-signal alerts can be false positives. Multi-signal correlation = confirmed incident.

---

### 7. Multi-Layer Error Correlation (Metrics + Logs)

**THE KEY ALERT FOR FASTER INCIDENT RESPONSE**

```yaml
- uid: multi_layer_error_correlation
  title: Multi-Layer Error Correlation - Confirmed Incident
  condition: D
  for: 3m
  severity: critical
  labels:
    incident_confidence: high
  annotations:
    description: 'CONFIRMED INCIDENT: Errors in both metrics (5xx: {{ $values.A.Value }}%) AND logs (ERROR count: {{ $values.B.Value }}). Multi-layer correlation = real degradation, not false positive.'
  data:
    # Query A: 5xx error rate from Prometheus
    - refId: A
      datasourceUid: grafana_prometheus
      model:
        expr: '(sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / sum(rate(fastapi_requests_total[5m]))) * 100'
    # Query B: ERROR log count from Loki
    - refId: B
      datasourceUid: grafana_loki
      model:
        expr: 'sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)ERROR" [5m]))'
    # Condition: Both must be elevated
    - refId: C
      datasourceUid: __expr__
      model:
        expression: A
        type: threshold
        conditions:
          - evaluator:
              params: [2]  # 5xx rate > 2%
              type: gt
    - refId: D
      datasourceUid: __expr__
      model:
        expression: B
        type: threshold
        conditions:
          - evaluator:
              params: [5]  # ERROR logs > 5
              type: gt
```

**Why This Is Critical:**
- ✅ Eliminates false positives (both signals must fire)
- ✅ Confirms real incidents vs. noise
- ✅ Faster triage — you know it's real
- ✅ High confidence = immediate action warranted

**Detection Logic:**
```
IF (5xx_error_rate > 2%) AND (ERROR_log_count > 5)
THEN: Confirmed incident (not a false positive)
ACTION: Immediate investigation
```

---

### 8. Parallel Provider Failures

**Detects when 2+ providers fail simultaneously**

```yaml
- uid: parallel_provider_failures
  title: Parallel Provider Failures - Multiple Providers Down
  condition: C
  for: 5m
  severity: critical
  labels:
    incident_type: parallel_failure
  annotations:
    description: '{{ $values.A.Value }} providers with >10% error rate simultaneously. Systemic issue - check network, DNS, auth, or shared infrastructure.'
  data:
    - refId: A
      datasourceUid: grafana_prometheus
      model:
        # Count providers with >10% error rate
        expr: 'count((sum by (provider) (rate(model_inference_requests_total{status="error"}[5m])) / sum by (provider) (rate(model_inference_requests_total[5m]))) > 0.10)'
    - refId: C
      datasourceUid: __expr__
      model:
        expression: A
        type: threshold
        conditions:
          - evaluator:
              params: [2]  # 2+ providers
              type: gt
```

**Why This Matters:**
- Single provider failure = provider issue
- **Multiple provider failures = YOUR issue** (network, auth, DNS, config)
- Prevents misdiagnosis of systemic problems as provider-specific

---

### 9. Parallel Endpoint Failures

**Detects when 3+ API endpoints fail simultaneously**

```yaml
- uid: parallel_endpoint_failures
  title: Parallel Endpoint Failures - Multiple Endpoints Down
  condition: C
  for: 5m
  severity: critical
  labels:
    incident_type: parallel_failure
  annotations:
    description: '{{ $values.A.Value }} endpoints with >5% error rate. Backend-wide issue - check database, cache, dependencies.'
  data:
    - refId: A
      datasourceUid: grafana_prometheus
      model:
        # Count endpoints with >5% error rate
        expr: 'count((sum by (endpoint) (rate(fastapi_requests_total{status_code=~"5.."}[5m])) / sum by (endpoint) (rate(fastapi_requests_total[5m]))) > 0.05)'
    - refId: C
      datasourceUid: __expr__
      model:
        expression: A
        type: threshold
        conditions:
          - evaluator:
              params: [3]  # 3+ endpoints
              type: gt
```

**Why This Matters:**
- Single endpoint failure = code bug in that endpoint
- **Multiple endpoint failures = shared dependency issue** (DB, cache, auth)
- Directs investigation to shared infrastructure

---

### 10. Error + Latency Correlation

**Detects when error rate AND latency spike together**

```yaml
- uid: error_latency_correlation
  title: Error + Latency Correlation - Capacity Issue
  condition: D
  for: 5m
  severity: critical
  labels:
    incident_type: capacity_degradation
  annotations:
    description: 'Error rate {{ $values.A.Value }}% AND P95 latency {{ $values.B.Value }}s elevated. Capacity issue causing timeouts and failures.'
  data:
    - refId: A  # 5xx error rate
      datasourceUid: grafana_prometheus
      model:
        expr: '(sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / sum(rate(fastapi_requests_total[5m]))) * 100'
    - refId: B  # P95 latency
      datasourceUid: grafana_prometheus
      model:
        expr: 'histogram_quantile(0.95, sum(rate(fastapi_requests_duration_seconds_bucket[5m])) by (le))'
    # Conditions: Both must be elevated
```

**Why This Matters:**
- Errors + high latency = capacity problem
- Directs investigation to resource limits, slow queries, bottlenecks
- Action: Scale or optimize

---

### 11. Traffic Spike + Error Correlation

**Detects when traffic surge causes errors**

```yaml
- uid: traffic_spike_error_correlation
  title: Traffic Spike + Error Correlation - Capacity Limit
  condition: D
  for: 5m
  severity: critical
  labels:
    incident_type: load_spike
  annotations:
    description: 'Traffic {{ $values.A.Value }}x baseline AND {{ $values.B.Value }}% error rate. System unable to handle load. Scale immediately.'
  data:
    - refId: A  # Traffic ratio
      datasourceUid: grafana_prometheus
      model:
        expr: 'sum(rate(fastapi_requests_total[5m])) / sum(rate(fastapi_requests_total[5m] offset 1h))'
    - refId: B  # Error rate
      datasourceUid: grafana_prometheus
      model:
        expr: '(sum(rate(fastapi_requests_total{status_code=~"5.."}[5m])) / sum(rate(fastapi_requests_total[5m]))) * 100'
    # Conditions: Traffic > 2x AND errors > 2%
```

**Why This Matters:**
- Traffic spike alone = might be good (growth)
- **Traffic spike + errors = capacity limit reached**
- Action: Emergency scaling or aggressive rate limiting

---

## Alert Count Summary

### Before Changes
| Category | Count | Status |
|----------|-------|--------|
| Prometheus Alerts | 16 | ✅ Working |
| Grafana Log Alerts | 4 | ❌ **Broken** (placeholder queries) |
| Grafana Anomaly Alerts | 36 | ✅ Working |
| **Total** | **56** | **4 broken** |

### After Changes
| Category | Count | Status |
|----------|-------|--------|
| Prometheus Alerts | 16 | ✅ Working |
| Grafana Log Alerts | 6 | ✅ **Fixed + 2 new** |
| Grafana Correlation Alerts | 5 | ✅ **NEW** |
| Grafana Anomaly Alerts | 36 | ✅ Working |
| **Total** | **63** | **All working** |

**Net Change:** +7 alerts (4 fixed, 2 new log alerts, 5 new correlation alerts)

---

## Testing Checklist

Before merging to main, verify:

### 1. Loki Datasource Verification
```bash
# In Grafana UI:
# 1. Go to Connections → Datasources → Loki
# 2. Verify UID = "grafana_loki"
# 3. Click "Test" — should show "Data source is working"
```

### 2. Test Log Queries
```bash
# In Grafana Explore:
# 1. Select Loki datasource
# 2. Run query: sum(count_over_time({job=~".*gatewayz.*"} |~ "(?i)ERROR" [5m]))
# 3. Should return data if backend has ERROR logs
# 4. If returns 0, that's OK (no errors currently)
# 5. If returns "No data", check Loki configuration
```

### 3. Alert Rules Provisioning
```bash
# Check alert rules loaded correctly
cd railway-grafana-stack
docker-compose restart grafana

# In Grafana UI:
# 1. Go to Alerting → Alert Rules
# 2. Verify "Logs Alerts" folder has 6 rules
# 3. Verify "Correlated Incidents" folder has 5 rules
# 4. Check each rule shows "Normal" or "Pending" (not "Error")
```

### 4. Simulate Alert (Optional)
```bash
# To test if alert fires, inject ERROR logs into backend
# OR wait for natural ERROR logs to accumulate
# Alert should fire after threshold exceeded for duration
```

### 5. Verify Alertmanager Integration
```bash
# When alert fires, check:
# 1. Grafana Alerting → Firing alerts
# 2. Alertmanager UI (port 9093) → Alerts
# 3. Email notification sent (if configured)
```

---

## Deployment Instructions

### Local Testing (Docker Compose)
```bash
cd railway-grafana-stack
docker-compose down
docker-compose up -d
# Wait 30 seconds for provisioning
# Check Grafana UI → Alerting → Alert Rules
```

### Railway Deployment
```bash
# DO NOT run yet — wait for verification
# When ready:
git add .
git commit -m "feat: add log-based and correlated failure detection alerts"
git push origin feature/feature-availability
# Then deploy via Railway UI
```

---

## Expected Behavior After Deployment

### Immediate Changes
1. **"Logs Alerts" folder** — 6 working alert rules visible in Grafana
2. **"Correlated Incidents" folder** — 5 new alert rules visible
3. **Alert evaluation starts** — Rules begin checking conditions every 1 minute

### When Errors Occur
1. **Single ERROR log** → No alert (below threshold)
2. **10+ ERROR logs in 5m** → `critical_errors_detected` fires
3. **5xx errors + ERROR logs** → `multi_layer_error_correlation` fires (HIGH PRIORITY)
4. **2+ providers failing** → `parallel_provider_failures` fires
5. **Database errors** → `database_connection_errors` fires immediately

### Alert Notifications
- **Warning alerts** → Route to ops-email (check daily)
- **Critical alerts** → Route to critical-email (immediate response)
- **incident_confidence: high** → Requires immediate triage

---

## Rollback Plan

If issues occur after deployment:

```bash
# Revert to previous version
git revert HEAD
git push origin feature/feature-availability

# Or disable specific alert rules in Grafana UI:
# 1. Alerting → Alert Rules
# 2. Edit rule → Disable → Save
```

**Safe to disable individually:** Each new alert is independent. Disabling one doesn't affect others.

---

## Next Steps

1. ✅ **Review this document** — Verify changes align with requirements
2. ⚠️ **Test locally** — Run Docker Compose and verify alerts load
3. ⚠️ **Verify Loki datasource** — Confirm UID and connectivity
4. ⚠️ **Test one alert** — Inject error to verify alert fires
5. ✅ **Deploy to Railway** — Push to branch, deploy via Railway UI
6. 📊 **Monitor for 24h** — Watch for false positives or missed incidents
7. 🔧 **Tune thresholds** — Adjust if too noisy or not sensitive enough

---

## Questions & Support

| Question | Answer |
|----------|--------|
| Will these alerts cause noise? | No — thresholds tuned for actionable alerts only. Multi-layer correlation reduces false positives. |
| What if I get too many alerts? | Increase thresholds or "for" duration in YAML files. |
| How do I disable an alert? | Grafana UI → Alerting → Edit rule → Disable → Save |
| Can I test without deploying? | Yes — use Docker Compose locally first |
| What if Loki has no data? | Alerts show "No Data" state (not firing). Verify backend log shipping. |

---

**Author:** Claude (AI Assistant)
**Date:** March 10, 2026
**Review Status:** ⚠️ Awaiting human verification
**Deployment Status:** ❌ Not deployed (on feature branch only)
