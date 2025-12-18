# Railway Auth & Deployment Verification

## 1. Fix Grafana Login
The "Invalid username or password" error happens because Railway ignores `docker-compose.yml` environment variables. You must set them manually.

**Action:**
1. Go to your Railway Project Dashboard.
2. Click on the **Grafana** service.
3. Click the **Variables** tab.
4. Add the following variables:
   - `GF_SECURITY_ADMIN_USER` = `admin`
   - `GF_SECURITY_ADMIN_PASSWORD` = `<your-secure-password>`
5. Railway will automatically redeploy Grafana. Wait for it to finish.

## 2. Verify Fix for "400 Bad Request"
The "Same error over and over" (400 Bad Request) was caused by invalid Loki queries in the dashboard.
This has been **FIXED** on `main`.

**Action:**
1. Once Grafana redeploys (after step 1), open it in your browser.
2. **Hard Refresh** the page (Cmd+Shift+R or Ctrl+F5) to clear cached dashboard JSON.
3. Go to the **Loki Logs** dashboard.
4. Verify that the panels now load (or show "No data" instead of "Error").

**Why it failed before:**
- You were pushing to `main`, but the fix was only on `staging`.
- Now `main` has the fix (commit `58fa2f0` merged via PR #58).
- The `loki-logs.json` file on `main` now correctly uses `[5m]` instead of `$__rate_interval`.

## 3. Verify Datasource URLs
Ensure your Railway environment variables for datasources are correct (these also need to be set in Railway **Variables** tab, not just Docker Compose):

**Grafana Service Variables:**
- `LOKI_INTERNAL_URL` = `http://loki:3100`
- `PROMETHEUS_INTERNAL_URL` = `http://prometheus:9090`
- `TEMPO_INTERNAL_URL` = `http://tempo:3200`

## Summary
- **Login:** Set `GF_SECURITY_ADMIN_PASSWORD` in Railway Variables.
- **Errors:** Redeployment (triggered by variable change) + Hard Refresh will fix the 400s.
