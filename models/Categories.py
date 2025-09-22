from app import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify
from sqlalchemy.dialects.mysql import JSON, TEXT
from sqlalchemy import func

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
    