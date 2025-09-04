---
title: "CI/CD Pipeline Documentation"
description: "Complete guide to the continuous integration and deployment pipeline for dental analytics."
category: "Documentation"
subcategory: "CI/CD"
product_line: "Dental Analytics"
audience: "Developers, DevOps, QA"
status: "Active"
author: "AOJDevStudio"
created_date: "2025-09-04"
last_updated: "2025-09-04"
tags:
  - ci-cd
  - github-actions
  - quality-gates
  - deployment
  - monitoring
---

# CI/CD Pipeline Documentation

## Overview

The Dental Analytics CI/CD pipeline is designed to enforce the quality framework established by QA while automating testing, security scanning, and deployment processes. The pipeline ensures that only high-quality, secure code reaches production.

## Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │   Staging       │    │   Production    │
│                 │    │                 │    │                 │
│ • Local Testing │───▶│ • Auto Deploy  │───▶│ • Manual Deploy │
│ • Pre-commit    │    │ • Smoke Tests   │    │ • Health Checks │
│ • Branch Push   │    │ • Integration   │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Quality Gates  │    │  Security Scan  │    │   Monitoring    │
│                 │    │                 │    │                 │
│ • Format Check  │    │ • Dependency    │    │ • Performance   │
│ • Linting       │    │ • Static Analysis │  │ • Error Rates   │
│ • Type Check    │    │ • Secret Scan   │    │ • Uptime        │
│ • Test Coverage │    │ • Vuln Assessment │  │ • User Metrics  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Workflows Overview

### 1. Main CI/CD Pipeline (`ci.yml`)

**Triggers:**
- Push to `main`, `develop`, `story-*` branches
- Pull requests to `main`, `develop`
- Manual dispatch

**Jobs Flow:**
1. **Quality Gates** → Code formatting, linting, type checking
2. **Security Scan** → Dependency audit, secret detection, static analysis
3. **Test Matrix** → Unit tests across Python 3.10, 3.11, 3.12
4. **Coverage Report** → Track coverage trends and PR comments
5. **Performance Test** → Benchmark critical functions
6. **Integration Test** → External API and service testing
7. **Build Validation** → Package building and validation
8. **Deploy Staging** → Automated deployment to staging (non-main branches)
9. **Deploy Production** → Manual approval deployment (main branch only)
10. **Quality Metrics** → Collect and report quality trends

### 2. Quality Gate Enforcement (`quality-gate.yml`)

**Purpose:** Block PRs that don't meet quality standards

**Triggers:**
- Pull request opened, synchronized, reopened

**Enforcement Rules:**
- ✅ Code formatting (Black)
- ✅ Linting (Ruff)
- ✅ Type checking (MyPy)
- ✅ Test coverage ≥ 90%
- ✅ Code complexity ≤ 10
- ✅ Security scan passed
- ✅ No dead code

### 3. Deployment Pipeline (`deploy.yml`)

**Purpose:** Handle staging and production deployments

**Features:**
- Pre-deployment validation
- Environment-specific configuration
- Health checks and verification
- Automated rollback on failure
- Deployment tagging and notifications

### 4. Monitoring & Metrics (`monitoring.yml`)

**Purpose:** Track quality trends and application health

**Schedules:**
- Daily at 9 AM UTC (business hours consideration)
- On-demand via workflow dispatch
- After every main branch push

**Metrics Collected:**
- Code quality trends
- Performance benchmarks
- Security vulnerabilities
- Deployment health
- Application metrics

## Quality Gates in Detail

### Code Quality Standards

```python
# Enforced via Black, Ruff, and MyPy
def calculate_production_total(df: pd.DataFrame) -> float:
    """Calculate total production from dental data.

    Args:
        df: DataFrame containing Production column

    Returns:
        Total production amount

    Raises:
        ValueError: If Production column missing
    """
    if 'Production' not in df.columns:
        raise ValueError("Production column required")
    return float(df['Production'].sum())
```

### Coverage Requirements

- **Minimum**: 90% line coverage
- **Scope**: `backend/` and `frontend/` modules
- **Exclusions**: Test files, __init__.py files
- **Reporting**: XML and JSON formats for trend analysis

### Security Standards

- **Dependency Scanning**: pip-audit for known vulnerabilities
- **Static Analysis**: Bandit for security anti-patterns
- **Secret Detection**: TruffleHog for exposed credentials
- **Compliance**: Security findings reported but don't block (with warnings)

