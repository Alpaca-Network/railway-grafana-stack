# Metric Volatility Fix - Staging Testing Guide

## Status
✅ **Deployment to Staging In Progress**
- Branch: `fix/metric-volatility-dashboards` pushed to `staging`
- Changes committed: 3 commits
- Ready for testing

---

## What's Being Tested

### Critical Fix #1: Overall System Health Gauge
**Before:** `jsonPath: ".[*].health_score"` (returns array - causes volatility)
**After:** `jsonPath: "avg_health_score"` (returns single value - stable)

**Expected Behavior:**
- Gauge displays consistent value: `100.0`
- Value remains stable across page refreshes
- No jumping between different numbers

### Critical Fix #2: Request Volume Panel
**Before:** `jsonPath: "hourly_breakdown[*].requests"` (references empty field)
**After:** Removed invalid jsonPath (uses full response data)

**Expected Behavior:**
- Panel displays available provider request data
- No error messages about missing fields
- Gracefully handles empty data

---

## Pre-Testing Checklist

Before testing, ensure:
- [ ] GitHub Actions workflow completed on staging branch
- [ ] Staging Grafana instance is running
- [ ] You can login to Grafana
- [ ] You have the staging API key available

---

## Test Procedure

### Test 1: Overall System Health Gauge - Stability Test ⭐ CRITICAL

**Objective:** Verify metrics are stable across multiple refreshes

**Steps:**
1. Open Grafana staging instance
2. Login with your credentials
3. Navigate to: **Dashboards → Executive Overview**
4. Look at the **"Overall System Health"** gauge (top-left panel)
5. Note the current value
6. **Refresh the page** (Cmd+R or Ctrl+R)
7. **Repeat 9 more times** (total 10 refreshes)
8. Record the values from each refresh

**Example Test Run:**
```
Refresh 1: 100.0
Refresh 2: 100.0
Refresh 3: 100.0
Refresh 4: 100.0
Refresh 5: 100.0
Refresh 6: 100.0
Refresh 7: 100.0
Refresh 8: 100.0
Refresh 9: 100.0
Refresh 10: 100.0
```

**✅ PASS Criteria:**
- All 10 values are identical
- Value remains stable across refreshes
- Gauge displays consistent metric

**❌ FAIL Criteria:**
- Values jump around (2, 50, 25, etc.)
- Values are different on each refresh
- Gauge shows unpredictable numbers

---

### Test 2: Other Stat Panels - Value Verification

**Objective:** Verify other metrics display correctly

**Panels to Check:**
1. Active Requests/min
2. Avg Response Time
3. Daily Cost
4. Error Rate (%)

**Steps for Each Panel:**
1. Refresh page 5 times
2. Observe the panel value
3. Verify it stays consistent (or null if no data)
4. Note any console errors

**✅ PASS Criteria:**
- Values remain consistent across refreshes
- No error messages in panels
- Values may be 0 or null if no live traffic, but consistent

**❌ FAIL Criteria:**
- Values jump around or change unexpectedly
- Error messages appear in panels
- Red error icons in the dashboard

---

### Test 3: Time Range Changes

**Objective:** Verify dashboard works with different time ranges

**Steps:**
1. Click the time range selector (top-right)
2. Select "Last 24 hours"
3. Wait for data to load
4. Refresh the page 3 times
5. Verify "Overall System Health" gauge still stable
6. Repeat with "Last 7 days" and "Last 30 days"

**✅ PASS Criteria:**
- Dashboard updates with each time range
- "Overall System Health" remains stable
- No loading errors
- All panels responsive

**❌ FAIL Criteria:**
- Gauge becomes unstable with different time ranges
- Data loading fails
- Panels show errors

---

### Test 4: Browser Console Check

**Objective:** Verify no JSON parsing errors

**Steps:**
1. Press **F12** to open Developer Tools
2. Click the **Console** tab
3. Refresh the dashboard page
4. Watch console for errors
5. Look specifically for:
   - `jsonPath` errors
   - `parse error` messages
   - `JSON` errors
   - Red error messages

**✅ PASS Criteria:**
- Console shows no red errors
- No jsonPath parsing errors
- No JSON parse failures
- Clean console output

