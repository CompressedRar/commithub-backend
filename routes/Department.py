from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Departments import Department_Service
from models.Tasks import Tasks_Service

department = Blueprint("department", __name__, url_prefix="/api/v1/department")

@department.route("/", methods = ["GET"])
@token_required()
def get_departments():
    return Department_Service.get_all_departments()

@department.route("/<id>", methods = ["GET"])
@token_required()
def get_department(id):
    return Department_Service.get_department(id)

@department.route("/tasks/<id>", methods = ["GET"])
@token_required()
def get_department_tasks(id):
    return Tasks_Service.get_tasks_by_department(id)

@department.route("/general/", methods = ["GET"])
@token_required()
def get_general_tasks():
    return Tasks_Service.get_all_general_tasks()

@department.route("/ipcr/<id>", methods = ["GET"])
@token_required()
def get_department_ipcr(id):
    return Department_Service.get_all_department_ipcr(id)

@department.route("/head/<dept_id>", methods = ["GET"])
@token_required()
def get_department_head(dept_id):
    return Department_Service.get_department_head(dept_id)

@department.route("/opcr/<dept_id>", methods = ["GET"])
@token_required()
def get_department_opcr(dept_id):
    return Department_Service.get_all_department_opcr(dept_id=dept_id)

@department.route("/tasks/<task_id>&<dept_id>", methods = ["POST"])
@token_required()
def assign_department_tasks(task_id, dept_id):
    return Tasks_Service.assign_department(task_id, dept_id)

@department.route("/assigned/<dept_id>&<task_id>", methods = ["GET"])
@token_required()
def get_assigned_users_tasks(dept_id, task_id):
    return Tasks_Service.get_assigned_users(dept_id, task_id)

@department.route("/assigned/general/<task_id>", methods = ["GET"])
@token_required()
def get_general_assigned_users_tasks(task_id):
    return Tasks_Service.get_general_assigned_users(task_id)


@department.route("/assigned/<user_id>&<task_id>&<assigned_quantity>", methods = ["POST"])
@token_required()
@log_action(action = "ASSIGN", target="TASK")
def assign_user_task(user_id, task_id, assigned_quantity):
    return Tasks_Service.assign_user(task_id, user_id, assigned_quantity)



@department.route("/unassign/<user_id>&<task_id>", methods = ["POST"])
@token_required()
@log_action(action = "UNASSIGN", target="TASK")
def unassign_user_task(user_id, task_id):
    return Tasks_Service.unassign_user(task_id, user_id)

@department.route("/members/<id>", methods = ["GET"])
@token_required()
def get_department_members(id):
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    print("this trigger")
    return Department_Service.get_members(id, offset, limit)


@department.route("/create", methods = ["POST"])
@token_required()
@log_action(action = "CREATE", target="DEPARTMENT")
def create_department():
    data = request.form
    return Department_Service.create_department(data)


@department.route("/remove/<id>", methods = ["POST"])
@token_required()
@log_action(action = "REMOVE", target="USER")
def remove_user_from_department(id):
    
    return Department_Service.remove_user_from_department(id)


@department.route("/update", methods = ["POST"])
@token_required()
@log_action(action = "UPDATE", target="DEPARTMENT")
def update_department():
    data = request.form
    return Department_Service.update_department(data["id"],data)
    

@department.route("/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "ARCHIVE", target="DEPARTMENT")
def archive_department(id):
    return Department_Service.archive_department(id)


@department.route("/remove/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "REMOVE", target="TASK")
def remove_task_department(id):
    return Tasks_Service.remove_task_from_dept(id)

