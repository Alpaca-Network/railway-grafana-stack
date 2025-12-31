# 🚨 GatewayZ Alert System Guide

**Status:** ✅ Production Ready
**Last Updated:** December 31, 2025
**Alert Rules:** 16 total (4 categories)
**Notification Channels:** Email + Grafana UI

---

## 📋 Quick Start

### 1. Configure SMTP for Email Notifications

Set these environment variables in your `.env` file or Railway environment:

```bash
GF_SMTP_HOST=smtp.gmail.com:587
GF_SMTP_USER=your-email@gmail.com
GF_SMTP_PASSWORD=your-app-password  # Use Gmail app password, not regular password
GF_SMTP_FROM_ADDRESS=grafana@gatewayz.ai
GF_SMTP_FROM_NAME=GatewayZ Monitoring
```

### 2. Configure Email Recipients

Update the email addresses in `grafana/provisioning/alerting/contact_points.yml`:

```yaml
# Primary operations team
addresses: alerts@gatewayz.ai, ops@gatewayz.ai

# Critical alerts only (on-call)
addresses: on-call@gatewayz.ai

# Development team
addresses: dev@gatewayz.ai
```

### 3. Restart Grafana

```bash
docker-compose restart grafana
```

### 4. Verify Alert Provisioning

Visit **Grafana → Alerting → Alert Rules** and confirm all 16 rules appear.

---

## 🎯 Alert Categories

### 1. Model Alerts (4 rules)

Monitor individual model performance across all providers.

| Alert Name | Threshold | Severity | Duration |
|-----------|-----------|----------|----------|
| **Model Health Score Low** | health_score < 80% | ⚠️ Warning | 5 min |
| **Model Error Rate High** | error_rate > 5% (warn), > 10% (critical) | ⚠️ Warning | 5 min |
| **Model Latency High** | avg_latency > 500ms | ⚠️ Warning | 10 min |
| **Model Availability Low** | success_rate < 95% | ⚠️ Warning | 5 min |

**Notify:** `ops-email` (primary team)

**Example Scenario:**
- GPT-4o model health drops to 75% due to provider issues
- Alert fires after 5 minutes of sustained degradation
- Email sent to ops team with model name, current health score, runbook link

---

### 2. Backend Alerts (4 rules)

Monitor overall system health, circuit breakers, and provider availability.

| Alert Name | Threshold | Severity | Duration |
|-----------|-----------|----------|----------|
| **System Health Degraded** | avg_health_score < 80% | ⚠️ Warning | 5 min |
| **Circuit Breaker Open** | state == "open" | 🔴 Critical | Immediate |
| **Backend Error Rate High** | error_rate > 5% | ⚠️ Warning | 5 min |
| **Provider Availability Low** | availability < 95% | ⚠️ Warning | 10 min |

**Notify:**
- Critical alerts → `critical-email` (on-call team, immediate)
- Warning alerts → `ops-email` (5 min grouping)

**Example Scenario:**
- Circuit breaker opens for a provider
- Critical alert fires immediately
- On-call team receives urgent notification
- System automatically flags degraded service in dashboards

---

### 3. General Alerts (4 rules)

Monitor system-wide metrics, costs, and traffic anomalies.

| Alert Name | Threshold | Severity | Duration |
|-----------|-----------|----------|----------|
| **Provider Availability Critical** | availability < 90% | 🔴 Critical | 5 min |
| **Cost Anomaly Detected** | daily_cost > 110% of 7d avg | ⚠️ Warning | 5 min |
| **Budget Threshold Warning** | 7d_cost > $50,000 | ⚠️ Warning | 5 min |
| **High Request Volume** | req/sec > 200% of baseline | ⚠️ Warning | 10 min |

**Notify:** `ops-email` (10 min grouping for non-critical)

**Example Scenario:**
- Daily cost spikes to $60,000 (110% above weekly average)
- Cost anomaly alert fires
- Operations team investigates expensive model usage
- Can implement cost controls or alert on usage spikes

---

### 4. Logs Alerts (4 rules)

Monitor error logs, latency degradation, and system anomalies.

| Alert Name | Threshold | Severity | Duration |
|-----------|-----------|----------|----------|
| **Critical Errors Detected** | critical_count > 10 | 🔴 Critical | Immediate |
| **Error Rate Spike** | rate_increase > 50% vs 1h ago | ⚠️ Warning | 5 min |
| **Latency Degradation** | latency_increase > 50% vs 1h ago | ⚠️ Warning | 10 min |
| **Anomaly Count High** | anomaly_count > 5 | 🔴 Critical | Immediate |

**Notify:**
- Critical alerts → `critical-email` (immediate)
- Warning alerts → `ops-email` (5 min grouping)

