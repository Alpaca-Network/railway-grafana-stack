# Railway Deployment Guide - Grafana Monitoring Stack

## Problem: Datasources Not Connecting on Railway

**Issue**: Grafana dashboard shows "No data" on Railway deployment, but works fine locally.

**Root Cause**: Datasource configuration was using local Docker service names that don't resolve on Railway's network.

---

## Solution: Proper Service Networking on Railway

### How Railway Internal Networking Works

When you deploy services on Railway:
1. Each service gets an internal domain: `<service-name>.railway.internal`
2. Services can communicate using these domains from within Railway's network
3. Environment variables can be used to configure service URLs

### Configuration Changes Made

#### 1. Fixed Datasource Variable Names (loki.yml)
- **Before**: `${LOKI_URL:-http://loki:3100}`
- **After**: `${LOKI_INTERNAL_URL:-http://loki:3100}` (consistent naming)

This ensures all datasources (Prometheus, Loki, Tempo) use the same naming convention.

#### 2. Cleaned Docker Compose Configuration
- **Removed** duplicate/conflicting environment variables
- **Kept** only necessary datasource configuration
- **Comment** added explaining Railway vs. local behavior

#### 3. Dockerfile Already Has Railway Defaults
```dockerfile
ENV LOKI_INTERNAL_URL=http://loki.railway.internal:3100
ENV PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
ENV TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
```

---

## Deployment to Railway

### Step 1: Set Environment Variables on Railway

For the **Grafana service** on Railway, set these environment variables:

```
LOKI_INTERNAL_URL=http://loki.railway.internal:3100
PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
```

**How to set on Railway Dashboard:**
1. Go to your project → Grafana service
2. Click "Settings" → "Variables"
3. Add each environment variable with the values above
4. Click "Save" and redeploy

### Step 2: Verify Service Names Match

Ensure that your Railway services are named exactly:
- `prometheus` (not prometheus-service, prom, etc.)
- `loki` (not loki-service, logs, etc.)
- `tempo` (not tempo-service, traces, etc.)

If your services have different names, update the environment variables accordingly. For example:
- If Prometheus service is called `metrics`: `http://metrics.railway.internal:9090`

### Step 3: Commit Configuration Changes

```bash
cd railway-grafana-stack
git add docker-compose.yml grafana/provisioning/datasources/loki.yml
git commit -m "fix: correct datasource configuration for Railway deployment

- Fix inconsistent LOKI_URL to LOKI_INTERNAL_URL variable naming
- Clean up docker-compose environment variable overrides
- Add comment explaining Railway vs. local network configuration
- Ensure all datasources use consistent naming convention"
git push origin staging
```

### Step 4: Trigger Redeployment

Railway will automatically detect the changes and rebuild. Monitor the deployment:

1. Watch the Railway dashboard for build/deploy status
2. Check logs for each service starting correctly
3. Look for any connectivity errors

---

## Verification Checklist

### ✅ Services Running
In Railway dashboard, verify all services show "Running" status:
- [ ] prometheus - Running
- [ ] loki - Running
- [ ] tempo - Running
- [ ] grafana - Running

### ✅ Grafana Accessible
1. Open Grafana: `https://grafana-[your-project].up.railway.app`
2. Login with admin credentials
3. Verify no SSL certificate warnings

### ✅ Datasources Connected
1. Go to Grafana → Configuration → Data Sources
2. Click each datasource:
   - [ ] **Prometheus** - Green checkmark, shows "Success"
   - [ ] **Loki** - Green checkmark, shows "Success"
   - [ ] **Tempo** - Green checkmark, shows "Success"

**If datasource shows red X or "connection refused":**
- Check the environment variables are set correctly
- Verify the service names match (if you renamed services)
- Check service is actually running (may need to restart)

### ✅ Data Flowing
1. Open any dashboard (e.g., Backend Health)
2. Panels should show data (not "No data")
3. Timestamps should be recent (within last 5 minutes)

---

## Common Issues & Fixes

### Issue 1: All Datasources Show "Connection Refused"

**Symptom**: Red X on all datasources, error says "connection refused"

**Diagnosis**:
```bash
# Check if services are running and responding
# (From within Grafana container - through Railway SSH)

# Test Prometheus
curl http://prometheus.railway.internal:9090/api/v1/query?query=up

# Test Loki
curl http://loki.railway.internal:3100/loki/api/v1/status/ready

# Test Tempo
curl http://tempo.railway.internal:3200/status/ready
```

**Fixes** (in priority order):
1. ✅ **Verify environment variables are set** (most common issue)
   - Go to Grafana service settings
   - Confirm LOKI_INTERNAL_URL, PROMETHEUS_INTERNAL_URL, TEMPO_INTERNAL_URL are set

2. ✅ **Verify service names match**
   - If services have different names on Railway, update the URLs
   - Example: If service is named `prom` instead of `prometheus`, use `http://prom.railway.internal:9090`

3. ✅ **Restart affected services**
   - On Railway dashboard, restart each service in this order:
     1. Prometheus (waits 10s)
     2. Loki (waits 10s)
     3. Tempo (waits 10s)
     4. Grafana

