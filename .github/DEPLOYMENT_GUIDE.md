# Deployment Guide

This guide explains how the CI/CD workflow handles deployments to the Production environment.

## 🔄 Workflow Overview

The `deploy.yml` workflow manages the build, validation, and deployment process.

### Triggers

| Branch / Event | Environment | Action |
|---------------|------------|--------|
| `main` | Production | Push to main branch |
| Manual Dispatch | Production | Manual trigger via GitHub Actions UI |

### Manual Trigger Inputs

When manually triggering the workflow, you can select the environment (currently only 'production' is supported as Staging is deprecated).

## 📋 Phases

1. **Validation** - Validates JSON dashboards and YAML configuration files
2. **Determine Environment** - Sets deployment variables based on branch/input
3. **Build Images** - Builds Docker images for all services (cached for speed)
4. **Deploy Production** - Deploys to Production environment (if triggered)
5. **Summary** - Reports status of the deployment

## 🔐 Secrets Configuration

Required GitHub Secrets for deployment:

### Production Environment
- `RAILWAY_TOKEN_PRODUCTION` - Railway API token for production project
- `RAILWAY_PROJECT_ID_PRODUCTION` - Railway project ID for production
- `PRODUCTION_GRAFANA_URL` (optional) - URL to verify production deployment

## 🚀 How to Deploy

### Automatic Deployment

1. Merge Pull Request to `main` branch
2. Workflow automatically triggers validation and deployment to Production

### Manual Deployment

1. Go to **Actions** tab in GitHub
2. Select "Deploy to Production" workflow
3. Click **Run workflow**
4. Select environment: `production`
5. Click **Run workflow**

## ✅ Verification

The workflow performs automated verification after deployment:
1. Checks that the health endpoint is reachable (HTTP 200)
2. Retries for up to 5 minutes to allow for startup time

## 🛑 Rollback

If a deployment fails or issues are found:
1. Revert the commit in `main`
2. Push the revert
3. The workflow will deploy the previous stable version
