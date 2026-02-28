#!/bin/sh
set -e

# ============================================================================
# Alertmanager Entrypoint
# Substitutes environment variable placeholders into alertmanager.yml
# before handing off to the real Alertmanager binary.
#
# Required env vars:
#   SMTP_FROM         From address (e.g. alerts@gatewayz.ai)
#   SMTP_USER         SMTP auth username
#   SMTP_PASSWORD     SMTP auth password / app-password
#
# Optional env vars (all have sensible defaults):
#   SMTP_HOST         SMTP smarthost (default: smtp.gmail.com:465)
#   SMTP_STARTTLS     NoStartTLS | MandatoryStartTLS (default: NoStartTLS for port 465)
#   ALERT_EMAIL_OPS   Comma-separated ops emails
#   ALERT_EMAIL_CRIT  Comma-separated critical/pager emails
#   EXTERNAL_URL      Public URL of this service (for Prometheus → AM links)
# ============================================================================

# ── SMTP ────────────────────────────────────────────────────────────────────
SMTP_HOST="${SMTP_HOST:-smtp.gmail.com:465}"
SMTP_FROM="${SMTP_FROM:-${GF_SMTP_FROM_ADDRESS:-alerts@localhost}}"
SMTP_USER="${SMTP_USER:-${GF_SMTP_USER:-}}"
SMTP_PASSWORD="${SMTP_PASSWORD:-${GF_SMTP_PASSWORD:-no-password}}"

# ── Email addresses ─────────────────────────────────────────────────────────
DEFAULT_EMAILS="manjeshprasad21@gmail.com,vaughn@alpacanetwork.ai"
ALERT_EMAIL_OPS="${ALERT_EMAIL_OPS:-${ALERT_EMAIL:-${DEFAULT_EMAILS}}}"
ALERT_EMAIL_CRIT="${ALERT_EMAIL_CRIT:-${ALERT_EMAIL_OPS}}"

# ── Validate required values ────────────────────────────────────────────────
if [ -z "$SMTP_FROM" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
    echo "============================================="
    echo "⚠️  Alertmanager: SMTP not fully configured"
    echo "   Set SMTP_FROM, SMTP_USER, SMTP_PASSWORD"
    echo "   (or GF_SMTP_FROM_ADDRESS / GF_SMTP_USER / GF_SMTP_PASSWORD)"
    echo "   Alerts will not be delivered via email."
    echo "============================================="
fi

# ── External URL ────────────────────────────────────────────────────────────
if [ -z "$EXTERNAL_URL" ] && [ -n "$RAILWAY_STATIC_URL" ]; then
    EXTERNAL_URL="https://${RAILWAY_STATIC_URL}"
fi
EXTERNAL_URL="${EXTERNAL_URL:-http://localhost:9093}"

# ── Substitute placeholders ─────────────────────────────────────────────────
cp /etc/alertmanager/alertmanager.yml /tmp/alertmanager.yml.tmp

sed \
    -e "s|SMTP_HOST_PLACEHOLDER|${SMTP_HOST}|g" \
    -e "s|SMTP_FROM_PLACEHOLDER|${SMTP_FROM}|g" \
    -e "s|SMTP_USER_PLACEHOLDER|${SMTP_USER}|g" \
    -e "s|SMTP_PASSWORD_PLACEHOLDER|${SMTP_PASSWORD}|g" \
    -e "s|ALERT_EMAIL_OPS_PLACEHOLDER|${ALERT_EMAIL_OPS}|g" \
    -e "s|ALERT_EMAIL_CRIT_PLACEHOLDER|${ALERT_EMAIL_CRIT}|g" \
    /tmp/alertmanager.yml.tmp > /etc/alertmanager/alertmanager.yml

# ── Startup banner ──────────────────────────────────────────────────────────
W=60
SEP=$(printf '%*s' "$W" '' | tr ' ' '=')
echo "$SEP"
echo " ALERTMANAGER STARTUP" | awk '{printf "%-60s\n", $0}'
echo "$SEP"
echo "  SMTP host   : ${SMTP_HOST}"
echo "  SMTP from   : ${SMTP_FROM:-NOT SET}"
echo "  SMTP user   : ${SMTP_USER:-NOT SET}"
echo "  Ops email   : ${ALERT_EMAIL_OPS}"
echo "  Crit email  : ${ALERT_EMAIL_CRIT}"
echo "  Listen port : ${LISTEN_PORT}"
echo "  External URL: ${EXTERNAL_URL}"
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "  Environment : Railway (${RAILWAY_ENVIRONMENT})"
else
    echo "  Environment : local (Docker Compose)"
fi
echo "$SEP"

# Validate config
if amtool check-config /etc/alertmanager/alertmanager.yml 2>/dev/null; then
    echo "  ✅ Config valid"
else
    echo "  ⚠️  amtool not available — skipping config check"
fi
echo ""

# ── Listen address ──────────────────────────────────────────────────────────
# Railway injects PORT dynamically; fall back to 9093 for local Docker Compose.
LISTEN_PORT="${PORT:-9093}"

# ── Hand off to Alertmanager ────────────────────────────────────────────────
exec /bin/alertmanager \
    "--web.listen-address=:${LISTEN_PORT}" \
    "--web.external-url=${EXTERNAL_URL}" \
    "$@"
