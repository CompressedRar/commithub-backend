from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify

from sqlalchemy import func

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
        
    def get_log_activity_trend():
        results = (
            db.session.query(
                func.date(Log.created_at).label("date"),
                func.count(Log.id).label("value")
            )
            .group_by(func.date(Log.created_at))
            .order_by(func.date(Log.created_at))
            .all()
        )

        data = [
            {"name": r.date.strftime("%Y-%m-%d"), "value": r.value}
            for r in results
        ]

        return jsonify(data), 200
    
    def get_logs_by_hour():
        """
        Returns number of log entries per hour:
        [
            {"name": "00:00", "value": 2},
            {"name": "01:00", "value": 5},
            ...
        ]
        """
        results = (
            db.session.query(
                func.extract("hour", Log.created_at).label("hour"),
                func.count(Log.id).label("value")
            )
            .group_by(func.extract("hour", Log.created_at))
            .order_by(func.extract("hour", Log.created_at))
            .all()
        )

        # Initialize 24-hour bins to ensure all hours are present
        data = []
        for h in range(24):
            count = next((r.value for r in results if int(r.hour) == h), 0)
            label = f"{h:02d}:00"
            data.append({"name": label, "value": int(count)})

        return jsonify(data), 200
    
    def get_activity_scatter():
        """
        Returns data for scatter chart (activity by day and hour)
        [
            { "day": 0, "hour": 13, "count": 5 }, ...
        ]
        """
        results = (
            db.session.query(
                func.dayofweek(Log.created_at).label("day"),  # Sunday = 1, Saturday = 7
                func.hour(Log.created_at).label("hour"),
                func.count(Log.id).label("count")
            )
            .group_by("day", "hour")
            .all()
        )

        data = [
            {"day": r.day, "hour": r.hour, "count": r.count}
            for r in results
        ]
        return jsonify(data), 200
        

"""
si user palitan ng default password
"""

     