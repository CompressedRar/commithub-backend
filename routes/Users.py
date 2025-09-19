from flask import Blueprint, render_template, jsonify, request
from app import db

from models.User import Users

users = Blueprint("users", __name__, url_prefix="/api/v1/users")

@users.route("/", methods = ["GET"])
def get_users():
    return Users.get_all_users()

@users.route("/<id>", methods = ["GET"])
def get_user(id):
    return Users.get_user(id)


@users.route("/", methods = ["PATCH"])
def update_user():
    data = request.form
    return Users.update_user(data["id"], data)
