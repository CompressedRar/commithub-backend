from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from models.Positions import Positions, Position

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), default="", nullable=True)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False, default="12345678")
    profile_picture_link = db.Column(db.String(50), nullable=True)

    department = db.Column(db.String(50), default="staff", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    role = db.Column(db.Enum("faculty", "head", "administrator"), default="faculty")

    active_status = db.Column(db.Boolean, default=True)

    # FK references table name "positions"
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), default=1)
    position = db.relationship("Position", back_populates="users")


    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "middle_name": self.middle_name,
            "deparment": self.department,

            "role": self.role,
            "email": self.email,
            "profile_picture_link": self.profile_picture_link,
            "active-status": self.active_status,
            "created_at": self.created_at
        }


class Users():
    def check_username_if_exists():
        all_users = User.query.all()
        print(all_users)

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
                    user.department = data["department"] 
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



    def add_new_user(data):
        try:
            new_user = User(
            first_name=data["first_name"],
            last_name=data["last_name"],
            middle_name=data["middle_name"],
            position_id = data["position"],
            department=data["department"],
            
            email=data["email"],
            password=data["password"],
            profile_picture_link = ""
            
            )

            db.session.add(new_user)
            db.session.commit()

            return jsonify(message="Account creation succeed"), 200

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
        






