from flask import Blueprint, render_template, jsonify, request, json
from app import db

from services.tasks_service import Tasks_Service
from utils.decorators import log_action, token_required
task = Blueprint("task", __name__, url_prefix="/api/v1/task")

SUB_TASK_ALLOWED_FIELDS = {
    "target_acc",
    "target_time",
    "target_mod",
    "actual_acc",
    "actual_time",
    "actual_mod",
    "actual_deadline",
    "target_deadline",
    "quantity",
    "efficiency",
    "timeliness",
    "average",
}

ASSIGNED_DEPT_ALLOWED_FIELDS = {
    "quantity",
    "efficiency",
    "timeliness",
}

@task.route("/count", methods = ["GET"])
@token_required()
def get_tasks_count():
    return Tasks_Service.get_all_tasks_count()

@task.route("/", methods = ["GET"])
@token_required()
def get_tasks():
    return Tasks_Service.get_main_tasks()

@task.route("/general", methods = ["GET"])
@token_required()
def get_general_tasks():
    return Tasks_Service.get_general_tasks()


@task.route("/<id>", methods = ["GET"])
@token_required()
def get_task(id):
    return Tasks_Service.get_main_task(id)

@task.route("/<id>", methods = ["DELETE"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action = "ARCHIVE", target="TASK")

def archive_task(id):
    return Tasks_Service.archive_task(id)

@task.route("/", methods = ["POST"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action = "CREATE", target="TASK")

def create_main_task():
    data = request.form
    print(data)
    return Tasks_Service.create_main_task(data)

@task.route("/", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="TASK")
def update_main_task():
    data = request.form
    return Tasks_Service.update_task_info(data)

@task.route("/sub_task/<sub_task_id>", methods=["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="TASK")
def update_sub_task_field(sub_task_id):
    field = request.args.get("field")
    value = request.args.get("value")
 
    if field not in SUB_TASK_ALLOWED_FIELDS:
        return jsonify(error=f"Invalid field: '{field}'"), 400
 
    if value is None:
        return jsonify(error="value is required"), 400
 
    return Tasks_Service.update_sub_task_fields(sub_task_id, field, value)

@task.route("/sub_task/calculate/", methods = ["POST"])
@token_required()
@log_action(action = "GET", target="TASK")
def calc_ratings():
    data = request.json
    array = data.get("sub_tasks", [])
    print(array)
    return Tasks_Service.calculate_sub_tasks_rating(array)


@task.route("/assigned_department/<dept_id>", methods = ["GET"])
@token_required()
@log_action(action = "GET", target="TASK")
def get_assigned_department(dept_id):
    return Tasks_Service.get_assigned_department(dept_id)

@task.route("/assigned_department/", methods = ["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="TASK")
def update_assigned_department():
    data = request.json

    print(data)
    return Tasks_Service.update_tasks_weights(data)


@task.route("/department/<dept_id>", methods = ["GET"])
@token_required()
def get_tasks_assigned_by_dept(dept_id):
    return Tasks_Service.get_department_task(dept_id)


@task.route("/assigned_department/<adept_id>", methods=["PATCH"])
@token_required()
@log_action(action = "UPDATE", target="TASK")
def update_dept_task_field(adept_id):
    field = request.args.get("field")
    value = request.args.get("value")
 
    if field not in ASSIGNED_DEPT_ALLOWED_FIELDS:
        return jsonify(error=f"Invalid field: '{field}'"), 400
 
    if value is None:
        return jsonify(error="value is required"), 400
 
    return Tasks_Service.update_assigned_dept(adept_id, field, value)