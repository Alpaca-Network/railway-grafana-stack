# Diagnose Railway Datasource Connectivity Issues

When your Grafana dashboard shows "No data" and datasources show "connection refused", use this guide to identify the exact problem.

## Step 1: Check Grafana Service Status

### On Railway Dashboard:
1. Go to your project
2. Click "Grafana" service
3. Look at the "Deployments" tab

**Verify:**
- Status is "Success" (green checkmark)
- Latest deployment is recent (within last 10 minutes)
- No error messages in build logs

**If deployment failed:**
- Click the failed deployment
- View "Deploy Logs" for error messages
- Look for issues with building Docker image or environment variables

---

## Step 2: Verify Environment Variables

### On Railway Dashboard Grafana Service:

1. Click "Settings" tab
2. Look for "Variables" section
3. **Must have these set:**
   ```
   LOKI_INTERNAL_URL = http://loki.railway.internal:3100
   PROMETHEUS_INTERNAL_URL = http://prometheus.railway.internal:9090
   TEMPO_INTERNAL_URL = http://tempo.railway.internal:3200
   ```

**If missing:**
- Add them with the exact URLs above
- Click "Save"
- Redeploy Grafana

**If they have different URLs:**
- Check if your service names are different
- Update URLs to match your service names
- Example: If Loki service is called "logs-loki", use `http://logs-loki.railway.internal:3100`

---

## Step 3: Check Individual Service Status

### For Each Service (prometheus, loki, tempo):

1. Go to Railway Dashboard
2. Click on the service
3. Check "Deployments" tab:
   - [ ] Status is "Success"
   - [ ] Latest deployment is recent
   - [ ] No errors in build/deploy logs

**If any service shows failed deployment:**
- Click to view logs
- Look for configuration errors or resource issues
- Try redeploying: click "..." menu → "Deploy Latest Commit"

---

## Step 4: Test Datasource Connectivity From Within Railway

This requires SSH access to a Railway service.

### SSH Into Grafana Container:

```bash
# 1. From Railway Dashboard, go to Grafana service
# 2. Click the "Terminal" or "SSH" icon (if available)
# 3. Run these commands:

# Test Prometheus connectivity
echo "Testing Prometheus..."
curl -v http://prometheus.railway.internal:9090/api/v1/query?query=up

# Test Loki connectivity
echo "Testing Loki..."
curl -v http://loki.railway.internal:3100/loki/api/v1/status/ready

# Test Tempo connectivity
echo "Testing Tempo..."
curl -v http://tempo.railway.internal:3200/status/ready

# Test if Prometheus can reach the backend
echo "Testing Backend (via Prometheus scrape)..."
curl -v https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" | head -20
```

**Expected Results:**

| Test | Expected | Actual |
|------|----------|--------|
| Prometheus | `200 OK` with JSON response | ? |
| Loki | `204 No Content` | ? |
| Tempo | `204 No Content` | ? |
| Backend | `200 OK` with metrics | ? |

---

## Step 5: Check Prometheus Scrape Job Status

### Access Prometheus UI on Railway:

1. Find Prometheus service URL from Railway Dashboard
2. Usually: `https://prometheus-[project-id].up.railway.app`
3. Go to "Status" → "Targets"

**Check each job:**
- [ ] `prometheus` - State should be "UP"
- [ ] `redis_exporter` - State should be "UP"
- [ ] `gatewayz_staging` - State should be "UP"
- [ ] `health_service_exporter` - State should be "UP"

**If job shows "DOWN":**
- Click the job name to see error details
- Common errors:
  - `connection refused` - service not running or wrong URL
  - `no such host` - service name is wrong
  - `dial: i/o timeout` - network connectivity issue
  - `401 Unauthorized` - bearer token wrong

---

## Step 6: Check Prometheus Metrics Are Being Scraped

### In Prometheus UI:

1. Go to "Graph" tab
2. In query box, type: `up`
3. Click "Execute"

**Expected:** Table showing all scrape jobs and their status (1 = up, 0 = down)

**If empty:** Prometheus isn't scraping anything
- Go to "Status" → "Configuration"
- Verify `scrape_configs` look correct

---

## Step 7: Check Grafana Can Query Prometheus

### In Grafana UI:

1. Go to "Settings" (gear icon) → "Data Sources"
2. Click "Prometheus"
3. Scroll to bottom, click "Save & Test"

**Expected Messages:**
- "Data source is working" (green)
- "Query successfully responded"

**If error "connection refused" or "connection timeout":**
- The PROMETHEUS_INTERNAL_URL environment variable isn't correct
- Go back to Step 2 and verify the environment variable

---

## Step 8: Check Backend Is Sending Metrics

### Directly curl the backend:

```bash
# From your local machine (outside Railway)
curl -v https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" | head -30
```

