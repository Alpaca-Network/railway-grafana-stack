import { createLogger, transports, format } from 'winston';
import LokiTransport from 'winston-loki';

const LOKI_URL = process.env.LOKI_URL || 'http://loki.railway.internal:3100';


const options = {
  format: format.combine(
    format.timestamp(),
    format.json()
  ),
  transports: [
    new LokiTransport({
      host: LOKI_URL,
      labels: {
        app: 'gatewayz-monitor',
        service: 'api-monitoring',
        target: 'gatewayz'
      },
      json: true
    }),
    new transports.Console({
      format: format.combine(
        format.colorize(),
        format.simple()
      )
    })
  ],
}

export const logger = createLogger(options);