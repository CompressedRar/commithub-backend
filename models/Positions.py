from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify

class Position(db.Model):
    __tablename__ = "positions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    users = db.relationship("User", back_populates = "position")
    
    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
        }

    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "users": [user.to_dict() for user in self.users]
        }
    

class Positions():
    def get_all_positions():
        try:
            positions = Position.query.all()
            return jsonify([pos.to_dict() for pos in positions]), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
        