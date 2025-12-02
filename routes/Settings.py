from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Positions import Positions
from json import loads

from models.System_Settings import System_Settings_Service


settings = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings.route("/", methods = ["GET"])
def get_settings():
    return System_Settings_Service.get_settings()

@settings.route("/", methods = ["PATCH"])
def update_settings():
    new_settings = request.get_json()
    return System_Settings_Service.update_settings(new_settings)