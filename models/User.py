from app import db
from datetime import datetime
from utils.FileStorage import get_file


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default="", nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False, default="commithubnc")
    profile_picture_link = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(
        db.Enum("faculty", "head", "president", "administrator"), default="faculty"
    )
    active_status = db.Column(db.Boolean, default=True)
    account_status = db.Column(db.Integer, default=1)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), default=1)
    managed_dept_id = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=1, nullable=True)
    recovery_email = db.Column(db.String(255), nullable=True)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)

    position = db.relationship("Position", back_populates="users")
    department = db.relationship("Department", back_populates="users")
    outputs = db.relationship("Output", back_populates="user")
    ipcrs = db.relationship("IPCR", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete")
    assigned_tasks = db.relationship("Assigned_Task", back_populates="user")

    task_responses = db.relationship("TaskResponse", back_populates="submitted_user")

    def _middle_initial(self):
        return self.middle_name[0].upper() + ". " if self.middle_name else " "

    def full_name(self):
        return f"{self.first_name} {self._middle_initial()}{self.last_name}"

    def _profile_pic(self):
        return get_file(self.profile_picture_link) if self.profile_picture_link else "/default-profile-pic.jpg"

    def info(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "full_name": self.full_name(),
            "profile_picture_link": self._profile_pic(),
            "position": self.position.info(),
            "role": self.role,
            "account_status": self.account_status,
            "department_id": self.department_id,
            "department": self.department.info() if self.department else "NONE",
            "department_name": self.department.info()["name"] if self.department else "NONE",
            "recovery_email": self.recovery_email,
            "two_factor_enabled": self.two_factor_enabled,
        }

    def tasks(self):
        return {"assigned_tasks": [a.task_info() for a in self.assigned_tasks]}

    def assigned_task(self):
        return {"assigned_tasks": [a.assigned_task_info() for a in self.assigned_tasks]}

    def calculatePerformance(self):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        totals = [
            output.sub_task.calculateAverage()
            for output in self.outputs
            if output.status != 0 and output.period == settings.current_period_id
        ]
        return sum(totals) / len(totals) if totals else 0

    def to_dict(self):
        from models.System_Settings import System_Settings
        from models.PCR import Assigned_PCR
        settings = System_Settings.get_default_settings()

        
        active_ipcrs = []

        for ipcr in self.ipcrs:
            
            if ipcr.status == 1 and (settings and ipcr.period == settings.current_period_id):
                active_ipcrs.append(ipcr.to_dict())
            
            
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "role": self.role,
            "email": self.email,
            "password": self.password,
            "profile_picture_link": self._profile_pic(),
            "active_status": self.active_status,
            "account_status": self.account_status,
            "created_at": str(self.created_at),
            "recovery_email": self.recovery_email,
            "two_factor_enabled": self.two_factor_enabled,
            "avg_performance": self.calculatePerformance(),
            "position": self.position.info() if self.position else "NONE",
            "department": self.department.info() if self.department else "NONE",
            "ipcrs": active_ipcrs,
            "ipcrs_count": len(self.ipcrs),
            "main_tasks_count": len(self.outputs),
        }
