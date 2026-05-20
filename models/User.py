from app import db
from datetime import datetime
from utils.FileStorage import get_file

class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column( db.String(50), unique=True, nullable=False )
    password = db.Column( db.String(250), nullable=False, default="commithubnc" )
    recovery_email = db.Column( db.String(255), nullable=True )
    two_factor_enabled = db.Column( db.Boolean, default=False, nullable=False )
    profile_picture_link = db.Column( db.Text, nullable=True  )
    active_status = db.Column( db.Boolean, default=True  )
    created_at = db.Column(  db.DateTime, default=datetime.now )
    users = db.relationship( "User", back_populates="profile", cascade="all, delete" )

    def _profile_pic(self):
        return (
            get_file(self.profile_picture_link)
            if self.profile_picture_link
            else "/default-profile-pic.jpg"
        )

    def available_accounts(self):
        return [user.info() for user in self.users]

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "profile_picture_link": self._profile_pic(),
            "active_status": self.active_status,
            "created_at": str(self.created_at),
            "recovery_email": self.recovery_email,
            "two_factor_enabled": self.two_factor_enabled,
            "accounts": self.available_accounts(),
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    profile_id = db.Column( db.Integer,  db.ForeignKey("profiles.id"),  nullable=False )
    first_name = db.Column( db.String(50), nullable=False )
    middle_name = db.Column( db.String(50), default="", nullable=True )
    last_name = db.Column( db.String(50), nullable=False )
    created_at = db.Column( db.DateTime, default=datetime.now )
    role = db.Column( db.Enum( "faculty", "head", "president", "administrator" ), default="faculty" )
    active_status = db.Column( db.Boolean, default=True  )
    account_status = db.Column( db.Integer, default=1  )
    position_id = db.Column( db.Integer, db.ForeignKey("positions.id"), default=1 )
    managed_dept_id = db.Column(db.Integer)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=1, nullable=True )

    profile = db.relationship( "Profile", back_populates="users" )
    position = db.relationship( "Position", back_populates="users" )
    department = db.relationship( "Department", back_populates="users" )
    outputs = db.relationship( "Output", back_populates="user" )
    ipcrs = db.relationship( "IPCR", back_populates="user" )
    notifications = db.relationship( "Notification", back_populates="user", cascade="all, delete" )
    assigned_tasks = db.relationship( "Assigned_Task", back_populates="user" )
    task_responses = db.relationship( "TaskResponse", back_populates="submitted_user" )

    def _middle_initial(self):
        return (
            self.middle_name[0].upper() + ". "
            if self.middle_name
            else " "
        )

    def full_name(self):
        return (
            f"{self.first_name} "
            f"{self._middle_initial()}"
            f"{self.last_name}"
        )

    def _profile_pic(self):
        """
        Uses profile picture from linked profile
        """
        return self.profile._profile_pic()

    def info(self):
        return {
            "id": self.id,

            # identity
            "profile_id": self.profile_id,

            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "full_name": self.full_name(),

            # profile-based
            "email": self.profile.email,
            "profile_picture_link": self._profile_pic(),
            "recovery_email": self.profile.recovery_email,
            "two_factor_enabled": self.profile.two_factor_enabled,

            # account-based
            "position": self.position.info(),
            "role": self.role,
            "account_status": self.account_status,
            "department_id": self.department_id,

            "department": (
                self.department.info()
                if self.department
                else "NONE"
            ),

            "department_name": (
                self.department.info()["name"]
                if self.department
                else "NONE"
            ),
        }

    def tasks(self):
        return {
            "assigned_tasks": [
                a.task_info()
                for a in self.assigned_tasks
            ]
        }

    def assigned_task(self):
        return {
            "assigned_tasks": [
                a.assigned_task_info()
                for a in self.assigned_tasks
            ]
        }

    def calculatePerformance(self):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        totals = [
            output.sub_task.calculateAverage()
            for output in self.outputs
            if (
                output.status != 0
                and output.period == settings.current_period_id
            )
        ]

        return (
            sum(totals) / len(totals)
            if totals
            else 0
        )

    def to_dict(self):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        active_ipcrs = []

        for ipcr in self.ipcrs:

            if (
                ipcr.status == 1
                and (
                    settings
                    and ipcr.period == settings.current_period_id
                )
            ):
                active_ipcrs.append(ipcr.to_dict())

        return {
            "id": self.id,
            "profile_id": self.profile_id,

            # personal
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "full_name": self.full_name(),

            # account
            "role": self.role,
            "active_status": self.active_status,
            "account_status": self.account_status,

            # profile auth data
            "email": self.profile.email,
            "password": self.profile.password,
            "profile_picture_link": self._profile_pic(),
            "recovery_email": self.profile.recovery_email,
            "two_factor_enabled": self.profile.two_factor_enabled,

            # dates
            "created_at": str(self.created_at),

            # performance
            "avg_performance": self.calculatePerformance(),

            # organization
            "position": (
                self.position.info()
                if self.position
                else "NONE"
            ),

            "department": (
                self.department.info()
                if self.department
                else "NONE"
            ),

            # ipcr
            "ipcrs": active_ipcrs,
            "ipcrs_count": len(self.ipcrs),

            # outputs
            "main_tasks_count": len(self.outputs),
            "profile_id": self.profile_id
        }