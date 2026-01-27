from app import db
from app import socketio
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.Tasks import Tasks_Service, Assigned_Task, Output, Sub_Task, Formula_Engine
from models.User import Users, User, Notification_Service
from models.Departments import Department_Service, Department
from utils import FileStorage, ExcelHandler
from sqlalchemy import func, outerjoin
from pprint import pprint
import uuid

class OPCR_Rating(db.Model):
    __tablename__ = "opcr_ratings"
    id = db.Column(db.Integer, primary_key=True)
    mfo = db.Column(db.Text, default="")
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    opcr = db.relationship("OPCR", back_populates = "opcr_ratings")

    quantity = db.Column(db.Integer, default = 0)
    efficiency = db.Column(db.Integer, default = 0)
    timeliness = db.Column(db.Integer, default = 0)
    average = db.Column(db.Integer, default = 0)

    period = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        normalized_q = 5 if self.quantity > 5 else self.quantity
        normalized_e = 5 if self.efficiency > 5 else self.efficiency
        normalized_t = 5 if self.timeliness > 5 else self.timeliness
        return {
            "id": self.id,
            "mfo": self.mfo,
            "opcr_id": self.opcr_id,
            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "period_id": self.period,
            "average": round((normalized_q + normalized_e + normalized_t)/ 3)
        }

class Assigned_PCR(db.Model):
    __tablename__ = "assigned_pcrs"
    id = db.Column(db.Integer, primary_key=True)
    
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default = None)
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default = None)

    ipcr = db.relationship("IPCR", back_populates = "assigned_pcrs")
    opcr = db.relationship("OPCR", back_populates = "assigned_pcrs")
    department = db.relationship("Department", back_populates = "assigned_pcrs")

    period = db.Column(db.String(100), nullable=True)

class Supporting_Document(db.Model):
    __tablename__ = "supporting_documents"
    id = db.Column(db.Integer, primary_key=True)
    
    file_type = db.Column(db.Text, default="")
    file_name = db.Column(db.Text, default="")
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default = None)
    batch_id = db.Column(db.Text, default = "")
    status = db.Column(db.Integer, default = 1)

    ipcr = db.relationship("IPCR", back_populates = "supporting_documents")
    sub_task_id = db.Column(db.Integer, db.ForeignKey("sub_tasks.id"), default = None)

    sub_task = db.relationship("Sub_Task", back_populates = "supporting_documents")

    period = db.Column(db.String(100), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
            "object_name": "documents/" + self.file_name,
            "file_name": self.file_name,
            "batch_id": self.batch_id,
            "period_id": self.period,
            "ipcr_id": self.ipcr_id,
            "status": self.status,
            "download_url": FileStorage.get_file("documents/" + self.file_name),
            "task_name": self.sub_task.main_task.mfo if self.sub_task else "",
            "task_id": self.sub_task.id if self.sub_task else "",
            "main_task_id": self.sub_task.main_task.id,
            "user_name": self.ipcr.user.full_name(),
            "department_name": self.ipcr.user.department.name
        }
    
class OPCR_Supporting_Document(db.Model):
    __tablename__ = "opcr_supporting_documents"
    id = db.Column(db.Integer, primary_key=True)
    
    file_type = db.Column(db.Text, default="")
    file_name = db.Column(db.Text, default="")
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    batch_id = db.Column(db.Text, default = " ")
    status = db.Column(db.Integer, default = 1)

    opcr = db.relationship("OPCR", back_populates = "supporting_documents")

    period = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
            "period_id": self.period,
            "object_name": "documents/" + self.file_name,
            "file_name": self.file_name,
            "batch_id": self.batch_id,
            "ipcr_id": self.opcr_id,
            "status": self.status,
            "download_url": FileStorage.get_file("documents/" + self.file_name)
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

    rev_date = db.Column(db.DateTime, default = None)
    app_date = db.Column(db.DateTime, default = None)
    dis_date = db.Column(db.DateTime, default = None)
    ass_date = db.Column(db.DateTime, default = None)
    fin_date = db.Column(db.DateTime, default = None)
    con_date = db.Column(db.DateTime, default = None)

    created_at = db.Column(db.DateTime, default=datetime.now)

    #one ipcr to one user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="ipcrs")

    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    opcr = db.relationship("OPCR", back_populates="ipcrs")

    sub_tasks = db.relationship("Sub_Task", back_populates = "ipcr", cascade = "all, delete")
    outputs = db.relationship("Output", back_populates = "ipcr", cascade = "all, delete")
    supporting_documents = db.relationship("Supporting_Document", back_populates = "ipcr", cascade = "all, delete")

    isMain = db.Column(db.Boolean, default = False)
    status = db.Column(db.Integer, default = 1)
    form_status = db.Column(db.Text, default="draft")

    batch_id = db.Column(db.Text, default="")
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates = "ipcr", cascade = "all, delete")

    period = db.Column(db.String(100), nullable=True)

    def count_sub_tasks(self):
        return len([main_task for main_task in self.sub_tasks])
    
    def info(self):
        return {
            "id" : self.id,
            "user": self.user_id,
            "core_weight": self.user.position.core_weight,
            "strategic_weight": self.user.position.strategic_weight,
            "support_weight": self.user.position.support_weight
        }
    
    def department_info(self):
        return {
            "id" : self.id,
            "user": self.user.info(),
            "department_id": self.user.department_id,
            "created_at": str(self.created_at),
            "form_status": self.form_status,
            "isMain": self.isMain,
            "batch_id": self.batch_id,
            "status": self.status
        }


    def to_dict(self):

        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()
        president = settings.current_president_fullname if settings.current_president_fullname else ""
        mayor = settings.current_mayor_fullname if settings.current_mayor_fullname else ""

        user_middle_name = self.user.middle_name[0] + ". " if self.user.middle_name else " "

        if self.user.role == "faculty":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()
            dept_middle_name = department_head.middle_name[0] + ". " if department_head and department_head.middle_name else " "
            
            self.reviewed_by = department_head.first_name + " " + dept_middle_name + department_head.last_name if department_head else ""
            self.rev_position = department_head.position.name if department_head else ""

            self.approved_by = president
            self.app_position = "College President"

            self.discussed_with = self.user.first_name + " "+ user_middle_name + self.user.last_name 
            self.dis_position = self.user.position.name

            self.assessed_by = department_head.first_name + " "+ dept_middle_name + department_head.last_name if department_head else ""
            self.ass_position = department_head.position.name if department_head else ""

            self.final_rating_by = president
            self.fin_position = "College President"

            self.confirmed_by = mayor
            self.con_position = "PMT Chairperson"
            print("GEtting the user ipcr info")
            db.session.commit()
        elif self.user.role == "head":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()

            
            self.reviewed_by = president
            self.rev_position = "College President"

            self.approved_by = president
            self.app_position = "College President"

            self.discussed_with = self.user.first_name + " " + user_middle_name + self.user.last_name 
            self.dis_position = self.user.position.name

            self.assessed_by = president
            self.ass_position ="College President"

            self.final_rating_by = president
            self.fin_position = "College President"

            self.confirmed_by = mayor
            self.con_position = "PMT Chairperson"

        elif self.user.role == "administrator":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()
            
            self.reviewed_by = president
            self.rev_position = "College President"

            self.approved_by = president
            self.app_position = "College President"

            self.discussed_with = self.user.first_name + " "+ user_middle_name + self.user.last_name 
            self.dis_position = self.user.position.name

            self.assessed_by = president
            self.ass_position ="College President"

            self.final_rating_by = president
            self.fin_position = "College President"

            self.confirmed_by = mayor
            self.con_position = "PMT Chairperson"
            
            db.session.commit()
            

        elif self.user.role == "president":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()

            president = User.query.filter_by(role = "president").first()
            
            self.reviewed_by = president
            self.rev_position = "College President"

            self.approved_by = president
            self.app_position = "College President"

            self.discussed_with = president
            self.dis_position = "College President"

            self.assessed_by = president
            self.ass_position ="College President"

            self.final_rating_by = president
            self.fin_position = "College President"

            self.confirmed_by = mayor
            self.con_position = "PMT Chairperson"
            
            db.session.commit()

        return {
            "id" : self.id,
            "user": self.user_id,
            "user_info": self.user.info(),
            "sub_tasks": [main_task.to_dict() for main_task in self.sub_tasks],
            "sub_tasks_count": self.count_sub_tasks(),
            "created_at": str(self.created_at),
            "form_status": self.form_status,
            "isMain": self.isMain,
            "batch_id": self.batch_id,
            "status": self.status,
            "period_id": self.period,
            "review" : {
                "name": self.reviewed_by,
                "position": self.rev_position,
                "date": ""
            },
            "approve" : {
                "name": self.approved_by,
                "position": self.app_position,
                "date": ""
            },
            "discuss" : {
                "name": self.discussed_with,
                "position": self.dis_position,
                "date": ""
            },
            "assess" : {
                "name": self.assessed_by,
                "position": self.ass_position,
                "date": ""
            },
            "final" : {
                "name": self.final_rating_by,
                "position": self.fin_position,
                "date": ""
            },
            "confirm" : {
                "name": self.confirmed_by,
                "position": self.con_position,
                "date": ""
            }
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
    #one ipcr to one opcr

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", back_populates="opcrs")

    supporting_documents = db.relationship("OPCR_Supporting_Document", back_populates = "opcr", cascade = "all, delete")
    opcr_ratings = db.relationship("OPCR_Rating", back_populates = "opcr", cascade = "all, delete")

    ipcrs = db.relationship("IPCR", back_populates = "opcr", cascade = "all, delete")
    isMain = db.Column(db.Boolean, default = False)
    status = db.Column(db.Integer, default = 1)
    form_status = db.Column(db.Text, default="draft")

    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates = "opcr", cascade = "all, delete")

    rev_date = db.Column(db.DateTime, default = None)
    app_date = db.Column(db.DateTime, default = None)
    dis_date = db.Column(db.DateTime, default = None)
    ass_date = db.Column(db.DateTime, default = None)
    fin_date = db.Column(db.DateTime, default = None)
    con_date = db.Column(db.DateTime, default = None)

    period = db.Column(db.String(100), nullable=True)
    def count_ipcr(self):
        return len([ipcr for ipcr in self.ipcrs])
    
    
    def to_dict(self):
        department_head =User.query.filter_by(department_id = self.department_id, role = "head").first()

        dept_middle_name = department_head.middle_name[0] + ". " if department_head and department_head.middle_name else " "

        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()
        president = settings.current_president_fullname if settings.current_president_fullname else ""
        mayor = settings.current_mayor_fullname if settings.current_mayor_fullname else ""

        self.reviewed_by = department_head.first_name + " " + dept_middle_name + department_head.last_name if department_head else ""
        self.rev_position = department_head.position.name if department_head else ""

        self.approved_by = president
        self.app_position = "College President"

        self.discussed_with = department_head.first_name + " " + dept_middle_name + department_head.last_name if department_head else ""
        self.dis_position = department_head.position.name if department_head else ""

        self.assessed_by = president
        self.ass_position = "College President"

        self.final_rating_by = president
        self.fin_position = "College President"

        self.confirmed_by = mayor
        self.con_position = "PMT Chairperson"
        db.session.commit()

        return {
            "id" : self.id,
            "ipcr_count": self.count_ipcr(),
            "form_status": self.form_status,
            "created_at": str(self.created_at),
            "period_id": self.period,
            "review" : {
                "name": self.reviewed_by,
                "position": self.rev_position,
                "date": ""
            },
            "approve" : {
                "name": self.approved_by,
                "position": self.app_position,
                "date": ""
            },
            "discuss" : {
                "name": self.discussed_with,
                "position": self.dis_position,
                "date": ""
                
            },
            "assess" : {
                "name": self.assessed_by,
                "position": self.ass_position,
                "date": ""
            },
            "final" : {
                "name": self.final_rating_by,
                "position": self.fin_position,
                "date": ""
            },
            "confirm" : {
                "name": self.confirmed_by,
                "position": self.con_position,
                "date": ""
                
            },
            "department": self.department.name,
            "status": self.status
        }
    
