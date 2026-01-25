# Setup Complete: Prometheus → Mimir → Grafana Integration

**Status**: ✅ Configuration complete, ready for deployment testing  
**Date**: January 25, 2026  
**Next Action Required**: Set `RAILWAY_ENVIRONMENT=production` on Railway

---

## What Was Accomplished

### 1. Fixed Mimir 502 Gateway Error ✅
- **Problem**: Mimir returning 502 errors, not starting properly
- **Solution**: 
  - Changed kvstore from `memberlist` → `inmemory` (single-instance mode)
  - Added `instance_addr: 127.0.0.1` to all ring configurations
  - Created reliable startup script (`mimir/entrypoint.sh`)
  - Disabled ruler component to prevent startup conflicts
- **Files Modified**:
  - `mimir/Dockerfile`
  - `mimir/entrypoint.sh` (created)
  - `mimir/mimir-railway.yml`
- **Result**: Mimir now starts successfully and responds to `/ready` endpoint

### 2. Configured Prometheus → Mimir Remote Write ✅
- **Configuration**:
  - Added `remote_write` block to `prometheus/prom.yml`
  - Configured with URL placeholder: `MIMIR_URL/api/v1/push`
  - Set queue config for reliable delivery (10k capacity, 50 shards)
  - Set batch size: 2000 samples, 5s deadline
- **Runtime Substitution**:
  - Updated `prometheus/entrypoint.sh` to detect environment
  - If `RAILWAY_ENVIRONMENT` is set → use `http://mimir.railway.internal:9009`
  - Otherwise → use `http://mimir:9009` (Docker Compose)
- **Files Modified**:
  - `prometheus/prom.yml` (lines 13-23)
  - `prometheus/entrypoint.sh` (lines 42-56)
  - `prometheus/Dockerfile` (added diagnostic script)
- **Result**: Prometheus configured to send metrics to Mimir

### 3. Configured Grafana → Mimir Datasource ✅
- **Configuration**:
  - Added Mimir datasource to `grafana/datasources/datasources.yml`
  - Set URL: `${MIMIR_INTERNAL_URL}/prometheus` (Prometheus-compatible endpoint)
  - Configured default `MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009` in Dockerfile
  - Set as queryable datasource (not default)
- **Files Modified**:
  - `grafana/datasources/datasources.yml`
  - `grafana/Dockerfile`
- **Result**: Grafana ready to query Mimir for historical data

### 4. Created Mimir Dashboard ✅
- **Dashboard**: `grafana/dashboards/mimir/mimir.json`
- **Panels**:
  - Ingestion rate (samples/sec)
  - Active series count
  - Query latency (P50, P99)
  - Storage blocks created
  - Memory/CPU usage
  - Compaction status
- **Files Created/Modified**:
  - `grafana/dashboards/mimir/mimir.json`
  - `grafana/provisioning/dashboards/dashboards.yml`
  - `grafana/Dockerfile`
- **Result**: Comprehensive Mimir monitoring dashboard available

### 5. Created Diagnostic Tools ✅
- **Script 1**: `diagnose-prometheus-mimir.sh`
  - Checks environment variables
  - Tests DNS resolution for `mimir.railway.internal`
  - Tests TCP connection to port 9009
  - Tests HTTP endpoints (`/ready`, `/api/v1/push`, `/query`)
  - Analyzes Prometheus remote_write metrics
  - Provides color-coded recommendations
  
- **Script 2**: `test-prometheus-mimir-grafana-flow.sh`
  - Tests full pipeline: Prometheus → Mimir → Grafana
  - Verifies each service is accessible
  - Checks configuration files
  - Tests data ingestion and querying
  - Provides pass/fail status for each check
  
- **Script 3**: `quick-setup.sh`
  - Interactive setup wizard
  - Verifies Railway CLI installation
  - Guides through environment variable setup
  - Runs diagnostics and shows results
  
