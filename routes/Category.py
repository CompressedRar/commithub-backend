from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Categories import Category_Service

category = Blueprint("category", __name__, url_prefix="/api/v1/category")

@category.route("/", methods = ["GET"])
@token_required()
def get_categories():
    return Category_Service.get_all()

@category.route("/tasks", methods = ["GET"])
@token_required()
def get_categories_with_tasks():
    return Category_Service.get_all_with_tasks()

@category.route("/count", methods = ["GET"])
@token_required()
def get_categories_count():
    return Category_Service.get_category_count()

@category.route("/<id>", methods = ["GET"])
@token_required()
def get_category(id):
    return Category_Service.get_category(id)

@category.route("/order/<id>&<prio_num>", methods = ["PATCH"])
@token_required()
def update_priority_number(id, prio_num):
    return Category_Service.update_category_order(id, prio_num)


@category.route("/", methods = ["POST"])
@token_required(allowed_roles=["administrator"])
@log_action(action = "CREATE", target="CATEGORY")
def create_category():
    data = request.form
    return Category_Service.create_category(data)

@category.route("/<id>", methods = ["DELETE"])
@token_required(allowed_roles=["administrator"])
@log_action(action = "ARCHIVE", target="CATEGORY")
def archive_category(id):
    return Category_Service.archive_category(id)

@category.route("/", methods = ["PATCH"])
@token_required(allowed_roles=["administrator"])
@log_action(action = "UPDATE", target="CATEGORY")
def update_category():
    data = request.form
    print(data)
    return Category_Service.update_category(data)