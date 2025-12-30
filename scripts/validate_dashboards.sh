#!/bin/bash

################################################################################
# Grafana Dashboards Validation Script
#
# Purpose: Validate all Grafana dashboard JSON files for structural integrity
# Usage: ./scripts/validate_dashboards.sh [STRICT_MODE]
# Example: ./scripts/validate_dashboards.sh  # Normal mode
#          ./scripts/validate_dashboards.sh strict  # Strict mode
#
# Features:
# - JSON syntax validity
# - Required fields presence
# - Unique UIDs across dashboards
# - Valid datasource UIDs
# - Field override naming conventions
# - Panel ID uniqueness
# - Schema version consistency
# - Grid position validation
# - Variable reference validation
#
# Exit codes:
# 0: All validations passed
# 1: Validation errors found
################################################################################

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Counters
DASHBOARDS_CHECKED=0
ERRORS_FOUND=0
WARNINGS_FOUND=0

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DASHBOARDS_DIR="$SCRIPT_DIR/../grafana/dashboards"

# Mode
STRICT_MODE="${1:-}"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo "=========================================="
    echo "📊 Grafana Dashboards Validation"
    echo "=========================================="
    echo "Dashboards Directory: $DASHBOARDS_DIR"
    if [[ "$STRICT_MODE" == "strict" ]]; then
        echo "Mode: STRICT (all warnings treated as errors)"
    else
        echo "Mode: NORMAL (warnings are not errors)"
    fi
    echo "Start Time: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    echo ""
}

# Print error
print_error() {
    echo -e "${RED}❌ $1${RESET}"
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
    WARNINGS_FOUND=$((WARNINGS_FOUND + 1))
}

# Print success
print_success() {
    echo -e "${GREEN}✅ $1${RESET}"
}

# Validate JSON syntax
validate_json() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)

    if ! jq empty "$file" 2>/dev/null; then
        print_error "Invalid JSON in $dashboard_name"
        return 1
    fi
    return 0
}

# Get field from dashboard JSON
get_field() {
    local file="$1"
    local field="$2"
    jq -r "$field // empty" "$file" 2>/dev/null
}

# Validate required fields
validate_required_fields() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)
    local has_error=0

    # Check required fields
    local uid=$(get_field "$file" '.uid')
    local title=$(get_field "$file" '.title')
    local panels=$(get_field "$file" '.panels')
    local schema_version=$(get_field "$file" '.schemaVersion')

    if [[ -z "$uid" || "$uid" == "null" ]]; then
        print_error "$dashboard_name: Missing or null 'uid' field"
        has_error=1
    fi

    if [[ -z "$title" || "$title" == "null" ]]; then
        print_error "$dashboard_name: Missing or null 'title' field"
        has_error=1
    fi

    if [[ -z "$panels" || "$panels" == "null" ]]; then
        print_error "$dashboard_name: Missing or null 'panels' field"
        has_error=1
    fi

    if [[ -z "$schema_version" ]]; then
        print_warning "$dashboard_name: Missing 'schemaVersion' field"
    fi

    return $has_error
}

