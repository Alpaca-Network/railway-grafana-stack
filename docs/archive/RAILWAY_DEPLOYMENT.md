# Railway Deployment Guide

This guide explains how to deploy your Grafana observability stack to Railway with the new dashboards and gatewayz.ai metrics configuration.

## Prerequisites

- GitHub account connected to Railway
- Railway account (sign up at [railway.app](https://railway.app))
- This repository pushed to GitHub

## Deployment Steps

### Step 1: Push Your Changes to GitHub

First, commit and push all the dashboard configurations:

```bash
git add .
git commit -m "feat: add comprehensive dashboards and gatewayz.ai metrics scraping

- Added 5 pre-configured dashboards (Overview, Loki, Prometheus, Tempo, FastAPI)
- Enhanced datasource correlations for logs/metrics/traces integration
- Configured Prometheus to scrape api.gatewayz.ai/metrics
- Updated Grafana Dockerfile for dashboard provisioning"

git push origin main
```

### Step 2: Deploy to Railway

#### Option A: Using Railway Dashboard (Easiest)

1. **Go to Railway:**
   - Visit [railway.app](https://railway.app)
   - Log in with your GitHub account

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `Alpaca-Network/railway-grafana-stack`
   - Railway will detect your docker-compose.yml and create 4 services:
     - Grafana
     - Prometheus
     - Loki
     - Tempo

3. **Wait for Deployment:**
   - Railway will build and deploy all services
   - This typically takes 5-10 minutes
   - Watch the deployment logs for each service

4. **Configure Grafana Service:**
   - Click on the "Grafana" service
   - Go to "Variables" tab
   - Verify these variables are set:
     ```
     GF_SECURITY_ADMIN_USER=admin (or your preferred username)
     GF_SECURITY_ADMIN_PASSWORD=<generated or set your own>
     GF_DEFAULT_INSTANCE_NAME=Grafana on Railway
     GF_INSTALL_PLUGINS=grafana-simple-json-datasource,grafana-piechart-panel,grafana-worldmap-panel,grafana-clock-panel
     LOKI_INTERNAL_URL=${{Loki.RAILWAY_PRIVATE_DOMAIN}}:3100
     PROMETHEUS_INTERNAL_URL=${{Prometheus.RAILWAY_PRIVATE_DOMAIN}}:9090
     TEMPO_INTERNAL_URL=${{Tempo.RAILWAY_PRIVATE_DOMAIN}}:3200
     ```

5. **Generate Public Domain:**
   - In the Grafana service, go to "Settings" tab
   - Click "Generate Domain" under "Networking"
   - Save the generated URL (e.g., `your-app.up.railway.app`)

#### Option B: Using Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize Project:**
   ```bash
   railway init
   ```
   - Choose "Create new project"
   - Give it a name (e.g., "grafana-observability-stack")

4. **Link Services:**
   Railway will auto-detect your docker-compose.yml and create services.

5. **Deploy:**
   ```bash
   railway up
   ```

6. **Add Domain to Grafana:**
   ```bash
   railway domain
   ```

### Step 3: Access Your Grafana Instance

1. **Get Your URL:**
   - From Railway dashboard: Click on Grafana service → Settings → Domain
   - Copy the public URL

2. **Login:**
   - Navigate to your Grafana URL
   - Username: Value of `GF_SECURITY_ADMIN_USER` (default: `admin`)
   - Password: Value of `GF_SECURITY_ADMIN_PASSWORD` (check Railway variables)

3. **Verify Dashboards:**
   - Click the hamburger menu (☰) → Dashboards
   - You should see 5 dashboards:
     - Observability Stack Overview
     - Loki Logs
     - Prometheus Metrics
     - Tempo Traces
     - FastAPI Observability

### Step 4: Verify Metrics from api.gatewayz.ai

1. **Check Prometheus Targets:**
   - In Grafana, go to Explore
   - Select "Prometheus" datasource
   - Go to http://your-prometheus-url/targets (or use Prometheus Metrics dashboard)
   - Look for `gatewayz_api` job
   - Should show status "UP" in green

2. **Query GatewayZ Metrics:**
   - In Grafana Explore, select Prometheus
   - Try queries like:
     ```promql
     up{job="gatewayz_api"}
     {job="gatewayz_api"}
     ```

3. **Create Custom Dashboards:**
   - Use the metrics from `api.gatewayz.ai` to create custom visualizations
   - All metrics will be labeled with `job="gatewayz_api"`

## Service Configuration

### Grafana
- **Port:** 3000
- **Volume:** `grafana_data` (persistent)
- **Dashboards:** Auto-provisioned from `/grafana/dashboards/`
- **Datasources:** Auto-configured (Loki, Prometheus, Tempo)

### Prometheus
- **Port:** 9090
- **Volume:** `prometheus_data` (persistent)
- **Scrape Targets:**
  - `prometheus` (self-monitoring)
  - `example_api` (local example on port 9091)
  - `gatewayz_api` (https://api.gatewayz.ai/metrics)
- **Scrape Interval:** 15s (default), 30s for gatewayz_api

### Loki
- **Port:** 3100
- **Volume:** `loki_data` (persistent)
- **Purpose:** Log aggregation

### Tempo
- **Ports:**
  - 3200 (HTTP query)
  - 4317 (gRPC ingest)
  - 4318 (HTTP ingest)
- **Volume:** `tempo_data` (persistent)
- **Purpose:** Distributed tracing

## Railway-Specific Notes

### Private Networking
Railway services communicate via private networking:
- Services use `${{SERVICE_NAME.RAILWAY_PRIVATE_DOMAIN}}`
- No need to expose ports for internal communication
- Only Grafana needs a public domain

### Persistent Storage
Railway automatically provisions volumes for:
- `grafana_data` - Stores dashboards, users, settings
- `prometheus_data` - Stores metrics
- `loki_data` - Stores logs
- `tempo_data` - Stores traces

### Environment Variables
Railway automatically injects service references:
- `${{Loki.RAILWAY_PRIVATE_DOMAIN}}` → Internal Loki URL
- `${{Prometheus.RAILWAY_PRIVATE_DOMAIN}}` → Internal Prometheus URL
- `${{Tempo.RAILWAY_PRIVATE_DOMAIN}}` → Internal Tempo URL

### Resource Limits
Railway free tier limits:
- $5 credit/month
- Consider monitoring usage in Railway dashboard
- Can upgrade to pay-as-you-go for production use

## Troubleshooting

### Dashboards Not Appearing
1. Check Grafana build logs: `railway logs --service grafana`
2. Verify files copied correctly in Docker build
3. Restart Grafana service: `railway restart --service grafana`

### Prometheus Not Scraping api.gatewayz.ai
1. Check Prometheus logs: `railway logs --service prometheus`
2. Verify HTTPS connectivity from Railway
3. Check if gatewayz.ai is accessible: `curl https://api.gatewayz.ai/metrics`
4. Verify target in Prometheus UI at `/targets`

### Services Can't Communicate
1. Verify environment variables are correctly set
2. Check Railway private networking is enabled
3. Ensure service names match in docker-compose.yml

### Out of Railway Credits
1. Monitor usage in Railway dashboard
2. Optimize scrape intervals in prometheus/prom.yml
3. Consider data retention policies
4. Upgrade to paid plan if needed

## Updating the Deployment

To deploy updates:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Railway automatically redeploys on git push!

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Verify all dashboards load
3. ✅ Check gatewayz.ai metrics are being scraped
4. 📊 Create custom dashboards for gatewayz.ai metrics
5. 🔔 Set up Grafana alerts
6. 📱 Configure notification channels (Slack, email, etc.)
7. 🔐 Set up additional users/teams in Grafana

## Resources

- [Railway Documentation](https://docs.railway.app/)
- [Railway Templates](https://railway.app/templates)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [This Project's README](/README.md)
- [Dashboard Configuration Guide](/DASHBOARD_CONFIGURATION.md)

---

**Questions or Issues?**
- Check Railway logs: `railway logs`
- Visit Railway community: [discord.gg/railway](https://discord.gg/railway)
- Open an issue on GitHub
