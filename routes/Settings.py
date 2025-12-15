from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Positions import Positions
from json import loads

from models.System_Settings import System_Settings_Service


settings = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings.route("/", methods = ["GET"])
@token_required()
def get_settings():
    return System_Settings_Service.get_settings()

@settings.route("/", methods = ["PATCH"])
@token_required()
def update_settings():
    new_settings = request.get_json()
    return System_Settings_Service.update_settings(new_settings)

@settings.route("/validate-formula", methods = ["POST"])
@token_required()
def validate_formula():
    new_settings = request.get_json()
    formula = loads(new_settings.get("formula"))

    print(formula)

    from models.Tasks import Formula_Engine

    try:
        engine = Formula_Engine()

        result = engine.validate_formula(formula=formula)

        return jsonify(message = result), 200 

    except Exception as e:

        return jsonify(message = str(e)), 200 


    