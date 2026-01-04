# ✅ DATA VERIFICATION GUIDE - Real vs Mock Data

**Document Purpose**: Verify which data sources are real vs mock in the GatewayZ API Endpoint Tester dashboard.

---

## 📊 REAL DATA (Production/Live)

### ✅ Chat Completions Endpoint (`/v1/chat/completions`)
**Source**: Direct API calls to `https://api.gatewayz.ai`

```javascript
// Line 704-753: REAL API CALL
async function testChatCompletions() {
    const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: message }]
        })
    });

    const data = await response.json();
    // REAL response from backend
    document.getElementById('chatCompletionsResponse').textContent = JSON.stringify(data, null, 2);
}
```

**What's Real**:
- ✅ API Request headers (Authorization, Content-Type)
- ✅ Message content (user input)
- ✅ Model selection
- ✅ HTTP Response status (200, 400, 401, 429, 500, etc.)
- ✅ Response body (choices, tokens, finish_reason)
- ✅ Response time (measured from request)
- ✅ Error messages from API

**How to Verify**:
1. Enter valid API key in the tester
2. Click "Test Endpoint"
3. Look at response - it's JSON from your backend
4. Check status: 200 = endpoint working

---

### ✅ Responses Endpoint (`/v1/responses`)
**Source**: Direct API calls to `https://api.gatewayz.ai`

```javascript
// Line 755-804: REAL API CALL
async function testResponses() {
    const response = await fetch(`${API_BASE_URL}/v1/responses`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: model,
            input: input  // Alternative format
        })
    });

    const data = await response.json();
    // REAL response from backend
}
```

**What's Real**:
- ✅ API Request with alternative format
- ✅ Input parameter (instead of messages)
- ✅ HTTP Response status codes
- ✅ Response body with `output` field
- ✅ Actual response from backend

---

### ✅ Messages Endpoint (`/v1/messages`)
**Source**: Direct API calls to `https://api.gatewayz.ai`

```javascript
// Line 806-855: REAL API CALL
async function testMessages() {
    const response = await fetch(`${API_BASE_URL}/v1/messages`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: model,
            max_tokens: parseInt(maxTokens),
            messages: [{ role: 'user', content: content }]
        })
    });

    const data = await response.json();
    // REAL response from backend
}
```

**What's Real**:
- ✅ Anthropic-style API format
- ✅ Max tokens requirement
- ✅ Messages array format
- ✅ HTTP Response status codes
- ✅ Response with stop_reason
- ✅ Token usage information

---

## 📈 MOCK DATA (Demonstration Only)

### ❌ Scatter Plot - "Total Tokens Over Time"
**Source**: Simulated data generator (Line 521-593)

```javascript
// MOCK DATA - Not from actual API
function generateMockScatterData(timeRange) {
    // Creates realistic but SIMULATED token trends
    // Each model gets different base rate:
    const baseTokensPerReq = 50 + (modelIdx * 30);
    // gpt-4o-mini: ~50-70 tokens/request
    // claude-sonnet-4-5: ~80-100 tokens/request
    // llama-2-70b: ~110-130 tokens/request
}
```

**Where It's Used**:
- Only in the scatter plot visualization
- NOT used in endpoint testers
- NOT used for any actual API monitoring

**Why Mock Data**:
- No historical database of tokens exists yet
- Demonstrates what real data would look like
- Shows time-series trends (upward trend with volatility)
- Allows testing dashboard with realistic patterns

**Data Characteristics**:
- Time ranges: 1h, 1d, 1w, 1m, 1y
- Dynamic time intervals (5min, 1h, 6h, 1d, 1w)
- 30% volatility (realistic variance)
- Upward trend (reflects typical growth)
- Realistic request rates: 50-250 per interval

---

## 🔐 How to Verify Real Data Yourself

### Test 1: Check Chat Completions
```bash
# Copy this command
curl -X POST https://api.gatewayz.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

**Expected Response** (Real Data):
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "2+2 equals 4."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 5,
    "total_tokens": 15
  }
}
```

### Test 2: Compare Dashboard with cURL
1. Run cURL command above
2. Note the response (real backend data)
3. Open dashboard chat tester
4. Enter same API key and model
5. Send same message
6. Response should match cURL

---

## 📊 Dashboard Data Sources Summary

| Component | Real? | Source | How to Verify |
|-----------|-------|--------|---------------|
| Chat Completions Tester | ✅ YES | Your backend API | Test endpoint directly |
| Responses Endpoint Tester | ✅ YES | Your backend API | Test endpoint directly |
| Messages Endpoint Tester | ✅ YES | Your backend API | Test endpoint directly |
| API Response Status | ✅ YES | HTTP status code | Check response headers |
| Error Messages | ✅ YES | Backend error response | Trigger error with bad input |
| Scatter Plot | ❌ NO | Simulated generator | See chart label "using mock data" |
| Time Series Trends | ❌ NO | Simulated data | Plotted data is generated |
| Token Counts in Chart | ❌ NO | Random with realistic pattern | Chart shows demo data |

---

## 🛡️ What You Can Trust

### 100% Real
- ✅ All endpoint test responses
- ✅ API status codes
- ✅ Error messages
- ✅ Response latency
- ✅ Authentication validation
- ✅ Message format validation

### For Demo/Visualization Only
- ℹ️ Scatter plot trends
- ℹ️ Time-series token counts
- ℹ️ Historical comparisons

---

## 📝 Documentation

For more information:
- [API_ENDPOINT_TESTER_GUIDE.md](./grafana/dashboards/API_ENDPOINT_TESTER_GUIDE.md) - Complete testing guide
- [QUICK_START.md](./QUICK_START.md) - Setup instructions
- [API_ENDPOINT_TESTING_GUIDE.md](./API_ENDPOINT_TESTING_GUIDE.md) - Full API specs

---

## ✅ For Your Boss

**Summary**:
- **Real Data**: All endpoint testing against live backend API
- **Mock Data**: Only scatter plot visualization (clearly labeled)
- **Verification**: Can be tested locally with cURL or any HTTP client
- **Security**: API keys never logged or transmitted to third parties
- **Accuracy**: Real responses from your actual backend

**Recommendation**:
When presenting to stakeholders, emphasize that endpoint tests use REAL data from your API, while the scatter plot is a demonstration of what historical metrics would look like once you implement persistent metrics storage.

---

**Generated**: December 27, 2025
**Status**: ✅ Production Ready
**Verification**: Manual testing confirmed all real data endpoints working
