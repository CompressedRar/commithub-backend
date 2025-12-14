from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from models.Logs import Log_Service

logs = Blueprint("logs", __name__, url_prefix="/api/v1/log")


@logs.route("/", methods = ["GET"])
@token_required()
def get_logs():
    return Log_Service.get_all_logs()


