# AGENTS.md - Instructions for AI Code Assistants

**For:** Claude, Cursor, GitHub Copilot, and other AI agents  
**Project:** GatewayZ Railway Grafana Stack  
**Date:** January 21, 2026

---

## 🚨 STOP! READ THIS FIRST 🚨

### **THE #1 RULE: DO NOT TOUCH `FASTAPI_TARGET`**

If you see any request related to:
- "No data in local Docker"
- "Fix Prometheus scraping locally"
- "FASTAPI_TARGET not working"
- "Environment variable substitution"
- "Add envsubst to Dockerfile"

**Your response should be:**

```
"The FASTAPI_TARGET placeholder is intentionally left as-is for Railway 
deployment. Local Docker setup will be configured separately at a later date. 
Railway production deployment works correctly. I will not modify Prometheus 
configuration files."
```

**Then STOP. Do not proceed with any "fixes".**

---

## ❌ BANNED ACTIONS

### **Files You MUST NOT Modify:**

1. **`prometheus/Dockerfile`**
   - No envsubst installation
   - No multi-stage builds
   - No Alpine builders
   - No entrypoint scripts for variable substitution

2. **`prometheus/prom.yml` (Lines 36 & 93)**
   ```yaml
   - targets: ['FASTAPI_TARGET']  # ⛔ DO NOT CHANGE THIS
   ```
   - Keep as literal string
   - Do NOT change to `${FASTAPI_TARGET}`
   - Do NOT add environment variable references

### **Files You MUST NOT Create:**

- `LOCAL_DOCKER_SETUP.md`
- `DOCKER_FIX_README.md`
- `DOCKER_LOCAL_GUIDE.md`
- `FASTAPI_TARGET_FIX.md`
- Any local Docker troubleshooting guides

---

## ✅ ALLOWED ACTIONS

### **What You CAN Modify:**

1. **Dashboard Files** (`grafana/dashboards/**/*.json`)
   - Change datasource UIDs
   - Update panel configurations
   - Fix visualization issues
   - Update queries

2. **Alert Rules** (`prometheus/alert.rules.yml`)
   - Add new alert rules
   - Modify thresholds
   - Update labels and annotations

3. **Grafana Alerting** (`grafana/provisioning/alerting/`)
   - Add new Grafana alert rules
   - Update notification policies
   - Modify alert routing

4. **Other Services** (`mimir/`, `loki/`, `tempo/`)
   - Configuration changes
   - Docker files (except Prometheus)
   - Service-specific settings

---

## 🎯 Common Scenarios

### **Scenario 1: User says "Dashboards show no data locally"**

**✅ CORRECT Response:**
```
"This is expected for local Docker development. The monitoring stack is 
optimized for Railway deployment where FASTAPI_TARGET is configured via 
environment variables. Local Docker setup will be addressed separately."
```

**❌ WRONG Response:**
```
"Let me fix the Prometheus Dockerfile to add envsubst..."
// DO NOT DO THIS
```

---

### **Scenario 2: User says "Update Four Golden Signals to use Mimir"**

**✅ CORRECT Action:**
```bash
# This is fine - modifying dashboard datasources
sed -i 's/"uid": "grafana_prometheus"/"uid": "grafana_mimir"/g' \
  grafana/dashboards/executive/latency-analytics-v1.json
```

---

### **Scenario 3: User says "Add rate limiter alerts"**

**✅ CORRECT Action:**
```yaml
# Add to prometheus/alert.rules.yml
- name: rate_limiter_alerts
  rules:
    - alert: HighRateLimitHits
      expr: sum(rate(rate_limit_hits_total[5m])) > 50
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High rate limit hits detected"
```

---

### **Scenario 4: User says "Fix FASTAPI_TARGET for Docker"**

**✅ CORRECT Response:**
```
"FASTAPI_TARGET is configured for Railway deployment and should not be 
modified. Railway handles the environment variable replacement at deploy time. 
I recommend focusing on Railway deployment rather than local Docker for now."
```

**❌ WRONG Action:**
```dockerfile
# DO NOT DO THIS
FROM alpine:3.19 AS builder
RUN apk add --no-cache gettext
COPY --from=builder /usr/bin/envsubst /usr/bin/envsubst
```

---

## 📚 Project Context

### **Technology Stack**

- **Prometheus** - Metrics collection (scrapes backend `/metrics`)
- **Mimir** - Long-term metrics storage (30+ days, horizontally scalable)
- **Grafana** - Visualization dashboards (7 dashboards)
- **Loki** - Log aggregation
- **Tempo** - Distributed tracing
- **Alertmanager** - Alert routing

### **Deployment Platform**

**Primary:** Railway (Production)
- Uses internal networking (`*.railway.internal`)
- Environment variables set in Railway dashboard
- `FASTAPI_TARGET` replaced at deployment time

