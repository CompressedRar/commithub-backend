"""
Authentication and authorization decorators
Uses centralized UserContext for token management
"""
from functools import wraps
from flask import request, jsonify
from utils.UserContext import UserContext
from utils.Settings import AppSettings


def token_required(allowed_roles=None):
    """
    Decorator to validate JWT tokens and check roles
    
    Args:
        allowed_roles: List of allowed roles, e.g., ['administrator', 'head_of_department']
    
    Raises:
        401: If token is missing or invalid
        403: If user role is not in allowed_roles
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                return jsonify({"error": "Authorization header missing"}), 401
            
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Invalid authorization header format"}), 401
            
            token = auth_header.split(" ", 1)[1].strip()
            
            if not token:
                return jsonify({"error": "Token missing"}), 401
            
            # Decode token using centralized UserContext
            payload = UserContext.decode_token(auth_header)
            
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            user_id = payload.get("id")
            role = payload.get("role")
            
            if not user_id or not role:
                return jsonify({"error": "Invalid token payload"}), 401
            
            # Store payload in request for downstream handlers
            request.user_payload = payload
            
            # Check role authorization
            if allowed_roles and role not in allowed_roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        
        return wrapper
    return decorator


def log_action(action, target):
    """
    Decorator to log user actions for audit trail
    
    Args:
        action: Action type (CREATE, READ, UPDATE, DELETE, etc.)
        target: Target resource (USER, PCR, TASK, etc.)
    
    Usage:
        @log_action(action="CREATE", target="PCR")
        def create_pcr():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            
            try:
                # Get current user information from centralized UserContext
                payload = UserContext.get_current_user_payload()
                
                if not payload:
                    return response
                
                user_id = payload.get("id")
                full_name = UserContext.get_current_user_name()
                department = UserContext.get_current_user_department_name()
                
                # Get request metadata
                ip_address = UserContext.get_client_ip()
                user_agent = UserContext.get_user_agent()
                
                # Import here to avoid circular imports
                from models.Logs import Log_Service
                
                # Log the action asynchronously if possible
                try:
                    Log_Service.add_logs(
                        user_id=user_id,
                        full_name=full_name,
                        department=department,
                        action=action,
                        target=target,
                        ip=ip_address,
                        agent=user_agent
                    )
                except Exception as log_error:
                    # Don't fail the request if logging fails
                    if AppSettings.is_development():
                        print(f"Warning: Failed to log action {action}/{target}: {log_error}")
            
            except Exception as e:
                # Don't fail the request if anything goes wrong with logging
                if AppSettings.is_development():
                    print(f"Warning: Error in log_action decorator: {e}")
            
            return response
        
        return wrapper
    return decorator


def admin_required(f):
    """Decorator to require administrator role"""
    return token_required(allowed_roles=['administrator'])(f)


def role_required(*roles):
    """
    Flexible decorator to require any of specified roles
    
    Usage:
        @role_required('administrator', 'head_of_department')
        def some_endpoint():
            ...
    """
    return token_required(allowed_roles=list(roles))


def optional_tokens(f):
    """
    Decorator to optionally validate token if present
    If Authorization header is present, validates it; otherwise allows anonymous access
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Invalid authorization header format"}), 401
            
            token = auth_header.split(" ", 1)[1].strip()
            
            if not token:
                return jsonify({"error": "Token missing"}), 401
            
            payload = UserContext.decode_token(auth_header)
            
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            request.user_payload = payload
        
        return f(*args, **kwargs)
    
    return wrapper
