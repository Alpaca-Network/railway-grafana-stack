# Trace Sync Fix - Summary & Deployment Guide

> **Date:** March 10, 2026
> **Branch:** `feature/feature-availability`
> **Status:** ✅ Documentation Complete - Ready for Backend Implementation

---

## Problem Statement

**Symptom:** Grafana dashboards show no data in trace-based panels (model usage, provider performance, latency breakdowns) even though some traces are visible in Tempo.

**Root Cause:** Backend traces are missing OpenTelemetry semantic convention attributes (`gen_ai.*`) that Tempo's metrics generator needs to create span metrics.

**Impact:**
- ❌ Cannot see which models are being used
- ❌ Cannot track provider-specific performance
- ❌ Cannot measure LLM request latency by model
- ❌ Cannot identify cost patterns
- ❌ Slower incident response due to incomplete observability

---

## Solution Overview

### What Was Created

| Document | Location | Purpose | Audience |
|----------|----------|---------|----------|
| **BACKEND_TRACE_INTEGRATION_COMPLETE.md** | `docs/backend/` | Complete implementation guide with code examples | Backend developers |
| **TRACE_DATA_VERIFICATION_CHECKLIST.md** | `docs/tracing/` | Step-by-step validation procedure | Backend + DevOps |
| **INCIDENT_RESPONSE_IMPROVEMENTS.md** | `docs/deployment/` | Log alerts and correlated failure detection fixes | DevOps + SRE |
| **TRACE_SYNC_FIX_SUMMARY.md** | Root | This document - executive summary | All teams |

### What Needs To Be Done

**Backend Team Actions:**
1. Create new branch: `feat/enhanced-trace-attributes`
2. Implement OpenTelemetry span attribute tagging (see `BACKEND_TRACE_INTEGRATION_COMPLETE.md`)
3. Set `TEMPO_OTLP_HTTP_ENDPOINT` environment variable in Railway
4. Test using verification checklist
5. Deploy to staging → validate → deploy to production

**Observability Team Actions:**
- ✅ Documentation complete (this repo)
- ⚠️ Audit dashboard queries for label mismatches (if needed after backend implementation)
- ✅ No Tempo configuration changes needed (already correct)

---

## Technical Details

### Required Span Attributes

Every LLM API call span must have these attributes:

```python
span.set_attribute("gen_ai.system", "anthropic")  # or "openai", "google"
span.set_attribute("gen_ai.request.model", "anthropic/claude-opus-4.5")
span.set_attribute("gen_ai.usage.prompt_tokens", 450)
span.set_attribute("gen_ai.usage.completion_tokens", 823)
span.set_attribute("gen_ai.usage.total_tokens", 1273)
span.set_attribute("ai.provider", "openrouter")
span.set_attribute("customer.id", "cust_abc123")
```

### How It Works

1. **Backend sets span attributes** on LLM call spans
2. **Tempo extracts attributes** from spans
3. **Tempo metrics generator** creates Prometheus metrics with attributes as labels
4. **Tempo remote writes** span metrics to Mimir
5. **Dashboards query Mimir** for span metrics with specific labels
6. **Graphs populate** with model/provider-specific data

### Data Flow Diagram

```
Backend (OpenTelemetry)
  ↓ OTLP (4318)
  ├─ Trace with span attributes: gen_ai.request.model="claude-opus-4.5"
  ↓
Tempo
  ├─ Ingests trace
  ├─ Metrics generator extracts attributes
  ├─ Creates: traces_spanmetrics_calls_total{gen_ai_request_model="claude-opus-4.5"}
  ↓ Remote Write (9009)
Mimir
  ├─ Stores span metrics
  ↓
Grafana Dashboard
  ├─ Query: sum(rate(traces_spanmetrics_calls_total{gen_ai_request_model!=""}[5m]))
  ├─ Result: Graph by model name ✅
```

---

## Before & After

### BEFORE (Current State)

