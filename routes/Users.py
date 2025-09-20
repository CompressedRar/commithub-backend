from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.User import Users

users = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users.route("/", methods = ["GET"])
def get_users():
    return Users.get_all_users()

@users.route("/<id>", methods = ["GET"])
def get_user(id):
    return Users.get_user(id)



@users.route("/", methods = ["PATCH"])
@log_action(action = "UPDATE", target="USER")
def update_user():
    data = request.form
    return Users.update_user(data["id"], data)


@users.route("/<id>", methods = ["DELETE"])
@log_action(action = "DEACTIVATE", target="USER")
def archive_user(id):
    
    return Users.archive_user(id)


@users.route("/<id>", methods = ["POST"])
@log_action(action = "REACTIVATE", target="USER")
def unarchive_user(id):
    
    return Users.unarchive_user(id)