**Expected:**
- Status: `200 OK`
- Response shows Prometheus metrics (lines starting with `#` or metric names)
- You see metrics like `fastapi_requests_total`, `fastapi_request_duration_seconds`, etc.

**If you don't see metrics:**
- Backend might not have Prometheus metrics enabled
- Backend might not be running or accessible

---

## Common Issues & Solutions

### Issue: "Connection refused" to Prometheus from Grafana

**Diagnosis:** Prometheus service isn't listening on correct address

**Solutions:**
1. [ ] Verify `PROMETHEUS_INTERNAL_URL` is set in Grafana environment
2. [ ] Restart Prometheus service
3. [ ] Check Prometheus logs for startup errors
4. [ ] Verify Prometheus has 512MB+ memory allocation

### Issue: "No data" in Grafana despite green datasources

**Diagnosis:** Datasources connected but not receiving data

**Solutions:**
1. [ ] Check Prometheus Targets - is `gatewayz_staging` UP?
   - If DOWN: Check bearer token and backend URL in `prometheus/prom.yml`
2. [ ] Check if backend is actually sending metrics
   - Run: `curl https://gatewayz-staging.up.railway.app/metrics -H "Authorization: Bearer..."`
3. [ ] Check if Prometheus is storing data
   - In Prometheus UI, query: `fastapi_requests_total`
   - If no results: Backend metrics not being scraped

### Issue: "WebSocket connection failed"

**Diagnosis:** Browser can't connect to Grafana WebSocket

**Solutions:**
1. [ ] Clear browser cache (Ctrl+Shift+Delete)
2. [ ] Try in private/incognito window
3. [ ] Try different browser (Chrome vs Firefox)
4. [ ] Check if Grafana service is still running (might have crashed)

### Issue: Loki/Tempo show "connection refused"

**Diagnosis:** These services might not be running or listening

**Solutions:**
1. [ ] Check service status in Railway Dashboard
2. [ ] Check service logs for startup errors
3. [ ] Verify services have 512MB+ memory
4. [ ] Check `LOKI_INTERNAL_URL` and `TEMPO_INTERNAL_URL` environment variables
5. [ ] Restart services in this order: Loki → Tempo → Grafana

---

## Verification Flowchart

```
START: Dashboard shows "No data"
│
├─ Is Grafana accessible? (can you see login page)
│  ├─ NO → Check Grafana service status on Railway Dashboard
│  │     → Check build/deploy logs for errors
│  │
│  └─ YES → Can you log in with admin/password?
│     ├─ NO → Wrong credentials or GF_SECURITY_ADMIN_PASSWORD not set
│     │
│     └─ YES → Go to Data Sources (⚙️ → Data Sources)
│        ├─ ALL datasources RED?
│        │  └─ Environment variables not set (Step 2)
│        │
│        ├─ SOME datasources RED?
│        │  └─ That specific service not running (check logs)
│        │
│        └─ ALL datasources GREEN?
│           ├─ Open a dashboard (e.g., Backend Health)
│           ├─ Still no data?
│           │  ├─ Check Prometheus Targets (Step 5)
│           │  ├─ Is gatewayz_staging UP?
│           │  │  ├─ NO → Bearer token wrong or backend down
│           │  │  └─ YES → Query Prometheus UI directly
│           │  │           Query: fastapi_requests_total
│           │  │           If no results → Backend not sending metrics
│           │  │
│           │  └─ ✅ Data showing? Success!
```

---

## Quick Checklist for Troubleshooting

- [ ] All services deployed successfully (no errors in Railway Dashboard)
- [ ] Environment variables set on Grafana service
- [ ] Grafana can be accessed (login works)
- [ ] All datasources show green checkmark
- [ ] Backend is running and accessible
- [ ] Prometheus Targets show `gatewayz_staging` as "UP"
- [ ] Backend is returning metrics when you curl it
- [ ] You waited 2-3 minutes for data to accumulate

---

## Need More Help?

If you've followed all steps and still have issues:

1. **Collect diagnostic information:**
   ```bash
   # Screenshot of Railway Dashboard showing all services
   # Screenshot of Prometheus Targets
   # Output of: curl https://gatewayz-staging.up.railway.app/metrics -H "Authorization: Bearer..."
   # Grafana datasource error messages (if red X)
   ```

2. **Check these files:**
   - `prometheus/prom.yml` - Backend URL and bearer token
   - `docker-compose.yml` - Datasource environment variables
   - `grafana/Dockerfile` - Railway defaults

3. **Review logs:**
   - Grafana build and deploy logs
   - Prometheus logs (look for scrape errors)
   - Each service for error messages

---

## After You Fix It

Once datasources are working:

1. **Monitor for 30 minutes** - watch for stability
2. **Check dashboard refreshes** - data should update every 15 seconds
3. **Review both local and Railway** - ensure behavior is consistent
4. **Document what fixed it** - update this guide for future reference
