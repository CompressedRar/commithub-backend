"""
Pytest configuration and shared fixtures for testing.
"""

import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import db, migrate
from config import TestConfig
from models.User import User
from models.Departments import Department
from models.System_Settings import System_Settings
from models.AdminConfirmation import AdminConfirmation


@pytest.fixture(scope="function")
def app():
    """Create Flask app with test config."""
    # Don't use create_app() since it loads env vars
    # Instead, create app directly with TestConfig
    from flask import Flask
    
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import routes after app is configured
    with app.app_context():
        from routes.Auth import auth
        from routes.Tests import test
        from routes.Department import department
        from routes.Category import category
        from routes.Task import task
        from routes.Users import users
        from routes.Logs import logs
        from routes.PCR import pcrs
        from routes.Chart import charts
        from routes.AI import ai
        from routes.Positions import positions
        from routes.Settings import settings
        
        app.register_blueprint(auth)
        app.register_blueprint(test)
        app.register_blueprint(department)
        app.register_blueprint(category)
        app.register_blueprint(task)
        app.register_blueprint(users)
        app.register_blueprint(logs)
        app.register_blueprint(pcrs)
        app.register_blueprint(charts)
        app.register_blueprint(ai)
        app.register_blueprint(positions)
        app.register_blueprint(settings)
        
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """App context for database operations."""
    with app.app_context():
        yield app


@pytest.fixture
def db_session(app):
    """Database session."""
    with app.app_context():
        yield db
        db.session.rollback()


@pytest.fixture
def test_department(app):
    """Create test department."""
    with app.app_context():
        dept = Department(
            name="Test Department"
        )
        db.session.add(dept)
        db.session.commit()
        return dept


@pytest.fixture
def test_admin_user(app):
    """Create test admin user."""
    with app.app_context():
        admin = User(
            email="admin@test.com",
            password="hashed_test_password",
            first_name="Test",
            last_name="Admin",
            role="administrator",
            account_status=1
        )
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def test_employee_user(app, test_department):
    """Create test employee user."""
    with app.app_context():
        employee = User(
            email="employee@test.com",
            password="hashed_test_password",
            first_name="Test",
            last_name="Employee",
            role="faculty",
            department_id=test_department.id,
            account_status=1
        )
        db.session.add(employee)
        db.session.commit()
        return employee


@pytest.fixture
def system_settings(app):
    """Create system settings."""
    with app.app_context():
        settings = System_Settings(
            current_period_id="PERIOD-2026-TEST123",
            quantity_formula={"expression": "(actual/target)*5"},
            efficiency_formula={"expression": "(actual/target)*5"},
            timeliness_formula={"expression": "(actual/target)*5"}
        )
        db.session.add(settings)
        db.session.commit()
        return settings


@pytest.fixture
def auth_headers(client, test_admin_user):
    """Get authorization headers with valid token."""
    # Mock login for testing
    from unittest.mock import patch
    
    with patch('models.User.Users.authenticate_user') as mock_auth:
        mock_auth.return_value = (
            {'token': 'test_token_12345', 'message': 'Login successful'},
            200
        )
        
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com',
            'password': 'password123'
        })
    
    # Return headers with token
    return {'Authorization': 'Bearer test_token_12345'}


@pytest.fixture
def admin_token(test_admin_user):
    """Generate valid JWT token for admin user."""
    import jwt
    from datetime import datetime, timedelta

    
    
    token = jwt.encode(
        {
            'id': 1,
            'email': "admin@gmail.com",
            'role': "administrator",
            'exp': datetime.utcnow() + timedelta(hours=1),
            
        },
        'priscilla',
        algorithm='HS256'
    )
    return token


@pytest.fixture
def employee_token(test_employee_user):
    """Generate valid JWT token for employee user."""
    import jwt
    from datetime import datetime, timedelta
    
    token = jwt.encode(
        {
            'id': 2,
            'email': "faculty@gmail.com",
            'role': "faculty",
            'exp': datetime.utcnow() + timedelta(hours=1)
        },
        'priscilla',
        algorithm='HS256'
    )
    return token


@pytest.fixture
def admin_headers(admin_token):
    """Authorization headers for admin user."""
    token = AdminConfirmation.create_for_user(1, 20)
    return {'Authorization': f'Bearer {admin_token}', 'X-Admin-Confirmation': f'{token}'}


@pytest.fixture
def employee_headers(employee_token):
    """Authorization headers for employee user."""
    return {'Authorization': f'Bearer {employee_token}'}


@pytest.fixture
def invalid_token_headers():
    """Authorization headers with invalid token."""
    return {'Authorization': 'Bearer invalid.token.here'}


@pytest.fixture
def malformed_headers():
    """Authorization headers with malformed format."""
    return {'Authorization': 'InvalidFormat token_here'}


