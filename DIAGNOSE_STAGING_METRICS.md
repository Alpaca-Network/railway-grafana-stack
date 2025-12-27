# Diagnose Staging Metrics Collection Issue

Production is working but staging is not collecting metrics. Let's find out why.

---

## Quick Test 1: Test Staging Backend Directly (2 minutes)

Run this from your local machine to test if the staging backend is even responding:

```bash
# Test if staging backend is accessible
curl -v https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" | head -50
```

**Expected Output:**
- Status: `200 OK`
- Response should contain Prometheus metrics (lines starting with `#` or metric names like `fastapi_requests_total`)

**If you see:**
- `curl: (7) Failed to connect` or `Connection refused` → Backend not reachable
- `401 Unauthorized` → Bearer token is wrong or expired
- `404 Not Found` → Metrics endpoint doesn't exist
- `200 OK` but empty/no metrics → Metrics not being generated on backend

---

## Quick Test 2: Check Prometheus in Staging on Railway (3 minutes)

1. Go to Railway Dashboard
2. Find your **staging Prometheus service** instance
3. Check if it's running (should show "Running" status)
4. Open Prometheus UI (usually `https://prometheus-[project].up.railway.app` for staging)

Once in Prometheus UI:
1. Go to **Status** → **Targets**
2. **Look for the `gatewayz_staging` job**

**Check the state:**
- [ ] State = `UP` (green) → Connection working, collecting metrics ✅
- [ ] State = `DOWN` (red) → Something wrong, click to see error
- [ ] Job not listed → Not configured in prom.yml

**If DOWN, click the job and look for errors like:**
- `connection refused` - Backend not reachable
- `no such host` - DNS resolution failing
- `401 Unauthorized` - Bearer token wrong
- `dial timeout` - Network connectivity issue

---

## Likely Issues & Solutions

### Issue 1: Staging Backend Not Returning Metrics

**Symptom**: `curl` returns 200 OK but no metrics data

**Cause**: Backend may not have Prometheus metrics enabled/initialized

**Solution**:
```bash
# Check if backend is actually generating metrics
curl https://gatewayz-staging.up.railway.app/health
curl https://gatewayz-staging.up.railway.app/status

# If these work, backend is running
# Then check if metrics endpoint needs to be triggered/initialized
# You may need to make some requests to the backend first to generate metrics
```

**Fix**:
- Ensure backend has Prometheus metrics middleware enabled
- Make some API requests to the backend (generates HTTP request metrics)
- Wait 15-30 seconds for Prometheus to scrape
- Check Prometheus UI again

---

### Issue 2: Bearer Token Expired or Wrong

**Symptom**: `curl` returns `401 Unauthorized`

**Current token in prom.yml:**
```
gw_live_wTfpLJ5VB28qMXpOAhr7Uw
```

**Solution**:
1. Get the correct bearer token for staging backend
2. Update `prometheus/prom.yml` line 53:
   ```yaml
   bearer_token: 'YOUR_NEW_TOKEN_HERE'
   ```
3. Redeploy Prometheus on Railway
4. Test again

---

### Issue 3: Staging Backend URL Wrong or Down

**Symptom**: `curl` returns `Connection refused` or `Network timeout`

**Causes**:
- Staging backend service is not running on Railway
- Service name changed on Railway
- Network connectivity issue between services

**Solution**:
1. Verify staging backend is running on Railway Dashboard
2. Verify the exact service name/URL
3. Update `prometheus/prom.yml` line 50 with correct URL:
   ```yaml
   static_configs:
     - targets: ['your-actual-staging-backend.up.railway.app']
   ```

---

### Issue 4: Prometheus Scrape Job Not Configured

**Symptom**: `gatewayz_staging` job not visible in Prometheus Targets

**Cause**: prom.yml not deployed or misconfigured

**Solution**:
1. Verify `prometheus/prom.yml` contains the `gatewayz_staging` job (lines 45-57)
2. Restart Prometheus service on Railway
3. Check Prometheus logs for configuration errors

---

## Complete Diagnostic Flow

