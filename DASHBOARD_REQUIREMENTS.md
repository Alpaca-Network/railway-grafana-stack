# 📊 Dashboard Requirements Analysis
**Created:** 2025-12-28
**Purpose:** Detailed specification of data sources, endpoints, and requirements for 6-dashboard monitoring suite
**Status:** 🔍 Requirements Definition Phase

---

## Executive Summary

The 6-dashboard suite requires data from **7 major categories**. This document identifies every data point needed, its source, granularity, and expected format.

---

## 📈 Data Categories & Requirements

### Category 1: Provider/Gateway Metrics

**Definition**: Real-time and historical metrics for all 17 providers

**Required Metrics Per Provider**:
```
├── Real-time Metrics
│   ├── Health Score (0-100)
│   ├── Status (healthy/warning/critical)
│   ├── Requests/minute (current)
│   ├── Errors/minute (current)
│   ├── Error Rate % (current)
│   ├── Avg Latency (p50, p95, p99, p999)
│   └── Uptime % (24h)
│
├── Financial Metrics
│   ├── Cost (24h, 7d, 30d)
│   ├── Cost per request
│   └── Cost trend
│
├── Token Metrics
│   ├── Total tokens (24h, 7d, 30d)
│   ├── Tokens/second (throughput)
│   └── Cost per million tokens
│
└── Availability Metrics
    ├── Availability % (24h, 7d, 30d)
    └── Circuit breaker status
```

**Data Granularity Needed**:
- Real-time: 1-minute intervals (last 24h)
- Historical: 1-hour aggregates (7d, 30d)
- Latest value: Current health score, status

**Used By Dashboards**: All 6 dashboards
**Sample Endpoint Pattern**: `/api/providers/{provider_slug}/metrics`

---

### Category 2: Model-Level Metrics

**Definition**: Metrics broken down by specific model (gpt-4o, claude-sonnet, etc.)

**Required Metrics Per Model**:
```
├── Usage Metrics
│   ├── Total requests (24h, 7d, 30d)
│   ├── Requests/second (throughput)
│   ├── Error count & error rate %
│   └── Success rate %
│
├── Performance Metrics
│   ├── Latency (p50, p95, p99, p999)
│   ├── Response time distribution
│   └── Timeout rate %
│
├── Token Metrics
│   ├── Input tokens (total & avg per request)
│   ├── Output tokens (total & avg per request)
│   ├── Completion ratio (output/input)
│   └── Cost per token
│
├── Financial Metrics
│   ├── Cost (24h, 7d, 30d)
│   ├── Cost per request
│   ├── Cost vs budget (if model has budget)
│   └── Cost trend
│
└── Model Properties
    ├── Provider name (which provider hosts this model)
    ├── Model family (GPT, Claude, Llama, etc.)
    └── Max tokens / context window
```

**Data Granularity Needed**:
- Real-time: 1-minute intervals (last 24h)
- Historical: 1-hour aggregates (7d)
- Latest value: Current requests/sec, cost/token

**Used By Dashboards**: Dashboard 2 (primary), Dashboard 4 (cost), Dashboard 6 (tokens)
**Sample Endpoint Pattern**: `/api/models/{model_id}/metrics` or `/api/models/list`

---

### Category 3: Error & Incident Data

**Definition**: Detailed error tracking for incident response

**Required Data Per Error**:
```
├── Error Identification
│   ├── Timestamp (when occurred)
│   ├── Error type (timeout, rate_limit, invalid_request, server_error, auth_error)
│   ├── Error message
│   └── Error code (if applicable)
│
├── Context
│   ├── Affected provider
│   ├── Affected model
│   ├── Request ID (for tracing)
│   └── User/API key (for analysis)
│
├── Impact
│   ├── Error count (recent)
│   ├── Error rate % (recent)
│   └── Error trend (increasing/stable/decreasing)
│
└── Details (for drill-down)
    ├── Stack trace
    ├── Request payload (sanitized)
    └── Response details
```

**Aggregate Metrics Needed**:
- Error rate % by provider (last 24h, 7d)
- Error rate % by model (last 24h)
- Error type distribution (pie chart data)
- Error count time series (5-min intervals)
- Recent error feed (tail of last 100 errors)

