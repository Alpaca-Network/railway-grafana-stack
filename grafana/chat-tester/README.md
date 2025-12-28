# 🚀 GatewayZ API Endpoint Tester

Interactive testing tool for GatewayZ chat completion endpoints with real-time performance monitoring.

## Features

### 📊 Model Performance Scatter Plot
- Real-time visualization of tokens/sec vs response time
- Top 3 most popular models
- Time range filters: 1h, 1d, 1w, 1m, 1y
- Live statistics display

### 💬 Chat Completions Endpoint (/v1/chat/completions)
- OpenAI-compatible format with messages array
- Real-time response display
- Health status indicators (2xx = healthy, 4xx/5xx = error)

### 📝 Responses Endpoint (/v1/responses)
- Alternative endpoint format using `input` parameter
- Returns `output` instead of `choices`
- Full JSON response display

### 🤖 Messages Endpoint (/v1/messages)
- Anthropic-style API with separate system parameter
- Required `max_tokens` parameter
- Returns `stop_reason` instead of `finish_reason`

## Usage

### Local Development
```bash
# Open directly in browser
open index.html

# Or serve with Python
python3 -m http.server 8080
# Then open http://localhost:8080
```

### Docker Deployment
```bash
# File is served by Grafana container automatically
# Access via: http://grafana:3000/public/plugins/gatewayz-chat-tester/index.html
```

### Railway Deployment
```bash
# File is accessible via Grafana static content
# Access via: https://your-grafana-instance/public/plugins/gatewayz-chat-tester/index.html
```

## API Configuration

**Base URL**: `https://api.gatewayz.ai`

### Authentication
All endpoints require Bearer token in Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

### Endpoint Details

#### Chat Completions
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "user", "content": "Your message here"}
  ]
}
```

#### Responses
```json
{
  "model": "gpt-4o-mini",
  "input": "Your message here"
}
```

#### Messages
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "Your message here"}
  ]
}
```

## Response Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | ✅ Success | Endpoint healthy, response generated |
| 400 | ❌ Bad Request | Invalid format or missing required fields |
| 401 | ❌ Unauthorized | Invalid or missing API key |
| 429 | ⚠️ Rate Limited | Too many requests, wait and retry |
| 500 | ❌ Server Error | Internal server error, check status |

## Testing Steps

1. **Enter API Key**: Your GatewayZ API token
2. **Select Model**: Choose model or enter custom name
3. **Enter Message**: Type your test message
4. **Click Test**: Submit request and view response
5. **Check Status**: Look for success/error indicator
6. **Review Response**: Full JSON response shown below

## Troubleshooting

### "Network error"
- Check API base URL is correct
- Verify internet connection
- Check CORS headers if in browser

### "Authorization failed"
- Verify API key is correct
- Check key hasn't expired
- Ensure key has proper permissions

### "Bad request"
- Check message format
- Ensure required fields are provided
- Verify JSON structure

### "No response"
- Check endpoint is online
- Verify request format matches endpoint spec
- Check for server-side errors in response

## Integration with Grafana

### As Embedded Panel
You can embed this in Grafana using the `grafana-piechart-panel` or custom iframe panel:
```json
{
  "type": "iframe",
  "options": {
    "url": "/public/plugins/gatewayz-chat-tester/index.html"
  }
}
```

### As Standalone Tool
Link to the dashboard:
```
/public/plugins/gatewayz-chat-tester/index.html
```

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile: ✅ Responsive design

## Security Notes

- API keys are NOT stored in browser
- API keys are NOT sent to any third-party
- All requests go directly to your API endpoint
- Keys must be entered each session

## Development

### Structure
```
chat-tester/
├── index.html          # Main testing interface
├── README.md           # This file
└── style.css          # (Optional) External styles
```

### Technologies
- HTML5 / CSS3
- Vanilla JavaScript (no dependencies)
- Chart.js for visualizations
- Fetch API for HTTP requests

## Support

For issues:
1. Check [DIAGNOSE_CONNECTIVITY.md](../../DIAGNOSE_CONNECTIVITY.md)
2. Review [IMMEDIATE_ACTION_REQUIRED.md](../../IMMEDIATE_ACTION_REQUIRED.md)
3. Check endpoint status at https://api.gatewayz.ai/health

---

**Last Updated**: December 27, 2025
**Status**: ✅ Production Ready
**Version**: 1.0.0
