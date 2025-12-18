# Railway Deployment Quick Start

## Prerequisites
- Railway account with project access
- GitHub repository connected to Railway
- `staging/models-and-fixes` branch pushed to GitHub

---

## Step-by-Step Railway Deployment

### Step 1: Connect GitHub Repository
1. Go to [Railway Dashboard](https://railway.app)
2. Select your project
3. Click **+ New** → **GitHub Repo**
4. Select `railway-grafana-stack` repository
5. Click **Deploy**

### Step 2: Configure Services

Railway will auto-detect services from `docker-compose.yml`. Configure each:

#### Prometheus Service
1. Click **Prometheus** service
2. Go to **Settings**
3. Set environment variables (if needed):
   - `PROMETHEUS_URL=http://prometheus:9090`
4. Click **Deploy**

#### Loki Service
1. Click **Loki** service
2. Go to **Settings**
3. Verify no special configuration needed
4. Click **Deploy**

#### Tempo Service
1. Click **Tempo** service
2. Go to **Settings**
3. Verify no special configuration needed
4. Click **Deploy**

#### Grafana Service
1. Click **Grafana** service
2. Go to **Settings**
3. Set environment variables:
   ```
   GF_SECURITY_ADMIN_USER=admin
   GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>
   GF_DEFAULT_INSTANCE_NAME=Grafana
   PROMETHEUS_INTERNAL_URL=http://prometheus:9090
   LOKI_INTERNAL_URL=http://loki:3100
   TEMPO_INTERNAL_URL=http://tempo:3200
   TEMPO_INTERNAL_HTTP_INGEST=http://tempo:4318
   TEMPO_INTERNAL_GRPC_INGEST=http://tempo:4317
   ```
4. Click **Deploy**

#### Redis Exporter Service
1. Click **redis-exporter** service
2. Go to **Settings**
3. Set environment variables:
   ```
   REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
   REDIS_PASSWORD=<your-redis-password>
   REDIS_SKIP_PING=false
   REDIS_SKIP_CLUSTER_INFO=true
   ```
4. Click **Deploy**

### Step 3: Deploy from Staging Branch

1. In Railway dashboard, go to **Deployments**
2. Click **New Deployment**
3. Select **GitHub** source
4. Choose branch: `staging/models-and-fixes`
5. Click **Deploy**
6. Wait 2-3 minutes for all services to start

### Step 4: Verify Deployment

1. Go to **Deployments** and wait for all services to show "Success"
2. Click **Grafana** service
3. Click **Open** or find the public URL
4. Login with credentials set in Step 2
5. Go to **Configuration → Data Sources**
6. Verify all datasources show "Data source is working":
   - Prometheus
   - Loki
   - Tempo

### Step 5: Verify Dashboards

1. Go to **Dashboards**
2. Verify each dashboard loads:
   - FastAPI Dashboard
   - Models Monitoring
   - Tempo Distributed Tracing
   - Loki Logs
   - GatewayZ Application Health
   - Provider Management

3. Check browser console (F12) for errors
4. Verify no Tempo query errors
5. Verify no Loki query errors

---

## Environment Variables Reference

### Grafana
```
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<secure-password>
GF_DEFAULT_INSTANCE_NAME=Grafana
PROMETHEUS_INTERNAL_URL=http://prometheus:9090
LOKI_INTERNAL_URL=http://loki:3100
TEMPO_INTERNAL_URL=http://tempo:3200
TEMPO_INTERNAL_HTTP_INGEST=http://tempo:4318
TEMPO_INTERNAL_GRPC_INGEST=http://tempo:4317
```

### Redis Exporter
```
REDIS_ADDR=redis-production-bb6d.up.railway.app:6379
REDIS_PASSWORD=<your-redis-password>
REDIS_SKIP_PING=false
REDIS_SKIP_CLUSTER_INFO=true
```

### Prometheus
- No special environment variables needed
- Scrape configuration in `prometheus/prom.yml` handles all targets

### Loki
- No special environment variables needed
- Configuration in `loki/loki.yml` handles all settings

### Tempo
- No special environment variables needed
- Configuration in `tempo/tempo.yml` handles all settings

---

## Troubleshooting

### Services Won't Start
1. Check Railway logs for each service
2. Verify environment variables are set correctly
3. Check for port conflicts
4. Redeploy individual services

### Datasources Show "Data source is working" but No Data
This is expected if backend isn't emitting metrics/logs/traces yet.

### Tempo Dashboard Shows Errors
1. Check browser console (F12) for specific errors
2. Verify Tempo service is running
3. Check Tempo logs in Railway dashboard

### Loki Dashboard Shows Errors
1. Check browser console (F12) for specific errors
2. Verify Loki service is running
3. Check Loki logs in Railway dashboard

### Can't Access Grafana
1. Verify Grafana service is running
2. Check the public URL in Railway dashboard
3. Verify firewall/network allows access

---

## Accessing Services

### Grafana
- URL: `https://<your-railway-domain>.railway.app`
- Username: `admin`
- Password: Set in environment variables

### Prometheus
- URL: `https://<your-railway-domain>.railway.app/prometheus`
- (If exposed via Grafana proxy)

### Loki
- URL: `https://<your-railway-domain>.railway.app/loki`
- (If exposed via Grafana proxy)

### Tempo
- URL: `https://<your-railway-domain>.railway.app/tempo`
- (If exposed via Grafana proxy)

---

## Monitoring Deployment

1. Go to **Deployments** in Railway dashboard
2. Click on each service to view logs
3. Look for errors or warnings
4. Check resource usage (CPU, memory)
5. Monitor for any service restarts

---

## Next Steps After Deployment

1. **Verify all services are running**
   - Check Prometheus targets
   - Verify Grafana datasources
   - Check dashboards load

2. **Test data flow (once backend instrumentation is added)**
   - Prometheus metrics should appear
   - Loki logs should appear
   - Tempo traces should appear

3. **Monitor for issues**
   - Check logs regularly
   - Monitor resource usage
   - Watch for any errors

4. **Create PR once verified**
   - After successful Railway testing
   - Create PR from staging to main
   - Request review

---

## Quick Checklist

- [ ] GitHub repository connected to Railway
- [ ] All services deployed from `staging/models-and-fixes`
- [ ] Environment variables set for all services
- [ ] All services show "Success" in deployments
- [ ] Grafana is accessible
- [ ] All datasources show "Data source is working"
- [ ] All dashboards load without errors
- [ ] No console errors in browser
- [ ] Prometheus targets show UP
- [ ] Ready for PR submission

---

## Support

If you encounter issues:
1. Check Railway logs for each service
2. Verify environment variables
3. Check the troubleshooting section above
4. Review STAGING_WORKFLOW.md for more details
5. Check SYSTEM_HEALTH_CHECK.md for configuration details
