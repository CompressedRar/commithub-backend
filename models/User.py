from app import db
from app import socketio
from pprint import pprint
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError

from flask import jsonify
from models.Positions import Positions, Position
from FirebaseApi.config import upload_file
from utils.Generate import generate_default_password
from utils.Email import send_email, send_reset_email
from models.Logs import Log_Service

import uuid
from argon2 import PasswordHasher
import jwt

# gagawa ng output base sa id
#pagtapos gumawa ng mga output, kukunin id ni ipcr
#kuhanin yung mga outputs ni user
#i assign yung ipcr id sa subtasks ng output ni user
# si output ang kukuni kay user, si sub task ang lalagyan ng ipcr
class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates = "notifications")
    created_at = db.Column(db.DateTime, default=datetime.now)
    read = db.Column(db.Boolean, default=False)
    
    user = db.relationship("User", back_populates = "notifications")


    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "created_at": str(self.created_at),
            "read":self.read
        }
    
class Notification_Service():

    def mark_as_read(id_arrays):
        try:
            for id in id_arrays:
                notif = Notification.query.get(id)
                notif.read = True
            
            db.session.commit()

            return jsonify(message = "Success") , 200
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

    def get_user_notification(user_id):
        try:
            all_notification = Notification.query.filter_by(user_id = user_id).all()

            return jsonify([notif.to_dict() for notif in all_notification]), 200
        
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

    def notify_everyone(msg):
        try:
            users = User.query.all()

            if not users:
                return

            for user in users:
                new_notification = Notification(user_id = user.id, name = msg)
                db.session.add(new_notification)


            db.session.commit()
            socketio.emit("notification")
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
    def notify_user(user_id, msg):
        try:
            users = User.query.filter_by(id = user_id).first()

            if not users:
                return

            new_notification = Notification(user_id = user_id, name = msg)
            db.session.add(new_notification)


            db.session.commit()
            socketio.emit("notification")
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

    def notify_department(dept_id, msg):
        try:
            users = User.query.filter_by(department_id = dept_id).all()

            for user in users:
                new_notification = Notification(user_id = user.id, name = msg)
                db.session.add(new_notification)


            db.session.commit()
            socketio.emit("notification")
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
        
    def notify_heads(msg):
        try:
            heads = User.query.filter_by(role = "head").all()

            if not heads:
                return
            
            for head in heads:
                new_notif = Notification(user_id = head.id, name = msg)
                db.session.add(new_notif)
            
            db.session.commit()
            socketio.emit("notification")

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
        
    def notify_department_heads(dept_id, msg):
        try:
            heads = User.query.filter_by(role = "head", department_id = dept_id).all()

            if not heads:
                return
            
            for head in heads:
                new_notif = Notification(user_id = head.id, name = msg)
                db.session.add(new_notif)
            
            db.session.commit()
            socketio.emit("notification")

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
        
    def notify_presidents(msg):
        try:
            pres = User.query.filter_by(role = "president").all()

            if not pres:
                return

            for president in pres:
                new_notif = Notification(user_id = president.id, name = msg)
                db.session.add(new_notif)
            
            db.session.commit()
            socketio.emit("notification")

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
        
    def notify_administrators(msg):
        try:
            pres = User.query.filter_by(role = "administrator").all()

            if not pres:
                return

            for president in pres:
                new_notif = Notification(user_id = president.id, name = msg)
                db.session.add(new_notif)
            
            db.session.commit()
            socketio.emit("notification")

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
        

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default="", nullable=True)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False, default="commithubnc")
    profile_picture_link = db.Column(db.String(200), nullable=True)

    
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.Enum("faculty", "head", "president", "administrator"), default="faculty")

    active_status = db.Column(db.Boolean, default=True)
    account_status = db.Column(db.Integer, default = 1)

    # FK references table name "positions"
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), default=1)
    position = db.relationship("Position", back_populates="users")

    managed_dept_id = db.Column(db.Integer)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=1, nullable = True)
    department = db.relationship("Department", back_populates="users")

    outputs = db.relationship("Output", back_populates="user")

    ipcrs = db.relationship("IPCR", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user", cascade = "all, delete")

    assigned_tasks = db.relationship("Assigned_Task", back_populates="user")
    
    def info(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "profile_picture_link": self.profile_picture_link,
            "position": self.position.info(),
            "role": self.role,
            
            "department_id":self.department_id,
            "department": self.department.info() if self.department else "NONE",
            "department_name": self.department.info()["name"] if self.department else "NONE",
        }
    
    def tasks(self):
        return {
            "assigned_tasks" : [assigned.task_info() for assigned in self.assigned_tasks]            
        }
    
    def assigned_task(self):
        return {
            "assigned_tasks" : [assigned.assigned_task_info() for assigned in self.assigned_tasks]            
        }
    
    def calculatePerformance(self):
        all_output_total = 0
        total = 0
        for output in self.outputs:
            total += 1
            all_output_total += output.sub_task.calculateAverage()
        

        
        return all_output_total / total if total != 0 else 0

    def to_dict(self):
        active_ipcrs = []

        for ipcr in self.ipcrs:
            if ipcr.status == 1:
                active_ipcrs.append(ipcr.to_dict())

        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            
            "role": self.role,
            "email": self.email,
            "password": self.password,
            "profile_picture_link": self.profile_picture_link,
            "active_status": self.active_status,
            "account_status": self.account_status,
            "created_at": str(self.created_at),

            "position":self.position.info() if self.position else "NONE",
            "department": self.department.info() if self.department else "NONE",
            "ipcrs": active_ipcrs,
            "ipcrs_count": len([ipcr.to_dict() for ipcr in self.ipcrs]),
            "main_tasks_count": len(self.outputs),
            "avg_performance": self.calculatePerformance()
        }


