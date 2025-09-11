from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    users = db.relationship("User", back_populates="department")
    opcrs = db.relationship("OPCR", back_populates="department")


    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "users": [user.to_dict() for user in self.users]
        }