**Data Granularity Needed**:
- Real-time: 1-minute intervals
- Tail log: Last 100-1000 events with 5s refresh
- Historical: 1-hour aggregates for trends

**Used By Dashboards**: Dashboard 5 (primary), Dashboard 1 (alert list), Dashboard 3 (error rate comparison)
**Sample Endpoint Pattern**: `/api/errors` (tail), `/api/errors/stats/{provider}`, `/api/errors/stats/by-type`

---

### Category 4: Financial & Business Metrics

**Definition**: Revenue, cost, and budget tracking

**Required Data**:
```
├── Revenue Metrics
│   ├── Daily revenue (current day)
│   ├── Revenue trend (7d, 30d)
│   ├── Revenue by model/provider
│   └── Revenue vs cost (profit)
│
├── Cost Metrics
│   ├── Daily cost breakdown
│   │   ├── By provider
│   │   ├── By model
│   │   └── By customer/team
│   ├── Cost trends (7d, 30d)
│   ├── Cost per request (weighted avg)
│   └── Cost per token (weighted avg)
│
├── Budget & Allocation
│   ├── Monthly budget (total)
│   ├── Budget allocation by model
│   ├── Budget allocation by provider
│   ├── Current spend vs budget
│   ├── Projected vs budget (forecast)
│   └── Budget alerts (% of budget used)
│
└── Financial Health
    ├── Profit margin % (revenue - cost / revenue)
    ├── Cost per request trend
    ├── Cost per token trend
    └── Unit economics by model
```

**Data Granularity Needed**:
- Daily: Cost and revenue snapshots
- Hourly: Cost trends (for visualization)
- Real-time: Current day cost/revenue running totals
- Monthly/Historical: For trend lines

**Used By Dashboards**: Dashboard 4 (primary), Dashboard 1 (KPIs), Dashboard 2 (cost ranking)
**Sample Endpoint Pattern**: `/api/financial/revenue`, `/api/financial/costs`, `/api/financial/budget`

---

### Category 5: SLO & Availability Metrics

**Definition**: Service level objectives and availability tracking

**Required Data**:
```
├── SLO Definition
│   ├── Target availability % (e.g., 99.9%)
│   ├── Target latency p95 (e.g., 500ms)
│   ├── Target error rate % (e.g., <1%)
│   └── Reporting period (daily, weekly, monthly)
│
├── SLO Compliance
│   ├── Current availability % vs target
│   ├── Current latency vs target
│   ├── Current error rate vs target
│   ├── Compliance status (pass/fail/warning)
│   └── Compliance trend (7d, 30d)
│
├── Availability Metrics
│   ├── Uptime % (provider level)
│   ├── Downtime incidents (count, duration)
│   ├── Incident timestamps
│   └── Incident severity
│
└── Circuit Breaker Status
    ├── Is breaker OPEN/CLOSED (per provider)
    ├── Time in current state
    ├── Failure count (why it opened)
    └── Last failure timestamp
```

**Data Granularity Needed**:
- Real-time: Current SLO compliance
- Hourly: Availability %, uptime %
- Incidents: Timestamp + duration
- Circuit breaker: Current state (no history needed)

**Used By Dashboards**: Dashboard 5 (primary), Dashboard 1 (alerts), Dashboard 3 (uptime comparison)
**Sample Endpoint Pattern**: `/api/slo/status`, `/api/health/availability`, `/api/providers/{provider}/breaker-status`

---

### Category 6: Token Metrics (Detailed)

**Definition**: Comprehensive token usage and efficiency tracking

**Required Data**:
```
├── Token Counts (by time period)
│   ├── Total input tokens
│   ├── Total output tokens
│   ├── Total tokens (input + output)
│   ├── Average tokens per request
│   └── Tokens per second (throughput)
│
├── Token Distribution
│   ├── Tokens by model (top 10)
│   ├── Tokens by provider
│   ├── Input vs output ratio (per model)
│   └── Token cost breakdown
│
├── Token Efficiency
│   ├── Estimated tokens vs actual
│   ├── Efficiency ratio (how close to estimate)
│   ├── Token waste % (over-estimation)
│   └── Token optimization opportunities
│
└── Cost Per Token
    ├── Weighted average $/token
    ├── $/token by provider
    ├── $/token by model
    └── $/token trend (7d, 30d)
```

