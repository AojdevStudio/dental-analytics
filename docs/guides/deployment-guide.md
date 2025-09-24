# Deployment Guide

## Overview

This guide covers deployment procedures for the Dental Analytics Dashboard v2.1.0.

## Prerequisites

### System Requirements
- Python 3.10+ (tested with 3.11)
- 2GB RAM minimum
- 1GB disk space
- Network access to Google Sheets API

### Required Credentials
- Google Cloud service account JSON
- Access to target Google Sheets
- Appropriate IAM permissions

## Local Development Deployment

### 1. Clone Repository
```bash
git clone https://github.com/your-org/dental-analytics.git
cd dental-analytics
```

### 2. Install Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 3. Configure Credentials
```bash
# Place service account JSON
cp /path/to/service-account.json config/credentials.json

# Set permissions
chmod 600 config/credentials.json
```

### 4. Configure Sheets Access
```yaml
# Edit config/sheets.yml
sheets:
  baytown_eod:
    spreadsheet_id: "YOUR_SHEET_ID"
    range: "EOD - Baytown Billing!A:N"
```

### 5. Start Application
```bash
uv run streamlit run apps/frontend/app.py
```

Access at: http://localhost:8501

## Production Deployment

### Option 1: Streamlit Cloud

#### Setup
1. Fork repository to your GitHub account
2. Sign in to [share.streamlit.io](https://share.streamlit.io)
3. Create new app from repository

#### Configuration
```toml
# .streamlit/secrets.toml
[google]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n..."
client_email = "service-account@project.iam.gserviceaccount.com"
```

#### Environment Variables
```bash
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY apps/ apps/
COPY config/ config/
COPY .streamlit/ .streamlit/

# Run application
EXPOSE 8501
CMD ["streamlit", "run", "apps/frontend/app.py", "--server.address=0.0.0.0"]
```

#### Build and Run
```bash
# Build image
docker build -t dental-analytics:v2.1.0 .

# Run container
docker run -p 8501:8501 \
  -v $(pwd)/config:/app/config:ro \
  dental-analytics:v2.1.0
```

### Option 3: Cloud Platform Deployment

#### Google Cloud Run
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/dental-analytics

# Deploy to Cloud Run
gcloud run deploy dental-analytics \
  --image gcr.io/PROJECT_ID/dental-analytics \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501
```

#### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag dental-analytics:v2.1.0 $ECR_URI/dental-analytics:v2.1.0
docker push $ECR_URI/dental-analytics:v2.1.0

# Create task definition and service
aws ecs create-service \
  --cluster dental-cluster \
  --service-name dental-analytics \
  --task-definition dental-analytics-task:1
```

## Security Considerations

### Credential Management
- Never commit credentials to repository
- Use secret management services (AWS Secrets Manager, GCP Secret Manager)
- Rotate service account keys regularly
- Limit service account permissions to read-only

### Network Security
- Use HTTPS in production
- Implement authentication (OAuth, SAML)
- Configure CORS appropriately
- Enable rate limiting

### Example Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name analytics.dental-practice.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Logging

### Health Check Endpoint
```python
# Add to app.py
@st.cache_data(ttl=60)
def health_check():
    try:
        provider = build_sheets_provider()
        return {"status": "healthy", "version": "2.1.0"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Logging Configuration
```python
# config/logging.yaml
version: 1
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/dental-analytics.log
    maxBytes: 10485760
    backupCount: 5
    formatter: detailed

formatters:
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

root:
  level: INFO
  handlers: [file]
```

### Monitoring Tools
- Prometheus metrics endpoint
- Grafana dashboards
- CloudWatch/Stackdriver integration
- Error tracking (Sentry)

## Backup and Recovery

### Data Backup
- Google Sheets are automatically backed up
- Export KPI history regularly:
```bash
uv run python scripts/export_historical_data.py --days 365
```

### Configuration Backup
```bash
# Backup configurations
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Exclude credentials
tar --exclude='credentials.json' -czf config-backup.tar.gz config/
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Request had insufficient authentication scopes
```
**Solution**: Verify service account has Sheets API access

#### 2. Data Not Loading
```
Error: Data Unavailable
```
**Solution**: Check sheet names and ranges in config/sheets.yml

#### 3. Slow Performance
**Solution**:
- Reduce historical data range
- Implement caching
- Optimize queries

#### 4. Memory Issues
**Solution**:
- Increase container memory
- Implement data pagination
- Use data sampling for large datasets

## Rollback Procedures

### Version Rollback
```bash
# Tag current version
git tag -a v2.1.0-backup -m "Backup before rollback"

# Rollback to previous version
git checkout v2.0.0
docker build -t dental-analytics:v2.0.0 .
docker run -p 8501:8501 dental-analytics:v2.0.0
```

### Database Rollback
Not applicable - data sourced from Google Sheets

## Performance Optimization

### Caching Strategy
```python
# Implement in app.py
@st.cache_data(ttl=300)  # 5-minute cache
def get_cached_kpis(location):
    return get_all_kpis(location)
```

### Query Optimization
- Limit date ranges to necessary periods
- Use column subset in sheet ranges
- Implement incremental data loading

## Support

### Logs Location
- Local: `logs/dental-analytics.log`
- Docker: `/app/logs/`
- Cloud Run: Cloud Logging console

### Debug Mode
```bash
# Enable debug logging
STREAMLIT_LOGGER_LEVEL=debug uv run streamlit run apps/frontend/app.py
```

### Contact
- Technical Support: dev-team@dental-practice.com
- Documentation: https://docs.dental-analytics.com