**Example Scenario:**
- 15 critical errors detected in 5 minutes
- Critical alert fires immediately
- On-call team gets notification with error context
- Can link to Logs & Diagnostics dashboard for investigation

---

## 📊 Alert Routing & Notification Policy

### Alert Grouping Strategy

**Critical Alerts:** No grouping (sent immediately)
```yaml
groupWait: 0s
repeatInterval: 15m
```

**Warning Alerts:** Group for 5 minutes
```yaml
groupWait: 5m
groupInterval: 5m
repeatInterval: 30m
```

**Info Alerts:** Group for 30 minutes
```yaml
groupWait: 30m
groupInterval: 30m
repeatInterval: 1h
```

### Routing Rules

1. **Critical alerts** → `critical-email` immediately
2. **Model alerts** → `ops-email` (group by model)
3. **Backend alerts** → `ops-email` (group by component)
4. **General alerts** → `ops-email` (group globally)
5. **Logs alerts** → `ops-email` (group by service)

---

## ⚙️ SMTP Configuration

### Gmail (Recommended)

1. Enable 2FA on your Gmail account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use app password (not your regular password):

```bash
GF_SMTP_USER=your-email@gmail.com
GF_SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-character app password
GF_SMTP_HOST=smtp.gmail.com:587
```

### SendGrid

```bash
GF_SMTP_HOST=smtp.sendgrid.net:587
GF_SMTP_USER=apikey
GF_SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### AWS SES

```bash
GF_SMTP_HOST=email-smtp.region.amazonaws.com:587
GF_SMTP_USER=AKIA...  # SMTP username
GF_SMTP_PASSWORD=...  # SMTP password
```

### Test Email Delivery

In Grafana UI:
1. Go to **Administration → Settings → SMTP**
2. Click **Send Test Email**
3. Check inbox for test message

---

## 🧪 Testing Alerts

### Method 1: Manual Threshold Trigger

1. Go to **Alerting → Alert Rules**
2. Find the alert you want to test
3. Click **Edit** → Modify threshold to trigger condition
4. Save and wait for alert to fire
5. Revert threshold to original value

### Method 2: Synthetic Alert

Create a temporary alert that always fires:

```yaml
- alert: TestAlert
  expr: 'up == 1'  # Always evaluates to true
  for: 0m
  annotations:
    summary: "Test alert - safe to ignore"
  labels:
    severity: info
    category: general
```

### Method 3: API Endpoint Manipulation

Temporarily return data that triggers alert thresholds:

```bash
# Simulate high error rate
curl -X POST http://api.gatewayz.ai/api/monitoring/error-rates \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"error_rate": 15}'  # > 5% threshold
```

### Verification Checklist

- [ ] Alert rule is visible in Grafana UI
- [ ] Contact point is configured with correct email address
- [ ] Notification policy routes alert to correct email
- [ ] SMTP credentials are valid
- [ ] Test email is received in inbox
- [ ] Alert fires when threshold is breached
- [ ] Email contains alert name, severity, value, and runbook link
- [ ] Alert resolves when threshold returns to normal

---

## 📈 Alert Response Runbooks

### Model Health Alert Runbook

**When:** Model health score < 80% for 5+ minutes

**Steps:**
1. Check [Model Performance Analytics](d/model-performance-v1) dashboard
2. Identify which model has degraded health
3. Review [Logs & Diagnostics](d/logs-monitoring-v1) for error patterns
4. Check provider status (model may depend on unavailable provider)
5. Review recent code deployments or model updates
6. If temporary, monitor recovery; if persistent, escalate to platform team

**Commands:**
```bash
# Check model-specific errors
curl -H "Authorization: Bearer $API_KEY" \
  "https://api.gatewayz.ai/api/monitoring/errors/gpt-4o"

# Check provider availability
curl -H "Authorization: Bearer $API_KEY" \
  "https://api.gatewayz.ai/api/monitoring/health"