4. ✅ **Check service resources**
   - Verify each service has at least 512MB memory allocated
   - Check if any service is showing resource exhaustion

### Issue 2: Only Some Datasources Work

**Symptom**: Prometheus works (green checkmark) but Loki shows "connection refused"

**Possible Causes**:
- Loki service hasn't fully started yet
- Loki port mapping incorrect
- Loki configuration has errors (check logs)

**Fix**:
1. Check Loki logs for startup errors
2. Verify Loki has persistent volume properly mounted
3. Restart Loki service
4. Wait 30 seconds before testing datasource again

### Issue 3: Dashboard Shows "No Data" but Datasources Connected

**Symptom**: All datasources show green checkmark, but dashboard panels say "No data"

**Causes**:
- Prometheus not scraping backend metrics
- Loki not receiving logs
- Queries/dashboards configured incorrectly

**Fix**:
1. In Prometheus → Targets, check if `gatewayz_staging` is "UP"
   - If DOWN: Check backend URL and bearer token in prom.yml
   - Fix: Update `prometheus/prom.yml` and redeploy

2. In Loki → API → Labels, check if log streams exist
   - If none: Backend may not be sending logs
   - Fix: Configure backend to send logs to Loki endpoint

3. Test queries directly:
   - Prometheus query: `fastapi_requests_total` (should return results)
   - Loki query: `{app="gatewayz"}` (should return log lines)

### Issue 4: WebSocket Connection Error

**Symptom**: Console error: `WebSocket connection to 'wss://grafana.../api/live/ws' failed`

**Fix**:
- This is usually a browser caching issue
- Clear browser cache: `Ctrl+Shift+Delete` (Chrome) or `Cmd+Shift+Delete` (Mac)
- Open Grafana in private/incognito window
- Try accessing Grafana from a different browser

---

## Local vs. Railway Behavior

### Local Development (docker-compose up)
```yaml
# docker-compose.yml provides these defaults:
PROMETHEUS_INTERNAL_URL=http://prometheus:9090
LOKI_INTERNAL_URL=http://loki:3100
TEMPO_INTERNAL_URL=http://tempo:3200

# Docker resolves these service names using Docker's internal DNS
```

### Railway Production
```yaml
# Dockerfile provides these defaults:
LOKI_INTERNAL_URL=http://loki.railway.internal:3100
PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200

# BUT docker-compose.yml overrides with local defaults
# UNLESS you explicitly set them in Railway environment variables

# Solution: Set in Railway Dashboard for explicit control
```

---

## Troubleshooting Flow

```
Is Grafana accessible? (can you see login page)
├─ NO → Check Railway deployment status, service running?
│
├─ YES → Can you log in?
│  ├─ NO → Check GF_SECURITY_ADMIN_PASSWORD environment variable
│  │
│  └─ YES → Go to Configuration → Data Sources
│      ├─ ALL RED → Check environment variables on Railway
│      ├─ SOME RED → That service may not be running, check logs
│      ├─ ALL GREEN but "No data" → Check dashboard queries and backend metrics
│      └─ ALL GREEN with DATA → ✅ SUCCESS!
```

---

## Prevention: Best Practices

### 1. Always Set Railway Environment Variables Explicitly
Don't rely on Dockerfile defaults when they could be ambiguous.

### 2. Name Services Consistently
Use simple, lowercase names:
- `prometheus` (not `prometheus-monitoring`)
- `loki` (not `loki-logs`)
- `tempo` (not `tempo-tracing`)

### 3. Document Your Configuration
Add a `railway.env.example` file showing required variables:

```bash
# LOKI_INTERNAL_URL=http://loki.railway.internal:3100
# PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090
# TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200
```

### 4. Test Locally First
```bash
# Always run locally before pushing to Railway
docker-compose up

# Verify dashboard in browser at http://localhost:3000
# Check datasources are connected
# Confirm data is showing

# Only after local verification, push to Railway
git push origin staging
```

### 5. Monitor After Deployment
- Watch service logs for errors
- Test datasource connectivity immediately after deploy
- Wait 2-3 minutes for services to fully stabilize
- Monitor for 30 minutes before considering deployment complete

---

## Next Steps

1. **Set the environment variables on Railway** (Step 1 above)
2. **Verify services are connected** (Verification Checklist)
3. **Monitor dashboard for data flow** (wait 2-3 minutes)
4. **Document any custom service names** if different from defaults

---

## Need Help?

If datasources still don't connect after following this guide:

1. **Check Grafana Logs**:
   - Railway Dashboard → Grafana Service → Deployments → View Logs
   - Look for datasource configuration errors

2. **Check Individual Service Logs**:
   - Prometheus Logs - look for scrape errors
   - Loki Logs - look for startup errors
   - Tempo Logs - look for connection issues

3. **Verify Network Configuration**:
   - Are services in the same Railway project? (required for `.railway.internal`)
   - Is there a firewall or network policy blocking ports?

4. **Test Connectivity from Within Services**:
   - SSH into Grafana container on Railway
   - Run: `curl http://prometheus.railway.internal:9090/api/v1/query?query=up`
   - If that fails, services can't reach each other