- **Files Created**:
  - `diagnose-prometheus-mimir.sh`
  - `test-prometheus-mimir-grafana-flow.sh`
  - `quick-setup.sh`
  - All scripts made executable with `chmod +x`
- **Result**: Comprehensive troubleshooting toolkit available

### 6. Created Documentation ✅
- **MIMIR.md**: Complete Mimir reference
  - Architecture overview
  - Configuration details
  - API endpoints and usage examples
  - Deployment guide
  - Troubleshooting section
  
- **PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md**: Railway-specific setup
  - Environment variable setup
  - Verification steps
  - Troubleshooting common Railway issues
  
- **DATA_FLOW_VERIFICATION.md**: Data flow verification guide
  - Current configuration status
  - Manual verification procedures
  - Architecture diagrams
  - Expected behavior at each step
  
- **PROMETHEUS_MIMIR_CONNECTION_FIXES.md**: Quick troubleshooting
  - Most likely causes (ranked by probability)
  - Quick tests to run
  - Step-by-step fixes
  - Common scenarios and solutions
  
- **NEXT_STEPS.md**: Action plan for deployment
  - Step-by-step setup instructions
  - Verification checklist
  - Timeline expectations
  - Troubleshooting flowchart
  
- **SETUP_COMPLETE.md** (this file): Summary and next actions

### 7. Updated Test Infrastructure ✅
- **Backend Tests**: `tests/test_stack_configuration.py`
  - Added `TestMimirConfiguration` class
  - 13 tests covering: config validation, API endpoints, startup script, dashboard
  
- **CI/CD Workflows**:
  - `.github/workflows/test-production.yml` - Added Mimir validation
  - `.github/workflows/test-staging.yml` - Added Mimir validation
  
- **Result**: Automated testing for Mimir configuration

---

## Current Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Railway Internal Network                                │
│                                                           │
│  ┌─────────────────┐                                     │
│  │   Prometheus    │  Scrapes metrics every 15s          │
│  │   :9090         │                                     │
│  └────────┬────────┘                                     │
│           │                                              │
│           │ remote_write (every 30s)                     │
│           │ http://mimir.railway.internal:9009/api/v1/push│
│           │                                              │
│           ▼                                              │
│  ┌─────────────────┐                                     │
│  │     Mimir       │  Long-term storage (30 days)       │
│  │     :9009       │  - Ingests samples                 │
│  │                 │  - Compacts blocks                 │
│  │   Components:   │  - Handles queries                 │
│  │   - Distributor │                                     │
│  │   - Ingester    │                                     │
│  │   - Querier     │                                     │
│  │   - Compactor   │                                     │
│  └────────▲────────┘                                     │
│           │                                              │
│           │ query: /prometheus/api/v1/query              │
│           │ http://mimir.railway.internal:9009/prometheus│
│           │                                              │
│  ┌────────┴────────┐                                     │
│  │    Grafana      │  Visualizes metrics                │
│  │    :3000        │  - Queries Prometheus (recent)     │
│  │                 │  - Queries Mimir (historical)      │
│  │  Datasources:   │                                     │
│  │  - Prometheus   │  (default, for recent data)        │
│  │  - Mimir        │  (for historical analysis)         │
│  └─────────────────┘                                     │
│                                                           │
└──────────────────────────────────────────────────────────┘

