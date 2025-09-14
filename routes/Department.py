from flask import Blueprint, render_template, jsonify, request
from app import db

from models.Departments import Department_Service

department = Blueprint("department", __name__, url_prefix="/api/v1/department")

@department.route("/", methods = ["GET"])
def get_departments():
    return Department_Service.get_all_departments()

@department.route("/<id>", methods = ["GET"])
def get_department(id):
    return Department_Service.get_department(id)

@department.route("/members/<id>", methods = ["GET"])
def get_department_members(id):
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    print("this trigger")
    return Department_Service.get_members(id, offset, limit)

@department.route("/create", methods = ["POST"])
def create_department():
    data = request.form
    return Department_Service.create_department(data)

@department.route("/update", methods = ["POST"])
def update_department():
    data = request.form
    return Department_Service.update_department(data["id"],data)
    

@department.route("/<id>", methods = ["DELETE"])
def archive_department(id):
    return Department_Service.archive_department(id)