from app import db, socketio
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from flask import request, jsonify
from werkzeug.utils import secure_filename
from argon2 import PasswordHasher
import jwt
import secrets
import os
import uuid
from datetime import timezone, timedelta, datetime

from models.User import User, Profile
from models.Notification import Notification_Service
from utils.FileStorage import upload_profile_pic
from utils.Generate import generate_default_password
from utils.Email import send_email, send_email_account_creation, send_templated_reset_email
from models.Logs import Log_Service


JWT_EXPIRY_HOURS = os.getenv("JWT_EXPIRY_HOURS", 8)
JWT_SECRET = os.getenv("JWT_SECRET")

class Users:
    def check_email_if_exists(email):
        try:
            exists = Profile.query.filter_by(email=email).first() is not None
            msg = "Email was already taken." if exists else "Available"
            return jsonify(message=msg), 200

        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def authenticate_if_email_exists(email):
        print("checking email", email)
        try:
            user = Profile.query.filter_by(email=email).first()


            if not user:
                print("email not found")
                return False

            active_user = next(
                (u for u in user.users if u.account_status == 1),
                None
            )

            return active_user.to_dict() if active_user else False
        except Exception as e:
            print("error checking email")
            print(e)
            return False

    def does_president_exists():
        try:
            exists = User.query.filter_by(role="president").first() is not None
            return jsonify(exists), 200
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def does_admin_exists():
        try:
            exists = User.query.filter_by(role="administrator").first() is not None
            return jsonify(exists), 200
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_all_users():
        try:
            return jsonify([u.to_dict() for u in User.query.all()]), 200
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_user(id):
        try:
            user = User.query.get(id)
            if user:
                return jsonify(user.to_dict()), 200
            return jsonify(error="There is no user with that id"), 400
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_assigned_tasks(id):
        try:
            user = User.query.get(id)
            if user:
                return jsonify(user.tasks()), 200
            return jsonify(error="There is no user with that id"), 400
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def get_user_assigned_tasks(id):
        try:
            user = User.query.get(id)
            if user:
                return jsonify(user.assigned_task()), 200
            return jsonify(error="There is no user with that id"), 400
        except OperationalError:
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            return jsonify(error=str(e)), 500

    def _upload_profile_picture(profile_file, first_name, last_name):
        """Save and upload a profile picture, returning the storage URL."""
        filename = secure_filename(profile_file.filename)
        filepath = os.path.join("profile_pics", filename)
        profile_file.save(filepath)
        object_name = f"profile_pictures/{first_name}{last_name}{uuid.uuid4()}.png"
        return upload_profile_pic(filepath, "commithub-bucket", object_name)

    def add_new_user(data, profile_picture):
        try:
            ph = PasswordHasher()

            new_default_password = generate_default_password()

            hashed_password = ph.hash(new_default_password)

            profile_link = None

            if profile_picture:
                profile_link = Users._upload_profile_picture(
                    profile_picture,
                    data["first_name"],
                    data["last_name"]
                )

            # =========================
            # CREATE PROFILE
            # =========================

            profile = Profile(
                email=data["email"],
                password=hashed_password,
                profile_picture_link=profile_link,
            )

            db.session.add(profile)
            db.session.flush()

            # =========================
            # CREATE USER ACCOUNT
            # =========================

            new_user = User(
                profile_id=profile.id,

                first_name=data["first_name"],
                last_name=data["last_name"],
                middle_name=data.get("middle_name", ""),

                position_id=data["position"],
                department_id=data["department"],
                role=data["role"],
            )

            db.session.add(new_user)

            send_email_account_creation(
                data["email"],
                f"Hello! Your default password is: {new_default_password}",
                new_default_password
            )

            db.session.commit()

            full = f"{data['first_name']} {data['last_name']}"

            dept_name = new_user.department.name

            socketio.emit("user_created", "user added")

            Notification_Service.notify_user(
                new_user.id,
                "Welcome to Commithub! Start by creating your own IPCR."
            )

            Notification_Service.notify_department_heads(
                data["department"],
                f"{full} joined {dept_name}."
            )

            Notification_Service.notify_administrators(
                f"{full} joined {dept_name}."
            )

            Notification_Service.notify_presidents(
                f"{full} joined {dept_name}."
            )

            return jsonify(
                message="Account creation is successful."
            ), 200

        except IntegrityError:
            db.session.rollback()
            return jsonify(error="Email already exists"), 400

        except DataError:
            db.session.rollback()
            return jsonify(error="Invalid data format"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500

        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def update_user(id, data, rq):
        from models.Tasks import Main_Task, Output

        try:
            user = User.query.get(id)
            if not user:
                return jsonify(error="There is no user with that ID"), 400

            profile = rq.files.get("profile_picture_link")
            if profile:
                user.profile.profile_picture_link = Users._upload_profile_picture(
                    profile, data.get("first_name", ""), data.get("last_name", "")
                )

            for field in (
                "first_name",
                "last_name",
                "middle_name",
                "role",
            ):
                if field in data:
                    setattr(user, field, data[field])

            # PROFILE FIELDS
            for field in (
                "email",
                "password",
                "recovery_email",
            ):
                if field in data:
                    setattr(user.profile, field, data[field])

            if "two_factor_enabled" in data:
                user.profile.two_factor_enabled = bool(
                    int(data["two_factor_enabled"])
                )

            if "position" in data:
                user.position_id = int(data["position"])

            from services.tasks_service import TaskAssignmentService
            if "department" in data:
                new_dept_id = int(data["department"])
                if new_dept_id != user.department_id:
                    for output in list(user.outputs):
                        if output.main_task:
                            TaskAssignmentService.unassign_user(output.main_task.id , user.id)                            


                    user.department_id = new_dept_id

            db.session.commit()
            socketio.emit("user_modified", "modified")
            socketio.emit("user_updated", "modified")
            return jsonify(message="User successfully updated"), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def delete_user(id):
        try:
            user = User.query.get(id)
            if not user:
                return jsonify(error="There is no user with that id"), 400
            db.session.delete(user)
            db.session.commit()
            return jsonify(message="User successfully deleted"), 200
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def archive_user(id):
        try:
            user = User.query.get(id)
            if not user:
                return jsonify(error="There is no user with that id"), 400

            user.account_status = 0
            db.session.commit()

            full = f"{user.first_name} {user.last_name}"
            socketio.emit("user_modified", "user deactivated")
            Notification_Service.notify_user(user.id, "This account has been deactivated.")
            Notification_Service.notify_department_heads(user.department.id, f"The account of {full} has been deactivated.")
            Notification_Service.notify_presidents(f"The account of {full} has been deactivated.")
            Notification_Service.notify_administrators(f"The account of {full} has been deactivated.")
            return jsonify(message="User successfully deactivated"), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def unarchive_user(id):
        try:
            user = User.query.get(id)
            if not user:
                return jsonify(error="There is no user with that id"), 400
            user.account_status = 1
            db.session.commit()
            socketio.emit("user_modified", "user reactivated")
            Notification_Service.notify_user(user.id, "This account has been reactivated.")
            return jsonify(message="User successfully reactivated"), 200
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def reset_password(id):
        try:
            user = User.query.get(id)
            if not user:
                return jsonify(error="There is no user with that id"), 400

            new_default_password = "commithubnc"
            ph = PasswordHasher()
            user.profile.password = ph.hash(new_default_password)
            db.session.commit()

            send_templated_reset_email(
                user.profile.email,
                f"Hello! The password reset was done to this account. The default password is: {new_default_password}",
            )
            Notification_Service.notify_user(user.id, "The account password has been reset.")
            socketio.emit("user_modified", "modified")
            return jsonify(message="Password successfully reset."), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def change_password(user_id, password):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify(error="User not found"), 404
            ph = PasswordHasher()
            user.profile.password = ph.hash(password)
            db.session.commit()
            return jsonify(message="Success"), 200
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500


    def get_all_accountsby_profile(profile_id):
        try:
            profile = Profile.query.get(profile_id)
            if not profile:
                return jsonify(error="There is no profile with that id"), 400
            accounts = [user.info() for user in profile.users]
            return jsonify(accounts), 200
        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500
        
    def switch_account(profile_id, user_id):
        try:
            # =========================
            # VERIFY PROFILE
            # =========================

            profile = Profile.query.get(profile_id)

            if not profile:
                return jsonify(
                    error="Profile does not exist."
                ), 400

            # =========================
            # VERIFY ACCOUNT
            # =========================

            user = User.query.get(user_id)

            if not user:
                return jsonify(
                    error="Account does not exist."
                ), 400

            # =========================
            # VERIFY OWNERSHIP
            # IMPORTANT SECURITY CHECK
            # =========================

            if user.profile_id != profile.id:
                return jsonify(
                    error="This account does not belong to this profile."
                ), 403

            # =========================
            # VERIFY ACCOUNT STATUS
            # =========================

            if user.account_status != 1:
                return jsonify(
                    error="This account is inactive."
                ), 403

            # =========================
            # GENERATE NEW TOKEN
            # =========================

            token = Users.generate_token(
                user.to_dict()
            )

            # =========================
            # LOG SWITCH
            # =========================

            ip_address = request.remote_addr

            user_agent = request.headers.get(
                "User-Agent"
            )

            Log_Service.add_logs(
                user.id,
                user.full_name(),
                (
                    user.department.name
                    if user.department
                    else "NONE"
                ),
                "SWITCH_ACCOUNT",
                "User Account",
                (
                    f"Switched into "
                    f"{user.full_name()} "
                    f"({user.role})"
                ),
                ip_address,
                user_agent,
            )

            socketio.emit(
                "account_switched",
                "account switched"
            )

            return jsonify(
                message="Account switched successfully.",
                token=token,
                active_account=user.to_dict(),
            ), 200

        except OperationalError:
            db.session.rollback()

            return jsonify(
                error="Database connection error"
            ), 500

        except Exception as e:
            db.session.rollback()

            return jsonify(
                error=str(e)
            ), 500

    def generate_token(user_data: dict) -> str:

        payload = {
            # ACTIVE ACCOUNT
            "id": user_data.get("id"),

            # PROFILE
            "profile_id": user_data.get("profile_id"),

            # ACCOUNT
            "role": user_data.get("role"),

            # DISPLAY
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),

            # PROFILE AUTH
            "email": user_data.get("email"),

            # ORG
            "department": user_data.get("department"),

            # UI
            "profile_picture_link":
                user_data.get("profile_picture_link"),

            "two_factor_enabled":
                user_data.get("two_factor_enabled"),

            # EXPIRATION
            "exp":
                datetime.now(timezone.utc)
                + timedelta(hours=int(JWT_EXPIRY_HOURS)),
        }

        return jwt.encode(
            payload,
            JWT_SECRET,
            algorithm="HS256"
        )

    def authenticate_pass(login_data):
        try:
            if "email" not in login_data:
                return jsonify(error="Missing Email"), 400
            if "password" not in login_data:
                return jsonify(error="Missing Password"), 400

            user_dict = Users.authenticate_if_email_exists(login_data["email"])
            if not user_dict:
                return jsonify(error="Incorrect Email or Password"), 400

            ph = PasswordHasher()
            if ph.verify(hash=user_dict["password"], password=login_data["password"]):
                return jsonify(message="Authenticated"), 200
            return jsonify(error="Incorrect Email or Password"), 400

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error="Incorrect Email or Password"), 500

    def authenticate_user(login_data):
        try:
            if "email" not in login_data:
                return jsonify(error="Missing Email"), 400
            if "password" not in login_data:
                return jsonify(error="Missing Password"), 400

            email = login_data["email"]
            user_dict = Users.authenticate_if_email_exists(email)

            if not user_dict:
                print("no email")
                return jsonify(error="Incorrect Email or Password"), 400

            ph = PasswordHasher()
            if not ph.verify(hash=user_dict["password"], password=login_data["password"]):
                print("wrong pass")
                return jsonify(error="Incorrect Email or Password"), 400

            user = User.query.get(user_dict["id"])
            profile = user.profile
            ip_address = request.remote_addr
            user_agent = request.headers.get("User-Agent")

            if profile.two_factor_enabled:
                from models.LoginOTP import LoginOTP
                otp = f"{secrets.randbelow(10**6):06d}"
                LoginOTP.create_for_user(user.id, otp, expires_minutes=5)
                send_email(email, f"Your CommitHub login OTP is {otp}. It expires in 5 minutes.")
                return jsonify(message="OTP sent", two_factor_enabled=True, email=email), 200

            token = Users.generate_token(user.to_dict())
            Log_Service.add_logs(
                user.id, user.full_name(),
                user_dict.get("department_name", "NONE"),
                "LOGIN", "User Account",
                f"{email} logged in", ip_address, user_agent,
            )
            return jsonify(message="Login successful", token=token, two_factor_enabled=False), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify(error="Incorrect Email or Password"), 500

    def verify_login_otp(email, otp):
        from models.LoginOTP import LoginOTP

        try:
            profile = Profile.query.filter_by(email=email).first()

            if not profile:
                return jsonify(error="There is no user with that id."), 400

            user = next(
                (
                    u for u in profile.users
                    if u.account_status == 1
                ),
                None
            )

            if not user:
                return jsonify(error="No active account found."), 400
            

            if not LoginOTP.verify_user_otp(user.id, otp):
                return jsonify(error="Invalid or expired OTP"), 400

            token = Users.generate_token(user.to_dict())
            ip_address = request.remote_addr
            user_agent = request.headers.get("User-Agent")
            dept_name = user.department.name if user.department else "UNKNOWN"
            Log_Service.add_logs(user.id, user.full_name(), dept_name, "LOGIN", "LOGIN", ip=ip_address, agent=user_agent)

            return jsonify(message="Authenticated.", token=token), 200

        except OperationalError as e:
            print(e)
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify(error="Invalid or expired OTP"), 500

    def assign_department_head(user_id, dept_id):
        from models.Departments import Department

        try:
            department = Department.query.get(dept_id)
            if not department:
                return jsonify(message="There is no department with that id."), 400

            for u in department.users:
                if u.role not in ("administrator", "president"):
                    u.role = "faculty"

            user = User.query.get(user_id)
            if not user:
                return jsonify(message="There is no user with that id."), 400

            user.role = "head"
            db.session.commit()

            full = user.full_name()
            Notification_Service.notify_user(user.id, f"This account is now the office head of {department.name}.")
            Notification_Service.notify_department(department.id, f"{full} has been assigned as the new office head of {department.name}.")
            Notification_Service.notify_heads(f"{full} has been assigned as the new office head of {department.name}.")
            Notification_Service.notify_presidents(f"{full} has been assigned as the new office head of {department.name}.")
            socketio.emit("department", "office head assigned")
            return jsonify(message="Office head successfully assigned."), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def remove_department_head(user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify(message="There is no user with that id."), 400

            user.role = "faculty"
            db.session.commit()

            full = user.full_name()
            dept_name = user.department.name
            socketio.emit("department", "department head removed")
            Notification_Service.notify_user(user.id, "This account has been removed from being office head.")
            Notification_Service.notify_department(dept_id=user.department_id, msg=f"The head of {dept_name} has been removed from its position.")
            Notification_Service.notify_presidents(f"The head of {dept_name} has been removed from its position.")
            return jsonify(message="Office head successfully removed."), 200

        except OperationalError:
            db.session.rollback()
            return jsonify(error="Database connection error"), 500
        except Exception as e:
            db.session.rollback()
            return jsonify(error=str(e)), 500

    def count_users_by_depts():
        all_users = [u.to_dict() for u in User.query.all()]
        counts = {"cs": 0, "educ": 0, "hm": 0, "other": 0}
        dept_map = {
            "College of Computing Studies ": "cs",
            "College of Education ": "educ",
            "College of Hospitality Management": "hm",
        }

        for user in all_users:
            if user["department"] == "NONE":
                continue
            key = dept_map.get(user["department"]["name"], "other")
            counts[key] += 1

        return jsonify(message={**counts, "all": len(all_users)}), 200
