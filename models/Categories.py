from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from sqlalchemy import func
from models.Tasks import Sub_Task, Main_Task, Output
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer, default = 1)

    main_tasks = db.relationship("Main_Task", back_populates = "category")

    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
            "status": self.status
        }

    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "main_tasks": [main_task.info() for main_task in self.main_tasks],
            "status": self.status
        }
    

class Category_Service():
    def get_all():
        try:
            all_categories = Category.query.filter_by(status = 1).all()
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
            all_categories = Category.query.filter_by(status = 1).all()
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
                return jsonify(message = "There is no category with that id"), 400
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def create_category(data):
        try:
            print(data)
            new_category = Category(
                name = data["category_name"]
            )
            db.session.add(new_category)

            return jsonify(message = "Category created."), 200
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
        
    def update_category(data):
        try:
            found_category = Category.query.get(data["id"])
            
            if found_category == None:
                return jsonify(message = "Category doesn't exists."), 400
            found_category.name = data["title"]

            db.session.commit()

            return jsonify(message = "Category updated."), 200
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
            found_task = Category.query.get(id)

            if found_task == None:
                return jsonify(message="No category with that ID"), 400
            
            found_task.status = 0
            db.session.commit()
            return jsonify(message = "Category successfully archived."), 200
        
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
            },
            ...
        ]
        """
        # Query all main tasks under the category
        tasks = (
            db.session.query(Main_Task.id, Main_Task.mfo)
            .filter(Main_Task.category_id == category_id)
            .all()
        )

        # Query averages grouped by task
        results = (
            db.session.query(
                Main_Task.id.label("task_id"),
                func.avg(Sub_Task.quantity).label("avg_quantity"),
                func.avg(Sub_Task.efficiency).label("avg_efficiency"),
                func.avg(Sub_Task.timeliness).label("avg_timeliness"),
                func.avg(Sub_Task.average).label("avg_overall")
            )
            .join(Sub_Task, Sub_Task.main_task_id == Main_Task.id)
            .filter(Main_Task.category_id == category_id)
            .group_by(Main_Task.id)
            .all()
        )

        # Convert results into a dictionary for quick lookup
        result_map = {r.task_id: r for r in results}

        # Combine data for all tasks (even those without Sub_Tasks)
        data = []
        for t in tasks:
            if t.id in result_map:
                r = result_map[t.id]
                data.append({
                    "task_id": t.id,
                    "task_name": t.mfo,
                    "average_quantity": round(r.avg_quantity or 0, 2),
                    "average_efficiency": round(r.avg_efficiency or 0, 2),
                    "average_timeliness": round(r.avg_timeliness or 0, 2),
                    "overall_average": round(r.avg_overall or 0, 2),
                })
            else:
                # Task has no Sub_Tasks yet
                data.append({
                    "task_id": t.id,
                    "task_name": t.mfo,
                    "average_quantity": 0,
                    "average_efficiency": 0,
                    "average_timeliness": 0,
                    "overall_average": 0,
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

        print(category)
        if not category:
            return {"quantity": 0, "efficiency": 0, "timeliness": 0, "overall_average": 0}

        total_quantity = 0
        total_efficiency = 0
        total_timeliness = 0
        total_average = 0
        count = 0

        for main_task in category.main_tasks:
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
    
