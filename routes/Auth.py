from flask import Blueprint, render_template, jsonify, request
from app import db
from models.User import Users
from models.Positions import Position, Positions

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.route("/login", methods = ["POST"])
def authenticate_user():
    return "working login"

@auth.route("/register", methods=["POST"])
def register_user():
    data = request.form
    profile_pic = request.files.get("profile_picture")
    print(data)
    if not data:

        return jsonify({"error": "Missing field JSON"}), 400
    
    return Users.add_new_user(data, profile_pic)

@auth.route("/")
def authenticate_test():
    return jsonify(message = "testingall", response = "test")

@auth.route("/positions", methods=["GET"])
def get_all_positions():
    return Positions.get_all_positions()

@auth.route("/check/<email>", methods=["GET"])
def check_email(email):
    return Users.check_email_if_exists(email)
