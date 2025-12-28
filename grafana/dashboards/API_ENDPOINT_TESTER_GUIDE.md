# 📖 GatewayZ API Endpoint Tester - Complete Guide

## Overview

The API Endpoint Tester dashboard provides comprehensive tools for testing and monitoring GatewayZ API endpoints with real-time performance visualization.

## Dashboard Features

### 1. 💬 Interactive Chat Completion Tester
Embedded HTML interface for testing three API endpoint types:

#### Chat Completions (`/v1/chat/completions`)
- **Format**: OpenAI-compatible with messages array
- **Request**:
  ```json
  {
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Your message"}
    ]
  }
  ```
- **Response**: Full JSON with choices, tokens, and finish_reason
- **Health Check**: 2xx = healthy, 4xx/5xx = error

#### Responses (`/v1/responses`)
- **Format**: Uses `input` parameter instead of messages
- **Request**:
  ```json
  {
    "model": "gpt-4o-mini",
    "input": "Your message"
  }
  ```
- **Response**: Returns `output` field instead of `choices`

#### Messages (`/v1/messages`)
- **Format**: Anthropic-style API with separate system parameter
- **Request**:
  ```json
  {
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Your message"}
    ]
  }
  ```
- **Response**: Returns `stop_reason` instead of `finish_reason`

### 2. 📊 Model Performance Analytics
Real-time visualization of API endpoint performance metrics:
- **Time Series**: Response times, token usage, and request rates over time
- **Visual Stats**: Key performance indicators (KPIs)
- **Models Tracked**: gpt-4o-mini, claude-sonnet-4-5, llama-2-70b

### 3. 🎯 Chat Completions Performance
Monitor real-time performance of the Chat Completions endpoint:
- Response latency trends
- Token throughput metrics
- Success/error rates
- Model comparison

### 4. 📤 Responses Endpoint Performance
Track alternative endpoint format performance:
- Alternative input/output format metrics
- Processing time analysis
- Throughput monitoring
- Error tracking

### 5. 📈 Model Performance Scatter Plot
**⚠️ Note**: Currently using mock data for demonstration purposes.

Visualizes relationship between:
- **X-axis**: Tokens per second (throughput)
- **Y-axis**: Response time (latency)
- **Top 3 Models**: Most frequently used models

**To enable real data**: Backend metrics endpoint required.

## Testing Workflows

### Scenario 1: Basic Health Check
```
1. Open the Interactive Chat Completion Tester
2. Enter your API key
3. Use default model (gpt-4o-mini)
4. Send test message: "Hello"
5. Verify 200 response code
6. Check green success indicator
```

### Scenario 2: Compare Endpoints
```
1. Test Chat Completions endpoint
2. Note response time and tokens
3. Switch to Responses endpoint tab
4. Send similar input
5. Compare performance metrics
6. Check differences in response format
```

### Scenario 3: Monitor Performance Trends
```
1. Make multiple API requests
2. Observe time series graphs updating
3. Watch performance metrics change
4. Identify patterns in response times
5. Track token usage over time
```

### Scenario 4: Error Handling
```
1. Test with invalid API key → Expect 401
2. Test with malformed message → Expect 400
3. Test with non-existent model → Expect 400
4. Make rapid requests → Expect 429 (rate limit)
5. Verify error responses display correctly
```

## API Configuration

### Base URL
```
https://api.gatewayz.ai
```

### Authentication
All endpoints require Bearer token:
```bash
Authorization: Bearer YOUR_API_KEY
```

### Available Models

#### OpenAI Compatible
- `gpt-4o-mini` (recommended for testing)
- `gpt-4-turbo`
- `gpt-3.5-turbo`

#### Anthropic Compatible
- `claude-sonnet-4-5-20250929` (default)
- `claude-opus-4`

## Response Status Codes

| Code | Status | Action |
|------|--------|--------|
| 200 | ✅ Success | Endpoint working, response received |
| 201 | ✅ Created | Resource created successfully |
| 400 | ❌ Bad Request | Fix message format or required fields |
| 401 | ❌ Unauthorized | Verify API key is correct |
| 429 | ⚠️ Rate Limited | Wait 60 seconds before retrying |
| 500 | ❌ Server Error | Check backend status, retry later |
| 503 | ❌ Unavailable | Service temporarily down |

## Troubleshooting

### "Network error: Failed to fetch"
**Causes**: Network issues, CORS blocking, endpoint unreachable

**Solutions**:
```bash
# Test connectivity
curl -v https://api.gatewayz.ai/health

# Check endpoint status
curl https://api.gatewayz.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"test"}]}'
```

