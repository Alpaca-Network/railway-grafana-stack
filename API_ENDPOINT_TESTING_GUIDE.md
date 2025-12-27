# 🧪 GatewayZ API Endpoint Testing Guide

Complete guide for testing GatewayZ API endpoints with interactive tools and real-time monitoring.

## Overview

The testing suite includes:
1. **Grafana Dashboard** - Visualization and monitoring of endpoint health
2. **Standalone HTML Tester** - Interactive testing tool with live responses
3. **Performance Metrics** - Real-time tokens/sec and response time tracking

---

## 🚀 Quick Start

### Option 1: Grafana Dashboard (Recommended)
```
1. Open Grafana: http://localhost:3000 (or your Grafana URL)
2. Go to Dashboards → Search → "GatewayZ Model API Endpoint Tester"
3. Use variables to select time range and models
4. Monitor endpoint health and performance
```

### Option 2: Standalone HTML Tester
```
1. Navigate to: /grafana/chat-tester/index.html
2. Open in browser (or http://localhost:3000/public/plugins/...)
3. Enter API key, model, and message
4. Click "Test Endpoint"
5. View response immediately
```

---

## 📊 Grafana Dashboard Features

### Location
- **File**: `grafana/dashboards/api-endpoint-tester.json`
- **Name**: "GatewayZ Model API Endpoint Tester"
- **UID**: `gatewayz-api-tester`

### Dashboard Panels

#### 1. Model Performance Scatter Plot
Shows relationship between tokens/second and response time.

**Variables**:
- `time_range`: Select 1h, 1d, 1w, 1m, or 1y

**Metrics Shown**:
- Top Models Count
- Average Tokens/Second
- Average Response Time

#### 2. Endpoint Health Status
Pie chart showing percentage of successful vs failed requests.

**What's Measured**:
- 2xx responses = Healthy
- 4xx responses = Client errors
- 5xx responses = Server errors

#### 3. Chat Completions Tester Panel
Interface for testing `/v1/chat/completions` endpoint.

**Configuration**:
- Model variable: `chat_model` (default: gpt-4o-mini)
- Input format: OpenAI-compatible messages array

#### 4. Responses Endpoint Tester
Interface for testing `/v1/responses` endpoint.

**Configuration**:
- Uses `input` parameter instead of `messages`
- Returns `output` field

#### 5. Messages Endpoint Tester
Interface for testing `/v1/messages` endpoint.

**Configuration**:
- Model variable: `messages_model` (default: claude-sonnet-4-5-20250929)
- Requires `max_tokens` parameter

---

## 💬 Standalone HTML Tester

### Location
- **File**: `grafana/chat-tester/index.html`
- **Docs**: `grafana/chat-tester/README.md`

### Features

#### Model Performance Visualization
```
Features:
- Real-time scatter plot (Chart.js)
- X-axis: Tokens per second
- Y-axis: Response time (seconds)
- Time range filters: 1h, 1d, 1w, 1m, 1y
- Live statistics
```

#### Endpoint Testers
Three tabs for different API endpoints:

1. **Chat Completions**
   - Endpoint: `/v1/chat/completions`
   - Format: OpenAI-compatible
   - Field: `messages` array

2. **Responses**
   - Endpoint: `/v1/responses`
   - Format: Custom format
   - Field: `input` string

3. **Messages**
   - Endpoint: `/v1/messages`
   - Format: Anthropic-style
   - Fields: `messages` + `max_tokens`

### How to Use

1. **Enter API Key**
   ```
   Click password field and paste your GatewayZ API key
   ```

2. **Select Model**
   ```
   Choose from predefined models or enter custom model name
   Defaults:
   - Chat: gpt-4o-mini
   - Messages: claude-sonnet-4-5-20250929
   ```

3. **Enter Message**
   ```
   Type your test message in the textarea
   ```

4. **Test Endpoint**
   ```
   Click "Test Endpoint" button
   Wait for response (shows loading spinner)
   ```

5. **View Response**
   ```
   Response displayed as formatted JSON
   Green box = success (2xx)
   Red box = error (4xx/5xx)
   ```

---

## 🔌 API Configuration

### Base URL
```
https://api.gatewayz.ai
```

### Authentication
All requests require Bearer token:
```
Header: Authorization: Bearer YOUR_API_KEY
```

### Endpoint Specifications

#### 1. Chat Completions (`/v1/chat/completions`)
```bash
curl -X POST https://api.gatewayz.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**Request**:
```json
{
  "model": "string",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string"
    }
  ]
}
```

**Response** (Success):
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
        "content": "Response text..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### 2. Responses (`/v1/responses`)
```bash
curl -X POST https://api.gatewayz.ai/v1/responses \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "input": "Hello!"
  }'
```

**Request**:
```json
{
  "model": "string",
  "input": "string"
}
```

**Response** (Success):
```json
{
  "output": "Response text...",
  "tokens_used": 30,
  "model": "gpt-4o-mini"
}
```

#### 3. Messages (`/v1/messages`)
```bash
curl -X POST https://api.gatewayz.ai/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**Request**:
```json
{
  "model": "string",
  "max_tokens": integer,
  "messages": [
    {
      "role": "user|assistant",
      "content": "string"
    }
  ]
}
```

