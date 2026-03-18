from app import db, socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from flask import jsonify


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.now)
    read = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": str(self.created_at),
            "read": self.read,
        }


class Notification_Service:

    def _notify_users(users, msg):
        """Shared helper: create notifications for a list of users and emit."""
        for user in users:
            db.session.add(Notification(user_id=user.id, name=msg))
        db.session.commit()
        socketio.emit("notification")

    def _handle_exc(e):
        db.session.rollback()

    def mark_as_read(id_arrays):
        try:
            for id in id_arrays:
                notif = Notification.query.get(id)
                notif.read = True
            db.session.commit()
            return jsonify(message="Success"), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def get_user_notification(user_id):
        try:
            notifications = Notification.query.filter_by(user_id=user_id).all()
            return jsonify([n.to_dict() for n in notifications]), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def notify_everyone(msg):
        try:
            from models.User import User
            Notification_Service._notify_users(User.query.all(), msg)
        except Exception as e:
            db.session.rollback()

    def notify_user(user_id, msg):
        try:
            from models.User import User
            user = User.query.filter_by(id=user_id).first()
            if user:
                Notification_Service._notify_users([user], msg)
        except Exception as e:
            db.session.rollback()

    def notify_department(dept_id, msg):
        try:
            from models.User import User
            Notification_Service._notify_users(
                User.query.filter_by(department_id=dept_id).all(), msg
            )
        except Exception as e:
            db.session.rollback()

    def notify_by_role(role, msg):
        """Generic role-based notifier used by heads, presidents, administrators."""
        try:
            from models.User import User
            users = User.query.filter_by(role=role).all()
            if users:
                Notification_Service._notify_users(users, msg)
        except Exception as e:
            db.session.rollback()

    def notify_heads(msg):
        Notification_Service.notify_by_role("head", msg)

    def notify_presidents(msg):
        Notification_Service.notify_by_role("president", msg)

    def notify_administrators(msg):
        Notification_Service.notify_by_role("administrator", msg)

    def notify_department_heads(dept_id, msg):
        try:
            from models.User import User
            heads = User.query.filter_by(role="head", department_id=dept_id).all()
            if heads:
                Notification_Service._notify_users(heads, msg)
        except Exception as e:
            db.session.rollback()
