from app import db
from sqlalchemy.exc import OperationalError
from flask import jsonify
from models.Tasks import Main_Task, Assigned_Department, Output, Sub_Task


class TaskQueryService:

    def get_assigned_department(dept_id):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            found = Assigned_Department.query.filter_by(
                department_id=dept_id, period=settings.current_period_id
            ).all()

            converted = [ad.info() for ad in found if ad.main_task.status]
            return jsonify(converted), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_assigned_departments_for_opcr(dept_id):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            found = Assigned_Department.query.filter_by(
                department_id=dept_id,
                period=settings.current_period_id,
                status=1,
            ).all()

            converted = [ad.info() for ad in found if ad.main_task.status]
            return jsonify(converted), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_tasks_by_department(id):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            all_dept_tasks = Assigned_Department.query.filter_by(
                department_id=id, period=settings.current_period_id
            ).all()

            converted = []
            for task in all_dept_tasks:
                if task.main_task.status:
                    data = task.main_task.info()
                    data["quantity_formula"] = settings.quantity_formula
                    data["efficiency_formula"] = settings.efficiency_formula
                    data["timeliness_formula"] = settings.timeliness_formula
                    data["assigned_dept_id"] = task.id
                    data["enable_formulas"] = task.enable_formulas
                    converted.append(data)

            return jsonify(converted), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_department_task(dept_id):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            all_assigned = Assigned_Department.query.filter_by(
                period=settings.current_period_id, department_id=dept_id
            ).all()

            return jsonify(tasks=[t.main_task.ipcr_info() for t in all_assigned]), 200

        except Exception as e:
            return jsonify(error="There is an error fetching tasks."), 500

    def get_assigned_users(dept_id, task_id):
        try:
            found_task = Main_Task.query.get(task_id)
            if found_task is None:
                return jsonify(""), 200

            return jsonify(found_task.get_users_by_dept(id=dept_id)), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_general_assigned_users(task_id):
        try:
            found_task = Main_Task.query.filter_by(id=task_id).first()
            if found_task is None:
                return jsonify(""), 200

            return jsonify(found_task.get_users()), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_general_tasks():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            tasks = Main_Task.query.filter(
                Main_Task.department_id.is_(None),
                Main_Task.status == 1,
                Main_Task.period == settings.current_period_id,
            ).all()
            return jsonify([t.info() for t in tasks]), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_all_general_tasks():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            tasks = Main_Task.query.filter_by(
                department_id=None, status=1, period=settings.current_period_id
            ).all()
            return jsonify([t.info() for t in tasks]), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500