**Data Granularity Needed**:
- Hourly: Token counts for trends
- Per request: Input/output breakdown (for averaging)
- Daily: Cost per token calculations
- Historical: 7d, 30d aggregates

**Used By Dashboards**: Dashboard 6 (primary), Dashboard 2 (model comparison), Dashboard 4 (cost per token)
**Sample Endpoint Pattern**: `/api/tokens/usage`, `/api/tokens/stats/{model}`, `/api/tokens/efficiency`

---

### Category 7: Metadata & Configuration

**Definition**: Static/slowly-changing reference data

**Required Data**:
```
├── Provider Definitions (17 total)
│   ├── Provider name & slug
│   ├── Provider status (active/deprecated/beta)
│   ├── Assigned color (for consistent visualization)
│   ├── Supported models (list)
│   ├── Website/docs URL
│   └── Contact info
│
├── Model Definitions
│   ├── Model name & ID
│   ├── Model family (GPT/Claude/Llama/etc)
│   ├── Provider (which provider hosts it)
│   ├── Context window size
│   ├── Max tokens (output limit)
│   ├── Cost per 1M tokens (input/output separate)
│   ├── Is deprecated? (boolean)
│   ├── Release date
│   └── Description
│
├── Dashboard Configuration
│   ├── Budget limits (monthly, by model)
│   ├── SLO targets (latency, availability, error rate)
│   ├── Alert thresholds (cost spike, error spike, etc.)
│   ├── Refresh rates per dashboard
│   └── Color scheme/theme
│
└── User/Team Information
    ├── Team name
    ├── API keys (masked)
    ├── Assigned budget
    └── Notification preferences
```

**Data Type**: Static/Reference - minimal refresh needed
**Used By**: All dashboards for labeling, filtering, drilling down
**Sample Endpoint Pattern**: `/api/providers/list`, `/api/models/list`, `/api/config/dashboard`

---

## 🔄 Dashboard-to-Data Mapping

### Dashboard 1: Executive Overview
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Overall Health Score | Provider avg health (all 17) | 30s | Aggregate metric |
| Active Requests/min | Sum of all providers | 15s | Real-time |
| Avg Response Time | Weighted avg of all providers | 30s | By request volume |
| Daily Cost | Sum from financial system | 60s | Running total |
| Provider Health Grid (17) | Individual provider health | 60s | Color-coded status |
| Request Volume (24h) | Hourly aggregates | 30s | All providers combined |
| Error Rate Distribution | Error % by provider | 60s | Latest 24h data |
| Alert List | Errors/anomalies (recent) | 30s | Tail of incidents |

---

### Dashboard 2: Model Performance Analytics
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Top 5 Models | Models sorted by requests (7d) | 60s | From model metrics |
| Models with Issues | Models with high error % | 30s | >5% error threshold |
| Request Volume (7d) | Hourly by model | 60s | Stacked area/bar |
| Cost per Model | Cost totals ranked | 300s | 7d aggregates |
| Latency Distribution | P50, P95, P99 per model | 60s | Top 10 models |
| Success Rate vs Usage | XY: success% vs request count | 60s | Bubble size = cost |
| Performance Heatmap | Model x Time heatmap | 60s | Hour x model grid |
| Model Health Gauge | Weighted score (top 3) | 30s | Custom calculation |

---

### Dashboard 3: Gateway & Provider Comparison
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Health Gauge Grid (17) | Individual health scores | 60s | 6-column grid |
| Comparison Matrix | All metrics per provider | 300s | 10+ columns |
| Cost vs Reliability | XY: cost/req vs success% | 300s | Bubble = volume |
| Request Distribution | % by provider (pie) | 60s | 7d data |
| Cost Distribution | % by provider (pie) | 60s | 7d data |
| Latency Distribution | P95 by provider (violin) | 60s | Statistical view |
| Cost Trend | Line per provider (7d) | 300s | 1-hour granularity |
| Uptime Trend | Uptime % per provider (7d) | 300s | 1-hour granularity |

---

