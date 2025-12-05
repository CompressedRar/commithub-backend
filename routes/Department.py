from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Departments import Department_Service
from models.Tasks import Tasks_Service

department = Blueprint("department", __name__, url_prefix="/api/v1/department")

@department.route("/", methods = ["GET"])
def get_departments():
    return Department_Service.get_all_departments()

@department.route("/<id>", methods = ["GET"])
def get_department(id):
    return Department_Service.get_department(id)

@department.route("/tasks/<id>", methods = ["GET"])
def get_department_tasks(id):
    return Tasks_Service.get_tasks_by_department(id)

@department.route("/general/", methods = ["GET"])
def get_general_tasks():
    return Tasks_Service.get_all_general_tasks()

@department.route("/ipcr/<id>", methods = ["GET"])
def get_department_ipcr(id):
    return Department_Service.get_all_department_ipcr(id)

@department.route("/head/<dept_id>", methods = ["GET"])
def get_department_head(dept_id):
    return Department_Service.get_department_head(dept_id)

@department.route("/opcr/<dept_id>", methods = ["GET"])
def get_department_opcr(dept_id):
    return Department_Service.get_all_department_opcr(dept_id=dept_id)

@department.route("/tasks/<task_id>&<dept_id>", methods = ["POST"])
def assign_department_tasks(task_id, dept_id):
    return Tasks_Service.assign_department(task_id, dept_id)

@department.route("/assigned/<dept_id>&<task_id>", methods = ["GET"])
def get_assigned_users_tasks(dept_id, task_id):
    return Tasks_Service.get_assigned_users(dept_id, task_id)

@department.route("/assigned/general/<task_id>", methods = ["GET"])
def get_general_assigned_users_tasks(task_id):
    return Tasks_Service.get_general_assigned_users(task_id)

@log_action(action = "ASSIGN", target="TASK")
@department.route("/assigned/<user_id>&<task_id>&<assigned_quantity>", methods = ["POST"])
def assign_user_task(user_id, task_id, assigned_quantity):
    return Tasks_Service.assign_user(task_id, user_id, assigned_quantity)


@log_action(action = "UNASSIGN", target="TASK")
@department.route("/unassign/<user_id>&<task_id>", methods = ["POST"])
def unassign_user_task(user_id, task_id):
    return Tasks_Service.unassign_user(task_id, user_id)

@department.route("/members/<id>", methods = ["GET"])
def get_department_members(id):
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    print("this trigger")
    return Department_Service.get_members(id, offset, limit)

@log_action(action = "CREATE", target="DEPARTMENT")
@department.route("/create", methods = ["POST"])
def create_department():
    data = request.form
    return Department_Service.create_department(data)

@log_action(action = "REMOVE", target="USER")
@department.route("/remove/<id>", methods = ["POST"])
def remove_user_from_department(id):
    
    return Department_Service.remove_user_from_department(id)

@log_action(action = "UPDATE", target="DEPARTMENT")
@department.route("/update", methods = ["POST"])
def update_department():
    data = request.form
    return Department_Service.update_department(data["id"],data)
    
@log_action(action = "ARCHIVE", target="DEPARTMENT")
@department.route("/<id>", methods = ["DELETE"])
def archive_department(id):
    return Department_Service.archive_department(id)

@log_action(action = "REMOVE", target="TASK")
@department.route("/remove/<id>", methods = ["DELETE"])
def remove_task_department(id):
    return Tasks_Service.remove_task_from_dept(id)