# gagawa ng output base sa id
#pagtapos gumawa ng mga output, gagwa at kukunin id ni ipcr
#kuhanin yung mga outputs ni user
#i assign yung ipcr id sa subtasks ng output ni user
# si output ang kukuni kay user, si sub task ang lalagyan ng ipcr

#si subtask yung target, kasse pag may output may sub_task din,eh si sub task kailangan ng ipcr id
class PCR_Service():
    def compute_rating_with_override(metric, target, actual, task_id, settings, dept_configs):
        """
        metric: 'quantity' | 'efficiency' | 'timeliness'
        """
        from models.Tasks import Formula_Engine

        engine = Formula_Engine()
        dept_cfg = dept_configs.get(task_id)

        if dept_cfg and dept_cfg["enable"]:
            formula = dept_cfg[metric]
        else:
            formula = getattr(settings, f"{metric}_formula")

        return engine.compute_rating(
                formula=formula,
                target=target,
                actual=actual
        )


    def compute_quantity_rating(target, actual, settings):
        
        engine = Formula_Engine()

        rating = engine.compute_rating(
            formula=settings.quantity_formula,
            target=target,
            actual= actual
        )

        return rating

    
    def compute_efficiency_rating(target, actual, settings):
        engine = Formula_Engine()

        rating = engine.compute_rating(
            formula=settings.efficiency_formula,
            target = target,
            actual = actual
        )

        return rating
    
    def compute_timeliness_rating(target, actual, settings):
        engine = Formula_Engine()

        rating = engine.compute_rating(
            formula=settings.timeliness_formula,
            target = target,
            actual = actual
        )

        return rating

    @staticmethod
    def _calculate_quantity_with_formula(target_acc, actual_acc, settings):
        """Calculate quantity using formula from settings or default"""
        if settings and settings.quantity_formula and settings.quantity_formula.get("expression"):
            expression = settings.quantity_formula.get("expression", "")
            safe_dict = {
                "target": target_acc,
                "actual": actual_acc,
                "target_acc": target_acc,
                "actual_acc": actual_acc
            }
            try:
                result = eval(expression, {"__builtins__": {}}, safe_dict)

                print("Quantity Formula Result:", target_acc, actual_acc, expression, result)
                return float(result) if result <= 5 else 5
            except:
                pass
        
        # Default calculation
        return PCR_Service.calculateQuantity(target_acc, actual_acc)

    @staticmethod
    def _calculate_efficiency_with_formula(target_mod, actual_mod, settings):
        """Calculate efficiency using formula from settings or default"""
        if settings and settings.efficiency_formula and settings.efficiency_formula.get("expression"):
            expression = settings.efficiency_formula.get("expression", "")
            safe_dict = {
                "target": target_mod,
                "actual": actual_mod,
                "target_mod": target_mod,
                "actual_mod": actual_mod
            }
            try:
                result = eval(expression, {"__builtins__": {}}, safe_dict)
                return int(result) if result <= 5 else 5
            except:
                pass
        
        # Default calculation
        return PCR_Service.calculateEfficiency(target_mod, actual_mod)

    @staticmethod
    def _calculate_timeliness_with_formula(target_time, actual_time, settings):
        """Calculate timeliness using formula from settings or default"""
        if settings and settings.timeliness_formula and settings.timeliness_formula.get("expression"):
            print("Timeliness Formula Found")
            expression = settings.timeliness_formula.get("expression", "")
            safe_dict = {
                "target": target_time,
                "actual": actual_time,
                "target_time": target_time,
                "actual_time": actual_time
            }
            try:
                result = eval(expression, {"__builtins__": {}}, safe_dict)
                return int(result) if result <= 5 else 5
            except:
                pass
        
        # Default calculation
        return PCR_Service.calculateTimeliness(target_time, actual_time)
    
    def generate_IPCR_from_tasks(user_id, main_task_id, assigned_quantity):
        try:
            from models.System_Settings import System_Settings
            current_batch_id = str(uuid.uuid4())

            current_period = System_Settings.get_default_settings().current_period_id

            new_ipcr = IPCR(user_id=user_id, batch_id=current_batch_id, form_status="submitted", period=current_period, isMain=True)
            db.session.add(new_ipcr)
            db.session.flush()   # <-- new_ipcr.id now available

            # For each main task, create batch-scoped Assigned_Task (if not exist)
            # and create Output (which will create Sub_Task inside Output.__init__)


                # create batch-scoped Assigned_Task if it doesn't exist for this batch
            existing_assigned = Assigned_Task.query.filter_by(
                    user_id=user_id, main_task_id=main_task_id, batch_id=current_batch_id, period=current_period
            ).first()

            if not existing_assigned:
                new_assigned = Assigned_Task(
                        user_id=user_id,
                        main_task_id=main_task_id,
                        is_assigned=False,
                        batch_id=current_batch_id,
                        period=current_period,
                        assigned_quantity = assigned_quantity
                    )
                db.session.add(new_assigned)

                # create new Output (this will create Sub_Task in Output.__init__)
            new_output = Output(
                    user_id=user_id,
                    main_task_id=main_task_id,
                    batch_id=current_batch_id,
                    ipcr_id=new_ipcr.id,
                    period=current_period,
                    assigned_quantity= assigned_quantity 
                )
            db.session.add(new_output)

            # commit all at once
            db.session.commit()

            # emit one structured event
            socketio.emit("ipcr_create", {
                "ipcr_id": new_ipcr.id,
                "batch_id": current_batch_id,
                "user_id": user_id,
                "task_count": len(main_task_id)
            })
            Notification_Service.notify_presidents(f"A new IPCR has been submitted from {new_ipcr.user.department.name}.")

            return jsonify(message="IPCR successfully created"), 200

        except Exception as e:
            db.session.rollback()
            print("generate_IPCR error:", e)
            return jsonify(error=str(e)), 500

    def generate_IPCR(user_id, main_task_id_array):
        try:
            from models.System_Settings import System_Settings
            current_batch_id = str(uuid.uuid4())

            current_period = System_Settings.get_default_settings().current_period_id
            current_period_ipcr = IPCR.query.filter_by(user_id=user_id, period=current_period).first()

            if current_period_ipcr:

                print("An IPCR for the current period already exists.")
                for mt_id in main_task_id_array:
                    # skip if there's already an output for same user/task/batch
                    existing_output = Output.query.filter_by(
                        user_id=user_id, main_task_id=mt_id, batch_id=current_period_ipcr.batch_id, period=current_period
                    ).first()

                    if existing_output:
                        print("Currently exists in the batch and period")
                        # already created for this batch — skip
                        continue

                    # create batch-scoped Assigned_Task if it doesn't exist for this batch
                    existing_assigned = Assigned_Task.query.filter_by(
                        user_id=user_id, main_task_id=mt_id, batch_id=current_period_ipcr.batch_id, period=current_period
                    ).first()

                    if not existing_assigned:
                        print("Creating assigned task for the existing ipcr")
                        new_assigned = Assigned_Task(
                            user_id=user_id,
                            main_task_id=mt_id,
                            is_assigned=False,
                            batch_id=current_period_ipcr.batch_id,
                            period=current_period
                        )
                        db.session.add(new_assigned)

                    # create new Output (this will create Sub_Task in Output.__init__)
                    print("Creating output for the existing ipcr")
                    new_output = Output(
                        user_id=user_id,
                        main_task_id=mt_id,
                        batch_id=current_period_ipcr.batch_id,
                        ipcr_id=current_period_ipcr.id,
                        period=current_period,
                        assigned_quantity=existing_assigned.assigned_quantity if existing_assigned else 0
                    )

                    db.session.add(new_output)
                    db.session.flush()
                    db.session.commit()
                return jsonify(message="An IPCR for the current period already exists."), 200


            # start batch
            

            # create IPCR and flush so id is available
            new_ipcr = IPCR(user_id=user_id, batch_id=current_batch_id, form_status="submitted", period=current_period, isMain=True)
            db.session.add(new_ipcr)
            db.session.flush()   # <-- new_ipcr.id now available

            # For each main task, create batch-scoped Assigned_Task (if not exist)
            # and create Output (which will create Sub_Task inside Output.__init__)

            for mt_id in main_task_id_array:
                # skip if there's already an output for same user/task/batch
                existing_output = Output.query.filter_by(
                    user_id=user_id, main_task_id=mt_id, batch_id=current_batch_id, period=current_period
                ).first()

                if existing_output:
                    # already created for this batch — skip
                    continue

                # create batch-scoped Assigned_Task if it doesn't exist for this batch
                existing_assigned = Assigned_Task.query.filter_by(
                    user_id=user_id, main_task_id=mt_id, batch_id=current_batch_id, period=current_period
                ).first()

                if not existing_assigned:
                    new_assigned = Assigned_Task(
                        user_id=user_id,
                        main_task_id=mt_id,
                        is_assigned=False,
                        batch_id=current_batch_id,
                        period=current_period
                    )
                    db.session.add(new_assigned)

                # create new Output (this will create Sub_Task in Output.__init__)
                new_output = Output(
                    user_id=user_id,
                    main_task_id=mt_id,
                    batch_id=current_batch_id,
                    ipcr_id=new_ipcr.id,
                    period=current_period,
                    assigned_quantity=existing_assigned.assigned_quantity if existing_assigned else 0
                )
                db.session.add(new_output)

            # commit all at once
            db.session.commit()

            # emit one structured event
            socketio.emit("ipcr_create", {
                "ipcr_id": new_ipcr.id,
                "batch_id": current_batch_id,
                "user_id": user_id,
                "task_count": len(main_task_id_array)
            })
            Notification_Service.notify_presidents(f"A new IPCR has been submitted from {new_ipcr.user.department.name}.")

            return jsonify(message="IPCR successfully created"), 200

        except Exception as e:
            db.session.rollback()
            print("generate_IPCR error:", e)
            return jsonify(error=str(e)), 500
        
    def reject_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            
            if ipcr:
                ipcr.form_status = "rejected"
                db.session.commit()
                socketio.emit("ipcr", "approved")
                socketio.emit("opcr", "approved")
                socketio.emit("reject")
                Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been rejected by department head of this department.")
                Notification_Service.notify_presidents(f"IPCR: #{ipcr_id} from {ipcr.user.department.name} has been rejected by department head.")
                return jsonify(message = "This IPCR is successfully rejected."), 200

            return jsonify(error = "There is no ipcr with that id"), 400
        
        except OperationalError as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def reject_opcr(opcr_id):
        try:
            ipcr = OPCR.query.get(opcr_id)
            
            if ipcr:
                ipcr.form_status = "rejected"
                db.session.commit()
                socketio.emit("ipcr", "approved")
                socketio.emit("opcr", "approved")
                socketio.emit("reject")
                Notification_Service.notify_department(ipcr.department_id ,f"The OPCR from this department has been rejected by department head.")
                return jsonify(message = "This OPCR is successfully rejected."), 200

            return jsonify(error = "There is no opcr with that id"), 400
        
        except OperationalError as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def review_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            
            if ipcr:
                ipcr.form_status = "reviewed"
                db.session.commit()
                socketio.emit("ipcr", "approved")
                socketio.emit("opcr", "approved")
                Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been reviewed by department head of this department.")
                Notification_Service.notify_presidents(f"IPCR: #{ipcr_id} from {ipcr.user.department.name} has been reviewed by department head.")
                return jsonify(message = "This IPCR is successfully reviewed."), 200

            return jsonify(message = "There is no ipcr with that id"), 400
        
        except OperationalError as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def approve_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.form_status = "approved"
            db.session.commit()
            socketio.emit("ipcr", "approved")
            socketio.emit("opcr", "approved")
            if ipcr:
                Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been reviewed by president.")
                return jsonify(message = "This IPCR is successfully approved."), 200

            return jsonify(message = "There is no ipcr with that id"), 400
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def review_opcr(opcr_id):
        try:
            opcr = OPCR.query.get(opcr_id)
            
            if opcr:
                opcr.form_status = "reviewed"
                db.session.commit()
                socketio.emit("ipcr", "approved")
                socketio.emit("opcr", "approved")
                Notification_Service.notify_department_heads(opcr.department_id, f"OPCR: #{opcr.id} has been reviewed by the president.")
                return jsonify(message = "This OPCR is successfully reviewed."), 200

            return jsonify(message = "There is no ipcr with that id"), 400
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def approve_opcr(opcr_id):
        try:
            opcr = OPCR.query.get(opcr_id)
            
            if opcr:
                opcr.form_status = "approved"
                db.session.commit()
                socketio.emit("ipcr", "approved")
                socketio.emit("opcr", "approved")
                Notification_Service.notify_department_heads(opcr.department_id, f"OPCR: #{opcr.id} has been approved by the president.")
                return jsonify(message = "This OPCR is successfully approved."), 200

            return jsonify(message = "There is no ipcr with that id"), 400
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
    
    def get_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)

            if ipcr:
                return jsonify(ipcr.to_dict()), 200

            return jsonify(message = "There is no ipcr with that id"), 400
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def assign_main_ipcr(ipcr_id, user_id):
        try:
            user = User.query.get(user_id)

            if user == None:
                return jsonify(message = "There is no user with that id"), 400

            for ipcr in user.ipcrs:
                ipcr.isMain = False
                ipcr.form_status = "draft"

            
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.isMain = True
            ipcr.form_status = "submitted"
            

            socketio.emit("assign")

            db.session.commit()
            Notification_Service.notify_department_heads(user.department_id, f"{user.first_name + " " + user.last_name} assigned IPCR: #{ipcr_id} as its latest IPCR.")
            Notification_Service.notify_presidents(f"{user.first_name + " " + user.last_name} from {user.department.name} assigned IPCR: #{ipcr_id} as its latest IPCR.")
            
            return jsonify(message = "IPCR successfully assigned."), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def update_rating(rating_id, field, value):
        try:
            rating = OPCR_Rating.query.get(rating_id)
            
            if "quantity" in field.split(" "):
                rating.quantity = value
                db.session.commit()

            if "efficiency" in field.split(" "):
                rating.efficiency = value
                db.session.commit()

            if "timeliness" in field.split(" "):
                rating.timeliness = value
                db.session.commit()

            socketio.emit("rating", "change")

            
            return jsonify(message = "Rating updated"), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def assign_pres_ipcr(ipcr_id, user_id):
        try:
            user = User.query.get(user_id)

            if user == None:
                return jsonify(message = "There is no user with that id"), 400

            for ipcr in user.ipcrs:
                ipcr.isMain = False

            
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.isMain = True

            socketio.emit("assign")

            db.session.commit()
            
            return jsonify(message = "IPCR successfully assigned."), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def assign_main_opcr(opcr_id, dept_id):
        try:
            opcrs = OPCR.query.filter_by(department_id = dept_id).all()
            dept = Department.query.filter_by(id = dept_id).first()
            for opcr in opcrs:
                opcr.isMain = False
                opcr.status = 0

            

            
            ipcr = OPCR.query.get(opcr_id)
            ipcr.isMain = True
            ipcr.status = 1 
            ipcr.form_status = "submitted"

            socketio.emit("assign")

            db.session.commit()
            Notification_Service.notify_department_heads(dept_id, f"{dept.name} submitted their latest OPCR.")
            Notification_Service.notify_presidents(f"{dept.name}  submitted their latest IPCR.")
            
            return jsonify(message = "OPCR successfully assigned."), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

    def archive_ipcr(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)

            ipcr.status = 0
            batch_id = ipcr.batch_id

            all_batched_outputs = Output.query.filter_by(batch_id = batch_id).all()
            all_batched_assigned_task = Assigned_Task.query.filter_by(batch_id = batch_id).all()
            all_batched_sub_tasks = Sub_Task.query.filter_by(batch_id = batch_id).all()

            for i in all_batched_outputs:
                i.status = 0

            for i in all_batched_assigned_task:
                i.status = 0

            for i in all_batched_sub_tasks:
                i.status = 0
            socketio.emit("ipcr_create", "ipcr archive")
            db.session.commit()
            Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been archived.")
            Notification_Service.notify_department_heads(ipcr.user.department_id, f"The IPCR: #{ipcr_id} has been archived.")
            Notification_Service.notify_presidents(f"The IPCR: #{ipcr_id} from {ipcr.user.department.name} has been archived.")
            return jsonify(message="IPCR was archived successfully."), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def archive_opcr(opcr_id):
        try:
            opcr = OPCR.query.get(opcr_id)
            opcr.status = 0
            print("ARCHIVED OPCR", opcr_id)
            for ipcr in opcr.ipcrs:
                PCR_Service.archive_ipcr(ipcr.id)

            socketio.emit("opcr", "arcgive")

            db.session.commit()
            return jsonify(message="OPCR was archived successfully."), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500

    def record_supporting_document(file_type, file_name, ipcr_id, batch_id, sub_task_id = None):
        try:
            from models.System_Settings import System_Settings            
            current_settings = System_Settings.get_default_settings()

            ipcr = IPCR.query.get(ipcr_id)
            new_supporting_document = Supporting_Document(file_type = file_type, file_name = file_name, ipcr_id = ipcr_id, batch_id = batch_id, sub_task_id = sub_task_id, period = current_settings.current_period_id)
            db.session.add(new_supporting_document)
            db.session.commit()
            socketio.emit("document", "document")
            Notification_Service.notify_department_heads(ipcr.user.department_id, f"{ipcr.user.first_name + " " + ipcr.user.last_name} attached supporting document to IPCR: #{ipcr_id}.")
            Notification_Service.notify_presidents(f"{ipcr.user.first_name + " " + ipcr.user.last_name} attached supporting document to IPCR: #{ipcr_id}.")
            return jsonify(message = "File successfully uploaded."), 200
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
        
    
        
    def get_ipcr_supporting_document(ipcr_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            return [docs.to_dict() for docs in ipcr.supporting_documents], 200

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        

    def get_supporting_documents(opcr_id):
        try:
            pcrs = Assigned_PCR.query.filter_by(opcr_id = opcr_id).all()
            all_documents = []
            for pcr in pcrs:
                
                for docs in pcr.ipcr.supporting_documents:

                    all_documents.append(docs.to_dict()) 

            return jsonify(all_documents), 200

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
    
    def archive_document(document_id):
        try:
            docu = Supporting_Document.query.get(document_id)
            docu.status = 0
            db.session.commit()
            socketio.emit("document", "document")
            return jsonify(message = "Document successfully archived."), 200
        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        

    @staticmethod
    def _create_or_archive_opcrs_for_period(dept_id, current_period_id):
        """Helper: Create new OPCR if missing, archive old period OPCRs."""
        existing_opcr = OPCR.query.filter_by(
            department_id=dept_id, isMain=True, period=current_period_id
        ).first()

        if existing_opcr:
            return existing_opcr

        # Create new OPCR for current period
        new_opcr = OPCR(department_id=dept_id, isMain=True, period=current_period_id)
        db.session.add(new_opcr)
        db.session.flush()

        # Archive old period OPCRs (mark as not main)
        OPCR.query.filter_by(department_id=dept_id).filter(
            OPCR.period != current_period_id
        ).update({"isMain": False, "status": 0}, synchronize_session=False)

        return new_opcr

    @staticmethod
    def _mark_main_opcr(dept_id, new_opcr_id, current_period_id):
        """Helper: Ensure only one OPCR is marked as main in current period."""
        OPCR.query.filter_by(department_id=dept_id, period=current_period_id).update(
            {"isMain": False, "status": 0}, synchronize_session=False
        )
        OPCR.query.filter_by(id=new_opcr_id).update(
            {"isMain": True, "status": 1}, synchronize_session=False
        )

    @staticmethod
    def _add_mfo_ratings(new_opcr, current_period_id, ipcr_ids):
        """Helper: Add OPCR_Rating entries for unique MFOs across IPCRs."""
        existing_mfos = {r.mfo for r in new_opcr.opcr_ratings}
        mfos_to_add = set()

        # Collect all unique MFOs from IPCR sub_tasks
        for ipcr_id in ipcr_ids:
            ipcr = IPCR.query.get(ipcr_id)
            if not ipcr or ipcr.period != current_period_id:
                continue
            for sub_task in ipcr.sub_tasks:
                if sub_task.status != 0 and sub_task.main_task.mfo not in existing_mfos:
                    mfos_to_add.add(sub_task.main_task.mfo)

        # Bulk add new ratings
        for mfo in mfos_to_add:
            db.session.add(OPCR_Rating(
                mfo=mfo, opcr_id=new_opcr.id, period=current_period_id
            ))
            existing_mfos.add(mfo)

    @staticmethod
    def _assign_pcrs_to_opcr(new_opcr, dept_id, current_period_id, ipcr_ids):
        """Helper: Create Assigned_PCR entries for valid IPCRs."""
        # Get all valid IPCRs for current period
        valid_ipcrs = IPCR.query.filter(
            IPCR.id.in_(ipcr_ids), IPCR.period == current_period_id
        ).all()

        # Get existing assignments to avoid duplicates
        existing_ids = {
            (a.ipcr_id,) for a in Assigned_PCR.query.filter_by(
                opcr_id=new_opcr.id, department_id=dept_id
            ).all()
        }

        # Add only new assignments
        for ipcr in valid_ipcrs:
            if (ipcr.id,) not in existing_ids:
                db.session.add(Assigned_PCR(
                    opcr_id=new_opcr.id, ipcr_id=ipcr.id,
                    department_id=dept_id, period=current_period_id
                ))

    def create_opcr(dept_id, ipcr_ids):
        """
        Create or update OPCR for a department in the current period.
        
        - Validates department & period exist
        - Creates new OPCR if period changed, archives old period OPCRs
        - Adds MFO ratings from IPCR sub_tasks
        - Creates Assigned_PCR relationships
        
        Args:
            dept_id: Department ID
            ipcr_ids: List of IPCR IDs to assign to OPCR
            
        Returns:
            tuple: (jsonify response, HTTP status code)
        """
        try:
            from models.System_Settings import System_Settings

            # Validate inputs
            if not dept_id or not isinstance(ipcr_ids, list):
                return jsonify(error="Invalid department ID or IPCR list"), 400

            # Get current period
            current_settings = System_Settings.get_default_settings()
            if not current_settings or not current_settings.current_period_id:
                return jsonify(error="System period not configured"), 400

            current_period_id = current_settings.current_period_id

            # Verify department exists
            dept = Department.query.get(dept_id)
            if not dept:
                return jsonify(error=f"Department {dept_id} not found"), 404

            # Create/get OPCR and archive old periods
            new_opcr = PCR_Service._create_or_archive_opcrs_for_period(
                dept_id, current_period_id
            )

            # Ensure this is the main OPCR for current period
            PCR_Service._mark_main_opcr(dept_id, new_opcr.id, current_period_id)

            # Add MFO ratings
            PCR_Service._add_mfo_ratings(new_opcr, current_period_id, ipcr_ids)

            # Assign IPCRs to OPCR
            PCR_Service._assign_pcrs_to_opcr(
                new_opcr, dept_id, current_period_id, ipcr_ids
            )

            db.session.commit()

            # Notify clients
            socketio.emit("opcr", "created")
            socketio.emit("opcr_created", "created")

            return jsonify(
                message="OPCR successfully created or updated.",
                opcr_id=new_opcr.id
            ), 200

        except IntegrityError as e:
            db.session.rollback()
            return jsonify(error="Data integrity error"), 400

        except OperationalError as e:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500


    
    def generate_opcr(opcr_id):
        from models.System_Settings import System_Settings
        opcr = OPCR.query.get(opcr_id)
        opcr_data = opcr.to_dict()
        data = []
        categories = {}
        assigned = {}

        from models.Tasks import Assigned_Department
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
                department_id=opcr.department_id,
                period=settings.current_period_id
            ).all()
        }

        for assigned_pcr in opcr.assigned_pcrs:
            if assigned_pcr.ipcr.status == 0:
                continue
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                if sub_task.status == 0: continue

                if sub_task.main_task.mfo in assigned.keys():
                    assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                else:
                    assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]



        # load settings once
       

        assigned_dept_tasks = (
            Assigned_Department.query
            .filter_by(department_id=opcr.department_id, period = settings.current_period_id)
            .join(Assigned_Department.main_task)
            .all()
        )

        for ad in assigned_dept_tasks:
            main_task = ad.main_task
            category = main_task.category

            if category.status == 0 or main_task.status == 0:
                continue

            # Register category
            if category.name not in categories:
                categories[category.name] = {
                    "priority": category.priority_order,
                    "tasks": []
                }

            # Add task skeleton (NO ACTUALS YET)
            categories[category.name]["tasks"].append({
                "title": main_task.mfo,
                "summary": {
                    "target": main_task.target_quantity or 0,
                    "actual": 0
                },
                "corrections": {
                    "target": main_task.target_efficiency or 0,
                    "actual": 0
                },
                "working_days": {
                    "target": (
                        1 if main_task.timeliness_mode == "deadline"
                        else main_task.target_timeframe or 0
                    ),
                    "actual": 0
                },
                "description": {
                    "target": main_task.target_accomplishment,
                    "actual": main_task.actual_accomplishment,
                    "alterations": main_task.modification,
                    "time": main_task.time_description,
                    "timeliness_mode": main_task.timeliness_mode,
                    "task_weight": ad.task_weight / 100
                },
                "rating": {
                    "quantity": 0,
                    "efficiency": 0,
                    "timeliness": 0,
                    "average": 0,
                    "weighted_avg": 0
                },
                "frequency": 0,
                "_task_id": main_task.id  # INTERNAL KEY
            })


        for cat_name, meta in sorted(
            categories.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        ):
            data.append({cat_name: meta["tasks"]})



        print("lenght of opcr assignedpcrs",len(opcr.assigned_pcrs))

        for assigned_pcr in opcr.assigned_pcrs:
            ipcr = assigned_pcr.ipcr
            if ipcr.status == 0:
                continue

            for sub_task in ipcr.sub_tasks:
                if sub_task.status == 0:
                    continue

                for cat in data:
                    for _, tasks in cat.items():
                        for task in tasks:
                            if task["_task_id"] != sub_task.main_task.id:
                                continue

                            # 🔁 TIMELINESS MODE (same as before)
                            if (
                                sub_task.main_task.timeliness_mode == "deadline"
                                and sub_task.actual_deadline
                                and sub_task.main_task.target_deadline
                            ):
                                days_late = (
                                    sub_task.actual_deadline
                                    - sub_task.main_task.target_deadline
                                ).days
                                actual_working_days = days_late
                                target_working_days = 1
                            else:
                                actual_working_days = sub_task.actual_time or 0
                                target_working_days = sub_task.main_task.target_timeframe or 0

                            # AGGREGATE
                            task["summary"]["actual"] += sub_task.actual_acc
                            task["corrections"]["actual"] += sub_task.actual_mod
                            task["working_days"]["actual"] += actual_working_days                          
                            task["frequency"] += 1

        for cat in data:
            for _, tasks in cat.items():
                for task in tasks:
                    if task["frequency"] == 0:
                        continue

                    quantity = PCR_Service.compute_rating_with_override(
                        "quantity",
                        task["summary"]["target"],
                        task["summary"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    efficiency = PCR_Service.compute_rating_with_override(
                        "efficiency",
                        task["corrections"]["target"],
                        task["corrections"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    timeliness = PCR_Service.compute_rating_with_override(
                        "timeliness",
                        task["working_days"]["target"],
                        task["working_days"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    avg = PCR_Service.calculateAverage(quantity, efficiency, timeliness)

                    task["rating"] = {
                        "quantity": quantity,
                        "efficiency": efficiency,
                        "timeliness": timeliness,
                        "average": avg,
                        "weighted_avg": avg * task["description"]["task_weight"]
                    }

                    task.pop("_task_id", None)

        # Get the head
        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = {}
        if head:
            head_data = {
                "fullName": head.first_name + " " + head.last_name,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {
                        "name": head.first_name + " " + head.last_name,
                        "position": head.position.name,
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }
        else:
            head_data = {
                "fullName": "",
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "",
                "individuals": {
                    "review": {
                        "name": "",
                        "position": "",
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }    
        
        file_url = ExcelHandler.createNewOPCR(data = data, assigned = assigned, admin_data = head_data)

        return file_url
    
    def generate_weighted_opcr(opcr_id):

        from models.System_Settings import System_Settings

        opcr = OPCR.query.get(opcr_id)
        opcr_data = opcr.to_dict()
        data = []
        categories = {}
        assigned = {}

        from models.Tasks import Assigned_Department
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
                department_id=opcr.department_id, period = settings.current_period_id
            ).all()
        }


        # load settings once
        

        for assigned_pcr in opcr.assigned_pcrs:
            if assigned_pcr.ipcr.status == 0:
                continue
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                if sub_task.status == 0: continue

                cat = sub_task.main_task.category
                categories[cat.name] = cat.priority_order


                if sub_task.main_task.mfo in assigned.keys():
                    assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                else:
                    assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]

        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],   # priority_number
            reverse=True
        )

        for cat_name, _ in sorted_categories:
            data.append({cat_name: []})

        print("lenght of opcr assignedpcrs",len(opcr.assigned_pcrs))

        for assigned_pcr in opcr.assigned_pcrs:
            if assigned_pcr.ipcr.status == 0:
                continue

            print("lenght of sub taskls",len(assigned_pcr.ipcr.sub_tasks))

            for sub_task in assigned_pcr.ipcr.sub_tasks:
                #sub_task.main_task.category.name
                if sub_task.status == 0: continue
                print(sub_task.main_task.category.name)
                current_data_index = 0
                
                
                for cat in data:
                    for name, arr in cat.items():
                        print("may nahanap", sub_task.main_task.category.name == name)
                        if sub_task.main_task.category.name == name:
                            #check mo kung exzisting na yung task sa loob ng category
                            print("may nahanap", sub_task.main_task.category.name == name)

                            current_task_index = 0
                            found = False

                            for tasks in data[current_data_index][name]:
                                # compute ratings using settings formulas (falls back to defaults)
                                

                                if sub_task.mfo == tasks["title"]:
                                    if sub_task.main_task.timeliness_mode == "deadline" and sub_task.actual_deadline and sub_task.main_task.target_deadline:
                                        from datetime import datetime
                                        # Positive if actual submission is AFTER target (late)

                                        

                                        target_working_days = ""
                                        actual_working_days = ""

                                        days_late = (sub_task.actual_deadline - sub_task.main_task.target_deadline).days

                                        actual_working_days = days_late
                                        target_working_days = 1  

                                        quantity = quantity = PCR_Service.compute_rating_with_override(
                                            "quantity",
                                            sub_task.target_acc,
                                            sub_task.actual_acc,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                        efficiency = PCR_Service.compute_rating_with_override(
                                            "efficiency",
                                            sub_task.target_mod,
                                            sub_task.actual_mod,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                        timeliness = PCR_Service.compute_rating_with_override(
                                            "timeliness",
                                            target_working_days,
                                            actual_working_days,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )


                                        rating_data = {
                                            "quantity": quantity,
                                            "efficiency": efficiency,
                                            "timeliness": timeliness,
                                            "average": PCR_Service.calculateAverage(quantity, efficiency, timeliness),
                                            "weighted_avg": PCR_Service.calculateAverage(quantity, efficiency, timeliness) * assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        }


                                        found = True
                                        data[current_data_index][name][current_task_index]["summary"]["actual"] += sub_task.actual_acc

                                        data[current_data_index][name][current_task_index]["corrections"]["actual"] += sub_task.actual_mod

                                        data[current_data_index][name][current_task_index]["working_days"]["actual"] += actual_working_days

                                        data[current_data_index][name][current_task_index]["rating"] = rating_data
                                        data[current_data_index][name][current_task_index]["frequency"] += 1
                                    else:

                                        quantity = quantity = PCR_Service.compute_rating_with_override(
                                            "quantity",
                                            sub_task.target_acc,
                                            sub_task.actual_acc,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                        efficiency = PCR_Service.compute_rating_with_override(
                                            "efficiency",
                                            sub_task.target_mod,
                                            sub_task.actual_mod,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                        timeliness = PCR_Service.compute_rating_with_override(
                                            "timeliness",
                                            sub_task.target_time,
                                            sub_task.actual_time,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )

                                        rating_data = {
                                            "quantity": quantity,
                                            "efficiency": efficiency,
                                            "timeliness": timeliness,
                                            "average": PCR_Service.calculateAverage(quantity, efficiency, timeliness),
                                            "weighted_avg": PCR_Service.calculateAverage(quantity, efficiency, timeliness) * assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        }
                                        found = True
                                        data[current_data_index][name][current_task_index]["summary"]["actual"] += sub_task.actual_acc

                                        data[current_data_index][name][current_task_index]["corrections"]["actual"] += sub_task.actual_mod

                                        data[current_data_index][name][current_task_index]["working_days"]["actual"] += sub_task.actual_time

                                        data[current_data_index][name][current_task_index]["rating"] = rating_data
                                        data[current_data_index][name][current_task_index]["frequency"] += 1
                                current_task_index += 1     

                            if not found:
                                                            
                            
                                if sub_task.main_task.timeliness_mode == "deadline" and sub_task.actual_deadline and sub_task.main_task.target_deadline:
                                    from datetime import datetime
                                    # Positive if actual submission is AFTER target (late)

                                    target_working_days = ""
                                    actual_working_days = ""

                                    days_late = (sub_task.actual_deadline - sub_task.main_task.target_deadline).days

                                    actual_working_days = days_late
                                    target_working_days = 1  

                                    quantity = quantity = PCR_Service.compute_rating_with_override(
                                            "quantity",
                                            sub_task.target_acc,
                                            sub_task.actual_acc,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                    efficiency = PCR_Service.compute_rating_with_override(
                                            "efficiency",
                                            sub_task.target_mod,
                                            sub_task.actual_mod,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                    timeliness = PCR_Service.compute_rating_with_override(
                                            "timeliness",
                                            target_working_days,
                                            actual_working_days,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )


                                    rating_data = {
                                            "quantity": quantity,
                                            "efficiency": efficiency,
                                            "timeliness": timeliness,
                                            "average": PCR_Service.calculateAverage(quantity, efficiency, timeliness),
                                            "weighted_avg": PCR_Service.calculateAverage(quantity, efficiency, timeliness) * assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        }

                                    data[current_data_index][name].append({
                                        "title": sub_task.mfo,
                                        "summary": {
                                            "target": sub_task.main_task.target_quantity, "actual": sub_task.actual_acc
                                        },
                                        "corrections": {
                                            "target": sub_task.main_task.target_efficiency, "actual": sub_task.actual_mod
                                        },
                                        "working_days": {
                                            "target": sub_task.main_task.target_deadline, "actual": actual_working_days
                                        },
                                        "description": {
                                            "target": sub_task.main_task.target_accomplishment,
                                            "actual": sub_task.main_task.actual_accomplishment,
                                            "alterations": sub_task.main_task.modification,
                                            "time": sub_task.main_task.time_description,
                                            "timeliness_mode": sub_task.main_task.timeliness_mode,
                                            "task_weight": assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        },

                                        "rating": rating_data,
                                        "type": sub_task.main_task.category.type,
                                        "frequency": 1
                                    })
                                else:
                                    from datetime import datetime
                                    # Positive if actual submission is AFTER target (late)
                                    

                                    quantity = quantity = PCR_Service.compute_rating_with_override(
                                            "quantity",
                                            sub_task.target_acc,
                                            sub_task.actual_acc,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                    efficiency = PCR_Service.compute_rating_with_override(
                                            "efficiency",
                                            sub_task.target_mod,
                                            sub_task.actual_mod,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )
                                    timeliness = PCR_Service.compute_rating_with_override(
                                            "timeliness",
                                            sub_task.target_time,
                                            sub_task.actual_time,
                                            sub_task.main_task.id,
                                            settings,
                                            assigned_dept_configs
                                        )

                                    rating_data = {
                                            "quantity": quantity,
                                            "efficiency": efficiency,
                                            "timeliness": timeliness,
                                            "average": PCR_Service.calculateAverage(quantity, efficiency, timeliness),
                                            "weighted_avg": PCR_Service.calculateAverage(quantity, efficiency, timeliness) * assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        }

                                    data[current_data_index][name].append({
                                        "title": sub_task.mfo,
                                        "summary": {
                                            "target": sub_task.main_task.target_quantity, "actual": sub_task.actual_acc
                                        },
                                        "corrections": {
                                            "target": sub_task.main_task.target_efficiency, "actual": sub_task.actual_mod
                                        },
                                        "working_days": {
                                            "target": sub_task.main_task.target_timeframe, "actual": sub_task.actual_time
                                        },
                                        "description":{
                                            "target": sub_task.main_task.target_accomplishment,
                                            "actual": sub_task.main_task.actual_accomplishment,
                                            "alterations": sub_task.main_task.modification,
                                            "time": sub_task.main_task.time_description,
                                            "timeliness_mode": sub_task.main_task.timeliness_mode,
                                            "target_timeframe": sub_task.main_task.target_timeframe,
                                            "target_dealine": sub_task.main_task.target_deadline,
                                            "task_weight": assigned_dept_configs.get(sub_task.main_task.id, {}).get("weight", 0)
                                        },
                                        "rating": rating_data,
                                        "type": sub_task.main_task.category.type,
                                        "frequency": 1
                                    })


                    current_data_index += 1

        # Get the head
        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = {}
        if head:
            head_data = {
                "fullName": head.first_name + " " + head.last_name,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {
                        "name": head.first_name + " " + head.last_name,
                        "position": head.position.name,
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }
        else:
            head_data = {
                "fullName": "",
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "",
                "individuals": {
                    "review": {
                        "name": "",
                        "position": "",
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }    
        
        file_url = ExcelHandler.createNewWeightedOPCR(data = data, assigned = assigned, admin_data = head_data)

        return file_url
    
    def generate_master_opcr():
        try:
            from models.System_Settings import System_Settings
            from models.Categories import Category
            from models.PCR import PCR_Service
            
            settings = System_Settings.get_default_settings()
            current_period = settings.current_period_id

            opcrs = OPCR.query.filter_by(status=1, isMain=True, period = current_period).all()
            if not opcrs:
                return jsonify(error="There is no OPCR to consolidate"), 400

            data = []
            assigned = {}

            # ✅ PASS 0 — LOAD ALL CATEGORIES (NO DEPT FILTER)
            categories = Category.query.filter_by(status=1, period = current_period).order_by(
                Category.priority_order.desc()
            ).all()

            category_blocks = {}  # category_name -> task list

            task_index = {}  # main_task_id -> task dict

            for category in categories:
                task_list = []

                for main_task in category.main_tasks:
                    if main_task.status == 0:
                        continue

                    task = {
                        "title": main_task.mfo,
                        "summary": {
                            "target": main_task.target_quantity or 0,
                            "actual": 0
                        },
                        "corrections": {
                            "target": main_task.target_efficiency or 0,
                            "actual": 0
                        },
                        "working_days": {
                            "target": (
                                1 if main_task.timeliness_mode == "deadline"
                                else main_task.target_timeframe or 0
                            ),
                            "actual": 0
                        },
                        "description": {
                            "target": main_task.target_accomplishment,
                            "actual": main_task.actual_accomplishment,
                            "alterations": main_task.modification,
                            "time": main_task.time_description,
                            "target_timeframe": main_task.target_timeframe,
                            "target_dealine": main_task.target_deadline,
                            "timeliness_mode": main_task.timeliness_mode
                        },
                        "rating": {
                            "quantity": 0,
                            "efficiency": 0,
                            "timeliness": 0,
                            "average": 0
                        },
                        "frequency": 0,
                        "_task_id": main_task.id
                    }

                    task_list.append(task)
                    task_index[main_task.id] = task

                data.append({category.name: task_list})


            # ✅ PASS 1 — COLLECT ASSIGNED USERS (UNCHANGED LOGIC)
            assigned = {}

            for opcr in opcrs:
                for assigned_pcr in opcr.assigned_pcrs:
                    ipcr = assigned_pcr.ipcr
                    if ipcr.status == 0 or ipcr.form_status == "draft":
                        continue

                    for sub_task in ipcr.sub_tasks:
                        mfo = sub_task.main_task.mfo
                        user_name = f"{ipcr.user.first_name} {ipcr.user.last_name}"

                        assigned.setdefault(mfo, set()).add(user_name)

            assigned = {k: list(v) for k, v in assigned.items()}


            # ✅ PASS 2 — AGGREGATE ALL TASKS (NO DEPARTMENT FILTER)
            for opcr in opcrs:
                for assigned_pcr in opcr.assigned_pcrs:
                    ipcr = assigned_pcr.ipcr
                    if ipcr.status == 0 or ipcr.form_status == "draft":
                        continue

                    for sub_task in ipcr.sub_tasks:
                        task = task_index.get(sub_task.main_task.id)
                        if not task:
                            continue

                        # Timeliness
                        if (
                            sub_task.main_task.timeliness_mode == "deadline"
                            and sub_task.actual_deadline
                            and sub_task.main_task.target_deadline
                        ):
                            actual_days = (
                                sub_task.actual_deadline - sub_task.main_task.target_deadline
                            ).days
                        else:
                            actual_days = sub_task.actual_time or 0

                        task["summary"]["actual"] += sub_task.actual_acc
                        task["corrections"]["actual"] += sub_task.actual_mod
                        task["working_days"]["actual"] += actual_days
                        task["frequency"] += 1

            settings = System_Settings.get_default_settings()

            for task in task_index.values():
                if task["frequency"] == 0:
                    continue

                quantity = PCR_Service.compute_quantity_rating(
                    task["summary"]["target"],
                    task["summary"]["actual"],
                    settings
                )

                efficiency = PCR_Service.compute_efficiency_rating(
                    task["corrections"]["target"],
                    task["corrections"]["actual"],
                    settings
                )

                timeliness = PCR_Service.compute_timeliness_rating(
                    task["working_days"]["target"],
                    task["working_days"]["actual"],
                    settings
                )

                avg = PCR_Service.calculateAverage(quantity, efficiency, timeliness)

                task["rating"] = {
                    "quantity": quantity,
                    "efficiency": efficiency,
                    "timeliness": timeliness,
                    "average": avg
                }

                task.pop("_task_id", None)


            # ✅ PRESIDENT / HEAD INFO (UNCHANGED)

            settings = System_Settings.get_default_settings()

            head_data = {
                "fullName": settings.current_president_fullname,
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "College President",
                "individuals": {
                    "review": {"name": settings.current_president_fullname, "position": "College President", "date": ""},
                    "approve": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""},
                    "discuss": {"name": "", "position": "", "date": ""},
                    "assess": {"name": "", "position": "Municipal Administrator", "date": ""},
                    "final": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""},
                    "confirm": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""}
                }
            }

            # Generate master OPCR Excel using same structured grouping
            file_url = ExcelHandler.createNewMasterOPCR(data=data, assigned=assigned, admin_data=head_data)

            return jsonify(link=file_url), 200

        except Exception as e:
            print("Error generating master OPCR:", str(e))
            return jsonify(error=str(e)), 500

    def generate_planned_opcr_by_department(department_id):
        data = []
        categories = {}
        assigned = {}

        from models.Tasks import Assigned_Department
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()

        assigned_departments = Assigned_Department.query.filter_by(
            department_id=department_id,
            period = settings.current_period_id

        ).all()

        for ad in assigned_departments:
            cat = ad.main_task.category
            categories[cat.name] = cat.priority_order

        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],  # priority_number
            reverse=True
        )


        for cat_name, _ in sorted_categories:
            data.append({cat_name: []})

        # 3️⃣ Build OPCR structure (NO ACTUAL DATA)
        for ad in assigned_departments:
            main_task = ad.main_task
            category_name = main_task.category.name

            current_data_index = next(
                i for i, d in enumerate(data) if category_name in d
            )

            # Track assigned users (planning view)
            assigned[main_task.mfo] = [user_info["full_name"] for user_info in main_task.get_users_by_dept(department_id)]

            # Planned values only
            data[current_data_index][category_name].append({
                "title": main_task.mfo,

                "summary": {
                    "target": main_task.target_quantity or 0,
                    "actual": 0
                },

                "corrections": {
                    "target": main_task.target_efficiency or 0,
                    "actual": 0
                },

                "working_days": {
                    "target": (
                        1 if main_task.timeliness_mode == "deadline"
                        else main_task.target_timeframe or 0
                    ),
                    "actual": 0
                },

                "description": {
                    "target": main_task.target_accomplishment,
                    "actual": main_task.actual_accomplishment,
                    "alterations": main_task.modification,
                    "time": main_task.time_description,
                    "timeliness_mode": main_task.timeliness_mode,
                    "target_timeframe": main_task.target_timeframe,
                    "target_deadline": (
                        str(main_task.target_deadline)
                        if main_task.target_deadline else None
                    ),
                    "weight": float(ad.task_weight / 100)
                },

                "rating": {
                    "quantity": 0,
                    "efficiency": 0,
                    "timeliness": 0,
                    "average": 0
                },

                "type": main_task.category.type,
                "frequency": 0
            })

        # Get the head
        head = User.query.filter_by(department_id=department_id, role="head").first()
        head_data = {}

        opcr = OPCR.query.filter_by(department_id = department_id).all()[-1]
        opcr_data = opcr.to_dict()

        if head:
            head_data = {
                "fullName": head.first_name + " " + head.last_name,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {
                        "name": head.first_name + " " + head.last_name,
                        "position": head.position.name,
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }
        else:
            head_data = {
                "fullName": "",
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "",
                "individuals": {
                    "review": {
                        "name": "",
                        "position": "",
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }

        file_url = ExcelHandler.createNewOPCR(data = data, assigned = assigned, admin_data = head_data)

        return file_url
    
    def get_planned_opcr_by_department(department_id):
        data = []
        categories = {}
        assigned = {}

        from models.Tasks import Assigned_Department
        from models.System_Settings import System_Settings

        settings = System_Settings.get_default_settings()

        assigned_departments = Assigned_Department.query.filter_by(
            department_id=department_id,
            period = settings.current_period_id
        ).all()

        print("DRAFTED OPCR ASSIGNED DEPARTMENT TASK LENGTH", len(assigned_departments))

        for ad in assigned_departments:
            cat = ad.main_task.category
            categories[cat.name] = cat.priority_order

        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1],  # priority_number
            reverse=True
        )


        for cat_name, _ in sorted_categories:
            data.append({cat_name: []})


        for ad in assigned_departments:
            main_task = ad.main_task
            category_name = main_task.category.name

            current_data_index = next(
                i for i, d in enumerate(data) if category_name in d
            )

            # Track assigned users (planning view)
            assigned[main_task.mfo] = [user_info["full_name"] for user_info in main_task.get_users_by_dept(department_id)]

            # Planned values only
            data[current_data_index][category_name].append({
                "title": main_task.mfo,

                "summary": {
                    "target": main_task.target_quantity or 0,
                    "actual": 0
                },

                "corrections": {
                    "target": main_task.target_efficiency or 0,
                    "actual": 0
                },

                "working_days": {
                    "target": (
                        1 if main_task.timeliness_mode == "deadline"
                        else main_task.target_timeframe or 0
                    ),
                    "actual": 0
                },

                "description": {
                    "target": main_task.target_accomplishment,
                    "actual": main_task.actual_accomplishment,
                    "alterations": main_task.modification,
                    "time": main_task.time_description,
                    "timeliness_mode": main_task.timeliness_mode,
                    "target_timeframe": main_task.target_timeframe,
                    "target_deadline": (
                        str(main_task.target_deadline)
                        if main_task.target_deadline else None
                    ),
                    "weight": float(ad.task_weight / 100)
                },

                "rating": {
                    "quantity": 0,
                    "efficiency": 0,
                    "timeliness": 0,
                    "average": 0
                },

                "type": main_task.category.type,
                "frequency": 0
            })

        # Get the head
        head = User.query.filter_by(department_id=department_id, role="head").first()
        head_data = {}

        opcr = OPCR.query.filter_by(department_id = department_id).all()[-1]
        opcr_data = opcr.to_dict()

        if head:
            head_data = {
                "fullName": head.first_name + " " + head.last_name,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {
                        "name": head.first_name + " " + head.last_name,
                        "position": head.position.name,
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }
        else:
            head_data = {
                "fullName": "",
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "",
                "individuals": {
                    "review": {
                        "name": "",
                        "position": "",
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }

        return jsonify(ipcr_data=data, assigned=assigned, admin_data=head_data, form_status=1)
  
    def get_opcr(opcr_id):
        from models.System_Settings import System_Settings
        opcr = OPCR.query.get(opcr_id)
        opcr_data = opcr.to_dict()
        data = []
        categories = {}
        assigned = {}

        from models.Tasks import Assigned_Department
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
                department_id=opcr.department_id,
                period = settings.current_period_id
            ).all()
        }

        print("ASSIGNED DEPT CONFIGS",assigned_dept_configs)

        for assigned_pcr in opcr.assigned_pcrs:
            if assigned_pcr.ipcr.status == 0:
                continue
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                if sub_task.status == 0: continue

                if sub_task.main_task.mfo in assigned.keys():
                    assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                else:
                    assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]



        # load settings once
        

        assigned_dept_tasks = (
            Assigned_Department.query
            .filter_by(department_id=opcr.department_id, period = settings.current_period_id)
            .join(Assigned_Department.main_task)
            .all()
        )

        for ad in assigned_dept_tasks:
            main_task = ad.main_task
            category = main_task.category

            if category.status == 0 or main_task.status == 0:
                continue

            # Register category
            if category.name not in categories:
                categories[category.name] = {
                    "priority": category.priority_order,
                    "tasks": []
                }

            # Add task skeleton (NO ACTUALS YET)
            categories[category.name]["tasks"].append({
                "title": main_task.mfo,
                "summary": {
                    "target": main_task.target_quantity or 0,
                    "actual": 0
                },
                "corrections": {
                    "target": main_task.target_efficiency or 0,
                    "actual": 0
                },
                "working_days": {
                    "target": (
                        1 if main_task.timeliness_mode == "deadline"
                        else main_task.target_timeframe or 0
                    ),
                    "actual": 0
                },
                "description": {
                    "target": main_task.target_accomplishment,
                    "actual": main_task.actual_accomplishment,
                    "alterations": main_task.modification,
                    "time": main_task.time_description,
                    "timeliness_mode": main_task.timeliness_mode,
                    "task_weight": ad.task_weight / 100
                },
                "rating": {
                    "quantity": 0,
                    "efficiency": 0,
                    "timeliness": 0,
                    "average": 0,
                    "weighted_avg": 0
                },
                "frequency": 0,
                "_task_id": main_task.id  # INTERNAL KEY
            })


        for cat_name, meta in sorted(
            categories.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        ):
            data.append({cat_name: meta["tasks"]})



        print("lenght of opcr assignedpcrs",len(opcr.assigned_pcrs))

        for assigned_pcr in opcr.assigned_pcrs:
            ipcr = assigned_pcr.ipcr
            if ipcr.status == 0:
                continue

            for sub_task in ipcr.sub_tasks:
                if sub_task.status == 0:
                    continue

                for cat in data:
                    for _, tasks in cat.items():
                        for task in tasks:
                            if task["_task_id"] != sub_task.main_task.id:
                                continue

                            # 🔁 TIMELINESS MODE (same as before)
                            if (
                                sub_task.main_task.timeliness_mode == "deadline"
                                and sub_task.actual_deadline
                                and sub_task.main_task.target_deadline
                            ):
                                days_late = (
                                    sub_task.actual_deadline
                                    - sub_task.main_task.target_deadline
                                ).days
                                actual_working_days = days_late
                                target_working_days = 1
                            else:
                                actual_working_days = sub_task.actual_time or 0
                                target_working_days = sub_task.main_task.target_timeframe or 0

                            # AGGREGATE
                            task["summary"]["actual"] += sub_task.actual_acc
                            task["corrections"]["actual"] += sub_task.actual_mod
                            task["working_days"]["actual"] += actual_working_days                          
                            task["frequency"] += 1

        for cat in data:
            for _, tasks in cat.items():
                for task in tasks:
                    if task["frequency"] == 0:
                        continue

                    quantity = PCR_Service.compute_rating_with_override(
                        "quantity",
                        task["summary"]["target"],
                        task["summary"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    efficiency = PCR_Service.compute_rating_with_override(
                        "efficiency",
                        task["corrections"]["target"],
                        task["corrections"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    timeliness = PCR_Service.compute_rating_with_override(
                        "timeliness",
                        task["working_days"]["target"],
                        task["working_days"]["actual"],
                        task["_task_id"],
                        settings,
                        assigned_dept_configs
                    )

                    avg = PCR_Service.calculateAverage(quantity, efficiency, timeliness)

                    task["rating"] = {
                        "quantity": quantity,
                        "efficiency": efficiency,
                        "timeliness": timeliness,
                        "average": avg,
                        "weighted_avg": avg * task["description"]["task_weight"]
                    }

                    task.pop("_task_id", None)
  


        # Get the head
        head = User.query.filter_by(department_id=opcr.department_id, role="head").first()
        head_data = {}
        if head:
            head_data = {
                "fullName": head.first_name + " " + head.last_name,
                "givenName": head.first_name,
                "middleName": head.middle_name,
                "lastName": head.last_name,
                "position": head.position.name,
                "individuals": {
                    "review": {
                        "name": head.first_name + " " + head.last_name,
                        "position": head.position.name,
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }
        else:
            head_data = {
                "fullName": "",
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "",
                "individuals": {
                    "review": {
                        "name": "",
                        "position": "",
                        "date": ""
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": ""
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": ""
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": ""
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": ""
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": ""
                    }
                }
            }

        return jsonify(ipcr_data=data, assigned=assigned, admin_data=head_data, form_status=opcr.form_status)
    
    def get_master_opcr():
        try:
            from models.System_Settings import System_Settings
            from models.Categories import Category
            from models.PCR import PCR_Service

            settings = System_Settings.get_default_settings()
            current_period = str(settings.current_period_id)

            opcrs = OPCR.query.filter_by(status=1, isMain=True, period = current_period).all()
            print("TOTAL OPCRS:", len(opcrs))
            print("CURRENT PERIOD:", current_period)
            if not opcrs:
                return jsonify(error="There is no OPCR to consolidate"), 400

            data = []
            assigned = {}

            # ✅ PASS 0 — LOAD ALL CATEGORIES (NO DEPT FILTER)
            categories = Category.query.filter_by(status=1, period = current_period).order_by(
                Category.priority_order.desc()
            ).all()

            category_blocks = {}  # category_name -> task list

            task_index = {}  # main_task_id -> task dict

            for category in categories:
                task_list = []

                for main_task in category.main_tasks:
                    if main_task.status == 0:
                        continue

                    task = {
                        "title": main_task.mfo,
                        "summary": {
                            "target": main_task.target_quantity or 0,
                            "actual": 0
                        },
                        "corrections": {
                            "target": main_task.target_efficiency or 0,
                            "actual": 0
                        },
                        "working_days": {
                            "target": (
                                1 if main_task.timeliness_mode == "deadline"
                                else main_task.target_timeframe or 0
                            ),
                            "actual": 0
                        },
                        "description": {
                            "target": main_task.target_accomplishment,
                            "actual": main_task.actual_accomplishment,
                            "alterations": main_task.modification,
                            "time": main_task.time_description,
                            "target_timeframe": main_task.target_timeframe,
                            "target_dealine": main_task.target_deadline,
                            "timeliness_mode": main_task.timeliness_mode
                        },
                        "rating": {
                            "quantity": 0,
                            "efficiency": 0,
                            "timeliness": 0,
                            "average": 0
                        },
                        "frequency": 0,
                        "_task_id": main_task.id
                    }

                    task_list.append(task)
                    task_index[main_task.id] = task

                data.append({category.name: task_list})


            # ✅ PASS 1 — COLLECT ASSIGNED USERS (UNCHANGED LOGIC)
            assigned = {}

            for opcr in opcrs:
                for assigned_pcr in opcr.assigned_pcrs:
                    ipcr = assigned_pcr.ipcr
                    if ipcr.status == 0 or ipcr.form_status == "draft":
                        continue

                    for sub_task in ipcr.sub_tasks:
                        mfo = sub_task.main_task.mfo
                        user_name = f"{ipcr.user.first_name} {ipcr.user.last_name}"

                        assigned.setdefault(mfo, set()).add(user_name)

            assigned = {k: list(v) for k, v in assigned.items()}


            # ✅ PASS 2 — AGGREGATE ALL TASKS (NO DEPARTMENT FILTER)
            for opcr in opcrs:
                for assigned_pcr in opcr.assigned_pcrs:
                    ipcr = assigned_pcr.ipcr
                    if ipcr.status == 0 or ipcr.form_status == "draft":
                        continue

                    for sub_task in ipcr.sub_tasks:
                        task = task_index.get(sub_task.main_task.id)
                        if not task:
                            continue

                        # Timeliness
                        if (
                            sub_task.main_task.timeliness_mode == "deadline"
                            and sub_task.actual_deadline
                            and sub_task.main_task.target_deadline
                        ):
                            actual_days = (
                                sub_task.actual_deadline - sub_task.main_task.target_deadline
                            ).days
                        else:
                            actual_days = sub_task.actual_time or 0

                        task["summary"]["actual"] += sub_task.actual_acc
                        task["corrections"]["actual"] += sub_task.actual_mod
                        task["working_days"]["actual"] += actual_days
                        task["frequency"] += 1

            settings = System_Settings.get_default_settings()

            for task in task_index.values():
                if task["frequency"] == 0:
                    continue

                quantity = PCR_Service.compute_quantity_rating(
                    task["summary"]["target"],
                    task["summary"]["actual"],
                    settings
                )

                efficiency = PCR_Service.compute_efficiency_rating(
                    task["corrections"]["target"],
                    task["corrections"]["actual"],
                    settings
                )

                timeliness = PCR_Service.compute_timeliness_rating(
                    task["working_days"]["target"],
                    task["working_days"]["actual"],
                    settings
                )

                avg = PCR_Service.calculateAverage(quantity, efficiency, timeliness)

                task["rating"] = {
                    "quantity": quantity,
                    "efficiency": efficiency,
                    "timeliness": timeliness,
                    "average": avg
                }

                task.pop("_task_id", None)





            settings = System_Settings.get_default_settings()

            head_data = {
                "fullName": settings.current_president_fullname,
                "givenName": "",
                "middleName": "",
                "lastName": "",
                "position": "College President",
                "individuals": {
                    "review": {"name": settings.current_president_fullname, "position": "College President", "date": ""},
                    "approve": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""},
                    "discuss": {"name": "", "position": "", "date": ""},
                    "assess": {"name": "", "position": "Municipal Administrator", "date": ""},
                    "final": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""},
                    "confirm": {"name": settings.current_mayor_fullname, "position": "PMT Chairperson", "date": ""}
                }
            }

            return jsonify(
                ipcr_data=data,
                assigned=assigned,
                admin_data=head_data,
                form_status=""
            )

        except Exception as e:
            db.session.rollback()
            print("Error in get_master_opcr:", str(e))
            return jsonify(error=str(e)), 500
  

    def collect_all_supporting_documents_by_department(dept_id):
        try:
            from models.System_Settings import System_Settings
            settings = System_Settings.get_default_settings()
            all_supporting_documents = Supporting_Document.query.filter_by(period = settings.current_period_id).all()

            filtered_documents = []

            for document in all_supporting_documents:
                print("COMparing docs", document.ipcr.user.department.id, dept_id)
                if str(document.ipcr.user.department.id) == dept_id:
                    filtered_documents.append(document.to_dict())

            return jsonify(message = filtered_documents), 200
        except Exception as e:
            return jsonify(error= "Collecting supporting documents failed"), 500

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
        
        q = 5 if quantity > 5 else quantity
        e = 5 if efficiency > 5 else efficiency
        t = 5 if timeliness > 5 else timeliness

        calculations = q + e + t
        result = float(calculations/3)
        return result
    
    def get_department_performance_summary():
        """
        Returns department performance averages like:
        [
            {
                "name": "Education",
                "Quantity": 4.2,
                "Efficiency": 3.8,
                "Timeliness": 4.5,
                "Average": 4.17
            },
            ...
        ]
        """
        from models.System_Settings import System_Settings
        settings = System_Settings.get_default_settings()
        current_period = settings.current_period_id

        # Aggregate averages per department through user → sub_task relationship
        # NOTE: use Sub_Task.period because Output is not joined here and Sub_Task.average
        # may not be persisted reliably; compute Average from components to avoid
        # relying on the stored `average` column.
        avg_quantity = func.avg(Sub_Task.quantity)
        avg_efficiency = func.avg(Sub_Task.efficiency)
        avg_timeliness = func.avg(Sub_Task.timeliness)

        results = (
            db.session.query(
                Department.id.label("dept_id"),
                Department.name.label("name"),
                avg_quantity.label("Quantity"),
                avg_efficiency.label("Efficiency"),
                avg_timeliness.label("Timeliness"),
                ((func.coalesce(avg_quantity, 0) + func.coalesce(avg_efficiency, 0) + func.coalesce(avg_timeliness, 0)) / 3.0).label("Average")
            )
            .join(User, User.department_id == Department.id)
            .join(IPCR, IPCR.user_id == User.id)
            .join(Sub_Task, Sub_Task.ipcr_id == IPCR.id)
            .filter(
                Sub_Task.period == current_period,
                Sub_Task.status == 1,
                IPCR.status == 1
            )
            .group_by(Department.id)
            .all()
        )

        # Include all departments (even without any subtasks)
        departments = Department.query.all()
        data = []

        for i in results:
            print("RESULT", i)

        for dept in departments:
            # find match from query results
            match = next((r for r in results if r.dept_id == dept.id), None)
            if match:
                data.append({
                    "name": dept.name,
                    "Quantity": round(match.Quantity or 0, 2),
                    "Efficiency": round(match.Efficiency or 0, 2),
                    "Timeliness": round(match.Timeliness or 0, 2),
                    "Average": round(match.Average or 0, 2)
                })
            else:
                # department with no users or subtasks
                data.append({
                    "name": dept.name,
                    "Quantity": 0,
                    "Efficiency": 0,
                    "Timeliness": 0,
                    "Average": 0
                })

        return jsonify(data), 200
    
    def get_member_pendings(dept_id):
        try:
            all_user = User.query.filter_by(account_status = 1, department_id = dept_id, role = "faculty").all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "head"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    print(ipcr.status == 1 and ipcr.form_status == "pending" and ipcr.isMain == True)
                    
                    if ipcr.status == 1 and ipcr.form_status == "pending" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_member_reviewed():
        try:
            all_user = User.query.all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "head"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == "reviewed" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_member_approved():
        try:
            all_user = User.query.all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "head"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == "approved" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_head_pendings():
        try:
            all_user = User.query.all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "faculty"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    print(ipcr.status == 1 and ipcr.form_status == "pending" and ipcr.isMain == True)
                    
                    if ipcr.status == 1 and ipcr.form_status == "pending" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_head_reviewed():
        try:
            all_user = User.query.all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "faculty"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == "reviewed" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_head_approved():
        try:
            all_user = User.query.all()

            ipcr_to_review = []

            skip_roles = ["administrator", "president", "faculty"]
            for user in all_user:
                if user.role in skip_roles:
                    print(user.first_name)
                    continue

                for ipcr in user.ipcrs:
                    if ipcr.status == 1 and ipcr.form_status == "approved" and ipcr.isMain == True:
                        ipcr_to_review.append(ipcr.department_info()) 

            return jsonify(ipcr_to_review), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    
    def get_opcr_pendings():
        try:
            all_opcr = OPCR.query.filter_by(status = 1, form_status = "pending").all()


            return jsonify([opcr.to_dict() for opcr in all_opcr]), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_opcr_reviewed():
        try:
            all_opcr = OPCR.query.filter_by(status = 1, form_status = "reviewed").all()


            return jsonify([opcr.to_dict() for opcr in all_opcr]), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_opcr_approved():
        try:
            all_opcr = OPCR.query.filter_by(status = 1, form_status = "approved").all()


            return jsonify([opcr.to_dict() for opcr in all_opcr]), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
        



#lagyan ng date period si ipcr
#search subtask by ipcr id



#kusang gumagawa ng sub task, kapag inassign sa user yung tasks
# and problema dun, pag gagawa na ng ibang ipcr, hindi na makagawa ng another sub tasks kase kapag inassign sa user yung tasks, isa lang talaga yung sub tasks
#kailangan ko ng way para makapag assign ako, nang di nagcre create ng sub tasks at ng output
#isa pang problema: scan nalang yung mga naassign na tasks, tapos i render na lahat ng department tasks