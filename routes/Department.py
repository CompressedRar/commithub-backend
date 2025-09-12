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