### Performance Benchmarks

```python
# Example performance test
def test_production_calculation_performance(benchmark):
    """Ensure production calculations are performant."""
    large_data = pd.DataFrame({'Production': [1000.0] * 10000})
    result = benchmark(calculate_production_total, large_data)
    assert result == 10000000.0
    # Benchmark automatically tracks performance trends
```

## Deployment Strategy

### Staging Deployment (Automated)

**Triggers:** Push to `develop` or `story-*` branches
**Process:**
1. Pre-deployment validation
2. Create deployment package
3. Deploy to Streamlit Cloud staging
4. Run smoke tests
5. Update deployment status

**Configuration:**
- Environment: `staging`
- Debug mode: enabled
- Test credentials: used
- URL: `https://staging-dental-analytics.streamlit.app`

### Production Deployment (Manual)

**Triggers:** Push to `main` branch (with manual approval)
**Process:**
1. Final pre-production validation
2. Security and performance verification
3. Create production package
4. Deploy with 5-minute reflection period
5. Comprehensive health checks
6. Create deployment tag
7. Monitor for issues

**Configuration:**
- Environment: `production`
- Debug mode: disabled
- Production credentials: used
- URL: `https://dental-analytics.streamlit.app`

## Environment Configuration

### Staging Environment

```yaml
# .streamlit/secrets.toml (staging)
[general]
environment = "staging"

[google_sheets]
type = "service_account"
project_id = "${{ secrets.STAGING_GOOGLE_PROJECT_ID }}"
# ... other staging credentials
```

### Production Environment

```yaml
# .streamlit/secrets.toml (production)
[general]
environment = "production"

[google_sheets]
type = "service_account"
project_id = "${{ secrets.PROD_GOOGLE_PROJECT_ID }}"
# ... other production credentials
```

## Monitoring and Alerting

### Application Metrics

- **Daily Active Users**: Tracked via application logs
- **API Call Volume**: Google Sheets API usage monitoring
- **Error Rates**: Application error tracking
- **Response Times**: Performance monitoring
- **Uptime**: Service availability tracking

### Quality Metrics

- **Code Coverage Trends**: Historical coverage data
- **Test Count Growth**: Test suite expansion tracking
- **Security Issues**: Vulnerability trend analysis
- **Performance Regression**: Benchmark comparison
- **Code Complexity**: Maintainability tracking

### Health Scoring

```python
# Overall health calculation
health_score = 100
if coverage < 90:
    health_score -= 20
if security_issues > 0:
    health_score -= 25
if performance_regression:
    health_score -= 15
if deployment_unhealthy:
    health_score -= 30

status = "healthy" if health_score >= 80 else \
         "needs_attention" if health_score >= 60 else \
         "critical"
```

## Branch Strategy

### Main Branches

- **`main`**: Production-ready code, protected with strict rules
- **`develop`**: Integration branch, moderately protected

### Feature Branches

- **`story-*`**: User story implementation branches
- **`bugfix/*`**: Bug fix branches
- **`hotfix/*`**: Critical production fixes

### Branch Protection Rules

```yaml
main:
  required_reviews: 1
  dismiss_stale_reviews: true
  required_status_checks:
    - "quality-gates / enforce-quality-gate"
    - "test-matrix (3.10)"
    - "test-matrix (3.11)"
    - "test-matrix (3.12)"
    - "security-scan"
    - "build-validation"
  restrict_pushes: true
  allow_force_pushes: false
  allow_deletions: false

develop:
  required_reviews: 1
  required_status_checks:
    - "quality-gates / enforce-quality-gate"
    - "test-matrix (3.11)"
    - "security-scan"
```

## Rollback Procedures

### Automatic Rollback Triggers

1. **Health Check Failures**: Post-deployment verification fails
2. **Performance Regression**: Response times exceed thresholds
3. **Security Alert**: Critical vulnerability detected
4. **Error Rate Spike**: Application error rate > 5%

### Manual Rollback Process

```bash
# Emergency rollback procedure
1. Navigate to GitHub Actions
2. Select latest deployment workflow
3. Manually trigger rollback job
4. Monitor health checks
5. Verify rollback success
6. Investigate and fix underlying issue
```

## Secrets Management

