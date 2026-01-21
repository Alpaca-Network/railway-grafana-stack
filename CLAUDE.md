# CLAUDE.md - Context for AI Agents (Claude, Cursor, etc.)

**Project:** GatewayZ Railway Grafana Stack  
**Purpose:** Monitoring and observability for GatewayZ AI Inference Platform  
**Primary Deployment:** Railway (Production)  
**Last Updated:** January 21, 2026

---

## ⚠️ **CRITICAL RULES - READ FIRST**

### **Rule #1: NEVER MODIFY `FASTAPI_TARGET`**

**Files that are OFF-LIMITS:**
- ❌ `prometheus/Dockerfile` - DO NOT modify
- ❌ `prometheus/prom.yml` lines 36 & 93 - DO NOT change `FASTAPI_TARGET`

**Why:**
- `FASTAPI_TARGET` is a **placeholder** replaced by Railway at deployment time
- This pattern works perfectly in production Railway environment
- Attempting to "fix" it for local Docker breaks Railway deployments
- **Local Docker setup is NOT a priority and will be configured later**

**If user says "No Data in local Docker":**
```
Response: "Local Docker is not fully configured yet. This will be set up 
at a later date. Railway deployment works correctly with FASTAPI_TARGET."
```

**DO NOT:**
- ❌ Add envsubst or environment variable substitution
- ❌ Create multi-stage Docker builds
- ❌ Modify Prometheus configuration for local development
- ❌ Create local Docker setup guides

---

### **Rule #2: Dashboard Files ONLY for Data Source Fixes**

**You MAY modify:**
- ✅ Dashboard JSON files in `grafana/dashboards/`
- ✅ Datasource UIDs (e.g., `grafana_prometheus` → `grafana_mimir`)
- ✅ Panel configurations and visualizations
- ✅ Alert rules in `prometheus/alert.rules.yml`
- ✅ Grafana alert rules in `grafana/provisioning/alerting/`

**You MAY NOT modify:**
- ❌ `prometheus/Dockerfile`
- ❌ `prometheus/prom.yml` (except alert rules)
- ❌ Scrape job configurations
- ❌ `FASTAPI_TARGET` references

---

### **Rule #3: No Local Docker Documentation**

**DO NOT create files like:**
- `LOCAL_DOCKER_SETUP.md`
- `DOCKER_FIX_README.md`
- `DOCKER_LOCAL_GUIDE.md`
- Any "How to fix No Data locally" guides

**Why:** User will handle local setup separately at a later date.

---

## 📁 Project Structure

```
railway-grafana-stack/
├── prometheus/
│   ├── Dockerfile              # ⛔ DO NOT MODIFY
│   ├── prom.yml                # ⛔ FASTAPI_TARGET lines OFF-LIMITS
│   └── alert.rules.yml         # ✅ Alert rules OK to modify
├── grafana/
│   ├── dashboards/
│   │   ├── executive/          # ✅ OK to modify
│   │   ├── backend/            # ✅ OK to modify
│   │   ├── gateway/            # ✅ OK to modify
│   │   ├── prometheus/         # ✅ OK to modify
│   │   ├── loki/               # ✅ OK to modify
│   │   └── tempo/              # ✅ OK to modify
│   ├── datasources/
│   │   └── datasources.yml     # ✅ OK to modify
│   └── provisioning/
│       └── alerting/           # ✅ OK to modify
├── mimir/                      # ✅ OK to modify
├── loki/                       # ✅ OK to modify
└── tempo/                      # ✅ OK to modify
```

---

## 🎯 Common Tasks

### **Task: Update Dashboard Datasources**

**Example:** Change Four Golden Signals to use Mimir instead of Prometheus

```bash
# ✅ CORRECT - Modify dashboard JSON
sed -i 's/"uid": "grafana_prometheus"/"uid": "grafana_mimir"/g' \
  grafana/dashboards/executive/latency-analytics-v1.json
```

### **Task: Add New Alert Rules**

**Example:** Add rate limiter alert

```yaml
# ✅ CORRECT - Add to prometheus/alert.rules.yml
- name: rate_limiter_alerts
  rules:
    - alert: HighRateLimitHits
      expr: sum(rate(rate_limit_hits_total[5m])) > 50
```

### **Task: Fix "No Data" Issue**

**❌ WRONG Approach:**
```bash
# DO NOT DO THIS
# Modify prometheus/Dockerfile to add envsubst
# Change FASTAPI_TARGET to ${FASTAPI_TARGET}
```

**✅ CORRECT Approach:**
```
Explain: "This is expected for local Docker. Railway deployment 
works correctly. Local Docker will be configured separately."
```

---

## 🚀 Deployment Information

### **Railway (Production)**

