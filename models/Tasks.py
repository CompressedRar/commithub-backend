from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

class Main_Task(db.Model):
    __tablename__ = "main_tasks"
    id = db.Column(db.Integer, primary_key=True)
    
    mfo = db.Column(db.Text, nullable=False)

    target_accomplishment = db.Column(db.Text, nullable=False)
    target_time_description = db.Column(db.Text, nullable=False)
    target_modification = db.Column(db.Text, nullable=False)

    actual_accomplishment = db.Column(db.Text, nullable=False)
    actual_time_description = db.Column(db.Text, nullable=False)
    actual_modification = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Boolean, default=True)

    #one category and one department
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates = "main_tasks")

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    deparment = db.relationship("Department", back_populates = "main_tasks")

    sub_tasks = db.relationship("Sub_Task", back_populates = "main_task", cascade = "all, delete")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "target_time": self.target_time_description,
            "target_mod": self.target_modification,
            "actual_acc": self.actual_accomplishment,
            "actual_time": self.actual_time_description,
            "actual_acc": self.actual_modification,
            "created_at": self.created_at,
            "status": self.status,
            
            "department": self.department_id,
            "category": self.category_id,
            "sub_tasks": [sub_task.to_dict() for sub_task in self.sub_tasks],
        }
    
class Sub_Task(db.Model):
    __tablename__ = "sub_tasks"
    id = db.Column(db.Integer, primary_key=True)
    
    mfo = db.Column(db.Text, nullable=False)


    """
     target : {
                description: test,
                value: 0
                }
    """
    target_accomplishment = db.Column(JSON)
    target_time_description = db.Column(JSON)
    target_modification = db.Column(JSON)

    actual_accomplishment = db.Column(JSON)
    actual_time_description = db.Column(JSON)
    actual_modification = db.Column(JSON)

    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Boolean, default=True)
    
    quantity = db.Column(db.Integer, default = 0)
    efficiency = db.Column(db.Integer, default = 0)
    timeliness = db.Column(db.Integer, default = 0)
    average = db.Column(db.Integer, default = 0)

    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    main_task = db.relationship("Main_Task", back_populates="sub_tasks")

    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"))
    ipcr = db.relationship("IPCR", back_populates="sub_tasks")    


    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "target_time": self.target_time_description,
            "target_mod": self.target_modification,
            "actual_acc": self.actual_accomplishment,
            "actual_time": self.actual_time_description,
            "actual_acc": self.actual_modification,
            "created_at": self.created_at,
            "status": self.status,

            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "average": self.average,

            "ipcr": self.ipcr_id,
            "main_task": self.main_task_id
        }
 