External Access:
- Prometheus: https://prometheus-{project}.railway.app
- Mimir: https://mimir-{project}.railway.app
- Grafana: https://grafana-{project}.railway.app
```

---

## What's Working vs What's Not

### ✅ Working (Code/Configuration)
1. **Mimir Service**: Starts successfully, responds to health checks
2. **Prometheus Configuration**: Has remote_write block with correct placeholder
3. **Prometheus Entrypoint**: Has logic to substitute Railway URLs
4. **Grafana Datasource**: Configured to connect to Mimir
5. **Mimir Dashboard**: Created and provisioned in Grafana
6. **Diagnostic Tools**: Scripts ready to run
7. **Documentation**: Comprehensive guides available

### ❓ Needs Verification (Runtime)
1. **RAILWAY_ENVIRONMENT Variable**: Not confirmed if set on Prometheus service
2. **Prometheus → Mimir Connection**: Depends on environment variable
3. **Data Flow**: Will work once environment variable is set
4. **Grafana → Mimir Queries**: Will work once data is flowing

### ⚠️ Known Limitation
- **Single-Instance Mode**: Mimir is configured for single-instance (not clustered)
  - Reason: Railway doesn't support Kubernetes (memberlist kvstore requires clustering)
  - Trade-off: No high availability, but simpler setup and lower cost
  - Acceptable for: Development, staging, small production deployments
  - Not acceptable for: Large-scale production requiring HA

---

## Next Steps: Deployment & Verification

### Immediate Action Required (5 minutes)

#### 1. Set Environment Variable on Railway
**Railway Dashboard:**
1. Go to: https://railway.app/dashboard
2. Select: Your GatewayZ project
3. Click: **Prometheus** service
4. Click: **Variables** tab
5. Click: **+ New Variable**
6. Enter:
   - **Key**: `RAILWAY_ENVIRONMENT`
   - **Value**: `production`
7. Click: **Add**
8. **Wait 2-3 minutes** for automatic redeploy

**Why**: This triggers the entrypoint script to use Railway internal networking (`mimir.railway.internal:9009`) instead of Docker Compose hostname (`mimir:9009`).

#### 2. Rebuild Prometheus Image (If Using Railway GitHub Integration)
If you're deploying from GitHub (recommended):
1. Commit changes: `git add . && git commit -m "feat: add Mimir integration with diagnostics"`
2. Push: `git push origin main` (or your deployment branch)
3. Railway will automatically rebuild and deploy

If deploying manually:
1. Build locally: `docker build -t prometheus:latest railway-grafana-stack/prometheus/`
2. Push to Railway: `railway up --service prometheus`

### Verification Steps (After 5 minutes)

#### Step 1: Check Prometheus Logs ✅
**Expected Output:**
```
===========================================
Prometheus Configuration
===========================================
MIMIR_URL: http://mimir.railway.internal:9009
MIMIR_TARGET: mimir.railway.internal:9009
RAILWAY_ENVIRONMENT: production
===========================================
Configured remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
```

**How to Check:**
- Railway Dashboard → Prometheus → Logs
- Search for: "MIMIR_URL"

#### Step 2: Run Diagnostic Script (Optional, but recommended) 🔍
```bash
# Option A: Using Railway CLI
cd railway-grafana-stack
railway run --service prometheus bash /app/diagnose-prometheus-mimir.sh

# Option B: Using quick-setup script
./quick-setup.sh
```

**Expected Output:**
- ✓ DNS resolution successful
- ✓ TCP connection successful
- ✓ Mimir /ready endpoint returns 200
- ✓ Prometheus remote_write configured
- ✓ Samples being sent to Mimir

#### Step 3: Check Prometheus Remote Write Status 📊
Visit: `https://prometheus-{project}.railway.app`

1. Go to: **Status** → **TSDB Status**
2. Look for: **Remote Write** section
3. Verify:
   - **Samples Sent**: > 0 (increasing)
   - **Samples Failed**: 0
   - **Shards**: 1-10 (active)

**Query to run:**
```promql
prometheus_remote_storage_samples_total
```
Should show increasing value over time.

#### Step 4: Check Mimir Ingestion 📥
On Prometheus UI, run:
```promql
cortex_ingester_ingested_samples_total
```

**Expected**: 
- Should return data points
- Value should be > 0 and increasing
- Indicates Mimir is successfully ingesting samples

**Alternative Query:**
```promql
cortex_ingester_active_series
```
Shows number of active time series in Mimir (should be > 1000 after 5 minutes).

