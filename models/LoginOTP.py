from app import db
from datetime import datetime, timedelta
import hashlib
import uuid

class LoginOTP(db.Model):
    __tablename__ = "login_otps"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    otp_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def create_for_user(user_id, otp_plain, expires_minutes=5):
        salt = uuid.uuid4().hex
        otp_hash = hashlib.sha256((otp_plain + salt).encode()).hexdigest()
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        new = LoginOTP(user_id=user_id, otp_hash=otp_hash, salt=salt, expires_at=expires_at)
        db.session.add(new)
        db.session.commit()
        return new

    def verify_user_otp(user_id, otp_plain):
        try:
            otps = LoginOTP.query.filter_by(user_id=user_id, used=False).filter(LoginOTP.expires_at >= datetime.now()).order_by(LoginOTP.created_at.desc()).all()
            if not otps:
                return False
            for otp in otps:
                calc_hash = hashlib.sha256((otp_plain + otp.salt).encode()).hexdigest()
                if calc_hash == otp.otp_hash:
                    otp.used = True
                    db.session.commit()
                    return True
            return False
        except Exception as e:
            print("LoginOTP verify failed", e)
            db.session.rollback()
            return False
