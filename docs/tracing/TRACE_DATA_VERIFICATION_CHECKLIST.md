# Trace Data Verification Checklist

> **Purpose:** Step-by-step validation that backend traces have required OpenTelemetry attributes
> **Use When:** After implementing OpenTelemetry enhancements, before deploying to production
> **Time:** ~15 minutes per environment

---

## Pre-Deployment Verification

### ✅ Step 1: Verify Environment Variables

**In Railway Backend Service → Variables:**

```bash
# Check these variables are set:
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo.railway.internal:4318/v1/traces
SERVICE_VERSION=1.0.0
ENVIRONMENT=production (or staging)
```

**Command to verify (if you have Railway CLI):**
```bash
railway variables list --service gatewayz-backend
```

**Expected:**
- ✅ `TEMPO_OTLP_HTTP_ENDPOINT` is present and points to Tempo
- ✅ `ENVIRONMENT` matches deployment environment

**If Missing:**
- Set the variable in Railway dashboard
- Restart the backend service
- Wait 60 seconds for restart to complete

---

### ✅ Step 2: Verify Backend Logs Show OpenTelemetry Init

**In Railway Backend Service → Logs:**

```bash
# Look for these log lines on startup:
"Configuring OpenTelemetry: endpoint=http://tempo.railway.internal:4318/v1/traces"
"OpenTelemetry configured successfully"
"FastAPI auto-instrumentation enabled"
"HTTPX auto-instrumentation enabled"
```

**Expected:**
- ✅ All 4 log lines appear on service start
- ✅ No errors related to OTLP exporter

**If Not Found:**
- Check `opentelemetry_config.py` is being imported in `main.py`
- Verify `configure_telemetry()` is called BEFORE FastAPI app creation
- Check for Python import errors in logs

---

## Post-Request Verification

### ✅ Step 3: Generate Test Traffic

**Send a test chat completion request:**

```bash
# Replace with your actual API endpoint and key
curl -X POST https://api.gatewayz.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-opus-4.5",
    "messages": [
      {"role": "user", "content": "Say hello"}
    ]
  }'
```

**Expected Response:**
- ✅ HTTP 200 OK
- ✅ Response contains completion from model

**Wait 30 seconds** for trace ingestion and processing.

---

### ✅ Step 4: Verify Traces Reach Tempo

**In Grafana:**
1. Navigate to **Explore** (left sidebar)
2. Select **Tempo** datasource (top dropdown)
3. Switch to **TraceQL** tab
4. Enter query:
   ```
   {resource.service.name="gatewayz-api"}
   ```
5. Set time range to **Last 5 minutes**
6. Click **Run query**

**Expected:**
- ✅ At least one trace appears
- ✅ Trace has multiple spans (FastAPI → model_inference → llm_inference)
- ✅ Duration matches expected response time

**If No Traces:**
- Go back to Step 1 - env var likely missing
- Check backend can reach Tempo: `curl http://tempo.railway.internal:4318/v1/traces`
- Check Tempo logs for ingestion errors: Railway → Tempo service → Logs

---

### ✅ Step 5: Verify Root Span Attributes (FastAPI)

**In Grafana Explore → Tempo:**
1. Click on the trace from Step 4
2. Expand the **first span** (should be the HTTP request span)
3. Click **"Attributes"** tab

**Check for these resource attributes:**
- ✅ `resource.service.name` = `"gatewayz-api"`
- ✅ `resource.deployment.environment` = `"production"` or `"staging"`
- ✅ `resource.service.version` = your version string

**Check for these span attributes:**
- ✅ `http.method` = `"POST"`
- ✅ `http.route` = `"/v1/chat/completions"`
- ✅ `http.status_code` = `200`
- ✅ `http.target` = `"/v1/chat/completions"`

**If Missing:**
- HTTP attributes → FastAPI auto-instrumentation not working
- Fix: Verify `FastAPIInstrumentor.instrument_app(app)` is called
- Resource attributes → Check `Resource.create({...})` in opentelemetry_config.py

---

### ✅ Step 6: Verify LLM Span Attributes (CRITICAL)

**In the same trace from Step 5:**
1. Find the span named **"llm_inference"** or **"model_inference"**
2. Expand it
3. Click **"Attributes"** tab