#### Step 5: Test Grafana → Mimir Connection 📈
1. Visit: `https://grafana-{project}.railway.app`
2. Click: **Explore** (compass icon in sidebar)
3. Select: **Mimir** datasource (dropdown at top)
4. Enter query: `up`
5. Click: **Run query**

**Expected**:
- Should show graph with time series data
- Data points from past 30 seconds to 30 days (depending on retention)
- Multiple series for different jobs (prometheus, gatewayz_production, etc.)

#### Step 6: Check Mimir Dashboard 📊
1. In Grafana, click: **Dashboards** (four squares icon)
2. Search: "Mimir"
3. Click: **Mimir Monitoring** dashboard

**Expected Panels:**
- **Ingestion Rate**: > 100 samples/sec
- **Active Series**: > 1000
- **Query Latency**: < 100ms (P99)
- **Storage Blocks**: Increasing over time
- **Resource Usage**: Memory and CPU graphs

---

## Troubleshooting Guide

### Problem: MIMIR_URL still shows `http://mimir:9009` (wrong)

**Diagnosis:**
```bash
railway logs --service prometheus | grep "MIMIR_URL"
```
Shows: `MIMIR_URL: http://mimir:9009`

**Cause**: Environment variable not set or not picked up

**Solution:**
1. Verify variable is set: Railway → Prometheus → Variables → `RAILWAY_ENVIRONMENT=production`
2. Force redeploy: Railway → Prometheus → Settings → **Redeploy**
3. Wait 2 minutes, check logs again

### Problem: `dial tcp: lookup mimir.railway.internal: no such host`

**Diagnosis:**
```bash
railway run --service prometheus -- nslookup mimir.railway.internal
```
Returns: `server can't find mimir.railway.internal: NXDOMAIN`

**Cause**: Railway internal networking issue

**Solutions:**
1. Check Mimir service is running: Railway → Mimir → Status (should show "Running")
2. Check Mimir service name: Railway → Mimir → Settings → Service Name (should be exactly "mimir")
3. Try external URL temporarily:
   ```bash
   # Set in Prometheus variables
   MIMIR_INTERNAL_URL=https://mimir-{project}.railway.app
   ```
4. Contact Railway support if internal networking is broken

### Problem: `Connection refused to mimir.railway.internal:9009`

**Diagnosis:**
```bash
railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready
```
Returns: `curl: (7) Failed to connect to mimir.railway.internal port 9009: Connection refused`

**Cause**: Mimir not listening on port 9009

**Solution:**
1. Check Mimir logs: Railway → Mimir → Logs
2. Look for: `level=info msg="server listening on [::]:9009"`
3. If not found:
   - Check `mimir-railway.yml` has `http_listen_port: 9009`
   - Restart Mimir: Railway → Mimir → Settings → Restart
4. If still failing:
   - Check Mimir startup script: `mimir/entrypoint.sh`
   - Look for startup errors in logs

### Problem: Samples Sent = 0, No Errors

**Diagnosis:**
```bash
# On Prometheus UI
prometheus_remote_storage_samples_total
# Returns 0
```

**Cause**: Prometheus not scraping any targets

**Solution:**
1. Check targets: Prometheus → Status → Targets
2. Verify targets are **UP** (green status)
3. If targets are **DOWN**:
   - Check target URLs are accessible
   - Verify bearer tokens are correct
   - Check firewall rules
4. If targets are **UP** but no samples:
   - Check scrape interval (15s) has passed
   - Look for scrape errors in target list
   - Verify metrics endpoint returns data

### Problem: Grafana Can't Query Mimir

**Diagnosis:**
In Grafana: Configuration → Data Sources → Mimir → **Test** button
Returns: ❌ Error connecting to data source

**Cause**: Grafana → Mimir connection issue

**Solution:**
1. Check Mimir is accessible from Grafana container:
   ```bash
   railway run --service grafana -- curl http://mimir.railway.internal:9009/ready
   ```
