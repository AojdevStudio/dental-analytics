# Configuration Management

## Credentials Storage
```
config/
└── credentials.json    # Google service account key
    {
      "type": "service_account",
      "project_id": "dental-analytics",
      "private_key_id": "...",
      "private_key": "...",
      "client_email": "dental-dashboard@project.iam.gserviceaccount.com"
    }
```

## Environment Configuration
```python
