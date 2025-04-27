import time
from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta
import logging
from functools import wraps
from fastapi import HTTPException, Request
import redis
import os

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, secret_key: str, redis_url: Optional[str] = None):
        self.secret_key = secret_key
        self.redis = redis.from_url(redis_url) if redis_url else None
        self.token_blacklist = set()

    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate a JWT token."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> Dict:
        """Verify a JWT token."""
        try:
            if token in self.token_blacklist:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def revoke_token(self, token: str) -> None:
        """Revoke a token."""
        self.token_blacklist.add(token)

    def rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if a request should be rate limited."""
        if not self.redis:
            return False

        current = int(time.time())
        window_start = current - window

        # Clean up old entries
        self.redis.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        count = self.redis.zcard(key)
        
        if count >= limit:
            return True

        # Add new request
        self.redis.zadd(key, {str(current): current})
        self.redis.expire(key, window)
        return False

def require_auth(func):
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.split(' ')[1]
        security_manager = request.app.state.security_manager
        payload = security_manager.verify_token(token)
        request.state.user_id = payload['user_id']
        
        return await func(request, *args, **kwargs)
    return wrapper

def rate_limit_decorator(limit: int = 100, window: int = 3600):
    """Decorator to implement rate limiting."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            security_manager = request.app.state.security_manager
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}:{func.__name__}"
            
            if security_manager.rate_limit(key, limit, window):
                raise HTTPException(status_code=429, detail="Too many requests")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator 