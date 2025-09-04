# Performance Optimization

## Caching Strategy
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1)
def get_cached_kpis(cache_key: str) -> Dict:
    """Cache KPIs for 5 minutes to reduce API calls."""
    return get_all_kpis()

def get_current_kpis() -> Dict:
    """Get KPIs with 5-minute cache."""
    cache_key = datetime.now().strftime('%Y%m%d%H%M')[:-1]  # 5-min blocks
    return get_cached_kpis(cache_key)
```

## API Rate Limiting
- Google Sheets API: 100 requests per 100 seconds
- Our usage: ~10 requests per dashboard load
- Safety margin: 10x under limit
