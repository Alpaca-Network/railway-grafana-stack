# Deployment Guide

This guide explains how the CI/CD workflow handles deployments to Production and Staging environments.

## Overview

The deployment workflow (`deploy.yml`) automatically deploys to different environments based on:
1. **Branch name** (automatic push triggers)
2. **Manual workflow dispatch** (with environment selection)

## Deployment Rules

### Automatic Deployments (on push)

| Branch | Environment | Trigger |
|--------|-------------|---------|
| `main` | Production | Push to main branch |
| `staging` | Staging | Push to staging branch |
| `refactor/**` | Staging | Push to any refactor branch |
| `fix/**` | Staging | Push to any fix branch |

### Manual Deployments (workflow_dispatch)

You can manually trigger deployments from GitHub Actions with these options:
- **staging** - Deploy only to Staging
- **production** - Deploy only to Production
- **both** - Deploy to both Staging and Production

## Workflow Steps

1. **Validate** - Validates JSON dashboards and YAML configuration files
2. **Determine Environment** - Decides which environment(s) to deploy to
3. **Build Images** - Builds Docker images for all services
4. **Deploy Staging** (if applicable) - Deploys to Staging environment
5. **Deploy Production** (if applicable) - Deploys to Production environment
6. **Summary** - Prints deployment summary

## Required Secrets

Configure these secrets in your GitHub repository settings:

### Staging Environment
- `RAILWAY_TOKEN_STAGING` - Railway API token for staging project
- `RAILWAY_PROJECT_ID_STAGING` - Railway project ID for staging
- `STAGING_GRAFANA_URL` (optional) - URL to verify staging deployment

### Production Environment
- `RAILWAY_TOKEN_PRODUCTION` - Railway API token for production project
- `RAILWAY_PROJECT_ID_PRODUCTION` - Railway project ID for production
- `PRODUCTION_GRAFANA_URL` (optional) - URL to verify production deployment

## How to Set Up Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Create new repository secrets with the names above
4. Paste your Railway tokens and project IDs

## Triggering Deployments

### Automatic (on push)
```bash
# Deploy to Staging
git push origin refactor/my-feature

# Deploy to Production
git push origin main
```

### Manual (workflow_dispatch)
1. Go to GitHub Actions tab
2. Select "Deploy to Production & Staging" workflow
3. Click "Run workflow"
4. Select environment: staging, production, or both
5. Click "Run workflow"

## Verification

Each deployment includes health checks for:
- Grafana (`/api/health`)
- Prometheus (`/-/healthy`)
- Loki (`/ready`)
- Tempo (`/status`)

## Troubleshooting

### Deployment fails with "Railway token not found"
- Verify secrets are set in GitHub repository settings
- Check secret names match exactly (case-sensitive)

### Services don't start after deployment
- Check Railway logs in the Railway dashboard
- Verify environment variables are set correctly
- Ensure docker-compose.yml is valid

### Health checks timeout
- Services may still be starting (normal for first deployment)
- Check Railway logs for startup errors
- Verify network connectivity between services

## Best Practices

1. **Always test in Staging first** - Push to a feature branch to deploy to staging
2. **Use meaningful branch names** - Helps identify what's being deployed
3. **Review changes before production** - Use pull requests to main branch
4. **Monitor deployments** - Check GitHub Actions logs and Railway dashboard
5. **Keep secrets secure** - Never commit tokens or passwords to git

## CI/CD Pipeline

```
Push to branch
    ↓
Validate (JSON/YAML)
    ↓
Determine Environment
    ↓
Build Docker Images
    ↓
Deploy to Staging (if applicable)
    ↓
Deploy to Production (if applicable)
    ↓
Summary Report
```
