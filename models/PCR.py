from app import db
from app import socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.Tasks import Tasks_Service, Assigned_Task, Output, Sub_Task
from models.User import Users, User, Notification_Service
from models.Departments import Department_Service, Department
from utils import FileStorage, ExcelHandler
from sqlalchemy import func, outerjoin

from pprint import pprint
import uuid

class Assigned_PCR(db.Model):
    __tablename__ = "assigned_pcrs"
    id = db.Column(db.Integer, primary_key=True)
    
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default = None)
    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default = None)

    ipcr = db.relationship("IPCR", back_populates = "assigned_pcrs")
    opcr = db.relationship("OPCR", back_populates = "assigned_pcrs")
    department = db.relationship("Department", back_populates = "assigned_pcrs")

class Supporting_Document(db.Model):
    __tablename__ = "supporting_documents"
    id = db.Column(db.Integer, primary_key=True)
    
    file_type = db.Column(db.Text, default="")
    file_name = db.Column(db.Text, default="")
    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"), default = None)
    batch_id = db.Column(db.Text, default = " ")
    status = db.Column(db.Integer, default = 1)

    ipcr = db.relationship("IPCR", back_populates = "supporting_documents")

    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
            "object_name": "documents/" + self.file_name,
            "file_name": self.file_name,
            "batch_id": self.batch_id,
            "ipcr_id": self.ipcr_id,
            "status": self.status,
            "download_url": FileStorage.get_file("documents/" + self.file_name)
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

    def to_dict(self):
        return {
            "id": self.id,
            "file_type": self.file_type,
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
    form_status = db.Column(db.Enum("draft","pending", "reviewed", "approved", "rejected", "archived"), default="draft")

    batch_id = db.Column(db.Text, default="")
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates = "ipcr", cascade = "all, delete")

    def count_sub_tasks(self):
        return len([main_task.to_dict() for main_task in self.sub_tasks])
    
    def info(self):
        return {
            "id" : self.id,
            "user": self.user_id
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
        if self.user.role == "faculty":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()

            president = User.query.filter_by(role = "president").first()
            
            self.reviewed_by = department_head.first_name + " " + department_head.last_name if department_head else ""
            self.rev_position = department_head.position.name if department_head else ""

            self.approved_by = president.first_name + " " + president.last_name if president else ""
            self.app_position = president.position.name if president else ""

            self.discussed_with = self.user.first_name + " " + self.user.last_name 
            self.dis_position = self.user.position.name

            self.assessed_by = department_head.first_name + " " + department_head.last_name if department_head else ""
            self.ass_position = department_head.position.name if department_head else ""

            self.final_rating_by = president.first_name + " " + president.last_name if president else ""
            self.fin_position = president.position.name if president else ""

            self.confirmed_by = "HON. MARIA ELENA L. GERMAR"
            self.con_position = "PMT Chairperson"
            print("GEtting the user ipcr info")
            db.session.commit()
        elif self.user.role == "head":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()

            president = User.query.filter_by(role = "president").first()
            
            self.reviewed_by = president.first_name + " " + president.last_name if president else ""
            self.rev_position = president.position.name if president else ""

            self.approved_by = president.first_name + " " + president.last_name if president else ""
            self.app_position = president.position.name if president else ""

            self.discussed_with = department_head.first_name + " " + department_head.last_name if department_head else ""
            self.dis_position = department_head.position.name if department_head else ""

            self.assessed_by = president.first_name + " " + president.last_name if president else ""
            self.ass_position = president.position.name if president else ""

            self.final_rating_by = president.first_name + " " + president.last_name if president else ""
            self.fin_position = president.position.name if president else ""

            self.confirmed_by = "HON. MARIA ELENA L. GERMAR"
            self.con_position = "PMT Chairperson"
            

        elif self.user.role == "president":
            department_head =User.query.filter_by(department_id = self.user.department_id, role = "head").first()

            president = User.query.filter_by(role = "president").first()
            
            self.reviewed_by = president.first_name + " " + president.last_name if president else ""
            self.rev_position = president.position.name if president else ""

            self.approved_by = president.first_name + " " + president.last_name if president else ""
            self.app_position = president.position.name if president else ""

            self.discussed_with = department_head.first_name + " " + department_head.last_name if department_head else ""
            self.dis_position = department_head.position.name if department_head else ""

            self.assessed_by = president.first_name + " " + president.last_name if president else ""
            self.ass_position = president.position.name if president else ""

            self.final_rating_by = president.first_name + " " + president.last_name if president else ""
            self.fin_position = president.position.name if president else ""

            self.confirmed_by = "HON. MARIA ELENA L. GERMAR"
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
            "review" : {
                "name": self.reviewed_by,
                "position": self.rev_position,
                "date": str(self.rev_date)
            },
            "approve" : {
                "name": self.approved_by,
                "position": self.app_position,
                "date": str(self.app_date)
            },
            "discuss" : {
                "name": self.discussed_with,
                "position": self.dis_position,
                "date": str(self.dis_date)
            },
            "assess" : {
                "name": self.assessed_by,
                "position": self.ass_position,
                "date": str(self.ass_date)
            },
            "final" : {
                "name": self.final_rating_by,
                "position": self.fin_position,
                "date": str(self.fin_date)
            },
            "confirm" : {
                "name": self.confirmed_by,
                "position": self.con_position,
                "date": str(self.con_date)
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

    ipcrs = db.relationship("IPCR", back_populates = "opcr", cascade = "all, delete")
    isMain = db.Column(db.Boolean, default = False)
    status = db.Column(db.Integer, default = 1)
    form_status = db.Column(db.Enum("draft","pending", "approved", "rejected", "archived"), default="draft")

    created_at = db.Column(db.DateTime, default=datetime.now)
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates = "opcr", cascade = "all, delete")

    rev_date = db.Column(db.DateTime, default = None)
    app_date = db.Column(db.DateTime, default = None)
    dis_date = db.Column(db.DateTime, default = None)
    ass_date = db.Column(db.DateTime, default = None)
    fin_date = db.Column(db.DateTime, default = None)
    con_date = db.Column(db.DateTime, default = None)

    def count_ipcr(self):
        return len([ipcr.to_dict() for ipcr in self.ipcrs])
    
    
    def to_dict(self):
        department_head =User.query.filter_by(department_id = self.department_id, role = "head").first()

        president = User.query.filter_by(role = "president").first()
          

        self.reviewed_by = department_head.first_name + " " + department_head.last_name if department_head else ""
        self.rev_position = department_head.position.name if department_head else ""

        self.approved_by = president.first_name + " " + president.last_name if president else ""
        self.app_position = president.position.name if president else ""

        self.discussed_with = department_head.first_name + " " + department_head.last_name if department_head else ""
        self.dis_position = department_head.position.name if department_head else ""

        self.assessed_by = president.first_name + " " + president.last_name if president else ""
        self.ass_position = president.position.name if president else ""

        self.final_rating_by = president.first_name + " " + president.last_name if president else ""
        self.fin_position = president.position.name if president else ""

        self.confirmed_by = "HON. MARIA ELENA L. GERMAR"
        self.con_position = "PMT Chairperson"
        db.session.commit()

        print("eto si president: ", self.approved_by)  
        return {
            "id" : self.id,
            "ipcr_count": self.count_ipcr(),
            "form_status": self.form_status,
            "created_at": str(self.created_at),
            "review" : {
                "name": self.reviewed_by,
                "position": self.rev_position,
                "date": str(self.rev_date)
            },
            "approve" : {
                "name": self.approved_by,
                "position": self.app_position,
                "date": str(self.app_date)
            },
            "discuss" : {
                "name": self.discussed_with,
                "position": self.dis_position,
                "date": str(self.dis_date)
                
            },
            "assess" : {
                "name": self.assessed_by,
                "position": self.ass_position,
                "date": str(self.ass_date)
            },
            "final" : {
                "name": self.final_rating_by,
                "position": self.fin_position,
                "date": str(self.fin_date)
            },
            "confirm" : {
                "name": self.confirmed_by,
                "position": self.con_position,
                "date": str(self.con_date)
                
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
    def generate_IPCR(user_id, main_task_id_array):
        try:
            # start batch
            current_batch_id = str(uuid.uuid4())

            # create IPCR and flush so id is available
            new_ipcr = IPCR(user_id=user_id, batch_id=current_batch_id)
            db.session.add(new_ipcr)
            db.session.flush()   # <-- new_ipcr.id now available

            # For each main task, create batch-scoped Assigned_Task (if not exist)
            # and create Output (which will create Sub_Task inside Output.__init__)
            for mt_id in main_task_id_array:
                # skip if there's already an output for same user/task/batch
                existing_output = Output.query.filter_by(
                    user_id=user_id, main_task_id=mt_id, batch_id=current_batch_id
                ).first()

                if existing_output:
                    # already created for this batch — skip
                    continue

                # create batch-scoped Assigned_Task if it doesn't exist for this batch
                existing_assigned = Assigned_Task.query.filter_by(
                    user_id=user_id, main_task_id=mt_id, batch_id=current_batch_id
                ).first()

                if not existing_assigned:
                    new_assigned = Assigned_Task(
                        user_id=user_id,
                        main_task_id=mt_id,
                        is_assigned=False,
                        batch_id=current_batch_id
                    )
                    db.session.add(new_assigned)

                # create new Output (this will create Sub_Task in Output.__init__)
                new_output = Output(
                    user_id=user_id,
                    main_task_id=mt_id,
                    batch_id=current_batch_id,
                    ipcr_id=new_ipcr.id
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
                ipcr.rev_date = datetime.now()
                ipcr.ass_date = datetime.now()
                ipcr.dis_date = datetime.now()
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
                ipcr.rev_date = datetime.now()
                ipcr.ass_date = datetime.now()
                ipcr.dis_date = datetime.now()
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
                ipcr.rev_date = datetime.now()
                ipcr.ass_date = datetime.now()
                ipcr.dis_date = datetime.now()
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
            ipcr.app_date = datetime.now()
            ipcr.fin_date = datetime.now()
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
                opcr.dis_date = datetime.now()
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

            
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.isMain = True
            ipcr.form_status = "pending"

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
        
    def assign_pres_ipcr(ipcr_id, user_id):
        try:
            user = User.query.get(user_id)

            if user == None:
                return jsonify(message = "There is no user with that id"), 400

            for ipcr in user.ipcrs:
                ipcr.isMain = False

            
            ipcr = IPCR.query.get(ipcr_id)
            ipcr.isMain = True
            ipcr.form_status = "approved"

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

            

            
            ipcr = OPCR.query.get(opcr_id)
            ipcr.isMain = True
            ipcr.form_status = "pending"

            socketio.emit("assign")

            db.session.commit()
            Notification_Service.notify_department_heads(dept_id, f"{dept.name} submitted their latest OPCR.")
            Notification_Service.notify_presidents(f"{dept.name}  as its latest IPCR.")
            
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

    def record_supporting_document(file_type, file_name, ipcr_id, batch_id):
        try:
            ipcr = IPCR.query.get(ipcr_id)
            new_supporting_document = Supporting_Document(file_type = file_type, file_name = file_name, ipcr_id = ipcr_id, batch_id = batch_id)
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
        

    #create a many to many relationship between ipcr and opcr
    #fix the creation of opcr
    def create_opcr(dept_id, ipcr_ids):
        try:
            all_opcr = OPCR.query.filter_by(department_id = dept_id).all()

            for opcr in all_opcr:
                opcr.isMain = False
                opcr.status = 0
                db.session.commit()


            new_opcr = OPCR(department_id = dept_id, isMain = True)
            db.session.add(new_opcr)
            db.session.flush()
            
            for ipcr_id in ipcr_ids:
                ipcr = IPCR.query.get(ipcr_id)
                new_assigned_pcr = Assigned_PCR(opcr_id = new_opcr.id, ipcr_id = ipcr_id, department_id = dept_id)
                Notification_Service.notify_user(ipcr.user.id, f"Your IPCR: #{ipcr_id} has been consolidated to OPCR: #{new_opcr.id}.")
                Notification_Service.notify_presidents(f"{ipcr.user.department.name} created a new OPCR.")
                db.session.add(new_assigned_pcr)
            
            db.session.commit()

            socketio.emit("opcr", "created")
            Notification_Service.notify_department(dept_id, f"A new OPCR has been created for this department.")

            return jsonify(message="OPCR successfully created."), 200
        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def generate_opcr(opcr_id):

        opcr = OPCR.query.get(opcr_id)
        opcr_data = opcr.to_dict()
        data = []
        categories = []

        assigned = {}

        for assigned_pcr in opcr.assigned_pcrs:
            
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                
                if sub_task.main_task.category.name not in categories:
                    categories.append(sub_task.main_task.category.name)
                    #print(sub_task.main_task.mfo)
                if sub_task.main_task.mfo in assigned.keys():
                    assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                else:
                    assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]

        
        for cat in categories:
            data.append({
                cat:[]
            })

        for assigned_pcr in opcr.assigned_pcrs:


            for sub_task in assigned_pcr.ipcr.sub_tasks:
                #sub_task.main_task.category.name
                print(sub_task.main_task.category.name)
                
                current_data_index = 0
                for cat in data:
                    for name, arr in cat.items():

                        

                        if sub_task.main_task.category.name == name:


                            #check mo kung exzisting na yung task sa loob ng category
                            current_task_index = 0
                            found = False
                            for tasks in data[current_data_index][name]:
                                
                                if sub_task.mfo == tasks["title"]:
                                    found = True
                                    data[current_data_index][name][current_task_index]["summary"]["target"] += sub_task.target_acc
                                    data[current_data_index][name][current_task_index]["summary"]["actual"] += sub_task.actual_acc
                                    data[current_data_index][name][current_task_index]["corrections"]["target"] += sub_task.target_mod
                                    data[current_data_index][name][current_task_index]["corrections"]["actual"] += sub_task.actual_mod
                                    data[current_data_index][name][current_task_index]["working_days"]["target"] += sub_task.target_time
                                    data[current_data_index][name][current_task_index]["working_days"]["actual"] += sub_task.actual_time

                                    data[current_data_index][name][current_task_index]["rating"]["quantity"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["summary"]["target"], data[current_data_index][name][current_task_index]["summary"]["actual"])
                                    data[current_data_index][name][current_task_index]["rating"]["efficiency"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["corrections"]["target"], data[current_data_index][name][current_task_index]["corrections"]["actual"])
                                    data[current_data_index][name][current_task_index]["rating"]["timeliness"] = PCR_Service.calculateTimeliness(data[current_data_index][name][current_task_index]["working_days"]["target"], data[current_data_index][name][current_task_index]["working_days"]["actual"])

                                    data[current_data_index][name][current_task_index]["rating"]["average"] = PCR_Service.calculateAverage(data[current_data_index][name][current_task_index]["rating"]["quantity"], data[current_data_index][name][current_task_index]["rating"]["efficiency"], data[current_data_index][name][current_task_index]["rating"]["timeliness"])
                                current_task_index += 1     

                            if not found:
                                data[current_data_index][name].append({
                                "title": sub_task.mfo,
                                "summary": {
                                    "target": sub_task.target_acc, "actual": sub_task.actual_acc
                                },
                                "corrections": {
                                    "target": sub_task.target_mod, "actual": sub_task.actual_mod
                                },
                                "working_days": {
                                    "target": sub_task.target_time, "actual": sub_task.actual_time
                                },
                                "description":{
                                    "target": sub_task.main_task.target_accomplishment,
                                    "actual": sub_task.main_task.actual_accomplishment,
                                    "alterations": sub_task.main_task.modification,
                                    "time": sub_task.main_task.time_description,
                                },
                                "rating": {
                                    "quantity": 0,
                                    "efficiency": 0,
                                    "timeliness": 0,
                                    "average": 0,
                                }
                            })
                            

                    current_data_index += 1

                    
        #get the head
        head_data = {}
        head = User.query.filter_by(department_id = opcr.department_id, role = "head").first()
        
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
                        "date": "2025-03-10"
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": "2025-03-12"
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": "2025-03-15"
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": "2025-03-16"
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": "2025-03-20"
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": "2025-03-21"
                    }
                }
            }      
        
        file_url = ExcelHandler.createNewOPCR(data = data, assigned = assigned, admin_data = head_data)

        return file_url
    
    def generate_master_opcr():

        opcrs = OPCR.query.filter_by(isMain = True, form_status = "approved").all()
        data = []
        categories = []

        if not opcrs:
            return jsonify(error = "There is no approved opcr to consolidate"), 400

        assigned = {}

        for opcr in opcrs:
            for assigned_pcr in opcr.assigned_pcrs:
            
                for sub_task in assigned_pcr.ipcr.sub_tasks:
                    
                    if sub_task.main_task.category.name not in categories:
                        categories.append(sub_task.main_task.category.name)
                        #print(sub_task.main_task.mfo)
                    if sub_task.main_task.mfo in assigned.keys():
                        assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                    else:
                        assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]

            
            for cat in categories:
                data.append({
                    cat:[]
                })

            for assigned_pcr in opcr.assigned_pcrs:


                for sub_task in assigned_pcr.ipcr.sub_tasks:
                    #sub_task.main_task.category.name
                    print(sub_task.main_task.category.name)
                    
                    current_data_index = 0
                    for cat in data:
                        for name, arr in cat.items():

                            

                            if sub_task.main_task.category.name == name:


                                #check mo kung exzisting na yung task sa loob ng category
                                current_task_index = 0
                                found = False
                                for tasks in data[current_data_index][name]:
                                    
                                    if sub_task.mfo == tasks["title"]:
                                        found = True
                                        data[current_data_index][name][current_task_index]["summary"]["target"] += sub_task.target_acc
                                        data[current_data_index][name][current_task_index]["summary"]["actual"] += sub_task.actual_acc
                                        data[current_data_index][name][current_task_index]["corrections"]["target"] += sub_task.target_mod
                                        data[current_data_index][name][current_task_index]["corrections"]["actual"] += sub_task.actual_mod
                                        data[current_data_index][name][current_task_index]["working_days"]["target"] += sub_task.target_time
                                        data[current_data_index][name][current_task_index]["working_days"]["actual"] += sub_task.actual_time

                                        data[current_data_index][name][current_task_index]["rating"]["quantity"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["summary"]["target"], data[current_data_index][name][current_task_index]["summary"]["actual"])
                                        data[current_data_index][name][current_task_index]["rating"]["efficiency"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["corrections"]["target"], data[current_data_index][name][current_task_index]["corrections"]["actual"])
                                        data[current_data_index][name][current_task_index]["rating"]["timeliness"] = PCR_Service.calculateTimeliness(data[current_data_index][name][current_task_index]["working_days"]["target"], data[current_data_index][name][current_task_index]["working_days"]["actual"])

                                        data[current_data_index][name][current_task_index]["rating"]["average"] = PCR_Service.calculateAverage(data[current_data_index][name][current_task_index]["rating"]["quantity"], data[current_data_index][name][current_task_index]["rating"]["efficiency"], data[current_data_index][name][current_task_index]["rating"]["timeliness"])
                                    current_task_index += 1     

                                if not found:
                                    data[current_data_index][name].append({
                                    "title": sub_task.mfo,
                                    "summary": {
                                        "target": sub_task.target_acc, "actual": sub_task.actual_acc
                                    },
                                    "corrections": {
                                        "target": sub_task.target_mod, "actual": sub_task.actual_mod
                                    },
                                    "working_days": {
                                        "target": sub_task.target_time, "actual": sub_task.actual_time
                                    },
                                    "description":{
                                        "target": sub_task.main_task.target_accomplishment,
                                        "actual": sub_task.main_task.actual_accomplishment,
                                        "alterations": sub_task.main_task.modification,
                                        "time": sub_task.main_task.time_description,
                                    },
                                    "rating": {
                                        "quantity": 0,
                                        "efficiency": 0,
                                        "timeliness": 0,
                                        "average": 0,
                                    }
                                })
                                

                        current_data_index += 1

        

                    
        #get the head
        head_data = {}
        head = User.query.filter_by(role = "president").first()
        
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
                        "date": "2025-03-10"
                    },
                    "approve": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": "2025-03-21"
                    },
                    "discuss": {
                        "name": "",
                        "position": "",
                        "date": "2025-03-15"
                    },
                    "assess": {
                        "name": "",
                        "position": "Municipal Administrator",
                        "date": "2025-03-16"
                    },
                    "final": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": "2025-03-21"
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": "2025-03-21"
                    }
                }
            }      
        
        file_url = ExcelHandler.createNewMasterOPCR(data = data, assigned = assigned, admin_data = head_data)

        return jsonify(link = file_url), 200
    
    def get_opcr(opcr_id):
        opcr = OPCR.query.get(opcr_id)
        opcr_data = opcr.to_dict()
        data = []
        categories = []
        assigned = {}

        for assigned_pcr in opcr.assigned_pcrs:
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                if sub_task.main_task.category.name not in categories:
                    categories.append(sub_task.main_task.category.name)
                    #print(sub_task.main_task.mfo)
                if sub_task.main_task.mfo in assigned.keys():
                    assigned[sub_task.main_task.mfo].append(f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}")
                else:
                    assigned[sub_task.main_task.mfo] = [f"{assigned_pcr.ipcr.user.first_name} {assigned_pcr.ipcr.user.last_name}"]

        for cat in categories:
            data.append({
                cat:[]
            })

        for assigned_pcr in opcr.assigned_pcrs:
            for sub_task in assigned_pcr.ipcr.sub_tasks:
                #sub_task.main_task.category.name
                print(sub_task.main_task.category.name)
                current_data_index = 0
                for cat in data:
                    for name, arr in cat.items():
                        if sub_task.main_task.category.name == name:
                            #check mo kung exzisting na yung task sa loob ng category
                            current_task_index = 0
                            found = False
                            for tasks in data[current_data_index][name]:
                                if sub_task.mfo == tasks["title"]:
                                    found = True
                                    data[current_data_index][name][current_task_index]["summary"]["target"] += sub_task.target_acc
                                    data[current_data_index][name][current_task_index]["summary"]["actual"] += sub_task.actual_acc
                                    data[current_data_index][name][current_task_index]["corrections"]["target"] += sub_task.target_mod
                                    data[current_data_index][name][current_task_index]["corrections"]["actual"] += sub_task.actual_mod
                                    data[current_data_index][name][current_task_index]["working_days"]["target"] += sub_task.target_time
                                    data[current_data_index][name][current_task_index]["working_days"]["actual"] += sub_task.actual_time

                                    data[current_data_index][name][current_task_index]["rating"]["quantity"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["summary"]["target"], data[current_data_index][name][current_task_index]["summary"]["actual"])
                                    data[current_data_index][name][current_task_index]["rating"]["efficiency"] = PCR_Service.calculateQuantity(data[current_data_index][name][current_task_index]["corrections"]["target"], data[current_data_index][name][current_task_index]["corrections"]["actual"])
                                    data[current_data_index][name][current_task_index]["rating"]["timeliness"] = PCR_Service.calculateTimeliness(data[current_data_index][name][current_task_index]["working_days"]["target"], data[current_data_index][name][current_task_index]["working_days"]["actual"])

                                    data[current_data_index][name][current_task_index]["rating"]["average"] = PCR_Service.calculateAverage(data[current_data_index][name][current_task_index]["rating"]["quantity"], data[current_data_index][name][current_task_index]["rating"]["efficiency"], data[current_data_index][name][current_task_index]["rating"]["timeliness"])
                                current_task_index += 1     

                            if not found:
                                data[current_data_index][name].append({
                                "title": sub_task.mfo,
                                "summary": {
                                    "target": sub_task.target_acc, "actual": sub_task.actual_acc
                                },
                                "corrections": {
                                    "target": sub_task.target_mod, "actual": sub_task.actual_mod
                                },
                                "working_days": {
                                    "target": sub_task.target_time, "actual": sub_task.actual_time
                                },
                                "description":{
                                    "target": sub_task.main_task.target_accomplishment,
                                    "actual": sub_task.main_task.actual_accomplishment,
                                    "alterations": sub_task.main_task.modification,
                                    "time": sub_task.main_task.time_description,
                                },
                                "rating": {
                                    "quantity": 0,
                                    "efficiency": 0,
                                    "timeliness": 0,
                                    "average": 0,
                                }
                            })
                    current_data_index += 1

                    
        #get the head
        head = User.query.filter_by(department_id = opcr.department_id, role = "head").first()
        
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
                        "date": "2025-03-10"
                    },
                    "approve": {
                        "name": opcr_data["approve"]["name"],
                        "position": opcr_data["approve"]["position"],
                        "date": "2025-03-12"
                    },
                    "discuss": {
                        "name": opcr_data["discuss"]["name"],
                        "position": opcr_data["discuss"]["position"],
                        "date": "2025-03-15"
                    },
                    "assess": {
                        "name": opcr_data["assess"]["name"],
                        "position": opcr_data["assess"]["position"],
                        "date": "2025-03-16"
                    },
                    "final": {
                        "name": opcr_data["final"]["name"],
                        "position": opcr_data["final"]["position"],
                        "date": "2025-03-20"
                    },
                    "confirm": {
                        "name": "Hon. Maria Elena L. Germar",
                        "position": "PMT Chairperson",
                        "date": "2025-03-21"
                    }
                }
            }
        

        return jsonify(ipcr_data = data, assigned = assigned, admin_data = head_data, form_status = opcr.form_status)
        

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
        result = calculations/3
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

        # Aggregate averages per department through user → sub_task relationship
        results = (
            db.session.query(
                Department.id.label("dept_id"),
                Department.name.label("name"),
                func.avg(Sub_Task.quantity).label("Quantity"),
                func.avg(Sub_Task.efficiency).label("Efficiency"),
                func.avg(Sub_Task.timeliness).label("Timeliness"),
                func.avg(Sub_Task.average).label("Average")
            )
            .join(User, User.department_id == Department.id)
            .join(IPCR, IPCR.user_id == User.id)
            .join(Sub_Task, Sub_Task.ipcr_id == IPCR.id)
            .group_by(Department.id)
            .all()
        )

        # Include all departments (even without any subtasks)
        departments = Department.query.all()
        data = []

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