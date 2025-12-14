from functools import wraps
from flask import request, jsonify
import jwt
from models.Logs import Log_Service


def token_required(allowed_roles=None):
    """ lagay mo sa array yung roles"""

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

            try:
                payload = jwt.decode(
                    token,
                    "priscilla",
                    algorithms=["HS256"]
                )

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            user_id = payload.get("id")
            role = payload.get("role")

            if not user_id or not role:
                return jsonify({"error": "Invalid token payload"}), 401

            if allowed_roles and role not in allowed_roles:
                return jsonify({"error": "Forbidden"}), 403


            return f(*args, **kwargs)

        return wrapper
    return decorator

def log_action(action, target):
    def decorator(func):
        @wraps(func)

        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            token = request.headers.get("Authorization")
            
            if not token:
                return jsonify({"error": "Token is missing"}), 401
            
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            
            try:
                data = jwt.decode(token, "priscilla", algorithms=["HS256"])
                current_user_id = data["id"]
                current_user_full_name = data["first_name"] + " " + data["last_name"]
                department = data["department"]["name"]

                ip_address = request.remote_addr
                user_agent = request.headers.get("User-Agent")
                
                res = Log_Service.add_logs(current_user_id,current_user_full_name, department, action, target, ip=ip_address, agent=user_agent)
                print("Log Recorded: ", res)
                
                
            except Exception as e:
                print("Logging Failed", e)
            return response
        return wrapper
    return decorator

def log_enter(action):
    def decorator(func):
        @wraps(func)

        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            
            
            try:
                ip_address = request.remote_addr
                user_agent = request.headers.get("User-Agent")
                
                res = Log_Service.add_logs("0","UNKNOWN", "UNKNOWN", action, "UNKNOWN", ip=ip_address, agent=user_agent)
                print("Log Recorded: ", res)
                
                
            except Exception as e:
                print("Logging Failed", e)
            return response
        return wrapper
    return decorator
