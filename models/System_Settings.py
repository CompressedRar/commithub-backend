from app import db
from app import socketio
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
import uuid
import secrets

class System_Settings(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)

    # -----------------------
    # RATING SCALE THRESHOLDS
    # -----------------------
    # Example:
    # {
    #   "outstanding": {"min":1.30},
    #   "very_satisfactory": {"min":1.15, "max":1.29},
    #   "satisfactory": {"min":0.90, "max":1.14},
    #   "unsatisfactory": {"min":0.51, "max":0.89},
    #   "poor": {"max":0.50}
    # }
    rating_thresholds = db.Column(JSON, nullable=False, default={})

    # -----------------------
    # COMPUTATION FORMULA SETTINGS (optional but powerful)
    # -----------------------
    quantity_formula = db.Column(JSON, default={})
    efficiency_formula = db.Column(JSON, default={})
    timeliness_formula = db.Column(JSON, default={})

    # -----------------------
    # METADATA
    # -----------------------
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, 
        default=datetime.now,
        onupdate=datetime.now
    )



    current_period_id = db.Column(db.String(100), nullable=True)

    current_president_fullname = db.Column(db.String(255), nullable=True)
    current_mayor_fullname = db.Column(db.String(255), nullable=True)


    #planning period
    #monitoring period
    #rating period
    current_phase = db.Column(db.String(100), nullable=True)
    
    current_period = db.Column(db.String(100), nullable=True)

    planning_start_date = db.Column(db.Date, nullable=True)
    planning_end_date = db.Column(db.Date, nullable=True)

    monitoring_start_date = db.Column(db.Date, nullable=True)
    monitoring_end_date = db.Column(db.Date, nullable=True)

    rating_start_date = db.Column(db.Date, nullable=True)
    rating_end_date = db.Column(db.Date, nullable=True)

    def get_current_period(self):
        """
        Determines the current period based on today's date and the configured date ranges.
        Returns a dict with period info or None if no active period.
        """
        today = datetime.now().date()
        current_phases = []
        
        # Check planning period
        if (self.planning_start_date and self.planning_end_date and 
            self.planning_start_date <= today <= self.planning_end_date):
            current_phases.append("planning")
        
        # Check monitoring period
        if (self.monitoring_start_date and self.monitoring_end_date and 
            self.monitoring_start_date <= today <= self.monitoring_end_date):
            current_phases.append("monitoring")
        
        # Check rating period
        if (self.rating_start_date and self.rating_end_date and 
            self.rating_start_date <= today <= self.rating_end_date):
            current_phases.append("rating")
        
        # No active period found
        return current_phases if current_phases else None



    def to_dict(self):
        return {
            "id": self.id,
            "rating_thresholds": self.rating_thresholds,
            "quantity_formula": self.quantity_formula,
            "efficiency_formula": self.efficiency_formula,
            "timeliness_formula": self.timeliness_formula,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "planning_start_date": self.planning_start_date,
            "planning_end_date": self.planning_end_date,    
            "monitoring_start_date": self.monitoring_start_date,
            "monitoring_end_date": self.monitoring_end_date,
            "rating_start_date": self.rating_start_date,
            "rating_end_date": self.rating_end_date,
            "current_period": self.current_period,
            "current_period_id": self.current_period_id,
            "current_president_fullname": self.current_president_fullname,
            "current_mayor_fullname": self.current_mayor_fullname,
            "current_phase": self.get_current_period()            
        }
    

class System_Settings_Service:
    @staticmethod
    def get_settings():
        settings = System_Settings.query.first()
        if settings:
            return jsonify({"status":"success", "data":settings.to_dict()}), 200
        else:
            return jsonify({"status":"error", "message":"Settings not found."}), 404
        
    def update_settings(new_settings):
        settings = System_Settings.query.first()
        if not settings:
            settings = System_Settings()
            db.session.add(settings)

        print("PATCHING SETTINGS")
        
        settings.rating_thresholds = new_settings.get("rating_thresholds", settings.rating_thresholds)
        settings.quantity_formula = new_settings.get("quantity_formula", settings.quantity_formula)
        settings.efficiency_formula = new_settings.get("efficiency_formula", settings.efficiency_formula)
        settings.timeliness_formula = new_settings.get("timeliness_formula", settings.timeliness_formula)

        settings.planning_start_date = new_settings.get("planning_start_date", settings.planning_start_date)
        settings.planning_end_date = new_settings.get("planning_end_date", settings.planning_end_date)

        settings.monitoring_start_date = new_settings.get("monitoring_start_date", settings.monitoring_start_date)  
        settings.monitoring_end_date = new_settings.get("monitoring_end_date", settings.monitoring_end_date)

        settings.rating_start_date = new_settings.get("rating_start_date", settings.rating_start_date)
        settings.rating_end_date = new_settings.get("rating_end_date", settings.rating_end_date)

        settings.current_period = new_settings.get("current_period", settings.current_period)
        settings.current_period_id = new_settings.get("current_period_id", settings.current_period_id)

        settings.current_president_fullname = new_settings.get("current_president_fullname", settings.current_president_fullname)
        settings.current_mayor_fullname = new_settings.get("current_mayor_fullname", settings.current_mayor_fullname)

        try:
            print("SETTINGS PATCHED")
            db.session.commit()
            return jsonify({"status":"success", "data":settings.to_dict()}), 200
        except (IntegrityError, OperationalError, DataError, ProgrammingError) as e:
            db.session.rollback()
            return jsonify({"status":"error", "message":str(e)}), 500
        
    def check_if_rating_period():

        setting = System_Settings.query.first()
        if not setting or not setting.rating_start_date or not setting.rating_end_date:
            return False


        start = str(setting.rating_start_date)
        end = str(setting.rating_end_date)

        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
        today = date.today()

        

        is_between = start_date <= today <= end_date
        return is_between
    
    def change_period():
        """
        Generate a new random period ID and set it as the current period.
        Returns the updated settings with the new period ID.
        """
        try:
            settings = System_Settings.query.first()
            if not settings:
                settings = System_Settings()
                db.session.add(settings)
            
            # Generate a random period ID (UUID format: e.g., "PERIOD-2024-f7b3c8a1")
            random_id = f"PERIOD-{datetime.now().year}-{str(uuid.uuid4().hex[:8]).upper()}"
            
            # Update the current period ID
            settings.current_period_id = random_id
            settings.updated_at = datetime.now()
            
            from models.PCR import OPCR, OPCR_Rating, OPCR_Supporting_Document
            
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Period changed successfully",
                "new_period_id": random_id,
                "data": settings.to_dict()
            }), 200
            
        except (IntegrityError, OperationalError, DataError, ProgrammingError) as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"Database error: {str(e)}"
            }), 500
        except Exception as e:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }), 500