2. Check datasource URL in Grafana:
   - Should be: `http://mimir.railway.internal:9009/prometheus`
   - NOT: `http://mimir.railway.internal:9009` (missing `/prometheus`)
3. Verify environment variable:
   ```bash
   railway run --service grafana -- env | grep MIMIR
   ```
   Should show: `MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009`
4. Restart Grafana: Railway → Grafana → Settings → Restart

---

## Performance Expectations

### Prometheus → Mimir Remote Write
- **Interval**: Every 30 seconds (configurable)
- **Batch Size**: Up to 2000 samples per batch
- **Expected Rate**: 100-10,000 samples/sec (depends on scrape targets)
- **Latency**: < 100ms for write requests
- **Failure Rate**: < 0.01% (should be near zero)

### Mimir Ingestion
- **Ingestion Rate**: Should match Prometheus send rate
- **Active Series**: 1,000-100,000+ (depends on targets and metrics)
- **Query Latency**: < 100ms for recent data, < 500ms for historical
- **Storage Growth**: ~1-10 MB/day per 1000 active series

### Grafana Queries
- **Recent Data (Prometheus)**: < 100ms
- **Historical Data (Mimir)**: < 500ms
- **Large Range Queries**: 1-5s (e.g., 30-day aggregations)

---

## Retention & Storage

### Current Configuration
- **Prometheus Local Storage**: 2 hours (default)
- **Mimir Storage**: 30 days (720 hours)
- **Compaction**: Automatic (runs every 2 hours)

### Storage Estimates
| Active Series | Daily Growth | 30-Day Total |
|--------------|-------------|--------------|
| 1,000 | ~5 MB | ~150 MB |
| 10,000 | ~50 MB | ~1.5 GB |
| 100,000 | ~500 MB | ~15 GB |

### Adjusting Retention
Edit `mimir/mimir-railway.yml`:
```yaml
limits:
  ingestion_rate: 100000
  ingestion_burst_size: 200000
  max_global_series_per_user: 0
  
compactor:
  retention_enabled: true
  retention_delete_delay: 720h  # Change this value
```

To increase retention:
- `retention_delete_delay: 2160h` = 90 days
- `retention_delete_delay: 4320h` = 180 days
- `retention_delete_delay: 8760h` = 1 year

**Note**: Longer retention = more storage required.

---

## Monitoring & Alerting

### Key Metrics to Monitor

#### Prometheus Remote Write
```promql
# Samples sent per second
rate(prometheus_remote_storage_samples_total[5m])

# Failed samples
rate(prometheus_remote_storage_samples_failed_total[5m])

# Queue length (should stay below 10k)
prometheus_remote_storage_samples_pending

# Shards (should be 1-50)
prometheus_remote_storage_shards
```

#### Mimir Ingestion
```promql
# Ingestion rate
rate(cortex_ingester_ingested_samples_total[5m])

# Active series
cortex_ingester_active_series

# Query latency (P99 should be < 500ms)
histogram_quantile(0.99, rate(cortex_request_duration_seconds_bucket[5m]))

# Memory usage
cortex_ingester_memory_series
```

### Recommended Alerts
Create these alerts in `prometheus/alert.rules.yml`:

```yaml
# Mimir not receiving data
- alert: MimirNoIngestion
  expr: rate(cortex_ingester_ingested_samples_total[5m]) == 0
  for: 5m
  annotations:
    summary: Mimir is not ingesting samples
    description: No samples ingested in the last 5 minutes

# Remote write failing
- alert: PrometheusRemoteWriteFailing
  expr: rate(prometheus_remote_storage_samples_failed_total[5m]) > 0
  for: 5m
  annotations:
    summary: Prometheus remote write failing
    description: {{ $value }} samples/sec failing to write to Mimir

# Mimir query latency high
- alert: MimirQueryLatencyHigh
  expr: histogram_quantile(0.99, rate(cortex_request_duration_seconds_bucket[5m])) > 1
  for: 10m
  annotations:
    summary: Mimir query latency high
    description: P99 latency is {{ $value }}s (threshold: 1s)
```

