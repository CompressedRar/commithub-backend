from app import db, socketio
from sqlalchemy.exc import OperationalError
from flask import jsonify

from models.PCR import IPCR, OPCR
from models.Notification import Notification_Service


class PCRWorkflowService:

    # ------------------------------------------------------------------
    # Generic status-change helper
    # ------------------------------------------------------------------

    def _set_ipcr_status(ipcr_id, status, notify_fn=None):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            if not ipcr:
                return jsonify(error="There is no ipcr with that id"), 400

            ipcr.form_status = status
            db.session.commit()
            socketio.emit("ipcr", status)
            socketio.emit("opcr", status)

            if notify_fn:
                notify_fn(ipcr)

            return jsonify(message=f"This IPCR is successfully {status}."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    def _set_opcr_status(opcr_id, status, notify_fn=None):
        try:
            opcr = OPCR.query.get(opcr_id)
            if not opcr:
                return jsonify(error="There is no opcr with that id"), 400

            opcr.form_status = status
            db.session.commit()
            socketio.emit("ipcr", status)
            socketio.emit("opcr", status)

            if notify_fn:
                notify_fn(opcr)

            return jsonify(message=f"This OPCR is successfully {status}."), 200

        except Exception as e:
            return jsonify(error=str(e)), 500

    # ------------------------------------------------------------------
    # IPCR workflow
    # ------------------------------------------------------------------

    def reject_ipcr(ipcr_id):
        def notify(ipcr):
            socketio.emit("reject")
            Notification_Service.notify_user(
                ipcr.user.id,
                f"Your IPCR: #{ipcr_id} has been rejected by department head of this department.",
            )
            Notification_Service.notify_presidents(
                f"IPCR: #{ipcr_id} from {ipcr.user.department.name} has been rejected by department head."
            )

        return PCRWorkflowService._set_ipcr_status(ipcr_id, "rejected", notify)

    def review_ipcr(ipcr_id):
        def notify(ipcr):
            Notification_Service.notify_user(
                ipcr.user.id,
                f"Your IPCR: #{ipcr_id} has been reviewed by department head of this department.",
            )
            Notification_Service.notify_presidents(
                f"IPCR: #{ipcr_id} from {ipcr.user.department.name} has been reviewed by department head."
            )

        return PCRWorkflowService._set_ipcr_status(ipcr_id, "reviewed", notify)

    def approve_ipcr(ipcr_id):
        def notify(ipcr):
            Notification_Service.notify_user(
                ipcr.user.id,
                f"Your IPCR: #{ipcr_id} has been reviewed by president.",
            )

        return PCRWorkflowService._set_ipcr_status(ipcr_id, "approved", notify)

    # ------------------------------------------------------------------
    # OPCR workflow
    # ------------------------------------------------------------------

    def reject_opcr(opcr_id):
        def notify(opcr):
            socketio.emit("reject")
            Notification_Service.notify_department(
                opcr.department_id,
                "The OPCR from this department has been rejected by department head.",
            )

        return PCRWorkflowService._set_opcr_status(opcr_id, "rejected", notify)

    def review_opcr(opcr_id):
        def notify(opcr):
            Notification_Service.notify_department_heads(
                opcr.department_id, f"OPCR: #{opcr.id} has been reviewed by the president."
            )

        return PCRWorkflowService._set_opcr_status(opcr_id, "reviewed", notify)

    def approve_opcr(opcr_id):
        def notify(opcr):
            Notification_Service.notify_department_heads(
                opcr.department_id, f"OPCR: #{opcr.id} has been approved by the president."
            )

        return PCRWorkflowService._set_opcr_status(opcr_id, "approved", notify)

    # ------------------------------------------------------------------
    # IPCR pending/reviewed/approved queries
    # ------------------------------------------------------------------

    def _get_ipcrs_by_role_and_status(roles, form_status):
        """Return IPCRs matching roles and form_status that are active and main."""
        try:
            from models.user import User

            skip_roles = set(User.query.with_entities(User.role).distinct()) - set(roles)
            results = []

            for user in User.query.all():
                if user.role not in roles:
                    continue
                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == form_status and ipcr.isMain:
                        results.append(ipcr.department_info())

            return jsonify(results), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_member_pendings(dept_id):
        try:
            from models.user import User

            results = []
            for user in User.query.filter_by(account_status=1, department_id=dept_id, role="faculty").all():
                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == "pending" and ipcr.isMain:
                        results.append(ipcr.department_info())
            return jsonify(results), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_member_reviewed():
        return PCRWorkflowService._get_ipcrs_by_role_and_status(["faculty"], "reviewed")

    def get_member_approved():
        return PCRWorkflowService._get_ipcrs_by_role_and_status(["faculty"], "approved")

    def get_head_pendings():
        return PCRWorkflowService._get_ipcrs_by_role_and_status(["head"], "pending")

    def get_head_reviewed():
        return PCRWorkflowService._get_ipcrs_by_role_and_status(["head"], "reviewed")

    def get_head_approved():
        return PCRWorkflowService._get_ipcrs_by_role_and_status(["head"], "approved")

    # ------------------------------------------------------------------
    # OPCR pending/reviewed/approved queries
    # ------------------------------------------------------------------

    def _get_opcrs_by_status(form_status):
        try:
            opcrs = OPCR.query.filter_by(status=1, form_status=form_status).all()
            return jsonify([o.to_dict() for o in opcrs]), 200
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_opcr_pendings():
        return PCRWorkflowService._get_opcrs_by_status("pending")

    def get_opcr_reviewed():
        return PCRWorkflowService._get_opcrs_by_status("reviewed")

    def get_opcr_approved():
        return PCRWorkflowService._get_opcrs_by_status("approved")
