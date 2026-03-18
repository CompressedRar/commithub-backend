from app import db, socketio
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from sqlalchemy import func
from flask import jsonify
from models.Categories import Category


class CategoryCRUDService:

    def get_all():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            categories = (
                Category.query
                .filter_by(status=1, period=settings.current_period_id)
                .order_by(Category.priority_order.desc())
                .all()
            )
            return jsonify([c.info() for c in categories]), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_all_with_tasks():
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            categories = Category.query.filter_by(
                status=1, period=settings.current_period_id
            ).all()
            return jsonify([c.to_dict() for c in categories]), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_category(id):
        try:
            category = Category.query.get(id)
            if not category:
                return jsonify(message="There is no key result area with that id"), 400

            print("category", category.to_dict())
            return jsonify(category.to_dict()), 200

        except OperationalError as e:
            print(e)
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            print(e)
            return jsonify(error=str(e)), 500

    def get_category_count():
        count = db.session.query(func.count(Category.id)).scalar()
        return jsonify(message={"count": count})

    def create_category(data):
        try:
            from models.System_Settings import System_Settings

            settings = System_Settings.get_default_settings()
            name = data.get("category_name", "").strip()
            category_type = data.get("category_type", "").strip()
            description = data.get("description", "").strip()

            if not name:
                return jsonify(error="Category name is required."), 400

            if Category.query.filter_by(name=name, period=settings.current_period_id).first():
                return jsonify(error="Category name already exists."), 400

            db.session.add(Category(
                name=name,
                type=category_type,
                period=settings.current_period_id if settings else None,
                description=description,
            ))
            db.session.commit()
            socketio.emit("category")
            return jsonify(message="Category created successfully."), 200

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format."), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error."), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_category(data):
        try:
            category = Category.query.get(data["id"])
            if category is None:
                return jsonify(message="Key Result Area doesn't exists."), 400

            category.name = data["title"]
            db.session.commit()
            return jsonify(message="Key Result Area updated."), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Category already exists"), 400
        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_category_order(cat_id, order_num):
        try:
            category = Category.query.get(cat_id)
            if not category:
                return jsonify(message="Category was not found."), 404

            category.priority_order = int(order_num)
            db.session.commit()
            socketio.emit("category", "category changed")
            return jsonify(message="Category Priority Number was successfully updated."), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error="Updating priority number failed."), 400

    def archive_category(id):
        try:
            category = Category.query.get(id)
            if not category:
                return jsonify(message="No category with that ID"), 400

            category.status = 0
            for task in category.main_tasks:
                task.status = 0
                for sub_task in task.sub_tasks:
                    sub_task.status = 0
                for output in task.outputs:
                    db.session.delete(output)
                for assigned_task in task.assigned_tasks:
                    db.session.delete(assigned_task)

            db.session.commit()
            socketio.emit("category", "archived")
            return jsonify(message="Key Result Area successfully archived."), 200

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