### "Error (401): Unauthorized"
**Causes**: Invalid/expired API key, insufficient permissions

**Solutions**:
1. Verify API key is correct (copy/paste carefully)
2. Check API key hasn't expired
3. Regenerate key if necessary
4. Verify key has proper permissions

### "Error (400): Bad Request"
**Causes**: Missing required fields, invalid JSON, wrong format

**Solutions**:
- Verify all required fields are present
- Check JSON syntax
- Ensure field names match endpoint spec
- Review error message in response

### "Error (429): Too Many Requests"
**Causes**: Rate limit exceeded

**Solutions**:
1. Wait 60 seconds before retrying
2. Reduce request frequency
3. Batch requests efficiently
4. Contact support for rate limit increase

### No response / Timeout
**Causes**: Server overloaded, network latency, long-running requests

**Solutions**:
1. Retry after 10 seconds
2. Check server status
3. Try with shorter message
4. Monitor network latency

## Performance Metrics Explained

### Response Time
Time from request submission to receiving first token.
- **Good**: < 500ms
- **Acceptable**: 500ms - 2s
- **Slow**: > 2s

### Tokens/Second
Throughput of token generation.
- **Good**: > 300 tokens/sec
- **Acceptable**: 150-300 tokens/sec
- **Slow**: < 150 tokens/sec

### Success Rate
Percentage of requests returning 2xx status.
- **Good**: > 99%
- **Acceptable**: 95-99%
- **Poor**: < 95%

### Error Rate
Percentage of requests with errors (4xx/5xx).
- **Good**: < 1%
- **Acceptable**: 1-5%
- **Poor**: > 5%

## Security Best Practices

### API Key Management
✅ **DO**:
- Store keys in environment variables
- Rotate keys regularly
- Use different keys for different environments
- Regenerate if compromised
- Never commit keys to git

❌ **DON'T**:
- Share API keys in messages
- Commit keys to repository
- Use same key across all environments
- Log API keys
- Store in plaintext files

### Testing Safety
✅ **SAFE**:
- Test with dummy/test data
- Use staging endpoint first
- Monitor rate limits
- Use short messages
- Test error cases

❌ **UNSAFE**:
- Send sensitive data
- Test without authentication
- Ignore rate limits
- No request throttling
- Large batch requests

## Advanced Features

### Monitoring Integrations
The dashboard can integrate with:
- **Prometheus**: For historical metrics collection
- **Loki**: For log aggregation
- **Tempo**: For distributed tracing
- **Grafana Alerting**: For threshold alerts

### Custom Dashboards
Create custom panels by:
1. Using Prometheus queries for metrics
2. Adding alert rules for thresholds
3. Creating custom drill-down dashboards
4. Building alert notifications

### Data Export
Export test results by:
1. Exporting dashboard as JSON
2. Exporting panel data as CSV
3. Creating automated reports
4. Integrating with external systems

## API Examples

### cURL - Chat Completions
```bash
curl -X POST https://api.gatewayz.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "You are helpful"},
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

### cURL - Responses
```bash
curl -X POST https://api.gatewayz.ai/v1/responses \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "input": "What is 2+2?"
  }'
```

### cURL - Messages
```bash
curl -X POST https://api.gatewayz.ai/v1/messages \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ]
  }'
```

### Python Example
```python
import requests

api_key = "YOUR_API_KEY"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Chat Completions
response = requests.post(
    "https://api.gatewayz.ai/v1/chat/completions",
    headers=headers,
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
print(response.json())
```

## Support & Resources

### Documentation
- [QUICK_START.md](../QUICK_START.md) - Local development setup
- [RAILWAY_DEPLOYMENT_GUIDE.md](../RAILWAY_DEPLOYMENT_GUIDE.md) - Production deployment
- [API_ENDPOINT_TESTING_GUIDE.md](../API_ENDPOINT_TESTING_GUIDE.md) - Comprehensive testing guide
- [DIAGNOSE_CONNECTIVITY.md](../DIAGNOSE_CONNECTIVITY.md) - Network troubleshooting

### External Resources
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference/chat/create)
- [Anthropic API Docs](https://docs.anthropic.com/en/api)
- [Grafana Docs](https://grafana.com/docs/)

### Getting Help
1. Check troubleshooting section above
2. Review error message details
3. Check backend status
4. Review logs in Grafana/Loki
5. Contact support with error details

---

**Dashboard Version**: 2.0
**Last Updated**: December 27, 2025
**Status**: ✅ Production Ready