### Dashboard 4: Business & Financial Metrics
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Daily Revenue | Today's revenue total | 60s | Running total |
| Daily Cost | Today's cost total | 60s | Running total |
| Profit Margin | (Revenue - Cost) / Revenue % | 60s | Calculated |
| Cost by Model | Treemap hierarchical view | 300s | All models |
| Cost Trend | Area chart with budget line | 300s | 7d with rolling avg |
| Cost/Token vs Throughput | XY scatter | 300s | Efficiency view |
| Top 5 Expensive Models | Bar chart ranked | 300s | 7d totals |
| Cost Optimization Tips | Text recommendations | Static/600s | Auto-generated? |

---

### Dashboard 5: Real-Time Incident Response
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Alert List (top) | Critical anomalies | 15s | Sorted by severity |
| Error Rate (real-time) | Error % with threshold bands | 10s | 5-min granularity |
| SLO Compliance Gauge | % vs target (e.g., 99.9%) | 30s | Green/yellow/red |
| Recent Errors Table | Error log tail | 5s | Last 100 events |
| Circuit Breaker Status | OPEN/CLOSED per provider | 30s | 17-item grid |
| Availability Heatmap | 24h x 17 providers | 60s | Uptime visualization |
| Request Success Rate | % successful vs failed | 15s | Real-time trend |
| Application Logs | Raw log tail | 5s | Last 50 lines |

---

### Dashboard 6: Tokens & Throughput Analysis
| Panel | Required Data | Refresh | Notes |
|-------|--------------|---------|-------|
| Total Tokens (24h) | Sum of all tokens | 60s | Big stat |
| Tokens/Second | Current throughput | 30s | Real-time |
| Cost per 1M Tokens | Weighted average | 300s | Financial calc |
| Tokens by Model | Horizontal bar (input/output) | 60s | Top 10 models |
| Input:Output Ratio | XY scatter per model | 60s | Bubble = cost |
| Efficiency Gauge | Estimated vs actual ratio | 60s | 0-100 scale |
| Tokens/Sec Trend (7d) | Line stacked by provider | 300s | 1-hour granularity |
| Cost/Token Trend (7d) | Line with benchmark | 300s | 1-hour granularity |

---

## 🌐 API Endpoint Design Recommendations

### Provider Metrics Endpoints

**Option A: Comprehensive Single Endpoint**
```bash
GET /api/providers/metrics
Response: {
  timestamp: "2025-12-28T10:30:00Z",
  providers: [
    {
      slug: "openrouter",
      name: "OpenRouter",
      health_score: 95,
      status: "healthy",
      realtime: {
        requests_per_minute: 1245,
        errors_per_minute: 8,
        error_rate_percent: 0.64,
        avg_latency_ms: 245,
        p50_latency_ms: 120,
        p95_latency_ms: 450,
        p99_latency_ms: 890
      },
      availability: {
        uptime_24h_percent: 99.95,
        uptime_7d_percent: 99.87,
        circuit_breaker_open: false
      },
      financial: {
        cost_24h: 3456.78,
        cost_7d: 24123.45,
        cost_30d: 89234.56,
        cost_per_request: 0.00012
      },
      tokens: {
        total_24h: 1234567,
        tokens_per_second: 14285,
        cost_per_million: 2.80
      }
    },
    // ... 16 more providers
  ]
}
```

**Option B: Separate Endpoints (more granular)**
```bash
GET /api/providers/list
GET /api/providers/{slug}/health
GET /api/providers/{slug}/realtime
GET /api/providers/{slug}/availability
GET /api/providers/{slug}/financial
GET /api/providers/{slug}/tokens
```

### Model Metrics Endpoints

