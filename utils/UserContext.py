"""
User context utilities - Single source of truth for accessing user information
Provides methods to extract and work with user data from JWT tokens
"""
from flask import request
import jwt
import os


class UserContext:
    """Utility class for accessing current user information from JWT token"""
    
    @staticmethod
    def get_jwt_secret():
        """Get JWT secret key from environment or config"""
        return os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    
    @staticmethod
    def get_current_user_payload():
        """
        Get the current user's JWT payload
        Returns the decoded payload if already decoded by decorator
        """
        if hasattr(request, 'user_payload'):
            return request.user_payload
        return None
    
    @staticmethod
    def get_current_user_id():
        """Get current user ID from JWT token"""
        payload = UserContext.get_current_user_payload()
        return payload.get('id') if payload else None
    
    @staticmethod
    def get_current_user_role():
        """Get current user role from JWT token"""
        payload = UserContext.get_current_user_payload()
        return payload.get('role') if payload else None
    
    @staticmethod
    def get_current_user_email():
        """Get current user email from JWT token"""
        payload = UserContext.get_current_user_payload()
        return payload.get('email') if payload else None
    
    @staticmethod
    def get_current_user_name():
        """Get current user full name from JWT token"""
        payload = UserContext.get_current_user_payload()
        if payload:
            first_name = payload.get('first_name', '')
            last_name = payload.get('last_name', '')
            return f"{first_name} {last_name}".strip()
        return None
    
    @staticmethod
    def get_current_user_department():
        """Get current user department from JWT token"""
        payload = UserContext.get_current_user_payload()
        if payload and 'department' in payload:
            return payload['department']
        return None
    
    @staticmethod
    def get_current_user_department_id():
        """Get current user department ID from JWT token"""
        dept = UserContext.get_current_user_department()
        return dept.get('id') if dept and isinstance(dept, dict) else None
    
    @staticmethod
    def get_current_user_department_name():
        """Get current user department name from JWT token"""
        dept = UserContext.get_current_user_department()
        return dept.get('name') if dept and isinstance(dept, dict) else None
    
    @staticmethod
    def decode_token(token):
        """
        Decode JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Decoded payload or None if invalid
        """
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            payload = jwt.decode(
                token,
                UserContext.get_jwt_secret(),
                algorithms=['HS256']
            )
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    @staticmethod
    def get_client_ip():
        """Get client IP address from request"""
        return request.remote_addr
    
    @staticmethod
    def get_user_agent():
        """Get user agent from request"""
        return request.headers.get('User-Agent')
