from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.User import Users, Notification, Notification_Service
from models.PCR import PCR_Service
users = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users.route("/", methods = ["GET"])
def get_users():
    return Users.get_all_users()

@users.route("/pres-exists", methods = ["GET"])
def does_president_exists():
    return Users.does_president_exists()

@users.route("/<id>", methods = ["GET"])
def get_user(id):
    return Users.get_user(id)

@users.route("/notification/<id>", methods = ["GET"])
def get_user_notifications(id):
    return Notification_Service.get_user_notification(id)


@users.route("/", methods = ["PATCH"])
@log_action(action = "UPDATE", target="USER")
def update_user():
    data = request.form
    req = request
    return Users.update_user(data["id"], data, req)

@users.route("/reset-password/<user_id>", methods = ["PATCH"])
def reset_password_user(user_id):
    
    return Users.reset_password(user_id)

@users.route("/change-password/<user_id>", methods = ["PATCH"])
def change_password_user(user_id):
    new_pass = request.json.get("password")
    return Users.change_password(user_id, new_pass)

@users.route("/<id>", methods = ["DELETE"])
@log_action(action = "DEACTIVATE", target="USER")
def archive_user(id):
    
    return Users.archive_user(id)

@users.route("/tasks/<id>", methods = ["GET"])
def get_user_tasks(id):
    
    return Users.get_user_assigned_tasks(id)

@users.route("/assigned/<user_id>", methods = ["GET"])
def get_assigned_tasks(user_id):
    
    return Users.get_user_assigned_tasks(user_id)

@users.route("/tasks/<user_id>", methods = ["POST"])
def generate_user_tasks(user_id):
    
    data = request.get_json()
    id_array = data.get("task_ids", [])
    print(id_array)
    return PCR_Service.generate_IPCR(user_id, id_array)

@users.route("/head/<user_id>", methods = ["POST"])
def assign_department_head(user_id):
    
    data = request.args
    dept_id = data.get("dept_id")
    return Users.assign_department_head(user_id, dept_id)

@users.route("/head/<user_id>", methods = ["DELETE"])
def remove_department_head(user_id):
    return Users.remove_department_head(user_id)
    
@users.route("/notifications/", methods = ["PATCH"])
def read_notifications():

    data = request.get_json()
    id_array = data.get("id", [])
    return Notification_Service.mark_as_read(id_array)
    


@users.route("/<id>", methods = ["POST"])
@log_action(action = "REACTIVATE", target="USER")
def unarchive_user(id):
    
    return Users.unarchive_user(id)



