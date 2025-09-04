# Module Dependencies

```yaml
backend/:
  __init__.py:
    - Empty file for module initialization
    
  sheets_reader.py:
    external:
      - google-auth >= 2.23
      - google-api-python-client >= 2.103
      - pandas >= 2.1
    internal:
      - None (standalone module)
    
  metrics.py:
    external:
      - pandas >= 2.1
    internal:
      - sheets_reader (for get_all_kpis only)
```
