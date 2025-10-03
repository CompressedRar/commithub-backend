from flask import Blueprint, render_template, jsonify, request
from app import db

from models.Tasks import Tasks_Service
from utils.decorators import log_action
task = Blueprint("task", __name__, url_prefix="/api/v1/task")

@task.route("/count", methods = ["GET"])
def get_tasks_count():
    return Tasks_Service.get_all_tasks_count()

@task.route("/", methods = ["GET"])
def get_tasks():
    return Tasks_Service.get_main_tasks()

@task.route("/general", methods = ["GET"])
def get_general_tasks():
    return Tasks_Service.get_general_tasks()


@task.route("/<id>", methods = ["GET"])
def get_task(id):
    return Tasks_Service.get_main_task(id)

@task.route("/<id>", methods = ["DELETE"])
@log_action(action = "ARCHIVE", target="TASK")
def archive_task(id):
    return Tasks_Service.archive_task(id)

@task.route("/", methods = ["POST"])
@log_action(action = "CREATE", target="TASK")
def create_main_task():
    data = request.form
    print(data)
    return Tasks_Service.create_main_task(data)

@task.route("/", methods = ["PATCH"])
@log_action(action = "UPDATE", target="TASK")
def update_main_task():
    data = request.form
    return Tasks_Service.update_task_info(data)

@task.route("/sub_task/<sub_task_id>", methods = ["PATCH"])
def update_sub_task_field(sub_task_id):
    field = request.args.get("field")
    value = request.args.get("value")
    print(sub_task_id, field, value)
    return Tasks_Service.update_sub_task_fields(sub_task_id, field, value)