import time
from typing import Dict, Any, Optional
import json
import hashlib

class APICache:
    def __init__(self, default_ttl: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key from endpoint and parameters"""
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached data if valid"""
        key = self._generate_key(endpoint, params)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() < entry['expires']:
                return entry['data']
            else:
                del self.cache[key]
        return None
    
    def set(self, endpoint: str, params: Dict, data: Any, ttl: Optional[int] = None) -> None:
        """Cache data with TTL"""
        key = self._generate_key(endpoint, params)
        expires = time.time() + (ttl or self.default_ttl)
        self.cache[key] = {
            'data': data,
            'expires': expires,
            'timestamp': time.time()
        }
    
    def clear_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [k for k, v in self.cache.items() if current_time >= v['expires']]
        for key in expired_keys:
            del self.cache[key]

# Global cache instance
api_cache = APICache(default_ttl=60)