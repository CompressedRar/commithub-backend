from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify

class Log(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50), nullable=False)

    department = db.Column(db.String(50), default="staff", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(50),  nullable=False)


    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "department": self.department,
            "action": self.action,
            "target": self.target,            
        }
    
class Logs:
    def add_logs(f_name, dept, action, target):
        try: 
            new_log = Logs(full_name = f_name, department = dept, action = action, target = target)
            db.session.add(new_log)
            db.session.commit()
            return jsonify(message = "Logs recorded"), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500

     