**Response** (Success):
```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Response text..."
    }
  ],
  "model": "claude-sonnet-4-5-20250929",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

---

## 🧪 Testing Scenarios

### Scenario 1: Basic Connectivity Test
```
1. Open Chat Completions tester
2. Enter API key
3. Use default model (gpt-4o-mini)
4. Send simple message: "Hello"
5. Check for 200 response
```

### Scenario 2: Model Comparison
```
1. Test Chat Completions endpoint
2. Test Messages endpoint
3. Compare response times and token usage
4. Check output format differences
```

### Scenario 3: Load Testing
```
1. Send multiple requests in succession
2. Monitor for rate limiting (429 errors)
3. Check response times under load
4. Review token usage metrics
```

### Scenario 4: Error Handling
```
1. Test with invalid API key (401)
2. Test with missing required fields (400)
3. Test with non-existent model (400)
4. Test with very long message (check limits)
```

---

## 📈 Performance Metrics

### Key Metrics Tracked

| Metric | Unit | Meaning |
|--------|------|---------|
| Tokens/Sec | tokens/s | Generation speed |
| Response Time | seconds | Time to first token |
| Model Count | count | Number of models tested |
| Requests | count | Total test requests |

### Health Status Codes

| Code | Status | Color | Action |
|------|--------|-------|--------|
| 200 | ✅ Success | Green | Endpoint healthy |
| 201 | ✅ Created | Green | Resource created |
| 400 | ❌ Bad Request | Red | Fix request format |
| 401 | ❌ Unauthorized | Red | Check API key |
| 429 | ⚠️ Rate Limited | Yellow | Wait and retry |
| 500 | ❌ Server Error | Red | Check server status |

---

## 🐛 Troubleshooting

### "Network error: Failed to fetch"
**Causes**:
- API endpoint is unreachable
- CORS policy blocking request
- Network connectivity issue

**Solutions**:
```bash
# Test connectivity
curl -v https://api.gatewayz.ai/health

# Check endpoint status
ping api.gatewayz.ai

# Verify network connection
curl https://google.com
```

### "Error (401): Unauthorized"
**Causes**:
- API key is invalid
- API key has expired
- API key lacks required permissions

**Solutions**:
1. Verify API key is correct
2. Check key hasn't expired
3. Regenerate key if needed
4. Verify key permissions

### "Error (400): Bad Request"
**Causes**:
- Missing required field (`max_tokens` for Messages)
- Invalid JSON format
- Wrong field names for endpoint

**Solutions**:
1. Check required fields for endpoint
2. Validate JSON syntax
3. Review endpoint documentation
4. Compare request format in guide

### "Error (429): Too Many Requests"
**Causes**:
- Rate limit exceeded
- Too many requests in short period

**Solutions**:
1. Wait 60 seconds
2. Reduce request frequency
3. Implement request batching
4. Contact support for rate limit increase

### No response / Timeout
**Causes**:
- Server overloaded
- Network latency
- Long-running request

**Solutions**:
1. Retry after a few seconds
2. Check server status
3. Try shorter message
4. Monitor network latency

---

## 🔒 Security Best Practices

### API Key Management
```
✅ DO:
- Store API key securely
- Regenerate compromised keys
- Use environment variables
- Rotate keys periodically

❌ DON'T:
- Commit keys to git
- Share keys in messages
- Use same key across environments
- Log API keys
```

### Testing Safety
```
✅ SAFE:
- Test with dummy data
- Use staging endpoint first
- Monitor rate limits
- Use short messages

❌ UNSAFE:
- Send sensitive data
- Test without auth
- No rate limiting
- Send large payloads
```

---

## 📚 Additional Resources

### Documentation Files
- [QUICK_START.md](QUICK_START.md) - Local development setup
- [RAILWAY_DEPLOYMENT_GUIDE.md](RAILWAY_DEPLOYMENT_GUIDE.md) - Production deployment
- [IMMEDIATE_ACTION_REQUIRED.md](IMMEDIATE_ACTION_REQUIRED.md) - Quick fixes
- [DIAGNOSE_CONNECTIVITY.md](DIAGNOSE_CONNECTIVITY.md) - Network troubleshooting

### Dashboard Documentation
- [Grafana Dashboards](grafana/dashboards/) - Available dashboards
- [Chat Tester README](grafana/chat-tester/README.md) - Standalone tool docs

### External Resources
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference/chat/create)
- [Anthropic API Docs](https://docs.anthropic.com/en/api)
- [Grafana Docs](https://grafana.com/docs/)

---

## 📞 Support

### For Dashboard Issues
1. Check Grafana status: http://localhost:3000
2. Verify datasources are configured
3. Check network connectivity
4. Review Grafana logs

### For API Issues
1. Check endpoint status: https://api.gatewayz.ai/health
2. Verify API key is valid
3. Check request format
4. Review API documentation

### For Testing Issues
1. Try with curl first
2. Check browser console for errors
3. Verify CORS configuration
4. Check network tab in DevTools

---

**Last Updated**: December 27, 2025
**Status**: ✅ Production Ready
**Version**: 1.0.0
