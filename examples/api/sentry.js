import * as Sentry from "@sentry/node";
import { nodeProfilingIntegration } from "@sentry/profiling-node";

const SENTRY_DSN = process.env.SENTRY_DSN;
const SENTRY_ENVIRONMENT = process.env.SENTRY_ENVIRONMENT || 'production';
const SENTRY_TRACE_SAMPLE_RATE = parseFloat(process.env.SENTRY_TRACE_SAMPLE_RATE || '1.0');

// Only initialize if DSN is provided
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,
    integrations: [
      new Sentry.Integrations.Http({ tracing: true }),
      new Sentry.Integrations.Express({
        request: true,
        serverName: true,
        transaction: true,
      }),
      nodeProfilingIntegration(),
    ],
    tracesSampleRate: SENTRY_TRACE_SAMPLE_RATE,
    profilesSampleRate: SENTRY_TRACE_SAMPLE_RATE,
    // Attach stack trace to all messages
    attachStacktrace: true,
    // Include local variables in error reports
    includeLocalVariables: true,
  });
}

export default Sentry;
