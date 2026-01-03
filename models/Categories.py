from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from sqlalchemy import func, case, cast, Float, and_
from models.Tasks import Sub_Task, Main_Task, Output
from app import socketio


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique = True )
    status = db.Column(db.Integer, default = 1)
    type = db.Column(db.String(50), default = "Core Function" )

    main_tasks = db.relationship("Main_Task", back_populates = "category")
    description = db.Column(db.Text, nullable=True)

    period = db.Column(db.String(100), nullable=True)


    def get_category_avg_rating(self):
        total_rating = 0
        task_count = 0

        for main_task in self.main_tasks:
            if main_task.status == 1:
                total_rating += main_task.get_task_avg_rating()
                task_count += 1

        if task_count == 0:
            return 0

        return total_rating / task_count


    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
            "status": self.status,
            "type":self.type,
            "period_id": self.period,
            "description": self.description,
            "task_count": len(self.main_tasks),
            "average_rating": self.get_category_avg_rating()
            
        }

    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "main_tasks": [main_task.info() for main_task in self.main_tasks],
            "status": self.status,
            "type":self.type,
            "period_id": self.period,
            "description": self.description,
            "task_count": len(self.main_tasks),
            "average_rating": self.get_category_avg_rating()
        }
    

class Category_Service():
    def get_all():
        try:
            from models.System_Settings import System_Settings
            settings = System_Settings.query.first()

            all_categories = Category.query.filter_by(status = 1, period = settings.current_period_id).all()
            converted_categories = [category.info() for category in all_categories]
        
            return jsonify(converted_categories), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_all_with_tasks():
        try:
            from models.System_Settings import System_Settings
            settings = System_Settings.query.first()
            all_categories = Category.query.filter_by(status = 1, period = settings.current_period_id).all()
            
            converted_categories = [category.to_dict() for category in all_categories]
        
            return jsonify(converted_categories), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_category(id):
        try:
            all_depts = Category.query.filter_by(id = id).all()
            
            if all_depts:
                dept = all_depts[0].to_dict()
                return jsonify(dept), 200
            else:
                return jsonify(message = "There is no key result area with that id"), 400
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def create_category(data):
        try:
            from models.System_Settings import System_Settings            
            current_settings = System_Settings.query.first()

            category_name = data.get("category_name", "").strip()
            category_type = data.get("category_type", "").strip()
            category_description = data.get("description", "").strip()

            if not category_name:
                return jsonify(error="Category name is required."), 400

            # Check if the category already exists
            existing_category = Category.query.filter_by(name=category_name).first()
            if existing_category:
                return jsonify(error="Category name already exists."), 400

            # Create new category
            new_category = Category(name=category_name, type = category_type, period = current_settings.current_period_id if current_settings else None, description = category_description)
            db.session.add(new_category)
            db.session.commit()  # Make sure to commit!

            socketio.emit("category")

            return jsonify(message="Category created successfully."), 200

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
        
    def update_category(data):
        try:
            found_category = Category.query.get(data["id"])
            
            if found_category == None:
                return jsonify(message = "Key Result Area doesn't exists."), 400
            found_category.name = data["title"]

            db.session.commit()

            return jsonify(message = "Key Result Area updated."), 200
        except IntegrityError as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error="Category already exists"), 400
        
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
    
    def archive_category(id):
        try:
            category = Category.query.get(id)
            if not category:
                return jsonify(message="No category with that ID"), 400

            # Archive the category
            category.status = 0

            for main_task in category.main_tasks:
                # Archive the main task
                main_task.status = 0

                # Archive all subtasks under this main task
                for sub_task in main_task.sub_tasks:
                    sub_task.status = 0

                # Delete all outputs linked to this main task
                for output in main_task.outputs:
                    db.session.delete(output)

                # Delete all assigned tasks linked to this main task
                for assigned_task in main_task.assigned_tasks:
                    db.session.delete(assigned_task)

            db.session.commit()
            socketio.emit("category", "archived")

            return jsonify(message="Key Result Area successfully archived."), 200

        except Exception as e:
            db.session.rollback()
            print(str(e))
            return jsonify(error=str(e)), 500



        
    
    def get_category_count():
        categories_count = db.session.query(func.count(Category.id)).scalar()        
        return jsonify(message = {
            "count":categories_count
        })
    
    def get_task_average_summary(category_id):
        """
        Returns a summary of all main tasks in a given category with their average scores:
        [
            {
                "task_id": 1,
                "task_name": "Tree Planting",
                "average_quantity": 4.3,
                "average_efficiency": 4.1,
                "average_timeliness": 4.6,
                "overall_average": 4.33
            }, ...
        ]

        Ratings are computed in SQL to match the Python logic in Sub_Task.calculate*().
        """

        # cast helpers
        tgt_acc = cast(Sub_Task.target_acc, Float)
        act_acc = cast(Sub_Task.actual_acc, Float)
        tgt_mod = cast(Sub_Task.target_mod, Float)
        act_mod = cast(Sub_Task.actual_mod, Float)
        tgt_time = cast(Sub_Task.target_time, Float)
        act_time = cast(Sub_Task.actual_time, Float)

        # quantity ratio = actual / nullif(target,0)
        qty_ratio = act_acc / func.nullif(tgt_acc, 0.0)

        qty_rating = case(
            
            (Sub_Task.target_acc == 0, 0),           # if target == 0 -> 0
            (qty_ratio >= 1.3, 5),
            (qty_ratio >= 1.01, 4),
            (qty_ratio >= 0.90, 3),
            (qty_ratio >= 0.70, 2),
            
            else_=1  # else covers <= 0.699 etc.
        )

        # efficiency uses actual_mod (the original logic returns 5 when actual_mod == 0)
        eff_rating = case(
            
                (Sub_Task.actual_mod == 0, 5),
                (and_(act_mod >= 1, act_mod <= 2), 4),
                (and_(act_mod >= 3, act_mod <= 4), 3),
                (and_(act_mod >= 5, act_mod <= 6), 2),
            
            else_=1
        )

        # timeliness calculation: 1 + (target - actual) / target ; if target == 0 -> 0
        tim_calc = 1 + (tgt_time - act_time) / func.nullif(tgt_time, 0.0)

        tim_rating = case(
            
                (Sub_Task.target_time == 0, 0),
                (tim_calc >= 1.3, 5),
                (tim_calc >= 1.15, 4),
                (tim_calc >= 0.9, 3),
                (tim_calc >= 0.51, 2),
            
            else_=1
        )

        # Build query: left outer join so tasks without subtasks are included

        from models.System_Settings import System_Settings
        settings = System_Settings.query.first()
        results = (
            db.session.query(
                Main_Task.id.label("task_id"),
                Main_Task.mfo.label("task_name"),
                func.avg(qty_rating).label("avg_quantity"),
                func.avg(eff_rating).label("avg_efficiency"),
                func.avg(tim_rating).label("avg_timeliness"),
                # average of the three computed ratings per sub_task
                func.avg((qty_rating + eff_rating + tim_rating) / 3.0).label("avg_overall")
            )
            .outerjoin(Sub_Task, Sub_Task.main_task_id == Main_Task.id)
            .filter(Main_Task.category_id == category_id, Main_Task.status == 1, Main_Task.period == settings.current_period_id)
            .group_by(Main_Task.id)
            .all()
        )

        data = []
        for r in results:
            data.append({
                "task_id": int(r.task_id),
                "task_name": r.task_name,
                "average_quantity": round(float(r.avg_quantity or 0), 2),
                "average_efficiency": round(float(r.avg_efficiency or 0), 2),
                "average_timeliness": round(float(r.avg_timeliness or 0), 2),
                "overall_average": round(float(r.avg_overall or 0), 2),
            })

        return jsonify(data), 200
    
    def calculate_category_performance(category_id):
        """
        Calculate the average quantity, efficiency, timeliness, and overall average
        for all tasks under a given category.
        
        Returns:
        {
            "quantity": 4.2,
            "efficiency": 3.8,
            "timeliness": 4.0,
            "overall_average": 4.0
        }
        """

        category = Category.query.get(category_id)
        from models.System_Settings import System_Settings
        settings = System_Settings.query.first()

        print(category)
        if not category:
            return {"quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}

        total_quantity = 0
        total_efficiency = 0
        total_timeliness = 0
        total_average = 0
        count = 0

        for main_task in category.main_tasks:
            print(main_task.status)
            if main_task.status == 1 and main_task.period == settings.current_period_id:

                for sub_task in main_task.sub_tasks:
                    # Ensure calculations are up to date
                    quantity = sub_task.calculateQuantity()
                    efficiency = sub_task.calculateEfficiency()
                    timeliness = sub_task.calculateTimeliness()
                    average = sub_task.calculateAverage()

                    total_quantity += quantity
                    total_efficiency += efficiency
                    total_timeliness += timeliness
                    total_average += average
                    count += 1

                    print("merrpon")

        if count == 0:
            return {"quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}
        
        data = {
            "quantity": round(total_quantity / count, 2),
            "efficiency": round(total_efficiency / count, 2),
            "timeliness": round(total_timeliness / count, 2),
            "overall_average": round(total_average / count, 2)
        }
        return jsonify(data), 200 
    
    def calculate_category_performance_per_department(category_id):
        """
        Returns:
        [
            {
                "name": "Education",
                "quantity": 3.5,
                "efficiency": 2.0,
                "timeliness": 2.0,
                "average": 2.0
            },
            ...
        ]
        """

        from models.System_Settings import System_Settings

        category = Category.query.get(category_id)
        settings = System_Settings.query.first()

        if not category:
            return jsonify([]), 200

        depts = {}

        for main_task in category.main_tasks:
            if main_task.status == 1 and main_task.period == settings.current_period_id:

                for sub_task in main_task.sub_tasks:
                    # Defensive checks
                    if not sub_task.output or not sub_task.output.user:
                        continue

                    dept_name = sub_task.output.user.department.name

                    if dept_name not in depts:
                        depts[dept_name] = {
                            "quantity": 0,
                            "efficiency": 0,
                            "timeliness": 0,
                            "average": 0,
                            "count": 0
                        }

                    depts[dept_name]["quantity"] += sub_task.calculateQuantity()
                    depts[dept_name]["efficiency"] += sub_task.calculateEfficiency()
                    depts[dept_name]["timeliness"] += sub_task.calculateTimeliness()
                    depts[dept_name]["average"] += sub_task.calculateAverage()
                    depts[dept_name]["count"] += 1

        # Convert to response format
        response = []

        for dept_name, values in depts.items():
            count = values["count"]
            if count == 0:
                continue

            response.append({
                "name": dept_name,
                "quantity": round(values["quantity"] / count, 2),
                "efficiency": round(values["efficiency"] / count, 2),
                "timeliness": round(values["timeliness"] / count, 2),
                "average": round(values["average"] / count, 2)
            })

        return jsonify(response), 200

    
