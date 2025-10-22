from app import db
from app import socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.User import User, Notification_Service
from sqlalchemy import func, case
from collections import defaultdict

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

    

    def user_info(self):
        return self.user.info()
     
    def task_info(self):
        return self.main_task.info()
    
    def assigned_task_info(self):
        return {
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

    status = db.Column(db.Integer, default = 1)

    def __init__(self, user_id, main_task_id, batch_id, ipcr_id):
        super().__init__()
        self.user_id = user_id
        self.batch_id = batch_id
        self.ipcr_id = ipcr_id
        self.main_task = Main_Task.query.get(main_task_id)

        # Create subtask automatically by copying from main task
        new_sub_task = Sub_Task(
            mfo=self.main_task.mfo,
            main_task=self.main_task,
            batch_id = batch_id,
            ipcr_id = self.ipcr_id
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

    #one category and one department
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default = None)
    department = db.relationship("Department", back_populates = "main_tasks")

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates = "main_tasks")

    sub_tasks = db.relationship("Sub_Task", back_populates = "main_task", cascade = "all, delete")
    outputs = db.relationship("Output", back_populates="main_task", cascade = "all, delete")

    assigned_tasks = db.relationship("Assigned_Task", back_populates="main_task", cascade = "all, delete")

    

    def get_users(self):
        all_user = []
        for assigned in self.assigned_tasks:            
            all_user.append(assigned.user_info())
        
        return all_user
    
    def get_users_by_dept(self, id):
        all_user = []
        for assigned in self.assigned_tasks:
            print(assigned.user_info())
            
            if assigned.user_info()["department_name"] == "NONE": 
                continue
            if  str(assigned.user_info()["department"]["id"]) == id:
                all_user.append(assigned.user_info())
        
        return all_user
    
    
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

            "category": self.category.info()
        }

    def info(self):
        return {
            "id" : self.id,
            "name": self.mfo,
            "department": self.department.name if self.department else "General",
            "created_at": str(self.created_at),
            "target_accomplishment": self.target_accomplishment,
            "actual_accomplishment": self.actual_accomplishment,
            "time_measurement" : self.time_description,
            "modifications": self.modification,
            "users": [assigned.user_info() for assigned in self.assigned_tasks],
            "status": self.status,
            "category": self.category.info() if self.category else "NONE",
            "sub_tasks": [sub.info() for sub in self.sub_tasks]
        }

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "actual_acc": self.actual_accomplishment,
            "created_at": str(self.created_at),
            "status": self.status,

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

    

    batch_id = db.Column(db.Text, nullable=False)

    def calculateQuantity(self):
        rating = 0
        target = self.target_acc
        actual = self.actual_acc

        if target == 0:
            self.quantity = 0
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

    def calculateEfficiency(self):
        
        target = self.target_mod
        actual = self.actual_mod
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
    
    def calculateTimeliness(self):
        
        target = self.target_time
        actual = self.actual_time
        rating = 0
        if target == 0:
            self.timeliness = 0
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
    
    def calculateAverage(self):
        
        calculations = self.quantity + self.efficiency + self.timeliness
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

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_acc,
            "target_time": self.target_time,
            "target_mod": self.target_mod,
            "actual_acc": self.actual_acc,
            "actual_time": self.actual_time,
            "actual_mod": self.actual_mod,
            "created_at": str(self.created_at),
            "status": self.status,
            "batch_id": self.batch_id,

            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "average": self.average,

         
            "ipcr": self.ipcr.info(),
            "main_task": self.main_task.ipcr_info()
        }
  
 

