from app import db, socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from flask import jsonify
from models.Tasks import Main_Task, Assigned_Department, Assigned_Task, Output
from models.User import Notification_Service


class TaskCRUDService:

    def get_main_tasks():
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()

        try:
            all_main_tasks = Main_Task.query.filter_by(
                status=1, period=settings.current_period_id
            ).all()
            return jsonify([t.info() for t in all_main_tasks]), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_main_task(id):
        try:
            main_task = Main_Task.query.get(id)
            return jsonify(main_task.info()), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_all_tasks_count():
        from sqlalchemy import func
        tasks_count = db.session.query(func.count(Main_Task.id)).scalar()
        return jsonify(message={"count": tasks_count})

    def create_main_task(data):
        try:
            from models.System_Settings import System_Settings
            current_settings = System_Settings.get_default_settings()

            new_main_task = Main_Task(
                mfo=data["task_name"],
                target_accomplishment=data["task_desc"],
                actual_accomplishment=data["past_task_desc"],
                accomplishment_editable=int(data["accomplishment_editable"]),
                time_editable=int(data["time_editable"]),
                modification_editable=int(data["modification_editable"]),
                time_description=data["time_measurement"],
                modification=data["modification"],
                category_id=int(data["id"]),
                require_documents=data.get("require_documents", False),
                period=current_settings.current_period_id if current_settings else None,
                description=data["description"],
                target_quantity=data.get("target_quantity", 0),
                target_efficiency=data.get("target_efficiency", 0),
                target_timeframe=data.get("target_timeframe", 0),
                target_deadline=(
                    datetime.strptime(data["target_deadline"], "%Y-%m-%d")
                    if data.get("target_deadline")
                    else None
                ),
                timeliness_mode=data.get("timeliness_mode", "timeframe"),
            )
            db.session.add(new_main_task)
            db.session.flush()

            if data.get("department"):
                for department_id in data["department"].split(","):
                    new_assigned_department = Assigned_Department(
                        department_id=department_id,
                        main_task_id=new_main_task.id,
                        period=current_settings.current_period_id if current_settings else None,
                    )
                    db.session.add(new_assigned_department)

            Notification_Service.notify_department(
                dept_id=data["department"], msg="A new task has been added to the department."
            )
            Notification_Service.notify_presidents(msg="A new task has been added.")
            Notification_Service.notify_administrators(msg="A new task has been added.")

            db.session.commit()
            return jsonify(message="Task successfully created."), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Task already exists"), 400
        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_task_info(data):
        try:
            found_task = Main_Task.query.get(data["id"])

            if found_task is None:
                return jsonify(message="No output with that ID"), 400
            if not data:
                return jsonify(message="You must submit data to update fields"), 400

            from models.System_Settings import System_Settings
            current_settings = System_Settings.get_default_settings()

            all_previous_department = found_task.info()["department_ids"]
            updated_departments = (
                [int(i) for i in data["department"].split(",")]
                if data.get("department")
                else []
            )

            for dept_id in updated_departments:
                if dept_id not in all_previous_department:
                    db.session.add(Assigned_Department(
                        main_task_id=int(data["id"]),
                        department_id=dept_id,
                        period=current_settings.current_period_id,
                    ))

            for dept_id in all_previous_department:
                if dept_id not in updated_departments:
                    found_ad = Assigned_Department.query.filter_by(
                        main_task_id=int(data["id"]), department_id=dept_id
                    ).first()
                    db.session.delete(found_ad)

                    for ass_task in Assigned_Task.query.filter_by(main_task_id=int(data["id"])).all():
                        if ass_task.user.department.id == dept_id:
                            db.session.delete(ass_task)

                        for output in Output.query.filter_by(
                            user_id=ass_task.user.id, main_task_id=data["id"]
                        ).all():
                            db.session.delete(output)

            field_map = {
                "name": "mfo",
                "target_accomplishment": "target_accomplishment",
                "description": "description",
                "actual_accomplishment": "actual_accomplishment",
                "time_description": "time_description",
                "modification": "modification",
                "target_quantity": "target_quantity",
                "target_efficiency": "target_efficiency",
                "status": "status",
            }
            for key, attr in field_map.items():
                if key in data:
                    setattr(found_task, attr, data[key])

            if "require_documents" in data:
                found_task.require_documents = data["require_documents"] == "true"

            if "timeliness_mode" in data:
                found_task.timeliness_mode = data["timeliness_mode"]
                if data["timeliness_mode"] == "timeframe" and "target_timeframe" in data:
                    found_task.target_timeframe = data["target_timeframe"]
                elif data["timeliness_mode"] != "timeframe" and "target_deadline" in data:
                    found_task.target_deadline = (
                        datetime.strptime(data["target_deadline"], "%Y-%m-%d")
                        if data["target_deadline"]
                        else None
                    )

            socketio.emit("category", "update")
            db.session.commit()
            Notification_Service.notify_everyone(msg=f"The task: {found_task.mfo} has been updated.")
            return jsonify(message="Task successfully updated."), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Data does not exists"), 400
        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def archive_task(id):
        try:
            main_task = Main_Task.query.get(id)
            if not main_task:
                return jsonify(message="No main task with that ID"), 400

            main_task.status = 0
            for sub_task in main_task.sub_tasks:
                sub_task.status = 0
            for output in main_task.outputs:
                db.session.delete(output)
            for assigned_task in main_task.assigned_tasks:
                db.session.delete(assigned_task)

            db.session.commit()
            socketio.emit("main_task", "archived")
            return jsonify(message="Task successfully archived."), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_tasks_weights(data):
        try:
            for assigned_task_id, weight in dict(data).items():
                found_task = Assigned_Department.query.get(assigned_task_id)
                found_task.task_weight = weight

            db.session.commit()
            socketio.emit("weight", "update")
            return jsonify(message="Weights are successfully updated."), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_assigned_dept(assigned_dept_id, field, value):
        try:
            found_task = Assigned_Department.query.get(assigned_dept_id)
            if not found_task:
                return jsonify(error="Task is not found"), 400

            if field in ("quantity", "efficiency", "timeliness"):
                setattr(found_task, field, value)

            db.session.commit()
            socketio.emit("rating", "change")
            return jsonify(message="Updated Successfully"), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error="There is an error updating task"), 500

    def update_department_task_formula(assigned_dept_id, data):
        try:
            assigned_dept = Assigned_Department.query.get(assigned_dept_id)
            assigned_dept.enable_formulas = data.get("enable_formulas", assigned_dept.enable_formulas)
            assigned_dept.quantity_formula = data.get("quantity_formula", assigned_dept.quantity_formula)
            assigned_dept.efficiency_formula = data.get("efficiency_formula", assigned_dept.efficiency_formula)
            assigned_dept.timeliness_formula = data.get("timeliness_formula", assigned_dept.timeliness_formula)

            db.session.commit()
            return jsonify(message="Formula successfully updated."), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