```bash
GET /api/models/list
Response: [
  {
    id: "gpt-4o",
    name: "GPT-4o",
    provider: "openrouter",
    model_family: "gpt",
    context_window: 128000,
    cost_per_1m_input: 5.00,
    cost_per_1m_output: 15.00
  },
  // ... all models
]

GET /api/models/{model_id}/metrics
Response: {
  model_id: "gpt-4o",
  timestamp: "2025-12-28T10:30:00Z",
  period: "24h",  // or "7d", "30d"
  usage: {
    total_requests: 45678,
    success_count: 45234,
    error_count: 444,
    success_rate_percent: 98.97,
    requests_per_second: 0.528
  },
  performance: {
    p50_latency_ms: 120,
    p95_latency_ms: 450,
    p99_latency_ms: 890,
    timeout_rate_percent: 0.12
  },
  tokens: {
    input_tokens: 234567890,
    output_tokens: 123456789,
    total_tokens: 358024679,
    avg_input_per_request: 5143,
    avg_output_per_request: 2705,
    tokens_per_second: 4141
  },
  financial: {
    total_cost: 1234.56,
    cost_per_request: 0.027,
    cost_per_token: 0.00000344
  }
}

GET /api/models/metrics/compare
Query params: ?model_ids=gpt-4o,claude-sonnet,llama-70b&period=7d
Response: [...] // Multiple models with comparable structure
```

### Error & Incident Endpoints

```bash
GET /api/errors/recent
Query params: ?limit=100&sort=newest
Response: [
  {
    timestamp: "2025-12-28T10:25:43Z",
    error_type: "timeout",
    error_message: "Request exceeded 30s timeout",
    provider: "together",
    model: "llama-2-70b",
    error_code: 504,
    request_id: "req_abc123..."
  },
  // ... 99 more
]

GET /api/errors/stats
Query params: ?period=24h
Response: {
  total_errors_24h: 1234,
  error_rate_percent: 0.92,
  errors_by_type: {
    timeout: 456,
    rate_limit: 234,
    auth_error: 88,
    invalid_request: 45,
    server_error: 411
  },
  errors_by_provider: {
    together: 345,
    openrouter: 123,
    // ... rest of providers
  },
  trending: "decreasing"  // or "stable", "increasing"
}

GET /api/errors/stats/{provider}
Response: {
  provider: "together",
  error_count_24h: 345,
  error_rate_percent: 2.1,
  errors_by_type: {...},
  recent_errors_sample: [...]
}
```

### Financial Endpoints

```bash
GET /api/financial/daily-summary
Response: {
  date: "2025-12-28",
  revenue: 12456.78,
  cost: 3245.67,
  margin_percent: 73.96,
  requests_total: 3500000,
  tokens_total: 12345678
}

GET /api/financial/cost-breakdown
Query params: ?period=24h&group_by=model
Response: {
  period: "24h",
  total_cost: 3245.67,
  by_model: [
    {
      model: "gpt-4o",
      cost: 2431.50,
      percent_of_total: 74.9,
      requests: 2345000,
      tokens: 8934567
    },
    // ... other models
  ],
  by_provider: [...]  // Same structure
}

GET /api/financial/budget
Response: {
  monthly_budget: 100000,
  spent_so_far: 75234.56,
  percent_used: 75.23,
  days_remaining: 3,
  daily_average_spend: 8359.40,
  projected_total: 102831.99,
  over_budget: true,
  alert_level: "critical"
}
```

### SLO & Availability Endpoints

```bash
GET /api/slo/status
Response: {
  availability_target_percent: 99.9,
  current_availability_percent: 99.87,
  compliant: false,  // Very close but below target
  latency_p95_target_ms: 500,
  current_latency_p95_ms: 523,
  latency_compliant: false,
  error_rate_target_percent: 1.0,
  current_error_rate_percent: 0.92,
  error_compliant: true,
  overall_compliant: false,
  period: "current_month"
}

GET /api/providers/{provider}/circuit-breaker
Response: {
  provider: "together",
  breaker_state: "CLOSED",  // or "OPEN", "HALF_OPEN"
  failure_count: 2,
  failure_threshold: 10,
  last_failure: "2025-12-28T09:45:00Z",
  time_in_state_seconds: 3600,
  success_rate_since_last_failure: 99.2
}

GET /api/availability/timeline
Query params: ?period=24h
Response: {
  interval_seconds: 3600,  // 1-hour intervals
  providers: [
    {
      slug: "openrouter",
      timeline: [
        { timestamp: "2025-12-27T10:00:00Z", uptime_percent: 100 },
        { timestamp: "2025-12-27T11:00:00Z", uptime_percent: 99.8 },
        // ... 24 more hours
      ]
    },
    // ... 16 more providers
  ]
}
```