class Users():

    


    def check_email_if_exists(email):
        try:
            all_users = User.query.filter_by(email = email).all()
            if all_users:
                return jsonify(message = "Email was already taken."), 200
            else:
                return jsonify(message = "Available"), 200
            
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        

    def authenticate_if_email_exists(email):
        try:
            all_users = User.query.filter_by(email = email, account_status = 1).all()
            
            if all_users:
                return all_users[0].to_dict()
            else:
                return False
            
        except OperationalError as e:
            print(e)
            #db.session.rollback()
            return False

        except Exception as e:
            #db.session.rollback()
            return False
        
    def does_president_exists():
        try:
            users  = User.query.all()

            for user in users:
                if user.role == "president": return jsonify(True), 200

            return jsonify(False), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def does_admin_exists():
        try:
            users  = User.query.all()

            for user in users:
                if user.role == "administrator": return jsonify(True), 200

            return jsonify(False), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        

    def get_all_users():
        try:
            users  = User.query.all()

            return jsonify([user.to_dict() for user in users]), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_assigned_tasks(id):
        try:
            user = User.query.get(id)

            if user:
                return jsonify(user.tasks()), 200
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
    
    def get_user_assigned_tasks(id):
        try:
            user = User.query.get(id)

            if user:
                return jsonify(user.assigned_task()), 200
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_user(id):
        try:
            user = User.query.get(id)

            if user:
                return jsonify(user.to_dict()), 200
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def update_user(id, data, rq):
        from models.Tasks import Main_Task, Sub_Task, Output
        print("form data", data)
        try:
            user = User.query.get(id)

            if not user:
                return jsonify(error="There is no user with that ID"), 400

            # Handle profile picture upload
            profile = rq.files.get("profile_picture_link")
            if profile:
                res = upload_file(profile)
                user.profile_picture_link = res

            # Basic info updates
            fields = ["first_name", "last_name", "middle_name", "email", "password", "position", "role"]
            for field in fields:
                if field in data:
                    setattr(user, field, data[field])

            # ✅ Handle department change logic
            if "department" in data:
                new_department_id = int(data["department"])
                old_department_id = user.department_id

                if new_department_id != old_department_id:
                    print(f"Changing department: {old_department_id} → {new_department_id}")

                    # Get user's active IPCR (if any)
                    active_ipcr = next((ipcr for ipcr in user.ipcrs if ipcr.status == 1), None)

                    # 🗑️ Delete outputs tied to old department tasks
                    for output in list(user.outputs):
                        if output.main_task and output.main_task.department_id == old_department_id:
                            db.session.delete(output)

                    # ➕ Add new department tasks (if active IPCR exists)
                    if active_ipcr:
                        new_tasks = Main_Task.query.filter_by(department_id=new_department_id, status=1).all()
                        for task in new_tasks:
                            new_output = Output(
                                user_id=user.id,
                                main_task_id=task.id,
                                ipcr_id=active_ipcr.id,
                                batch_id=str(uuid.uuid4())
                            )
                            db.session.add(new_output)

                    # Update user's department
                    user.department_id = new_department_id

            # ✅ Commit once for all changes
            db.session.commit()

            # Notify connected clients
            socketio.emit("user_modified", "modified")
            socketio.emit("user_updated", "modified")

            return jsonify(message="User successfully updated"), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            print("Update user error:", e)
            return jsonify(error=str(e)), 500
    
    def delete_user(id):
        try:
            user = User.query.get(id)

            if user:
                db.session.delete(user)
                db.session.commit()

                return jsonify(message = "User successfully deleted"), 200
    
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
    

    def reset_password(id):
       
        try:
            user = User.query.get(id)
            
            if user:
                new_default_password = "commithubnc"
                msg = "Hello!, The password reset was done to this account. The default password is: " + new_default_password 

                ph = PasswordHasher()
                hashed_password = ph.hash(new_default_password)

                user.password = hashed_password
                send_reset_email(user.email, msg)
                Notification_Service.notify_user(user.id, "The account password has been reset.")

                socketio.emit("user_modified", "modified")
                db.session.commit()
                

                return jsonify(message = "Password successfully reset."), 200
            

            
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
    

    def archive_user(id):
        try:
            user = User.query.get(id)

            if user:
                user.account_status = 0
                db.session.commit()
                socketio.emit("user_modified", "user deactivated")
                Notification_Service.notify_user(user.id, "This account has been deactivated.")
                Notification_Service.notify_department_heads(user.department.id, f"The account of {user.first_name + " " + user.last_name} has been deactivated.")
                Notification_Service.notify_presidents(f"The account of {user.first_name + " " + user.last_name} has been deactivated.")
                Notification_Service.notify_administrators(f"The account of {user.first_name + " " + user.last_name} has been deactivated.")
                
                

                return jsonify(message = "User successfully deactivated"), 200
    
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def unarchive_user(id):
        try:
            user = User.query.get(id)

            if user:
                user.account_status = 1
                db.session.commit()
                socketio.emit("user_modified", "user deactivated")
                Notification_Service.notify_user(user.id, "This account has been reactivated.")
                return jsonify(message = "User successfully reactivated"), 200
    
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def change_password(user_id, password):
        try:
            user = User.query.get(user_id)
            ph = PasswordHasher()
            hashed_password = ph.hash(password)
            user.password = hashed_password
            db.session.commit()
            return jsonify(message = "Success"), 200
        
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500


    def add_new_user(data, profile_picture):
        print(profile_picture)
        try:
            #new_default_password = generate_default_password()
            new_default_password = "commithubnc"
            msg = "Hello!, Your default password is: " + new_default_password 

            print(msg)

            ph = PasswordHasher()
            hashed_password = ph.hash(new_default_password)
            
            res = upload_file(profile_picture)

            dept_id = data["department"]

            new_user = User(
                first_name=data["first_name"],
                last_name=data["last_name"],
                middle_name=data["middle_name"] if data["middle_name"] else "",
                position_id = data["position"],
                department_id=dept_id,
                role = data["role"],            
                email=data["email"],
                password= hashed_password,
                profile_picture_link = res
            
            )
            db.session.flush()
            send_email(data["email"], msg)

            db.session.add(new_user)
            db.session.commit()
            
            socketio.emit("user_created", "user added")
            Notification_Service.notify_user(new_user.id, "Welcome to Commithub! Start by creating your own IPCR.")
            Notification_Service.notify_department_heads(data["department"],f"{data["first_name"] + " " + data["last_name"]} joined {new_user.department.name}.")
            Notification_Service.notify_administrators(f"{data["first_name"] + " " + data["last_name"]} joined {new_user.department.name}.")
            Notification_Service.notify_presidents(f"{data["first_name"] + " " + data["last_name"]} joined {new_user.department.name}.")
            

            return jsonify(message="Account creation is successful."), 200

        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Email already exists"), 400
        
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
    
    def generate_token(data):
        token = jwt.encode(
            data, "priscilla", algorithm="HS256"
        )

        return token
    
    def count_users_by_depts():
        all_users = User.query.all()
        all_converted = [user.to_dict() for user in all_users]
        ccs_count = 0
        educ_count = 0
        hm_count = 0
        other_count = 0

        for user in all_converted:
            if user["department"] == "NONE":
                continue
            
            dept = user["department"]["name"]
            print(dept)
            if dept == "Computing Studies":
                ccs_count += 1
            elif dept == "Education":
                educ_count += 1
            elif dept == "Hospitality Management":
                hm_count += 1
            else:
                other_count += 1
        
        return jsonify(message = {
            "cs": ccs_count,
            "educ" : educ_count,
            "hm": hm_count,
            "other": other_count,
            "all": len(all_converted)
        }), 200
    
    def assign_department_head(user_id, dept_id):
        try:
            department = Department.query.get(dept_id)

            if department == None:
                return jsonify(message = "There is no department with that id."), 400

            for user in department.users:
                if user.role == "administrator" or user.role == "president": continue
                user.role = "faculty"

            user = User.query.get(user_id)

            if user == None:
                return jsonify(message = "There is no user with that id."), 400

            user.role = "head"
            db.session.commit()
            Notification_Service.notify_user(user.id, f"This account is now the office head of {department.name}.")
            Notification_Service.notify_department(department.id, f"{user.first_name + " " + user.last_name} has been assigned as the new office head of {department.name}.")
            Notification_Service.notify_heads(msg = f"{user.first_name + " " + user.last_name} has been assigned as the new office head of {department.name}.")
            Notification_Service.notify_presidents(msg = f"{user.first_name + " " + user.last_name} has been assigned as the new office head of {department.name}.")
            socketio.emit("department", "office head assigned")
            return jsonify(message = "Office head successfully assigned."), 200
        
        except OperationalError as e:
            db.session.rollback()
            print(str(e),  "OPERATIONAL")
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e), "EXCEPTION")
            return jsonify(error=str(e)), 500
        
    def remove_department_head(user_id):
        try:        
            user = User.query.get(user_id)

            if user == None:
                return jsonify(message = "There is no user with that id."), 400

            user.role = "faculty"
            db.session.commit()

            socketio.emit("department", "department head removed")
            Notification_Service.notify_user(user.id, "This account has been removed from being office head.")
            Notification_Service.notify_department(dept_id=user.department_id, msg = f"The head of {user.department.name} has been removed from its position.")
            Notification_Service.notify_presidents(msg = f"The head of {user.department.name} has been removed from its position.")
            return jsonify(message = "Office head successfully removed."), 200
        
        except OperationalError as e:
            db.session.rollback()
            print(str(e),  "OPERATIONAL")
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e), "EXCEPTION")
            return jsonify(error=str(e)), 500


    def authenticate_user(login_data):
        print("entry pointof authentication")
        try:
            email = login_data["email"]
            password = login_data["password"]

            userCheck = Users.authenticate_if_email_exists(email)
            
            if userCheck:
                
                ph = PasswordHasher()
                

                result = ph.verify(hash=userCheck["password"], password = password)
                
                print(result)

                if result:
                    token = Users.generate_token(userCheck)
                    return jsonify(message ="Authenticated.", token = token), 200
                
                else:
                    return jsonify(error ="Invalid Credentials"), 400

            else:
                return jsonify(error = "Invalid Credentials"), 400
            
        except OperationalError as e:
            db.session.rollback()
            print(str(e),  "OPERATIONAL")
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e), "EXCEPTION")
            return jsonify(error=str(e)), 500
        

    
        
    


    

            
"JEX8iu1hAA"




def test_create_user():
    position = Position().query.get(1)
    user_data = {
        "first_name": "test_name",
        "middle_name": "test_name",
        "last_name": "test_name",
        "position": 1,
        "department": "test_department",
        "email": "test_email1",
        "password": "test_password"
    }

    result = Users.add_new_user(data = user_data)
    return result
        






