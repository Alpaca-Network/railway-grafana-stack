# 🔍 GatewayZ Backend Monitoring Tool

Interactive HTML-based monitoring dashboard for real-time provider health, performance analytics, and anomaly detection.

## Overview

This is a standalone monitoring tool that provides comprehensive visibility into GatewayZ backend providers with:

- **Real-time Health Scores**: 0-100 scale for each provider
- **Interactive Charts**: Request volume, latency, error rates, costs
- **Anomaly Detection**: Automatic identification of performance issues
- **Cost Analysis**: Provider cost breakdown and trends
- **Auto-Refresh**: Optional 30-second auto-refresh for live monitoring

## Features

### Health Dashboard
One health card per provider showing:
- Health score (color-coded: green/yellow/red)
- Status badge (Healthy/Warning/Critical)
- Request count
- Error count
- Average latency
- Detected anomalies with severity

### Performance Analytics
Time-series charts for the top 5 providers:
- **Request Volume**: Requests per time interval
- **Latency Trends**: P95 latency percentile
- **Error Rates**: Error count over time
- **Cost Trends**: Cost per time interval

### Cost Analysis
- Pie chart showing provider cost breakdown
- Summary statistics:
  - Total cost (24 hours)
  - Highest cost provider
  - Most efficient provider
  - Total requests

### Anomaly Detection
Real-time detection with automatic alert generation:
- **Cost Spike Anomalies**: >200% of 24h average
- **Latency Spike Anomalies**: >200% of 24h average
- **Error Rate Anomalies**: >10% (WARNING), >25% (CRITICAL)

### Severity Levels
- 🟢 **Healthy** (80-100): Service operating normally
- 🟡 **Warning** (50-79): Service degradation detected
- 🔴 **Critical** (0-49): Service experiencing serious issues

## Supported Providers

All 17 GatewayZ providers are supported:
- OpenRouter
- Portkey
- Featherless
- Chutes
- DeepInfra
- Fireworks
- Together
- Hugging Face
- xAI
- Aimo
- NEAR
- FAL
- Anannas
- Google Vertex
- ModelZ
- AIHubMix
- Vercel AI Gateway

## Usage

### Standalone Deployment

1. **Copy to web server**:
```bash
cp grafana/monitoring-tool/index.html /var/www/html/monitoring/
```

2. **Access via browser**:
```
http://your-domain.com/monitoring/index.html
```

3. **Enter API Key**:
   - Paste your GatewayZ API key
   - Default base URL: `https://api.gatewayz.ai`
   - Select time range (1h, 1d, 1w, 1m, 1y)

4. **Load Data**:
   - Click "Load Data" button
   - Charts and health cards will populate
   - Enable "Auto Refresh" for continuous updates (30s interval)

### Grafana Integration

The tool is embedded in the Grafana monitoring dashboard:

1. Open Grafana: `http://localhost:3000`
2. Navigate to Dashboard → GatewayZ Backend Monitoring
3. The monitoring tool appears as the main interactive component
4. All other panels provide supplementary analytics

### Standalone vs Embedded

**Standalone Benefits**:
- No Grafana dependency
- Lightweight and fast
- Can be shared as simple link
- Works in iframes
- Mobile-friendly

**Grafana Integration Benefits**:
- Centralized monitoring
- Additional analytics panels
- Alert integration
- Historical trending
- User access control

## API Endpoints Used

### Tier 1 - Core Endpoints
- `GET /api/monitoring/health` - Provider health status
- `GET /api/monitoring/stats/realtime` - Real-time metrics
- `GET /api/monitoring/latency/{provider}/{model}` - Latency data

### Tier 2 - Advanced Endpoints
- `GET /api/monitoring/errors/{provider}` - Error details
- `GET /api/monitoring/anomalies` - Anomaly data
- `GET /api/monitoring/cost-analysis` - Cost breakdown

See `MONITORING_GUIDE.md` for complete endpoint specifications.

## Configuration

### Input Fields

**API Key** (Required)
- Your GatewayZ API key
- Used for Bearer token authentication
- Must have monitoring scope

**Base URL** (Optional)
- Default: `https://api.gatewayz.ai`
- Can be changed for staging/custom endpoints
- Include protocol (http/https)

**Time Range** (Optional)
- Options: 1h, 1d, 1w, 1m, 1y
- Default: 1d (Last 24 hours)
- Affects all time-series charts

### Auto-Refresh

Toggle with "Auto Refresh" button:
- **Off**: Manual loading only
- **On**: Loads data every 30 seconds
- Status shown in button text
- Continues until explicitly disabled

## Understanding the Metrics

### Health Score
Composite metric (0-100) based on:
- Uptime percentage (40%)
- Error rate inverse (30%)
- Latency inverse (20%)
- Availability (10%)

Interpretation:
- **80-100**: Excellent service
- **50-79**: Service issues present
- **0-49**: Severe service degradation

### Request Volume
Current requests per time interval. Higher is typically better (within capacity).

### Latency (P95)
95th percentile response time - meaning 95% of requests complete within this time.

**Good**: < 500ms
**Acceptable**: 500ms - 2s
**Poor**: > 2s

### Error Rate
Percentage of failed requests (4xx/5xx responses).

**Good**: < 1%
**Acceptable**: 1-5%
**Poor**: > 5%

### Cost Per Request
Amount charged per API call.

**Good**: < $0.0001
**Expensive**: > $0.001

## Anomaly Detection Details

### How Anomalies are Detected

The system compares current metrics against 24-hour baselines:

