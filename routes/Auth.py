from flask import Blueprint, render_template, jsonify, request
from app import db, limiter
from app import socketio

from models.User import Users, User
from models.Positions import Position, Positions
from models.Categories import Category
from models.Tasks import Sub_Task, Main_Task
from models.Departments import Department
from models.PCR import IPCR, OPCR
from utils.decorators import log_enter, token_required
from argon2 import PasswordHasher
import jwt

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.route("/login", methods = ["POST"])
@limiter.limit("5 per minute")
def authenticate_user():
    data = request.form
    print("Data received: ", data.keys())
    return Users.authenticate_user(data)

@auth.route("/verify-otp", methods=["POST"])
@limiter.limit("10 per minute")
def verify_otp():
    data = request.get_json() or request.form
    email = data.get("email")
    otp = data.get("otp")
    return Users.verify_login_otp(email, otp)

@auth.route("/register", methods=["POST"])
@log_enter(action="REGISTER")
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

@auth.route("/user-count")
def getall_count():
    
    return Users.count_users_by_depts()

@auth.route("/check/<email>", methods=["GET"])
def check_email(email):
    return Users.check_email_if_exists(email)

@auth.route("/verify-admin-password", methods=["POST"])
@token_required(allowed_roles=["administrator"])
def verify_admin_password():
    data = request.get_json() or request.form
    password = data.get("password")

    if not password:
        return jsonify(error="Password is required"), 400

    # decode token to get user id
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify(error="Authorization header missing"), 401

    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, "priscilla", algorithms=["HS256"])
    except Exception as e:
        return jsonify(error="Invalid token"), 401

    user_id = payload.get("id")
    if not user_id:
        return jsonify(error="Invalid token payload"), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify(error="There is no user with that id."), 400

    ph = PasswordHasher()
    try:
        ph.verify(hash=user.password, password=password)
        return jsonify(message="Verified"), 200
    except Exception:
        return jsonify(error="Invalid password"), 401
