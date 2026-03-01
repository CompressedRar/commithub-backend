from app import db
from app import socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.User import User, Notification_Service
from sqlalchemy import func, case
from collections import defaultdict
from simpleeval import SimpleEval, NameNotDefined


class Formula_Engine:

    def _safe_eval(self, expression, variables):
        s = SimpleEval()
        s.names = variables
        s.functions = {}
        return float(s.eval(expression))


    def validate_formula(self, formula):
        """
        Validates formula structure, expression, and rating rules.
        Raises ValueError if invalid.
        """

        # ---- 1. Structure check ----
        if "expression" not in formula:
            raise ValueError("Missing 'expression'")

        if "rating_scale" not in formula:
            raise ValueError("Missing 'rating_scale'")

        if not isinstance(formula["rating_scale"], dict):
            raise ValueError("'rating_scale' must be an object")

        # ---- 2. Validate expression safely ----
        self._validate_expression(formula["expression"])

        # ---- 3. Validate rating rules ----
        self._validate_rating_scale(formula["rating_scale"])

        # ---- 4. Test evaluation with sample values ----
        self._dry_run(formula)

        return "Valid JSON"
    
    def _dry_run(self, formula):
        test_cases = [
            {"actual": 0, "target": 0},
            {"actual": 1, "target": 1},
            {"actual": 5, "target": 10},
            {"actual": 10, "target": 5}
        ]

        for case in test_cases:
            try:
                calc = self._safe_eval(formula["expression"], case)
                matched = False

                for rules in formula["rating_scale"].values():
                    if self._match_rules(calc, rules):
                        matched = True
                        break

                if not matched:
                    raise ValueError("No rating matched for test case")
            except Exception as e:
                raise ValueError(f"Dry run failed: {str(e)}")



    def _validate_expression(self, expression):
        s = SimpleEval()
        s.names = {
            "actual": 1,
            "target": 1
        }
        s.functions = {}

        try:
            s.eval(expression)
        except Exception as e:
            raise ValueError(f"Invalid expression: {str(e)}")
        
    def _validate_rating_scale(self, rating_scale):
        allowed_ops = {"lt", "lte", "gt", "gte", "eq"}

        for rating, rules in rating_scale.items():
            if not rating.isdigit():
                raise ValueError(f"Invalid rating key: {rating}")

            if not isinstance(rules, dict):
                raise ValueError(f"Rules for rating {rating} must be an object")

            for op, value in rules.items():
                if op not in allowed_ops:
                    raise ValueError(f"Invalid operator '{op}' in rating {rating}")
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Invalid value for rating {rating}")
                
    def _validate_no_overlap(self, rating_scale):
        ranges = []

        for rating, rules in rating_scale.items():
            low = float("-inf")
            high = float("inf")

            if "gt" in rules:
                low = rules["gt"]
            if "gte" in rules:
                low = rules["gte"]

            if "lt" in rules:
                high = rules["lt"]
            if "lte" in rules:
                high = rules["lte"]

            ranges.append((low, high, rating))

        ranges.sort()

        for i in range(len(ranges) - 1):
            curr_high = ranges[i][1]
            next_low = ranges[i + 1][0]

            if curr_high > next_low:
                raise ValueError(
                    f"Rating ranges overlap between {ranges[i][2]} and {ranges[i + 1][2]}"
                )



    def compute_rating(self, formula, target, actual):
        expre = formula["expression"]
        rating_scale = formula["rating_scale"]

        s = SimpleEval()

        s.names = {
            "target": target,
            "actual": actual
        }

        s.functions = {}

        try:
            calc = float(s.eval(expre))            
        
        except Exception as e:
            raise ValueError(f"Invalid Expression : {str(e)}")
        
        for rating, rules in rating_scale.items():
            if self._match_rules(calc, rules):
                return int(rating)
    

    def _match_rules(self, calc, rules):
        if "eq" in rules and calc != rules["eq"]:
            return False
        if "lt" in rules and not calc < rules["lt"]:
            return False
        if "lte" in rules and not calc <= rules["lte"]:
            return False
        if "gt" in rules and not calc > rules["gt"]:
            return False
        if "gte" in rules and not calc >= rules["gte"]:
            return False
        return True

class Assigned_Task(db.Model):
    __tablename__ = "assigned_tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    is_assigned = db.Column(db.Boolean, default = False)

    batch_id = db.Column(db.Text, default = "")

    user = db.relationship("User", back_populates = "assigned_tasks")
    main_task = db.relationship("Main_Task", back_populates = "assigned_tasks")

    status = db.Column(db.Integer, default = 1)

    period = db.Column(db.String(100), nullable=True)

    assigned_quantity = db.Column(db.Integer, default = 0)

    def user_info(self):
        return self.user.info()
     
    def task_info(self):
        return self.main_task.info()
    
    def assigned_task_info(self):
        return {
            "period_id": self.period,
            "tasks": self.main_task.info(),
            "is_assigned": self.is_assigned
        }

class Output(db.Model):
    __tablename__ = "outputs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"))

    batch_id = db.Column(db.Text, default = "")
    
    user = db.relationship("User", back_populates = "outputs")
    ipcr = db.relationship("IPCR", back_populates = "outputs")
    sub_task = db.relationship("Sub_Task", back_populates="output", uselist=False, cascade="all, delete")
    main_task = db.relationship("Main_Task", back_populates = "outputs")

    period = db.Column(db.String(100), nullable=True)

    status = db.Column(db.Integer, default = 1)

    assigned_quantity = db.Column(db.Integer, default = 0)

    def __init__(self, user_id, main_task_id, batch_id, ipcr_id, period, assigned_quantity):
        super().__init__()
        self.user_id = user_id
        self.batch_id = batch_id
        self.ipcr_id = ipcr_id
        self.main_task = Main_Task.query.get(main_task_id)
        self.period = period
        self.assigned_quantity = assigned_quantity
        

        # Create subtask automatically by copying from main task
        new_sub_task = Sub_Task(
            mfo=self.main_task.mfo,
            main_task=self.main_task,
            batch_id = batch_id,
            ipcr_id = self.ipcr_id,
            assigned_quantity = assigned_quantity,
            target_acc=assigned_quantity,
            period=period
        )             
       

        db.session.add(new_sub_task)
        db.session.flush()  # make sure sub_task.id is available

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

    batch_id = db.Column(db.Text, default = "")
    period = db.Column(db.Text, default ="")
    
    department = db.relationship("Department", back_populates = "main_tasks")
    main_task = db.relationship("Main_Task", back_populates = "assigned_departments")

    task_weight = db.Column(db.Float, default = 0.0)

    quantity_formula = db.Column(JSON, default={})
    efficiency_formula = db.Column(JSON, default={})
    timeliness_formula = db.Column(JSON, default={})

    quantity = db.Column(db.Integer)
    efficiency = db.Column(db.Integer)
    timeliness = db.Column(db.Integer)

    enable_formulas = db.Column(db.Boolean, default=False)


    def info(self):
        return {
            "id": self.id,
            "department_id": self.department_id,
            "main_task_id": self.main_task_id,
            "department_name": self.department.name,
            "task_weight": self.task_weight,
            "task_name": self.main_task.mfo
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
            "task_data": self.main_task.get_performance_by_department(self.department_id)
        }


