from app import db
from datetime import datetime, timedelta
import hashlib
import secrets # More secure for tokens than uuid

class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @staticmethod
    def create_for_user(user_id, expires_hours=1):
        # Generate a long, secure random token for the URL
        plain_token = secrets.token_urlsafe(32) 
        salt = secrets.token_hex(16)
        
        # Hash the token for storage
        token_hash = hashlib.sha256((plain_token + salt).encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        new_token = PasswordResetToken(
            user_id=user_id, 
            token_hash=token_hash, 
            salt=salt, 
            expires_at=expires_at
        )
        
        db.session.add(new_token)
        db.session.commit()
        
        # Return the PLAIN token to send in the email
        return plain_token

    @staticmethod
    def verify_and_get_user(plain_token):
        try:
            # Look for all unused tokens that haven't expired
            active_tokens = PasswordResetToken.query.filter_by(used=False).filter(
                PasswordResetToken.expires_at >= datetime.now()
            ).all()

            for record in active_tokens:
                calc_hash = hashlib.sha256((plain_token + record.salt).encode()).hexdigest()
                if calc_hash == record.token_hash:
                    # Mark as used immediately to prevent replay attacks
                    record.used = True
                    db.session.commit()
                    return record.user_id # Return ID so you can update the user's password
            
            return None
        except Exception as e:
            print("Token verification failed", e)
            db.session.rollback()
            return None