**Check for Gen AI semantic conventions:**
| Attribute | Expected Value | Status |
|-----------|----------------|--------|
| `gen_ai.system` | `"anthropic"` (or `"openai"`, etc.) | ⬜ |
| `gen_ai.request.model` | `"anthropic/claude-opus-4.5"` | ⬜ |
| `gen_ai.usage.prompt_tokens` | (number > 0) | ⬜ |
| `gen_ai.usage.completion_tokens` | (number > 0) | ⬜ |
| `gen_ai.usage.total_tokens` | (number > 0) | ⬜ |
| `ai.provider` | `"openrouter"` (or your provider) | ⬜ |
| `customer.id` | (customer/user identifier) | ⬜ |

**ALL 7 must be present and have valid values.**

**If Missing:**
- Review `call_llm_provider()` function implementation
- Verify `span.set_attribute("gen_ai.system", ...)` calls are present
- Check span is created with `tracer.start_as_current_span("llm_inference")`
- Confirm attributes are set BEFORE the span ends

**If Values Are Wrong:**
- `gen_ai.system` → Must match provider name: "anthropic", "openai", "google"
- `gen_ai.request.model` → Should be full model path: "anthropic/claude-opus-4.5"
- Token counts → Must be integers from response.usage

---

### ✅ Step 7: Verify Span Metrics Generated

**In Grafana:**
1. Navigate to **Explore**
2. Select **Mimir** datasource (NOT Prometheus, NOT Tempo - use Mimir!)
3. Enter query:
   ```promql
   traces_spanmetrics_calls_total
   ```
4. Click **Run query**

**Expected:**
- ✅ Metric exists (not "No data")
- ✅ Has labels: `service_name`, `span_name`
- ✅ Value > 0

**Now query with label filter:**
```promql
traces_spanmetrics_calls_total{gen_ai_request_model!=""}
```

**Expected:**
- ✅ Returns data
- ✅ Label `gen_ai_request_model` = `"anthropic/claude-opus-4.5"` (or your model)
- ✅ Label `gen_ai_system` = `"anthropic"` (or your provider)
- ✅ Label `ai_provider` = `"openrouter"` (or your gateway provider)

**If No Data:**
- Tempo metrics generator not creating metrics → Check Step 6 (span attributes missing)
- Metrics not being remote-written to Mimir → Check Tempo logs for remote write errors
- Wrong datasource → Ensure you're querying **Mimir**, not Prometheus

**If Data But Wrong Labels:**
- Labels have dots instead of underscores → Dashboard queries need fixing (see Step 10)
- Missing `gen_ai_request_model` label → Span attribute `gen_ai.request.model` not set
- Missing other labels → Corresponding span attributes not set

---

### ✅ Step 8: Verify Span Latency Metrics

**In Grafana Explore → Mimir:**
```promql
histogram_quantile(0.95,
  sum(rate(traces_spanmetrics_latency_bucket{gen_ai_request_model!=""}[5m])) by (le, gen_ai_request_model)
)
```

**Expected:**
- ✅ Returns data
- ✅ Shows P95 latency per model
- ✅ Values match observed response times (e.g., 1-5 seconds for LLM calls)

**If No Data:**
- Check `traces_spanmetrics_latency_bucket` exists: `traces_spanmetrics_latency_bucket{gen_ai_request_model!=""}`
- If metric missing → Tempo not generating histogram metrics
- Check tempo/tempo.yml has `histogram_buckets` configured

---

### ✅ Step 9: Verify Dashboard Data Population

**Go to Dashboards → Distributed Tracing:**

| Panel Name | Expected Data | Status |
|------------|---------------|--------|
| **Trace Ingestion Rate** (Panel 201) | > 0 spans/second | ⬜ |
| **Span Calls Rate** (Panel 202) | > 0 calls/second | ⬜ |
| **Span Error Rate** (Panel 203) | 0% (if no errors) | ⬜ |
| **Average Span Duration** (Panel 204) | 1-5 seconds | ⬜ |
| **Most Popular Models** (Panel 209) | Bar chart with model names | ⬜ |
| **P95 Latency by Model** (Panel 210) | Line graph by model | ⬜ |

**Go to Dashboards → Four Golden Signals:**

| Panel Name | Expected Data | Status |
|------------|---------------|--------|
| **Multi-Layer Error Correlation** | Graph with 3 lines (Metrics, Logs, Traces) | ⬜ |
| **Trace Error Rate** (any trace-related panel) | Shows trace data | ⬜ |