class Tasks_Service():

    def test_ipcr():
        from models.PCR import IPCR
        ipcr = IPCR.query.get(9)
        return jsonify(ipcr.to_dict()), 200
    def get_main_tasks():
        try:
            all_main_tasks = Main_Task.query.filter_by(status = 1).all()
            converted_main_tasks = [main_task.info() for main_task in all_main_tasks]
        
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
        
    def create_main_task(data):
        try:
            print("creating task right now")
            new_main_task = Main_Task(
                mfo = data["task_name"],
                department_id  = int(data["department"]) if int(data["department"]) != 0 else None,
                target_accomplishment = data["task_desc"],
                actual_accomplishment = data["past_task_desc"],
                accomplishment_editable =  int(data["accomplishment_editable"]),
                time_editable =  int(data["time_editable"]),
                modification_editable =  int(data["modification_editable"]),
                time_description = data["time_measurement"],
                modification =  data["modification"],
                category_id = int(data["id"])
            )
            print("registered task")
            Notification_Service.notify_department(dept_id=data["department"], msg="A new output has been added to the department.")
            Notification_Service.notify_presidents( msg="A new output has been added.")
            Notification_Service.notify_administrators( msg="A new output has been added.")
            db.session.add(new_main_task)
            db.session.commit()
            return jsonify(message="Output successfully created."), 200
        
        except IntegrityError as e:
            db.session.rollback()
            print(str(e), "Integrity")
            return jsonify(error="Output already exists"), 400
        
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

            if found_task == None:
                return jsonify(message="No output with that ID"), 400
            
            if len(data) == 0:
                return jsonify(message="You must submit data to update fields"), 400

            if "name" in data:
                found_task.mfo = data["name"]

            if "target_accomplishment" in data:
                found_task.target_accomplishment = data["target_accomplishment"]

            if "actual_accomplishment" in data:
                found_task.actual_accomplishment = data["actual_accomplishment"]

            if "time_description" in data:
                found_task.time_description = data["time_description"]

            if "modification" in data:
                found_task.modification = data["modification"]

            if "status" in data:
                print("status detected", data["status"])
                found_task.status = data["status"]

            db.session.commit()
            Notification_Service.notify_everyone(msg=f"The task: {found_task.mfo} has been updated.")
            return jsonify(message = "Output successfully updated."), 200
        
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
    
    def assign_user(task_id, user_id):
        try:
            #search ko muna lahat ng assigned task kung existing na siya

            new_assigned_task = Assigned_Task(user_id = user_id, main_task_id = task_id, is_assigned = True)
            

            db.session.add(new_assigned_task)
            db.session.flush()

            db.session.commit()
            user = User.query.get(user_id)
            socketio.emit("user_assigned", "user assigned")

            Notification_Service.notify_user(user_id, msg=f"The output: { new_assigned_task.main_task.mfo} has been assigned to this account.")
            Notification_Service.notify_presidents( msg=f"The output: { new_assigned_task.main_task.mfo} has been assigned to {user.first_name + " " + user.last_name}.")
            

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
            new_output = Output(user_id = user_id, main_task_id = task_id, batch_id = current_batch_id, ipcr_id=ipcr_id)
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
            new_output = Output(user_id = user_id, main_task_id = task_id, batch_id = current_batch_id, ipcr_id=ipcr_id)
            new_assigned_tasks = Assigned_Task(user_id=user_id, main_task_id = task_id, batch_id = current_batch_id)
            
            print("new output", new_output.batch_id)
                        
            db.session.add(new_output)
            db.session.add(new_assigned_tasks)
            db.session.commit()
            socketio.emit("ipcr_added", "user assigned")

            return jsonify(message = "Output successfully added."), 200
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
            task = Main_Task.query.get(task_id)

            #buburahin niya yung mga task na di naman nasa department
            for output in task.outputs:
                if not output.user.department.id == dept_id:
                    db.session.delete(output)
                    db.session.commit()

            if task == None:
                return jsonify(message = "Output is not found."), 400
            
            task.department_id = dept_id

            db.session.commit()
            print("task id: ", task_id)
            print("dept id: ", dept_id)

            Notification_Service.notify_department(dept_id=dept_id, msg=f"The output: {task.mfo} has been assigned to the office.")
            Notification_Service.notify_administrators(msg=f"The output: {task.mfo} has been assigned to {task.department.name}.")
            Notification_Service.notify_presidents(msg=f"The output: {task.mfo} has been assigned to {task.department.name}.")
            socketio.emit("department_assigned", "department assigned")
            socketio.emit("user_assigned", "user assigned")

            return jsonify(message = "Output successfully assigned."), 200
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
            Notification_Service.notify_user(user_id=user_id, msg=f"An output has been unassigned from you.")
            Notification_Service.notify_presidents(msg=f"{user.first_name + " " + user.last_name} has been removed from output: {task.mfo}.")
            
            return jsonify(message = "Output successfully removed."), 200
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
            found_task = Main_Task.query.filter_by(department_id = dept_id, id = task_id).all()[0]
            if found_task == None:
                 return jsonify(""), 200
            converted = found_task.get_users_by_dept(id = dept_id) 
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
            all_general_tasks = Main_Task.query.filter(Main_Task.department_id.is_(None), Main_Task.status == 1).all()
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
            all_department_tasks = Main_Task.query.filter_by(department_id = id, status = 1).all()
            converted = [task.info() for task in all_department_tasks]
            return jsonify(converted), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_all_general_tasks():
        try:
            all_general_tasks = Main_Task.query.filter_by(department_id = None, status = 1).all()
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
            found_task = Main_Task.query.get(id)

            if found_task == None:
                return jsonify(message="No Output with that ID"), 400
            
            found_task.status = 0
            db.session.commit()
            Notification_Service.notify_everyone(f"The output: {found_task.mfo} has been archived.")

            return jsonify(message = "Output successfully archived."), 200
        
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
        
    def remove_task_from_dept(id):
        try:
            found_task = Main_Task.query.get(id)
            dept_id = found_task.department_id
            

            if found_task == None:
                return jsonify(message="No task with that ID"), 400
            
            found_task.department_id = None
            db.session.commit()
            socketio.emit("task_modified", "task modified")
            socketio.emit("department_assigned", "task modified")
            Notification_Service.notify_department(dept_id,f"The output: {found_task.mfo} has been removed from this office.")
            Notification_Service.notify_heads(f"The output: {found_task.mfo} has been assigned as a general output.")
            Notification_Service.notify_presidents(f"The output: {found_task.mfo} has been assigned as a general output.")
            Notification_Service.notify_administrators(f"The output: {found_task.mfo} has been assigned as a general output.")

            return jsonify(message = "Output successfully removed."), 200
        
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
                return jsonify(message = "There is no outputs found."), 400
            
            if assigned_task == None:
                return jsonify(message = "There is no assigned outputs found."), 400
            
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

        q = 5 if quantity > 5 else quantity
        e = 5 if efficiency > 5 else efficiency
        t = 5 if timeliness > 5 else timeliness
        calculations = q + e + t
        result = calculations/3
        return result


        
    def update_sub_task_fields(sub_task_id, field, value):
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


            if field == "actual_acc":
                ipcr.actual_acc = int(value)
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_time":
                ipcr.actual_time = int(value)
                ipcr.average = Tasks_Service.calculateAverage(ipcr.quantity, ipcr.efficiency,ipcr.timeliness)

            if field == "actual_mod":
                ipcr.actual_mod = int(value)
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
                ipcr.average = int(value)
                
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
        results = (
            db.session.query(
                Output.user_id,
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("overall_average")
            )
            .join(Sub_Task, Output.id == Sub_Task.output_id)
            .filter(Output.main_task_id == task_id)
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
            quantity = sub_task.calculateQuantity()
            efficiency = sub_task.calculateEfficiency()
            timeliness = sub_task.calculateTimeliness()
            average = sub_task.calculateAverage()

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

        results = (
            db.session.query(
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("avg_overall")
            )
            .join(Output, Output.id == Sub_Task.output_id)
            .filter(Output.user_id == user_id)
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

        all_tasks = Main_Task.query.filter_by(status=1).all()
        data = []

        for task in all_tasks:
            total_quantity = 0
            total_efficiency = 0
            total_timeliness = 0
            total_average = 0
            count = 0

            for sub_task in task.sub_tasks:
                # Dynamically compute each rating
                quantity = sub_task.calculateQuantity()
                efficiency = sub_task.calculateEfficiency()
                timeliness = sub_task.calculateTimeliness()
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