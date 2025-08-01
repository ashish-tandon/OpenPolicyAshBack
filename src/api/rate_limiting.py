"""
API Rate Limiting and Authentication for OpenPolicy Database

Implements comprehensive rate limiting, API key authentication, and security features.
"""

import os
import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import jwt
from sqlalchemy.orm import Session

# Redis connection for rate limiting
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Security configuration
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "1000"))  # requests per hour
RATE_LIMIT_ENABLED = os.getenv("API_RATE_LIMIT_ENABLED", "true").lower() == "true"
API_KEY_REQUIRED = os.getenv("API_KEY_REQUIRED", "false").lower() == "true"

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int = 3600) -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (IP, user ID, API key)
            limit: Number of requests allowed
            window: Time window in seconds (default: 1 hour)
        
        Returns:
            Dict with allowed status and remaining requests
        """
        now = int(time.time())
        pipe = self.redis.pipeline()
        
        # Sliding window rate limiting
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        
        results = pipe.execute()
        current_requests = results[1]
        
        return {
            "allowed": current_requests < limit,
            "current": current_requests,
            "limit": limit,
            "reset_time": now + window,
            "remaining": max(0, limit - current_requests - 1)
        }

rate_limiter = RateLimiter(redis_client)

def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers"""
    # Check for forwarded headers (behind proxy)
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    elif "x-real-ip" in request.headers:
        return request.headers["x-real-ip"]
    else:
        return request.client.host

async def rate_limit_middleware(request: Request):
    """Rate limiting middleware"""
    if not RATE_LIMIT_ENABLED:
        return
    
    # Get client identifier
    client_ip = get_client_ip(request)
    
    # Check API key if provided for higher limits
    api_key = request.headers.get("x-api-key")
    if api_key:
        # API key users get higher limits
        rate_key = f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()}"
        limit = API_RATE_LIMIT * 10  # 10x higher limit for API key users
    else:
        rate_key = f"ip:{client_ip}"
        limit = API_RATE_LIMIT
    
    # Check rate limit
    result = rate_limiter.is_allowed(rate_key, limit)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": result["limit"],
                "current": result["current"],
                "reset_time": result["reset_time"]
            },
            headers={
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": str(result["remaining"]),
                "X-RateLimit-Reset": str(result["reset_time"]),
                "Retry-After": str(3600)  # 1 hour
            }
        )

def verify_api_key(api_key: str) -> bool:
    """Verify API key (implement your own logic)"""
    # For demo purposes, accept any key that starts with 'op_'
    # In production, store API keys in database with user associations
    valid_keys = [
        "op_demo_key_12345",
        "op_public_access",
        os.getenv("MASTER_API_KEY", "op_master_key")
    ]
    return api_key in valid_keys

def create_jwt_token(user_id: str, permissions: list = None) -> str:
    """Create JWT token for authenticated users"""
    payload = {
        "user_id": user_id,
        "permissions": permissions or ["read"],
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    # Check if authentication is required
    if not API_KEY_REQUIRED:
        return {"user_id": "anonymous", "permissions": ["read"]}
    
    # Check API key in headers
    api_key = request.headers.get("x-api-key")
    if api_key and verify_api_key(api_key):
        return {
            "user_id": f"api_key_user_{hashlib.sha256(api_key.encode()).hexdigest()[:8]}",
            "permissions": ["read", "write"],
            "auth_method": "api_key"
        }
    
    # Check JWT token
    if credentials:
        user_data = verify_jwt_token(credentials.credentials)
        return {
            **user_data,
            "auth_method": "jwt"
        }
    
    # No valid authentication found
    if API_KEY_REQUIRED:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide API key in X-API-Key header or JWT token in Authorization header."
        )
    
    return None

# API key authentication endpoint
async def authenticate_api_key(api_key: str) -> Dict[str, str]:
    """Authenticate with API key and return JWT token"""
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user_id = f"api_user_{hashlib.sha256(api_key.encode()).hexdigest()[:8]}"
    token = create_jwt_token(user_id, ["read", "write"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours
        "user_id": user_id
    }

# Permission checking
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(user: Dict[str, Any] = Depends(get_current_user)):
        if user and permission in user.get("permissions", []):
            return user
        raise HTTPException(
            status_code=403,
            detail=f"Permission '{permission}' required"
        )
    return decorator

# Usage tracking
async def track_api_usage(request: Request, user: Dict[str, Any] = None):
    """Track API usage for analytics"""
    if not user:
        return
    
    usage_key = f"usage:{user['user_id']}:{datetime.now().strftime('%Y-%m-%d-%H')}"
    endpoint = request.url.path
    method = request.method
    
    # Increment usage counter
    redis_client.hincrby(usage_key, f"{method}:{endpoint}", 1)
    redis_client.expire(usage_key, 86400 * 30)  # Keep for 30 days

# Security headers middleware
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response