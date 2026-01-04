# Dashboard Expansion Plan - Logs & Backend Health

## Overview
Create 2 comprehensive new monitoring dashboards with reusable components from all 14 existing dashboards, enhanced with better visual hierarchy, color coding, and alert indicators.

---

## Phase 1: Analysis & Component Extraction

### Step 1.1: Audit All 14 Dashboards
Extract reusable components from:
- ✅ FastAPI Dashboard
- ✅ Model Health
- ✅ GatewayZ App Health
- ✅ GatewayZ Backend Metrics
- ✅ GatewayZ Redis Services
- ✅ Loki Logs
- ✅ Prometheus Metrics
- ✅ Tempo Distributed Tracing
- ✅ Executive Overview (v1)
- ✅ Model Performance Analytics (v1)
- ✅ Gateway & Provider Comparison (v1)
- ✅ Real-Time Incident Response (v1)
- ✅ Tokens & Throughput Analysis (v1)
- ⚠️ Chat Completion Monitoring (may be deprecated)

**Components to Extract:**
- Gauge panels (health scores, uptime %)
- Stat panels (counts, metrics)
- Tables (detailed data)
- Time series charts (trends)
- Pie/donut charts (distributions)
- Alert/anomaly tables

---

## Phase 2: Logs Dashboard Design

### 2.1: Dashboard Structure
**UID:** `logs-monitoring-v1`
**Title:** Logs & Diagnostics Dashboard
**Refresh Rate:** 30s (balance between freshness and performance)

### 2.2: Sections & Panels

#### Section 1: Log Overview (Top)
- **Real-time Log Count** (stat card - green/yellow/red)
- **Error Count (24h)** (stat card - prominent RED if >0)
- **Log Sources/Services** (table with count)
- **Critical Alerts** (red banner if errors detected)

#### Section 2: Error Analysis (High Priority)
- **Error Logs Timeline** (timeseries - 24h)
- **Errors by Severity** (pie chart: CRITICAL/ERROR/WARNING)
- **Errors by Service** (bar chart)
- **Top Error Messages** (table - clickable for details)

#### Section 3: API Request Logs
- **Request Trace Table** (with latency, status, service)
- **Status Code Distribution** (pie chart: 200/4xx/5xx)
- **Latency Distribution** (histogram or heatmap)
- **Slow Requests Alert** (table of requests >500ms)

#### Section 4: Performance Issues
- **Slow Query Detection** (timeseries)
- **Timeout Events** (table - when and where)
- **Resource-Heavy Queries** (bar chart)
- **Performance Trend** (24h/7d/30d selector)

#### Section 5: Log Search (Bottom - Flexible)
- **Loki Log Search Panel** (raw log search)
- **Advanced Filters** (service, level, timestamp)
- **Raw Log View** (with timestamps and context)

### 2.3: Data Sources & Queries
- **Loki** - Log aggregation and search
- **Prometheus** (if available) - Error metrics
- **Custom endpoints** - Log statistics
- **Tempo** - Distributed trace correlation

---

## Phase 3: Backend Health Dashboard Design

### 3.1: Dashboard Structure
**UID:** `backend-health-v1`
**Title:** Backend Health & Service Status
**Refresh Rate:** 10s (real-time health monitoring)

### 3.2: Sections & Panels

#### Section 1: System Health Overview (Top - Prominent)
- **Overall Health Score** (large gauge - 0-100)
- **Services Status Summary** (table: 17 providers + Redis/DB/Cache)
- **Critical Issues Badge** (red alert if any critical)
- **Last Updated Timestamp**

#### Section 2: Provider Health (Detailed)
- **Provider Health Grid** (stat cards: 4 columns × 4-5 rows)
  - Each provider shows: name, health%, uptime%, response time
  - Color coded: Green (>95%), Yellow (80-95%), Red (<80%)
- **Provider Availability Trend** (7d timeseries for each provider)
- **Provider Error Rate Comparison** (bar chart)

#### Section 3: Service Dependencies (Critical)
- **Redis Health** (gauge + latency stats)
- **Database Connection Pool** (gauge for connections)
- **Cache Status** (hit rate, eviction stats)
- **Message Queue Depth** (if applicable)
- **Connection Health Table** (status, uptime, response time)

#### Section 4: Circuit Breaker Status (Real-time)
- **Circuit Breaker States** (table: Provider → State → Reason → Last Trip Time)
- **Circuit Breaker Timeline** (timeseries - open/closed state changes)
- **MTTR (Mean Time To Recovery)** (stats by provider)
- **Trip Frequency** (24h count - alert if >5 trips/day)

#### Section 5: Resource Utilization
- **CPU Usage** (timeseries per service)
- **Memory Usage** (timeseries per service)
- **Connection Pool Utilization** (gauge per service)
- **Request Queue Depth** (timeseries)
- **Disk I/O** (if available)

#### Section 6: Alerts & Anomalies (Bottom)
- **Active Alerts Table** (fired alerts with timestamps)
- **Health Score Trend** (7d historical, with anomalies marked)
- **SLA/Uptime Report** (monthly uptime %)

---

## Phase 4: Visual Enhancement Strategy

### Color Coding & Thresholds
```
Health Score / Uptime %:
  Red:    < 80%   (Critical)
  Yellow: 80-95%  (Warning)
  Green:  > 95%   (Healthy)

Response Time (ms):
  Green:  < 100ms
  Yellow: 100-500ms
  Red:    > 500ms

Error Rate %:
  Green:  0-1%
  Yellow: 1-5%
  Red:    > 5%

Circuit Breaker:
  Green:  CLOSED (normal)
  Red:    OPEN (tripped)
```

