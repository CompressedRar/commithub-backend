from functools import wraps
from flask import request, jsonify
import jwt
from models.Logs import Log_Service


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            data = jwt.decode(token, "priscilla", algorithms=["HS256"])
            current_user_id = data["user_id"]
        except:
            return jsonify({"error": "Token is invalid"}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated



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
                print("token:", data)
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
