from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify

class Log(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    full_name = db.Column(db.String(50), nullable=False)

    department = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    action = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(50),  nullable=False)

    description = db.Column(db.Text, nullable=True) 
    ip_address = db.Column(db.String(45), nullable=True) 
    user_agent = db.Column(db.String(255), nullable=True)


    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "department": self.department,
            "action": self.action,
            "target": self.target,
            "user_id": self.user_id,
            "user_agent": self.user_agent,    
            "ip_address": self.ip_address,
            "timestamp": self.created_at,       
        }
    
class Log_Service:

    def add_logs(userid, f_name, dept, action, target, description = None, ip = None, agent = None):
        try: 
            new_log = Log(full_name = f_name,
                          department = dept,
                          action = action,
                          target = target,
                          description = description,
                          ip_address = ip,
                          user_agent = agent,
                          user_id = userid
                          )
            
            db.session.add(new_log)
            db.session.commit()
            return "Logs recorded"
        except DataError as e:
            db.session.rollback()
            print(str(e))            
            return "Invalid data format"

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return "Database connection error"

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return str(e)
        
    def get_all_logs():
        try:
            all_logs = Log.query.all()
            converted = [log.to_dict() for log in all_logs]

            return jsonify(converted), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        

"""
si user palitan ng default password
"""

     