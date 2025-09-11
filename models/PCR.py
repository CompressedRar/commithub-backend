from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

class IPCR(db.Model):
    __tablename__ = "ipcr"
    id = db.Column(db.Integer, primary_key=True)
    
    reviewed_by = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")

    #one ipcr to one user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="ipcrs")

    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"))
    opcr = db.relationship("OPCR", back_populates="ipcrs")

    


    sub_tasks = db.relationship("Sub_Task", back_populates = "ipcr", cascade = "all, delete")


    def to_dict(self):
        return {
            "id" : self.id,
            "user": self.user_id,
            "sub_tasks": [main_task.to_dict() for main_task in self.sub_tasks]
        }
    
class OPCR(db.Model):
    __tablename__ = "opcr"
    id = db.Column(db.Integer, primary_key=True)
    
    reviewed_by = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")
    #one ipcr to one opcr

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", back_populates="opcrs")

    ipcrs = db.relationship("IPCR", back_populates = "opcr", cascade = "all, delete")

    def to_dict(self):
        return {
            "id" : self.id,
            "user": self.user_id,
            "sub_tasks": [main_task.to_dict() for main_task in self.sub_tasks]
        }