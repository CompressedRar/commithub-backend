from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action
from models.Departments import Department_Service
from models.PCR import PCR_Service
from models.Logs import Log_Service
from models.Categories import Category_Service
from models.Tasks import Tasks_Service
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

@charts.route("/bar/category/<cat_id>", methods = ["GET"])
def get_tasks_average(cat_id):
    return Category_Service.get_task_average_summary(category_id=cat_id)

@charts.route("/bar/task/all", methods = ["GET"])
def get_all_tasks_average():
    return Tasks_Service.get_all_tasks_average_summary()

@charts.route("/bar/task-user-average/<main_task_id>", methods = ["GET"])
def get_tasks_user_average(main_task_id):
    return Tasks_Service.get_task_user_averages(main_task_id)

@charts.route("/pie/task-ratio/<main_task_id>", methods = ["GET"])
def get_tasks_user_ratio(main_task_id):
    return Tasks_Service.get_department_subtask_percentage(main_task_id)


@charts.route("/pie/category-performance/<cat_id>", methods = ["GET"])
def get_category_performancve(cat_id):
    return Category_Service.calculate_category_performance(category_id=cat_id)


@charts.route("/pie/main-task-performance/<main_task_id>", methods = ["GET"])
def get_main_task_performancve(main_task_id):
    return Tasks_Service.calculate_main_task_performance(main_task_id)


@charts.route("/pie/user-task-performance/<user_id>", methods = ["GET"])
def get_user_task_performancve(user_id):
    return Tasks_Service.calculate_user_performance(user_id=user_id)

@charts.route("/top/department-performance/", methods = ["GET"])
def get_top_department():
    return Department_Service.get_top_performing_department()