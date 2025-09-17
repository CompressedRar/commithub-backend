from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.User import User

class Output(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))

    user = db.relationship("User", back_populates = "outputs")
    main_task = db.relationship("Main_Task", back_populates = "outputs")

    def user_info(self):
        return{
            "users": [use.info() for use in self.user ]
        }
    
    def task_info(self):
        return{
            "users": [task.info() for task in self.main_task ]
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

    #one category and one department
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default = None)
    department = db.relationship("Department", back_populates = "main_tasks")

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates = "main_tasks")

    sub_tasks = db.relationship("Sub_Task", back_populates = "main_task", cascade = "all, delete")
    outputs = db.relationship("Output", back_populates="main_task")

    def get_users(self):
        return {
            "users": self.outputs
        }

    def info(self):
        return {
            "id" : self.id,
            "name": self.mfo,
            "department": self.department.name if self.department else "General",
            "created_at": self.created_at,
            "target_accomplishment": self.target_accomplishment,
            "actual_accomplishment": self.actual_accomplishment,
            "time_measurement" : self.time_description,
            "modifications": self.modification,
            "users": [output.info() for output in self.outputs],
            "status": self.status
        }

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "actual_acc": self.actual_accomplishment,
            "created_at": self.created_at,
            "status": self.status,

            "category": self.category_id,
            "sub_tasks": [sub_task.to_dict() for sub_task in self.sub_tasks],
        }
    
class Sub_Task(db.Model):
    __tablename__ = "sub_tasks"
    id = db.Column(db.Integer, primary_key=True)
    
    mfo = db.Column(db.Text, nullable=False)


    """
     target : {
                description: test,
                value: 0
                }
    """
    target_accomplishment = db.Column(JSON)
    target_time_description = db.Column(JSON)
    target_modification = db.Column(JSON)

    actual_accomplishment = db.Column(JSON)
    actual_time_description = db.Column(JSON)
    actual_modification = db.Column(JSON)

    created_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Boolean, default=True)
    
    quantity = db.Column(db.Integer, default = 0)
    efficiency = db.Column(db.Integer, default = 0)
    timeliness = db.Column(db.Integer, default = 0)
    average = db.Column(db.Integer, default = 0)

    main_task_id = db.Column(db.Integer, db.ForeignKey("main_tasks.id"))
    main_task = db.relationship("Main_Task", back_populates="sub_tasks")

    ipcr_id = db.Column(db.Integer, db.ForeignKey("ipcr.id"))
    ipcr = db.relationship("IPCR", back_populates="sub_tasks")    


    def to_dict(self):
        return {
            "id": self.id,
            "title": self.mfo,
            "target_acc": self.target_accomplishment,
            "target_time": self.target_time_description,
            "target_mod": self.target_modification,
            "actual_acc": self.actual_accomplishment,
            "actual_time": self.actual_time_description,
            "actual_acc": self.actual_modification,
            "created_at": self.created_at,
            "status": self.status,

            "quantity": self.quantity,
            "efficiency": self.efficiency,
            "timeliness": self.timeliness,
            "average": self.average,

            "ipcr": self.ipcr_id,
            "main_task": self.main_task_id
        }
 

class Tasks_Service():
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
                department_id  = int(data["department"]),
                target_accomplishment = data["task_desc"],
                actual_accomplishment = data["task_desc"],
                accomplishment_editable =  int(data["accomplishment_editable"]),
                time_editable =  int(data["time_editable"]),
                modification_editable =  int(data["modification_editable"]),
                time_description = data["time_measurement"],
                modification =  data["modification"],
                category_id = int(data["id"])
            )
            print("registered task")
            db.session.add(new_main_task)
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

            if found_task == None:
                return jsonify(message="No task with that ID"), 400
            
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
        
    def archive_task(id):
        try:
            found_task = Main_Task.query.get(id)

            if found_task == None:
                return jsonify(message="No task with that ID"), 400
            
            found_task.status = 0
            db.session.commit()
            return jsonify(message = "Task successfully archived."), 200
        
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
        