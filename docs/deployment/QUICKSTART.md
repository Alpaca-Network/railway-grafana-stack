# GatewayZ Monitoring Quick Start

Get your monitoring and alerting up and running in 5 minutes.

---

## 🚀 Quick Setup (Local)

### 1. Configure Email Alerts (2 minutes)

```bash
cd railway-grafana-stack

# Create .env file with your Gmail credentials
cat > .env << EOF
SMTP_USERNAME=manjeshprasad21@gmail.com
SMTP_PASSWORD=your-16-character-app-password
EOF
```

**Get Gmail App Password**: https://myaccount.google.com/apppasswords

### 2. Start the Stack (1 minute)

```bash
docker-compose up -d --build
```

This starts:
- ✅ Prometheus (metrics collection)
- ✅ Alertmanager (email alerts)
- ✅ Grafana (dashboards)
- ✅ Loki (logs)
- ✅ Tempo (traces)

### 3. Verify Everything Works (2 minutes)

```bash
./verify_metrics.sh
```

Expected output:
```
✓ Backend API - OK
✓ Prometheus metrics endpoint - OK
✓ Prometheus health - OK
✓ Backend target is UP
✓ HTTP requests - OK
✓ Model inference requests - OK
✓ Alert rules loaded
```

---

## 📊 Access Your Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / yourpassword123 |
| **Prometheus** | http://localhost:9090 | (no auth) |
| **Alertmanager** | http://localhost:9093 | (no auth) |

### Key Dashboards:

1. **Model Performance**:
   http://localhost:3000/d/model-performance-v1/model-performance-analytics

2. **Executive Overview**:
   http://localhost:3000/d/executive-overview-v1

3. **Provider Comparison**:
   http://localhost:3000/d/gateway-comparison-v1

---

## 🚨 Verify Alerts Work

### Check Current Health Score

```bash
# Via Prometheus
open http://localhost:9090/graph

# Run this query:
sum(rate(model_inference_requests_total{status="success"}[10m])) / sum(rate(model_inference_requests_total[10m])) * 100
```

### View Alert Status

```bash
# Prometheus Alerts
open http://localhost:9090/alerts

# Alertmanager
open http://localhost:9093/#/alerts
```

### Test Email (Optional)

To force an alert for testing:

1. Edit `prometheus/alert.rules.yml`:
   ```yaml
   # Temporarily change threshold
   ) < 99  # Changed from 20 to 99 for testing
   ```

2. Restart Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

3. Wait 5-10 minutes for alert to fire

4. Check email at manjeshprasad21@gmail.com

5. **Don't forget to change back to 20!**

---

## 🔧 Troubleshooting

### No Metrics Showing

```bash
# Check backend is running
curl http://localhost:8000/health

# Check Prometheus can reach backend
curl http://localhost:9090/api/v1/targets
```

### No Email Alerts

```bash
# Check Alertmanager logs
docker-compose logs alertmanager | grep -i error

# Verify SMTP credentials
cat .env

# Test Alertmanager is running
curl http://localhost:9093/-/healthy
```

### Dashboard Shows No Data

```bash
# Check Grafana datasources
open http://localhost:3000/datasources

# Restart Grafana
docker-compose restart grafana
```

---

## 📖 Full Documentation

For detailed setup, customization, and troubleshooting:

- **Setup Guide**: `ALERTING_SETUP.md`
- **Summary**: `../PROMETHEUS_VERIFICATION_SUMMARY.md`
- **Verification**: `./verify_metrics.sh`

---

## ✅ You're Done!

Your monitoring is now:
- ✅ Collecting real production data
- ✅ Alerting when health score < 20%
- ✅ Sending emails to manjeshprasad21@gmail.com
- ✅ Displaying beautiful dashboards

**View your dashboards**: http://localhost:3000  
**Check alerts**: http://localhost:9090/alerts  
**Monitor health**: http://localhost:3000/d/model-performance-v1

---

**Questions?** Check the full documentation or run `./verify_metrics.sh`
