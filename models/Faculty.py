from app import db
from datetime import datetime

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default="")
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique= True, nullable=False)
    password = db.Column(db.String(50), nullable=False, default = "12345678")
    position = db.Column(db.String(50), default="faculty")
    created_at = db.Column(db.DateTime, default=datetime.now)