**How FASTAPI_TARGET Works:**
1. User sets `FASTAPI_TARGET` environment variable in Railway dashboard
2. Railway replaces the literal string in deployed containers
3. Prometheus scrapes the correct backend URL
4. Data flows to Grafana dashboards

**Environment Variables (Railway):**
- `FASTAPI_TARGET=gatewayz-backend.railway.internal`
- `PROMETHEUS_INTERNAL_URL=http://prometheus.railway.internal:9090`
- `MIMIR_INTERNAL_URL=http://mimir.railway.internal:9009`
- `LOKI_INTERNAL_URL=http://loki.railway.internal:3100`
- `TEMPO_INTERNAL_URL=http://tempo.railway.internal:3200`

### **Local Docker (Not Fully Configured)**

**Status:** ⚠️ Not priority, will be set up later

**If asked about local Docker:**
- Acknowledge it's not fully working
- Explain Railway is the primary deployment
- Do NOT attempt to fix it
- User will configure it separately

---

## 📊 Dashboard Overview

### **All Dashboards Use Mimir for Metrics**

| Dashboard | Location | Datasource | Status |
|-----------|----------|------------|--------|
| Executive Overview | `executive/executive-overview-v1.json` | Mimir | ✅ |
| Four Golden Signals | `executive/latency-analytics-v1.json` | Mimir | ✅ |
| Backend Services | `backend/backend-services-v1.json` | Mimir | ✅ |
| Gateway Comparison | `gateway/gateway-comparison-v1.json` | JSON API | ✅ |
| Prometheus Metrics | `prometheus/prometheus.json` | Mimir | ✅ |
| Loki Logs | `loki/loki.json` | Loki | ✅ |
| Tempo Traces | `tempo/tempo.json` | Tempo | ✅ |

---

## 🔔 Alert System

### **Prometheus Alert Rules** (`prometheus/alert.rules.yml`)

**Alert Groups:**
- `performance_alerts` - API latency, error rate
- `performance_trends` - Degradation detection
- `model_health_alerts` - Model/provider health
- `redis_alerts` - Redis memory, cache hit rate
- `infrastructure_alerts` - Traffic spikes, SLO breaches
- `rate_limiter_alerts` - Rate limiting abuse detection

### **Grafana Alert Rules** (`grafana/provisioning/alerting/rules/`)

- `redis_alerts.yml` - Grafana-native Redis monitoring
- `rate_limiter_alerts.yml` - Rate limiter + traffic spike alerts

### **Notification Routing** (`grafana/provisioning/alerting/notification_policies.yml`)

- Critical alerts → immediate email
- Warning alerts → grouped, delayed email
- Component-based routing (redis, rate_limiter, slo, etc.)

---

## 🛠️ Recent Changes (January 2026)

### **Fix Gateway Sync (Branch: fix/fix-gateway-sync)**

**✅ Completed:**
1. Updated Four Golden Signals dashboard: `grafana_prometheus` → `grafana_mimir`
2. Updated Prometheus dashboard: `grafana_prometheus` → `grafana_mimir`
3. Added rate limiter alert rules (5 Prometheus, 4 Grafana)
4. Added notification routing for rate limiter alerts
5. Updated `FIX_GATEWAY_SYNC_SUMMARY.md` with complete details

**❌ Reverted (DO NOT REPEAT):**
- Attempted FASTAPI_TARGET envsubst fix - **WRONG APPROACH**
- Created LOCAL_DOCKER_SETUP.md - **NOT NEEDED**
- Modified Prometheus Dockerfile - **BREAKS RAILWAY**

---

## 📝 Documentation Files

### **Keep These Updated:**
- `FIX_GATEWAY_SYNC_SUMMARY.md` - Latest changes summary
- `CLAUDE.md` (this file) - Agent guidelines
- `AGENTS.md` - Additional agent instructions
- `README.md` - User-facing documentation

### **Do NOT Create:**
- Local Docker setup guides
- FASTAPI_TARGET fix documentation
- Environment variable substitution guides

---

## ✅ Summary for AI Agents

**What You Can Do:**
- ✅ Modify dashboard JSON files
- ✅ Update datasource UIDs
- ✅ Add/modify alert rules
- ✅ Update notification policies
- ✅ Modify Mimir, Loki, Tempo configs

**What You Cannot Do:**
- ❌ Modify `prometheus/Dockerfile`
- ❌ Change `FASTAPI_TARGET` in `prom.yml`
- ❌ Create local Docker fixes
- ❌ Add environment variable substitution

**Golden Rule:**
> "If it involves FASTAPI_TARGET or local Docker, SAY NO and explain Railway handles it."

---

**Last Updated:** January 21, 2026  
**Branch:** main  
**Status:** Production-ready for Railway deployment
