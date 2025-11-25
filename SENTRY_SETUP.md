# Sentry Integration Guide

This guide explains how to set up Sentry for comprehensive error tracking and integrate it with your Grafana observability stack.

## What is Sentry?

Sentry is a real-time error tracking platform that helps you monitor and fix crashes in production. It provides:

- **Error Aggregation**: Groups duplicate errors into individual issues with fingerprinting
- **Error Context**: Captures breadcrumbs, user info, and environment data
- **Performance Monitoring**: Tracks transaction performance and identifies slow operations
- **Release Tracking**: Links errors to specific code releases
- **Smart Alerting**: Alerts on new errors, error regressions, and trends
- **User Impact Analysis**: Shows how many users are affected by each error

## Prerequisites

- Active Sentry account (free tier available at [sentry.io](https://sentry.io))
- Sentry organization with appropriate permissions (Owner/Manager/Admin role)
- Grafana Sentry datasource plugin installed (automatically added to Grafana)

## Step 1: Create Sentry Projects

1. **Log in to Sentry**: Visit [sentry.io](https://sentry.io)
2. **Create Projects**: You need separate projects for each application:
   - Project for Node.js API Monitor (`gatewayz-monitor`)
   - Project for FastAPI App (`fastapi-app`)

For each project:
- Choose the appropriate platform/SDK (Node.js or Python)
- Copy the **DSN** (Data Source Name) - you'll need this later

## Step 2: Generate Sentry Auth Token

For Grafana to query Sentry data:

1. **Go to Settings** → **Auth Tokens** (or Account Settings → Integrations)
2. **Create New Token** with these scopes:
   - `org:read` - Read organization data
   - `project:read` - Read project data
   - `team:read` - Read team data
   - `event:read` - Read events/issues
3. **Copy the token** - save it securely

## Step 3: Configure Railway Environment Variables

In your Railway dashboard for the Grafana service, set these variables:

```
SENTRY_DSN=<your-sentry-dsn>                    # Optional: for the services
SENTRY_ENVIRONMENT=production                   # Environment name (production/staging/development)
SENTRY_TRACE_SAMPLE_RATE=1.0                   # Sample rate for transactions (0.0-1.0)
SENTRY_AUTH_TOKEN=<your-sentry-auth-token>     # For Grafana datasource
SENTRY_INTERNAL_URL=https://sentry.io          # Sentry API URL (or your self-hosted URL)
```

### For Applications:

Each application (gatewayz_monitor, fastapi_app) needs:

```
SENTRY_DSN=<your-specific-project-dsn>         # Each app gets its own DSN
SENTRY_ENVIRONMENT=production                  # Can be different per environment
SENTRY_TRACE_SAMPLE_RATE=1.0                  # Controls performance monitoring sampling
```

## Step 4: Deploy and Verify

1. **Push your changes** to GitHub (SDKs are already integrated in the code)
2. **Railway automatically redeploys**
3. **Check application logs** for Sentry initialization messages:
   - Node.js: Look for "Sentry" in logs
   - FastAPI: Check for "sentry_sdk" initialization

4. **Trigger test errors**:
   - Node.js: Errors are automatically captured
   - FastAPI: Visit `http://your-app:8000/error` endpoint

5. **Verify in Sentry**:
   - Go to your Sentry projects
   - You should see errors appearing in real-time
   - Check Issues list for new events

## Step 5: Connect Sentry Datasource to Grafana

1. **In Grafana**, go to **Configuration** → **Data Sources**
2. **Click "Add Data Source"**
3. **Search for "Sentry"** and select the Grafana Sentry Datasource plugin
4. **Configure**:
   - **Name**: `Sentry` (or your preferred name)
   - **URL**: Your Sentry instance URL (default: `https://sentry.io`)
   - **Auth**: Add your auth token
     - Token name: `Authorization`
     - Token value: `Bearer <your-sentry-auth-token>`

5. **Test Connection** and **Save**

## Step 6: View Sentry Dashboard in Grafana

1. **Navigate to Dashboards** → **Sentry Error Tracking**
2. The pre-configured dashboard shows:
   - **Issues by Status**: Pie chart of resolved vs unresolved issues
   - **Total Issues**: Gauge showing total issue count
   - **Recent Issues**: Table of recent errors
   - **Issues Trend**: Time-series graph of error rates

### Dashboard Features:

- **Environment Filter**: Filter issues by environment (production, staging, etc.)
- **Project Filter**: Filter by specific Sentry project
- **Auto-refresh**: Updates every 10 seconds
- **Time Range**: Defaults to last 24 hours

## Understanding Sentry SDKs in the Code

### Node.js Application (`examples/api/`)

The Sentry SDK is initialized in `sentry.js`:

```javascript
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: SENTRY_DSN,
  environment: SENTRY_ENVIRONMENT,
  integrations: [
    new Sentry.Integrations.Http({ tracing: true }),
    new Sentry.Integrations.Express({ transaction: true }),
  ],
  tracesSampleRate: SENTRY_TRACE_SAMPLE_RATE,
  attachStacktrace: true,
  includeLocalVariables: true,
});
```

**What it does**:
- Captures unhandled exceptions
- Tracks HTTP requests and spans
- Includes local variables in error context
- Performance monitoring for transactions

**Error Capturing**:
- Automatically via `Sentry.Handlers.errorHandler()` middleware
- Manual: `Sentry.captureException(error)`

### FastAPI Application (`examples/fastapi-app/`)

The Sentry SDK is initialized in `main.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT,
    integrations=[FastApiIntegration()],
    traces_sample_rate=SENTRY_TRACE_SAMPLE_RATE,
    attach_stacktrace=True,
    include_local_variables=True,
)
```

**What it does**:
- Automatically instruments FastAPI endpoints
- Captures request/response data
- Tracks exceptions with full context
- Performance monitoring for slow endpoints

**Error Capturing**:
- Automatically via FastAPI exception handlers
- Manual: `sentry_sdk.capture_exception(error)`

## Configuration Options

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `SENTRY_DSN` | Data Source Name from Sentry project | Empty (Sentry disabled) | `https://key@sentry.io/project-id` |
| `SENTRY_ENVIRONMENT` | Environment name for filtering | `production` | `staging`, `development` |
| `SENTRY_TRACE_SAMPLE_RATE` | Fraction of transactions to sample (0-1) | `1.0` | `0.1` (10% sampling) |
| `SENTRY_AUTH_TOKEN` | Auth token for Grafana datasource | Empty | Bearer token |
| `SENTRY_INTERNAL_URL` | Sentry API endpoint | `http://sentry.railway.internal:9000` | `https://sentry.io` |

### Sample Rate Guidance

- **Development**: `1.0` (capture all transactions)
- **Staging**: `0.5` (50% sampling)
- **Production**: `0.1` (10% sampling) - adjust based on volume

Lower sample rates reduce Sentry quota usage for high-traffic applications.

## Integration with Observability Stack

Sentry complements your existing observability stack:

| Tool | Purpose | Data |
|------|---------|------|
| **Sentry** | Error tracking & alerting | Exceptions, errors, performance |
| **Prometheus** | Metrics collection | Request counts, latencies, error rates |
| **Loki** | Log aggregation | Application logs with context |
| **Tempo** | Distributed tracing | Request traces and spans |
| **Grafana** | Unified visualization | All of the above |

**Workflow**:
1. Error occurs in production
2. **Sentry** captures it, deduplicates, and alerts
3. **Loki** logs include error context and trace ID
4. **Tempo** shows the full request trace
5. **Prometheus** metrics show error rate spike
6. **Grafana** dashboard consolidates all signals

## Advanced Configuration

### Add Custom Context

#### Node.js:
```javascript
Sentry.setContext("user", {
  id: userId,
  email: userEmail,
});

Sentry.captureMessage("Important event", "info");
```

#### FastAPI:
```python
sentry_sdk.set_context("user", {
    "id": user_id,
    "email": user_email,
})

sentry_sdk.capture_message("Important event", "info")
```

### Release Tracking

Update `docker-compose.yml` to include release version:

```yaml
environment:
  - SENTRY_RELEASE=1.0.0
  - SENTRY_VERSION=1.0.0
```

### Source Maps (Advanced)

For production deployments, upload source maps to Sentry for better error context:

```bash
npm install --save-dev @sentry/cli

# After building, upload source maps
sentry-cli releases files upload-sourcemaps ./dist
```

## Troubleshooting

### Errors Not Appearing in Sentry

1. **Check DSN Configuration**:
   - Verify `SENTRY_DSN` is correctly set
   - Ensure it's the right project DSN

2. **Check Application Logs**:
   ```bash
   railway logs --service fastapi_app
   railway logs --service gatewayz_monitor
   ```

3. **Verify Network Connectivity**:
   - Check if your Railway services can reach `sentry.io`
   - Self-hosted Sentry requires correct URL in `SENTRY_INTERNAL_URL`

4. **Test Manually**:
   - FastAPI: Visit `/error` endpoint to trigger test error
   - Check Sentry project for incoming event

### Grafana Datasource Connection Failed

1. **Verify Auth Token**:
   - Check token exists and has correct scopes
   - Try creating a new token if issues persist

2. **Check URL Configuration**:
   - For cloud: Use `https://sentry.io`
   - For self-hosted: Use your instance URL

3. **Test in Grafana**:
   - Go to Configuration → Data Sources → Sentry
   - Click "Save & Test"
   - Check error message for details

### High Quota Usage

1. **Reduce Sample Rate**:
   ```
   SENTRY_TRACE_SAMPLE_RATE=0.1  # Only 10% of transactions
   ```

2. **Exclude Certain Paths**:
   ```python
   # In FastAPI
   SENTRY_TRACES_SAMPLE_RATE = 0.1  # for transactions
   ```

3. **Set Error Filtering**:
   - In Sentry project settings → Inbound Filters
   - Ignore specific error types or paths

## Best Practices

1. **Use Different DSNs Per Environment**:
   - Separate projects for production/staging/development
   - Makes filtering and alerting easier

2. **Set Meaningful Releases**:
   - Include version number or git commit hash
   - Helps correlate errors to code changes

3. **Monitor Sentry Quota**:
   - Check quota usage in Sentry Settings
   - Plan for growth or upgrade plan as needed

4. **Configure Alerts**:
   - Set up Slack/email alerts for new errors
   - Use rules to avoid alert fatigue

5. **Regular Review**:
   - Review unresolved issues weekly
   - Mark fixed issues as resolved
   - Archive known/expected errors

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Sentry Node.js SDK](https://docs.sentry.io/platforms/node/)
- [Grafana Sentry Datasource](https://grafana.com/grafana/plugins/grafana-sentry-datasource/)
- [Sentry Pricing](https://sentry.io/pricing/)

## Next Steps

1. ✅ Create Sentry projects
2. ✅ Generate auth token
3. ✅ Configure environment variables in Railway
4. ✅ Deploy with Sentry integration
5. 🔔 Configure Sentry alerts in project settings
6. 📊 Create custom dashboards with Sentry data
7. 🔗 Link Sentry issues to your internal issue tracker

---

For questions or issues, refer to [Sentry docs](https://docs.sentry.io/) or the main [README](README.md).
