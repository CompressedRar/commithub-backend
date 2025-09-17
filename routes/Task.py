from flask import Blueprint, render_template, jsonify, request
from app import db

from models.Tasks import Tasks_Service

task = Blueprint("task", __name__, url_prefix="/api/v1/task")

@task.route("/", methods = ["GET"])
def get_tasks():
    return Tasks_Service.get_main_tasks()

@task.route("/<id>", methods = ["GET"])
def get_task(id):
    return Tasks_Service.get_main_task(id)

@task.route("/<id>", methods = ["DELETE"])
def archive_task(id):
    return Tasks_Service.archive_task(id)

@task.route("/", methods = ["POST"])
def create_main_task():
    data = request.form
    print(data)
    return Tasks_Service.create_main_task(data)

@task.route("/", methods = ["PATCH"])
def update_main_task():
    data = request.form
    return Tasks_Service.update_task_info(data)
