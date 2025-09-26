from app import db
from app import socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.Tasks import Tasks_Service, Assigned_Task, Output
from models.User import Users, User
import uuid

class IPCR(db.Model):
    __tablename__ = "ipcr"
    id = db.Column(db.Integer, primary_key=True)
    
    reviewed_by = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    #one ipcr to one user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="ipcrs")

    opcr_id = db.Column(db.Integer, db.ForeignKey("opcr.id"), default = None)
    opcr = db.relationship("OPCR", back_populates="ipcrs")

    sub_tasks = db.relationship("Sub_Task", back_populates = "ipcr", cascade = "all, delete")
    outputs = db.relationship("Output", back_populates = "ipcr")

    isMain = db.Column(db.Boolean, default = False)
    status = db.Column(db.Integer, default = 1)
    form_status = db.Column(db.Enum("pending", "reviewed", "approved"), default="pending")

    batch_id = db.Column(db.Text, default="")

    def count_sub_tasks(self):
        return len([main_task.to_dict() for main_task in self.sub_tasks])
    
    def info(self):
        return {
            "id" : self.id,
            "user": self.user_id
        }


    def to_dict(self):
        return {
            "id" : self.id,
            "user": self.user_id,
            "sub_tasks": [main_task.to_dict() for main_task in self.sub_tasks],
            "sub_tasks_count": self.count_sub_tasks(),
            "created_at": str(self.created_at),
            "form_status": self.form_status,
            "isMain": self.isMain,
            "batch_id": self.batch_id
        }
    
class OPCR(db.Model):
    __tablename__ = "opcr"
    id = db.Column(db.Integer, primary_key=True)
    
    reviewed_by = db.Column(db.Text, default="")
    approved_by = db.Column(db.Text, default="")
    discussed_with = db.Column(db.Text, default="")
    assessed_by = db.Column(db.Text, default="")
    final_rating_by = db.Column(db.Text, default="")
    confirmed_by = db.Column(db.Text, default="")
    #one ipcr to one opcr

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    department = db.relationship("Department", back_populates="opcrs")

    ipcrs = db.relationship("IPCR", back_populates = "opcr", cascade = "all, delete")
    isMain = db.Column(db.Boolean, default = False)
    status = db.Column(db.Integer, default = 1)
    form_status = db.Column(db.Enum("pending", "reviewed", "approved"), default="pending")

    def count_ipcr(self):
        return len([ipcr.to_dict() for ipcr in self.ipcrs])
    
    
    
    def to_dict(self):
        return {
            "id" : self.id,
            "user": self.user_id,
            "ipcr_count": self.count_ipcr()
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

            return jsonify(message="IPCR successfully created"), 200

        except Exception as e:
            db.session.rollback()
            print("generate_IPCR error:", e)
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
            socketio.emit("ipcr", "ipcr assigned as main")

            db.session.commit()

            return jsonify(message = "IPCR successfully assigned."), 200
        
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