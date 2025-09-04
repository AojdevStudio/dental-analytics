---
title: "Branch Protection Configuration Guide"
description: "Instructions for setting up branch protection rules for the dental analytics project."
category: "CI/CD"
subcategory: "Branch Protection"
product_line: "Dental Analytics"
audience: "DevOps, Project Maintainers"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - branch-protection
  - github
  - ci-cd
  - quality-gates
---

# Branch Protection Configuration

This document provides instructions for configuring branch protection rules for the dental analytics repository to enforce quality gates and prevent direct pushes to critical branches.

## Required Branch Protection Rules

### Main Branch Protection (`main`)

Configure the following settings for the `main` branch:

#### General Settings
- ✅ **Restrict pushes that create files larger than 100MB**
- ✅ **Require a pull request before merging**
- ✅ **Require approvals**: 1 approval minimum
- ✅ **Dismiss stale PR approvals when new commits are pushed**
- ✅ **Require review from code owners**

#### Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required Status Checks:**
- `quality-gates / enforce-quality-gate`
- `test-matrix (3.10)`
- `test-matrix (3.11)`
- `test-matrix (3.12)`
- `security-scan`
- `performance-test`
- `build-validation`

#### Additional Restrictions
- ✅ **Restrict pushes that create files larger than 100MB**
- ✅ **Do not allow bypassing the above settings**
- ❌ **Allow force pushes** (disabled for safety)
- ❌ **Allow deletions** (disabled for safety)

### Develop Branch Protection (`develop`)

Configure the following settings for the `develop` branch:

#### General Settings
- ✅ **Require a pull request before merging**
- ✅ **Require approvals**: 1 approval minimum
- ✅ **Dismiss stale PR approvals when new commits are pushed**

#### Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**

**Required Status Checks:**
- `quality-gates / enforce-quality-gate`
- `test-matrix (3.11)` (minimum one Python version)
- `security-scan`

## Environment Protection Rules

### Staging Environment

Create a `staging` environment with the following rules:

#### Deployment Branches
- ✅ **Protected branches only**: `develop`, `story-*`
- ✅ **Required reviewers**: 0 (automated deployment)
- ✅ **Wait timer**: 0 minutes
- ✅ **Prevent self-review**: Enabled

#### Environment Secrets
Configure the following secrets for staging:
- `STAGING_GOOGLE_PROJECT_ID`
- `STAGING_GOOGLE_PRIVATE_KEY_ID`
- `STAGING_GOOGLE_PRIVATE_KEY`
- `STAGING_GOOGLE_CLIENT_EMAIL`
- `STAGING_GOOGLE_CLIENT_ID`
- `STREAMLIT_SHARING_EMAIL`

### Production Environment

Create a `production` environment with the following rules:

#### Deployment Branches
- ✅ **Protected branches only**: `main`
- ✅ **Required reviewers**: 1 (manual approval required)
- ✅ **Wait timer**: 5 minutes (reflection period)
- ✅ **Prevent self-review**: Enabled

#### Environment Secrets
Configure the following secrets for production:
- `PROD_GOOGLE_PROJECT_ID`
- `PROD_GOOGLE_PRIVATE_KEY_ID`
- `PROD_GOOGLE_PRIVATE_KEY`
- `PROD_GOOGLE_CLIENT_EMAIL`
- `PROD_GOOGLE_CLIENT_ID`
- `STREAMLIT_SHARING_EMAIL`
- `CODECOV_TOKEN`

## Repository Secrets

Configure the following repository-level secrets:

### Authentication
- `GITHUB_TOKEN` (automatically provided)
- `CODECOV_TOKEN` (for coverage reporting)

### Notifications (Optional)
- `SLACK_WEBHOOK_URL` (for deployment notifications)
- `DISCORD_WEBHOOK_URL` (alternative notification channel)

## GitHub Repository Settings

### General Repository Settings
- ✅ **Allow squash merging**: Enabled
- ✅ **Allow merge commits**: Enabled
- ✅ **Allow rebase merging**: Enabled
- ✅ **Always suggest updating pull request branches**: Enabled
- ✅ **Allow auto-merge**: Enabled (for automated dependency updates)
- ✅ **Automatically delete head branches**: Enabled

### Security Settings
- ✅ **Enable vulnerability alerts**: Enabled
- ✅ **Enable Dependabot alerts**: Enabled
- ✅ **Enable Dependabot security updates**: Enabled
- ✅ **Enable Dependabot version updates**: Enabled

### Actions Settings
- ✅ **Allow actions and reusable workflows**: Any action or reusable workflow
- ✅ **Allow actions created by GitHub**: Enabled
- ✅ **Allow actions by Marketplace verified creators**: Enabled

## Implementation Steps

### 1. Configure Branch Protection

1. Go to **Settings** → **Branches** in your repository
2. Click **Add rule** for `main` branch
3. Apply all settings listed above for main branch
4. Repeat for `develop` branch with its specific settings

### 2. Create Environments

1. Go to **Settings** → **Environments**
2. Create `staging` environment with specified rules
3. Create `production` environment with specified rules
4. Add required secrets to each environment

### 3. Configure Repository Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add all repository-level secrets listed above

### 4. Verify Configuration

1. Create a test branch from `develop`
2. Make a small change and create a PR to `develop`
3. Verify that all required status checks run
4. Verify that merge is blocked until checks pass
5. Test the same flow for `main` branch

## Quality Gate Enforcement

The branch protection rules work in conjunction with the quality gate workflow to ensure:

1. **Code Quality**: All code must pass formatting, linting, and type checking
2. **Test Coverage**: Minimum 90% test coverage required
3. **Security**: No security vulnerabilities in dependencies or code
4. **Performance**: Performance benchmarks must pass
5. **Review Process**: Code reviews required for all changes

## Troubleshooting

### Common Issues

1. **Status checks not running**
   - Verify workflow files are in `.github/workflows/`
   - Check workflow syntax and permissions
   - Ensure branch naming matches workflow triggers

2. **Required status checks missing**
   - Check that status check names match workflow job names exactly
   - Verify workflows are enabled in repository settings

3. **Environment secrets not working**
   - Confirm secret names match exactly (case-sensitive)
   - Verify environment names in workflows match configured environments

### Contact Information

For issues with branch protection or CI/CD pipeline:
- Repository Owner: @ossieirondi
- Review the workflow logs in Actions tab
- Check repository Issues for known problems

## Monitoring and Maintenance

- **Weekly**: Review failed CI/CD runs and address any infrastructure issues
- **Monthly**: Update required status checks if new quality gates are added
- **Quarterly**: Review and update branch protection rules based on team feedback

This configuration ensures that only high-quality, tested, and secure code is merged into critical branches while maintaining development velocity.
