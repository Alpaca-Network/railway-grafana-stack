# Railway Mimir Fix - Quick Instructions

**Issue**: Mimir crashes on Railway with config error  
**Status**: ✅ FIXED - Deploy immediately  
**Commit**: `a32d414`

---

## ⚡ Quick Fix Summary

The Mimir configuration had an invalid field (`query_frontend_address`) that doesn't work in monolithic mode on Railway. This has been fixed.

### What Was Fixed

1. ✅ Removed invalid `query_frontend_address` from config
2. ✅ Created Railway-optimized config (`mimir-railway.yml`)
3. ✅ Updated Dockerfile to use Railway config by default
4. ✅ Added Railway deployment guide

---

## 🚀 Deploy to Railway Now

### Option 1: Railway Auto-Deploy (Recommended)

If your Railway service is connected to GitHub:

1. **Railway will auto-deploy** the latest commit (`a32d414`)
2. **Monitor deployment** in Railway dashboard
3. **Check logs** for successful start:
   ```
   level=info msg="Mimir started"
   level=info msg="Starting server" service=server
   ```

### Option 2: Manual Deploy

If auto-deploy is not enabled:

1. **Trigger Deployment**:
   - Railway Dashboard → Mimir Service
   - Click "Deploy" or "Redeploy"

2. **Select Latest Commit**: `a32d414`

---

## ✅ Verify Deployment

### 1. Check Mimir Health

```bash
# Railway will provide a public URL, use that:
curl https://mimir-production-XXXX.up.railway.app/ready

# Expected response: "ready"
```

### 2. Check Logs

In Railway Dashboard:
- Go to Mimir service
- Click "Logs"
- Look for:
  ```
  ✅ level=info msg="Mimir started"
  ✅ level=info msg="Starting server"
  ❌ No "error" or "fatal" messages
  ```

### 3. Test Query

```bash
curl "https://mimir-production-XXXX.up.railway.app/prometheus/api/v1/labels"

# Should return JSON with metric labels
```

---

## 🔧 Railway Service Configuration

### Required Settings

**In Railway Dashboard → Mimir Service**:

1. **Root Directory**: Leave empty (or `/mimir` if needed)
2. **Build Command**: (Use Dockerfile - default)
3. **Start Command**: (Use Dockerfile CMD - default)
4. **Port**: `9009`
5. **Health Check**:
   - Path: `/ready`
   - Timeout: 10s
   - Interval: 30s

### Recommended Resources

- **Memory**: 1024 MB (1 GB) minimum
- **CPU**: 1 vCPU

### Environment Variables (Optional)

No environment variables required! The Dockerfile defaults to Railway config.

**If you want to override** (not needed):
```
CONFIG_FILE=/etc/mimir/mimir-railway.yml
```

---

## 🔗 Connect Other Services

### Update Prometheus to Use Mimir

**In `prometheus/prom.yml`** (should already be configured):

```yaml
remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
    name: mimir-remote-write
    remote_timeout: 30s
```

**Railway Internal URL**: `mimir.railway.internal:9009`

### Update Grafana Datasource

**In `grafana/provisioning/datasources/mimir.yml`**:

```yaml
datasources:
  - name: Mimir
    type: prometheus
    url: http://mimir.railway.internal:9009
```

---

## 🐛 If Mimir Still Crashes

### Check Logs First

Railway Dashboard → Mimir → Logs

**Look for**:
- Config parsing errors
- Port binding issues
- Memory issues
- Connection errors

### Common Issues & Solutions

#### Issue: "config file not found"

**Solution**: Rebuild with latest code
```bash
Railway Dashboard → Mimir → Settings → Redeploy
```

#### Issue: "Out of memory"

**Solution**: Increase memory limit
```bash
Railway Dashboard → Mimir → Settings → Resources → Memory: 1024 MB
```

#### Issue: "Health check failing"

**Solution**: Increase health check initial delay
```bash
Railway Dashboard → Mimir → Settings → Health Check
Initial Delay: 60 seconds
```

#### Issue: "Cannot bind to port"

**Solution**: Check port configuration
```bash
Railway Dashboard → Mimir → Settings
Port should be: 9009
```

---

## 📊 What Changed in the Code

### Files Modified

1. **`mimir/mimir.yml`** (local config)
   ```yaml
   # ❌ Removed this (invalid in monolithic mode):
   querier:
     query_frontend_address: localhost:9095
   
   # ✅ Replaced with:
   querier:
     max_concurrent: 20
   ```

2. **`mimir/mimir-railway.yml`** (NEW - Railway config)
   - Listens on `0.0.0.0` (required for Railway)
   - Simplified memberlist (single instance)
   - No frontend/query scheduler config

3. **`mimir/Dockerfile`**
   - Copies both config files
   - Defaults to `mimir-railway.yml` for Railway
   - Increased health check start period to 60s

---

## 🎯 Expected Behavior After Fix

### Immediate (after deployment)

1. ✅ Mimir container starts successfully
2. ✅ Health check passes after ~60 seconds
3. ✅ `/ready` endpoint returns "ready"
4. ✅ No config parsing errors in logs

### After Prometheus Connects (~5 minutes)

1. ✅ Prometheus successfully writes metrics to Mimir
2. ✅ Mimir shows ingested metrics
3. ✅ Grafana can query Mimir datasource
4. ✅ No errors in Prometheus remote_write logs

---

## 📞 Need More Help?

### Detailed Guide

See **`RAILWAY_MIMIR_DEPLOYMENT.md`** for:
- Complete deployment steps
- Troubleshooting guide
- Configuration examples
- Verification procedures

### Quick Commands

```bash
# Test Mimir health
curl https://your-mimir.railway.app/ready

# Query Mimir
curl "https://your-mimir.railway.app/prometheus/api/v1/query?query=up"

# Check Prometheus connection (from Railway dashboard)
Railway → Prometheus → Logs | Search: "mimir" or "remote_write"
```

---

## ✅ Summary

**Problem**: Mimir config had invalid `query_frontend_address` field  
**Solution**: Created Railway-compatible config without that field  
**Status**: ✅ Fixed and pushed to main  
**Action**: Railway will auto-deploy or manually trigger deployment  

**The fix is live. Your Mimir service should now start successfully on Railway!** 🎉

---

**Last Updated**: January 17, 2026  
**Commit**: `a32d414`  
**Branch**: `main`  
**Status**: ✅ Ready for Deployment
