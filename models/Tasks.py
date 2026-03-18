from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import func
from collections import defaultdict
from models.Formula_engine import Formula_Engine


class Assigned_Task(db.Model):
    __tablename__ = "assigned_tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    is_assigned = db.Column(db.Boolean, default=False)
    batch_id = db.Column(db.Text, default="")
    status = db.Column(db.Integer, default=1)
    period = db.Column(db.String(100), nullable=True)
    assigned_quantity = db.Column(db.Integer, default=0)
    assigned_time = db.Column(db.Integer, default=0)
    assigned_mod = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="assigned_tasks")
    main_task = db.relationship("Main_Task", back_populates="assigned_tasks")

    def user_info(self):
        return self.user.info()

    def task_info(self):
        return self.main_task.info()

    def assigned_task_info(self):
        return {
            "period_id": self.period,
            "tasks": self.main_task.info(),
            "is_assigned": self.is_assigned,
        }


class Output(db.Model):
    __tablename__ = "outputs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"))
    batch_id = db.Column(db.Text, default="")
    period = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Integer, default=1)
    assigned_quantity = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="outputs")
    ipcr = db.relationship("IPCR", back_populates="outputs")
    sub_task = db.relationship(
        "Sub_Task", back_populates="output", uselist=False, cascade="all, delete"
    )
    main_task = db.relationship("Main_Task", back_populates="outputs")

    def __init__(
        self,
        user_id,
        main_task_id,
        batch_id,
        ipcr_id,
        period,
        assigned_quantity,
        assigned_time,
        assigned_mod,
    ):
        super().__init__()
        self.user_id = user_id
        self.batch_id = batch_id
        self.ipcr_id = ipcr_id
        self.main_task = Main_Task.query.get(main_task_id)
        self.period = period
        self.assigned_quantity = assigned_quantity

        new_sub_task = Sub_Task(
            mfo=self.main_task.mfo,
            main_task=self.main_task,
            batch_id=batch_id,
            ipcr_id=self.ipcr_id,
            assigned_quantity=assigned_quantity,
            target_acc=assigned_quantity,
            target_time=assigned_time,
            target_mod=assigned_mod,
            period=period,
        )

        db.session.add(new_sub_task)
        db.session.flush()
        self.sub_task = new_sub_task

    def user_info(self):
        return self.user.info()

    def task_info(self):
        return self.main_task.info()

    def sub_task_info(self):
        return self.sub_task.to_dict()


class Assigned_Department(db.Model):
    __tablename__ = "assigned_departments"

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    batch_id = db.Column(db.Text, default="")
    period = db.Column(db.Text, default="")
    task_weight = db.Column(db.Float, default=0.0)
    quantity_formula = db.Column(JSON, default={})
    efficiency_formula = db.Column(JSON, default={})
    timeliness_formula = db.Column(JSON, default={})
    quantity = db.Column(db.Integer, default=1)
    efficiency = db.Column(db.Integer, default=1)
    timeliness = db.Column(db.Integer, default=1)
    enable_formulas = db.Column(db.Boolean, default=False)

    department = db.relationship("Department", back_populates="main_tasks")
    main_task = db.relationship("Main_Task", back_populates="assigned_departments")

    def info(self):
        return {
            "id": self.id,
            "department_id": self.department_id,
            "main_task_id": self.main_task_id,
            "department_name": self.department.name,
            "task_weight": self.task_weight,
            "task_name": self.main_task.mfo,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "department_id": self.department_id,
            "main_task": self.main_task.ipcr_info(),
            "main_task_id": self.main_task_id,
            "department_name": self.department.name,
            "task_weight": self.task_weight,
            "task_name": self.main_task.mfo,
            "assigned_users": self.main_task.get_users_by_dept(self.department_id),
            "task_data": self.main_task.get_performance_by_department(self.department_id),
        }


