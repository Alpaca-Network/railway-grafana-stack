# Alerting Implementation Plan

## Current State Analysis

### ✅ What We Have
1. **Alert Rules Defined**: `prometheus/alert.rules.yml` with 5 groups, 25+ alert rules
   - Performance alerts (API, latency, model inference)
   - Performance trends (degradation detection)
   - Model health alerts
   - Redis alerts
   - Infrastructure alerts (SLO, targets, traffic)

2. **Rule Files Referenced**: `prom.yml` includes `alert.rules.yml` in `rule_files` section

### ❌ What's Missing
1. **Alerting Configuration**: No `alerting:` section in `prom.yml`
2. **Alertmanager**: Not deployed (required for alert routing/notification)
3. **Grafana Alerting**: Not configured to read Prometheus alerts
4. **Alert State Not Visible**: Prometheus UI shows alerts but they're not firing/routing

---

## Problem: Why Alerts Don't Show in Prometheus UI

**Prometheus Alert States**:
- **Inactive**: Alert condition not met
- **Pending**: Alert condition met, waiting for `for` duration
- **Firing**: Alert condition met for duration, sent to Alertmanager

**Current Issue**: Alerts are evaluated but not sent anywhere because:
1. No `alerting:` section in Prometheus config
2. No Alertmanager endpoint configured
3. Alerts show as "inactive" or "pending" but never "firing" to destinations

---

## Solution Options

### Option 1: Full Alertmanager Setup (Recommended for Production)
**Deploy Alertmanager service on Railway**

**Pros**:
- Proper alert routing and grouping
- Multiple notification channels (email, Slack, PagerDuty, webhook)
- Alert deduplication and silencing
- Alert inhibition (suppress dependent alerts)
- Industry standard approach

**Cons**:
- Additional service to deploy/maintain
- More complexity
- Additional cost (~$5-10/month on Railway)

**Components**:
- Alertmanager service (Docker container)
- Configuration for routing rules
- Notification channel setup (email, Slack, etc.)
- Prometheus config update to point to Alertmanager

---

### Option 2: Direct Grafana Alerting (Simpler, Immediate)
**Use Grafana's built-in alerting with Prometheus as datasource**

**Pros**:
- No additional services needed
- Grafana already deployed
- Easier to manage (UI-based configuration)
- Alert annotations visible in dashboards
- Built-in notification channels

**Cons**:
- Not using Prometheus alert rules (need to recreate in Grafana)
- Less flexible than Alertmanager
- Tighter coupling to Grafana

**Components**:
- Grafana contact points (email, Slack, etc.)
- Grafana notification policies
- Alert rules per dashboard panel
- Prometheus datasource already configured

---

### Option 3: Hybrid Approach (Best of Both Worlds)
**Use both Alertmanager AND Grafana Alerting**

**Pros**:
- Prometheus alerts route through Alertmanager (proper handling)
- Grafana provides UI for alert management
- Grafana can also have its own alert rules
- Maximum flexibility

**Cons**:
- Most complex setup
- Potential for duplicate alerts
- Need to coordinate both systems

---

## Recommended Approach

### Phase 1: Enable Prometheus Alerts (Quick Win) ✅
**Timeline**: 30 minutes

1. **Add Alerting Configuration to Prometheus**
   - Add `alerting:` section to `prom.yml`
   - Point to Alertmanager endpoint (placeholder for now)
   - Alerts will show proper state in Prometheus UI

2. **Benefits**:
   - Alerts visible in Prometheus UI with firing state
   - Can monitor alert state without notifications
   - Foundation for adding Alertmanager later

---

### Phase 2: Deploy Alertmanager (Production-Ready) 🚀
**Timeline**: 1-2 hours

1. **Create Alertmanager Service**
   - Docker container on Railway
   - Configuration file with routing rules
   - Setup notification receivers (email first)

2. **Update Prometheus Config**
   - Point `alerting:` to Alertmanager Railway internal URL
   - Configure alert relabeling if needed

3. **Benefits**:
   - Alerts sent to email/Slack/etc.
   - Proper alert management (grouping, silencing)
   - Production-grade alerting

---

### Phase 3: Grafana Dashboard Alerts (UI Enhancement) 📊
**Timeline**: 1-2 hours

1. **Create Alert Rules in Grafana**
   - One alert per critical panel
   - Use same thresholds as Prometheus rules
   - Configure contact points (email, Slack)

2. **Setup Per-Dashboard Alerts**:
   - **Model Performance**: High latency, low health score
   - **Gateway Comparison**: Provider errors, slow response
   - **Backend Services**: Redis down, high memory
   - **Executive Overview**: SLO breach, traffic spike
   - **Mimir Dashboard**: Ingestion failures, query errors

3. **Benefits**:
   - Alert annotations visible on dashboard panels
   - UI-based alert management
   - Better integration with dashboard workflows

---

## Implementation Details

### Phase 1: Enable Prometheus Alerts (DOING THIS NOW)

