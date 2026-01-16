# GatewayZ Monitoring Stack - Deployment Checklist

## Pre-Deployment Checklist

### 1. Email Configuration ✉️

- [ ] **Gmail Account Ready**
  - Using: manjeshprasad21@gmail.com
  - [ ] 2-Factor Authentication enabled
  - [ ] App Password created (16 characters)
  - [ ] App Password saved securely

- [ ] **Environment Variables Set**
  ```bash
  # For local Docker Compose
  cd railway-grafana-stack
  cat .env
  # Should contain:
  # SMTP_USERNAME=manjeshprasad21@gmail.com
  # SMTP_PASSWORD=xxxx xxxx xxxx xxxx
  ```

  ```bash
  # For Railway Production
  # Set in Railway dashboard → Service → Variables:
  # SMTP_USERNAME = manjeshprasad21@gmail.com
  # SMTP_PASSWORD = your-app-password
  ```

### 2. File Verification 📁

- [ ] **New Files Created**
  - [ ] `prometheus/alertmanager.yml` (9.5KB)
  - [ ] `ALERTING_SETUP.md` (8KB)
  - [ ] `QUICKSTART.md` (3.6KB)
  - [ ] `verify_metrics.sh` (7.7KB, executable)
  - [ ] `PROMETHEUS_VERIFICATION_SUMMARY.md` (created in parent dir)

- [ ] **Modified Files**
  - [ ] `prometheus/alert.rules.yml` (health score alerts added)
  - [ ] `gatewayz-backend/prometheus.yml` (alertmanager enabled)
  - [ ] `docker-compose.yml` (alertmanager service added)
  - [ ] `grafana/dashboards/models/model-performance-v1.json` (layout fixed)

### 3. Configuration Validation ✅

Run these checks before deploying:

```bash
# Check alertmanager.yml syntax
docker run --rm -v $(pwd)/prometheus:/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml

# Check prometheus config
docker run --rm -v $(pwd)/prometheus:/config prom/prometheus:latest promtool check config /config/prom.yml

# Check alert rules
docker run --rm -v $(pwd)/prometheus:/config prom/prometheus:latest promtool check rules /config/alert.rules.yml
```

Expected output:
```
✅ SUCCESS: alertmanager.yml is valid
✅ SUCCESS: prom.yml is valid  
✅ SUCCESS: 3 rule(s) found
```

---

## Local Deployment (Docker Compose)

### Step 1: Prepare Environment

```bash
cd railway-grafana-stack

# Create .env file
cat > .env << 'EOF'
SMTP_USERNAME=manjeshprasad21@gmail.com
SMTP_PASSWORD=your-16-character-app-password-here
EOF

# Verify .env
cat .env
```

### Step 2: Build and Start Services

```bash
# Stop any running services
docker-compose down

# Remove old volumes (optional, only if you want fresh start)
# docker-compose down -v

# Build and start
docker-compose up -d --build

# Check service status
docker-compose ps
```

Expected output:
```
NAME                          STATUS          PORTS
grafana                       Up             0.0.0.0:3000->3000/tcp
prometheus                    Up             0.0.0.0:9090->9090/tcp
alertmanager                  Up             0.0.0.0:9093->9093/tcp
loki                          Up             0.0.0.0:3100->3100/tcp
tempo                         Up             multiple
redis-exporter                Up             0.0.0.0:9121->9121/tcp
json-api-proxy                Up             0.0.0.0:5000->5000/tcp
```

### Step 3: Verify Services

```bash
# Run automated verification
./verify_metrics.sh

# Manual checks
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:9093/-/healthy  # Alertmanager
curl http://localhost:3000/api/health # Grafana
```