class Main_Task(db.Model):
    __tablename__ = "main_tasks"

    id = db.Column(db.Integer, primary_key=True)
    mfo = db.Column(db.Text, nullable=False)
    time_description = db.Column(db.Text, nullable=False)
    modification = db.Column(db.Text, nullable=False)
    target_accomplishment = db.Column(db.Text, nullable=False)
    actual_accomplishment = db.Column(db.Text, nullable=False)
    time_taken = db.Column(db.Integer, nullable=False, default=0)
    modifications_done = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Integer, default=1)
    assigned = db.Column(db.Boolean, default=False)
    accomplishment_editable = db.Column(db.Boolean, default=False)
    time_editable = db.Column(db.Boolean, default=False)
    modification_editable = db.Column(db.Boolean, default=False)
    require_documents = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    period = db.Column(db.String(100), nullable=True)
    target_quantity = db.Column(db.Integer, nullable=True, default=0)
    target_efficiency = db.Column(db.Integer, nullable=True, default=0)
    target_deadline = db.Column(db.DateTime, nullable=True)
    target_timeframe = db.Column(db.Integer, nullable=True, default=0)
    timeliness_mode = db.Column(db.String(100), nullable=True, default="timeframe")
    description = db.Column(db.Text, nullable=True)

    category = db.relationship("Category", back_populates="main_tasks")
    assigned_departments = db.relationship("Assigned_Department", back_populates="main_task")
    sub_tasks = db.relationship("Sub_Task", back_populates="main_task", cascade="all, delete")
    outputs = db.relationship("Output", back_populates="main_task", cascade="all, delete")
    assigned_tasks = db.relationship("Assigned_Task", back_populates="main_task", cascade="all, delete")

    def get_task_avg_rating(self):
        rated = [sub.average for sub in self.sub_tasks if sub.average > 0]
        return sum(rated) / len(rated) if rated else 0

    def get_users(self):
        return [assigned.user_info() for assigned in self.assigned_tasks]

    def get_users_by_dept(self, id):
        all_user = []
        for assigned in self.assigned_tasks:
            user_info = assigned.user_info()
            if user_info["department_name"] == "NONE":
                continue
            if str(assigned.user.department.id) == id:
                user_info["assigned_quantity"] = assigned.assigned_quantity
                user_info["assigned_time"] = assigned.assigned_time
                user_info["assigned_mod"] = assigned.assigned_mod
                all_user.append(user_info)
        return all_user

    def get_performance_by_department(self, dept_id):
        from models.PCR import PCR_Service
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        totals = {
            "target_acc": 0,
            "actual_acc": 0,
            "target_time": 0,
            "actual_time": 0,
            "target_mod": 0,
            "actual_mod": 0,
            "rating": {},
        }

        for output in self.outputs:
            if output.user.department.id != dept_id:
                continue
            if output.status != 1 or output.sub_task.status != 1:
                continue

            sub = output.sub_task

            if self.timeliness_mode == "deadline":
                days_late = (sub.actual_deadline - sub.main_task.target_deadline).days
                totals["target_time"] = 1
                totals["actual_time"] += days_late
            else:
                totals["target_time"] = sub.target_time
                totals["actual_time"] += sub.actual_time

            totals["target_acc"] += sub.target_acc
            totals["actual_acc"] += sub.actual_acc
            totals["target_mod"] += sub.target_mod
            totals["actual_mod"] += sub.actual_mod

            quantity = self.quantity
            efficiency = self.efficiency
            timeliness = self.timeliness

            if settings.enable_formula:
                quantity = PCR_Service.compute_quantity_rating(
                    totals["target_acc"], totals["actual_acc"], settings
                )
                efficiency = PCR_Service.compute_efficiency_rating(
                    totals["target_mod"], totals["actual_mod"], settings
                )
                timeliness = PCR_Service.compute_timeliness_rating(
                    totals["target_time"], totals["actual_time"], settings
                )

            totals["rating"] = {
                "quantity": quantity,
                "efficiency": efficiency,
                "timeliness": timeliness,
                "average": PCR_Service.calculateAverage(
                    self.quantity, self.efficiency, self.timeliness
                ),
            }

        return totals

    def ipcr_info(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "actual_acc": self.actual_accomplishment,
            "created_at": str(self.created_at),
            "status": self.status,
            "time": self.time_description,
            "modification": self.modification,
            "period_id": self.period,
            "category": self.category.info(),
            "target_quantity": self.target_quantity,
            "target_efficiency": self.target_efficiency,
            "target_timeframe": self.target_timeframe,
            "timeliness_mode": self.timeliness_mode,
            "target_deadline": str(self.target_deadline) if self.target_deadline else None,
            "required_documents": self.require_documents,
        }

    def info(self):
        return {
            "id": self.id,
            "name": self.mfo,
            "departments": [d.info() for d in self.assigned_departments],
            "department_ids": [d.info()["department_id"] for d in self.assigned_departments],
            "department": [d.info()["department_id"] for d in self.assigned_departments],
            "created_at": str(self.created_at),
            "target_accomplishment": self.target_accomplishment,
            "actual_accomplishment": self.actual_accomplishment,
            "time_measurement": self.time_description,
            "modifications": self.modification,
            "users": [a.user_info() for a in self.assigned_tasks],
            "status": self.status,
            "category": self.category.info() if self.category else "NONE",
            "period_id": self.period,
            "sub_tasks": [sub.info() for sub in self.sub_tasks],
            "require_documents": self.require_documents,
            "target_quantity": self.target_quantity,
            "target_efficiency": self.target_efficiency,
            "target_timeframe": self.target_timeframe,
            "timeliness_mode": self.timeliness_mode,
            "description": self.description,
            "target_deadline": str(self.target_deadline) if self.target_deadline else None,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "period_id": self.period,
            "target_acc": self.target_accomplishment,
            "actual_acc": self.actual_accomplishment,
            "created_at": str(self.created_at),
            "status": self.status,
            "target_quantity": self.target_quantity,
            "target_efficiency": self.target_efficiency,
            "target_timeframe": self.target_timeframe,
            "timeliness_mode": self.timeliness_mode,
            "target_deadline": str(self.target_deadline) if self.target_deadline else None,
            "task_description": self.description,
            "category": self.category_id,
            "sub_tasks": [sub.to_dict() for sub in self.sub_tasks],
        }