class Main_Task(db.Model):
    __tablename__ = "main_tasks"
    id = db.Column(db.Integer, primary_key=True)
    
    mfo = db.Column(db.Text, nullable=False)    

    time_description = db.Column(db.Text, nullable=False)
    modification = db.Column(db.Text, nullable=False)
    
    target_accomplishment = db.Column(db.Text, nullable=False)
    actual_accomplishment = db.Column(db.Text, nullable=False)

    time_taken = db.Column(db.Integer, nullable=False, default = 0)
    modifications_done = db.Column(db.Integer, nullable=False, default = 0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Integer, default=1)
    assigned = db.Column(db.Boolean, default=False)

    accomplishment_editable = db.Column(db.Boolean, default=False)
    time_editable = db.Column(db.Boolean, default=False)
    modification_editable = db.Column(db.Boolean, default=False)

    require_documents = db.Column(db.Boolean, default=False)
    #one category and one department
    
    assigned_departments = db.relationship("Assigned_Department", back_populates="main_task")

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates = "main_tasks")
    sub_tasks = db.relationship("Sub_Task", back_populates = "main_task", cascade = "all, delete")
    outputs = db.relationship("Output", back_populates="main_task", cascade = "all, delete")
    assigned_tasks = db.relationship("Assigned_Task", back_populates="main_task", cascade = "all, delete")
    period = db.Column(db.String(100), nullable=True)

    target_quantity = db.Column(db.Integer, nullable=True, default = 0)
    target_efficiency = db.Column(db.Integer, nullable=True, default = 0)
    
    target_deadline = db.Column(db.DateTime, nullable=True)
    target_timeframe = db.Column(db.Integer, nullable=True, default = 0)  #in days / hours / minutes
    timeliness_mode = db.Column(db.String(100), nullable=True, default = "timeframe")  #timeframe or deadline

    description = db.Column(db.Text, nullable=True)

    def get_task_avg_rating(self):
        total = 0
        count = 0
        for sub in self.sub_tasks:
            if sub.average > 0:
                total += sub.average
                count += 1
        if count == 0:
            return 0
        return total / count


    def get_users(self):
        all_user = []
        for assigned in self.assigned_tasks:            
            all_user.append(assigned.user_info())
        
        return all_user
    
    def get_users_by_dept(self, id):
        all_user = []
        for assigned in self.assigned_tasks:

            user_info = assigned.user_info() 
            user_info["assigned_quantity"] = assigned.assigned_quantity
            
            if assigned.user_info()["department_name"] == "NONE": 
                continue

            if  str(assigned.user.department.id) == id:
                print("MAY NAHANAP")
                all_user.append(user_info)
        
        return all_user
    
    def get_performance_by_department(self, dept_id):
        all_sub_tasks = {
            "target_acc": 0,
            "actual_acc": 0,
            "target_time":0,
            "actual_time": 0,
            "target_mod": 0,
            "actual_mod": 0,
            "rating":{}
        }
        from models.PCR import PCR_Service 
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings() 

        for output in self.outputs:
            user_department = output.user.department.id

            if user_department == dept_id and output.status == 1 and output.sub_task.status == 1:
                if self.timeliness_mode == "deadline":
                    from datetime import datetime
                                   
    
                    target_working_days = ""
                    actual_working_days = ""

                    days_late = (output.sub_task.actual_deadline - output.sub_task.main_task.target_deadline).days

                    actual_working_days = days_late
                    target_working_days = 1  

                    all_sub_tasks["target_acc"] += output.sub_task.target_acc
                    all_sub_tasks["target_mod"] += output.sub_task.target_mod
                    all_sub_tasks["target_time"] = target_working_days

                    all_sub_tasks["actual_acc"] += output.sub_task.actual_acc
                    all_sub_tasks["actual_mod"] += output.sub_task.actual_mod
                    all_sub_tasks["actual_time"] += actual_working_days

                    
                else:

                    all_sub_tasks["target_acc"] += output.sub_task.target_acc
                    all_sub_tasks["target_mod"] += output.sub_task.target_mod
                    all_sub_tasks["target_time"] = output.sub_task.target_time

                    all_sub_tasks["actual_acc"] += output.sub_task.actual_acc
                    all_sub_tasks["actual_mod"] += output.sub_task.actual_mod
                    all_sub_tasks["actual_time"] += output.sub_task.actual_time
                
                quantity = self.quantity
                efficiency = self.efficiency
                timeliness = self.timeliness
                
                if settings.enable_formula:
                    quantity = PCR_Service.compute_quantity_rating(all_sub_tasks['target_acc'], all_sub_tasks['actual_acc'], settings)
                    efficiency = PCR_Service.compute_efficiency_rating(all_sub_tasks['target_mod'], all_sub_tasks['actual_mod'], settings)
                    timeliness = PCR_Service.compute_timeliness_rating(all_sub_tasks['target_time'], all_sub_tasks['actual_time'], settings)

                rating_data = {
                        "quantity": quantity,
                        "efficiency": efficiency,
                        "timeliness": timeliness,
                        "average": PCR_Service.calculateAverage(self.quantity, self.efficiency, self.timeliness)
                    }
                
                all_sub_tasks["rating"] = rating_data


        return all_sub_tasks



    
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
            "required_documents": self.require_documents
        }

    def info(self):
        return {
            "id" : self.id,
            "name": self.mfo,
            "departments": [depts.info() for depts in self.assigned_departments],
            "department_ids": [depts.info()["department_id"] for depts in self.assigned_departments],
            "department": [depts.info()["department_id"] for depts in self.assigned_departments],
            "created_at": str(self.created_at),
            "target_accomplishment": self.target_accomplishment,
            "actual_accomplishment": self.actual_accomplishment,
            "time_measurement" : self.time_description,
            "modifications": self.modification,
            "users": [assigned.user_info() for assigned in self.assigned_tasks],
            "status": self.status,
            "category": self.category.info() if self.category else "NONE",
            "period_id": self.period,
            "sub_tasks": [sub.info() for sub in self.sub_tasks],
            "require_documents": self.require_documents,
            "target_quantity": self.target_quantity,
            "target_efficiency": self.target_efficiency,
            "target_timeframe": self.target_timeframe,
            "timeliness_mode": self.timeliness_mode,
            "description":self.description,
            
            "target_deadline": str(self.target_deadline) if self.target_deadline else None
            
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
            "task_description":self.description,

            "category": self.category_id,
            "sub_tasks": [sub_task.to_dict() for sub_task in self.sub_tasks],
        }
    
