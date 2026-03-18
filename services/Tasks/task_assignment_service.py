from app import db, socketio
from sqlalchemy.exc import OperationalError, DataError
from flask import jsonify
from models.Tasks import Main_Task, Assigned_Task, Assigned_Department, Output, Sub_Task
from models.User import User
from models.Notification import Notification, Notification_Service


class TaskAssignmentService:

    def _check_if_ipcrs_have_tasks():
        """Remove IPCRs that have no remaining sub_tasks."""
        from models.PCR import IPCR, Supporting_Document

        ipcrs = IPCR.query.filter(~IPCR.sub_tasks.any()).all()
        for ipcr in ipcrs:
            Supporting_Document.query.filter_by(ipcr_id=ipcr.id).delete()
            db.session.delete(ipcr)
        db.session.commit()

    def assign_user(task_id, user_id, assigned_quantity, assigned_time, assigned_mod):
        try:
            from models.System_Settings import System_Settings
            from models.PCR import IPCR
            from services.pcr_service import PCR_Service

            current_settings = System_Settings.get_default_settings()
            period = current_settings.current_period_id if current_settings else None

            main_task = Main_Task.query.get(task_id)
            existing_ipcr = IPCR.query.filter_by(user_id=user_id, period=period).first()

            if existing_ipcr:
                Assigned_Task.query.filter_by(user_id=user_id, main_task_id=task_id).delete()
                db.session.flush()

                db.session.add(Assigned_Task(
                    user_id=user_id,
                    main_task_id=task_id,
                    is_assigned=True,
                    period=period,
                    assigned_quantity=assigned_quantity,
                    assigned_time=assigned_time,
                    assigned_mod=assigned_mod,
                ))
                db.session.flush()
                db.session.commit()

                from models.PCR import Supporting_Document

                for docu in Supporting_Document.query.filter_by(ipcr_id=existing_ipcr.id).all():
                    if docu.sub_task.main_task.id == int(task_id):
                        db.session.delete(docu)
                db.session.commit()

                Sub_Task.query.filter_by(
                    main_task_id=task_id,
                    batch_id=existing_ipcr.batch_id,
                    ipcr_id=existing_ipcr.id,
                    period=period,
                ).delete()
                db.session.commit()

                Output.query.filter_by(
                    user_id=user_id,
                    main_task_id=task_id,
                    batch_id=existing_ipcr.batch_id,
                    ipcr_id=existing_ipcr.id,
                    period=period,
                ).delete()
                db.session.commit()

                db.session.add(Output(
                    user_id=user_id,
                    main_task_id=task_id,
                    batch_id=existing_ipcr.batch_id if current_settings else "",
                    ipcr_id=existing_ipcr.id,
                    period=period,
                    assigned_quantity=assigned_quantity,
                    assigned_time=assigned_time,
                    assigned_mod=assigned_mod,
                ))
            else:
                PCR_Service.generate_IPCR_from_tasks(
                    user_id=user_id,
                    main_task_id=task_id,
                    assigned_quantity=assigned_quantity,
                )

            db.session.commit()

            user = User.query.get(user_id)
            socketio.emit("user_assigned", "user assigned")
            Notification_Service.notify_user(
                user_id, msg=f"The task: {main_task.mfo} has been assigned to this account."
            )
            Notification_Service.notify_presidents(
                msg=f"The task: {main_task.mfo} has been assigned to {user.first_name} {user.last_name}."
            )
            return jsonify(message="Member successfully assigned."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def unassign_user(task_id, user_id):
        try:
            Assigned_Task.query.filter_by(user_id=user_id, main_task_id=task_id).delete()

            user = User.query.get(user_id)

            for output in Output.query.filter_by(user_id=user_id, main_task_id=task_id).all():
                for task in Sub_Task.query.filter_by(output_id=output.id).all():
                    for doc in task.supporting_documents:
                        db.session.delete(doc)
                    db.session.commit()
                    db.session.delete(task)
                db.session.commit()

            Output.query.filter_by(user_id=user_id, main_task_id=task_id).delete()
            db.session.commit()

            TaskAssignmentService._check_if_ipcrs_have_tasks()

            task = Main_Task.query.get(task_id)
            socketio.emit("user_unassigned", "user assigned")
            Notification_Service.notify_user(user_id=user_id, msg="A task has been unassigned from you.")
            Notification_Service.notify_presidents(
                msg=f"{user.first_name} {user.last_name} has been removed from task: {task.mfo}."
            )
            return jsonify(message="Task successfully removed."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def assign_department(task_id, dept_id):
        try:
            from models.Departments import Department
            from models.System_Settings import System_Settings

            task = Main_Task.query.get(task_id)
            department = Department.query.get(dept_id)
            settings = System_Settings.get_default_settings()

            db.session.add(Assigned_Department(
                main_task_id=task_id,
                department_id=dept_id,
                period=settings.current_period_id,
                quantity_formula=settings.quantity_formula,
                efficiency_formula=settings.efficiency_formula,
                timeliness_formula=settings.timeliness_formula,
                enable_formulas=False,
            ))

            if task is None:
                return jsonify(message="Output is not found."), 400

            db.session.commit()

            Notification_Service.notify_department(
                dept_id=dept_id, msg=f"The task: {task.mfo} has been assigned to the office."
            )
            Notification_Service.notify_administrators(
                msg=f"The task: {task.mfo} has been assigned to {department.name}."
            )
            Notification_Service.notify_presidents(
                msg=f"The task: {task.mfo} has been assigned to {department.name}."
            )
            socketio.emit("department_assigned", "department assigned")
            socketio.emit("user_assigned", "user assigned")
            return jsonify(message="Task successfully assigned."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def remove_task_from_dept(id, dept_id):
        try:
            from models.System_Settings import System_Settings

            found_task = Main_Task.query.get(id)
            if found_task is None:
                return jsonify(message="No task with that ID"), 400

            settings = System_Settings.get_default_settings()
            found_ad = Assigned_Department.query.filter_by(
                main_task_id=id, department_id=dept_id, period=settings.current_period_id
            ).first()
            db.session.delete(found_ad)

            for ass_task in Assigned_Task.query.filter_by(main_task_id=id).all():
                if ass_task.user.department_id == int(dept_id):
                    db.session.delete(ass_task)

                for output in Output.query.filter_by(user_id=ass_task.user.id, main_task_id=id).all():
                    db.session.delete(output)

            TaskAssignmentService._check_if_ipcrs_have_tasks()

            db.session.commit()
            socketio.emit("task_modified", "task modified")
            socketio.emit("department_assigned", "task modified")
            Notification_Service.notify_department(
                dept_id, f"The task: {found_task.mfo} has been removed from this office."
            )
            return jsonify(message="Task successfully removed."), 200

        except (IntegrityError := __import__('sqlalchemy.exc', fromlist=['IntegrityError']).IntegrityError):
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

    def create_user_output(task_id, user_id, current_batch_id, ipcr_id):
        try:
            from models.System_Settings import System_Settings

            current_settings = System_Settings.get_default_settings()
            period = current_settings.current_period_id if current_settings else None

            db.session.add(Output(
                user_id=user_id,
                main_task_id=task_id,
                batch_id=current_batch_id,
                ipcr_id=ipcr_id,
                period=period,
            ))
            db.session.commit()
            socketio.emit("user_assigned", "user assigned")
            return jsonify(message="User successfully assigned."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def create_task_for_ipcr(task_id, user_id, current_batch_id, ipcr_id):
        try:
            from models.System_Settings import System_Settings

            current_settings = System_Settings.get_default_settings()
            period = current_settings.current_period_id if current_settings else None

            db.session.add(Output(
                user_id=user_id,
                main_task_id=task_id,
                batch_id=current_batch_id,
                ipcr_id=ipcr_id,
                period=period,
            ))
            db.session.add(Assigned_Task(
                user_id=user_id,
                main_task_id=task_id,
                batch_id=current_batch_id,
                period=period,
                is_assigned=True,
            ))
            db.session.commit()
            socketio.emit("ipcr_added", "user assigned")
            return jsonify(message="Task successfully added."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def remove_output_by_main_task_id(main_task_id, batch_id):
        try:
            output = Output.query.filter_by(main_task_id=main_task_id, batch_id=batch_id).first()
            assigned_task = Assigned_Task.query.filter_by(
                main_task_id=main_task_id, batch_id=batch_id
            ).first()

            if output is None:
                return jsonify(message="There is no tasks found."), 400
            if assigned_task is None:
                return jsonify(message="There is no assigned tasks found."), 400

            db.session.delete(output)
            db.session.delete(assigned_task)
            db.session.commit()

            socketio.emit("ipcr", "subtask removed")
            socketio.emit("ipcr_remove", "subtask removed")
            return jsonify(message="Output was successfully removed."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
