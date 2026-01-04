# Staging Metrics Not Pooling - Most Likely Causes

Production works with `api.gatewayz.ai`, but staging with `gatewayz-staging.up.railway.app` has no data.

---

## Quick Diagnosis (Choose One)

### Scenario A: You Can Test Backend URL Directly ⭐ (RECOMMENDED)

Run this command from your terminal to test if the staging backend is working:

```bash
curl -v https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw" 2>&1 | head -50
```

**What to look for:**

| Response | What It Means | Fix |
|----------|---------------|-----|
| `Connection refused` or `Network timeout` | Staging backend not reachable | Check if service is running on Railway |
| `HTTP 401 Unauthorized` | Bearer token is wrong/expired | Get new token from staging |
| `HTTP 404 Not Found` | Metrics endpoint missing | Metrics not enabled on backend |
| `HTTP 200` + empty response | Backend running but no metrics | Backend needs to process some requests first |
| `HTTP 200` + metrics data (lines like `fastapi_requests_total 123`) | ✅ Backend is fine! | Check Prometheus configuration |

---

### Scenario B: Prometheus Targets Check ⭐ (FASTEST)

Go to **Prometheus UI** on your staging Railway instance and check the `gatewayz_staging` job status:

**Path:** Prometheus UI → Status → Targets → Find `gatewayz_staging`

| Status | Meaning | Action |
|--------|---------|--------|
| **UP** (green) | ✅ Working! | Check Grafana dashboard - should see data |
| **DOWN** (red) | ❌ Failing | Click to see error, match to fixes below |
| **Not listed** | Not configured | Update prometheus/prom.yml |

---

## Root Causes & Fixes

### Cause 1: Bearer Token Expired or Wrong ⚠️ (60% likely)

**How to check:**
```bash
curl https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw"
```

**If you get `401 Unauthorized`:**

1. Get the correct bearer token for staging backend
2. Update the token in `prometheus/prom.yml` line 53
3. Redeploy Prometheus to Railway
4. Wait 1-2 minutes for it to start scraping

**File to update:**
```yaml
# prometheus/prom.yml line 53
bearer_token: 'YOUR_NEW_TOKEN_HERE'  # ← Replace this
```

---

### Cause 2: Staging Backend Not Generating Metrics ⚠️ (25% likely)

**How to check:**
```bash
# First verify backend is running
curl https://gatewayz-staging.up.railway.app/health

# Then check if metrics exist
curl https://gatewayz-staging.up.railway.app/metrics \
  -H "Authorization: Bearer gw_live_wTfpLJ5VB28qMXpOAhr7Uw"
```

**If you get 200 OK but empty:**
- Backend is running but has no metrics yet
- Metrics are generated from API requests

**Fix:**
1. Make some API calls to the staging backend to generate metrics
   ```bash
   curl https://gatewayz-staging.up.railway.app/some-endpoint
   ```
2. Wait 15-30 seconds for Prometheus to scrape
3. Check Prometheus again → query `fastapi_requests_total`
4. Should see data now

---

### Cause 3: Prometheus Can't Reach Backend URL ⚠️ (10% likely)

**How to check:**
```bash
curl -I https://gatewayz-staging.up.railway.app/
```

**If connection refused:**
- URL is wrong or backend is down

**Verify:**
- Is the staging backend service running on Railway? Check Railway Dashboard
- Is the service name/URL correct?
- Are there network connectivity issues?

**Fix:**
1. Verify correct staging backend URL on Railway Dashboard
2. Update `prometheus/prom.yml` line 50:
   ```yaml
   targets: ['correct-staging-backend-url']
   ```
3. Redeploy Prometheus

---

### Cause 4: Prometheus Configuration Error ⚠️ (5% likely)

**How to check:**
1. Open Prometheus UI (staging instance)
2. Go to **Status** → **Configuration**
3. Search for `gatewayz_staging`
4. If not listed or has syntax error, it's not configured

