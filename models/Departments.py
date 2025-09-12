from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    manager_id = db.Column(db.Integer)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=1)
    department = db.relationship("Department", back_populates="users")

    users = db.relationship("User", back_populates="department")
    opcrs = db.relationship("OPCR", back_populates="department")

    


    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "users": [user.to_dict() for user in self.users],
            "opcrs":[opcr.to_dict() for opcr in self.opcrs]
        }