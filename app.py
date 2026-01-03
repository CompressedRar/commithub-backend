from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os
from utils.Email import mail, send_email


db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()


def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    
    app.config["SECRET_KEY"] = "hannelore"
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("LOCAL_DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'qwertythanzip1103@gmail.com'
    app.config['MAIL_PASSWORD'] = 'bafx xxnm qryx egpc'
    app.config['MAIL_DEFAULT_SENDER'] = 'qwertythanzip1103@gmail.com'

    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    

    # dito daw ilagay lahat ng routes
    from routes.Auth import auth
    app.register_blueprint(auth)

    from routes.Tests import test
    app.register_blueprint(test)

    from routes.Department import department
    app.register_blueprint(department)

    from routes.Category import category
    app.register_blueprint(category)

    from routes.Task import task
    app.register_blueprint(task)

    from routes.Users import users
    app.register_blueprint(users)

    from routes.Logs import logs
    app.register_blueprint(logs)

    from routes.PCR import pcrs
    app.register_blueprint(pcrs)

    from routes.Chart import charts
    app.register_blueprint(charts)

    from routes.AI import ai
    app.register_blueprint(ai)

    from routes.Positions import positions
    app.register_blueprint(positions)

    from routes.Settings import settings
    app.register_blueprint(settings)


    @app.route("/test-email")
    def test_email():
        res = send_email("qwertythanzip@gmail.com")
        return res


    @app.route("/")
    def home():
        return "working now"

    return app



