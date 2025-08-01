"""
Policy Middleware for FastAPI
Integrates Open Policy Agent for request validation and rate limiting
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import asyncio
from typing import Dict, Optional
import logging
import json
from datetime import datetime

from src.policy_engine.opa_client import OPAClient

logger = logging.getLogger(__name__)

class PolicyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces OPA policies for API access control
    Handles rate limiting, authentication, and authorization
    """
    
    def __init__(self, app, opa_client: Optional[OPAClient] = None):
        super().__init__(app)
        self.opa_client = opa_client or OPAClient()
        self.request_counts = {}  # In production, use Redis
        self.excluded_paths = {
            "/docs", "/redoc", "/openapi.json", "/health", 
            "/policy/health", "/metrics", "/favicon.ico"
        }
        
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip policy checks for excluded paths
        if self._should_skip_policy_check(request):
            return await call_next(request)
        
        try:
            # Extract user and request information
            user_data = await self._extract_user_data(request)
            request_data = await self._extract_request_data(request)
            
            # Check OPA health first
            if not await self._check_opa_health():
                logger.warning("OPA service unavailable, allowing request with basic validation")
                return await self._handle_opa_unavailable(request, call_next, user_data, request_data)
            
            # Evaluate access policies
            access_result = self.opa_client.check_api_access(user_data, request_data)
            
            if not access_result.get("allowed", False):
                return self._create_access_denied_response(access_result)
            
            # Track request for rate limiting
            self._track_request(request_data["client_ip"])
            
            # Add policy context to request
            request.state.policy_context = {
                "user": user_data,
                "access_result": access_result,
                "audit_required": access_result.get("audit_required", False)
            }
            
            # Process request
            response = await call_next(request)
            
            # Add policy headers to response
            self._add_policy_headers(response, access_result)
            
            # Log audit trail if required
            if access_result.get("audit_required"):
                await self._log_audit_trail(request, response, user_data, access_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Policy middleware error: {e}")
            # On error, allow request but log the issue
            return await call_next(request)
    
    def _should_skip_policy_check(self, request: Request) -> bool:
        """Check if request should skip policy validation"""
        path = request.url.path
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    async def _extract_user_data(self, request: Request) -> Dict:
        """Extract user authentication and role information"""
        auth_header = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")
        
        user_data = {
            "authenticated": False,
            "role": "anonymous",
            "api_key": api_key,
            "api_key_type": None,
            "verified_researcher": False,
            "verified_government": False,
            "government_level": None,
            "monitoring_permissions": False
        }
        
        # API Key authentication
        if api_key:
            user_data.update(await self._process_api_key(api_key))
        
        # JWT Token authentication
        elif auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            user_data.update(await self._process_jwt_token(token))
        
        return user_data
    
    async def _process_api_key(self, api_key: str) -> Dict:
        """Process API key and extract user information"""
        # In a real implementation, this would query the database
        # For now, using simple key-based logic
        
        if api_key.startswith("gov-"):
            return {
                "authenticated": True,
                "role": "government",
                "api_key_type": "government",
                "verified_government": True,
                "government_level": "federal" if "federal" in api_key else "provincial"
            }
        elif api_key.startswith("research-"):
            return {
                "authenticated": True,
                "role": "researcher",
                "api_key_type": "research",
                "verified_researcher": True
            }
        elif api_key.startswith("admin-"):
            return {
                "authenticated": True,
                "role": "admin",
                "api_key_type": "admin",
                "monitoring_permissions": True
            }
        elif api_key.startswith("journalist-"):
            return {
                "authenticated": True,
                "role": "journalist",
                "api_key_type": "journalist"
            }
        else:
            return {
                "authenticated": True,
                "role": "user",
                "api_key_type": "general"
            }
    
    async def _process_jwt_token(self, token: str) -> Dict:
        """Process JWT token and extract user information"""
        # In a real implementation, this would validate and decode the JWT
        # For now, returning basic authenticated user
        return {
            "authenticated": True,
            "role": "user"
        }
    
    async def _extract_request_data(self, request: Request) -> Dict:
        """Extract request information for policy evaluation"""
        client_ip = self._get_client_ip(request)
        
        return {
            "endpoint": request.url.path,
            "method": request.method,
            "client_ip": client_ip,
            "country_code": self._get_country_code(request),
            "requests_per_hour": self._get_request_count(client_ip),
            "export_size": await self._get_export_size(request),
            "user_agent": request.headers.get("User-Agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies"""
        # Check for X-Forwarded-For header (from load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return getattr(request.client, "host", "unknown")
    
    def _get_country_code(self, request: Request) -> str:
        """Get country code from request (could use GeoIP service)"""
        # In a real implementation, this would use a GeoIP service
        # For now, return Canada as default for Canadian government data
        return request.headers.get("X-Country-Code", "CA")
    
    async def _get_export_size(self, request: Request) -> int:
        """Extract export size from request parameters"""
        try:
            if request.method == "GET":
                limit = request.query_params.get("limit", "100")
                return int(limit)
            elif request.method == "POST":
                # For POST requests, we might need to read the body
                # This is a simplified approach
                return 1  # Default for POST requests
        except:
            return 0
        
        return 0
    
    def _get_request_count(self, client_ip: str) -> int:
        """Get current request count for IP (last hour)"""
        current_time = int(time.time())
        hour_ago = current_time - 3600
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Remove old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > hour_ago
        ]
        
        return len(self.request_counts[client_ip])
    
    def _track_request(self, client_ip: str):
        """Track a new request for rate limiting"""
        current_time = int(time.time())
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)
    
    async def _check_opa_health(self) -> bool:
        """Check if OPA service is available"""
        try:
            health = self.opa_client.health_check()
            return health.get("healthy", False)
        except:
            return False
    
    async def _handle_opa_unavailable(self, request: Request, call_next, user_data: Dict, request_data: Dict) -> Response:
        """Handle requests when OPA is unavailable - basic validation"""
        # Basic rate limiting without OPA
        requests_per_hour = request_data["requests_per_hour"]
        
        # Conservative limits when OPA is down
        if user_data["authenticated"]:
            rate_limit = 1000  # Authenticated users
        else:
            rate_limit = 100   # Anonymous users
        
        if requests_per_hour >= rate_limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Policy service temporarily unavailable, using reduced limits",
                    "retry_after": 3600
                }
            )
        
        # Track request and allow
        self._track_request(request_data["client_ip"])
        return await call_next(request)
    
    def _create_access_denied_response(self, access_result: Dict) -> JSONResponse:
        """Create appropriate access denied response"""
        rate_limit_status = access_result.get("rate_limit_status", {})
        
        if not rate_limit_status.get("allowed", True):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Request frequency exceeds allowed limits",
                    "limit": rate_limit_status.get("limit"),
                    "remaining": rate_limit_status.get("remaining", 0),
                    "retry_after": rate_limit_status.get("retry_after", 3600)
                }
            )
        else:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access denied",
                    "message": "Request violates access policies",
                    "restrictions": access_result.get("restrictions", [])
                }
            )
    
    def _add_policy_headers(self, response: Response, access_result: Dict):
        """Add policy-related headers to response"""
        rate_limit_status = access_result.get("rate_limit_status", {})
        
        if rate_limit_status:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_status.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_status.get("remaining", 0))
        
        restrictions = access_result.get("restrictions", [])
        if restrictions:
            response.headers["X-Policy-Restrictions"] = ",".join(restrictions)
        
        response.headers["X-Policy-Engine"] = "OPA"
        response.headers["X-Policy-Timestamp"] = datetime.utcnow().isoformat()
    
    async def _log_audit_trail(self, request: Request, response: Response, user_data: Dict, access_result: Dict):
        """Log audit trail for requests that require it"""
        audit_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": {
                "role": user_data.get("role"),
                "authenticated": user_data.get("authenticated"),
                "api_key_type": user_data.get("api_key_type")
            },
            "request": {
                "method": request.method,
                "endpoint": request.url.path,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", "")
            },
            "response": {
                "status_code": response.status_code
            },
            "policy_context": {
                "access_allowed": access_result.get("allowed"),
                "restrictions": access_result.get("restrictions", [])
            }
        }
        
        # Log to appropriate destination (file, database, external service)
        logger.info(f"AUDIT: {json.dumps(audit_log)}")

# Helper middleware class for easy integration
class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simplified rate limiting middleware when OPA is not available
    Can be used as a fallback or for development
    """
    
    def __init__(self, app, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = getattr(request.client, "host", "unknown")
        
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded", 
                    "message": f"Maximum {self.requests_per_hour} requests per hour"
                }
            )
        
        self._track_request(client_ip)
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        current_time = int(time.time())
        hour_ago = current_time - 3600
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > hour_ago
        ]
        
        return len(self.request_counts[client_ip]) >= self.requests_per_hour
    
    def _track_request(self, client_ip: str):
        current_time = int(time.time())
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(current_time)

# Factory function for easy setup
def create_policy_middleware(opa_url: str = "http://opa:8181") -> PolicyMiddleware:
    """Create policy middleware with OPA client"""
    opa_client = OPAClient(opa_url)
    return PolicyMiddleware(None, opa_client)