### Alert Badges & Icons
- 🔴 Critical (errors, outages)
- 🟡 Warning (degraded performance)
- 🟢 Healthy (all systems operational)
- ⚠️ Anomaly (unusual pattern detected)

### Panel Sizing Strategy
**Large Panels (4-6 grid width):**
- Overall Health Score (most critical)
- Health Score Trend (historical view)
- Provider Health Grid (17 providers - need space)
- Circuit Breaker Status (important for visibility)

**Medium Panels (3 grid width):**
- Service Dependencies
- Error Timeline
- Availability Comparison
- Status Distribution

**Small Panels (2 grid width):**
- Count metrics (alerts, errors)
- Single service stats
- Status badges

---

## Phase 5: Implementation Tasks

### 5.1: Data Availability Assessment
Need to verify these endpoints exist:
- [ ] Loki endpoints for logs
- [ ] Error metrics endpoints
- [ ] Circuit breaker status endpoint
- [ ] Resource utilization endpoints
- [ ] Service health check endpoints
- [ ] Performance metrics endpoints

### 5.2: Create Logs Dashboard
- [ ] Build dashboard structure JSON
- [ ] Add Loki queries
- [ ] Add error log panels
- [ ] Add API request tracking
- [ ] Add performance issue detection
- [ ] Apply color coding & thresholds
- [ ] Add alert badges

### 5.3: Create Backend Health Dashboard
- [ ] Build dashboard structure JSON
- [ ] Add health score gauge
- [ ] Add provider health grid (17 providers)
- [ ] Add service dependency monitoring
- [ ] Add circuit breaker status
- [ ] Add resource utilization panels
- [ ] Add alert & anomaly detection
- [ ] Apply visual enhancements

### 5.4: Link Dashboards
- [ ] Update Executive Overview with nav links to:
  - Logs & Diagnostics
  - Backend Health & Status
- [ ] Add cross-links between new dashboards
- [ ] Add breadcrumb navigation

### 5.5: Make Existing Components More Apparent
- [ ] Increase critical metric panel sizes
- [ ] Add color coding to all thresholds
- [ ] Add alert badges/icons
- [ ] Reorganize panels by importance
- [ ] Add section headers/grouping
- [ ] Apply consistent styling across dashboards

---

## Concerns & Mitigation

### ⚠️ Concern #1: Data Availability
**Issue:** Some endpoints may not be implemented
**Mitigation:**
- [ ] Verify all endpoints first (endpoint testing)
- [ ] Create placeholder panels for missing data
- [ ] Document which endpoints are required
- [ ] Create fallback queries if needed

### ⚠️ Concern #2: Performance
**Issue:** Too many panels = slow dashboard loading
**Mitigation:**
- [ ] Use dashboard tags for filtering
- [ ] Implement panel refresh optimization
- [ ] Use variable-based panel visibility (show/hide)
- [ ] Lazy load optional sections
- [ ] Monitor dashboard load time

### ⚠️ Concern #3: Complexity
**Issue:** Too much information might be overwhelming
**Mitigation:**
- [ ] Organize by importance (critical → optional)
- [ ] Use collapsible sections
- [ ] Add "quick view" mode (summary only)
- [ ] Provide detailed view (all panels)
- [ ] Add help text/tooltips

---

## Success Criteria

✅ **Logs Dashboard:**
- [ ] All 4 focus areas covered (search, errors, API logs, performance)
- [ ] Real-time error detection and alerting
- [ ] Search capability functional
- [ ] Load time < 5 seconds

✅ **Backend Health Dashboard:**
- [ ] All 3 metric types visible (resources, circuit breakers, dependencies)
- [ ] Real-time health scoring
- [ ] Visual status indicators clear and accurate
- [ ] Load time < 5 seconds

✅ **Visual Enhancements:**
- [ ] All color coding applied correctly
- [ ] Alert badges show on critical issues
- [ ] Panels organized logically
- [ ] Critical metrics prominent (larger sizes)

✅ **Integration:**
- [ ] Executive Overview links to both new dashboards
- [ ] Cross-dashboard navigation working
- [ ] All existing components still functional
- [ ] No regression in existing dashboards

---

## Estimated Work Breakdown

| Phase | Task | Complexity | Time |
|-------|------|-----------|------|
| 1 | Analyze 14 dashboards | Medium | 30 min |
| 2 | Design Logs dashboard | Medium | 45 min |
| 3 | Design Backend Health | Medium | 45 min |
| 4 | Visual enhancements | Low | 30 min |
| 5 | Create Logs JSON | High | 1.5h |
| 5 | Create Backend Health JSON | High | 1.5h |
| 5 | Link dashboards & navigation | Medium | 30 min |
| 5 | Testing & verification | Medium | 45 min |
| **TOTAL** | | | **6-7 hours** |

---

## Concerns & Questions from User

✅ **Data Availability Concern** - Plan: Verify endpoints first
✅ **Performance Concern** - Plan: Implement refresh optimization
✅ **Complexity Concern** - Plan: Organize by importance with filtering
✅ **Visual Enhancement** - Plan: Color coding, badges, larger panels
✅ **Comprehensive Approach** - Plan: Include all relevant metrics

---

## Next Steps (Upon Approval)

1. ✅ Verify all required endpoints are implemented
2. ✅ Create Logs dashboard JSON
3. ✅ Create Backend Health dashboard JSON
4. ✅ Update Executive Overview with navigation
5. ✅ Test all panels and queries
6. ✅ Deploy to staging for testing
7. ✅ Merge to production

---

**Status:** Ready for Implementation (Upon Your Approval)
**Created:** December 30, 2025
**Estimated Completion:** ~6-7 hours of development