**Tempo:**
- ✅ Traces arrive
- ❌ Traces lack `gen_ai.*` attributes
- ❌ Metrics generator cannot create span metrics

**Mimir:**
```promql
traces_spanmetrics_calls_total
# Returns: No data points with gen_ai_request_model label
```

**Dashboard:**
- Panel: "Most Popular Models" → ⬜ No data
- Panel: "P95 Latency by Model" → ⬜ No data
- Panel: "Span Calls by Provider" → ⬜ No data

### AFTER (Expected State)

**Tempo:**
- ✅ Traces arrive
- ✅ Traces have all required `gen_ai.*` attributes
- ✅ Metrics generator creates span metrics with labels

**Mimir:**
```promql
traces_spanmetrics_calls_total{gen_ai_request_model="anthropic/claude-opus-4.5"}
# Returns: Time series data ✅
```

**Dashboard:**
- Panel: "Most Popular Models" → ✅ Bar chart with model names
- Panel: "P95 Latency by Model" → ✅ Line graph by model
- Panel: "Span Calls by Provider" → ✅ Provider breakdown

---

## Deployment Plan

### Phase 1: Local Testing (Day 1)

**Backend Team:**
1. Create branch `feat/enhanced-trace-attributes`
2. Implement OpenTelemetry changes from `BACKEND_TRACE_INTEGRATION_COMPLETE.md`
3. Run local observability stack
4. Send test requests
5. Run through `TRACE_DATA_VERIFICATION_CHECKLIST.md`

**Success Criteria:**
- ✅ All checklist items pass
- ✅ Dashboard panels show data locally

### Phase 2: Staging Deployment (Day 2-3)

**DevOps/Backend:**
1. Deploy branch to Railway staging environment
2. Set environment variables:
   ```bash
   TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318/v1/traces
   ```
3. Send production-like traffic to staging
4. Run verification checklist against staging
5. Monitor for 24 hours

**Success Criteria:**
- ✅ Staging traces have required attributes
- ✅ Staging dashboards populate correctly
- ✅ No performance degradation observed

### Phase 3: Production Deployment (Day 4)

**DevOps:**
1. Merge to main
2. Deploy to production
3. Monitor dashboards immediately after deployment
4. Be ready to rollback if issues

**Success Criteria:**
- ✅ Production dashboards show data within 5 minutes
- ✅ No increase in error rates or latency
- ✅ Span metrics generation rate stable

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Span attributes cause performance overhead | Low | Low | Attributes are lightweight metadata - negligible impact |
| High cardinality labels overwhelm Tempo | Medium | Medium | `customer.id` limited to configured dimensions - monitored |
| Deployment breaks existing traces | Very Low | High | Changes are additive - existing instrumentation untouched |
| Staging validation misses production issues | Low | Medium | 24h staging soak test required before production |
| Rollback needed in production | Low | High | Simple: revert commit, restart service - 2 min rollback |

---

## Rollback Procedure

**If issues occur in production:**

```bash
# Option 1: Revert commit
git revert HEAD
git push origin main
# Trigger Railway redeploy

# Option 2: Environment variable (if that's the only change)
# In Railway dashboard:
# Unset TEMPO_OTLP_HTTP_ENDPOINT
# Restart service

# Option 3: Manual rollback in Railway UI
# Railway dashboard → Deployments → Select previous deployment → Redeploy
```

**Expected rollback time:** < 5 minutes

---

## Monitoring After Deployment

### Immediate (First Hour)

**Check every 5 minutes:**
- Dashboard panels populate with data
- Error rates remain stable
- Latency P95 unchanged
- Tempo ingestion rate stable

**Grafana Queries to Monitor:**
```promql
# Span metrics generation rate
rate(traces_spanmetrics_calls_total[1m])

# Backend error rate (should not increase)
rate(fastapi_requests_total{status_code=~"5.."}[5m])

# Backend latency (should not increase)
histogram_quantile(0.95, rate(fastapi_requests_duration_seconds_bucket[5m]))
```

### Short-term (First 24 Hours)

