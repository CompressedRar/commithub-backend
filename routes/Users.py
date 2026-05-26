from flask import Blueprint, render_template, jsonify, request
from app import db, limiter
from utils.decorators import log_action,token_required
from models.Notification import Notification, Notification_Service
from models.User import Profile
from services.pcr_service import PCR_Service
from services.User.users_service import Users
users = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users.route("/", methods = ["GET"])
@token_required()
def get_users():
    return Users.get_all_users()

@users.route("/pres-exists", methods = ["GET"])
@token_required()
def does_president_exists():
    return Users.does_president_exists()

@users.route("/admin-exists", methods = ["GET"])
@token_required()
def does_admin_exists():
    return Users.does_admin_exists()

@users.route("/<id>", methods = ["GET"])
@token_required()
def get_user(id):
    return Users.get_user(id)

@users.route("/notification/<id>", methods = ["GET"])
@token_required()
def get_user_notifications(id):
    return Notification_Service.get_user_notification(id)

@users.route("/", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="USER")
def update_user():
    data = request.form
    req = request
    
    print("UPDATE USRE DATA",data)
    return Users.update_user(data["id"], data, req)

@users.route("/settings/<user_id>", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="USER")
def update_user_settings(user_id):
    """Update user account settings (first_name, last_name, middle_name, position, department)"""
    data = request.get_json()
    return Users.update_user_settings(user_id, data)

@users.route("/reset-password/<user_id>", methods = ["PATCH"])
@limiter.limit("3 per hour")
def reset_password_user(user_id):
    
    return Users.reset_password(user_id)

@users.route("/change-password/<user_id>", methods = ["PATCH"])
@token_required()
def change_password_user(user_id):
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("password")
    print("CHANGING PASS",user_id, new_password)
    return Users.change_password(user_id, new_password, current_password)


@users.route("/profile/<profile_id>", methods = ["GET"])
def get_all_accounts_by_profile(profile_id):

    return Users.get_all_accountsby_profile(profile_id)

@users.route("/switch/<profile_id>&<user_id>", methods = ["GET"])
@token_required()
def switch_user(profile_id, user_id ):
    return Users.switch_account(profile_id, user_id)


@users.route("/forgot-change-password/<user_id>", methods = ["PATCH"])
def forgot_change_password_user(user_id):
    new_pass = request.json.get("password")
    print("CHANGING PASS",user_id, new_pass)
    return Users.change_password(user_id, new_pass)

@users.route("/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "DEACTIVATE", target="USER")
def archive_user(id):
    return Users.archive_user(id)

@users.route("/tasks/<id>", methods = ["GET"])
@token_required()
def get_user_tasks(id):
    
    return Users.get_user_assigned_tasks(id)

@users.route("/assigned/<user_id>", methods = ["GET"])
@token_required()
def get_assigned_tasks(user_id):
    
    return Users.get_user_assigned_tasks(user_id)

@users.route("/tasks/<user_id>", methods = ["POST"])
@token_required()
def generate_user_tasks(user_id):
    
    data = request.get_json()
    id_array = data.get("task_ids", [])
    print(id_array)
    return PCR_Service.generate_IPCR(user_id, id_array)

@users.route("/head/<user_id>", methods = ["POST"])
@token_required(allowed_roles=["administrator", "president"])
def assign_department_head(user_id):
    
    data = request.args
    dept_id = data.get("dept_id")
    return Users.assign_department_head(user_id, dept_id)

@users.route("/head/<user_id>", methods = ["DELETE"])
@token_required()
def remove_department_head(user_id):
    return Users.remove_department_head(user_id)
    
@users.route("/notifications/", methods = ["PATCH"])
@token_required()
def read_notifications():

    data = request.get_json()
    id_array = data.get("id", [])
    return Notification_Service.mark_as_read(id_array)
    


@users.route("/<id>", methods = ["POST"])
@token_required()
@log_action(action = "REACTIVATE", target="USER")
def unarchive_user(id):
    
    return Users.unarchive_user(id)


# Profile Routes
@users.route("/profiles/<profile_id>", methods = ["GET"])
@token_required()
def get_profile(profile_id):
    """Get profile information"""
    return Users.get_profile(profile_id)

@users.route("/profiles/<profile_id>", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="PROFILE")
def update_profile(profile_id):
    """Update profile settings (recovery_email, two_factor_enabled)"""
    data = request.get_json()
    return Users.update_profile(profile_id, data)

@users.route("/profiles/<profile_id>/picture", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="PROFILE")
def update_profile_picture(profile_id):
    """Update profile picture"""
    profile_pic = request.files.get("profile_picture")
    if not profile_pic:
        return jsonify(error="No profile picture provided"), 400
    return Users.update_profile_picture(profile_id, profile_pic)


"""
gawin yung override ng ratings bukas

"""