### Step 4: Check Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f alertmanager
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Look for errors
docker-compose logs | grep -i error
```

### Step 5: Access Dashboards

Open in browser:
- [ ] Grafana: http://localhost:3000 (admin / yourpassword123)
- [ ] Prometheus: http://localhost:9090
- [ ] Alertmanager: http://localhost:9093
- [ ] Model Performance: http://localhost:3000/d/model-performance-v1

---

## Railway Production Deployment

### Step 1: Update Railway Configuration

1. **Set Environment Variables**:
   - Go to Railway Dashboard
   - Select Prometheus service
   - Go to Variables tab
   - Add:
     ```
     SMTP_USERNAME = manjeshprasad21@gmail.com
     SMTP_PASSWORD = your-app-password
     ```

2. **Update Prometheus Config for Railway**:
   
   Edit `gatewayz-backend/prometheus.yml`:
   ```yaml
   alerting:
     alertmanagers:
       - static_configs:
           - targets: ['alertmanager.railway.internal:9093']
   ```

### Step 2: Deploy Alertmanager Service

1. **Create new service** in Railway:
   - Name: `alertmanager`
   - Image: `prom/alertmanager:latest`
   - Port: 9093

2. **Add volumes**:
   - `/alertmanager` for data persistence

3. **Mount configuration**:
   - Upload `prometheus/alertmanager.yml` to service
   - Mount at `/etc/alertmanager/alertmanager.yml`

4. **Set command**:
   ```
   --config.file=/etc/alertmanager/alertmanager.yml
   --storage.path=/alertmanager
   ```

### Step 3: Update Prometheus Service

1. **Upload new files**:
   - `prometheus/alert.rules.yml` (updated)
   - `gatewayz-backend/prometheus.yml` (updated)

2. **Redeploy** Prometheus service

### Step 4: Update Grafana Dashboards

1. **Upload new dashboard**:
   - `grafana/dashboards/models/model-performance-v1.json`

2. **Reload** Grafana service

### Step 5: Verify Production Deployment

```bash
# Check Prometheus targets
curl https://your-prometheus.railway.app/api/v1/targets

# Check alert rules
curl https://your-prometheus.railway.app/api/v1/rules

# Check Alertmanager
curl https://your-alertmanager.railway.app/api/v1/status
```

---

## Post-Deployment Verification

### 1. Metrics Collection ✅

```bash
# Check Prometheus is scraping backend
open http://localhost:9090/targets

# Should show:
# ✅ gatewayz-api (1/1 up) - State: UP
```

### 2. Alert Rules ✅

```bash
# Check alert rules are loaded
open http://localhost:9090/alerts

# Should show:
# ✅ LowModelHealthScore - State: Inactive (or Pending/Firing)
# ✅ LowProviderHealthScore - State: Inactive
# ✅ HighAPIErrorRate - State: Inactive
```

### 3. Alertmanager Integration ✅

```bash
# Check Alertmanager status
open http://localhost:9093/#/status

# Should show:
# ✅ Cluster Status: Ready
# ✅ Config: alertmanager.yml loaded
# ✅ Uptime: > 0s
```

### 4. Dashboard Functionality ✅

```bash
# Open Model Performance dashboard
open http://localhost:3000/d/model-performance-v1

# Verify:
# ✅ Panels are loading data
# ✅ Charts are readable (horizontal bars with values)
# ✅ No "No data" errors
# ✅ Time range selector works
# ✅ Refresh works (60s auto-refresh)
```

### 5. Email Test ✅

**Option A: Wait for Real Alert**
- Monitor health score
- When it drops below 20%, alert fires after 5 minutes
- Check email: manjeshprasad21@gmail.com

**Option B: Force Test Alert**

1. Edit `prometheus/alert.rules.yml`:
   ```yaml
   ) < 99  # Temporary: changed from 20 to 99
   ```

2. Restart Prometheus:
   ```bash
   docker-compose restart prometheus
   ```

3. Wait 5-10 minutes

4. Check email for alert

5. **Restore original threshold**:
   ```yaml
   ) < 20  # Back to normal
   ```

---

## Troubleshooting Guide

### Issue: Alertmanager not starting

**Symptoms**:
- Container exits immediately
- Logs show config error

**Solution**:
```bash
# Check config syntax
docker run --rm -v $(pwd)/prometheus:/config prom/alertmanager:latest amtool check-config /config/alertmanager.yml

