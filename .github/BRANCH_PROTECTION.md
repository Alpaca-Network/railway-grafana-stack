# Branch Protection Rules Setup

To enable status checks on the `main` branch, follow these steps:

## 1. Go to Repository Settings
- Navigate to your GitHub repository
- Click **Settings** → **Branches**

## 2. Add Branch Protection Rule
- Click **Add rule**
- Branch name pattern: `main`

## 3. Enable Required Status Checks
Check the following options:

### Required Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

### Select Status Checks to Require
- `validate-json` - Validates all JSON and YAML files
- `lint-docker` - Lints all Dockerfiles
- `docker-build` - Builds all Docker images
- `test-docker-compose` - Tests the full stack
- `check-config` - Verifies required configuration files exist

### Additional Settings
- ✅ **Require code reviews before merging** (optional)
- ✅ **Dismiss stale pull request approvals when new commits are pushed** (optional)
- ✅ **Require status checks from code owners** (optional)

## 4. Save Changes
Click **Create** to enable branch protection.

## What This Does

Now when you:
- **Push to main**: All checks must pass
- **Create a PR to main**: All checks must pass before merging
- **Push to feature branches**: Checks run but don't block merging

## Status Checks Explained

| Check | Purpose | Time |
|-------|---------|------|
| `validate-json` | Ensures all JSON/YAML files are valid | ~10s |
| `lint-docker` | Checks Dockerfile best practices | ~30s |
| `docker-build` | Builds all Docker images | ~3-5min |
| `test-docker-compose` | Runs full stack health checks | ~2-3min |
| `check-config` | Verifies required files exist | ~5s |

**Total time**: ~5-10 minutes per check run

## Bypassing Protection (if needed)

Repository admins can still push directly to `main` and merge PRs without checks, but this is not recommended.
