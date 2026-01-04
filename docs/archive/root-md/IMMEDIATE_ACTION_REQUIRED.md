# Immediate Actions Required - Grafana Datasource Fix

Your Grafana dashboard is showing "No data" because the datasources can't connect on Railway. This has been FIXED. Here's exactly what to do:

---

## Step 1: Commit Configuration Changes (2 minutes)

```bash
cd railway-grafana-stack

git add docker-compose.yml grafana/provisioning/datasources/loki.yml loki/loki.yml tempo/tempo.yml

git commit -m "fix: correct datasource configuration for Railway deployment

- Fix inconsistent LOKI_URL to LOKI_INTERNAL_URL variable naming
- Clean up docker-compose environment variable overrides
- Ensure all datasources use consistent naming convention
- Add explicit listen addresses to Loki and Tempo for Railway network
- Add comment explaining Railway vs. local network configuration"

git push origin staging
```

---

## Step 2: Configure Environment Variables on Railway (3 minutes)

This is THE KEY FIX.

### On Railway Dashboard:

1. Go to your project
2. Click **Grafana** service
3. Click **Settings** tab
4. Look for **Variables** section
5. **Add these environment variables:**

| Name | Value |
|------|-------|
| `LOKI_INTERNAL_URL` | `http://loki.railway.internal:3100` |
| `PROMETHEUS_INTERNAL_URL` | `http://prometheus.railway.internal:9090` |
| `TEMPO_INTERNAL_URL` | `http://tempo.railway.internal:3200` |

6. Click **Save**
7. Watch for Grafana to redeploy (should finish in 1-2 minutes)

---

## Step 3: Verify It's Working (2 minutes)

After Grafana finishes deploying:

1. Open Grafana: `https://grafana-[your-project].up.railway.app`
2. Login with `admin` / your password
3. Go to **⚙️ (Settings) → Data Sources**
4. **All three should show GREEN CHECKMARK:**
   - [ ] Prometheus - ✅ green
   - [ ] Loki - ✅ green
   - [ ] Tempo - ✅ green

5. If any show ❌ RED:
   - See "DIAGNOSE_CONNECTIVITY.md" for troubleshooting

6. Open a dashboard (e.g., Backend Health)
   - Panels should show DATA (not "No data")
   - Data should refresh every 15 seconds

---

## What Was Fixed

### Problem
- Grafana was trying to connect to `http://prometheus:9090` on Railway
- `prometheus` service name doesn't resolve on Railway
- Should be `http://prometheus.railway.internal:9090` instead

### Solution
- Fixed datasource variable naming (LOKI_URL → LOKI_INTERNAL_URL)
- Cleaned up environment variable overrides in docker-compose
- Added explicit listen addresses to services
- Created guides for Railway deployment

### Result
✅ Services can now communicate on Railway network using `.railway.internal` domains

---

## If You Have Different Service Names

If your Prometheus/Loki/Tempo services have different names on Railway, adjust the URLs accordingly:

| If service is named... | Use this URL |
|------------------------|--------------|
| `prometheus` | `http://prometheus.railway.internal:9090` |
| `my-prometheus` | `http://my-prometheus.railway.internal:9090` |
| `prom-dev` | `http://prom-dev.railway.internal:9090` |

Just replace the service name before `.railway.internal`.

---

## Timeline

- **Now**: Push code changes (git commit & push)
- **2 min**: Set environment variables on Railway
- **2 min**: Grafana redeploys
- **1 min**: Test datasources
- **Total: ~5 minutes** ✅

---

## Need Help?

### If datasources still show RED:
- See: `DIAGNOSE_CONNECTIVITY.md` (step-by-step troubleshooting)

### If you want to understand what changed:
- See: `RAILWAY_DATASOURCE_FIX_SUMMARY.md` (technical details)

### If you want complete deployment guide:
- See: `RAILWAY_DEPLOYMENT_GUIDE.md` (comprehensive guide)

---

## Quick Checklist

```
Before you start:
- [ ] SSH access or Railway Dashboard access
- [ ] Git repository access to push changes

Step 1 (2 min):
- [ ] Run git add/commit/push commands
- [ ] Watch Railway start building

Step 2 (3 min):
- [ ] Open Railway Dashboard
- [ ] Go to Grafana → Settings → Variables
- [ ] Add three environment variables
- [ ] Click Save and wait for redeploy

Step 3 (2 min):
- [ ] Open Grafana UI
- [ ] Check Data Sources - all green? ✅
- [ ] Open dashboard - see data? ✅

Done! 🎉
```

---

## What's Next

Once everything is working:

1. **Monitor for 30 minutes** - watch for stability
2. **Verify data updates** - should refresh every 15 seconds
3. **Check all metrics visible** - fastapi, model health, cache, etc.
4. **Document for team** - let them know it's fixed

---

## After You Complete This

Come back and let me know if:
- ✅ All datasources show green checkmarks
- ✅ Dashboard shows data
- ✅ Everything is working

Then we can verify everything is stable and working correctly!

---

**Time to fix: ~5 minutes**
**Complexity: Easy (just setting environment variables)**
**Impact: Complete fix for "No data" issue** ✅