class Sub_Task(db.Model):
    __tablename__ = "sub_tasks"

    id = db.Column(db.Integer, primary_key=True)
    mfo = db.Column(db.Text, nullable=False)
    target_acc = db.Column(db.Integer, nullable=True, default=0)
    target_time = db.Column(db.Integer, nullable=True, default=0)
    target_mod = db.Column(db.Integer, nullable=True, default=0)
    actual_acc = db.Column(db.Integer, nullable=True, default=0)
    actual_time = db.Column(db.Integer, nullable=True, default=0)
    actual_mod = db.Column(db.Integer, nullable=True, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Integer, default=1)
    quantity = db.Column(db.Integer, default=0)
    efficiency = db.Column(db.Integer, default=0)
    timeliness = db.Column(db.Integer, default=0)
    average = db.Column(db.Integer, default=0)
    period = db.Column(db.String(100), nullable=True)
    batch_id = db.Column(db.Text, nullable=False)
    assigned_quantity = db.Column(db.Integer, default=0)
    actual_deadline = db.Column(db.DateTime, nullable=True)

    output_id = db.Column(db.Integer, db.ForeignKey("outputs.id"), unique=True)
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default=None)

    output = db.relationship("Output", back_populates="sub_task")
    main_task = db.relationship("Main_Task", back_populates="sub_tasks")
    ipcr = db.relationship("IPCR", back_populates="sub_tasks")
    supporting_documents = db.relationship("Supporting_Document", back_populates="sub_task")

    def _get_formula(self, metric):
        """Returns the formula for the given metric, with department-level override support."""
        from models.System_Settings import System_Settings

        assigned = Assigned_Department.query.filter_by(
            department_id=self.ipcr.user.department.id,
            main_task_id=self.main_task.id,
        ).first()

        if assigned and assigned.enable_formulas:
            return getattr(assigned, f"{metric}_formula")

        settings = System_Settings.get_default_settings()
        return getattr(settings, f"{metric}_formula")

    def calculate_with_override(self, metric, target, actual):
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        assigned_dept_configs = {
            ad.main_task_id: {
                "enable": ad.enable_formulas,
                "quantity": ad.quantity_formula,
                "efficiency": ad.efficiency_formula,
                "timeliness": ad.timeliness_formula,
            }
            for ad in Assigned_Department.query.filter_by(
                department_id=self.ipcr.user.department.id,
                period=settings.current_period_id,
            ).all()
        }

        engine = Formula_Engine()
        dept_cfg = assigned_dept_configs.get(self.main_task_id)
        formula = dept_cfg[metric] if (dept_cfg and dept_cfg["enable"]) else getattr(settings, f"{metric}_formula")

        return engine.compute_rating(formula=formula, target=target, actual=actual)

    def calculateQuantity(self):
        engine = Formula_Engine()
        rating = engine.compute_rating(
            formula=self._get_formula("quantity"),
            target=self.target_acc,
            actual=self.actual_acc,
        )
        self.quantity = rating
        return rating

    def calculateEfficiency(self):
        engine = Formula_Engine()
        rating = engine.compute_rating(
            formula=self._get_formula("efficiency"),
            target=self.target_mod,
            actual=self.actual_mod,
        )
        self.efficiency = rating
        return rating

    def calculateTimeliness(self):
        target = self.target_time
        actual = self.actual_time

        if (
            self.main_task.timeliness_mode == "deadline"
            and self.actual_deadline
            and self.main_task.target_deadline
        ):
            days_late = (self.actual_deadline - self.main_task.target_deadline).days
            actual = 0 if days_late <= 0 else days_late
            target = 1

        engine = Formula_Engine()
        rating = engine.compute_rating(
            formula=self._get_formula("timeliness"),
            target=target,
            actual=actual,
        )
        self.timeliness = rating
        return rating

    def calculateAverage(self):
        q = min(self.quantity, 5)
        e = min(self.efficiency, 5)
        t = min(self.timeliness, 5)
        return (q + e + t) / 3

    def getPositionWeights(self):
        return self.ipcr.user.position.info()

    def getWeight(self):
        weights = self.getPositionWeights()
        category_type = self.main_task.category.type
        weight_map = {
            "Core Function": "core_weight",
            "Support Function": "support_weight",
            "Strategic Function": "strategic_weight",
        }
        return weights.get(weight_map.get(category_type))

    def info(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "created_at": str(self.created_at),
            "status": self.status,
            "batch_id": self.batch_id,
        }

    def to_dict(self):
        from models.System_Settings import System_Settings_Service, System_Settings

        settings = System_Settings.get_default_settings()
        is_rating_period = System_Settings_Service.check_if_rating_period()

        if settings.enable_formula and not is_rating_period:
            if self.main_task.timeliness_mode == "timeframe":
                self.timeliness = self.calculate_with_override(
                    "timeliness", self.target_time, self.actual_time
                )
            elif self.actual_deadline and self.main_task.target_deadline:
                days_late = (self.actual_deadline - self.main_task.target_deadline).days
                self.timeliness = self.calculate_with_override("timeliness", 1, days_late)

            self.efficiency = self.calculate_with_override("efficiency", self.target_mod, self.actual_mod)
            self.quantity = self.calculate_with_override("quantity", self.target_acc, self.actual_acc)

        return {
            "id": self.id,
            "period_id": self.period,
            "title": self.mfo,
            "target_acc": self.target_acc,
            "target_time": self.target_time,
            "target_mod": self.target_mod,
            "actual_acc": self.actual_acc,
            "actual_time": self.actual_time,
            "actual_mod": self.actual_mod,
            "actual_deadline": str(self.actual_deadline) if self.actual_deadline else None,
            "created_at": str(self.created_at),
            "status": self.status,
            "batch_id": self.batch_id,
            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "average": self.calculateAverage(),
            "ipcr": self.ipcr.info(),
            "main_task": self.main_task.ipcr_info(),
            "name": self.mfo,
            "assigned_quantity": self.assigned_quantity,
            "required_documents": self.main_task.require_documents,
        }
