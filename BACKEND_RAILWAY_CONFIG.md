# Backend Service Configuration Guide

To connect your **backend application** to this Observability Stack on Railway, you need to add the following environment variables to your **Backend Service** in the Railway Dashboard.

## 1. Environment Variables to Add

Go to your **Backend Service** -> **Variables** and add:

```bash
# Enable Instrumentation
LOKI_ENABLED=true
TEMPO_ENABLED=true

# Service Identification (Customize these)
SERVICE_NAME=gatewayz-api
ENVIRONMENT=staging
APP_ENV=staging

# Loki Connection (Logs)
# Use this if backend and stack are in the SAME Railway Project:
LOKI_PUSH_URL=http://loki:3100/loki/api/v1/push
LOKI_QUERY_URL=http://loki:3100/loki/api/v1/query_range

# Tempo Connection (Traces)
# Use this if backend and stack are in the SAME Railway Project:
TEMPO_OTLP_HTTP_ENDPOINT=http://tempo:4318
TEMPO_OTLP_GRPC_ENDPOINT=http://tempo:4317
```

> **Note:** If your backend is in a *different* Railway project than this stack, you must use the public URL of the stack services (e.g., `https://railway-grafana-stack-production.up.railway.app/loki/...`). However, private networking (`http://loki:3100`) is recommended for performance and security.

## 2. Verification

After adding these variables, Railway will redeploy your backend. Once deployed, run these verification steps:

### A. Check Instrumentation Health
Run this command against your **backend URL**:
```bash
curl https://gatewayz-staging.up.railway.app/api/instrumentation/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "loki": { "enabled": true, "url": "http://loki:3100/loki/api/v1/push" ... },
  "tempo": { "enabled": true, "endpoint": "http://tempo:4318" ... }
}
```

### B. Generate Test Data
Trigger a test log and trace to confirm they appear in Grafana:

**1. Test Log:**
```bash
curl -X POST \
  -H "Authorization: Bearer <YOUR_ADMIN_API_KEY>" \
  https://gatewayz-staging.up.railway.app/api/instrumentation/test-log
```

**2. Test Trace:**
```bash
curl -X POST \
  -H "Authorization: Bearer <YOUR_ADMIN_API_KEY>" \
  https://gatewayz-staging.up.railway.app/api/instrumentation/test-trace
```

### C. Verify in Grafana
1. Open Grafana.
2. Go to **Loki Logs Dashboard**: You should see the test log.
3. Go to **Tempo Distributed Tracing Dashboard**: Search for the `trace_id` returned by the test command.

## 3. Troubleshooting

- **Connection Refused?** Ensure both services are in the same Railway project.
- **404 Not Found?** Ensure `LOKI_PUSH_URL` ends with `/loki/api/v1/push`.
- **No Data in Grafana?** Check the "Logger Stream" panel in the FastAPI Dashboard or the "Loki Logs" dashboard.
