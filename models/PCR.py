from app import db
from datetime import datetime
from utils import FileStorage


class OPCR_Rating(db.Model):
    __tablename__ = "opcr_ratings"

    id = db.Column(db.Integer, primary_key=True)
    mfo = db.Column(db.Text, default="")
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default=None)
    quantity = db.Column(db.Integer, default=0)
    efficiency = db.Column(db.Integer, default=0)
    timeliness = db.Column(db.Integer, default=0)
    average = db.Column(db.Integer, default=0)
    period = db.Column(db.String(100), nullable=True)

    opcr = db.relationship("OPCR", back_populates="opcr_ratings")

    def to_dict(self):
        q = min(self.quantity, 5)
        e = min(self.efficiency, 5)
        t = min(self.timeliness, 5)
        return {
            "id": self.id,
            "mfo": self.mfo,
            "opcr_id": self.opcr_id,
            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "period_id": self.period,
            "average": round((q + e + t) / 3),
        }


class Assigned_PCR(db.Model):
    __tablename__ = "assigned_pcrs"

    id = db.Column(db.Integer, primary_key=True)
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default=None)
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default=None)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=None)
    period = db.Column(db.String(100), nullable=True)

    ipcr = db.relationship("IPCR", back_populates="assigned_pcrs")
    opcr = db.relationship("OPCR", back_populates="assigned_pcrs")
    department = db.relationship("Department", back_populates="assigned_pcrs")


class Supporting_Document(db.Model):
    __tablename__ = "supporting_documents"

    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.Text, default="")
    file_name = db.Column(db.Text, default="")
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default=None)
    sub_task_id = db.Column(db.Integer, db.ForeignKey("sub_tasks.id"), default=None)
    batch_id = db.Column(db.Text, default="")
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    event_date = db.Column(db.DateTime, default=None)
    description = db.Column(db.Text, default="")
    title = db.Column(db.Text, default="")
    period = db.Column(db.String(100), nullable=True)

    ipcr = db.relationship("IPCR", back_populates="supporting_documents")
    sub_task = db.relationship("Sub_Task", back_populates="supporting_documents")

    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
            "object_name": f"documents/{self.file_name}",
            "file_name": self.file_name,
            "batch_id": self.batch_id,
            "period_id": self.period,
            "ipcr_id": self.ipcr_id,
            "status": self.status,
            "download_url": FileStorage.get_file(f"documents/{self.file_name}"),
            "task_name": self.sub_task.main_task.mfo if self.sub_task else "",
            "task_id": self.sub_task.id if self.sub_task else "",
            "main_task_id": self.sub_task.main_task.id if self.sub_task else None,
            "user_name": self.ipcr.user.full_name(),
            "department_name": self.ipcr.user.department.name,
            "created_at": self.created_at,
            "event_date": self.event_date,
            "desc": self.description,
            "title": self.title,
        }


class OPCR_Supporting_Document(db.Model):
    __tablename__ = "opcr_supporting_documents"

    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.Text, default="")
    file_name = db.Column(db.Text, default="")
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default=None)
    batch_id = db.Column(db.Text, default=" ")
    status = db.Column(db.Integer, default=1)
    period = db.Column(db.String(100), nullable=True)

    opcr = db.relationship("OPCR", back_populates="supporting_documents")

    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
            "period_id": self.period,
            "object_name": f"documents/{self.file_name}",
            "file_name": self.file_name,
            "batch_id": self.batch_id,
            "ipcr_id": self.opcr_id,
            "status": self.status,
            "download_url": FileStorage.get_file(f"documents/{self.file_name}"),
        }


