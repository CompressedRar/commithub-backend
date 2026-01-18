from flask import Blueprint, render_template, jsonify, request
from app import db, limiter
from app import socketio

from models.AdminConfirmation import AdminConfirmation
from models.User import Users, User
from models.AdminConfirmation import AdminConfirmation
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
@limiter.limit("5 per minute")
def verify_admin_password():
    data = request.get_json() or request.form
    password = data.get("password")

    if not password:
        return jsonify(error="Password is required"), 400

    # get user id from payload attached by token_required
    payload = getattr(request, "user_payload", None)
    if not payload:
        return jsonify(error="Invalid token payload"), 401

    user_id = payload.get("id")
    if not user_id:
        return jsonify(error="Invalid token payload"), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify(error="There is no user with that id."), 400

    ph = PasswordHasher()
    try:
        ph.verify(hash=user.password, password=password)
        print("VERIFIED")
        # create short-lived confirmation token
        token = AdminConfirmation.create_for_user(user_id, minutes=10)
        return jsonify(message="Verified", confirmation_token=token, expires_in_minutes=10), 200
    except Exception:
        return jsonify(error="Invalid password"), 401