```
START: Staging has no metrics data
│
├─ Test 1: Can curl reach staging backend?
│  curl https://gatewayz-staging.up.railway.app/metrics -H "Bearer Token"
│
│  ├─ Connection refused/timeout
│  │  └─ Staging backend not running or wrong URL
│  │     → Check Railway Dashboard
│  │
│  ├─ 401 Unauthorized
│  │  └─ Bearer token expired or wrong
│  │     → Get new token, update prom.yml
│  │
│  ├─ 404 Not Found
│  │  └─ Metrics endpoint doesn't exist
│  │     → Ensure backend has metrics enabled
│  │
│  └─ 200 OK + Metrics data
│     └─ Backend is fine, check Prometheus
│
├─ Test 2: Is Prometheus scraping the backend?
│  Go to Prometheus UI → Status → Targets
│  Look for gatewayz_staging job
│
│  ├─ Job not visible
│  │  └─ Not configured in prom.yml
│  │     → Update prom.yml, redeploy Prometheus
│  │
│  ├─ Job UP (green)
│  │  └─ Metrics should be flowing!
│  │     → Go to Grafana, should see data
│  │
│  └─ Job DOWN (red)
│     └─ Click job to see error details
│        → Match error to Issue 1-3 above
│
└─ Test 3: Is Grafana getting Prometheus data?
   Go to Grafana → Configuration → Data Sources
   Click Prometheus → Verify connection works
   Then open dashboard - should see data

DONE! Metrics should now be flowing ✅
```

---

## Step-by-Step Debugging

### Step 1: Verify Staging Backend Metrics Endpoint

```bash
# First, check if the backend URL is correct
echo "Testing staging backend connectivity..."
curl -I https://gatewayz-staging.up.railway.app/

# Then test metrics endpoint specifically
echo "Testing metrics endpoint..."
curl -v https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  2>&1 | grep -E "HTTP|metrics|fastapi"

# If you get metrics, pipe to see them
curl https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" \
  2>/dev/null | head -30
```

**Record results:**
- HTTP Status: ___________
- Metrics returned: Yes / No
- Metric names visible: ___________

---

### Step 2: Check Prometheus Configuration

```bash
# Verify prom.yml has gatewayz_staging job configured
grep -A 10 "gatewayz_staging" prometheus/prom.yml

# Expected output:
# - job_name: 'gatewayz_staging'
#   scheme: https
#   metrics_path: '/metrics'
#   static_configs:
#     - targets: ['gatewayz-staging.up.railway.app']
#   bearer_token: 'gw_live_wTfpLJ5VB28qMXpOAhr7Uw'
```

---

### Step 3: Check Prometheus on Railway

1. Open Railway Dashboard
2. Go to Prometheus service (staging version)
3. Check "Deployments" - latest should be "Success"
4. Open Prometheus UI (click the service URL)
5. Go to **Status** → **Targets**
6. Find `gatewayz_staging` job

**Record the state:**
- State: UP / DOWN
- Error (if DOWN): ___________
- Scrapes: ___________ (should be > 0)

---

### Step 4: Verify Grafana Dashboard

1. Open Grafana staging instance
2. Go to any dashboard
3. Open browser DevTools → Console
4. Look for errors fetching data from Prometheus
5. Check if panels show "No data" or show data

---

## If All Tests Pass But Still No Data

**Metrics might not be generated yet.** Try:

```bash
# 1. Make some API requests to staging backend
curl https://gatewayz-staging.up.railway.app/health

# 2. Wait for Prometheus scrape interval (15 seconds)
sleep 20

# 3. Check Prometheus directly
# Query: fastapi_requests_total
# Should show results now

# 4. If still no results, Prometheus might not have metrics
# Check Prometheus logs for scrape errors
```

---

## Summary of What Could Be Wrong

| Issue | Sign | Fix |
|-------|------|-----|
| Backend not running | Connection refused | Check Railway staging backend status |
| Wrong backend URL | 404 Not Found / Connection refused | Verify correct staging URL |
| Bearer token expired | 401 Unauthorized | Get new token, update prom.yml |
| Backend metrics disabled | 200 OK, empty response | Enable Prometheus metrics on backend |
| Prometheus not scraping | Targets show DOWN | Check prom.yml configuration |
| No API traffic | Metrics empty | Make API calls to generate metrics |
| Prometheus configuration error | Prometheus fails to start | Check prometheus/prom.yml syntax |

---

## Next Steps

1. **Run the tests above** to identify the exact issue
2. **Report back with findings** - which test failed?
3. **I'll provide specific fix** based on the error you find

Most likely the issue is either:
- Bearer token needs updating
- Backend metrics not enabled
- Prometheus configuration needs update
