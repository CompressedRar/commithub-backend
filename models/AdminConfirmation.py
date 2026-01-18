from app import db
from datetime import datetime, timedelta
import uuid

class AdminConfirmation(db.Model):
    __tablename__ = "admin_confirmations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def create_for_user(user_id, minutes=10):
        token = uuid.uuid4().hex
        expires_at = datetime.now() + timedelta(minutes=minutes)
        confirm = AdminConfirmation(user_id=user_id, token=token, expires_at=expires_at)
        db.session.add(confirm)
        db.session.commit()
        return token

    @staticmethod
    def verify(user_id, token):
        try:
            print("VERIFYING TOKEN")
            conf = AdminConfirmation.query.filter_by(user_id=user_id, token=token, used=False).first()
            if not conf:
                return False
            if conf.expires_at < datetime.now():
                return False
            # mark used
            conf.used = True
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print("AdminConfirmation verify error", e)
            return False
