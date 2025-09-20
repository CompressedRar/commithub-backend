from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Categories import Category_Service

category = Blueprint("category", __name__, url_prefix="/api/v1/category")

@category.route("/", methods = ["GET"])
def get_categories():
    return Category_Service.get_all()

@category.route("/<id>", methods = ["GET"])
def get_category(id):
    return Category_Service.get_category(id)


@category.route("/", methods = ["POST"])
@log_action(action = "CREATE", target="CATEGORY")
def create_category():
    data = request.form
    return Category_Service.create_category(data)

@category.route("/<id>", methods = ["DELETE"])
@log_action(action = "ARCHIVE", target="CATEGORY")
def archive_category(id):
    return Category_Service.archive_category(id)

@category.route("/", methods = ["PATCH"])
@log_action(action = "UPDATE", target="CATEGORY")
def update_category():
    data = request.form
    print(data)
    return Category_Service.update_category(data)