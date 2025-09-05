from flask import Blueprint, render_template, jsonify
from app import db
from models.User import Users
from models.Positions import Position, Positions

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


