from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Positions import Positions
from json import loads
from datetime import datetime, date
from models.System_Settings import System_Settings_Service


settings = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings.route("/", methods = ["GET"])
@token_required(allowed_roles=["administrator"])
def get_settings():
    return System_Settings_Service.get_settings()

@settings.route("/", methods = ["PATCH"])
@token_required(allowed_roles=["administrator"])
def update_settings():
    new_settings = request.get_json()
    return System_Settings_Service.update_settings(new_settings)

@settings.route("/validate-formula", methods = ["POST"])
@token_required(allowed_roles=["administrator"])
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


@settings.route("/get-date")
def test_check_time():
    from models.System_Settings import System_Settings

    setting = System_Settings.query.first()

    start = str(setting.rating_start_date)
    end = str(setting.rating_end_date)

    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    today = date.today()

    print(start_date, end_date, today)

    is_between = start_date <= today <= end_date
    
    return str(is_between)
