from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Departments import Department_Service
from models.PCR import PCR_Service
from models.Logs import Log_Service

charts = Blueprint("charts", __name__, url_prefix="/api/v1/chart")

@charts.route("/pie/population-per-department", methods = ["GET"])
def population_per_department():
    return Department_Service.get_user_count_per_department()

@charts.route("/bar/performance-per-department", methods = ["GET"])
def performance_per_department():
    return Department_Service.get_average_performance_by_department()

@charts.route("/bar/performance/<dept_id>", methods = ["GET"])
def get_user_performance_by_department_id(dept_id):
    return Department_Service.get_user_performance_by_department_id(department_id=dept_id)

@charts.route("/bar/summary/", methods = ["GET"])
def get_department_performance_summary():
    return PCR_Service.get_department_performance_summary()

@charts.route("/line/activity/", methods = ["GET"])
def get_activity_trend():
    return Log_Service.get_log_activity_trend()

@charts.route("/line/logs-by-hour/", methods = ["GET"])
def get_logs_by_hour():
    return Log_Service.get_logs_by_hour()

@charts.route("/scatter/logs/", methods = ["GET"])
def get_scatter_activity():
    return Log_Service.get_activity_scatter()