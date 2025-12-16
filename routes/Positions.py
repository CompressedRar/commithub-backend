from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Positions import Positions
from json import loads
positions = Blueprint("positions", __name__, url_prefix="/api/v1/positions")


@positions.route("/", methods = ["GET"])
@token_required()
def get_positions():
    return Positions.get_all_positions()

@positions.route("/info", methods = ["GET"])
@token_required()
def get_positions_info():
    return Positions.get_position_info()

@positions.route("/", methods = ["PATCH"])
@token_required(allowed_roles=["administrator"])
def update_positions_info():
    data = loads(request.data)
    return Positions.update_position(data)

@positions.route("/", methods = ["POST"])
@token_required(allowed_roles=["administrator"])
def create_position():
    data = loads(request.data)

    return Positions.create_position(data)

@positions.route("/archive/<id>", methods = ["DELETE"])
@token_required(allowed_roles=["administrator"])
def archive_position(id):
    return Positions.archive_position(id)


@positions.route("/restore/<id>", methods = ["PATCH"])
@token_required(allowed_roles=["administrator"])
def restore_position(id):
    return Positions.restore_position(id)