class Sub_Task(db.Model):
    __tablename__ = "sub_tasks"
    id = db.Column(db.Integer, primary_key=True)
    
    mfo = db.Column(db.Text, nullable=False)

    target_acc = db.Column(db.Integer, nullable = True, default = 0)
    target_time = db.Column(db.Integer, nullable = True, default = 0)
    target_mod = db.Column(db.Integer, nullable = True, default = 0)

    actual_acc = db.Column(db.Integer, nullable = True, default = 0)
    actual_time = db.Column(db.Integer, nullable = True, default = 0)
    actual_mod = db.Column(db.Integer, nullable = True, default = 0)

    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Integer, default=1)
    
    quantity = db.Column(db.Integer, default = 0)
    efficiency = db.Column(db.Integer, default = 0)
    timeliness = db.Column(db.Integer, default = 0)
    average = db.Column(db.Integer, default = 0)

    output_id = db.Column(db.Integer, db.ForeignKey("outputs.id"), unique=True)
    output = db.relationship("Output", back_populates="sub_task")

    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    main_task = db.relationship("Main_Task", back_populates="sub_tasks")

    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default = None)
    ipcr = db.relationship("IPCR", back_populates="sub_tasks")   

    supporting_documents = db.relationship("Supporting_Document", back_populates="sub_task") 

    
    period = db.Column(db.String(100), nullable=True)
    batch_id = db.Column(db.Text, nullable=False)
    assigned_quantity = db.Column(db.Integer, default = 0)


    actual_deadline = db.Column(db.DateTime, nullable=True)

    

    """def compute_rating(self, formula, target, actual):
        expression = formula["expression"]

        # Replacing formula variables safely
        calc = eval(expression, {"__builtins__": None}, {
            "target": target,
            "actual": actual
        })

        for rating, condition in formula["rating_scale"].items():
            if eval(condition, {"__builtins__": None}, {"calc": calc}):
                return int(rating)

        return 0"""
    
    def _get_formula(self, metric):
        """
        metric: 'quantity', 'efficiency', 'timeliness'
        """
        from models.Tasks import Assigned_Department
        from models.System_Settings import System_Settings

        # Try department-level override
        assigned = Assigned_Department.query.filter_by(
            department_id=self.ipcr.user.department.id,
            main_task_id=self.main_task.id
        ).first()

        if assigned and assigned.enable_formulas:
            return getattr(assigned, f"{metric}_formula")

        # Fallback to system settings
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
                "weight": float(ad.task_weight / 100)
            }
            for ad in Assigned_Department.query.filter_by(
                department_id=self.ipcr.user.department.id,
                period = settings.current_period_id
            ).all()
        }

        engine = Formula_Engine()
        dept_cfg = assigned_dept_configs.get(self.main_task_id)

        if dept_cfg and dept_cfg["enable"]:
            formula = dept_cfg[metric]
        else:
            formula = getattr(settings, f"{metric}_formula")

        return engine.compute_rating(
                formula=formula,
                target=target,
                actual=actual
        )


    def calculateQuantity(self):
        target = self.assigned_quantity
        actual = self.actual_acc

        engine = Formula_Engine()
        formula = self._get_formula("quantity")

        rating = engine.compute_rating(
            formula=formula,
            target=target,
            actual=actual
        )

        self.quantity = rating
        return rating


    def calculateEfficiency(self):
        target = self.main_task.target_efficiency
        actual = self.actual_mod

        engine = Formula_Engine()
        formula = self._get_formula("efficiency")

        rating = engine.compute_rating(
            formula=formula,
            target=target,
            actual=actual
        )

        self.efficiency = rating
        return rating

    
    def calculateTimeliness(self):
        target = self.main_task.target_timeframe    
        actual = self.actual_time

        if self.main_task.timeliness_mode == "deadline" and self.actual_deadline and self.main_task.target_deadline:
            days_late = (self.actual_deadline - self.main_task.target_deadline).days
            actual = 0 if days_late <= 0 else days_late
            target = 1  # no late days expected

        engine = Formula_Engine()
        
        formula = self._get_formula("timeliness")

        rating = engine.compute_rating(
            formula=formula,
            target=target,
            actual=actual
        )

        self.timeliness = rating
        return rating

    
    def calculateAverage(self):
        
        q = 5 if self.quantity > 5 else self.quantity
        e = 5 if self.efficiency > 5 else self.efficiency
        t = 5 if self.timeliness > 5 else self.timeliness
        calculations = q + e + t
        result = calculations/3
        return result
    
    def info(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "created_at": str(self.created_at),
            "status": self.status,
            "batch_id": self.batch_id
        }
    
    def getPositionWeights(self):
        return self.ipcr.user.position.info()
    
    def getWeight(self):
        weights = self.getPositionWeights()
        if self.main_task.category.type == "Core Function":
            return weights["core_weight"]
        elif self.main_task.category.type == "Support Function":
            return weights["support_weight"]
        elif self.main_task.category.type == "Strategic Function":
            return weights["strategic_weight"]


    def to_dict(self):

        from models.System_Settings import System_Settings_Service, System_Settings
        settings = System_Settings.get_default_settings()

        if settings.enable_formula:
            timeliness = 0

            if self.main_task.timeliness_mode == "timeframe" and not System_Settings_Service.check_if_rating_period():
                timeliness = self.calculate_with_override("timeliness", self.main_task.target_timeframe, self.actual_time)
            else:
                if self.actual_deadline and self.main_task.target_deadline:
                    days_late = (
                        self.actual_deadline - self.main_task.target_deadline
                    ).days
                    actual_working_days = days_late
                    target_working_days = 1
                    timeliness = self.calculate_with_override("timeliness", target_working_days, actual_working_days)
                else:
                    timeliness = self.timeliness
            
            self.timeliness = timeliness if not System_Settings_Service.check_if_rating_period() else self.timeliness
            self.efficiency = self.calculate_with_override("efficiency", self.main_task.target_efficiency, self.actual_mod) if not System_Settings_Service.check_if_rating_period() else self.efficiency
            self.quantity = self.calculate_with_override("quantity", self.main_task.target_quantity, self.actual_acc) if not System_Settings_Service.check_if_rating_period() else self.quantity
      
        return {
            "id": self.id,
            "period_id": self.period,
            "title": self.mfo,
            "target_acc": self.assigned_quantity,
            "target_time": self.main_task.target_timeframe,
            "target_mod": self.main_task.target_efficiency,
            "actual_acc": self.actual_acc,
            "actual_time": self.actual_time,
            "actual_mod": self.actual_mod,
            "actual_deadline": str(self.actual_deadline) if self.actual_deadline else None,
            "created_at": str(self.created_at),
            "status": self.status,
            "batch_id": self.batch_id,

            "quantity":  self.quantity, 
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "average": self.calculateAverage(),        

            "ipcr": self.ipcr.info(),
            "main_task": self.main_task.ipcr_info(),
            "name":self.mfo,
            "assigned_quantity": self.assigned_quantity,
            "required_documents": self.main_task.require_documents
        }
  


