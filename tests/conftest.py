"""
Pytest configuration and shared fixtures for testing.
"""

import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from config import TestConfig
from models.User import User
from models.Departments import Department
from models.System_Settings import System_Settings


@pytest.fixture(scope="function")
def app():
    """Create Flask app with test config."""
    app = create_app()

    with app.app_context():
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
            role="employee",
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

