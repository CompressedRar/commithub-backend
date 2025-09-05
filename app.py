from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Config from env
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # dito daw ilagay lahat ng routes
    from routes.Auth import auth
    app.register_blueprint(auth)

    from routes.Tests import test
    app.register_blueprint(test)

    @app.route("/")
    def home():
        return "working now"

    return app