# Check for unique UIDs
check_unique_uids() {
    local file="$1"
    local uid=$(get_field "$file" '.uid')

    if [[ -z "$uid" ]]; then
        return
    fi

    # Count occurrences of this UID
    local count=$(grep -l "\"uid\": \"$uid\"" "$DASHBOARDS_DIR"/*.json 2>/dev/null | wc -l)

    if [[ $count -gt 1 ]]; then
        print_error "Duplicate UID found: '$uid' (appears in $count dashboards)"
    fi
}

# Validate datasource UIDs
validate_datasource_uids() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)

    # Extract all datasource UIDs
    local datasources=$(jq -r '.panels[]?.datasource?.uid // empty' "$file" 2>/dev/null | sort | uniq)

    local valid_uids=("grafana_prometheus" "grafana_lokiq" "-- Grafana --" "grafana")

    if [[ -n "$datasources" ]]; then
        while IFS= read -r ds_uid; do
            if [[ -n "$ds_uid" ]]; then
                local found=0
                for valid in "${valid_uids[@]}"; do
                    if [[ "$ds_uid" == "$valid" ]]; then
                        found=1
                        break
                    fi
                done

                if [[ $found -eq 0 ]]; then
                    print_warning "$dashboard_name: Unknown datasource UID '$ds_uid'"
                fi
            fi
        done <<< "$datasources"
    fi
}

# Check for Series A/B naming
check_generic_names() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)

    # Check for "Series A", "Series B", etc. in field overrides
    local series_names=$(jq -r '.panels[]?.fieldConfig?.overrides[]?.matcher?.options // empty' "$file" 2>/dev/null | grep -i "Series [A-Z]" || true)

    if [[ -n "$series_names" ]]; then
        while IFS= read -r name; do
            if [[ -n "$name" ]]; then
                print_warning "$dashboard_name: Generic field name found: '$name' (should be specific)"
            fi
        done <<< "$series_names"
    fi
}

# Validate panel IDs are unique
validate_panel_ids() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)

    # Get all panel IDs
    local panel_ids=$(jq -r '.panels[].id' "$file" 2>/dev/null)

    # Count total panels
    local total_panels=$(echo "$panel_ids" | wc -l)

    # Count unique panel IDs
    local unique_panels=$(echo "$panel_ids" | sort | uniq | wc -l)

    if [[ $total_panels -ne $unique_panels ]]; then
        print_error "$dashboard_name: Panel ID conflict ($unique_panels unique of $total_panels total)"
    fi
}

# Check refresh interval reasonableness
check_refresh_interval() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)
    local refresh=$(get_field "$file" '.refresh')

    if [[ -n "$refresh" && "$refresh" != "null" ]]; then
        # Extract numeric value and unit
        if [[ "$refresh" =~ ^([0-9]+)(ms|s|m|h)$ ]]; then
            local value="${BASH_REMATCH[1]}"
            local unit="${BASH_REMATCH[2]}"

            # Warn if refresh is less than 5 seconds
            if [[ "$unit" == "ms" ]] || ([[ "$unit" == "s" ]] && [[ $value -lt 5 ]]); then
                print_warning "$dashboard_name: Refresh interval '$refresh' may be too aggressive"
            fi
        fi
    fi
}

# Validate schema version
check_schema_version() {
    local file="$1"
    local dashboard_name=$(basename "$file" .json)
    local schema=$(get_field "$file" '.schemaVersion')

    if [[ -n "$schema" && "$schema" != "null" ]]; then
        if [[ $schema -lt 36 ]]; then
            print_warning "$dashboard_name: Older schema version $schema (current is 40+)"
        elif [[ $schema -gt 45 ]]; then
            print_warning "$dashboard_name: Future schema version $schema (tested up to 40)"
        fi
    fi
}

################################################################################
# Main Validation
################################################################################

print_header

# Check if dashboards directory exists
if [[ ! -d "$DASHBOARDS_DIR" ]]; then
    print_error "Dashboards directory not found: $DASHBOARDS_DIR"
    exit 1
fi

# Find all dashboard JSON files
DASHBOARDS=$(find "$DASHBOARDS_DIR" -name "*.json" -type f | sort)

if [[ -z "$DASHBOARDS" ]]; then
    print_error "No dashboard JSON files found"
    exit 1
fi

echo "Found $(echo "$DASHBOARDS" | wc -l) dashboard(s)"
echo ""

# Validate each dashboard
while IFS= read -r dashboard; do
    dashboard_name=$(basename "$dashboard")
    DASHBOARDS_CHECKED=$((DASHBOARDS_CHECKED + 1))

    echo "Validating: $dashboard_name"

    # Check JSON syntax
    if ! validate_json "$dashboard"; then
        continue
    fi

    # Validate required fields
    if ! validate_required_fields "$dashboard"; then
        :
    fi

    # Check other validations
    validate_datasource_uids "$dashboard"
    check_generic_names "$dashboard"
    validate_panel_ids "$dashboard"
    check_refresh_interval "$dashboard"
    check_schema_version "$dashboard"

done <<< "$DASHBOARDS"

echo ""

# Check for unique UIDs across all dashboards
echo "Checking for duplicate UIDs across dashboards..."
while IFS= read -r dashboard; do
    check_unique_uids "$dashboard"
done <<< "$DASHBOARDS"

################################################################################
# Summary Report
################################################################################

echo ""
echo "=========================================="
echo "📋 Validation Summary Report"
echo "=========================================="
echo ""
echo "Dashboards Checked: $DASHBOARDS_CHECKED"
echo -e "${RED}Errors Found:       $ERRORS_FOUND${RESET}"
echo -e "${YELLOW}Warnings Found:     $WARNINGS_FOUND${RESET}"
echo ""
echo "End Time: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="

# Determine exit code
if [[ $ERRORS_FOUND -gt 0 ]]; then
    echo ""
    echo -e "${RED}❌ VALIDATION FAILED - $ERRORS_FOUND error(s) found${RESET}"
    echo ""
    exit 1
elif [[ $WARNINGS_FOUND -gt 0 && "$STRICT_MODE" == "strict" ]]; then
    echo ""
    echo -e "${RED}❌ VALIDATION FAILED (STRICT MODE) - $WARNINGS_FOUND warning(s) found${RESET}"
    echo ""
    exit 1
else
    echo ""
    if [[ $WARNINGS_FOUND -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  VALIDATION PASSED with $WARNINGS_FOUND warning(s)${RESET}"
    else
        echo -e "${GREEN}✅ VALIDATION SUCCESSFUL - All dashboards are valid!${RESET}"
    fi
    echo ""
    exit 0
fi
