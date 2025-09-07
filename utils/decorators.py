from functools import wraps
from flask import request, jsonify
import jwt
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