class Tasks_Service():

    def test_ipcr():
        from models.PCR import IPCR
        ipcr = IPCR.query.get(9)
        return jsonify(ipcr.to_dict()), 200
    def get_main_tasks():
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()

        try:
            all_main_tasks = Main_Task.query.filter_by(status = 1, period = settings.current_period_id).all()

            
            converted_main_tasks = [main_task.info() for main_task in all_main_tasks] if len(all_main_tasks) != 0 else []
            print("LAHAT ng Tasks", converted_main_tasks)
            return jsonify(converted_main_tasks), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_main_task(id):
        try:
            main_task = Main_Task.query.get(id)
            converted_main_task = main_task.info()
        
            return jsonify(converted_main_task), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_assigned_department(dept_id):
        try:

            from models.System_Settings import System_Settings
            current_settings = System_Settings.get_default_settings()

            found_assigned_department = Assigned_Department.query.filter_by(department_id = dept_id, period = current_settings.current_period_id).all()
            converted = []
            for assigned_department in found_assigned_department:
                if assigned_department.main_task.status:
                    print("active")
                    converted.append(assigned_department.info())

            return jsonify(converted), 200
         
        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_assigned_departments_for_opcr(dept_id):
        try:

            from models.System_Settings import System_Settings
            current_settings = System_Settings.get_default_settings()

            found_assigned_department = Assigned_Department.query.filter_by(department_id = dept_id, period = current_settings.current_period_id, status = 1).all()
            
            converted = []
            for assigned_department in found_assigned_department:
                if assigned_department.main_task.status:
                    print("active")
                    converted.append(assigned_department.info())
            

            return jsonify(converted), 200
         
        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        

    def update_tasks_weights(data):
        try:
            for assigned_task_id, weight in dict(data).items():
                found_task = Assigned_Department.query.get(assigned_task_id)
                found_task.task_weight = weight

            db.session.commit()

            socketio.emit("weight", "update")

            return jsonify(message="Weights are successfully updated."), 200
        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

        
    def create_main_task(data):
        try:
            print("creating task right now")
            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            
            
            new_main_task = Main_Task(
                mfo = data["task_name"],
                target_accomplishment = data["task_desc"],
                actual_accomplishment = data["past_task_desc"],
                accomplishment_editable =  int(data["accomplishment_editable"]),
                time_editable =  int(data["time_editable"]),
                modification_editable =  int(data["modification_editable"]),
                time_description = data["time_measurement"],
                modification =  data["modification"],
                category_id = int(data["id"]),
                require_documents = data["require_documents"] if "require_documents" in data else False,
                period = current_settings.current_period_id if current_settings else None,
                description = data["description"],

                target_quantity = data["target_quantity"] if "target_quantity" in data else 0,
                target_efficiency = data["target_efficiency"] if "target_efficiency" in data else 0,
                target_timeframe = data["target_timeframe"] if "target_timeframe" in data else 0,
                target_deadline = datetime.strptime(data["target_deadline"], "%Y-%m-%d") if "target_deadline" in data and data["target_deadline"] != "" else None,
                timeliness_mode = data["timeliness_mode"] if "timeliness_mode" in data else "timeframe"                
            )
            db.session.add(new_main_task)

            db.session.flush()

            """
                department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
                main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))

                batch_id = db.Column(db.Text, default = "")
                period = db.Column(db.Text, default ="")
            """

            print("fetched dept", data["department"])

            if data["department"]:

                for department in data["department"].split(","):
                    print("Department ID", department)
                    new_assigned_department = Assigned_Department(
                        department_id = department,
                        main_task_id = new_main_task.id,
                        period = current_settings.current_period_id if current_settings else None,
                    )

                    db.session.add(new_assigned_department)

            print("registered task")
            Notification_Service.notify_department(dept_id=data["department"], msg="A new task has been added to the department.")
            Notification_Service.notify_presidents( msg="A new task has been added.")
            Notification_Service.notify_administrators( msg="A new task has been added.")

            
            db.session.commit()
            return jsonify(message="Task successfully created."), 200
        
        except IntegrityError as e:
            db.session.rollback()
            print(str(e), "Integrity")
            return jsonify(error="Task already exists"), 400
        
        except DataError as e:
            db.session.rollback()
            print(str(e), "data error")
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e), "operational")
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e), "unknown")
            return jsonify(error=str(e)), 500
        
    def update_task_info(data):
        try:
            found_task = Main_Task.query.get(data["id"])

            all_previous_department = found_task.info()["department_ids"]
            updated_departments = [int(i) for i in data["department"].split(",")] if data["department"] else []
        

            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            for current_id in updated_departments:
                print(current_id)
                if int(current_id) not in all_previous_department:
                    new_assigned_department = Assigned_Department(
                        main_task_id = int(data["id"]),
                        department_id = int(current_id),
                        period = current_settings.current_period_id

                    )
                    db.session.add(new_assigned_department)

            for current_id in all_previous_department:
                print(current_id)
                if int(current_id) not in updated_departments:
                    found_assigned_department = Assigned_Department.query.filter_by(main_task_id = int(data["id"]), department_id = int(current_id)).first()
                    db.session.delete(found_assigned_department)

                    found_assigned_tasks = Assigned_Task.query.filter_by(main_task_id = int(data["id"])).all()

                    for ass_tasks in found_assigned_tasks:
                        print("meron ass task")
                        if ass_tasks.user.department.id == int(current_id):
                            db.session.delete(Assigned_Task.query.get(ass_tasks.id))

                        found_output = Output.query.filter_by(user_id = ass_tasks.user.id, main_task_id = id).all()
                        for output in found_output:
                            db.session.delete(output)



            if found_task == None:
                return jsonify(message="No output with that ID"), 400
            
            if len(data) == 0:
                return jsonify(message="You must submit data to update fields"), 400

            if "name" in data:
                found_task.mfo = data["name"]


            if "target_accomplishment" in data:
                found_task.target_accomplishment = data["target_accomplishment"]

            if "description" in data:
                found_task.description = data["description"]

            if "actual_accomplishment" in data:
                found_task.actual_accomplishment = data["actual_accomplishment"]

            if "time_description" in data:
                found_task.time_description = data["time_description"]

            if "modification" in data:
                found_task.modification = data["modification"]

            if "require_documents" in data:
                print("required documents")
                found_task.require_documents = True if data["require_documents"] == "true" else False

            if "target_quantity" in data:
                print("target quantity detected", data["target_quantity"])
                found_task.target_quantity = data["target_quantity"]

            if "target_efficiency" in data:
                print("target efficiency detected", data["target_efficiency"])
                found_task.target_efficiency = data["target_efficiency"]

            if "timeliness_mode" in data:
                print("timeliness mode detected", data["timeliness_mode"])
                found_task.timeliness_mode = data["timeliness_mode"]

                if data["timeliness_mode"] == "timeframe":
                    if "target_timeframe" in data:
                        print("target timeframe detected", data["target_timeframe"])
                        found_task.target_timeframe = data["target_timeframe"]
                else:
                    if "target_deadline" in data:
                        print("target deadline detected", data["target_deadline"])
                        found_task.target_deadline = datetime.strptime(data["target_deadline"], "%Y-%m-%d") if data["target_deadline"] != "" else None
            

            if "status" in data:
                print("status detected", data["status"])
                found_task.status = data["status"]

            socketio.emit("category", "update")

            db.session.commit()
            Notification_Service.notify_everyone(msg=f"The task: {found_task.mfo} has been updated.")
            return jsonify(message = "Task successfully updated."), 200
        
        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Data does not exists"), 400
        
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def get_all_tasks_count():
        tasks_count = db.session.query(func.count(Main_Task.id)).scalar()        
        return jsonify(message = {
            "count":tasks_count
        })
    
    def assign_user(task_id, user_id, assigned_quantity):
        try:
            #search ko muna lahat ng assigned task kung existing na siya
            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            from models.PCR import IPCR, PCR_Service

            existing_ipcr = IPCR.query.filter_by(user_id=user_id, period=current_settings.current_period_id if current_settings else None).first()   

            
            main_task = Main_Task.query.get(task_id)
            
           

            if existing_ipcr:
                
                Assigned_Task.query.filter_by(user_id = user_id, main_task_id = task_id).delete()
                db.session.flush()
                
                new_assigned_task = Assigned_Task(user_id = user_id, main_task_id = task_id, is_assigned = True, period = current_settings.current_period_id if current_settings else None, assigned_quantity = assigned_quantity)
                db.session.add(new_assigned_task)
                db.session.flush()
                db.session.commit()

                Sub_Task.query.filter_by(main_task_id = task_id, batch_id = existing_ipcr.batch_id, ipcr_id=existing_ipcr.id, period = current_settings.current_period_id if current_settings else None).delete()
                db.session.commit()

                Output.query.filter_by(user_id = user_id, main_task_id = task_id, batch_id = existing_ipcr.batch_id, ipcr_id=existing_ipcr.id, period = current_settings.current_period_id if current_settings else None).delete()
                db.session.commit()
                new_output = Output(user_id = user_id, main_task_id = task_id, batch_id = existing_ipcr.batch_id if current_settings else "", ipcr_id=existing_ipcr.id, period = current_settings.current_period_id if current_settings else None, assigned_quantity = assigned_quantity)
                print("new output", new_output.batch_id)                            
                db.session.add(new_output)

            else:
                PCR_Service.generate_IPCR_from_tasks(user_id=user_id, main_task_id = task_id, assigned_quantity = assigned_quantity)

            db.session.commit()
            user = User.query.get(user_id)
            socketio.emit("user_assigned", "user assigned")

            Notification_Service.notify_user(user_id, msg=f"The task: { main_task.mfo} has been assigned to this account.")
            Notification_Service.notify_presidents( msg=f"The task: { main_task.mfo} has been assigned to {user.first_name + " " + user.last_name}.")
            

            return jsonify(message = "Member successfully assigned."), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def create_user_output(task_id, user_id, current_batch_id, ipcr_id):
        try:

            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            new_output = Output(user_id = user_id, main_task_id = task_id, batch_id = current_batch_id, ipcr_id=ipcr_id, period = current_settings.current_period_id if current_settings else None)
            print("new output", new_output.batch_id)
                        
            db.session.add(new_output)
            db.session.commit()
            socketio.emit("user_assigned", "user assigned")

            return jsonify(message = "User successfully assigned."), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def create_task_for_ipcr(task_id, user_id, current_batch_id, ipcr_id):
        try:
            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            new_output = Output(user_id = user_id, main_task_id = task_id, batch_id = current_batch_id, ipcr_id=ipcr_id, period = current_settings.current_period_id if current_settings else None)
            new_assigned_tasks = Assigned_Task(user_id=user_id, main_task_id = task_id, batch_id = current_batch_id, period = current_settings.current_period_id if current_settings else None, is_assigned=True)
            
            print("new output", new_output.batch_id)
                        
            db.session.add(new_output)
            db.session.add(new_assigned_tasks)
            db.session.commit()
            socketio.emit("ipcr_added", "user assigned")

            return jsonify(message = "Task successfully added."), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def assign_department(task_id, dept_id):
        try:
            
            from models.Departments import Department
            task = Main_Task.query.get(task_id)
            department = Department.query.get(dept_id)

            #buburahin niya yung mga task na di naman nasa department
            #buburahin yung mga output kase isang department lang pede maassign dati
            # ngayon madami na 

            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()

            """for output in task.outputs:
                if not output.user.department.id == dept_id:
                    db.session.delete(output)
                    db.session.commit()"""
            
            new_assigned_department = Assigned_Department(
                main_task_id = task_id,
                department_id = dept_id,
                period = settings.current_period_id,
                quantity_formula = settings.quantity_formula,
                efficiency_formula = settings.efficiency_formula,
                timeliness_formula = settings.timeliness_formula,
                enable_formulas = False
            )

            db.session.add(new_assigned_department)

            if task == None:
                return jsonify(message = "Output is not found."), 400
            

            db.session.commit()
            print("task id: ", task_id)
            print("dept id: ", dept_id)

            Notification_Service.notify_department(dept_id=dept_id, msg=f"The task: {task.mfo} has been assigned to the office.")
            Notification_Service.notify_administrators(msg=f"The task: {task.mfo} has been assigned to {department.name}.")
            Notification_Service.notify_presidents(msg=f"The task: {task.mfo} has been assigned to {department.name}.")
            socketio.emit("department_assigned", "department assigned")
            socketio.emit("user_assigned", "user assigned")

            return jsonify(message = "Task successfully assigned."), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
        #ayusin yung mga logs mamaya

    def update_department_task_formula(assigned_dept_id, data):
        try:
            assigned_dept = Assigned_Department.query.get(assigned_dept_id)
            assigned_dept.enable_formulas = data.get("enable_formulas", assigned_dept.enable_formulas)
            assigned_dept.quantity_formula = data.get("quantity_formula", assigned_dept.quantity_formula)
            assigned_dept.efficiency_formula = data.get("efficiency_formula", assigned_dept.efficiency_formula)
            assigned_dept.timeliness_formula = data.get("timeliness_formula", assigned_dept.timeliness_formula)

            db.session.commit()

            return jsonify(message="Formula successfully updated."), 200
        
        except Exception as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500

    def check_if_ipcrs_have_tasks():
        from models.PCR import IPCR, Supporting_Document
        
        ipcrs = IPCR.query.filter(~IPCR.sub_tasks.any()).all()

        for ipcr in ipcrs:

            Supporting_Document.query.filter_by(ipcr_id = ipcr.id).delete()

            print(f"Deleting IPCR {ipcr.id} with no sub_tasks")
            db.session.delete(ipcr)

        db.session.commit()



        
    def unassign_user(task_id, user_id):
        try:
            Assigned_Task.query.filter_by(user_id = user_id, main_task_id = task_id).delete()

            user = User.query.get(user_id)

            outputs = Output.query.filter_by(user_id = user_id, main_task_id = task_id).all()

            for output in outputs:
                Sub_Task.query.filter_by(output_id = output.id).delete()
                db.session.commit()
            

            Output.query.filter_by(user_id = user_id, main_task_id = task_id).delete()
            db.session.commit()

            Tasks_Service.check_if_ipcrs_have_tasks()




            task = Main_Task.query.get(task_id)
            
            socketio.emit("user_unassigned", "user assigned")
            Notification_Service.notify_user(user_id=user_id, msg=f"A task has been unassigned from you.")
            Notification_Service.notify_presidents(msg=f"{user.first_name + " " + user.last_name} has been removed from task: {task.mfo}.")
            
            return jsonify(message = "Task successfully removed."), 200
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
            
    
    def get_assigned_users(dept_id, task_id):
        try:
            found_task = Main_Task.query.get(task_id)

            if found_task == None:
                print("WALANG TAO")
                return jsonify(""), 200
            
            converted = found_task.get_users_by_dept(id = dept_id) 
            print("ASSIGNEd", converted)

            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
    
    def get_general_assigned_users(task_id):
        try:
            found_task = Main_Task.query.filter_by(id = task_id).first()
            if found_task == None:
                 return jsonify(""), 200
            
            converted = found_task.get_users() 
            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_general_tasks():
        try:
            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()

            all_general_tasks = Main_Task.query.filter(Main_Task.department_id.is_(None), Main_Task.status == 1, Main_Task.period == settings.current_period_id).all()
            converted = [task.info() for task in all_general_tasks]
            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
    
    def get_tasks_by_department(id):
        try:
            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()

            all_department_tasks = Assigned_Department.query.filter_by(department_id = id, period = settings.current_period_id).all()
            converted = []

            for task in all_department_tasks:
                if task.main_task.status:
                    data = task.main_task.info() 
                    data["quantity_formula"] = task.quantity_formula
                    data["efficiency_formula"] = task.efficiency_formula
                    data["timeliness_formula"] = task.timeliness_formula
                    data["assigned_dept_id"] = task.id  
                    data["enable_formulas"] = task.enable_formulas  

                    converted.append(data)

            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_all_general_tasks():
        try:

            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()
            all_general_tasks = Main_Task.query.filter_by(department_id = None, status = 1, period = settings.current_period_id).all()
            converted = [task.info() for task in all_general_tasks]

            
            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
        
    def archive_task(id):
        try:
            main_task = Main_Task.query.get(id)
            if not main_task:
                return jsonify(message="No main task with that ID"), 400

            # Archive main task
            main_task.status = 0

            # Archive all subtasks
            for sub_task in main_task.sub_tasks:
                sub_task.status = 0

            # Delete all outputs linked to this main task
            for output in main_task.outputs:
                db.session.delete(output)

            # Delete all assigned tasks linked to this main task
            for assigned_task in main_task.assigned_tasks:
                db.session.delete(assigned_task)

            db.session.commit()
            socketio.emit("main_task", "archived")

            return jsonify(message="Task successfully archived."), 200

        except Exception as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500

        
    def remove_task_from_dept(id, dept_id):
        try:
            found_task = Main_Task.query.get(id)
            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()


            found_assigned_department = Assigned_Department.query.filter_by(main_task_id = id, department_id = dept_id, period = settings.current_period_id).first()
            db.session.delete(found_assigned_department)

            if found_task == None:
                return jsonify(message="No task with that ID"), 400
            
            found_assigned_tasks = Assigned_Task.query.filter_by(main_task_id = id).all()

            for ass_tasks in found_assigned_tasks:
                
                if ass_tasks.user.department_id == int(dept_id):
                    print("meron ass task")
                    db.session.delete(ass_tasks)

                found_output = Output.query.filter_by(user_id = ass_tasks.user.id, main_task_id = id).all()
                for output in found_output:
                    db.session.delete(output)


            
            db.session.commit()
            socketio.emit("task_modified", "task modified")
            socketio.emit("department_assigned", "task modified")
            Notification_Service.notify_department(dept_id, f"The task: {found_task.mfo} has been removed from this office.")

            return jsonify(message = "Task successfully removed."), 200
        
        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Data does not exists"), 400
        
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
    
    def remove_output_by_main_task_id(main_task_id, batch_id):
        try:
            output = Output.query.filter_by(main_task_id = main_task_id, batch_id = batch_id).first()
            assigned_task = Assigned_Task.query.filter_by(main_task_id = main_task_id, batch_id = batch_id).first()

            if output == None:
                return jsonify(message = "There is no tasks found."), 400
            
            if assigned_task == None:
                return jsonify(message = "There is no assigned tasks found."), 400
            
            db.session.delete(output)
            db.session.delete(assigned_task)

            db.session.commit()
            socketio.emit("ipcr", "subtask removed")
            socketio.emit("ipcr_remove", "subtask removed")

            return jsonify(message = "Output was successfully removed."), 200
        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Data does not exists"), 400
        
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def calculateQuantity(target_acc, actual_acc):
        rating = 0
        target = target_acc
        actual = actual_acc

        if target == 0:
            
            return 0
        
        calculations = actual/target
        
        if calculations >= 1.3:
            rating = 5
        elif calculations >= 1.01 and calculations <= 1.299:
            rating = 4
        elif calculations >= 0.90 and calculations <= 1:
            rating = 3    
        elif calculations >= .70 and calculations <= 0.899:
            rating = 2
        elif calculations <= 0.699:
            rating = 1
        
        return rating  

    def calculateEfficiency(target_mod, actual_mod):
        
        target = target_mod
        actual = actual_mod
        rating = 0
        
        calculations = actual

        if calculations == 0:            
            rating = 5
        elif calculations >= 1 and calculations <= 2:
            rating = 4
        elif calculations >= 3 and calculations <= 4:
            rating = 3    
        elif calculations >= 5 and calculations <= 6:
            rating = 2
        elif calculations <= 7:
            rating = 1
        return rating 
    
    def calculateTimeliness(target_time, actual_time):
        
        target = target_time
        actual = actual_time
        rating = 0
        if target == 0:
            return 0
        
        calculations = ((target - actual) / target) + 1
        
        if calculations >= 1.3:
            rating = 5
        elif calculations >= 1.15 and calculations <= 1.29:
            rating = 4
        elif calculations >= 0.9 and calculations <= 1.14:
            rating = 3    
        elif calculations >= 0.51 and calculations <= 0.89:
            rating = 2
        elif calculations <= 0.5:
            rating = 1
        return rating
    
    def calculateAverage(quantity, efficiency, timeliness):

        normalized_quantity = quantity if quantity else 0
        normalized_efficiency = efficiency if efficiency else 0
        normalized_timeliness = timeliness if timeliness else 0

        q = 5 if normalized_quantity > 5 else normalized_quantity
        e = 5 if normalized_efficiency > 5 else normalized_efficiency
        t = 5 if normalized_timeliness > 5 else normalized_timeliness
        calculations = q + e + t
        result = calculations/3
        return result
    
    def get_department_task(dept_id):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()

            all_assigned_tasks = Assigned_Department.query.filter_by(period = settings.current_period_id , department_id = dept_id).all()

            all_converted_tasks = [task.main_task.ipcr_info() for task in all_assigned_tasks]

            return jsonify(tasks=all_converted_tasks), 200

        except Exception as e:
            return jsonify(error = "There is an error fetching tasks."), 500

    def update_assigned_dept(assigned_dept_id, field, value):
        try:
            found_task = Assigned_Department.query.get(assigned_dept_id)

            if not found_task:
                return jsonify(error="Task is not found"), 400
            
            if field == "quantity":
                found_task.quantity = value

            if field == "efficiency":
                found_task.efficiency = value

            if field == "timeliness":
                found_task.timeliness = value

            db.session.commit()
            socketio.emit("rating", "change")

            return jsonify(message = "Updated Successfully"), 200

        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify(error="There is an error updating task"), 500
        
    def update_sub_task_fields(sub_task_id, field, value):

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()
        try:
            ipcr = Sub_Task.query.get(sub_task_id)

            if field == "target_acc":
                ipcr.target_acc = int(value)
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "target_time":
                ipcr.target_time = int(value)
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "target_mod":
                ipcr.target_mod = int(value)
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_deadline":

                ipcr.actual_deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_acc":
                ipcr.actual_acc = int(value)
                db.session.commit()
                
                if settings.enable_formula:
                    print("trigger formula")
                    ipcr.calculate_with_override("quantity", ipcr.target_acc, int(value))

                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_time":
                ipcr.actual_time = int(value)
                db.session.commit()
                
                if settings.enable_formula:
                    ipcr.calculate_with_override("timeliness", ipcr.target_acc, int(value))

                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_mod":
                ipcr.actual_mod = int(value)
                db.session.commit()
                
                if settings.enable_formula:
                    ipcr.calculate_with_override("efficiency", ipcr.target_mod, int(value))

                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)
                


            
            if field == "quantity":

                
                
                ipcr.quantity = int(value)
                db.session.commit()
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "efficiency":
                ipcr.efficiency = int(value)
                db.session.commit()
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "timeliness":
                ipcr.timeliness = int(value)
                db.session.commit()
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "average":
                ipcr.average = float(value)
                
            db.session.commit()


            

            socketio.emit("ipcr", "change")
            return jsonify(message = "Task updated"), 200
        
        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Data does not exists"), 400
        
        except DataError as e:
            db.session.rollback()
            print(str(e))
            
            return jsonify(error="Invalid data format"), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def get_task_user_averages(task_id):
        """
        Returns a list of user summaries for a specific task.
        Each summary includes user info and their average ratings.
        """

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()


        results = (
            db.session.query(
                Output.user_id,
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("overall_average")
            )
            .join(Sub_Task, Output.id == Sub_Task.output_id)
            .filter(Output.main_task_id == task_id, Output.period == settings.current_period_id)
            .group_by(Output.user_id)
            .all()
        )

        # Format results
        user_averages = []
        for row in results:
            user = row.user_id  # you can fetch user info if needed
            user_data = {
                "user_id": row.user_id,
                "avg_quantity": round(row.avg_quantity or 0, 2),
                "avg_efficiency": round(row.avg_efficiency or 0, 2),
                "avg_timeliness": round(row.avg_timeliness or 0, 2),
                "overall_average": round(row.overall_average or 0, 2),
            }
            user_averages.append(user_data)
        
        return user_averages
    
    def get_department_subtask_percentage(main_task_id):
        """
        Returns the percentage of users with subtasks for a given main task,
        grouped by department. Output format is suitable for Recharts.
        
        Example output:
        [
            {"name": "HR", "value": 25.0},
            {"name": "Finance", "value": 50.0},
            {"name": "IT", "value": 25.0}
        ]
        """
        

        main_task = Main_Task.query.get(main_task_id)
        if not main_task:
            return []

        dept_count = defaultdict(int)
        total_users = 0

        # Count users per department based on outputs
        for output in main_task.outputs:
            user = output.user
            if not user or not user.department:
                continue
            dept_name = user.department.name
            dept_count[dept_name] += 1
            total_users += 1

        if total_users == 0:
            return []

        # Prepare list with counts and percentages
        stats_list = [
            {
                "name": dept,
                "count": count,
                "percentage": round((count / total_users) * 100, 2)
            }
            for dept, count in dept_count.items()
        ]

        return stats_list
    
    def calculate_main_task_performance(main_task_id):
        """
        Calculate the average quantity, efficiency, timeliness, and overall average
        for all subtasks under a given Main Task.

        Returns JSON response:
        {
            "quantity": 4.2,
            "efficiency": 3.8,
            "timeliness": 4.0,
            "overall_average": 4.0
        }
        """
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()

        main_task = Main_Task.query.get(main_task_id)

        if not main_task:
            return jsonify({
                "quantity": 0,
                "efficiency": 0,
                "timeliness": 0,
                "overall_average": 0
            }), 404

        total_quantity = 0
        total_efficiency = 0
        total_timeliness = 0
        total_average = 0
        count = 0

        for sub_task in main_task.sub_tasks:
            # Assuming these methods exist in your Sub_Task model
            quantity = sub_task.quantity
            efficiency = sub_task.efficiency
            timeliness = sub_task.timeliness
            average = sub_task.calculateAverage()

            if settings.enable_formula:
                quantity = sub_task.calculateQuantity()
                efficiency = sub_task.calculateEfficiency()
                timeliness = sub_task.calculateTimeliness()

            

            total_quantity += quantity
            total_efficiency += efficiency
            total_timeliness += timeliness
            total_average += average
            count += 1

        if count == 0:
            return jsonify({
                "quantity": 0,
                "efficiency": 0,
                "timeliness": 0,
                "overall_average": 0
            }), 200

        data = {
            "quantity": round(total_quantity / count, 2),
            "efficiency": round(total_efficiency / count, 2),
            "timeliness": round(total_timeliness / count, 2),
            "overall_average": round(total_average / count, 2)
        }

        return jsonify(data), 200
    
    def calculate_user_performance(user_id):
        """
        Calculate the average quantity, efficiency, timeliness, and overall average
        for all sub_tasks (via IPCR or Outputs) belonging to a specific user.

        Returns:
        {
            "user_id": 1,
            "quantity": 4.2,
            "efficiency": 3.8,
            "timeliness": 4.0,
            "overall_average": 4.0
        }
        """

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()

        results = (
            db.session.query(
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("avg_overall")
            )
            .join(Output, Output.id == Sub_Task.output_id)
            .filter(Output.user_id == user_id, Output.period == settings.current_period_id)
            .first()
        )

        if not results or results.avg_quantity is None:
            return {
                "user_id": user_id,
                "quantity": 0,
                "efficiency": 0,
                "timeliness": 0,
                "overall_average": 0
            }

        data = {
            "user_id": user_id,
            "quantity": round(results.avg_quantity or 0, 2),
            "efficiency": round(results.avg_efficiency or 0, 2),
            "timeliness": round(results.avg_timeliness or 0, 2),
            "overall_average": round(results.avg_overall or 0, 2)
        }

        return data
    
    
    
    def get_all_tasks_average_summary():
        """
        Calculates the real average performance for ALL main tasks
        (across all categories), using Sub_Task's calculation methods.
        """

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()


        all_tasks = Main_Task.query.filter_by(status=1, period = settings.current_period_id).all()
        data = []

        for task in all_tasks:
            total_quantity = 0
            total_efficiency = 0
            total_timeliness = 0
            total_average = 0
            count = 0

            for sub_task in task.sub_tasks:
                # Dynamically compute each rating

                timeliness = 0
                actual_working_days = 0
                target_working_days = 0

                if task.timeliness_mode == "timeframe":
                    timeliness = sub_task.calculate_with_override("timeliness", sub_task.target_time, sub_task.actual_time)
                else:
                    # Handle deadline-based timeliness with proper null checks
                    if sub_task.actual_deadline and sub_task.main_task.target_deadline:
                        days_late = (
                            sub_task.actual_deadline - sub_task.main_task.target_deadline
                        ).days
                        actual_working_days = days_late
                        target_working_days = 1
                        timeliness = sub_task.timeliness
                    else:
                        # Fallback if deadlines are missing: use default rating
                        timeliness = 0

                quantity = sub_task.quantity                
                efficiency = sub_task.efficiency


                if settings.enable_formula:
                    quantity = sub_task.calculate_with_override("quantity", sub_task.target_acc, sub_task.actual_acc)
                    timeliness = sub_task.calculate_with_override("timeliness", target_working_days, actual_working_days)
                    efficiency = sub_task.calculate_with_override("efficiency", sub_task.target_mod, sub_task.actual_mod)
                
                average = sub_task.calculateAverage()

                total_quantity += quantity
                total_efficiency += efficiency
                total_timeliness += timeliness

                total_average += average
                count += 1

            if count > 0:
                data.append({
                    "task_id": task.id,
                    "category_id": task.category_id,
                    "task_name": task.mfo,
                    "average_quantity": round(total_quantity / count, 2),
                    "average_efficiency": round(total_efficiency / count, 2),
                    "average_timeliness": round(total_timeliness / count, 2),
                    "overall_average": round(total_average / count, 2),
                })
            else:
                data.append({
                    "task_id": task.id,
                    "category_id": task.category_id,
                    "task_name": task.mfo,
                    "average_quantity": 0,
                    "average_efficiency": 0,
                    "average_timeliness": 0,
                    "overall_average": 0,
                })

        return jsonify(data), 200
    
    def calculate_all_tasks_average_summary():
        """
        Calculates the real average performance for ALL main tasks
        (across all categories), using Sub_Task's calculation methods.
        """

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()


        all_tasks = Main_Task.query.filter_by(status=1, period = settings.current_period_id).all()
        data = []

        for task in all_tasks:
            total_quantity = 0
            total_efficiency = 0
            total_timeliness = 0
            total_average = 0
            count = 0

            for sub_task in task.sub_tasks:
                # Dynamically compute each rating

                timeliness = 0
                actual_working_days = 0
                target_working_days = 0

                if task.timeliness_mode == "timeframe":
                    timeliness = sub_task.calculate_with_override("timeliness", sub_task.target_time, sub_task.actual_time)
                else:
                    # Handle deadline-based timeliness with proper null checks
                    if sub_task.actual_deadline and sub_task.main_task.target_deadline:
                        days_late = (
                            sub_task.actual_deadline - sub_task.main_task.target_deadline
                        ).days
                        actual_working_days = days_late
                        target_working_days = 1
                        timeliness = sub_task.timeliness
                    else:
                        # Fallback if deadlines are missing: use default rating
                        timeliness = 0

                quantity = sub_task.quantity                
                efficiency = sub_task.efficiency

                if settings.enable_formula:
                    quantity = sub_task.calculate_with_override("quantity", sub_task.target_acc, sub_task.actual_acc)
                    timeliness = sub_task.calculate_with_override("timeliness", target_working_days, actual_working_days)
                    efficiency = sub_task.calculate_with_override("efficiency", sub_task.target_mod, sub_task.actual_mod)

                average = sub_task.calculateAverage()

                total_quantity += quantity
                total_efficiency += efficiency
                total_timeliness += timeliness
                total_average += average
                count += 1

            if count > 0:
                data.append({
                    "task_id": task.id,
                    "category_id": task.category_id,
                    "task_name": task.mfo,
                    "average_quantity": round(total_quantity / count, 2),
                    "average_efficiency": round(total_efficiency / count, 2),
                    "average_timeliness": round(total_timeliness / count, 2),
                    "overall_average": round(total_average / count, 2),
                })
            else:
                data.append({
                    "task_id": task.id,
                    "category_id": task.category_id,
                    "task_name": task.mfo,
                    "average_quantity": 0,
                    "average_efficiency": 0,
                    "average_timeliness": 0,
                    "overall_average": 0,
                })

        return data

    @staticmethod
    def get_user_performance_history(user_id, start_date=None, end_date=None):
        """Get individual user's performance history over time"""
        try:
            from datetime import datetime as dt, timedelta
            from flask import jsonify

            # Parse dates
            if isinstance(start_date, str) and start_date:
                start = dt.strptime(start_date, '%Y-%m-%d').date()
            else:
                start = dt.now().date() - timedelta(days=365)  # Default: last year

            if isinstance(end_date, str) and end_date:
                end = dt.strptime(end_date, '%Y-%m-%d').date()
            else:
                end = dt.now().date()

            # Query user's sub_tasks within date range
            user_sub_tasks = db.session.query(
                func.date(Sub_Task.created_at).label('date'),
                func.avg(Sub_Task.quantity).label('avg_qty'),
                func.avg(Sub_Task.efficiency).label('avg_eff'),
                func.avg(Sub_Task.timeliness).label('avg_time'),
                func.count(Sub_Task.id).label('count')
            ).join(IPCR).filter(
                IPCR.user_id == user_id,
                Sub_Task.created_at >= start,
                Sub_Task.created_at <= end,
                Sub_Task.status == 1
            ).group_by(
                func.date(Sub_Task.created_at)
            ).order_by(
                func.date(Sub_Task.created_at)
            ).all()

            # Format data
            data = []
            for task in user_sub_tasks:
                avg_qty = float(task.avg_qty) if task.avg_qty else 0
                avg_eff = float(task.avg_eff) if task.avg_eff else 0
                avg_time = float(task.avg_time) if task.avg_time else 0
                avg_all = (avg_qty + avg_eff + avg_time) / 3

                data.append({
                    'date': task.date.strftime('%Y-%m-%d'),
                    'period': task.date.strftime('%Y-%m'),
                    'quantity': round(avg_qty, 2),
                    'efficiency': round(avg_eff, 2),
                    'timeliness': round(avg_time, 2),
                    'average': round(avg_all, 2),
                    'task_count': int(task.count)
                })

            # Calculate summary statistics
            if data:
                quantities = [d['quantity'] for d in data]
                efficiencies = [d['efficiency'] for d in data]
                timeliness = [d['timeliness'] for d in data]
                averages = [d['average'] for d in data]

                summary = {
                    'avg_quantity': round(sum(quantities) / len(quantities), 2),
                    'avg_efficiency': round(sum(efficiencies) / len(efficiencies), 2),
                    'avg_timeliness': round(sum(timeliness) / len(timeliness), 2),
                    'overall_average': round(sum(averages) / len(averages), 2),
                    'total_tasks': sum(d['task_count'] for d in data),
                    'periods': len(data)
                }
            else:
                summary = {
                    'avg_quantity': 0,
                    'avg_efficiency': 0,
                    'avg_timeliness': 0,
                    'overall_average': 0,
                    'total_tasks': 0,
                    'periods': 0
                }

            return jsonify({
                'status': 'success',
                'data': data,
                'summary': summary
            }), 200

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    