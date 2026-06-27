#!/usr/bin/env python
"""
CommitHub Database Seeding Script
==================================
Initializes the backend database with foundation data required for first-time setup.

Usage:
    python seed_database.py

This script will:
1. Create system settings with rating scales and alert thresholds
2. Create default positions (Faculty, Office Head, College President, Super Admin)
3. Create categories (Core Function, Strategic, Support)
4. Create organizational departments
5. Create admin profile and user account
6. Verify all data integrity

Author: CommitHub Team
Version: 1.0
"""

import os
import sys
from datetime import datetime, date, timedelta
from getpass import getpass
import traceback

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.User import Profile, User
from models.Positions import Position
from models.Categories import Category
from models.Departments import Department
from models.System_Settings import System_Settings
from models.Logs import Log

# Import password hasher
from argon2 import PasswordHasher


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_step(step_num, text):
    """Print a step indicator"""
    print(f"{Colors.BOLD}{Colors.BLUE}[{step_num}]{Colors.RESET} {text}")


def print_success(text):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """Print an error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """Print informational text"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def input_prompt(prompt, default=None, required=False):
    """Get user input with optional default value"""
    full_prompt = f"{Colors.BOLD}{prompt}"
    if default:
        full_prompt += f" [{default}]"
    full_prompt += f": {Colors.RESET}"
    
    value = input(full_prompt).strip()
    
    if not value and default:
        value = default
    
    if not value and required:
        print_error("This field is required!")
        return input_prompt(prompt, default, required)
    
    return value


def get_organization_details():
    """Interactively get organization details"""
    print_header("Organization Setup")
    
    print_info("Enter your organization's details")
    print_info("These will be used to configure the system for your institution.\n")
    
    org_name = input_prompt(
        "Organization name",
        default="College",
        required=True
    )
    
    president_name = input_prompt(
        "College President's full name",
        default="Dr. Juan dela Cruz",
        required=True
    )
    
    admin_name = input_prompt(
        "Administrative officer's full name",
        default="Maria Santos",
        required=True
    )
    
    admin_email = input_prompt(
        "Admin account email",
        default="admin@commithub.local",
        required=True
    )
    
    print_info("\nYou can change these details later via System Settings.\n")
    
    return {
        "org_name": org_name,
        "president_name": president_name,
        "admin_name": admin_name,
        "admin_email": admin_email
    }


def check_existing_data(app):
    """Check if database already has foundation data"""
    with app.app_context():
        try:
            profile_count = Profile.query.count()
            if profile_count > 0:
                print_error("Database already has profiles. Seeding would create duplicates.")
                print_info("To reset, delete all data from the database and try again.")
                return False
            return True
        except Exception as e:
            print_error(f"Error checking database: {e}")
            return None


