from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import bleach
import html
import json
import re
from typing import Any, Dict

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_tags: list = [], allowed_attributes: dict = {}):
        super().__init__(app)
        # Default: strip all HTML tags
        self.allowed_tags = allowed_tags or []
        self.allowed_attributes = allowed_attributes or {}

    async def dispatch(self, request: Request, call_next):
        # Add security headers to response
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

def sanitize_string(text: str) -> str:
    """Sanitize string input to prevent XSS attacks"""
    if not isinstance(text, str):
        return text

    # Remove HTML tags and attributes
    cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)

    # HTML escape any remaining content
    escaped = html.escape(cleaned)

    # Remove common XSS patterns
    xss_patterns = [
        r'javascript:',
        r'on\w+\s*=',
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
    ]

    for pattern in xss_patterns:
        escaped = re.sub(pattern, '', escaped, flags=re.IGNORECASE | re.DOTALL)

    return escaped

def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize dictionary values"""
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(item) if isinstance(item, str)
                else sanitize_dict(item) if isinstance(item, dict)
                else item for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized

def sanitize_input(data: Any) -> Any:
    """Main sanitization function"""
    if isinstance(data, str):
        return sanitize_string(data)
    elif isinstance(data, dict):
        return sanitize_dict(data)
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
        return data