### Token Endpoints

```bash
GET /api/tokens/usage
Query params: ?period=24h
Response: {
  period: "24h",
  total_input_tokens: 234567890,
  total_output_tokens: 123456789,
  total_tokens: 358024679,
  tokens_per_second: 4141,
  cost_per_million_tokens: 2.85
}

GET /api/tokens/by-model
Query params: ?period=7d&limit=10
Response: [
  {
    model: "gpt-4o",
    input_tokens: 456789012,
    output_tokens: 234567890,
    total_tokens: 691356902,
    avg_input_per_request: 5234,
    avg_output_per_request: 2700,
    cost_per_token: 0.00000344
  },
  // ... 9 more models
]

GET /api/tokens/efficiency
Response: {
  estimated_tokens: 340000000,
  actual_tokens: 358024679,
  efficiency_ratio: 94.7,  // 0-100, where 100 = perfect estimate
  waste_percent: 5.3,
  opportunities: [
    "Model A is running 8% over estimate",
    "Model B is 3% under estimate (good!)"
  ]
}
```

---

## 📋 Implementation Questions for Data Team

### 1. **Data Source Architecture**
- [ ] Are metrics coming from a metrics database (InfluxDB, Prometheus)?
- [ ] Are they coming from application logs + analytics backend?
- [ ] Are they pre-aggregated or computed on-the-fly?
- [ ] What's the latency for real-time metrics (5s, 30s, 1m)?

### 2. **Granularity & Storage**
- [ ] How far back is 1-minute granular data available? (24h, 7d?)
- [ ] How far back is 1-hour granular data available? (30d, 90d?)
- [ ] Do you retain raw logs beyond a certain period?
- [ ] Can you do custom aggregations on-demand or are they pre-computed?

### 3. **Financial Data**
- [ ] How is "daily revenue" calculated? (from billing system, usage * price?)
- [ ] Where does cost data come from? (provider invoices, pre-calculated, real-time?)
- [ ] Are costs finalized daily or updated continuously?
- [ ] Do you have monthly budget allocations per model?
- [ ] How are "cost optimization tips" generated? (rule-based, ML-based?)

### 4. **Model & Provider Definitions**
- [ ] Do you have a canonical list of supported models with metadata?
- [ ] Does this include context window, max tokens, cost per token?
- [ ] Do you have assigned colors per provider for consistent visualization?
- [ ] How often do new models/providers get added?

### 5. **Error & Incident Data**
- [ ] Where are errors logged? (Loki, ELK, application database?)
- [ ] How long is error history retained?
- [ ] Can you query errors by provider, model, error type, time range?
- [ ] Do you track error stack traces and request payloads (sanitized)?

### 6. **Circuit Breaker & Health**
- [ ] How is circuit breaker state tracked? (Redis, database?)
- [ ] How is health score calculated? (uptime %, error %, latency %)
- [ ] What are the thresholds for healthy/warning/critical?
- [ ] Is this pre-calculated or computed on request?

### 7. **Data Consistency & Freshness**
- [ ] What's the clock skew tolerance across systems?
- [ ] Are metrics eventually consistent or strongly consistent?
- [ ] What happens if a provider is unreachable (how is unavailability tracked)?
- [ ] How do you handle metric delays in real-time dashboards?

---

## 🎯 Next Steps

Once you provide answers to these questions and/or endpoint URLs, I will:

1. **Validate endpoint structures** - Ensure they can support all dashboard visualizations
2. **Design datasource configs** - Create JSON API datasource configs for Grafana
3. **Build all 6 dashboards** - 48 panels with proper queries, transformations, thresholds
4. **Implement drill-down navigation** - Dashboard links with variable passing
5. **Set color schemes** - Consistent provider colors across all dashboards
6. **Configure variables** - Time range, provider filter, model filter, etc.
7. **Set refresh rates** - 5s-300s based on data volatility
8. **Create documentation** - Dashboard guide explaining each panel and how to use

---

**Ready for**: Endpoint specifications, data samples, or architectural clarification
**Current Branch**: `feature/comprehensive-analytics-dashboards`
**Timeline**: Implementation ready upon data requirements confirmation
