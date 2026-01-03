from flask import Blueprint, render_template, jsonify
from app import db
from models.User import test_create_user
from models.User import Users
from models.Positions import Position, Positions
from utils import Email

test = Blueprint("test", __name__, url_prefix="/api/test")





@test.route("/create-user")
def test_create_user_route():
    
    return test_create_user()

@test.route("/get-user")
def test_get_user_route():
    
    return Users.get_user(1)

@test.route("/get-all-user")
def test_getall_user_route():
    
    return Users.get_all_users()

@test.route("/update-user")
def test_update_user_route():
    data = {
        "first_name": "test update name"
    }
    return Users.update_user(1, data)

@test.route("/delete-user")
def test_delete_user_route():
    
    return Users.delete_user(1)

@test.route("/get-all-positions")
def test_getall_positions():
    
    return Positions.get_all_positions()

@test.route("/get-all-user-count")
def test_getall_count():
    
    return Users.count_users_by_depts()





