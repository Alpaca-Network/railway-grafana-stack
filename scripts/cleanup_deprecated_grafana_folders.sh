#!/usr/bin/env bash
# cleanup_deprecated_grafana_folders.sh
#
# Deletes the deprecated Grafana folders (Developer, Prometheus, Sentry) and all
# content blocking their deletion — alert rule groups and library panels.
#
# Background: these folders were removed from dashboards.yml when the dashboard
# structure was restructured, but Grafana does not auto-delete folders when a
# provisioner block is removed. The folders persist in the Grafana database with
# orphaned alert rules and/or library panels, blocking UI-level folder deletion.
#
# Usage:
#   bash scripts/cleanup_deprecated_grafana_folders.sh
#
# Override defaults:
#   GRAFANA_URL=https://logs.gatewayz.ai \
#   GRAFANA_USER=admin \
#   GRAFANA_PASSWORD=<your-admin-password> \
#   bash scripts/cleanup_deprecated_grafana_folders.sh
#
# Requirements: curl, jq

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
AUTH="${GRAFANA_USER}:${GRAFANA_PASSWORD}"

DEPRECATED_FOLDERS=("Developer" "Prometheus" "Sentry")

# Check dependencies
if ! command -v jq &>/dev/null; then
  echo "Error: jq is required but not installed. Install with: brew install jq"
  exit 1
fi

echo "======================================================"
echo " GatewayZ — Deprecated Grafana Folder Cleanup"
echo " Target: ${GRAFANA_URL}"
echo "======================================================"
echo ""

for FOLDER_NAME in "${DEPRECATED_FOLDERS[@]}"; do
  echo "=== Processing folder: '$FOLDER_NAME' ==="

  # ------------------------------------------------------------------
  # 1. Resolve folder name → UID
  # ------------------------------------------------------------------
  FOLDER_UID=$(curl -sf -u "$AUTH" \
    "${GRAFANA_URL}/api/folders?limit=200" \
    | jq -r ".[] | select(.title == \"${FOLDER_NAME}\") | .uid")

  if [ -z "$FOLDER_UID" ]; then
    echo "  Folder '$FOLDER_NAME' not found — already deleted or never existed. Skipping."
    echo ""
    continue
  fi
  echo "  Resolved folder UID: $FOLDER_UID"

  # ------------------------------------------------------------------
  # 2. Delete all alert rule groups inside this folder
  #    GET /api/ruler/grafana/api/v1/rules/{folderUID}
  #    returns: { "group-name": [...rules...], ... }
  # ------------------------------------------------------------------
  echo "  Checking for alert rule groups..."
  RULER_RESPONSE=$(curl -sf -u "$AUTH" \
    "${GRAFANA_URL}/api/ruler/grafana/api/v1/rules/${FOLDER_UID}" 2>/dev/null || echo "{}")

  GROUPS=$(echo "$RULER_RESPONSE" | jq -r 'keys[]' 2>/dev/null || true)

  if [ -n "$GROUPS" ]; then
    while IFS= read -r GROUP; do
      [ -z "$GROUP" ] && continue
      ENCODED_GROUP=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$GROUP")
      echo "  Deleting alert rule group: '$GROUP'"
      HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X DELETE \
        "${GRAFANA_URL}/api/ruler/grafana/api/v1/rules/${FOLDER_UID}/${ENCODED_GROUP}")
      if [[ "$HTTP_STATUS" =~ ^2 ]]; then
        echo "    Deleted (HTTP $HTTP_STATUS)"
      else
        echo "    Warning: DELETE returned HTTP $HTTP_STATUS for group '$GROUP'"
      fi
    done <<< "$GROUPS"
  else
    echo "  No alert rule groups found."
  fi

  # ------------------------------------------------------------------
  # 3. Delete all library panels in this folder
  #    GET /api/library-elements?folderFilter={folderUID}&perPage=100
  # ------------------------------------------------------------------
  echo "  Checking for library panels..."
  LIB_RESPONSE=$(curl -sf -u "$AUTH" \
    "${GRAFANA_URL}/api/library-elements?folderFilter=${FOLDER_UID}&perPage=100" 2>/dev/null || echo '{"result":{"elements":[]}}')

  LIB_UIDS=$(echo "$LIB_RESPONSE" | jq -r '.result.elements[].uid' 2>/dev/null || true)

  if [ -n "$LIB_UIDS" ]; then
    while IFS= read -r LIB_UID; do
      [ -z "$LIB_UID" ] && continue
      echo "  Deleting library panel: $LIB_UID"
      HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X DELETE \
        "${GRAFANA_URL}/api/library-elements/${LIB_UID}")
      if [[ "$HTTP_STATUS" =~ ^2 ]]; then
        echo "    Deleted (HTTP $HTTP_STATUS)"
      else
        echo "    Warning: DELETE returned HTTP $HTTP_STATUS for library panel '$LIB_UID'"
      fi
    done <<< "$LIB_UIDS"
  else
    echo "  No library panels found."
  fi

  # ------------------------------------------------------------------
  # 4. Delete the now-empty folder
  # ------------------------------------------------------------------
  echo "  Deleting folder '$FOLDER_NAME' ($FOLDER_UID)..."
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -u "$AUTH" -X DELETE \
    "${GRAFANA_URL}/api/folders/${FOLDER_UID}")

  if [[ "$HTTP_STATUS" =~ ^2 ]]; then
    echo "  Folder '$FOLDER_NAME' deleted successfully."
  else
    echo "  Warning: DELETE folder returned HTTP $HTTP_STATUS — folder may still have content."
    echo "  Re-check the Grafana UI for remaining dashboards, alerts, or library panels in '$FOLDER_NAME'."
  fi

  echo ""
done

echo "======================================================"
echo " Cleanup complete."
echo " Verify in Grafana UI:"
echo "   Dashboards → confirm Developer/Prometheus/Sentry are gone"
echo "   Alerting → Alert rules → no orphaned rules in those folders"
echo "   Dashboards → Library panels → no panels in deprecated folders"
echo "======================================================"
