import express from 'express';
import promMiddleware from 'express-prometheus-middleware';
import { trace, context } from "@opentelemetry/api";

import { logger } from './logger.js';
import './tracer.js';


const app = express();
const PORT = process.env.PORT || 9091;
const TARGET_API = process.env.TARGET_API || 'https://api.gatewayz.ai';

app.use(promMiddleware({
  metricsPath: '/metrics',
  collectDefaultMetrics: true,
  requestDurationBuckets: [0.1, 0.5, 1, 1.5],
}));

// this creates custom spans to be sent to tempo
const tracer = trace.getTracer(process.env.TEMPO_SERVICE_NAME || 'gatewayz-monitor')

// Health check endpoint for the monitoring service
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', monitoring: TARGET_API });
});

// Function to make monitored requests to the target API
async function makeMonitoredRequest(endpoint, method = 'GET', body = null) {
  const span = tracer.startSpan(`${method} ${endpoint}`);
  const startTime = Date.now();

  try {
    const url = `${TARGET_API}${endpoint}`;
    logger.info(`Making ${method} request to ${url}`);

    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Gatewayz-Monitor/1.0'
      },
      signal: AbortSignal.timeout(10000) // 10 second timeout
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const duration = Date.now() - startTime;
    const responseText = await response.text();

    span.setAttribute('http.status_code', response.status);
    span.setAttribute('http.method', method);
    span.setAttribute('http.url', url);
    span.setAttribute('http.response_time_ms', duration);

    logger.info(`Response from ${url}`, {
      status: response.status,
      duration_ms: duration,
      endpoint: endpoint,
      method: method,
      response_size: responseText.length
    });

    return {
      status: response.status,
      duration,
      body: responseText,
      ok: response.ok
    };
  } catch (error) {
    const duration = Date.now() - startTime;
    span.setAttribute('error', true);
    span.setAttribute('error.message', error.message);

    logger.error(`Error calling ${TARGET_API}${endpoint}`, {
      error: error.message,
      duration_ms: duration,
      endpoint: endpoint,
      method: method
    });

    return {
      status: 0,
      duration,
      error: error.message,
      ok: false
    };
  } finally {
    span.end();
  }
}

// Periodic monitoring - probe the API every 30 seconds
async function startPeriodicMonitoring() {
  const INTERVAL_MS = parseInt(process.env.MONITOR_INTERVAL_MS || '30000');
  const endpoints = (process.env.MONITOR_ENDPOINTS || '/,/health,/status').split(',');

  logger.info(`Starting periodic monitoring of ${TARGET_API}`, {
    interval_ms: INTERVAL_MS,
    endpoints: endpoints
  });

  setInterval(async () => {
    const span = tracer.startSpan('periodic-health-check');

    for (const endpoint of endpoints) {
      await makeMonitoredRequest(endpoint.trim(), 'GET');
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    span.end();
  }, INTERVAL_MS);
}

app.listen(PORT, () => {
  console.log(`Gatewayz monitoring service is running on http://localhost:${PORT}`);
  console.log(`Monitoring target: ${TARGET_API}`);
  startPeriodicMonitoring();
});