```
If current_value > baseline_24h * 2.0
  → Anomaly detected
```

### Severity Classification

**WARNING** (⚠️ Yellow):
- Cost spike 200% above baseline
- Latency spike 200% above baseline
- Error rate 10-25%

**CRITICAL** (🔴 Red):
- Error rate > 25%
- Health score < 50

### Anomaly Table

Shows all detected anomalies with:
- Provider name
- Metric affected
- Current value
- 24h baseline
- Deviation percentage
- Severity level
- Detection timestamp

## Security Considerations

### API Key Handling
- ✅ Transmitted only to `api.gatewayz.ai`
- ✅ Never stored in browser storage
- ✅ Never logged in console
- ✅ HTTPS required for production
- ✅ No third-party tracking

### Data Privacy
- ✅ No metrics stored locally
- ✅ No analytics tracking
- ✅ No data sent to third parties
- ✅ Read-only API access

### Best Practices
- Rotate API keys regularly
- Use different keys per environment
- Don't share monitoring links with sensitive data
- Review logs for unauthorized access
- Monitor API usage patterns

## Troubleshooting

### "Please enter your API key"
**Solution**: API key field is required. Paste your valid GatewayZ API key.

### "Failed to fetch health data: API returned 401"
**Solutions**:
1. Verify API key is correct (copy/paste carefully)
2. Check API key hasn't expired
3. Regenerate key if necessary
4. Verify key has monitoring scope

### "Failed to fetch health data: Failed to fetch"
**Solutions**:
1. Check network connectivity
2. Verify base URL is correct
3. Ensure HTTPS is enabled
4. Check CORS settings
5. Review browser console for details

### No charts appear
**Solutions**:
1. Click "Load Data" button
2. Check for error messages
3. Verify API response in browser DevTools
4. Check network tab for failed requests

### Data not updating with auto-refresh
**Solutions**:
1. Check if auto-refresh is actually enabled
2. Verify API key still valid
3. Check browser console for JavaScript errors
4. Restart auto-refresh by toggling off/on
5. Check browser permissions and third-party cookies

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- IE 11: ❌ Not supported (ES6 required)

Recommended: Latest version of Chrome, Firefox, or Safari

## Performance

- Load Time: < 2 seconds
- Initial Data Load: < 1 second
- Chart Render: < 500ms
- Auto-Refresh Interval: 30 seconds
- Recommended Screen Size: 1200x800 or larger

## Mobile Responsiveness

The tool is responsive and works on mobile devices:
- Health cards stack vertically on small screens
- Charts resize to fit viewport
- Touch-friendly controls
- Optimized for 320px+ width

## Browser Storage

The tool does NOT use:
- localStorage
- sessionStorage
- Cookies
- IndexedDB

All data is loaded fresh on each request.

## CORS and Deployment

### Local Development
Works locally with:
```bash
python -m http.server 8000
```

### Grafana Embedding
Works perfectly embedded in Grafana iframes without special configuration.

### Custom Domain
If hosting on different domain than API, ensure:
- API supports CORS
- API allows your domain in CORS headers
- HTTPS is enabled (for production)

## Integration Examples

### Embed in HTML Page
```html
<iframe src="https://your-domain.com/monitoring/"
        width="100%" height="1200" frameborder="0"></iframe>
```

### Embed in Grafana Dashboard
Already configured in `monitoring-dashboard-v1.json`

### Link in Documentation
```markdown
[Live Monitoring](https://your-domain.com/monitoring/)
```

### Share with Team
Simply share the URL with your API key (security consideration):
```
https://your-domain.com/monitoring/?key=YOUR_API_KEY
```

⚠️ Note: URL-based API keys are visible in browser history/referer headers. Use with caution or share links without keys and have users enter keys manually.

## Advanced Configuration

### Custom Styling

Edit the `<style>` section in `index.html` to customize:
- Color scheme (gradient colors)
- Font family
- Panel sizes
- Chart colors

### Data Refresh Interval

Modify the auto-refresh interval in JavaScript:
```javascript
autoRefreshInterval = setInterval(loadMonitoringData, 30000); // 30000ms = 30s
```

### Chart Types

Charts are rendered with Chart.js. Modify chart types in the rendering functions to change from line to bar, area, etc.

### Provider List

The supported providers list can be customized by editing the `PROVIDERS` array:
```javascript
const PROVIDERS = [
    'openrouter', 'portkey', 'featherless', // ...
];
```

## Support & Documentation

### Full Documentation
See `MONITORING_GUIDE.md` for:
- Complete API endpoint specifications
- All supported providers and models
- Anomaly detection thresholds
- Testing procedures
- Integration patterns

### Quick References
- **API_ENDPOINT_TESTING_GUIDE.md** - Chat endpoint testing
- **QUICK_START.md** - Setup instructions
- **RAILWAY_DEPLOYMENT_GUIDE.md** - Production deployment

### Getting Help
1. Check the troubleshooting section above
2. Review `MONITORING_GUIDE.md` for detailed specs
3. Check browser console (F12 → Console tab)
4. Review Network tab for API failures
5. Contact support with error details

## Version History

### v1.0 (December 28, 2025)
- Initial release
- Real-time health monitoring
- Time-series analytics
- Anomaly detection
- Cost analysis
- Auto-refresh capability

## License

Part of GatewayZ monitoring stack. See main LICENSE for details.

---

**Last Updated**: December 28, 2025
**Status**: ✅ Production Ready
**Maintained By**: GatewayZ Team