**If Panels Show "No Data":**
- Check the panel's query in Edit mode
- Verify datasource is **Mimir** (for span metrics) or **Tempo** (for traces)
- Check query labels match what you verified in Step 7
- See Step 10 for dashboard query audit

---

### ✅ Step 10: Audit Dashboard Queries (If No Data)

**For each dashboard panel showing "No Data":**

1. Click panel title → **Edit**
2. Check **datasource** is correct:
   - Span metrics (`traces_spanmetrics_*`) → Use **Mimir**
   - Trace search (TraceQL) → Use **Tempo**
3. Check **query label names**:
   - Use underscores: `gen_ai_request_model` ✅
   - NOT dots: `gen_ai.request.model` ❌

**Common Label Mismatches:**

| Wrong (Dots) | Correct (Underscores) |
|--------------|-----------------------|
| `gen_ai.request.model` | `gen_ai_request_model` |
| `gen_ai.system` | `gen_ai_system` |
| `ai.provider` | `ai_provider` |
| `customer.id` | `customer_id` |

**If You Find Mismatches:**
- Dashboard queries need fixing (not backend)
- Update panel queries to use underscored labels
- Save dashboard and re-test

---

## Post-Verification Actions

### If All Checks Pass ✅

1. **Document successful verification:**
   ```bash
   # Create verification record
   echo "$(date): Trace verification passed for environment: $ENVIRONMENT" >> trace_verification.log
   ```

2. **Proceed to next environment:**
   - Local → Staging
   - Staging → Production (after 24h monitoring)

3. **Enable monitoring alerts:**
   - Ensure alert rules in `grafana/provisioning/alerting/rules/` are enabled
   - Verify Alertmanager is routing alerts correctly

### If Any Checks Fail ❌

1. **Do NOT proceed to production**
2. **Identify root cause:**
   - Missing attributes → Review `BACKEND_TRACE_INTEGRATION_COMPLETE.md` implementation
   - No traces → Check environment variables and Tempo connectivity
   - Wrong labels → Update dashboard queries or fix attribute naming
3. **Fix issues and re-run full checklist**
4. **Document failures:**
   ```bash
   echo "$(date): Trace verification FAILED at step X" >> trace_verification.log
   ```

---

## Quick Validation Queries

### Copy-Paste Queries for Fast Verification

**Tempo (check traces exist):**
```
{resource.service.name="gatewayz-api"}
```

**Tempo (check LLM spans have attributes):**
```
{span.gen_ai.request.model != ""}
```

**Mimir (check span metrics):**
```promql
sum(rate(traces_spanmetrics_calls_total[5m]))
```

**Mimir (check metrics have LLM labels):**
```promql
sum(rate(traces_spanmetrics_calls_total{gen_ai_request_model!=""}[5m])) by (gen_ai_request_model, gen_ai_system)
```

**Mimir (check latency histogram):**
```promql
histogram_quantile(0.95, sum(rate(traces_spanmetrics_latency_bucket[5m])) by (le, gen_ai_request_model))
```

---

## Troubleshooting Decision Tree

```
No traces in Tempo?
├─ No → Traces exist but no attributes?
│     ├─ Yes → Review Step 6 - implement span attribute setting
│     └─ No → Attributes exist but no span metrics?
│           ├─ Yes → Check Tempo metrics generator config
│           └─ No → Span metrics exist but dashboards empty?
│                 └─ Yes → Audit dashboard queries (Step 10)
└─ Yes → Check environment variables (Step 1)
      └─ Still no traces → Check Tempo connectivity
            └─ curl http://tempo.railway.internal:4318/v1/traces
```

---

## Success Criteria

**All of these must be TRUE before production deployment:**

- [x] Environment variables set in Railway
- [x] Backend logs show OpenTelemetry initialization
- [x] Test request completes successfully
- [x] Traces appear in Tempo within 30 seconds
- [x] Root span has http.route and http.status_code
- [x] LLM span has all 7 required gen_ai.* attributes
- [x] `traces_spanmetrics_calls_total` returns data in Mimir
- [x] Span metrics have gen_ai_request_model label
- [x] Distributed Tracing dashboard shows data
- [x] Four Golden Signals dashboard shows trace data

**Only deploy to production when all checkboxes are checked.**

---

**Next:** See `OPENTELEMETRY_LLM_CONVENTIONS.md` for complete attribute reference.
**Help:** See `BACKEND_TRACE_INTEGRATION_COMPLETE.md` for implementation details.