**❌ FAIL Criteria:**
- Red error messages appear
- jsonPath or parse errors logged
- JSON parsing failures
- Multiple console warnings

---

### Test 5: All 9 Panels Functional Test

**Objective:** Verify all dashboard panels load and function

**Panels to Check:**
1. ✅ Header (title panel)
2. ✅ Overall System Health (gauge)
3. ✅ Provider Health Status (stat table)
4. ✅ Active Requests/min (stat)
5. ✅ Avg Response Time (stat)
6. ✅ Daily Cost (stat)
7. ✅ Error Rate (%) (stat)
8. ✅ Request Volume (24h) (timeseries)
9. ✅ Error Rate Distribution (piechart)
10. ✅ Critical Anomalies (table)

**Steps:**
1. Scroll through entire dashboard
2. Verify each panel loads without errors
3. Check for missing data or error icons
4. Confirm all panels are visible

**✅ PASS Criteria:**
- All 10 panels visible and functional
- No panels showing error state
- All data displays correctly
- No missing/broken elements

**❌ FAIL Criteria:**
- Any panel shows error icon
- Any panel is blank/empty
- Missing panels
- Broken layout

---

## Expected Results Summary

| Test | Expected | Status |
|------|----------|--------|
| Gauge Stability | Value 100.0 on all 10 refreshes | ✅ PASS |
| Other Metrics | Consistent values across refreshes | ✅ PASS |
| Time Range Changes | Dashboard responsive, gauge stable | ✅ PASS |
| Console Errors | No jsonPath/parse errors | ✅ PASS |
| All Panels | All 10 panels load, no errors | ✅ PASS |

---

## Reporting Results

### If All Tests Pass ✅
Great! The fix is working correctly.

**Next Steps:**
1. Send me this message: "All tests passed - metrics are stable"
2. I'll create a Pull Request for main branch
3. We'll proceed to production deployment

### If Any Test Fails ❌
Please provide:

1. **Screenshot** of the issue
2. **Test #** that failed
3. **What you observed:**
   - Specific values shown
   - Any error messages
   - Unexpected behavior
4. **Browser** and **OS** information

Example:
```
Test #1 Failed: Overall System Health Gauge
Observed: Values jumping (100.0 → 50 → 25 → 100.0)
Browser: Chrome on Mac
Error: None in console
```

---

## Quick Reference

### Access Staging Grafana
- **URL:** [Your staging Grafana instance]
- **Login:** [Your credentials]

### View GitHub Status
- **URL:** https://github.com/Alpaca-Network/railway-grafana-stack/actions
- **Filter:** Branch = staging
- **Look for:** Workflow "Staging Tests - Stack Configuration"

### Revert If Issues
```bash
# If major issues found, can revert:
git push origin main:staging  # Revert staging to main
```

---

## Test Execution Checklist

- [ ] Accessed staging Grafana
- [ ] Test 1: Gauge Stability - 10 refreshes completed
- [ ] Test 2: Other Stat Panels - 5 refreshes completed
- [ ] Test 3: Time Range Changes - Tested 3 ranges
- [ ] Test 4: Browser Console - Checked for errors
- [ ] Test 5: All Panels - Verified all 10 panels
- [ ] Took screenshots if any issues
- [ ] Reported results back

---

## Troubleshooting

**Q: Dashboard won't load in staging?**
A: Check that staging Grafana is running and accessible. Verify staging branch deployment completed.

**Q: Still seeing volatile metrics?**
A: Clear browser cache (Ctrl+Shift+Delete), then refresh. If still failing, report the exact values you see.

**Q: Getting jsonPath errors in console?**
A: This would indicate the fix wasn't properly deployed. Check that fix/metric-volatility-dashboards branch was pushed to staging.

**Q: Metrics show null or 0 values?**
A: This is normal if there's no live traffic. As long as values are consistent across refreshes, the fix is working.

---

## Summary

**What's Being Tested:** Metric volatility fix in Executive Overview dashboard
**Critical Panel:** "Overall System Health" gauge
**Expected Result:** Stable, consistent metric values (no jumping/shifting)
**Success Criteria:** All 5 tests pass with no errors

**Estimated Testing Time:** 10-15 minutes

---

**Status:** ✅ Ready for Staging Testing
**Created:** December 30, 2025
**Last Updated:** December 30, 2025