def create_system_settings(app):
    """Create default system settings"""
    print_step("1", "Creating System Settings...")
    
    try:
        with app.app_context():
            # Check if settings already exist
            existing = System_Settings.query.first()
            if existing:
                print_info("System Settings already exist, skipping...")
                return True
            
            # Define rating thresholds (1-5 scale)
            rating_thresholds = {
                "1": {
                    "min": 0,
                    "max": 1.5,
                    "label": "Poor"
                },
                "2": {
                    "min": 1.5,
                    "max": 2.5,
                    "label": "Below Average"
                },
                "3": {
                    "min": 2.5,
                    "max": 3.5,
                    "label": "Average"
                },
                "4": {
                    "min": 3.5,
                    "max": 4.5,
                    "label": "Good"
                },
                "5": {
                    "min": 4.5,
                    "max": 5,
                    "label": "Excellent"
                }
            }
            
            # Define alert thresholds
            alert_thresholds = {
                "quantity": {
                    "warning": 70,
                    "critical": 50
                },
                "efficiency": {
                    "warning": 70,
                    "critical": 50
                },
                "timeliness": {
                    "warning": 70,
                    "critical": 50
                },
                "alert_to_roles": ["administrator", "head"],
                "daily_check_time": "08:00"
            }
            
            # Set period dates (calendar year 2024)
            planning_start = date(2024, 1, 1)
            planning_end = date(2024, 3, 31)
            monitoring_start = date(2024, 4, 1)
            monitoring_end = date(2024, 9, 30)
            rating_start = date(2024, 10, 1)
            rating_end = date(2024, 12, 31)
            
            settings = System_Settings(
                rating_thresholds=rating_thresholds,
                alert_thresholds=alert_thresholds,
                enable_formula=False,
                quantity_formula={},
                efficiency_formula={},
                timeliness_formula={},
                kpi_definitions={},
                current_period_id="2024-Q1",
                current_president_fullname="[To be configured]",
                current_mayor_fullname="[To be configured]",
                current_phase="planning",
                current_period="2024",
                planning_start_date=planning_start,
                planning_end_date=planning_end,
                monitoring_start_date=monitoring_start,
                monitoring_end_date=monitoring_end,
                rating_start_date=rating_start,
                rating_end_date=rating_end
            )
            
            db.session.add(settings)
            db.session.commit()
            print_success(f"System Settings created (ID: {settings.id})")
            return True
            
    except Exception as e:
        print_error(f"Failed to create System Settings: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False


def create_positions(app):
    """Create default positions"""
    print_step("2", "Creating Positions...")
    
    try:
        with app.app_context():
            # Check if positions already exist
            existing_count = Position.query.count()
            if existing_count > 0:
                print_info(f"Positions already exist ({existing_count}), skipping...")
                return True
            
            positions_data = [
                {
                    "name": "Faculty",
                    "core_weight": 0.0,
                    "strategic_weight": 0.0,
                    "support_weight": 0.0
                },
                {
                    "name": "Office Head",
                    "core_weight": 0.0,
                    "strategic_weight": 0.0,
                    "support_weight": 0.0
                },
                {
                    "name": "College President",
                    "core_weight": 0.0,
                    "strategic_weight": 0.0,
                    "support_weight": 0.0
                },
                {
                    "name": "Super Admin",
                    "core_weight": 0.0,
                    "strategic_weight": 0.0,
                    "support_weight": 0.0
                }
            ]
            
            for pos_data in positions_data:
                position = Position(**pos_data, status=1)
                db.session.add(position)
            
            db.session.commit()
            print_success(f"Created {len(positions_data)} positions")
            return True
            
    except Exception as e:
        print_error(f"Failed to create Positions: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False


def create_categories(app):
    """Create default categories"""
    print_step("3", "Creating Categories...")
    
    try:
        with app.app_context():
            # Check if categories already exist
            existing_count = Category.query.count()
            if existing_count > 0:
                print_info(f"Categories already exist ({existing_count}), skipping...")
                return True
            
            categories_data = [
                {
                    "name": "Core Function",
                    "type": "Core Function",
                    "description": "Core functions and responsibilities",
                    "priority_order": 1
                },
                {
                    "name": "Strategic",
                    "type": "Strategic",
                    "description": "Strategic initiatives and goals",
                    "priority_order": 2
                },
                {
                    "name": "Support",
                    "type": "Support",
                    "description": "Support and administrative tasks",
                    "priority_order": 3
                }
            ]
            
            for cat_data in categories_data:
                category = Category(**cat_data, status=1)
                db.session.add(category)
            
            db.session.commit()
            print_success(f"Created {len(categories_data)} categories")
            return True
            
    except Exception as e:
        print_error(f"Failed to create Categories: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False


def create_departments(app, org_name):
    """Create root department"""
    print_step("4", "Creating Departments...")
    
    try:
        with app.app_context():
            # Check if departments already exist
            existing_count = Department.query.count()
            if existing_count > 0:
                print_info(f"Departments already exist ({existing_count}), skipping...")
                return True
            
            # Create root department
            root_dept = Department(
                name=org_name,
                icon="building",
                manager_id=0,
                status=1
            )
            
            db.session.add(root_dept)
            db.session.commit()
            print_success(f"Created root department: '{org_name}' (ID: {root_dept.id})")
            return True
            
    except Exception as e:
        print_error(f"Failed to create Departments: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False


def create_admin_profile_and_user(app, admin_email, admin_name):
    """Create admin profile and user account"""
    print_step("5", "Creating Admin Profile and User Account...")
    
    try:
        with app.app_context():
            # Check if profile already exists
            existing_profile = Profile.query.filter_by(email=admin_email).first()
            if existing_profile:
                print_info(f"Profile with email '{admin_email}' already exists, skipping...")
                return True
            
            # Hash the default password
            ph = PasswordHasher()
            default_password = "commithubnc"
            hashed_password = ph.hash(default_password)
            
            # Create profile
            profile = Profile(
                email=admin_email,
                password=hashed_password,
                recovery_email=None,
                two_factor_enabled=False,
                active_status=True
            )
            
            db.session.add(profile)
            db.session.flush()  # Get the ID without committing yet
            
            # Parse admin name (simple split by space)
            name_parts = admin_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else "Admin"
            last_name = name_parts[-1] if len(name_parts) > 1 else "User"
            middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
            
            # Create user account
            admin_user = User(
                profile_id=profile.id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                role="administrator",
                position_id=4,  # Super Admin position
                department_id=1,  # Root department
                active_status=True,
                account_status=1
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print_success(f"Created Profile: {admin_email}")
            print_success(f"Created User: {admin_user.full_name()} (Administrator)")
            print_info(f"Default password: '{default_password}'")
            print_info("⚠ Change this password immediately after first login!")
            
            return True
            
    except Exception as e:
        print_error(f"Failed to create Admin Profile and User: {e}")
        traceback.print_exc()
        db.session.rollback()
        return False


def verify_setup(app):
    """Verify all foundation data was created correctly"""
    print_step("6", "Verifying Setup...")
    
    checks = {
        "System Settings": (System_Settings, 1),
        "Positions": (Position, 4),
        "Categories": (Category, 3),
        "Departments": (Department, 1),
        "Profiles": (Profile, 1),
        "Users": (User, 1),
    }
    
    all_passed = True
    
    try:
        with app.app_context():
            for check_name, (model, expected_count) in checks.items():
                actual_count = model.query.count()
                if actual_count >= expected_count:
                    print_success(f"{check_name}: {actual_count} ✓")
                else:
                    print_error(f"{check_name}: Expected {expected_count}, got {actual_count} ✗")
                    all_passed = False
            
            # Additional checks
            admin_user = User.query.filter_by(role="administrator").first()
            if admin_user:
                print_success(f"Admin User found: {admin_user.full_name()}")
            else:
                print_error("Admin User not found")
                all_passed = False
            
            if all_passed:
                print(f"\n{Colors.GREEN}{Colors.BOLD}All verification checks passed! ✓{Colors.RESET}\n")
            else:
                print(f"\n{Colors.RED}{Colors.BOLD}Some verification checks failed! ✗{Colors.RESET}\n")
            
            return all_passed
            
    except Exception as e:
        print_error(f"Verification failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Main seeding orchestration"""
    print_header("CommitHub Database Seeding")
    
    # Load Flask app
    app = create_app()
    
    # Check environment
    print_info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print_info(f"Environment: {'Development' if not app.config.get('TESTING') else 'Testing'}\n")
    
    # Check for existing data
    print_step("0", "Checking for existing data...")
    check_result = check_existing_data(app)
    
    if check_result is False:
        print_error("Database already seeded. Aborting.")
        return 1
    elif check_result is None:
        print_error("Could not verify database state. Aborting.")
        return 1
    
    print_success("Database is clean. Proceeding with seeding.\n")
    
    # Get organization details
    org_details = get_organization_details()
    
    # Execute seeding steps
    with app.app_context():
        try:
            db.create_all()  # Ensure all tables exist
            print_success("Database tables verified\n")
        except Exception as e:
            print_error(f"Failed to create tables: {e}")
            return 1
    
    steps = [
        (create_system_settings, (app,)),
        (create_positions, (app,)),
        (create_categories, (app,)),
        (create_departments, (app, org_details["org_name"])),
        (create_admin_profile_and_user, (app, org_details["admin_email"], org_details["admin_name"])),
    ]
    
    for step_func, args in steps:
        result = step_func(*args)
        if not result:
            print_error(f"Seeding failed at step: {step_func.__name__}")
            return 1
    
    # Verify setup
    if not verify_setup(app):
        print_error("Setup verification failed")
        return 1
    
    # Final message
    print_header("Setup Complete!")
    print_success("Your CommitHub backend is ready to use!")
    print_info("Next steps:")
    print_info("  1. Start your Flask server: python app.py")
    print_info(f"  2. Login with email: {org_details['admin_email']}")
    print_info("     Password: commithubnc")
    print_info("  3. Change the password immediately")
    print_info("  4. Configure System Settings via the admin panel\n")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
