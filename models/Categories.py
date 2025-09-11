from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    
    main_tasks = db.relationship("Main_Task", back_populates = "category", cascade = "all, delete")

    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "main_tasks": [main_task.to_dict() for main_task in self.main_tasks]
        }