---

## Cost & Resource Usage

### Railway Pricing (Estimated)
- **Prometheus**: ~$2-5/month (512MB RAM, 0.5 vCPU)
- **Mimir**: ~$5-15/month (1GB RAM, 1 vCPU, depends on storage)
- **Grafana**: ~$2-5/month (512MB RAM, 0.5 vCPU)

**Total**: ~$10-25/month for monitoring stack

### Optimization Tips
1. **Reduce Scrape Frequency**: 15s → 30s saves ~50% samples
2. **Filter Unnecessary Metrics**: Use `metric_relabel_configs`
3. **Reduce Retention**: 30 days → 14 days saves ~50% storage
4. **Use Recording Rules**: Pre-aggregate expensive queries
5. **Limit Active Series**: Monitor `cortex_ingester_active_series`, set limits if growing too fast

---

## Scaling Considerations

### Current Setup (Single-Instance)
- **Good for**: 
  - Development/staging environments
  - < 100,000 active series
  - < 10,000 samples/sec ingestion rate
  - Single region deployment

### When to Scale to Multi-Instance
- **Active series** > 100,000
- **Ingestion rate** > 10,000 samples/sec
- **Query latency** consistently > 1s
- **High availability** required (99.99% uptime)
- **Multi-region** deployment needed

### How to Scale (Future)
1. **Move to Kubernetes**: Mimir is designed for K8s
2. **Use Memberlist KVStore**: Enable clustering
3. **Separate Components**: Distributor, Ingester, Querier on different pods
4. **Add Load Balancer**: Distribute requests across instances
5. **Use Object Storage**: S3/GCS for block storage (instead of local filesystem)

---

## Security Considerations

### Current Security (Basic)
- ✅ **Railway Internal Networking**: Services communicate via private network
- ✅ **No Authentication**: Mimir has no auth (acceptable for internal services)
- ✅ **Bearer Tokens**: Prometheus uses bearer tokens for scraping external APIs
- ✅ **HTTPS Termination**: Railway provides SSL for external access

### Recommended Improvements (Production)
- [ ] **Add Basic Auth to Mimir**: Protect `/api/v1/push` endpoint
- [ ] **Enable Multi-Tenancy**: Use `X-Scope-OrgID` header for tenant isolation
- [ ] **Network Policies**: Restrict which services can access Mimir
- [ ] **Rate Limiting**: Prevent abuse of Mimir API
- [ ] **Audit Logging**: Log all write/query operations

### Example: Adding Basic Auth to Mimir
Edit `mimir/mimir-railway.yml`:
```yaml
server:
  http_listen_port: 9009
  grpc_listen_port: 9095
  log_level: info
  
  # Add basic auth
  http_server_write_timeout: 1m
  http_server_read_timeout: 1m
  
auth:
  type: basic
  basic_auth:
    username: prometheus
    password_file: /etc/mimir/password
```

Then update Prometheus remote_write:
```yaml
remote_write:
  - url: http://mimir.railway.internal:9009/api/v1/push
    basic_auth:
      username: prometheus
      password: your-secure-password
```

---

## References & Resources

### Official Documentation
- **Grafana Mimir**: https://grafana.com/docs/mimir/latest/
- **Prometheus Remote Write**: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#remote_write
- **Grafana Datasources**: https://grafana.com/docs/grafana/latest/datasources/

### Project Documentation
- **MIMIR.md**: Complete Mimir reference guide
- **PROMETHEUS_MIMIR_CONNECTION_RAILWAY.md**: Railway-specific setup
- **DATA_FLOW_VERIFICATION.md**: Verification procedures
- **PROMETHEUS_MIMIR_CONNECTION_FIXES.md**: Troubleshooting guide
- **NEXT_STEPS.md**: Action plan for deployment

