from functools import wraps
from flask import request, jsonify
import jwt
from models.Logs import Logs


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
            
            try:
                data = jwt.decode(token, "priscilla", algorithms=["HS256"])
                current_user_id = data["user_id"]
                current_user_full_name = data["first_name"] + " " + data["last_name"]
                department = data["department"]
                
                Logs.add_logs(current_user_full_name, department, action, target)
                print("Log Recorded")
                
                
            except:
                print("Logging Failed")
            return response
        return wrapper
    return decorator