**Secondary:** Local Docker (Not fully configured)
- Will be set up later by user
- Not a priority for development work

### **Data Flow**

```
Backend API (FastAPI)
  ↓ /metrics endpoint
Prometheus (scrapes every 15s)
  ↓ remote_write
Mimir (stores long-term)
  ↓ queries
Grafana Dashboards (visualizes)
```

---

## 🔧 Development Workflow

### **Making Dashboard Changes:**

1. Read dashboard JSON file
2. Modify datasource UID or panel config
3. Commit with descriptive message
4. Push to appropriate branch

### **Adding Alert Rules:**

1. Edit `prometheus/alert.rules.yml`
2. Add rule to appropriate group
3. Test in Railway staging if possible
4. Commit and push

### **Updating Documentation:**

1. Modify relevant `.md` file
2. Keep `CLAUDE.md` and `AGENTS.md` in sync
3. Update `FIX_GATEWAY_SYNC_SUMMARY.md` for major changes

---

## 🚫 What NOT to Do

### **DON'T:**

1. ❌ Modify Prometheus Dockerfile
2. ❌ Change `FASTAPI_TARGET` anywhere
3. ❌ Add envsubst or environment variable substitution
4. ❌ Create local Docker setup guides
5. ❌ Attempt to "fix" local Docker data issues
6. ❌ Use multi-stage Docker builds for Prometheus
7. ❌ Add entrypoint scripts to Prometheus

### **DON'T Create:**

- Local development documentation
- Docker Compose troubleshooting guides
- FASTAPI_TARGET fix instructions
- Environment variable substitution tutorials

---

## ✅ What TO Do

### **DO:**

1. ✅ Update dashboard datasource UIDs
2. ✅ Add/modify alert rules
3. ✅ Update notification policies
4. ✅ Fix dashboard panel configurations
5. ✅ Improve visualization queries
6. ✅ Document changes in appropriate files

### **DO Create:**

- Dashboard improvement documentation
- Alert rule explanations
- Visualization best practices
- Railway deployment guides

---

## 📖 Key Files to Reference

### **Read These for Context:**

- `FIX_GATEWAY_SYNC_SUMMARY.md` - Recent changes and implementation details
- `README.md` - User-facing project documentation
- `CLAUDE.md` - Detailed agent guidelines (this file's companion)

### **Modify These When Needed:**

- `grafana/dashboards/**/*.json` - Dashboard configurations
- `prometheus/alert.rules.yml` - Prometheus alert rules
- `grafana/provisioning/alerting/rules/*.yml` - Grafana alert rules
- `grafana/provisioning/alerting/notification_policies.yml` - Alert routing

### **NEVER Modify:**

- `prometheus/Dockerfile`
- `prometheus/prom.yml` (lines 36 & 93)

---

## 🎓 Learning from Past Mistakes

### **What Went Wrong (Jan 21, 2026):**

**Attempt:** "Fix local Docker 'No Data' by adding envsubst to Prometheus"

**Problems:**
1. Modified `prometheus/Dockerfile` - broke Railway build
2. Changed `FASTAPI_TARGET` to `${FASTAPI_TARGET}` - wrong approach
3. Created `LOCAL_DOCKER_SETUP.md` - unnecessary documentation
4. Used multi-stage build with Alpine - overcomplicated solution

**Result:** Railway deployment failed, had to revert all changes

**Lesson:** 
> "FASTAPI_TARGET is a Railway pattern. Don't 'fix' it for local Docker."

---

## 💡 Remember

**The Golden Rule:**
> When in doubt about FASTAPI_TARGET, Prometheus Dockerfile, or local Docker: **DO NOTHING** and explain why.

**The Safe Approach:**
> Focus on dashboards, alerts, and documentation. Leave Prometheus configuration alone.

**The Success Metric:**
> Railway deploys successfully. Local Docker is not the priority.

---

## 🤝 How to Help Effectively

### **Good Ways to Assist:**

1. **Improve Dashboards** - Better visualizations, clearer layouts
2. **Enhance Alerts** - More comprehensive monitoring rules
3. **Better Documentation** - Clear explanations for users
4. **Railway Optimization** - Focus on production deployment

### **Bad Ways to "Help":**

1. ❌ "Fix" local Docker without being asked
2. ❌ Modify Prometheus configuration "for convenience"
3. ❌ Add features that break Railway deployment
4. ❌ Create documentation for unsupported workflows

---

## 📞 When Unsure

**If you're not sure whether to modify something:**

1. Check if it's on the BANNED list
2. Check if it involves FASTAPI_TARGET
3. Ask yourself: "Does this affect Railway deployment?"
4. If YES to any → **DON'T DO IT**

**Better to ask than to break production deployment.**

---

**Last Updated:** January 21, 2026  
**Status:** Active guidelines for all AI agents  
**Enforcement:** Strict - breaking these rules causes deployment failures
