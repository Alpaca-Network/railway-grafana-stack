# Railway Mimir Deployment Guide

**Issue**: Mimir container crashes on Railway with config parsing error  
**Solution**: Railway-optimized configuration  
**Status**: ✅ Fixed

---

## 🐛 Problem

When deploying to Railway, Mimir crashes with:
```
error loading config from /etc/mimir/mimir.yml: Error parsing config file: 
yaml: unmarshal errors:
  line 38: field query_frontend_address not found in type querier.Config
```

**Root Cause**: The `query_frontend_address` field is only available in microservices mode, not monolithic mode (which we use for single-instance deployment).

---

## ✅ Solution Applied

### 1. Fixed Configuration Files

**Two configurations provided**:

1. **`mimir.yml`** - For local development (docker-compose)
   - Simplified, removed invalid fields
   - Works with docker-compose networking

2. **`mimir-railway.yml`** - For Railway deployment (default)
   - Optimized for Railway's networking
   - Listens on `0.0.0.0` for Railway's proxy
   - Simplified memberlist (single instance)
   - No query frontend configuration

### 2. Updated Dockerfile

**Dockerfile now**:
- Includes both config files
- Defaults to Railway config (`mimir-railway.yml`)
- Can override with `CONFIG_FILE` environment variable
- Increased health check start period (60s for Railway)

### 3. Configuration Changes

**Removed from config**:
```yaml
# ❌ Removed - not valid in monolithic mode
querier:
  query_frontend_address: localhost:9095

# ❌ Removed - causes issues in single instance
frontend:
  scheduler_address: ""
  results_cache:
    backend: memcached
```

**Added to Railway config**:
```yaml
# ✅ Server listens on all interfaces
server:
  http_listen_address: 0.0.0.0
  grpc_listen_address: 0.0.0.0

# ✅ Simplified memberlist for single instance
memberlist:
  bind_port: 7946
  join_members: []  # No other instances to join

# ✅ Simple querier config
querier:
  max_concurrent: 20
```

---

## 🚀 Railway Deployment Steps

### 1. Push Updated Code

```bash
cd railway-grafana-stack
git add mimir/
git commit -m "fix: Railway-compatible Mimir configuration"
git push origin main
```

### 2. Configure Railway Service

**In Railway Dashboard**:

1. **Create New Service** (if not exists):
   - Name: `mimir`
   - Source: GitHub repo (`railway-grafana-stack`)
   - Root Directory: `/mimir`

2. **Set Environment Variables**:
   ```
   CONFIG_FILE=/etc/mimir/mimir-railway.yml
   ```
   (Optional - this is the default)

3. **Configure Service Settings**:
   - **Port**: `9009` (HTTP API)
   - **Health Check Path**: `/ready`
   - **Start Command**: (Use default from Dockerfile)

4. **Set Resource Limits**:
   - **Memory**: 1024 MB (recommended)
   - **CPU**: 1 vCPU

### 3. Configure Networking

**For Internal Communication** (Prometheus → Mimir):

1. **Get Mimir's Internal URL**:
   - Railway provides: `mimir.railway.internal`
   - Port: `9009`

2. **Update Prometheus Config** (`prometheus/prom.yml`):
   ```yaml
   remote_write:
     - url: http://mimir.railway.internal:9009/api/v1/push
       name: mimir-remote-write
   ```

3. **Update Grafana Datasource** (`grafana/provisioning/datasources/mimir.yml`):
   ```yaml
   datasources:
     - name: Mimir
       type: prometheus
       url: http://mimir.railway.internal:9009
   ```

### 4. Deploy & Verify

**After deployment**:

1. **Check Mimir Logs**:
   ```
   Railway Dashboard → Mimir Service → Logs
   ```
   
   Look for:
   ```
   level=info msg="Mimir started"
   level=info msg="Starting server" service=server
   ```

2. **Test Health Endpoint**:
   ```bash
   # Using Railway's public URL
   curl https://mimir-production-xxxx.up.railway.app/ready
   
   # Should return: "ready"
   ```

3. **Verify Prometheus Remote Write**:
   ```bash
   # Check Prometheus logs
   Railway Dashboard → Prometheus Service → Logs
   
   # Look for successful remote write:
   level=info component=remote msg="Remote write successful"
   ```

4. **Test Mimir Query**:
   ```bash
   # Query Mimir directly
   curl "https://mimir-production-xxxx.up.railway.app/prometheus/api/v1/query?query=up"
   ```

---

## 🔧 Troubleshooting Railway Deployment

### Issue: Container Still Crashing

**Check**:
```bash
# View Mimir logs in Railway dashboard
Railway → Mimir → Logs
```

**Possible Causes**:

1. **Config File Not Found**:
   - Solution: Verify `mimir-railway.yml` is in Docker image
   - Build logs should show: `COPY mimir-railway.yml ...`

2. **Port Binding Issue**:
   - Solution: Ensure Railway has port `9009` exposed
   - Check service settings in Railway dashboard

3. **Memory Limit**:
   - Solution: Increase memory to 1024 MB minimum
   - Railway → Mimir → Settings → Resources

