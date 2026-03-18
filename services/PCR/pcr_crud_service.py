from app import db, socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from flask import jsonify
import uuid

from models.PCR import IPCR, OPCR, OPCR_Rating, Assigned_PCR, Supporting_Document
from models.Tasks import Assigned_Task, Output, Sub_Task
from models.Departments import Department
from models.Notification import Notification_Service


class PCRCRUDService:

    # ------------------------------------------------------------------
    # IPCR generation
    # ------------------------------------------------------------------

    def generate_IPCR_from_tasks(user_id, main_task_id, assigned_quantity):
        try:
            from models.System_Settings import System_Settings

            batch_id = str(uuid.uuid4())
            period = System_Settings.get_default_settings().current_period_id

            new_ipcr = IPCR(
                user_id=user_id, batch_id=batch_id,
                form_status="submitted", period=period, isMain=True,
            )
            db.session.add(new_ipcr)
            db.session.flush()

            if not Assigned_Task.query.filter_by(
                user_id=user_id, main_task_id=main_task_id,
                batch_id=batch_id, period=period,
            ).first():
                db.session.add(Assigned_Task(
                    user_id=user_id, main_task_id=main_task_id,
                    is_assigned=False, batch_id=batch_id, period=period,
                    assigned_quantity=0, assigned_time=0, assigned_mod=0,
                ))

            db.session.add(Output(
                user_id=user_id, main_task_id=main_task_id,
                batch_id=batch_id, ipcr_id=new_ipcr.id, period=period,
            ))
            db.session.commit()

            socketio.emit("ipcr_create", {
                "ipcr_id": new_ipcr.id,
                "batch_id": batch_id,
                "user_id": user_id,
            })
            Notification_Service.notify_presidents(
                f"A new IPCR has been submitted from {new_ipcr.user.department.name}."
            )
            return jsonify(message="IPCR successfully created"), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def generate_IPCR(user_id, main_task_id_array):
        try:
            from models.System_Settings import System_Settings

            batch_id = str(uuid.uuid4())
            period = System_Settings.get_default_settings().current_period_id

            existing_ipcr = IPCR.query.filter_by(user_id=user_id, period=period).first()

            if existing_ipcr:
                for mt_id in main_task_id_array:
                    if Output.query.filter_by(
                        user_id=user_id, main_task_id=mt_id,
                        batch_id=existing_ipcr.batch_id, period=period,
                    ).first():
                        continue

                    if not Assigned_Task.query.filter_by(
                        user_id=user_id, main_task_id=mt_id,
                        batch_id=existing_ipcr.batch_id, period=period,
                    ).first():
                        db.session.add(Assigned_Task(
                            user_id=user_id, main_task_id=mt_id,
                            is_assigned=False, batch_id=existing_ipcr.batch_id, period=period,
                        ))

                    db.session.add(Output(
                        user_id=user_id, main_task_id=mt_id,
                        batch_id=existing_ipcr.batch_id,
                        ipcr_id=existing_ipcr.id, period=period,
                    ))
                    db.session.flush()

                db.session.commit()
                return jsonify(message="An IPCR for the current period already exists."), 200

            new_ipcr = IPCR(
                user_id=user_id, batch_id=batch_id,
                form_status="submitted", period=period, isMain=True,
            )
            db.session.add(new_ipcr)
            db.session.flush()

            for mt_id in main_task_id_array:
                if Output.query.filter_by(
                    user_id=user_id, main_task_id=mt_id,
                    batch_id=batch_id, period=period,
                ).first():
                    continue

                if not Assigned_Task.query.filter_by(
                    user_id=user_id, main_task_id=mt_id,
                    batch_id=batch_id, period=period,
                ).first():
                    db.session.add(Assigned_Task(
                        user_id=user_id, main_task_id=mt_id,
                        is_assigned=False, batch_id=batch_id, period=period,
                    ))

                db.session.add(Output(
                    user_id=user_id, main_task_id=mt_id,
                    batch_id=batch_id, ipcr_id=new_ipcr.id, period=period,
                ))

            db.session.commit()
            socketio.emit("ipcr_create", {
                "ipcr_id": new_ipcr.id,
                "batch_id": batch_id,
                "user_id": user_id,
                "task_count": len(main_task_id_array),
            })
            Notification_Service.notify_presidents(
                f"A new IPCR has been submitted from {new_ipcr.user.department.name}."
            )
            return jsonify(message="IPCR successfully created"), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # OPCR creation helpers + main method
    # ------------------------------------------------------------------

    def _create_or_get_opcr(dept_id, period):
        existing = OPCR.query.filter_by(
            department_id=dept_id, isMain=True, period=period
        ).first()
        if existing:
            return existing

        new_opcr = OPCR(department_id=dept_id, isMain=True, period=period)
        db.session.add(new_opcr)
        db.session.flush()

        OPCR.query.filter_by(department_id=dept_id).filter(
            OPCR.period != period
        ).update({"isMain": False, "status": 0}, synchronize_session=False)

        return new_opcr

    def _mark_main_opcr(dept_id, opcr_id, period):
        OPCR.query.filter_by(department_id=dept_id, period=period).update(
            {"isMain": False, "status": 0}, synchronize_session=False
        )
        OPCR.query.filter_by(id=opcr_id).update(
            {"isMain": True, "status": 1}, synchronize_session=False
        )

    def _add_mfo_ratings(opcr, period, ipcr_ids):
        existing_mfos = {r.mfo for r in opcr.opcr_ratings}
        for ipcr_id in ipcr_ids:
            ipcr = IPCR.query.get(ipcr_id)
            if not ipcr or ipcr.period != period:
                continue
            for sub in ipcr.sub_tasks:
                if sub.status != 0 and sub.main_task.mfo not in existing_mfos:
                    db.session.add(OPCR_Rating(mfo=sub.main_task.mfo, opcr_id=opcr.id, period=period))
                    existing_mfos.add(sub.main_task.mfo)

    def _assign_pcrs_to_opcr(opcr, dept_id, period, ipcr_ids):
        valid_ipcrs = IPCR.query.filter(
            IPCR.id.in_(ipcr_ids), IPCR.period == period
        ).all()
        existing = {
            a.ipcr_id for a in Assigned_PCR.query.filter_by(
                opcr_id=opcr.id, department_id=dept_id
            ).all()
        }
        for ipcr in valid_ipcrs:
            if ipcr.id not in existing:
                db.session.add(Assigned_PCR(
                    opcr_id=opcr.id, ipcr_id=ipcr.id,
                    department_id=dept_id, period=period,
                ))

    def create_opcr(dept_id, ipcr_ids):
        try:
            from models.System_Settings import System_Settings

            if not dept_id or not isinstance(ipcr_ids, list):
                return jsonify(error="Invalid department ID or IPCR list"), 400

            settings = System_Settings.get_default_settings()
            if not settings or not settings.current_period_id:
                return jsonify(error="System period not configured"), 400

            period = settings.current_period_id

            if not Department.query.get(dept_id):
                return jsonify(error=f"Department {dept_id} not found"), 404

            opcr = PCRCRUDService._create_or_get_opcr(dept_id, period)
            PCRCRUDService._mark_main_opcr(dept_id, opcr.id, period)
            PCRCRUDService._add_mfo_ratings(opcr, period, ipcr_ids)
            PCRCRUDService._assign_pcrs_to_opcr(opcr, dept_id, period, ipcr_ids)

            db.session.commit()
            socketio.emit("opcr", "created")
            socketio.emit("opcr_created", "created")
            return jsonify(message="OPCR successfully created or updated.", opcr_id=opcr.id), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Data integrity error"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # Get / assign
    # ------------------------------------------------------------------

    def get_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            if ipcr:
                return jsonify(ipcr.to_dict()), 200
            return jsonify(message="There is no ipcr with that id"), 400
        except Exception as e:
            return jsonify(error=str(e)), 500

    def assign_main_ipcr(ipcr_id, user_id):
        try:
            from models.user import User

            user = User.query.get(user_id)
            if user is None:
                return jsonify(message="There is no user with that id"), 400

            for ipcr in user.ipcrs:
                ipcr.isMain = False
                ipcr.form_status = "draft"

            ipcr = IPCR.query.get(ipcr_id)
            ipcr.isMain = True
            ipcr.form_status = "submitted"

            db.session.commit()
            socketio.emit("assign")

            full = f"{user.first_name} {user.last_name}"
            Notification_Service.notify_department_heads(
                user.department_id,
                f"{full} assigned IPCR: #{ipcr_id} as its latest IPCR.",
            )
            Notification_Service.notify_presidents(
                f"{full} from {user.department.name} assigned IPCR: #{ipcr_id} as its latest IPCR."
            )
            return jsonify(message="IPCR successfully assigned."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def assign_pres_ipcr(ipcr_id, user_id):
        try:
            from models.user import User

            user = User.query.get(user_id)
            if user is None:
                return jsonify(message="There is no user with that id"), 400

            for ipcr in user.ipcrs:
                ipcr.isMain = False

            IPCR.query.get(ipcr_id).isMain = True
            db.session.commit()
            socketio.emit("assign")
            return jsonify(message="IPCR successfully assigned."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def assign_main_opcr(opcr_id, dept_id):
        try:
            dept = Department.query.get(dept_id)
            for opcr in OPCR.query.filter_by(department_id=dept_id).all():
                opcr.isMain = False
                opcr.status = 0

            target = OPCR.query.get(opcr_id)
            target.isMain = True
            target.status = 1
            target.form_status = "submitted"

            db.session.commit()
            socketio.emit("assign")

            Notification_Service.notify_department_heads(dept_id, f"{dept.name} submitted their latest OPCR.")
            Notification_Service.notify_presidents(f"{dept.name} submitted their latest IPCR.")
            return jsonify(message="OPCR successfully assigned."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    def archive_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.status = 0
            batch_id = ipcr.batch_id

            for q, model in [
                (Output.query.filter_by(batch_id=batch_id), "status"),
                (Assigned_Task.query.filter_by(batch_id=batch_id), "status"),
                (Sub_Task.query.filter_by(batch_id=batch_id), "status"),
            ]:
                for item in q.all():
                    item.status = 0

            db.session.commit()
            socketio.emit("ipcr_create", "ipcr archive")

            Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been archived.")
            Notification_Service.notify_department_heads(
                ipcr.user.department_id, f"The IPCR: #{ipcr_id} has been archived."
            )
            Notification_Service.notify_presidents(
                f"The IPCR: #{ipcr_id} from {ipcr.user.department.name} has been archived."
            )
            return jsonify(message="IPCR was archived successfully."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def archive_opcr(opcr_id):
        try:
            opcr = OPCR.query.get(opcr_id)
            opcr.status = 0
            for ipcr in opcr.ipcrs:
                PCRCRUDService.archive_ipcr(ipcr.id)

            db.session.commit()
            socketio.emit("opcr", "archive")
            return jsonify(message="OPCR was archived successfully."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # OPCR rating
    # ------------------------------------------------------------------

    def update_rating(rating_id, field, value):
        try:
            rating = OPCR_Rating.query.get(rating_id)
            for f in ("quantity", "efficiency", "timeliness"):
                if f in field.split(" "):
                    setattr(rating, f, value)
                    db.session.commit()

            socketio.emit("rating", "change")
            return jsonify(message="Rating updated"), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # Supporting documents
    # ------------------------------------------------------------------

    def record_supporting_document(file_type, file_name, ipcr_id, batch_id,
                                   sub_task_id=None, title="", desc="", event_date=None):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            parsed_date = datetime.strptime(event_date, "%Y-%m-%d") if event_date else None
            ipcr = IPCR.query.get(ipcr_id)

            db.session.add(Supporting_Document(
                file_type=file_type,
                file_name=file_name,
                ipcr_id=ipcr_id,
                batch_id=batch_id,
                sub_task_id=sub_task_id,
                period=settings.current_period_id,
                title=title,
                description=desc,
                event_date=parsed_date,
            ))
            db.session.commit()
            socketio.emit("document", "document")

            full = f"{ipcr.user.first_name} {ipcr.user.last_name}"
            Notification_Service.notify_department_heads(
                ipcr.user.department_id,
                f"{full} attached supporting document to IPCR: #{ipcr_id}.",
            )
            Notification_Service.notify_presidents(
                f"{full} attached supporting document to IPCR: #{ipcr_id}."
            )
            return jsonify(message="File successfully uploaded."), 200

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

    def get_ipcr_supporting_document(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            return [doc.to_dict() for doc in ipcr.supporting_documents], 200
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def get_supporting_documents(opcr_id):
        try:
            pcrs = Assigned_PCR.query.filter_by(opcr_id=opcr_id).all()
            docs = [doc.to_dict() for pcr in pcrs for doc in pcr.ipcr.supporting_documents]
            return jsonify(docs), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def archive_document(document_id):
        try:
            doc = Supporting_Document.query.get(document_id)
            doc.status = 0
            db.session.commit()
            socketio.emit("document", "document")
            return jsonify(message="Document successfully archived."), 200
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def collect_all_supporting_documents_by_department(dept_id):
        try:
            from models.System_Settings import System_Settings
            period = System_Settings.get_default_settings().current_period_id
            docs = Supporting_Document.query.filter_by(period=period).all()
            filtered = [d.to_dict() for d in docs if str(d.ipcr.user.department.id) == dept_id]
            return jsonify(message=filtered), 200
        except Exception as e:
            return jsonify(error="Collecting supporting documents failed"), 500

    def collect_all_supporting_documents():
        try:
            from models.System_Settings import System_Settings
            period = System_Settings.get_default_settings().current_period_id
            docs = Supporting_Document.query.filter_by(period=period).all()
            return jsonify(message=[d.to_dict() for d in docs]), 200
        except Exception as e:
            return jsonify(error="Collecting supporting documents failed"), 500
