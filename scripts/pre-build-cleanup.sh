#!/bin/bash
# ==============================================================================
# Pre-Build Cleanup Script for Railway Deployments
# ==============================================================================
# Run this BEFORE deploying to Railway to remove deprecated directories/files
# that may persist between builds and cause issues.
#
# Usage:
#   ./scripts/pre-build-cleanup.sh [--dry-run]
#
# Options:
#   --dry-run    Show what would be deleted without actually deleting
# ==============================================================================

# Don't use set -e because ((var++)) returns 1 when var is 0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check for dry-run mode
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo -e "${YELLOW}[DRY-RUN MODE] No files will be deleted${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Build Cleanup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Project root: ${PROJECT_ROOT}"
echo ""

# Track what we're cleaning
CLEANED=0
SKIPPED=0

# Function to remove item (file or directory)
remove_item() {
    local path="$1"
    local description="$2"

    if [[ -e "$path" || -d "$path" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo -e "${YELLOW}[WOULD DELETE]${NC} $description"
            echo "               Path: $path"
        else
            echo -e "${RED}[DELETING]${NC} $description"
            rm -rf "$path"
            echo -e "${GREEN}[DELETED]${NC} $path"
        fi
        ((CLEANED++))
    else
        echo -e "${GREEN}[SKIP]${NC} $description (not found)"
        ((SKIPPED++))
    fi
}

echo -e "${BLUE}--- Cleaning Deprecated Directories ---${NC}"
echo ""

# 1. Remove root alertmanager directory (now integrated into Prometheus)
remove_item \
    "${PROJECT_ROOT}/alertmanager" \
    "Root alertmanager/ directory (integrated into Prometheus)"

# 2. Remove empty prometheus/alertmanager.yml directory (should be a file, not dir)
remove_item \
    "${PROJECT_ROOT}/prometheus/alertmanager.yml" \
    "Empty prometheus/alertmanager.yml directory"

# 3. Clean up any .DS_Store files (macOS)
echo ""
echo -e "${BLUE}--- Cleaning macOS .DS_Store files ---${NC}"
if [[ "$DRY_RUN" == true ]]; then
    DS_COUNT=$(find "${PROJECT_ROOT}" -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}[WOULD DELETE]${NC} ${DS_COUNT} .DS_Store files"
else
    DS_COUNT=$(find "${PROJECT_ROOT}" -name ".DS_Store" -delete -print 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}[DELETED]${NC} ${DS_COUNT} .DS_Store files"
fi

# 5. Clean up Python cache directories
echo ""
echo -e "${BLUE}--- Cleaning Python Cache ---${NC}"
if [[ "$DRY_RUN" == true ]]; then
    PYCACHE_COUNT=$(find "${PROJECT_ROOT}" -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${YELLOW}[WOULD DELETE]${NC} ${PYCACHE_COUNT} __pycache__ directories"
else
    PYCACHE_COUNT=$(find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; echo $?)
    find "${PROJECT_ROOT}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}[CLEANED]${NC} __pycache__ directories"
fi

# 6. Clean up .pytest_cache
remove_item \
    "${PROJECT_ROOT}/.pytest_cache" \
    ".pytest_cache directory"

# 7. Clean up any stray volume data that shouldn't be committed
echo ""
echo -e "${BLUE}--- Checking for stray volume data ---${NC}"
for vol_dir in "prometheus_data" "grafana_data" "loki_data" "tempo_data" "mimir_data" "alertmanager_data"; do
    if [[ -d "${PROJECT_ROOT}/${vol_dir}" ]]; then
        remove_item "${PROJECT_ROOT}/${vol_dir}" "Stray volume directory: ${vol_dir}"
    fi
done

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup Summary${NC}"
echo -e "${BLUE}========================================${NC}"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}Items that would be cleaned: ${CLEANED}${NC}"
    echo -e "${GREEN}Items already clean (skipped): ${SKIPPED}${NC}"
    echo ""
    echo -e "${YELLOW}Run without --dry-run to actually delete files${NC}"
else
    echo -e "${GREEN}Items cleaned: ${CLEANED}${NC}"
    echo -e "${GREEN}Items skipped (already clean): ${SKIPPED}${NC}"
fi
echo ""

# Verify docker-compose is valid
echo -e "${BLUE}--- Validating docker-compose.yml ---${NC}"
if command -v docker &> /dev/null; then
    if docker compose -f "${PROJECT_ROOT}/docker-compose.yml" config > /dev/null 2>&1; then
        echo -e "${GREEN}[VALID]${NC} docker-compose.yml syntax is correct"
    else
        echo -e "${RED}[WARNING]${NC} docker-compose.yml may have issues"
        echo "Run: docker compose config"
    fi
else
    echo -e "${YELLOW}[SKIP]${NC} Docker not installed, skipping validation"
fi

echo ""
echo -e "${GREEN}Pre-build cleanup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit cleanup: git add -A && git commit -m 'chore: pre-build cleanup'"
echo "  3. Deploy to Railway: git push"
