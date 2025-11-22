from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Positions import Positions
from json import loads
positions = Blueprint("positions", __name__, url_prefix="/api/v1/positions")


@positions.route("/", methods = ["GET"])
def get_positions():
    return Positions.get_all_positions()

@positions.route("/info", methods = ["GET"])
def get_positions_info():
    return Positions.get_position_info()

@positions.route("/update", methods = ["PATCH"])
def update_positions_info():
    data = loads(request.data)
    return Positions.update_position(data)

@positions.route("/", methods = ["POST"])
def create_position():
    data = loads(request.data)

    return Positions.create_position(data)

@positions.route("/archive/<id>", methods = ["DELETE"])
def archive_position(id):
    return Positions.archive_position(id)


@positions.route("/restore/<id>", methods = ["PATCH"])
def restore_position(id):
    return Positions.restore_position(id)
