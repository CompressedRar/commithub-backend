from flask import Blueprint, render_template, jsonify, request
from app import db
from utils.decorators import log_action, token_required
from utils.permissions import permissions_required
from models.Departments import Department_Service
from models.Tasks import Tasks_Service
from utils.DepartmentReportHandler import create_department_performance_report, create_all_departments_performance_report, create_all_tasks_summary_report

department = Blueprint("department", __name__, url_prefix="/api/v1/department")

@department.route("/", methods = ["GET"])
@token_required()
def get_departments():
    return Department_Service.get_all_departments()

@department.route("/<id>", methods = ["GET"])
@token_required()
def get_department(id):
    return Department_Service.get_department(id)

@department.route("/tasks/<id>", methods = ["GET"])
@token_required()
def get_department_tasks(id):
    return Tasks_Service.get_tasks_by_department(id)

@department.route("/general/", methods = ["GET"])
@token_required()
def get_general_tasks():
    return Tasks_Service.get_all_general_tasks()

@department.route("/ipcr/<id>", methods = ["GET"])
@permissions_required("ipcr.view")
def get_department_ipcr(id):
    return Department_Service.get_all_department_ipcr(id)

@department.route("/head/<dept_id>", methods = ["GET"])
@token_required()
def get_department_head(dept_id):
    return Department_Service.get_department_head(dept_id)

@department.route("/opcr/<dept_id>", methods = ["GET"])
@permissions_required("ipcr.view")
def get_department_opcr(dept_id):
    return Department_Service.get_all_department_opcr(dept_id=dept_id)

@department.route("/tasks/<task_id>&<dept_id>", methods = ["POST"])
@permissions_required("departments.manage")
def assign_department_tasks(task_id, dept_id):
    return Tasks_Service.assign_department(task_id, dept_id)

@department.route("/assigned/<dept_id>&<task_id>", methods = ["GET"])
@token_required()
def get_assigned_users_tasks(dept_id, task_id):
    return Tasks_Service.get_assigned_users(dept_id, task_id)

@department.route("/assigned/general/<task_id>", methods = ["GET"])
@token_required()
def get_general_assigned_users_tasks(task_id):
    return Tasks_Service.get_general_assigned_users(task_id)


@department.route("/assigned/<user_id>&<task_id>&<assigned_quantity>", methods = ["POST"])
@token_required()
@log_action(action = "ASSIGN", target="TASK")
def assign_user_task(user_id, task_id, assigned_quantity):
    return Tasks_Service.assign_user(task_id, user_id, assigned_quantity)



@department.route("/unassign/<user_id>&<task_id>", methods = ["POST"])
@token_required()
@log_action(action = "UNASSIGN", target="TASK")
def unassign_user_task(user_id, task_id):
    return Tasks_Service.unassign_user(task_id, user_id)

@department.route("/members/<id>", methods = ["GET"])
@token_required()
def get_department_members(id):
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    print("this trigger")
    return Department_Service.get_members(id, offset, limit)


@department.route("/create", methods = ["POST"])
@token_required()
@log_action(action = "CREATE", target="DEPARTMENT")
def create_department():
    data = request.form
    return Department_Service.create_department(data)


@department.route("/remove/<id>", methods = ["POST"])
@token_required()
@log_action(action = "REMOVE", target="USER")
def remove_user_from_department(id):
    
    return Department_Service.remove_user_from_department(id)


@department.route("/update", methods = ["POST"])
@token_required()
@log_action(action = "UPDATE", target="DEPARTMENT")
def update_department():
    data = request.form or request.json
    return Department_Service.update_department(data["id"],data)
    

@department.route("/<id>", methods = ["DELETE"])
@token_required()
@log_action(action = "ARCHIVE", target="DEPARTMENT")
def archive_department(id):
    return Department_Service.archive_department(id)


@department.route("/remove/<id>&deptid=<dept_id>", methods = ["DELETE"])
@token_required()
@log_action(action = "REMOVE", target="TASK")
def remove_task_department(id, dept_id):
    return Tasks_Service.remove_task_from_dept(id, dept_id)

@department.route("/assigned_department/<dept_id>", methods = ["GET"])
def get_assigned_department(dept_id):
    return Tasks_Service.get_assigned_departments_for_opcr(dept_id)


@department.route("/assigned_department/<assigned_dept_id>", methods = ["PATCH"])
def update_assigned_department_formulas(assigned_dept_id):
    new_data = request.get_json() 
    return Tasks_Service.update_department_task_formula(assigned_dept_id=assigned_dept_id, data=new_data)

@department.route("/<dept_id>/performance-report", methods = ["GET"])
def generate_performance_report(dept_id):
    """
    Generate and download a performance assessment report for a department.
    Returns an Excel file with average performance of all members.
    """
    try:
        file_url = create_department_performance_report(dept_id)
        return jsonify({
            "status": "success",
            "message": "Report generated successfully",
            "download_url": file_url
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate report: {str(e)}"}), 500


@department.route("/all/performance-report", methods = ["GET"])
def generate_nc_performance_report():
    """
    Generate and download a performance assessment report for a department.
    Returns an Excel file with average performance of all members.
    """
    try:
        file_url = create_all_departments_performance_report()
        print(file_url)
        return jsonify({
            "status": "success",
            "message": "Report generated successfully",
            "download_url": file_url
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate report: {str(e)}"}), 500
    

@department.route("/all/task-report", methods = ["GET"])
def generate_task_performance_report():
    """
    Generate and download a performance assessment report for a department.
    Returns an Excel file with average performance of all members.
    """
    try:
        file_url = create_all_tasks_summary_report()
        print(file_url)
        return jsonify({
            "status": "success",
            "message": "Report generated successfully",
            "download_url": file_url
        }), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to generate report: {str(e)}"}), 500
