from flask import Blueprint, render_template, jsonify, request
from app import db
from models.User import Users
from models.Positions import Position, Positions
from utils.decorators import token_required

admin = Blueprint("admin", __name__, url_prefix="/api/v1/admin")

@admin.route("/")
@token_required
def admin_homepage():
    return "this is adminpage"