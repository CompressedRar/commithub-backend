"""
CommitHub Flask CLI Commands
============================
Custom CLI commands for database management and setup.

Commands:
  flask seed-db          - Initialize the database with foundation data
  flask verify-db        - Verify database integrity
"""

import click
from datetime import date
from argon2 import PasswordHasher
from app import db
from models.User import Profile, User
from models.Positions import Position
from models.Categories import Category
from models.Departments import Department
from models.System_Settings import System_Settings


def init_cli(app):
    """Register CLI commands with the Flask app"""
    
    @app.cli.command()
    def seed_db():
        """Initialize the database with foundation data"""
        click.echo("\n" + "=" * 70)
        click.echo("CommitHub Database Seeding".center(70))
        click.echo("=" * 70 + "\n")
        
        # Check if database already has data
        try:
            profile_count = Profile.query.count()
            if profile_count > 0:
                click.secho("✗ Database already seeded.", fg="red")
                click.echo("To reset, delete all data from the database and try again.")
                return
        except Exception as e:
            click.secho(f"✗ Error checking database: {e}", fg="red")
            return
        
        # Get organization details interactively
        click.secho("Organization Setup", fg="blue", bold=True)
        org_name = click.prompt("Organization name", default="College")
        president_name = click.prompt("College President's full name", default="Dr. Juan dela Cruz")
        admin_name = click.prompt("Administrative officer's full name", default="Maria Santos")
        admin_email = click.prompt("Admin account email", default="admin@commithub.local")
        
        click.echo()
        
        # Create all tables
        try:
            db.create_all()
            click.secho("✓ Database tables verified", fg="green")
        except Exception as e:
            click.secho(f"✗ Failed to create tables: {e}", fg="red")
            return
        
        # Step 1: System Settings
        click.echo("\n[1] Creating System Settings...")
        try:
            rating_thresholds = {
                "1": {"min": 0, "max": 1.5, "label": "Poor"},
                "2": {"min": 1.5, "max": 2.5, "label": "Below Average"},
                "3": {"min": 2.5, "max": 3.5, "label": "Average"},
                "4": {"min": 3.5, "max": 4.5, "label": "Good"},
                "5": {"min": 4.5, "max": 5, "label": "Excellent"}
            }
            
            alert_thresholds = {
                "quantity": {"warning": 70, "critical": 50},
                "efficiency": {"warning": 70, "critical": 50},
                "timeliness": {"warning": 70, "critical": 50},
                "alert_to_roles": ["administrator", "head"],
                "daily_check_time": "08:00"
            }
            
            settings = System_Settings(
                rating_thresholds=rating_thresholds,
                alert_thresholds=alert_thresholds,
                enable_formula=False,
                quantity_formula={},
                efficiency_formula={},
                timeliness_formula={},
                kpi_definitions={},
                current_period_id="2024-Q1",
                current_president_fullname=president_name,
                current_mayor_fullname=admin_name,
                current_phase="planning",
                current_period="2024",
                planning_start_date=date(2024, 1, 1),
                planning_end_date=date(2024, 3, 31),
                monitoring_start_date=date(2024, 4, 1),
                monitoring_end_date=date(2024, 9, 30),
                rating_start_date=date(2024, 10, 1),
                rating_end_date=date(2024, 12, 31)
            )
            
            db.session.add(settings)
            db.session.commit()
            click.secho(f"✓ System Settings created (ID: {settings.id})", fg="green")
        except Exception as e:
            click.secho(f"✗ Failed: {e}", fg="red")
            db.session.rollback()
            return
        
        # Step 2: Positions
        click.echo("\n[2] Creating Positions...")
        try:
            positions_data = [
                ("Faculty", 0.0, 0.0, 0.0),
                ("Office Head", 0.0, 0.0, 0.0),
                ("College President", 0.0, 0.0, 0.0),
                ("Super Admin", 0.0, 0.0, 0.0),
            ]
            
            for name, core, strategic, support in positions_data:
                position = Position(
                    name=name,
                    core_weight=core,
                    strategic_weight=strategic,
                    support_weight=support,
                    status=1
                )
                db.session.add(position)
            
            db.session.commit()
            click.secho(f"✓ Created {len(positions_data)} positions", fg="green")
        except Exception as e:
            click.secho(f"✗ Failed: {e}", fg="red")
            db.session.rollback()
            return
        
        # Step 3: Categories
        click.echo("\n[3] Creating Categories...")
        try:
            categories_data = [
                ("Core Function", "Core Function", "Core functions and responsibilities", 1),
                ("Strategic", "Strategic", "Strategic initiatives and goals", 2),
                ("Support", "Support", "Support and administrative tasks", 3),
            ]
            
            for name, cat_type, description, priority in categories_data:
                category = Category(
                    name=name,
                    type=cat_type,
                    description=description,
                    priority_order=priority,
                    status=1
                )
                db.session.add(category)
            
            db.session.commit()
            click.secho(f"✓ Created {len(categories_data)} categories", fg="green")
        except Exception as e:
            click.secho(f"✗ Failed: {e}", fg="red")
            db.session.rollback()
            return
        
        # Step 4: Departments
        click.echo("\n[4] Creating Departments...")
        try:
            root_dept = Department(
                name=org_name,
                icon="building",
                manager_id=0,
                status=1
            )
            
            db.session.add(root_dept)
            db.session.commit()
            click.secho(f"✓ Created root department: '{org_name}' (ID: {root_dept.id})", fg="green")
        except Exception as e:
            click.secho(f"✗ Failed: {e}", fg="red")
            db.session.rollback()
            return
        
        # Step 5: Admin Profile and User
        click.echo("\n[5] Creating Admin Profile and User Account...")
        try:
            ph = PasswordHasher()
            default_password = "commithubnc"
            hashed_password = ph.hash(default_password)
            
            profile = Profile(
                email=admin_email,
                password=hashed_password,
                recovery_email=None,
                two_factor_enabled=False,
                active_status=True
            )
            
            db.session.add(profile)
            db.session.flush()
            
            name_parts = admin_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else "Admin"
            last_name = name_parts[-1] if len(name_parts) > 1 else "User"
            middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
            
            admin_user = User(
                profile_id=profile.id,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                role="administrator",
                position_id=4,
                department_id=1,
                active_status=True,
                account_status=1
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            click.secho(f"✓ Created Profile: {admin_email}", fg="green")
            click.secho(f"✓ Created User: {admin_user.full_name()} (Administrator)", fg="green")
            click.secho(f"✓ Default password: '{default_password}'", fg="yellow")
            click.secho("⚠  Change this password immediately after first login!", fg="yellow")
        except Exception as e:
            click.secho(f"✗ Failed: {e}", fg="red")
            db.session.rollback()
            return
        
        # Verify
        click.echo("\n[6] Verifying Setup...")
        try:
            checks = {
                "System Settings": System_Settings.query.count(),
                "Positions": Position.query.count(),
                "Categories": Category.query.count(),
                "Departments": Department.query.count(),
                "Profiles": Profile.query.count(),
                "Users": User.query.count(),
            }
            
            for check_name, count in checks.items():
                click.secho(f"✓ {check_name}: {count}", fg="green")
            
            click.echo("\n" + "=" * 70)
            click.secho("Setup Complete!".center(70), fg="green", bold=True)
            click.echo("=" * 70)
            click.secho(f"\nYour CommitHub backend is ready to use!", fg="green", bold=True)
            click.echo(f"Next steps:")
            click.echo(f"  1. Start your Flask server: python app.py")
            click.echo(f"  2. Login with email: {admin_email}")
            click.echo(f"     Password: {default_password}")
            click.echo(f"  3. Change the password immediately")
            click.echo(f"  4. Configure System Settings via the admin panel\n")
        except Exception as e:
            click.secho(f"✗ Verification failed: {e}", fg="red")
    
    @app.cli.command()
    def verify_db():
        """Verify database integrity"""
        click.echo("\n" + "=" * 70)
        click.echo("CommitHub Database Verification".center(70))
        click.echo("=" * 70 + "\n")
        
        checks_passed = 0
        checks_failed = 0
        
        try:
            # Check counts
            tables = {
                "System Settings": (System_Settings, 1),
                "Positions": (Position, 4),
                "Categories": (Category, 3),
                "Departments": (Department, 1),
                "Profiles": (Profile, 1),
                "Users": (User, 1),
            }
            
            click.echo("Data Counts:")
            for table_name, (model, expected) in tables.items():
                actual = model.query.count()
                if actual >= expected:
                    click.secho(f"✓ {table_name}: {actual}", fg="green")
                    checks_passed += 1
                else:
                    click.secho(f"✗ {table_name}: {actual} (expected {expected})", fg="red")
                    checks_failed += 1
            
            # Check specific foundation data
            click.echo("\nFoundation Data:")
            required_positions = ["Faculty", "Office Head", "College President", "Super Admin"]
            for pos_name in required_positions:
                if Position.query.filter_by(name=pos_name).first():
                    click.secho(f"✓ Position '{pos_name}'", fg="green")
                    checks_passed += 1
                else:
                    click.secho(f"✗ Position '{pos_name}' missing", fg="red")
                    checks_failed += 1
            
            # Check admin
            click.echo("\nAdmin Account:")
            admin = User.query.filter_by(role="administrator").first()
            if admin:
                click.secho(f"✓ Admin: {admin.full_name()} ({admin.profile.email})", fg="green")
                checks_passed += 1
            else:
                click.secho(f"✗ No administrator account found", fg="red")
                checks_failed += 1
            
            # Summary
            click.echo("\n" + "=" * 70)
            if checks_failed == 0:
                click.secho(f"✓ ALL CHECKS PASSED ({checks_passed} passed)".center(70), fg="green", bold=True)
                click.echo("The database setup is valid and ready to use!\n")
            else:
                click.secho(
                    f"✗ CHECKS FAILED ({checks_passed} passed, {checks_failed} failed)".center(70),
                    fg="red",
                    bold=True
                )
                click.echo("Please review the issues above.\n")
        
        except Exception as e:
            click.secho(f"✗ Verification error: {e}", fg="red")
