from flask import Blueprint, render_template, jsonify
from app import db
from models.User import test_create_user
from models.User import Users

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.route("/login")
def authenticate_login():
    return "working login"

@auth.route("/login")
def register_user():
    return "working user"


@auth.route("/")
def authenticate_test():
    return jsonify(message = "testingall", response = "test")

@auth.route("/test-create-user")
def test_create_user_route():
    
    return test_create_user()

@auth.route("/test-get-user")
def test_get_user_route():
    
    return Users.get_user(1)

@auth.route("/test-get-all-user")
def test_getall_user_route():
    
    return Users.get_all_users()

@auth.route("/test-update-user")
def test_update_user_route():
    data = {
        "first_name": "test update name"
    }
    return Users.update_user(1, data)

@auth.route("/test-delete-user")
def test_delete_user_route():
    
    return Users.delete_user(1)