### Diagnostic Tools
- **diagnose-prometheus-mimir.sh**: Connection diagnostic script
- **test-prometheus-mimir-grafana-flow.sh**: Full pipeline test
- **quick-setup.sh**: Interactive setup wizard

### Configuration Files
- **prometheus/prom.yml**: Prometheus config (lines 13-23: remote_write)
- **prometheus/entrypoint.sh**: URL substitution logic (lines 42-56)
- **mimir/mimir-railway.yml**: Mimir single-instance config
- **mimir/entrypoint.sh**: Mimir startup script
- **grafana/datasources/datasources.yml**: Grafana datasources
- **grafana/dashboards/mimir/mimir.json**: Mimir dashboard

---

## Success Checklist

After completing deployment, verify all these are true:

### Configuration ✅
- [x] Mimir service starts without errors
- [x] Prometheus has remote_write configuration
- [x] Prometheus entrypoint substitutes URLs correctly
- [x] Grafana has Mimir datasource configured
- [x] Diagnostic scripts are executable and in Prometheus image

### Environment ⚠️ (Needs Verification)
- [ ] `RAILWAY_ENVIRONMENT=production` set on Prometheus service
- [ ] Prometheus logs show `MIMIR_URL: http://mimir.railway.internal:9009`
- [ ] Prometheus logs show `RAILWAY_ENVIRONMENT: production`

### Data Flow ⚠️ (Needs Verification After Setup)
- [ ] Prometheus scrapes targets successfully (all green)
- [ ] Prometheus remote_write shows samples sent > 0
- [ ] Mimir receives samples (cortex_ingester_ingested_samples_total > 0)
- [ ] Grafana can query Mimir datasource (test returns ✅)
- [ ] Mimir dashboard shows data in all panels

### Performance ⚠️ (Needs Monitoring)
- [ ] Remote write latency < 100ms
- [ ] Mimir query latency < 500ms (P99)
- [ ] No failed samples in Prometheus
- [ ] Mimir ingestion rate matches Prometheus send rate
- [ ] Resource usage within budget (< $25/month)

---

## Contact & Support

**Project**: Gateway Z Universal AI Inference Platform  
**Monitoring Stack Version**: Prometheus v3.2.1 + Mimir 2.x + Grafana 11.x  
**Deployment Platform**: Railway  

**For Issues**:
1. Check logs first: Railway → Service → Logs
2. Run diagnostic: `./quick-setup.sh` or `diagnose-prometheus-mimir.sh`
3. Review documentation: NEXT_STEPS.md, PROMETHEUS_MIMIR_CONNECTION_FIXES.md
4. Check Railway status: https://railway.statuspage.io/

---

**Last Updated**: January 25, 2026  
**Status**: ✅ Configuration Complete, Ready for Deployment Testing  
**Next Review**: After successful deployment and 24-hour monitoring period

---

## Quick Commands Reference

```bash
# Setup
./quick-setup.sh                      # Interactive setup wizard

# Check logs
railway logs --service prometheus     # Prometheus logs
railway logs --service mimir          # Mimir logs
railway logs --service grafana        # Grafana logs

# Run diagnostics
railway run --service prometheus bash /app/diagnose-prometheus-mimir.sh

# Test connectivity
railway run --service prometheus -- curl http://mimir.railway.internal:9009/ready
railway run --service prometheus -- nslookup mimir.railway.internal

# Check metrics
curl https://prometheus-{project}.railway.app/api/v1/query?query=prometheus_remote_storage_samples_total
curl https://prometheus-{project}.railway.app/api/v1/query?query=cortex_ingester_ingested_samples_total

# Force redeploy
railway redeploy --service prometheus
railway redeploy --service mimir
railway redeploy --service grafana
```

---

🎉 **Configuration is complete! Now set `RAILWAY_ENVIRONMENT=production` on Railway to enable the data flow.**
