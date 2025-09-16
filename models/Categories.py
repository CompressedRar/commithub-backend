from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT

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
            all_categories = Category.query.all()
            converted_categories = [category.info() for category in all_categories]
        
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
                print(dept)
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