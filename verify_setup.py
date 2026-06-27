#!/usr/bin/env python
"""
CommitHub Database Verification Script
======================================
Verifies the integrity of the database setup after seeding.

Usage:
    python verify_setup.py

This script will:
1. Check all foundation tables exist
2. Verify expected data counts
3. Check for data integrity issues
4. Validate foreign key relationships
5. Test admin authentication

Author: CommitHub Team
Version: 1.0
"""

import os
import sys
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models.User import Profile, User
from models.Positions import Position
from models.Categories import Category
from models.Departments import Department
from models.System_Settings import System_Settings
from models.Logs import Log
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


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


def print_check(check_name, result, details=""):
    """Print a check result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  [{status}] {check_name}")
    if details:
        print(f"       {details}")


def print_info(text):
    """Print informational text"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


def print_section(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-' * 70}{Colors.RESET}")


def verify_tables_exist(app):
    """Verify all required tables exist"""
    print_section("1. TABLE EXISTENCE CHECKS")
    
    tables = {
        "profiles": Profile,
        "users": User,
        "positions": Position,
        "categories": Category,
        "departments": Department,
        "system_settings": System_Settings,
        "logs": Log,
    }
    
    all_exist = True
    
    with app.app_context():
        for table_name, model in tables.items():
            try:
                count = model.query.count()
                print_check(f"Table '{table_name}' exists", True, f"{count} records")
            except Exception as e:
                print_check(f"Table '{table_name}' exists", False, str(e))
                all_exist = False
    
    return all_exist


def verify_data_counts(app):
    """Verify expected data counts"""
    print_section("2. DATA COUNT CHECKS")
    
    checks = {
        "System Settings (should be 1)": (System_Settings, 1, 1),
        "Positions (should be 4)": (Position, 4, None),
        "Categories (should be 3)": (Category, 3, None),
        "Departments (should be >= 1)": (Department, 1, None),
        "Profiles (should be >= 1)": (Profile, 1, None),
        "Users (should be >= 1)": (User, 1, None),
    }
    
    all_passed = True
    
    with app.app_context():
        for check_name, (model, min_count, exact_count) in checks.items():
            actual_count = model.query.count()
            
            if exact_count is not None:
                passed = actual_count == exact_count
                expected = f"exactly {exact_count}"
            else:
                passed = actual_count >= min_count
                expected = f"at least {min_count}"
            
            print_check(check_name, passed, f"Found: {actual_count}, Expected: {expected}")
            all_passed = all_passed and passed
    
    return all_passed


def verify_foundation_data(app):
    """Verify specific foundation data"""
    print_section("3. FOUNDATION DATA CHECKS")
    
    all_passed = True
    
    with app.app_context():
        # Check specific positions
        positions_to_check = ["Faculty", "Office Head", "College President", "Super Admin"]
        print("\n  Positions:")
        for pos_name in positions_to_check:
            pos = Position.query.filter_by(name=pos_name).first()
            exists = pos is not None
            print_check(f"  Position '{pos_name}'", exists)
            all_passed = all_passed and exists
        
        # Check specific categories
        print("\n  Categories:")
        categories_to_check = ["Core Function", "Strategic", "Support"]
        for cat_name in categories_to_check:
            cat = Category.query.filter_by(name=cat_name).first()
            exists = cat is not None
            print_check(f"  Category '{cat_name}'", exists)
            all_passed = all_passed and exists
        
        # Check system settings
        print("\n  System Settings:")
        settings = System_Settings.query.first()
        if settings:
            checks = [
                ("Rating thresholds configured", settings.rating_thresholds and len(settings.rating_thresholds) > 0),
                ("Alert thresholds configured", settings.alert_thresholds and len(settings.alert_thresholds) > 0),
                ("Period dates set", settings.planning_start_date is not None),
                ("Current phase set", settings.current_phase is not None),
            ]
            for check_name, result in checks:
                print_check(f"  {check_name}", result)
                all_passed = all_passed and result
        else:
            print_check("  System Settings exists", False)
            all_passed = False
    
    return all_passed


def verify_foreign_keys(app):
    """Verify foreign key relationships"""
    print_section("4. FOREIGN KEY RELATIONSHIP CHECKS")
    
    all_passed = True
    
    with app.app_context():
        # Check all users have valid profile_id
        users_without_profile = User.query.filter(
            ~User.profile_id.in_(db.session.query(Profile.id))
        ).count()
        
        print_check(
            "All users have valid profile references",
            users_without_profile == 0,
            f"Orphaned users: {users_without_profile}"
        )
        all_passed = all_passed and (users_without_profile == 0)
        
        # Check all users have valid position_id
        users_without_position = User.query.filter(
            ~User.position_id.in_(db.session.query(Position.id))
        ).count()
        
        print_check(
            "All users have valid position references",
            users_without_position == 0,
            f"Orphaned position links: {users_without_position}"
        )
        all_passed = all_passed and (users_without_position == 0)
        
        # Check all users have valid department_id
        users_without_dept = User.query.filter(
            ~User.department_id.in_(db.session.query(Department.id))
        ).count()
        
        print_check(
            "All users have valid department references",
            users_without_dept == 0,
            f"Orphaned department links: {users_without_dept}"
        )
        all_passed = all_passed and (users_without_dept == 0)
    
    return all_passed


def verify_unique_constraints(app):
    """Verify unique constraints are respected"""
    print_section("5. UNIQUE CONSTRAINT CHECKS")
    
    all_passed = True
    
    with app.app_context():
        # Check email uniqueness
        duplicate_emails = db.session.query(Profile.email).group_by(
            Profile.email
        ).having(db.func.count(Profile.email) > 1).count()
        
        print_check(
            "Profile emails are unique",
            duplicate_emails == 0,
            f"Duplicate emails: {duplicate_emails}"
        )
        all_passed = all_passed and (duplicate_emails == 0)
        
        # Check department name uniqueness
        duplicate_depts = db.session.query(Department.name).group_by(
            Department.name
        ).having(db.func.count(Department.name) > 1).count()
        
        print_check(
            "Department names are unique",
            duplicate_depts == 0,
            f"Duplicate names: {duplicate_depts}"
        )
        all_passed = all_passed and (duplicate_depts == 0)
        
        # Check position name uniqueness
        duplicate_pos = db.session.query(Position.name).group_by(
            Position.name
        ).having(db.func.count(Position.name) > 1).count()
        
        print_check(
            "Position names are unique",
            duplicate_pos == 0,
            f"Duplicate names: {duplicate_pos}"
        )
        all_passed = all_passed and (duplicate_pos == 0)
    
    return all_passed


def verify_admin_account(app):
    """Verify admin account and test authentication"""
    print_section("6. ADMIN ACCOUNT CHECKS")
    
    all_passed = True
    
    with app.app_context():
        # Check admin user exists
        admin_user = User.query.filter_by(role="administrator").first()
        
        admin_exists = admin_user is not None
        print_check("Administrator user exists", admin_exists)
        all_passed = all_passed and admin_exists
        
        if admin_user:
            print(f"\n  Admin Details:")
            print(f"    Name: {admin_user.full_name()}")
            print(f"    Email: {admin_user.profile.email}")
            print(f"    Role: {admin_user.role}")
            print(f"    Department: {admin_user.department.name if admin_user.department else 'N/A'}")
            
            # Verify profile relationship
            profile_exists = admin_user.profile is not None
            print_check("Admin has valid profile", profile_exists)
            all_passed = all_passed and profile_exists
            
            # Test password hashing
            if profile_exists:
                ph = PasswordHasher()
                try:
                    ph.verify(admin_user.profile.password, "commithubnc")
                    print_check("Default password is correctly hashed", True)
                except VerifyMismatchError:
                    print_check("Default password is correctly hashed", False, "Password hash doesn't match default")
                    all_passed = False
                except Exception as e:
                    print_check("Default password is correctly hashed", False, str(e))
                    all_passed = False
    
    return all_passed


def verify_system_status(app):
    """Verify overall system status"""
    print_section("7. SYSTEM STATUS SUMMARY")
    
    with app.app_context():
        total_users = User.query.count()
        total_departments = Department.query.count()
        total_positions = Position.query.count()
        total_categories = Category.query.count()
        
        print(f"\n  Total Records:")
        print(f"    Users: {total_users}")
        print(f"    Departments: {total_departments}")
        print(f"    Positions: {total_positions}")
        print(f"    Categories: {total_categories}")
        
        # System readiness
        admin = User.query.filter_by(role="administrator").first()
        system_ready = (
            total_users >= 1 and
            total_departments >= 1 and
            total_positions >= 4 and
            total_categories >= 3 and
            admin is not None
        )
        
        print_check(
            "System is ready for production",
            system_ready,
            "All foundation data is in place"
        )
        
        return system_ready


def main():
    """Main verification orchestration"""
    print_header("CommitHub Database Verification")
    
    # Load Flask app
    app = create_app()
    
    print_info(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all checks
    checks = [
        verify_tables_exist,
        verify_data_counts,
        verify_foundation_data,
        verify_foreign_keys,
        verify_unique_constraints,
        verify_admin_account,
        verify_system_status,
    ]
    
    results = []
    for check in checks:
        try:
            result = check(app)
            results.append(result)
        except Exception as e:
            print_info(f"Error during {check.__name__}: {e}")
            results.append(False)
    
    # Final report
    all_passed = all(results)
    
    print_header("Verification Complete")
    
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.RESET}")
        print(f"{Colors.GREEN}The database setup is valid and ready to use!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.RESET}")
        print(f"{Colors.RED}Please review the issues above.{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
