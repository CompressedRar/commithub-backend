from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.Tasks import Tasks_Service, Assigned_Task
from models.User import Users, User

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
            "created_at": self.created_at
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
        
        
        new_ipcr = IPCR(user_id = user_id)
        db.session.add(new_ipcr)
        
        for id in main_task_id_array:
            new_assigned = Assigned_Task(user_id = user_id, main_task_id = id)
            db.session.add(new_assigned)
            Tasks_Service.create_user_output(id, user_id)
        print("creawting outputs done")

        user = User.query.get(user_id)
        user_outputs = [output.sub_task for output in user.outputs] 
        
        for tasks in user_outputs:
            #eto nas yung id
            tasks.ipcr_id = new_ipcr.id

        db.session.commit()        
        return jsonify(message = "IPCR successfully created"), 200
    
#search subtask by ipcr id



#kusang gumagawa ng sub task, kapag inassign sa user yung tasks
# and problema dun, pag gagawa na ng ibang ipcr, hindi na makagawa ng another sub tasks kase kapag inassign sa user yung tasks, isa lang talaga yung sub tasks
#kailangan ko ng way para makapag assign ako, nang di nagcre create ng sub tasks at ng output
#isa pang problema: scan nalang yung mga naassign na tasks, tapos i render na lahat ng department tasks