### Required Secrets

**Repository Level:**
- `CODECOV_TOKEN`: Code coverage reporting
- `GITHUB_TOKEN`: Automatic (GitHub-provided)

**Staging Environment:**
- `STAGING_GOOGLE_PROJECT_ID`
- `STAGING_GOOGLE_PRIVATE_KEY_ID`
- `STAGING_GOOGLE_PRIVATE_KEY`
- `STAGING_GOOGLE_CLIENT_EMAIL`
- `STAGING_GOOGLE_CLIENT_ID`

**Production Environment:**
- `PROD_GOOGLE_PROJECT_ID`
- `PROD_GOOGLE_PRIVATE_KEY_ID`
- `PROD_GOOGLE_PRIVATE_KEY`
- `PROD_GOOGLE_CLIENT_EMAIL`
- `PROD_GOOGLE_CLIENT_ID`

## Troubleshooting

### Common Issues

1. **Quality Gate Failures**
   ```bash
   # Fix formatting
   uv run black backend/ frontend/ tests/

   # Fix linting
   uv run ruff check --fix backend/ frontend/ tests/

   # Check types
   uv run mypy backend/ tests/
   ```

2. **Coverage Below Threshold**
   ```bash
   # Run coverage report
   uv run pytest --cov=backend --cov=frontend --cov-report=term-missing

   # Add tests for uncovered code
   # Focus on business logic in backend/metrics.py
   ```

3. **Security Scan Issues**
   ```bash
   # Update dependencies
   uv sync --upgrade

   # Check for vulnerabilities
   uv add pip-audit
   uv run pip-audit

   # Review Bandit findings
   uv add bandit[toml]
   uv run bandit -r backend/
   ```

4. **Deployment Failures**
   - Check Streamlit Cloud status
   - Verify secrets are correctly configured
   - Review deployment logs in GitHub Actions
   - Ensure all required files are included in deployment package

### Performance Debugging

```python
# Add performance profiling
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your function call here
    result = calculate_production_total(large_df)

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

    return result
```

## Best Practices

### Development Workflow

1. **Create Feature Branch**: From `develop`
2. **Implement Changes**: Follow coding standards
3. **Run Local Tests**: `uv run pytest`
4. **Pre-commit Hooks**: Automatic quality checks
5. **Push Branch**: Triggers CI pipeline
6. **Create Pull Request**: To `develop` or `main`
7. **Address Feedback**: Fix any CI failures
8. **Merge**: After approval and quality gates pass

### Code Quality

- Write comprehensive tests for all business logic
- Use type hints for all function parameters and returns
- Follow dental domain naming conventions
- Keep functions focused and under 20 lines
- Document complex calculations with docstrings

### Security

- Never commit credentials or API keys
- Use environment secrets for sensitive data
- Regularly update dependencies
- Review security scan results
- Follow principle of least privilege

## Maintenance

### Weekly Tasks

- Review failed CI/CD runs
- Update dependencies via Dependabot PRs
- Monitor performance trends
- Check security alerts

### Monthly Tasks

- Review and update quality thresholds
- Analyze deployment success rates
- Update documentation
- Performance optimization review

### Quarterly Tasks

- Review and update CI/CD pipeline
- Security audit and penetration testing
- Infrastructure cost optimization
- Team training on new tools/processes

## Integration with BMAD Workflow

The CI/CD pipeline integrates seamlessly with the BMAD (Backlog Management and Development) workflow:

1. **User Story Planning**: Stories tagged with `story-*` branches
2. **Development Phase**: Quality gates enforce coding standards
3. **Testing Phase**: Automated test execution and coverage reporting
4. **Review Phase**: PR quality gates and manual review process
5. **Deployment Phase**: Automated staging, manual production approval
6. **Monitoring Phase**: Continuous quality and performance monitoring

This ensures that the technical quality matches the project management rigor established by the BMAD framework.

## Contact and Support

For CI/CD pipeline issues:
- **Primary Contact**: @ossieirondi
- **Documentation**: This document and inline workflow comments
- **Monitoring**: GitHub Actions logs and quality metrics dashboard
- **Emergency**: Manual rollback procedures documented above

The pipeline is designed to be self-healing and provide clear feedback when issues occur. Most problems can be resolved by addressing the quality gate feedback and ensuring all tests pass locally before pushing changes.
