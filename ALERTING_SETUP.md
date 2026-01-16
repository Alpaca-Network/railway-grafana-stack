# GatewayZ Alerting Setup Guide

## 📧 Email Alert Configuration

This guide helps you configure email alerts for critical system events, including when the overall health score drops below 20%.

---

## Prerequisites

To send email alerts, you need:
1. **Gmail Account** (or any SMTP-compatible email service)
2. **App Password** (required if using Gmail with 2FA)

---

## Setting Up Gmail App Password

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### Step 2: Create App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter name: `GatewayZ Alertmanager`
5. Click **Generate**
6. **Copy the 16-character password** (you'll need this)

---

## Configuration Steps

### Local Development (Docker Compose)

1. **Create `.env` file** in `railway-grafana-stack/` directory:

```bash
# Email Configuration for Alertmanager
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

2. **Start the stack**:

```bash
cd railway-grafana-stack
docker-compose up -d
```

3. **Verify Alertmanager is running**:

```bash
# Check logs
docker-compose logs alertmanager

# Access UI
open http://localhost:9093
```

---

### Railway Production Deployment

1. **Set Environment Variables** in Railway dashboard:

   Go to your Prometheus service → Variables → Add:
   
   ```
   SMTP_USERNAME = your-email@gmail.com
   SMTP_PASSWORD = your-16-char-app-password
   ```

2. **Update Prometheus configuration** for Railway:

   In `prometheus.yml`, change Alertmanager target:
   
   ```yaml
   alerting:
     alertmanagers:
       - static_configs:
           - targets: ['alertmanager.railway.internal:9093']
   ```

3. **Deploy changes**:
   
   Railway will automatically rebuild and deploy.

---

## Testing the Alert System

### Method 1: Manual Alert Simulation

1. **Access Alertmanager UI**:
   - Local: http://localhost:9093
   - Production: https://your-alertmanager.railway.app

2. **Check Alert Rules in Prometheus**:
   - Local: http://localhost:9090/alerts
   - Should see `LowModelHealthScore` rule

### Method 2: Trigger Real Alert

To test with real conditions:

1. **Check current health score**:
   ```bash
   curl http://localhost:8000/api/monitoring/health
   ```

2. **Health score calculation**:
   - Based on success rate of model inference requests
   - Alert fires when: `(successful_requests / total_requests) * 100 < 20`

3. **Wait for alert to fire** (if health is actually low)
   - Alert must be firing for 5 minutes before notification
   - Check Prometheus Alerts page to see status

### Method 3: Force Alert for Testing

To force an alert for testing:

1. **Temporarily lower threshold** in `alert.rules.yml`:
   ```yaml
   - alert: LowModelHealthScore
     expr: |
       (
         (
           sum(rate(model_inference_requests_total{status="success"}[10m])) 
           / 
           sum(rate(model_inference_requests_total[10m]))
         ) * 100
       ) < 99  # Changed from 20 to 99 for testing
   ```

2. **Reload Prometheus config**:
   ```bash
   docker-compose restart prometheus
   ```

3. **Wait 5-10 minutes** for alert to fire and email to arrive

4. **Restore original threshold** after testing

---

## Alert Rules Configured

### 1. Overall Model Health Score
- **Alert**: `LowModelHealthScore`
- **Condition**: Overall success rate < 20%
- **Duration**: 5 minutes
- **Severity**: Critical
- **Email**: manjeshprasad21@gmail.com

### 2. Individual Provider Health Score
- **Alert**: `LowProviderHealthScore`
- **Condition**: Provider success rate < 20%
- **Duration**: 5 minutes
- **Severity**: Critical
- **Email**: manjeshprasad21@gmail.com

### 3. High API Error Rate
- **Alert**: `HighAPIErrorRate`
- **Condition**: Error rate > 10%
- **Duration**: 3 minutes
- **Severity**: Critical

### 4. Critical API Latency
- **Alert**: `CriticalAPILatency`
- **Condition**: P95 latency > 3 seconds
- **Duration**: 2 minutes
- **Severity**: Critical

---

## Email Template Features

Emails include:
- **Alert Status**: Firing or Resolved
- **Summary & Description**: What's wrong
- **Dashboard Links**: Direct link to relevant Grafana dashboard
- **Severity Color Coding**: 
  - 🔴 Red for critical
  - 🟡 Yellow for warnings
- **Timestamp**: When alert started/ended

---

## Troubleshooting

### No Emails Received

1. **Check Alertmanager logs**:
   ```bash
   docker-compose logs alertmanager
   ```

2. **Verify SMTP credentials**:
   - Ensure App Password is correct (16 characters, no spaces)
   - Check Gmail account allows "Less secure app access"

3. **Check spam folder**:
   - Alerts might be filtered to spam initially

4. **Test SMTP connection**:
   ```bash
   # From Alertmanager container
   docker-compose exec alertmanager wget -qO- http://localhost:9093/-/healthy
   ```

### Alerts Not Firing

1. **Check Prometheus is scraping**:
   - Visit http://localhost:9090/targets
   - Ensure `gatewayz-api` target is UP

2. **Check metrics exist**:
   ```
   # In Prometheus UI, query:
   model_inference_requests_total
   ```

3. **Check alert rule evaluation**:
   - Visit http://localhost:9090/alerts
   - Look for `LowModelHealthScore` rule
   - Check evaluation status

### Wrong Email Recipient

Update in three places:

1. **alert.rules.yml**: Label `email: "your-email@example.com"`
2. **alertmanager.yml**: All `to:` fields in receivers
3. Rebuild: `docker-compose up -d --build prometheus alertmanager`

---

## Customizing Alerts

### Change Health Threshold

Edit `railway-grafana-stack/prometheus/alert.rules.yml`:

```yaml
- alert: LowModelHealthScore
  expr: |
    (
      (
        sum(rate(model_inference_requests_total{status="success"}[10m])) 
        / 
        sum(rate(model_inference_requests_total[10m]))
      ) * 100
    ) < 50  # Change from 20 to 50 for 50% threshold
```

### Change Alert Duration

```yaml
for: 10m  # Change from 5m to 10m
```

### Add Additional Recipients

Edit `alertmanager.yml`:

```yaml
- name: 'email-critical'
  email_configs:
    - to: 'manjeshprasad21@gmail.com'
      send_resolved: true
    - to: 'team@gatewayz.ai'  # Add additional recipient
      send_resolved: true
```

### Change Notification Frequency

Edit `alertmanager.yml`:

```yaml
route:
  repeat_interval: 1h  # Change from 4h to 1h
```

---

## Monitoring Alert System Health

### Check Alertmanager Status

```bash
# Web UI
open http://localhost:9093

# API status
curl http://localhost:9093/api/v1/status

# Check silences
curl http://localhost:9093/api/v1/silences
```

### Check Prometheus Alert Rules

```bash
# Web UI
open http://localhost:9090/alerts

# API rules
curl http://localhost:9090/api/v1/rules
```

### View Active Alerts

```bash
# Alertmanager API
curl http://localhost:9093/api/v1/alerts | jq
```

---

## Production Best Practices

1. **Use dedicated email** for alerts (not personal)
2. **Set up email filters** to route alerts properly
3. **Configure PagerDuty/Slack** for critical alerts
4. **Monitor Alertmanager health** via Grafana
5. **Test alerts monthly** to ensure delivery
6. **Document alert runbooks** for each alert type
7. **Use alert inhibition** to reduce noise
8. **Set up alert silences** during maintenance

---

## Next Steps

1. ✅ Configure SMTP credentials
2. ✅ Deploy Alertmanager
3. ✅ Test alert delivery
4. 📊 Create alert dashboard in Grafana
5. 📱 Add Slack/PagerDuty integration
6. 📝 Document incident response procedures

---

## Support

For issues:
1. Check logs: `docker-compose logs prometheus alertmanager`
2. Review [Prometheus Alerting Docs](https://prometheus.io/docs/alerting/latest/overview/)
3. Review [Alertmanager Config Docs](https://prometheus.io/docs/alerting/latest/configuration/)

---

**Last Updated**: January 16, 2026
**Maintained By**: GatewayZ Team