**Fix:**
1. Verify `prometheus/prom.yml` has `gatewayz_staging` job (lines 45-57)
2. Syntax check:
   ```bash
   # Make sure lines 45-57 look exactly like this:
   - job_name: 'gatewayz_staging'
     scheme: https
     metrics_path: '/metrics'
     static_configs:
       - targets: ['gatewayz-staging.up.railway.app']
     scrape_interval: 15s
     scrape_timeout: 10s
     bearer_token: 'gw_live_wTfpLJ5VB28qMXpOAhr7Uw'
     metric_relabel_configs:
       - source_labels: []
         target_label: env
         replacement: staging
   ```
3. Redeploy Prometheus

---

## What Production Has That Staging Might Not

**Production Job (WORKING):**
```yaml
- job_name: 'gatewayz_production'
  scheme: https
  metrics_path: '/metrics'
  static_configs:
    - targets: ['api.gatewayz.ai']
  scrape_interval: 15s
  scrape_timeout: 10s
  metric_relabel_configs:
    - source_labels: []
      target_label: env
      replacement: production
```

**Note:** Production has NO bearer_token! It works with just HTTPS.

**Staging Job (NOT WORKING):**
```yaml
- job_name: 'gatewayz_staging'
  scheme: https
  metrics_path: '/metrics'
  static_configs:
    - targets: ['gatewayz-staging.up.railway.app']
  scrape_interval: 15s
  scrape_timeout: 10s
  bearer_token: 'gw_live_wTfpLJ5VB28qMXpOAhr7Uw'  # ← This might be the issue
  metric_relabel_configs:
    - source_labels: []
      target_label: env
      replacement: staging
```

**Key differences:**
- Production uses public URL (`api.gatewayz.ai`) with no auth
- Staging uses Railway URL with bearer token authentication

The bearer token is the most likely culprit.

---

## Quick Fix Checklist

```
□ Step 1: Test backend connectivity
  curl https://gatewayz-staging.up.railway.app/metrics -H "Bearer Token"
  Result: ___________

□ Step 2: If 401 error → Get new token
  New token: ___________

□ Step 3: Update prometheus/prom.yml
  Replace line 53 bearer_token with new token

□ Step 4: Redeploy Prometheus on Railway
  Watch Railway Dashboard for deployment completion

□ Step 5: Check Prometheus Targets
  Should show gatewayz_staging job as UP

□ Step 6: Check Grafana Dashboard
  Should see data in panels

Done! ✅
```

---

## Testing After Fix

Once you've made changes:

1. **Wait 1-2 minutes** for Prometheus to redeploy
2. **Check Prometheus Targets:**
   - Prometheus UI → Status → Targets
   - Find `gatewayz_staging` job
   - Should show `UP` with recent timestamp
3. **Check Grafana:**
   - Open any dashboard
   - Panels should show data (not "No data")
   - Data should update every 15 seconds
4. **Check Prometheus Query:**
   - Go to Prometheus UI → Graph
   - Query: `fastapi_requests_total`
   - Should return results with staging environment label

---

## Most Likely Fix

Based on the pattern:
- Production works: uses public URL with no auth
- Staging doesn't work: uses Railway URL with auth

**Most likely issue:** Bearer token is expired or incorrect for the staging backend.

**Fastest fix:**
1. Get the correct bearer token for `gatewayz-staging.up.railway.app`
2. Update `prometheus/prom.yml` line 53
3. Redeploy Prometheus
4. Data should start flowing in 1-2 minutes

---

## Tell Me What You Find

Run the diagnostic and let me know:

1. **Does `curl` reach the staging backend?** (Yes/No/Error?)
2. **What's the HTTP response code?** (200/401/404/Connection refused?)
3. **If 401: Do you have the correct bearer token?**
4. **What does Prometheus Targets show?** (UP/DOWN/Not listed?)

With this info I can give you the exact fix! 🎯