#### Step 1.1: Add Alerting Section to Prometheus Config
Edit `prometheus/prom.yml`:
```yaml
# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            # Placeholder - will be replaced when Alertmanager is deployed
            # For now, this enables alert state tracking in Prometheus UI
            - 'alertmanager.railway.internal:9093'
      timeout: 10s
      api_version: v2
```

#### Step 1.2: Verify Alerts Load
After deployment:
1. Visit Prometheus UI → Alerts
2. Should see all 25+ alert rules
3. State will show: Inactive, Pending, or Firing
4. Click alert for details (query, duration, labels)

#### Step 1.3: Update Alert Rules with Better Annotations
Add dashboard links to existing alerts:
- Replace `localhost:3000` with `${GRAFANA_URL}` variable
- Add runbook_url for common issues
- Add tags for filtering

---

### Phase 2: Deploy Alertmanager (NEXT SESSION)

#### Step 2.1: Create Alertmanager Configuration
File: `railway-grafana-stack/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  # Email config (using Gmail as example)
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@gatewayz.ai'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_require_tls: true

# Route tree - how alerts are routed
route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  
  routes:
    # Critical alerts go to email immediately
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      
    # Warning alerts batched every 5 minutes
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_interval: 5m

# Notification receivers
receivers:
  - name: 'default'
    email_configs:
      - to: 'manjeshprasad21@gmail.com'
        headers:
          Subject: 'GatewayZ Alert: {{ .GroupLabels.alertname }}'
        
  - name: 'critical-alerts'
    email_configs:
      - to: 'manjeshprasad21@gmail.com'
        headers:
          Subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
          
  - name: 'warning-alerts'
    email_configs:
      - to: 'manjeshprasad21@gmail.com'
        headers:
          Subject: '⚠️  WARNING: {{ .GroupLabels.alertname }}'

# Inhibition rules - suppress alerts
inhibit_rules:
  # If Redis is down, don't alert on cache hit rate
  - source_match:
      alertname: 'RedisDown'
    target_match:
      component: 'redis'
    equal: ['instance']
```

#### Step 2.2: Create Alertmanager Dockerfile
File: `railway-grafana-stack/alertmanager/Dockerfile`

```dockerfile
FROM prom/alertmanager:v0.27.0

USER root

# Copy configuration
COPY alertmanager.yml /etc/alertmanager/alertmanager.yml

# Create data directory
RUN mkdir -p /alertmanager && chmod 0777 /alertmanager

EXPOSE 9093

CMD ["--config.file=/etc/alertmanager/alertmanager.yml", \
     "--storage.path=/alertmanager", \
     "--web.listen-address=:9093"]
```

#### Step 2.3: Deploy to Railway
1. Add Alertmanager service to Railway
2. Set environment variables for email credentials
3. Update Prometheus config to use real Alertmanager URL
4. Test alert firing

---

### Phase 3: Grafana Dashboard Alerts

#### Step 3.1: Configure Grafana Contact Points
In Grafana UI:
1. Go to: Alerting → Contact points
2. Add contact point:
   - Name: "Email - Critical"
   - Type: Email
   - Addresses: manjeshprasad21@gmail.com

#### Step 3.2: Create Notification Policies
1. Go to: Alerting → Notification policies
2. Create policy:
   - Match labels: severity=critical
   - Contact point: Email - Critical
   - Group by: alertname
   - Repeat interval: 4h

#### Step 3.3: Add Alert Rules to Dashboards

**Example: Model Performance Dashboard**
For each critical panel, add alert:

1. Edit panel → Alert tab
2. Create alert rule:
   - Name: "High Model Latency"
   - Query: Same as panel query
   - Condition: P95 > 5s
   - Evaluate every: 1m
   - For: 5m
   - Labels: severity=warning, dashboard=model-performance
   - Annotations: Links to runbook

Repeat for:
- Low health score alert
- High error rate alert
- Provider-specific alerts

---

## Alert Rules Per Dashboard (Phase 3 Details)

### Dashboard 1: Model Performance Analytics
**Critical Alerts**:
1. **High Model Latency**
   - Condition: P95 > 5s for 5m
   - Query: `histogram_quantile(0.95, sum(rate(model_inference_duration_seconds_bucket[5m])) by (le))`
   
2. **Low Model Health Score**
   - Condition: < 20% for 5m
   - Query: `(sum(rate(model_inference_requests_total{status="success"}[10m])) / sum(rate(model_inference_requests_total[10m]))) * 100`

3. **High Model Error Rate**
   - Condition: > 15% for 3m
   - Query: `sum(rate(model_inference_requests_total{status="error"}[5m])) / sum(rate(model_inference_requests_total[5m]))`

---

### Dashboard 2: Gateway Comparison
**Critical Alerts**:
1. **Provider Error Spike**
   - Condition: Error rate > 20% for provider
   - Query: Per-provider error rate

2. **Slow Provider Response**
   - Condition: P95 > 4s for provider
   - Query: Per-provider latency

