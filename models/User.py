from app import db
from app import socketio

from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from models.Positions import Positions, Position
from FirebaseApi.config import upload_file
from utils.Generate import generate_default_password
from utils.Email import send_email
from models.Logs import Log_Service
from argon2 import PasswordHasher
import jwt


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default="", nullable=True)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False, default="12345678")
    profile_picture_link = db.Column(db.String(200), nullable=True)

    
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.Enum("faculty", "head", "administrator"), default="faculty")

    active_status = db.Column(db.Boolean, default=True)
    account_status = db.Column(db.Integer, default = 1)

    # FK references table name "positions"
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), default=1)
    position = db.relationship("Position", back_populates="users")

    managed_dept_id = db.Column(db.Integer)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), default=1, nullable = True)
    department = db.relationship("Department", back_populates="users")

    #multiple ipcrs for one user
    outputs = db.relationship("Output", back_populates="user")

    ipcrs = db.relationship("IPCR", back_populates="user")
    notifications = db.relationship("Notification", back_populates="user", cascade = "all, delete")
    
    def info(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "profile_picture_link": self.profile_picture_link,

            "department": self.department.info() if self.department else "NONE",
            "department_name": self.department.info()["name"] if self.department else "NONE",
        }

    def to_dict(self):
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
            "ipcrs": [ipcr.to_dict() for ipcr in self.ipcrs],
            "ipcrs_count": len([ipcr.to_dict() for ipcr in self.ipcrs]),
            "main_tasks_count": len(self.outputs)         
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
            all_users = User.query.filter_by(email = email).all()
            
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
        
    def update_user(id, data):
        try:
            user = User.query.get(id)

            if user:

                if "first_name" in data:
                    user.first_name = data["first_name"] 
                    db.session.commit()

                if "last_name" in data:
                    user.last_name = data["last_name"] 
                    db.session.commit()

                if "middle_name" in data:
                    user.middle_name = data["middle_name"] 
                    db.session.commit()

                if "email" in data:
                    user.email = data["email"] 
                    db.session.commit()

                if "password" in data:
                    user.password = data["password"] 
                    db.session.commit()

                if "profile_picture_link" in data:
                    user.profile_picture_link = data["profile_picture_link"] 
                    db.session.commit()
                
                if "department" in data:
                    user.department_id = data["department"] 
                    db.session.commit()

                if "position" in data:
                    user.position_id = data["position"] 
                    db.session.commit()
                
                if "role" in data:
                    user.role = data["role"] 
                    db.session.commit()

                return jsonify(message = "User successfully updated"), 200
            

            
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
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
        
    

    def archive_user(id):
        try:
            user = User.query.get(id)

            if user:
                user.account_status = 0
                db.session.commit()
                socketio.emit("user_modified", "user deactivated")
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
                return jsonify(message = "User successfully reactivated"), 200
    
            else: 
                return jsonify(error= "There is no user with that id"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500


    def add_new_user(data, profile_picture):
        print(profile_picture)
        try:
            new_default_password = generate_default_password()
            msg = "Hello!, Your default password is: " + new_default_password 

            print(msg)

            ph = PasswordHasher()
            hashed_password = ph.hash(new_default_password)
            
            
            res = upload_file(profile_picture)

            new_user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            middle_name=data["middle_name"],
            position_id = data["position"],
            department_id=data["department"],
            
            email=data["email"],
            password= hashed_password,
            profile_picture_link = res
            
            )
            send_email(data["email"], msg)

            db.session.add(new_user)
            db.session.commit()
            
            socketio.emit("user_created", "user added")

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


    def authenticate_user(login_data):
        print("entry pointof authentication")
        try:
            email = login_data["email"]
            password = login_data["password"]

            userCheck = Users.authenticate_if_email_exists(email)
            print("User check: ", userCheck)
            if userCheck:
                
                ph = PasswordHasher()
                

                result = ph.verify(hash=userCheck["password"], password = password)
                
                print(result)

                if result:
                    token = Users.generate_token(userCheck)
                    return jsonify(message ="Authenticated.", token = token), 200
                
                else:
                    return jsonify(message ="Invalid Credentials"), 200

            else:
                return jsonify(message = "Invalid Credentials"), 200
            
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
        