class IPCR(db.Model):
    __tablename__ = "ipcr"

    id = db.Column(db.Integer, primary_key=True)
    reviewed_by = db.Column(db.Text, default="")
    rev_position = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    app_position = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    dis_position = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    ass_position = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    fin_position = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")
    con_position = db.Column(db.Text, default="")
    rev_date = db.Column(db.DateTime, default=None)
    app_date = db.Column(db.DateTime, default=None)
    dis_date = db.Column(db.DateTime, default=None)
    ass_date = db.Column(db.DateTime, default=None)
    fin_date = db.Column(db.DateTime, default=None)
    con_date = db.Column(db.DateTime, default=None)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default=None)
    isMain = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=1)
    form_status = db.Column(db.Text, default="draft")
    batch_id = db.Column(db.Text, default="")
    period = db.Column(db.String(100), nullable=True)

    user = db.relationship("User", back_populates="ipcrs")
    opcr = db.relationship("OPCR", back_populates="ipcrs")
    sub_tasks = db.relationship("Sub_Task", back_populates="ipcr", cascade="all, delete")
    outputs = db.relationship("Output", back_populates="ipcr", cascade="all, delete")
    supporting_documents = db.relationship("Supporting_Document", back_populates="ipcr", cascade="all, delete")
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates="ipcr", cascade="all, delete")

    def count_sub_tasks(self):
        return len(self.sub_tasks)

    def info(self):
        return {
            "id": self.id,
            "user": self.user_id,
            "core_weight": self.user.position.core_weight,
            "strategic_weight": self.user.position.strategic_weight,
            "support_weight": self.user.position.support_weight,
        }

    def department_info(self):
        return {
            "id": self.id,
            "user": self.user.info(),
            "department_id": self.user.department_id,
            "created_at": str(self.created_at),
            "form_status": self.form_status,
            "isMain": self.isMain,
            "batch_id": self.batch_id,
            "status": self.status,
        }

    def _middle_initial(self, user):
        return user.middle_name[0] + ". " if user.middle_name else " "

    def _slot(self, name, position):
        return {"name": name, "position": position, "date": ""}

    def to_dict(self):
        from models.System_Settings import System_Settings
        from models.User import User

        settings = System_Settings.get_default_settings()
        president = settings.current_president_fullname or ""
        mayor = settings.current_mayor_fullname or ""
        user = self.user
        mi = self._middle_initial(user)
        full = f"{user.first_name} {mi}{user.last_name}"

        dept_head = User.query.filter_by(department_id=user.department_id, role="head").first()
        dmi = self._middle_initial(dept_head) if dept_head else " "
        head_full = f"{dept_head.first_name} {dmi}{dept_head.last_name}" if dept_head else ""
        head_pos = dept_head.position.name if dept_head else ""

        if user.role == "faculty":
            review = self._slot(head_full, head_pos)
            approve = self._slot(president, "College President")
            discuss = self._slot(full, user.position.name)
            assess = self._slot(head_full, head_pos)
            final = self._slot(president, "College President")
        elif user.role in ("head", "administrator"):
            review = self._slot(president, "College President")
            approve = self._slot(president, "College President")
            discuss = self._slot(full, user.position.name)
            assess = self._slot(president, "College President")
            final = self._slot(president, "College President")
        else:  # president
            review = self._slot(president, "College President")
            approve = self._slot(president, "College President")
            discuss = self._slot(president, "College President")
            assess = self._slot(president, "College President")
            final = self._slot(president, "College President")

        db.session.commit()

        return {
            "id": self.id,
            "user": self.user_id,
            "user_info": user.info(),
            "sub_tasks": [t.to_dict() for t in self.sub_tasks],
            "sub_tasks_count": self.count_sub_tasks(),
            "created_at": str(self.created_at),
            "form_status": self.form_status,
            "isMain": self.isMain,
            "batch_id": self.batch_id,
            "status": self.status,
            "period_id": self.period,
            "review": review,
            "approve": approve,
            "discuss": discuss,
            "assess": assess,
            "final": final,
            "confirm": self._slot(mayor, "PMT Chairperson"),
        }


class OPCR(db.Model):
    __tablename__ = "opcr"

    id = db.Column(db.Integer, primary_key=True)
    reviewed_by = db.Column(db.Text, default="")
    rev_position = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    app_position = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    dis_position = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    ass_position = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    fin_position = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")
    con_position = db.Column(db.Text, default="")
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    isMain = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=1)
    form_status = db.Column(db.Text, default="draft")
    created_at = db.Column(db.DateTime, default=datetime.now)
    rev_date = db.Column(db.DateTime, default=None)
    app_date = db.Column(db.DateTime, default=None)
    dis_date = db.Column(db.DateTime, default=None)
    ass_date = db.Column(db.DateTime, default=None)
    fin_date = db.Column(db.DateTime, default=None)
    con_date = db.Column(db.DateTime, default=None)
    period = db.Column(db.String(100), nullable=True)

    department = db.relationship("Department", back_populates="opcrs")
    supporting_documents = db.relationship("OPCR_Supporting_Document", back_populates="opcr", cascade="all, delete")
    opcr_ratings = db.relationship("OPCR_Rating", back_populates="opcr", cascade="all, delete")
    ipcrs = db.relationship("IPCR", back_populates="opcr", cascade="all, delete")
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates="opcr", cascade="all, delete")

    def count_ipcr(self):
        return len(self.ipcrs)

    def _slot(self, name, position):
        return {"name": name, "position": position, "date": ""}

    def to_dict(self):
        from models.System_Settings import System_Settings
        from models.User import User

        settings = System_Settings.get_default_settings()
        president = settings.current_president_fullname or ""
        mayor = settings.current_mayor_fullname or ""

        head = User.query.filter_by(department_id=self.department_id, role="head").first()
        mi = head.middle_name[0] + ". " if head and head.middle_name else " "
        head_full = f"{head.first_name} {mi}{head.last_name}" if head else ""
        head_pos = head.position.name if head else ""

        self.reviewed_by = head_full
        self.rev_position = head_pos
        self.approved_by = president
        self.app_position = "College President"
        self.discussed_with = head_full
        self.dis_position = head_pos
        self.assessed_by = president
        self.ass_position = "College President"
        self.final_rating_by = president
        self.fin_position = "College President"
        self.confirmed_by = mayor
        self.con_position = "PMT Chairperson"
        db.session.commit()

        return {
            "id": self.id,
            "ipcr_count": self.count_ipcr(),
            "form_status": self.form_status,
            "created_at": str(self.created_at),
            "period_id": self.period,
            "review": self._slot(self.reviewed_by, self.rev_position),
            "approve": self._slot(self.approved_by, self.app_position),
            "discuss": self._slot(self.discussed_with, self.dis_position),
            "assess": self._slot(self.assessed_by, self.ass_position),
            "final": self._slot(self.final_rating_by, self.fin_position),
            "confirm": self._slot(self.confirmed_by, self.con_position),
            "department": self.department.name,
            "status": self.status,
        }