# Check environment variables
docker-compose config | grep SMTP

# Check logs
docker-compose logs alertmanager
```

### Issue: No email alerts received

**Symptoms**:
- Alert is firing in Prometheus
- No email received

**Checklist**:
- [ ] Check SMTP credentials in .env
- [ ] Verify Gmail App Password (not regular password)
- [ ] Check Alertmanager logs: `docker-compose logs alertmanager`
- [ ] Check spam folder
- [ ] Verify alert is firing: http://localhost:9090/alerts
- [ ] Check Alertmanager UI: http://localhost:9093/#/alerts

**Test SMTP manually**:
```bash
# Enter Alertmanager container
docker-compose exec alertmanager sh

# Test connectivity (if tools available)
wget -qO- http://localhost:9093/-/healthy
```

### Issue: Prometheus not scraping backend

**Symptoms**:
- Target shows as DOWN
- No metrics data

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check backend metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus config
docker-compose exec prometheus cat /etc/prometheus/prom.yml

# Check Prometheus logs
docker-compose logs prometheus | grep -i error

# Restart Prometheus
docker-compose restart prometheus
```

### Issue: Dashboard shows "No data"

**Symptoms**:
- Grafana loads but panels are empty

**Solution**:
```bash
# Check Grafana datasources
open http://localhost:3000/datasources

# Test Prometheus datasource
# Go to datasource → Test → Should show "Data source is working"

# Check if metrics exist in Prometheus
open http://localhost:9090/graph
# Query: fastapi_requests_total

# Check Grafana logs
docker-compose logs grafana | grep -i error
```

### Issue: Alert rules not loading

**Symptoms**:
- No alerts showing in Prometheus UI
- Rules file not loaded

**Solution**:
```bash
# Check rules file syntax
docker run --rm -v $(pwd)/prometheus:/config prom/prometheus:latest promtool check rules /config/alert.rules.yml

# Check Prometheus config points to rules file
docker-compose exec prometheus cat /etc/prometheus/prom.yml | grep rules

# Check file is mounted
docker-compose exec prometheus ls -la /etc/prometheus/

# Restart Prometheus
docker-compose restart prometheus
```

---

## Rollback Plan

If something goes wrong:

```bash
# Stop all services
docker-compose down

# Restore backup (if you made one)
# cp prometheus/alert.rules.yml.backup prometheus/alert.rules.yml
# cp gatewayz-backend/prometheus.yml.backup gatewayz-backend/prometheus.yml

# Or remove alertmanager from docker-compose.yml
# Comment out the alertmanager service section

# Restart without alertmanager
docker-compose up -d prometheus grafana loki tempo
```

---

## Success Criteria ✅

Your deployment is successful when:

- [x] All services are running (docker-compose ps shows "Up")
- [x] Prometheus is scraping backend (target is UP)
- [x] Alert rules are loaded (visible in /alerts)
- [x] Alertmanager is connected to Prometheus
- [x] Grafana dashboards are loading data
- [x] Model Performance dashboard is readable
- [x] Email test alert was received
- [x] No errors in logs

---

## Monitoring Post-Deployment

### Daily:
- [ ] Check dashboard for anomalies
- [ ] Review alert history
- [ ] Check email for alerts

### Weekly:
- [ ] Review Prometheus retention
- [ ] Check disk usage
- [ ] Verify all targets are UP
- [ ] Test alert delivery

### Monthly:
- [ ] Review alert thresholds
- [ ] Update dashboards based on feedback
- [ ] Check for Prometheus/Grafana updates
- [ ] Audit alert rules

---

## Contact & Support

**Alert Email**: manjeshprasad21@gmail.com  
**Documentation**: 
- Quick Start: `QUICKSTART.md`
- Setup Guide: `ALERTING_SETUP.md`
- Summary: `../PROMETHEUS_VERIFICATION_SUMMARY.md`

**Health Check Script**: `./verify_metrics.sh`

---

**Last Updated**: January 16, 2026  
**Version**: 1.0  
**Status**: Ready for Deployment
