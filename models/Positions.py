from app import db, socketio
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError, DataError, ProgrammingError
from flask import jsonify

class Position(db.Model):
    __tablename__ = "positions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    users = db.relationship("User", back_populates = "position")
    core_weight = db.Column(db.Float, default = 0.0)
    strategic_weight = db.Column(db.Float, default = 0.0)
    support_weight = db.Column(db.Float, default = 0.0)

    status = db.Column(db.Integer, default = 1)
    
    
    def info(self):
        return {
            "id" : self.id,
            "name": self.name,
            "core_weight": self.core_weight,
            "strategic_weight": self.strategic_weight,
            "support_weight": self.support_weight,
            "status": self.status
        }

    def to_dict(self):
        return {
            "id" : self.id,
            "name": self.name,
            "users": [user.to_dict() for user in self.users]
        }
    

class Positions():
    def get_all_positions():
        try:
            positions = Position.query.all()
            return jsonify([pos.to_dict() for pos in positions]), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def get_position_info():
        try:
            positions = Position.query.all()
            return jsonify([pos.info() for pos in positions]), 200
        
        except OperationalError:
            #db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            #db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def create_position(data):
        try:
            position_name = data["name"].strip()
            core_weight = data["core_weight"]
            strat_weight = data["strat_weight"]
            support_weight = data["support_weight"]

            if not position_name:
                return jsonify(error="Position name is required."), 400

            # Check if the category already exists
            existing_category = Position.query.filter_by(name=position_name).first()
            if existing_category:
                return jsonify(error="Position name already exists."), 400

            # Create new category
            new_position = Position(name=position_name, core_weight = core_weight, strategic_weight = strat_weight, support_weight = support_weight)
            db.session.add(new_position)
            db.session.commit()  # Make sure to commit!

            socketio.emit("position")

            return jsonify(message="Position created successfully."), 200

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
        
    def update_position(data):
        try:
            pos = Position.query.get(data["id"])

            if not pos:
                return jsonify(error="No position with that ID."), 400
            
            if "core_weight" in data:
                pos.core_weight = float(data["core_weight"])

            if "strat_weight" in data:
                pos.strategic_weight = float(data["strat_weight"])

            if "support_weight" in data:
                pos.support_weight = float(data["support_weight"])

            if "name" in data:
                pos.name = data["name"]

            db.session.commit()

            socketio.emit("position")

            return jsonify(message="Position updated successfully."), 200

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
        
    def archive_position(id):
        try:
            pos = Positions.query.get(id)

            if not pos:
                return jsonify(error="No position with that ID."), 400
            
            pos.status = 0

            db.session.commit()

            socketio.emit("position")

            return jsonify(message="Position archived successfully."), 200

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
        
    def restore_position(id):
        try:
            pos = Positions.query.get(id)

            if not pos:
                return jsonify(error="No position with that ID."), 400
            
            pos.status = 1

            db.session.commit()

            socketio.emit("position")

            return jsonify(message="Position archived successfully."), 200

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
        
        