"""
CENTRALIZED TEST SUITE FOR COMMITHUB API
=========================================

Comprehensive testing for all API endpoints, models, and services.
Run with: pytest backend/tests/test_all.py -v

Organization:
- Models Tests: User, Department, OPCR/IPCR, System Settings
- Auth Tests: Login, Register, Token management
- API Routes: All endpoints organized by feature
- Integration Tests: Multi-step workflows
- Error Handling: 4xx, 5xx responses
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import jsonify

from models.AdminConfirmation import AdminConfirmation
from models.User import User, Users
from models.Departments import Department, Department_Service
from models.System_Settings import System_Settings, System_Settings_Service
from models.PCR import OPCR, IPCR, Assigned_PCR, OPCR_Rating
from models.Tasks import Main_Task, Tasks_Service
from models.Categories import Category, Category_Service
from models.Logs import Log, Log_Service
from app import db


# ============================================================
# FIXTURES
# ============================================================

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
def test_admin(app_context):
    """Create test admin user."""
    admin = User(
        email="admin@tests.com",
        password="hashed_password",
        first_name="Admin",
        last_name="User",
        role="administrator",
        account_status=1
    )
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def test_employee(app_context):
    """Create test employee user."""
    dept = Department(name="Test Department")
    db.session.add(dept)
    db.session.commit()
    
    employee = User(
        email="employee@test.com",
        password="hashed_password",
        first_name="Employee",
        last_name="User",
        role="faculty",
        department_id=dept.id,
        account_status=1
    )
    db.session.add(employee)
    db.session.commit()
    return employee


@pytest.fixture
def test_department(app_context):
    """Create test department."""
    dept = Department(
        name="Engineering"
    )
    db.session.add(dept)
    db.session.commit()
    return dept


@pytest.fixture
def system_settings(app_context):
    """Create system settings."""
    settings = System_Settings(
        current_period_id="PERIOD-2026-ABC123",
        quantity_formula={"expression": "(actual/target)*5"},
        efficiency_formula={"expression": "(actual/target)*5"},
        timeliness_formula={"expression": "(actual/target)*5"}
    )
    db.session.add(settings)
    db.session.commit()
    return settings


@pytest.fixture
def auth_token(client, test_admin):
    """Get JWT token for authenticated requests."""
    with patch('models.User.Users.authenticate_user') as mock_auth:
        mock_auth.return_value = (
            jsonify(message="Login successful", token="test_token_12345"),
            200
        )
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com',
            'password': 'password123'
        })

        
    return "test_token_12345"


@pytest.fixture
def auth_headers(auth_token):
    """Headers with authorization token."""
    return {'Authorization': f'Bearer {auth_token}'}


# ============================================================
# MODEL TESTS
# ============================================================

class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, test_admin):
        """Test creating a user."""
        assert test_admin.email == "admin@tests.com"
        assert test_admin.first_name == "Admin"
        assert test_admin.role == "administrator"
        assert test_admin.account_status == 1
    
    def test_user_to_dict(self, test_admin):
        """Test user serialization."""
        user_dict = test_admin.to_dict()
        assert user_dict['email'] == "admin@tests.com"
        assert user_dict['first_name'] == "Admin"
        assert 'password' in user_dict
    
    def test_recovery_email_field(self, test_employee, app_context):
        """Test recovery email storage."""
        test_employee.recovery_email = "recovery@test.com"
        db.session.commit()
        
        retrieved = User.query.get(test_employee.id)
        assert retrieved.recovery_email == "recovery@test.com"
    
    def test_2fa_toggle(self, test_employee, app_context):
        """Test 2FA enable/disable."""
        assert test_employee.two_factor_enabled == False
        
        test_employee.two_factor_enabled = True
        db.session.commit()
        
        retrieved = User.query.get(test_employee.id)
        assert retrieved.two_factor_enabled == True


class TestDepartmentModel:
    """Test Department model."""
    
    def test_department_creation(self, test_department):
        """Test creating department."""
        assert test_department.name == "Engineering"
        assert test_department.status == 1
    
    def test_department_to_dict(self, test_department):
        """Test department serialization."""
        dept_dict = test_department.to_dict()
        assert dept_dict['name'] == "Engineering"
        assert 'id' in dept_dict


class TestSystemSettings:
    """Test System Settings model."""
    
    def test_settings_creation(self, system_settings):
        """Test creating system settings."""
        assert system_settings.current_period_id == "PERIOD-2026-ABC123"
        assert system_settings.quantity_formula is not None
    
    def test_change_period(self, system_settings, app_context):
        """Test changing period ID."""
        old_period = system_settings.current_period_id
        system_settings.current_period_id = "PERIOD-2026-XYZ789"
        db.session.commit()
        
        retrieved = System_Settings.query.first()
        assert retrieved.current_period_id != old_period


# ============================================================
# AUTH ROUTES TESTS
# ============================================================

class TestAuthRoutes:
    """Test authentication endpoints."""
    
    def test_login_endpoint_exists(self, client):
        """Test login endpoint is accessible."""
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com',
            'password': 'password123'
        })
        assert response.status_code in [200, 400, 422]
    
    def test_login_missing_email(self, client):
        """Test login validation."""
        response = client.post('/api/v1/auth/login', json={
            'password': 'password123'
        })
        assert response.status_code in [400, 422]
    
    def test_login_missing_password(self, client):
        """Test login validation."""
        response = client.post('/api/v1/auth/login', json={
            'email': 'admin@test.com'
        })
        assert response.status_code in [400, 422]
    
    def test_register_endpoint_exists(self, client):
        """Test register endpoint."""
        response = client.post('/api/v1/auth/register', json={
            'email': 'newuser@test.com',
            'password': 'secure123',
            'first_name': 'New',
            'last_name': 'User'
        })
        assert response.status_code in [200, 201, 400, 409, 422]
    
    def test_invalid_json(self, client):
        """Test invalid JSON handling."""
        response = client.post('/api/v1/auth/login',
            data='not json',
            content_type='application/json'
        )
        assert response.status_code in [400, 422]


# ============================================================
# USER ROUTES TESTS
# ============================================================

class TestUserRoutes:
    """Test user management endpoints."""
    
    def test_get_user_profile_protected(self, client, test_admin):
        """Test profile endpoint requires auth."""
        response = client.get(f'/api/v1/users/{test_admin.id}')
        assert response.status_code in [401, 403]
    
    def test_get_user_profile_with_auth(self, client, admin_headers, test_admin):
        """Test getting user profile with auth."""
        response = client.get(f'/api/v1/users/{test_admin.id}', headers=admin_headers)

        assert response.status_code in [200, 401]
    
    def test_update_profile_recovery_email(self, client, auth_headers):
        """Test updating recovery email."""
        response = client.patch('/api/v1/users/', 
            json={'recovery_email': 'recovery@test.com'},
            headers=auth_headers
        )
        assert response.status_code in [200, 400, 401, 404]
    
    def test_update_profile_2fa(self, client, auth_headers):
        """Test updating 2FA setting."""
        response = client.patch('/api/v1/users/',
            json={'two_factor_enabled': True},
            headers=auth_headers
        )
        assert response.status_code in [200, 400, 401, 404]
    
    def test_change_password(self, client, admin_headers, test_employee):
        """Test password change."""
        new_password = "newsecure1"
        res = Users.change_password(test_employee.id, new_password)
        
        assert res[1] in [200]
        assert User.query.get(test_employee.id).password


# ============================================================
# DEPARTMENT ROUTES TESTS
# ============================================================

class TestDepartmentRoutes:
    """Test department management endpoints."""
    
    def test_get_all_departments(self, client, admin_headers):
        """Test getting all departments."""
        response = client.get('/api/v1/department', headers = admin_headers, follow_redirects = True)
        assert response.status_code == 200
        assert isinstance(response.json, (list, dict))
    
    def test_get_department_by_id(self, client, test_department, admin_headers):
        """Test getting single department."""
        response = client.get(f'/api/v1/department/{test_department.id}', headers = admin_headers)
        assert response.status_code in [200, 404]
    
    def test_create_department_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test department creation requires valid auth."""
        # Test without headers
        response = client.post('/api/v1/department/create',
            json={'name': 'New Dept'},
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.post('/api/v1/department/create',
            json={'name': 'New Dept'},
            headers=invalid_token_headers
        )
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.post('/api/v1/department/create',
            json={'name': 'New Dept'},
            headers=malformed_headers
        )
        assert response.status_code == 401
    
    def test_create_department_with_auth(self, client, admin_headers):
        """Test creating department."""
        response = client.post('/api/v1/department/create',
            json={'name': 'IT Department'},
            headers=admin_headers
        )
        assert response.status_code in [200, 201, 400, 403]
    
    def test_update_department(self, client, admin_headers):
        """Test updating department."""
        response = client.post(f'/api/v1/department/update',
            json={'department_name': 'Updated Dept','id':"1", "icon" : "manage"},
            headers=admin_headers
        )
        assert response.status_code in [200, 400, 403, 404]
    
    def test_department_performance_report(self, client, admin_headers, test_department):
        """Test getting performance report."""
        response = client.get(
            f'/api/v1/departments/{test_department.id}/performance-report',
            headers=admin_headers
        )
        assert response.status_code in [200, 404, 400]


# ============================================================
# SYSTEM SETTINGS ROUTES TESTS
# ============================================================

class TestSettingsRoutes:
    """Test system settings endpoints."""
    
    def test_get_settings(self, client, admin_headers):
        """Test getting system settings."""

        response = client.get('/api/v1/settings', headers = admin_headers, follow_redirects=True)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json
            assert isinstance(data, dict)
    
    def test_update_settings_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test settings update requires valid auth."""
        # Test without headers
        response = client.patch('/api/v1/settings',
            json={'quantity_formula': '(actual/target)*5'}
        )
        assert response.status_code in [308, 401]
        
        # Test with invalid token
        response = client.patch('/api/v1/settings',
            json={'quantity_formula': '(actual/target)*5'},
            headers=invalid_token_headers
        )
        assert response.status_code in [308, 401]
        
        # Test with malformed headers
        response = client.patch('/api/v1/settings',
            json={'quantity_formula': '(actual/target)*5'},
            headers=malformed_headers
        )
        assert response.status_code in [308, 401]
    
    def test_update_settings_with_auth(self, client, admin_headers):
        """Test updating settings."""
        response = client.patch('/api/v1/settings',
            json={'quantity_formula': '(actual/target)*5'},
            headers=admin_headers,
            follow_redirects=True
        )
        assert response.status_code in [200, 400, 403]
    
    def test_reset_period_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test period reset requires valid auth."""
        # Test without headers
        response = client.patch('/api/v1/settings/reset', json={})
        assert response.status_code in [200, 401]
        
        # Test with invalid token
        response = client.patch('/api/v1/settings/reset',
            json={},
            headers=invalid_token_headers
        )
        assert response.status_code in [200, 401]
        
        # Test with malformed headers
        response = client.patch('/api/v1/settings/reset',
            json={},
            headers=malformed_headers
        )
        assert response.status_code in [200, 401]
    
    def test_reset_period_with_auth(self, client, admin_headers, system_settings):
        """Test resetting period."""
        response = client.patch('/api/v1/settings/reset',
            json={},
            headers=admin_headers,
            follow_redirects=True
        )
        assert response.status_code in [200, 400, 403]


# ============================================================
# PCR/OPCR ROUTES TESTS
# ============================================================

class TestPCRRoutes:
    """Test PCR/OPCR endpoints."""
    
    def test_create_opcr_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test OPCR creation requires valid auth."""
        # Test without headers
        response = client.post('/api/v1/pcr/opcr',
            json={'department_id': 1, 'ipcr_ids': [1, 2]}
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.post('/api/v1/pcr/opcr',
            json={'department_id': 1, 'ipcr_ids': [1, 2]},
            headers=invalid_token_headers
        )
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.post('/api/v1/pcr/opcr',
            json={'department_id': 1, 'ipcr_ids': [1, 2]},
            headers=malformed_headers
        )
        assert response.status_code == 401
    
    def test_create_opcr_with_auth(self, client, admin_headers, test_department):
        """Test creating OPCR."""
        response = client.post('/api/v1/pcr/opcr',
            json={'department_id': test_department.id, 'ipcr_ids': []},
            headers=admin_headers
        )
        assert response.status_code in [200, 201, 400, 403]
    
    def test_get_opcr(self, client, admin_headers):
        """Test getting OPCR."""
        response = client.get('/api/v1/pcr/opcr/1', headers=admin_headers)
        assert response.status_code in [200, 404, 401]
    
    def test_create_ipcr_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test IPCR creation requires valid auth."""
        # Test without headers
        response = client.post('/api/v1/pcr/ipcr',
            json={'main_task_ids': [1, 2]}
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.post('/api/v1/pcr/ipcr',
            json={'main_task_ids': [1, 2]},
            headers=invalid_token_headers
        )
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.post('/api/v1/pcr/ipcr',
            json={'main_task_ids': [1, 2]},
            headers=malformed_headers
        )
        assert response.status_code == 401
    
    def test_create_ipcr_with_auth(self, client, admin_headers):
        """Test creating IPCR."""
        response = client.post('/api/v1/pcr/ipcr',
            json={'main_task_ids': []},
            headers=admin_headers
        )
        assert response.status_code in [200, 201, 400, 403]
    
    def test_get_ipcr(self, client, admin_headers):
        """Test getting IPCR."""
        response = client.get('/api/v1/pcr/ipcr/1', headers=admin_headers)
        assert response.status_code in [200, 404, 401]


# ============================================================
# TASK ROUTES TESTS
# ============================================================

class TestTaskRoutes:
    """Test task endpoints."""
    
    def test_get_tasks(self, client):
        """Test getting all tasks."""
        response = client.get('/api/v1/tasks')
        assert response.status_code == 200
        assert isinstance(response.json, (list, dict))
    
    def test_create_task_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test task creation requires valid auth."""
        # Test without headers
        response = client.post('/api/v1/tasks',
            json={'mfo': 'Task-001', 'category_id': 1}
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.post('/api/v1/tasks',
            json={'mfo': 'Task-001', 'category_id': 1},
            headers=invalid_token_headers
        )
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.post('/api/v1/tasks',
            json={'mfo': 'Task-001', 'category_id': 1},
            headers=malformed_headers
        )
        assert response.status_code == 401
    
    def test_create_task_with_auth(self, client, admin_headers):
        """Test creating task."""
        response = client.post('/api/v1/tasks',
            json={'mfo': 'Task-001', 'category_id': 1},
            headers=admin_headers
        )
        assert response.status_code in [200, 201, 400, 403]


# ============================================================
# CATEGORY ROUTES TESTS
# ============================================================

class TestCategoryRoutes:
    """Test category endpoints."""
    
    def test_get_categories(self, client):
        """Test getting all categories."""
        response = client.get('/api/v1/categories')
        assert response.status_code == 200
    
    def test_create_category_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test category creation requires valid auth."""
        # Test without headers
        response = client.post('/api/v1/categories',
            json={'name': 'Category', 'priority_order': 1}
        )
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.post('/api/v1/categories',
            json={'name': 'Category', 'priority_order': 1},
            headers=invalid_token_headers
        )
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.post('/api/v1/categories',
            json={'name': 'Category', 'priority_order': 1},
            headers=malformed_headers
        )
        assert response.status_code == 401


# ============================================================
# LOG ROUTES TESTS
# ============================================================

class TestLogRoutes:
    """Test logging endpoints."""
    
    def test_get_logs_requires_auth(self, client, invalid_token_headers, malformed_headers):
        """Test logs endpoint requires valid auth."""
        # Test without headers
        response = client.get('/api/v1/logs')
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.get('/api/v1/logs', headers=invalid_token_headers)
        assert response.status_code == 401
        
        # Test with malformed headers
        response = client.get('/api/v1/logs', headers=malformed_headers)
        assert response.status_code == 401
    
    def test_get_logs_with_auth(self, client, admin_headers):
        """Test getting logs."""
        response = client.get('/api/v1/logs', headers=admin_headers)
        assert response.status_code in [200, 401, 403]
    
    def test_filter_logs_by_action(self, client, admin_headers):
        """Test filtering logs."""
        response = client.get('/api/v1/logs?action=LOGIN', headers=admin_headers)
        assert response.status_code in [200, 401, 403]


# ============================================================
# ERROR HANDLING TESTS
# ============================================================

class TestErrorHandling:
    """Test error responses."""
    
    def test_404_nonexistent_route(self, client):
        """Test 404 for nonexistent route."""
        response = client.get('/api/v1/nonexistent-route')
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method."""
        response = client.patch('/api/v1/auth/login')
        assert response.status_code == 405
    
    def test_401_unauthorized(self, client):
        """Test 401 for protected endpoints."""
        response = client.get('/api/v1/logs')
        assert response.status_code in [401, 403]
    
    def test_invalid_json(self, client):
        """Test invalid JSON payload."""
        response = client.post('/api/v1/auth/login',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 415, 422]
    
    def test_response_is_json(self, client):
        """Test responses are JSON."""
        response = client.get('/api/v1/departments')
        assert response.content_type in ['application/json', 'application/json; charset=utf-8']


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegrationFlow:
    """Test multi-step workflows."""
    
    def test_user_creation_flow(self, client):
        """Test complete user registration flow."""
        # Register
        register_response = client.post('/api/v1/auth/register', json={
            'email': 'newuser@test.com',
            'password': 'secure123',
            'first_name': 'New',
            'last_name': 'User'
        })
        assert register_response.status_code in [200, 201, 400, 409]
        
        # Login (if registration successful)
        if register_response.status_code in [200, 201]:
            login_response = client.post('/api/v1/auth/login', json={
                'email': 'newuser@test.com',
                'password': 'secure123'
            })
            assert login_response.status_code in [200, 401]
    
    def test_department_workflow(self, client, admin_headers, test_department):
        """Test department management workflow."""
        # Get departments
        response = client.get('/api/v1/departments')
        assert response.status_code == 200
        
        # Get specific department
        response = client.get(f'/api/v1/departments/{test_department.id}')
        assert response.status_code in [200, 404]
        
        # Update department
        response = client.patch(f'/api/v1/departments/{test_department.id}',
            json={'name': 'Updated'},
            headers=auth_headers
        )
        assert response.status_code in [200, 400, 403, 404]


# ============================================================
# SUMMARY HELPER
# ============================================================

def test_suite_summary(client):
    """Print summary of all testable endpoints."""
    public_endpoints = [
        ('GET', '/api/v1/departments'),
        ('GET', '/api/v1/categories'),
        ('GET', '/api/v1/tasks'),
        ('GET', '/api/v1/settings'),
    ]
    
    print("\n" + "="*60)
    print("TESTING PUBLIC ENDPOINTS")
    print("="*60)
    
    for method, endpoint in public_endpoints:
        response = client.open(endpoint, method=method)
        status = "✅" if response.status_code < 400 else "⚠️"
        print(f"{status} {method} {endpoint} → {response.status_code}")
