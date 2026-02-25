import jwt
from flask import request, jsonify
from models.AdminConfirmation import AdminConfirmation

# central role -> permissions mapping
ROLES_PERMISSIONS = {
    "administrator": [
        "settings.view",
        "settings.edit",
        "users.manage",
        "notifications.manage",
        "ipcr.view",
        "departments.manage"
    ],
    "president": [
        "settings.view",
        "settings.edit",
        "users.manage",
        "notifications.manage",
        "ipcr.view",
        "departments.manage"
    ],
    "head": [
        "departments.manage",
        "settings.view",
        "ipcr.view",
    ],
    "faculty": [
        "settings.view",
        "ipcr.view",
        "notifications.manage",
    ],
}


def get_permissions_for_role(role: str):
    return ROLES_PERMISSIONS.get(role, [])


def has_permission(role: str, permission: str) -> bool:
    return permission in get_permissions_for_role(role)


# decorator factory
def permissions_required(permission, require_admin_confirm=False):
    def decorator(f):
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Authorization header missing"}), 401

            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, "priscilla", algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token has expired"}), 401
            except Exception:
                return jsonify({"error": "Invalid token"}), 401

            role = payload.get("role")
            user_id = payload.get("id")

            if not role or not user_id:
                return jsonify({"error": "Invalid token payload"}), 401

            if not has_permission(role, permission):
                return jsonify({"error": "Forbidden"}), 403

            if require_admin_confirm:
                # Accept confirmation token via header X-Admin-Confirmation or JSON body field confirmation_token
                conf_token = request.headers.get("X-Admin-Confirmation")
                if not conf_token:
                    body = request.get_json(silent=True) or {}
                    conf_token = body.get("confirmation_token")

                if not conf_token:
                    return jsonify({"error": "Confirmation token is required"}), 401

                if not AdminConfirmation.verify(user_id, conf_token):
                    return jsonify({"error": "Invalid or expired confirmation token"}), 401

            # expose payload for downstream handlers
            request.user_payload = payload

            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