```

---

### Circuit Breaker Alert Runbook

**When:** Circuit breaker opens immediately

**Steps:**
1. Go to [Backend Health](d/backend-health-v1) dashboard
2. Check Circuit Breaker Status table
3. Identify which service/provider has opened circuit
4. Check recent metrics:
   - Error rate spike?
   - Latency spike?
   - Provider unavailability?
5. Take action:
   - If provider issue: wait for recovery, monitor status
   - If backend issue: check application logs, restart service
6. Monitor circuit breaker state until it closes

---

### Cost Anomaly Alert Runbook

**When:** Daily cost > 110% of 7-day average

**Steps:**
1. Check [Model Performance Analytics](d/model-performance-v1)
2. Look at Cost per Request panel - which models are most expensive?
3. Check Request Volume panel - which models have highest usage?
4. Investigate cost per request:
   - Input tokens higher than usual?
   - Output tokens higher than usual?
   - More expensive models used instead of cheaper ones?
5. Actions:
   - Implement usage throttling if needed
   - Switch to more cost-effective models
   - Alert development team to optimize prompts
6. Set budget threshold in alert if recurring

---

### Critical Errors Alert Runbook

**When:** > 10 critical errors in 5 minutes

**Steps:**
1. Go to [Logs & Diagnostics](d/logs-monitoring-v1)
2. Check "Critical Errors" stat card and alerts table
3. Look for common error patterns:
   - Same service failing?
   - Same error message repeated?
   - Specific provider impacted?
4. Check relevant dashboard:
   - If model-related: Model Performance Analytics
   - If provider-related: Gateway Comparison
   - If backend: Backend Health
5. Escalate if:
   - Multiple services affected
   - Error rate continues to climb
   - Unable to identify root cause

---

## 🔧 Customizing Alerts

### Change Alert Threshold

Edit the corresponding YAML file in `grafana/provisioning/alerting/rules/`:

```yaml
- alert: ModelHealthScoreLow
  expr: 'avg(health_score) < 80'  # Change 80 to your threshold
```

Then restart Grafana:

```bash
docker-compose restart grafana
```

### Add New Alert

Create new rule in appropriate category file:

```yaml
- alert: CustomAlert
  expr: 'some_metric > threshold'
  for: 5m
  annotations:
    summary: "Custom alert description"
  labels:
    severity: warning
    category: model
```

### Change Email Recipients

Edit `grafana/provisioning/alerting/contact_points.yml`:

```yaml
addresses: newemail@company.com, anotheronecall@company.com
```

### Disable Alert

Comment out the alert rule:

```yaml
# - alert: ModelHealthScoreLow
#   expr: 'avg(health_score) < 80'
```

---

## 🐛 Troubleshooting

### Alerts Not Firing

**Check 1: Alert rule provisioning**
```bash
# View Grafana logs
docker-compose logs grafana | grep -i "alert"

# Check if rules loaded
curl http://localhost:3000/api/ruler/grafana/rules/model_alerts
```

**Check 2: Data source connectivity**
- Verify `/api/monitoring/*` endpoints are responding
- Check Prometheus scrape targets (http://localhost:9090/targets)

**Check 3: Alert state**
- In Grafana, go to **Alerting → Alert Rules**
- Check if alert shows "Pending" (will fire after `for:` duration)
- Check if alert shows "Error" (PromQL syntax issue)

### Emails Not Being Sent

**Check 1: SMTP configuration**
```bash
# Verify SMTP in Grafana
curl http://localhost:3000/api/admin/settings | jq '.smtp'

# Test SMTP manually
telnet smtp.gmail.com 587
```

**Check 2: Contact point configuration**
- Go to **Alerting → Contact Points**
- Verify email addresses are correct
- Click "Test" to send test email

**Check 3: Notification policy**
- Go to **Alerting → Notification Policies**
- Verify routes are configured correctly
- Check if alert matches any route matchers

### Alert Firing Too Frequently

- Increase the `for:` duration (5m → 10m)
- Increase groupWait to batch notifications
- Check if threshold is set too low

### Alert Never Resolves

- Check if expr continues to evaluate true
- Verify metric is returning expected values
- Check `repeat_interval` - alert will repeat even if not resolved

---

## 📚 References

- **Grafana Alerting Docs:** https://grafana.com/docs/grafana/latest/alerting/
- **Alert Rule Syntax:** https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- **Notification Policies:** https://grafana.com/docs/grafana/latest/alerting/manage-notifications/create-notification-policy/
- **SMTP Configuration:** https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/configure-smtp/

---

## ✅ Deployment Checklist

- [ ] All 6 provisioning files created in `grafana/provisioning/alerting/`
- [ ] SMTP environment variables configured (GF_SMTP_*)
- [ ] Contact points configured with correct email addresses
- [ ] Notification policies routes configured
- [ ] All 16 alert rules visible in Grafana UI
- [ ] Test email sent and received successfully
- [ ] Model alerts tested (manually trigger high error rate)
- [ ] Backend alerts tested (check circuit breaker alert)
- [ ] General alerts tested (cost anomaly)
- [ ] Logs alerts tested (critical error count)
- [ ] Email contains all required information:
  - Alert name
  - Severity level
  - Current metric value
  - Runbook URL
  - Dashboard link

---

**Status:** ✅ Complete and Ready for Production
**Last Verified:** December 31, 2025
**Support:** Refer to runbooks for each alert category