### Issue: Prometheus Can't Connect to Mimir

**Check Internal Networking**:

1. **Verify Service Name**:
   ```bash
   # In Railway, services communicate via:
   [service-name].railway.internal
   ```

2. **Check Prometheus Config**:
   ```yaml
   # Should use Railway internal URL
   remote_write:
     - url: http://mimir.railway.internal:9009/api/v1/push
   ```

3. **Test Connectivity** (from Prometheus container):
   ```bash
   # Railway exec into Prometheus
   wget -O- http://mimir.railway.internal:9009/ready
   ```

### Issue: Health Check Failing

**Adjust Health Check** in Railway:

1. **Path**: `/ready`
2. **Timeout**: 10 seconds
3. **Interval**: 30 seconds
4. **Initial Delay**: 60 seconds (important!)

**Why 60s initial delay?**
- Mimir needs time to initialize
- Loads blocks from storage
- Establishes memberlist

---

## 📊 Verify Mimir is Working

### 1. Check Mimir Metrics

```bash
# Get Mimir's own metrics
curl https://mimir-production-xxxx.up.railway.app/metrics

# Should show Mimir internal metrics
```

### 2. Check Ingestion

```bash
# Check if Mimir is receiving data
curl "https://mimir-production-xxxx.up.railway.app/prometheus/api/v1/labels"

# Should return list of metric labels
```

### 3. Query Data

```bash
# Query recent data
curl "https://mimir-production-xxxx.up.railway.app/prometheus/api/v1/query?query=up"

# Should return time series data
```

### 4. Check Grafana Connection

1. Open Grafana in Railway
2. Go to **Configuration → Data Sources**
3. Find **Mimir** datasource
4. Click **Save & Test**
5. Should see: ✅ "Data source is working"

---

## 🔐 Railway Environment Variables

**Required Variables**:

| Variable | Value | Description |
|----------|-------|-------------|
| `CONFIG_FILE` | `/etc/mimir/mimir-railway.yml` | Config file path (optional, this is default) |

**Optional Variables**:

| Variable | Value | Description |
|----------|-------|-------------|
| `PORT` | `9009` | Railway auto-detects from Dockerfile |

---

## 📁 File Changes Summary

### Files Modified

1. **`mimir/mimir.yml`**
   - Removed `query_frontend_address` (invalid in monolithic mode)
   - Simplified frontend configuration
   - Works for local docker-compose

2. **`mimir/mimir-railway.yml`** (NEW)
   - Railway-optimized configuration
   - Listens on `0.0.0.0` for Railway proxy
   - Simplified memberlist for single instance
   - Default configuration for Railway deployment

3. **`mimir/Dockerfile`**
   - Copies both config files
   - Defaults to `mimir-railway.yml`
   - Increased health check start period to 60s
   - Supports `CONFIG_FILE` env var override

### Files Created

4. **`RAILWAY_MIMIR_DEPLOYMENT.md`** (this file)
   - Complete Railway deployment guide
   - Troubleshooting steps
   - Verification procedures

---

## 🎯 Quick Railway Deployment Checklist

Before deploying to Railway:

- [ ] Code pushed to GitHub
- [ ] Mimir service created in Railway
- [ ] Environment variables set (if needed)
- [ ] Port `9009` exposed
- [ ] Health check configured (`/ready`)
- [ ] Memory set to 1024 MB minimum
- [ ] Prometheus configured with Railway internal URL
- [ ] Grafana datasource uses Railway internal URL

After deployment:

- [ ] Check Mimir logs (no errors)
- [ ] Test `/ready` endpoint
- [ ] Verify Prometheus remote write working
- [ ] Test Grafana Mimir datasource
- [ ] Query Mimir for data

---

## 🔗 Railway Internal URLs

**For Service Communication**:

```yaml
# Mimir (from Prometheus)
http://mimir.railway.internal:9009

# Prometheus (from Grafana)
http://prometheus.railway.internal:9090

# Grafana (public)
https://grafana-production-xxxx.up.railway.app
```

**Update These Files**:

1. `prometheus/prom.yml`:
   ```yaml
   remote_write:
     - url: http://mimir.railway.internal:9009/api/v1/push
   ```

2. `grafana/provisioning/datasources/mimir.yml`:
   ```yaml
   url: http://mimir.railway.internal:9009
   ```

---

## 📞 Need Help?

### Common Commands

```bash
# View Mimir logs
Railway Dashboard → Mimir → Logs

# Test health endpoint
curl https://your-mimir.railway.app/ready

# Query Mimir
curl "https://your-mimir.railway.app/prometheus/api/v1/query?query=up"

# Check Prometheus connection
Railway Dashboard → Prometheus → Logs | grep mimir
```

### References

- [Mimir Monolithic Mode](https://grafana.com/docs/mimir/latest/references/architecture/deployment-modes/#monolithic-mode)
- [Railway Internal Networking](https://docs.railway.app/reference/private-networking)
- [Mimir Configuration](https://grafana.com/docs/mimir/latest/configure/)

---

**Status**: ✅ Ready for Railway Deployment  
**Config**: Railway-optimized  
**Last Updated**: January 17, 2026
