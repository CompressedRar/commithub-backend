import os
from dotenv import load_dotenv

load_dotenv()
class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'qwertythanzip1103@gmail.com'
    MAIL_PASSWORD = 'gldy eqwm hbgy xuee '
    MAIL_DEFAULT_SENDER = 'qwertythanzip1103@gmail.com'


class ProdConfig:
    SECRET_KEY = "hannelore"
    SQLALCHEMY_DATABASE_URI = os.getenv("LOCAL_DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'qwertythanzip1103@gmail.com'
    MAIL_PASSWORD = 'gldy eqwm hbgy xuee '
    MAIL_DEFAULT_SENDER = 'qwertythanzip1103@gmail.com'

# Directory where uploaded Excel IPCR files are stored
BASE_DIR = os.path.dirname(__file__)
EXCEL_UPLOAD_FOLDER = os.path.join(BASE_DIR, "excels", "UploadedIPCR")