---

### Dashboard 3: Backend Services
**Critical Alerts**:
1. **Redis Down**
   - Condition: redis_up == 0 for 1m
   - Immediate notification

2. **High Memory Usage**
   - Condition: > 90% for 2m
   - Critical threshold

3. **Low Cache Hit Rate**
   - Condition: < 50% for 10m
   - Warning level

---

### Dashboard 4: Executive Overview
**SLO Alerts**:
1. **Availability SLO Breach**
   - Condition: < 99.5% availability over 1h
   - Critical alert

2. **Latency SLO Breach**
   - Condition: P95 > 500ms over 1h
   - Warning alert

3. **Traffic Spike**
   - Condition: 2x baseline traffic
   - Warning level

---

### Dashboard 5: Mimir Monitoring
**Operational Alerts**:
1. **Mimir Ingestion Failure**
   - Condition: No samples ingested for 5m
   - Critical alert

2. **High Query Latency**
   - Condition: P99 > 1s
   - Warning alert

3. **Storage Issues**
   - Condition: Disk usage > 80%
   - Warning alert

---

## Testing Plan

### Phase 1 Testing (Prometheus UI)
1. Deploy updated Prometheus config
2. Visit: `https://prometheus-{project}.railway.app/alerts`
3. Verify all 25+ alerts visible
4. Trigger test alert (manually set low threshold)
5. Confirm state changes: Inactive → Pending → Firing

### Phase 2 Testing (Alertmanager)
1. Deploy Alertmanager service
2. Trigger test alert in Prometheus
3. Check Alertmanager UI: `https://alertmanager-{project}.railway.app`
4. Verify email received
5. Test silencing/inhibition

### Phase 3 Testing (Grafana)
1. Create test alert rule in Grafana
2. Set low threshold to trigger immediately
3. Verify alert shows on dashboard panel
4. Check notification received
5. Test muting/snoozing

---

## Documentation Cleanup

### Create `/docs` Directory Structure
```
railway-grafana-stack/
├── docs/
│   ├── setup/
│   │   ├── NEXT_STEPS.md
│   │   ├── QUICK_REFERENCE.md
│   │   ├── SETUP_COMPLETE.md
│   │   └── QUICK_START_PERCENTILE_FIX.md
│   ├── troubleshooting/
│   │   ├── REMOTE_WRITE_DEBUG.md
│   │   ├── PROMETHEUS_MIMIR_CONNECTION_FIXES.md
│   │   ├── DATA_FLOW_VERIFICATION.md
│   │   └── RAILWAY_QUICK_FIX.md
│   ├── architecture/
│   │   ├── MIMIR.md
│   │   ├── PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md
│   │   ├── RAILWAY_MIMIR_DEPLOYMENT.md
│   │   └── AGENTS.md
│   ├── monitoring/
│   │   ├── DASHBOARDS_USING_PERCENTILE_METRICS.md
│   │   ├── FOUR_GOLDEN_SIGNALS_AUDIT.md
│   │   ├── PERCENTILE_METRICS_FIX.md
│   │   └── PROMETHEUS_SCRAPING_AUDIT.md
│   ├── changes/
│   │   ├── BRANCH_CHANGES_SUMMARY.md
│   │   ├── SESSION_COMPLETE_SUMMARY.md
│   │   ├── BACKEND_SERVICES_FIX_SUMMARY.md
│   │   ├── BACKEND_SERVICES_INVESTIGATION.md
│   │   └── DOCUMENTATION_UPDATE_COMPLETE.md
│   ├── development/
│   │   ├── FUTURE_DEVELOPMENT_GUIDELINES.md
│   │   └── CLAUDE.md
│   └── README.md (index of all docs)
├── README.md (main project README)
└── ... (existing files)
```

### Update README with Documentation Index
Create master index pointing to organized docs.

---

## Timeline Summary

| Phase | Time | Deliverables |
|-------|------|--------------|
| **Phase 1** (Now) | 30 min | Prometheus alerting config, alerts visible in UI |
| **Doc Cleanup** (Now) | 30 min | Organized docs/ directory, updated references |
| **Phase 2** (Next) | 2 hours | Alertmanager deployed, email notifications working |
| **Phase 3** (Next) | 2 hours | Grafana alerts per dashboard, UI-based management |

**Total**: ~5 hours for complete alerting system

---

## Immediate Actions (This Session)

1. ✅ Add `alerting:` section to Prometheus config
2. ✅ Create docs/ directory structure
3. ✅ Move all .md files to appropriate subdirectories
4. ✅ Update references in moved files
5. ✅ Create docs/README.md index
6. ✅ Test Prometheus deployment with alerting enabled
7. ✅ Verify alerts show in Prometheus UI

**Next Session**:
- Deploy Alertmanager
- Setup email notifications
- Create Grafana alert rules per dashboard

---

**Last Updated**: January 25, 2026  
**Status**: Plan created, ready for implementation
