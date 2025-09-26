from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.User import User
from app import socketio

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default = "category")

    manager_id = db.Column(db.Integer, default = 0)
    status = db.Column(db.Integer, default = 1)

    users = db.relationship("User", back_populates="department")
    opcrs = db.relationship("OPCR", back_populates="department")

    main_tasks = db.relationship("Main_Task", back_populates = "department")

    def count_tasks(self):
        return len([main_task.info() for main_task in self.main_tasks])

    def count_users(self):
        return len([user.to_dict() for user in self.users])
    
    def count_opcr(self):
        return len([opcr.to_dict() for opcr in self.opcrs])
    
    def count_ipcr(self):
        count = 0
        for opcr in self.opcrs:
            stat = opcr.to_dict()
            ipcr_count = stat["ipcr_count"]
            count += ipcr_count

        return count
    
    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
        }


    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "manager": self.manager_id,
            "icon": self.icon,
            "users": [user.to_dict() for user in self.users],
            "opcrs":[opcr.to_dict() for opcr in self.opcrs],
            "user_count": self.count_users(),
            "opcr_count": self.count_opcr(),
            "ipcr_count": self.count_ipcr(),
            "main_tasks": [main_task.info() for main_task in self.main_tasks],
            "main_tasks_count": self.count_tasks()
        }
    

class Department_Service():
    def get_all_departments():
        try:
            all_depts = Department.query.filter_by(status=1).all()
            all_converted = [dept.to_dict() for dept in all_depts]

            return jsonify(all_converted), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_department(id):
        try:
            all_depts = Department.query.filter_by(id = id).first()
            
            if all_depts:
                dept = all_depts.to_dict()
                return jsonify(dept), 200
            else:
                return jsonify(message = "There is no department with that id"), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_members(dept_id, offset = 0, limit = 10):
        try:
            print("finding members of dept id:", dept_id)
            users = User.query.filter_by(department_id = dept_id).order_by(User.id.asc()).offset(offset).limit(limit).all()


            converted_user = [user.to_dict() for user in users]
            return jsonify(converted_user), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def create_department(data):
        try:
            print("department data:", data)
            new_department = Department(name = data["department_name"], icon = data["icon"])
            db.session.add(new_department)
            db.session.commit()

            return jsonify(message = "Department successfully created."), 200
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
        
    def update_department(id,data):
        try:
            print("department data:", data)
            found_department = Department.query.get(id)

            if not found_department:
                return jsonify({"error": "Department not found"}), 404
            
            found_department.name = data["department_name"]
            found_department.icon = data["icon"]

            db.session.commit()

            return jsonify(message = "Department successfully updated."), 200
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
    
    def remove_user_from_department(id):
        try:
            user = User.query.get(id)

            user.department_id = None
            db.session.commit()
            print("UPDSTING")
            socketio.emit("user_modified", "user removed from department")
            return jsonify(message="User successfully removed."), 200
        
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
    
    def archive_department(id):
        try:
            found_department = Department.query.get(id)

            if not found_department:
                return jsonify({"error": "Department not found"}), 404
            
            found_department.status = 0

            db.session.commit()

            return jsonify(message = "Department successfully archived."), 200
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
        
       
    
