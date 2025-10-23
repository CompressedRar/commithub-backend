from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from models.User import User, Notification_Service
from models.Tasks import Sub_Task, Output
from app import socketio
from sqlalchemy import func, outerjoin

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default = "")

    manager_id = db.Column(db.Integer, default = 0)
    status = db.Column(db.Integer, default = 1)

    users = db.relationship("User", back_populates="department")
    opcrs = db.relationship("OPCR", back_populates="department")

    main_tasks = db.relationship("Main_Task", back_populates = "department")
    assigned_pcrs = db.relationship("Assigned_PCR", back_populates = "department")

    def count_tasks(self):
        return len([main_task.info() for main_task in self.main_tasks])

    def count_users(self):
        return len([user.to_dict() for user in self.users])
    
    def count_opcr(self):
        return len([opcr.to_dict() for opcr in self.opcrs])
    
    def count_ipcr(self):
        ipcr_count = 0
        for user in self.users:
            ipcr_count += len(user.ipcrs)            
        return ipcr_count
    
    def is_head_occupied(self):
        for user in self.users:
            if user.role == "head": return True        
        return False
    
    
    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
        }
    
    def collect_all_ipcr(self):
        all_ipcr = []
        for user in self.users:
            for ipcr in user.ipcrs:
                if ipcr.status == 1:
                    all_ipcr.append(ipcr.department_info())
                
        return all_ipcr
    
    def collect_all_opcr(self):
        all_ipcr = []
        
        for opcr in self.opcrs:
            if opcr.status == 1:
                all_ipcr.append(opcr.to_dict())

        return all_ipcr


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
            "main_tasks_count": self.count_tasks(),     
            "is_head_occupied": self.is_head_occupied()       #true or false
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
                return jsonify(message = "There is no office with that id"), 200
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_department_head(dept_id):
        try:
            department_head = User.query.filter_by(department_id = dept_id, role = "head").first()

            if department_head:
                return jsonify(department_head.info()), 200
            
            return jsonify({
                "id": "",
                "first_name": "",
                "last_name": "",
                "middle_name": "",
                "profile_picture_link": "",
                "position": "",
            }), 400
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

            department_name = data.get("department_name", "").strip()
            icon = data.get("icon", "").strip()

            if not department_name:
                return jsonify(error="Department name is required."), 400

            # Check for duplicate department name (case-insensitive)
            existing_department = Department.query.filter(
                func.lower(Department.name) == department_name.lower()
            ).first()

            if existing_department:
                return jsonify(error="Department name already exists."), 400

            # Create the new department
            new_department = Department(name=department_name, icon=icon)
            db.session.add(new_department)
            db.session.commit()

            # Send notifications (use single quotes in f-strings to avoid syntax issues)
            Notification_Service.notify_heads(f"{department_name} has been added.")
            Notification_Service.notify_presidents(f"{department_name} has been added.")
            Notification_Service.notify_administrators(f"{department_name} has been added.")

            return jsonify(message="Office successfully created."), 200

        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Department name already exists."), 400

        except DataError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Invalid data format."), 400

        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error."), 500

        except Exception as e:
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
            Notification_Service.notify_heads(f"{data["department_name"]} has been updated.")
            Notification_Service.notify_presidents(f"{data["department_name"]} has been updated.")
            Notification_Service.notify_administrators(f"{data["department_name"]} has been updated.")

            return jsonify(message = "Office successfully updated."), 200
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
            prev_dept = user.department.name

            user.department_id = None
            db.session.commit()
            print("UPDSTING")
            socketio.emit("user_modified", "user removed from department")

            Notification_Service.notify_heads(f"{user.first_name + " " + user.last_name} has been removed from {prev_dept}.")
            Notification_Service.notify_presidents(f"{user.first_name + " " + user.last_name} has been removed from {prev_dept}.")
            Notification_Service.notify_administrators(f"{user.first_name + " " + user.last_name} has been removed from {prev_dept}.")
            return jsonify(message="Member successfully removed."), 200
        
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
                return jsonify({"error": "Office not found"}), 404
            
            found_department.status = 0

            db.session.commit()
            Notification_Service.notify_heads(f"{found_department.name} has been removed archived.")
            Notification_Service.notify_presidents(f"{found_department.name} has been removed archived.")
            Notification_Service.notify_administrators(f"{found_department.name} has been removed archived.")

            return jsonify(message = "Office successfully archived."), 200
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
    
    def get_all_department_ipcr(dept_id):
        try:
            dept_members = User.query.filter_by(department_id = dept_id).all()

            user_ipcr = []

            if dept_members == None:
                return jsonify([]), 200
            
            for members in dept_members:
                ipcr_container = None

                for ipcr in members.ipcrs:
                    if ipcr.isMain and ipcr.status == 1:
                        ipcr_container = ipcr.department_info()

                user_ipcr.append({
                    "member": members.info(),
                    "ipcr": ipcr_container
                })
        
            return jsonify(user_ipcr), 200
        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
        
    def get_all_department_opcr(dept_id):
        try:
            dept = Department.query.get(dept_id)

            if dept == None:
                return jsonify(error="Department not found"), 400
        
            return jsonify(dept.collect_all_opcr()), 200
        except OperationalError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Database connection error"), 500

        except Exception as e:  # fallback for unknown errors
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500
    
    def get_user_count_per_department():
        """
        Returns department-user counts formatted for Recharts:
        [
        { "name": "Department A", "value": 10 },
        { "name": "Department B", "value": 0 },
        ...
        ]
        """
        results = (
            db.session.query(
                Department.name.label("name"),
                func.count(User.id).label("value")
            )
            .outerjoin(User, User.department_id == Department.id)  # LEFT JOIN
            .group_by(Department.id)
            .all()
        )

        data = [{"name": row.name, "value": row.value or 0} for row in results]
        return jsonify(data), 200
    
    def get_average_performance_by_department():
        """
        Returns department performance averages:
        [
            { "name": "Education", "value": 3.5 },
            { "name": "Registrar", "value": 4.1 },
            ...
        ]
        """
        # Join Department → User → Output → Sub_Task
        results = (
            db.session.query(
                Department.name.label("name"),
                func.avg(Sub_Task.average).label("value")
            )
            .join(User, User.department_id == Department.id)
            .join(Output, Output.user_id == User.id)
            .join(Sub_Task, Sub_Task.output_id == Output.id)
            .group_by(Department.id)
            .all()
        )

        # Include all departments (even if they have no performance data)
        departments = Department.query.all()
        data = []
        for dept in departments:
            match = next((r for r in results if r.name == dept.name), None)
            avg_value = round(match.value, 2) if match and match.value else 0
            data.append({"name": dept.name, "value": avg_value})

        return jsonify(data), 200
    
    def get_user_performance_by_department_id(department_id):
        """
        Returns average performance per user for a specific department.
        Example:
        [
            { "name": "Juan Dela Cruz", "value": 4.5 },
            { "name": "Maria Santos", "value": 4.1 },
            ...
        ]
        """
        users = User.query.filter_by(department_id=department_id).all()
        data = []

        for user in users:
            avg = user.calculatePerformance()
            data.append({
                "name": f"{user.first_name} {user.last_name}",
                "value": round(avg, 2)
            })

        # Sort from highest to lowest
        data.sort(key=lambda x: x["value"], reverse=True)
        return jsonify(data), 200
    
    def get_top_performing_department():
        """
        Find the most performing department based on the average
        of their users' OPCR/Sub_Task overall averages.

        Returns:
        {
            "department": "Registrar",
            "average": 4.32,
            "quantity": 4.1,
            "efficiency": 4.3,
            "timeliness": 4.5
        }
        """

        # Query department averages based on Sub_Task ratings through user relationships
        results = (
            db.session.query(
                Department.id.label("dept_id"),
                Department.name.label("department"),
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("overall_average")
            )
            .join(User, User.department_id == Department.id)
            .join(Output, Output.user_id == User.id)
            .join(Sub_Task, Sub_Task.output_id == Output.id)
            .group_by(Department.id)
            .all()
        )

        if not results:
            return jsonify({"message": "No performance data available"}), 404

        # Find the department with the highest overall average
        top_dept = max(results, key=lambda r: r.overall_average or 0)

        data = {
            "department": top_dept.department,
            "quantity": round(top_dept.avg_quantity or 0, 2),
            "efficiency": round(top_dept.avg_efficiency or 0, 2),
            "timeliness": round(top_dept.avg_timeliness or 0, 2),
            "average": round(top_dept.overall_average or 0, 2)
        }

        return jsonify(data), 200
    
    