**Check every hour:**
- Dashboard data remains consistent
- No Tempo OOM or disk space issues
- Span metrics labels are correct
- Customer.id cardinality within limits

**Alert Rules to Watch:**
- Any new alerts firing unexpectedly
- Tempo resource usage alerts
- Backend performance degradation

### Long-term (First Week)

**Check daily:**
- Historical data accumulation correct
- Mimir storage capacity adequate
- No label cardinality explosions
- Dashboard query performance stable

---

## Success Metrics

**How to know it's working:**

1. **Quantitative:**
   - `traces_spanmetrics_calls_total` > 0
   - `traces_spanmetrics_calls_total{gen_ai_request_model!=""}` > 0
   - Dashboard "Most Popular Models" shows 5+ models
   - Dashboard "P95 Latency by Model" shows line graphs

2. **Qualitative:**
   - Team can identify which models are used most
   - Team can detect provider-specific performance issues
   - Team can track cost per model
   - Incident response time improves (can quickly identify model/provider during outage)

---

## Next Actions

### For Backend Team

**Immediate:**
- [ ] Read `docs/backend/BACKEND_TRACE_INTEGRATION_COMPLETE.md` thoroughly
- [ ] Create branch `feat/enhanced-trace-attributes`
- [ ] Schedule implementation (estimate: 4-6 hours development + testing)

**This Week:**
- [ ] Implement OpenTelemetry span attribute tagging
- [ ] Test locally using verification checklist (`docs/tracing/TRACE_DATA_VERIFICATION_CHECKLIST.md`)
- [ ] Deploy to staging
- [ ] Run 24h validation

**Next Week:**
- [ ] Deploy to production (Monday preferred - full team available)
- [ ] Monitor for 48 hours
- [ ] Mark task complete

### For Observability Team

**Immediate:**
- [x] Documentation complete
- [ ] Review documents for accuracy
- [ ] Be available for backend team questions

**After Backend Implementation:**
- [ ] Validate dashboards show data
- [ ] Audit any panels still showing "No Data"
- [ ] Update alert rules if needed
- [ ] Document lessons learned

---

## FAQ

### Q: Will this impact production performance?
**A:** No. Setting span attributes adds negligible overhead (<1ms). OpenTelemetry is designed for production use.

### Q: Can we deploy to production without staging validation?
**A:** Not recommended. Staging validation catches attribute naming issues and cardinality problems before they affect production.

### Q: What if dashboards still show no data after implementation?
**A:** Run `TRACE_DATA_VERIFICATION_CHECKLIST.md` step-by-step to identify the gap. Most likely cause: span attributes on wrong span or wrong attribute names.

### Q: Do we need to modify existing traces?
**A:** No. Changes are additive. Existing trace instrumentation remains unchanged. We're only adding attributes to LLM call spans.

### Q: Will historical data be backfilled?
**A:** No. Span metrics are generated from new traces only. Historical traces (before implementation) will not have span metrics.

### Q: What's the minimum viable implementation?
**A:** At minimum, set these 3 attributes on LLM call spans:
- `gen_ai.request.model`
- `gen_ai.system`
- `ai.provider`

All others are optional but recommended.

---

## Contact & Support

**Questions about:**
- Implementation → See `docs/backend/BACKEND_TRACE_INTEGRATION_COMPLETE.md`
- Validation → See `docs/tracing/TRACE_DATA_VERIFICATION_CHECKLIST.md`
- Incident Response Alerts → See `docs/deployment/INCIDENT_RESPONSE_IMPROVEMENTS.md`
- This summary → This document

**Still stuck?**
- Check Tempo logs: `Railway → Tempo service → Logs`
- Check backend logs: `Railway → gatewayz-backend → Logs`
- Review Grafana panel queries (Edit mode)

---

**Status:** ✅ Ready for backend team to begin implementation
**Estimated time to completion:** 1 week (with staging validation)
**Expected impact:** Full dashboard visibility of LLM operations
