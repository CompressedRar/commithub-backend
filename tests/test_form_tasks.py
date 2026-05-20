"""
Tests for form-based task creation and submission workflow.
"""

import pytest
import json
from datetime import datetime
from app import db, create_app
from models.FormTemplate import FormTemplate, FormInputField
from models.Tasks import Main_Task, Sub_Task
from models.User import User
from models.Departments import Department
from models.System_Settings import System_Settings
from models.PCR import IPCR
from services.Tasks.tasks_service import Tasks_Service
from config import TestConfig


@pytest.fixture
def app():
    """Create app for testing."""
    app = create_app()
    app.config.from_object(TestConfig)
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user."""
    with app.app_context():
        user = User(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password="hashed_password",
            role="administrator"
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_department(app):
    """Create test department."""
    with app.app_context():
        dept = Department(name="Test Department")
        db.session.add(dept)
        db.session.commit()
        return dept


@pytest.fixture
def system_settings(app, test_department):
    """Create system settings."""
    with app.app_context():
        settings = System_Settings.query.first()
        if not settings:
            settings = System_Settings(
                current_period_id=1,
                rating_start_date=datetime(2024, 1, 1),
                rating_end_date=datetime(2024, 12, 31)
            )
            db.session.add(settings)
            db.session.commit()
        return settings


@pytest.fixture
def form_template(app, system_settings):
    """Create a form template with admin and user fields."""
    with app.app_context():
        template = FormTemplate(
            title="Test Form Task",
            description="A test form for creating tasks",
            active=True
        )
        db.session.add(template)
        db.session.flush()
        
        # Add admin fields
        admin_field1 = FormInputField(
            form_template_id=template.id,
            title="Task Target Quantity",
            fieldId="target_qty",
            type="Integer",
            user="Admin",
            required=True,
            description="Target quantity for the task"
        )
        admin_field2 = FormInputField(
            form_template_id=template.id,
            title="Task Description",
            fieldId="task_desc",
            type="String",
            user="Admin",
            required=True,
            description="Additional task description"
        )
        
        # Add user fields
        user_field1 = FormInputField(
            form_template_id=template.id,
            title="Actual Accomplishment",
            fieldId="actual_acc",
            type="Integer",
            user="User",
            required=True,
            description="What did you accomplish?"
        )
        
        db.session.add(admin_field1)
        db.session.add(admin_field2)
        db.session.add(user_field1)
        db.session.commit()
        
        return template


class TestFormTaskCreation:
    """Tests for creating form-based tasks."""
    
    def test_create_main_task_with_form(self, app, form_template):
        """Test creating a main task with form template."""
        with app.app_context():
            data = {
                "task_name": "Test Task",
                "description": "Test Description",
                "form_template_id": form_template.id,
                "category_id": 1,
                "admin_field_values": {
                    "target_qty": 100,
                    "task_desc": "Complete the test task"
                }
            }
            
            result = Tasks_Service.create_main_task_with_form(data)
            
            # Check response
            assert result[1] == 201, f"Expected 201, got {result[1]}: {result[0].json}"
            response_data = result[0].get_json()
            assert response_data.get("task_id") is not None
            assert response_data.get("message") == "Task successfully created with form template."
            
            # Verify task was created
            task_id = response_data["task_id"]
            task = Main_Task.query.get(task_id)
            assert task is not None
            assert task.form_template_id == form_template.id
            assert task.mfo == "Test Task"
            assert task.description == "Test Description"
    
    def test_create_main_task_missing_required_field(self, app, form_template):
        """Test creating task with missing required admin field."""
        with app.app_context():
            data = {
                "task_name": "Test Task",
                "description": "Test Description",
                "form_template_id": form_template.id,
                "category_id": 1,
                "admin_field_values": {
                    # Missing required "task_desc" field
                    "target_qty": 100
                }
            }
            
            result = Tasks_Service.create_main_task_with_form(data)
            
            # Should return 400 error
            assert result[1] == 400
            response_data = result[0].get_json()
            assert "required" in response_data.get("error", "").lower()
    
    def test_create_main_task_invalid_template(self, app):
        """Test creating task with non-existent template."""
        with app.app_context():
            data = {
                "task_name": "Test Task",
                "description": "Test Description",
                "form_template_id": 99999,  # Non-existent
                "category_id": 1,
                "admin_field_values": {}
            }
            
            result = Tasks_Service.create_main_task_with_form(data)
            
            # Should return 404
            assert result[1] == 404


class TestFormTaskResponse:
    """Tests for user form task responses."""
    
    def test_submit_form_task_response(self, app, test_user, form_template, system_settings):
        """Test submitting a user response to a form task."""
        with app.app_context():
            # First create a main task
            data = {
                "task_name": "Test Task",
                "description": "Test Description",
                "form_template_id": form_template.id,
                "category_id": 1,
                "admin_field_values": {
                    "target_qty": 100,
                    "task_desc": "Complete the test"
                }
            }
            
            create_result = Tasks_Service.create_main_task_with_form(data)
            assert create_result[1] == 201
            task_id = create_result[0].get_json()["task_id"]
            
            # Create IPCR for user
            ipcr = IPCR(
                user_id=test_user.id,
                period=system_settings.current_period_id
            )
            db.session.add(ipcr)
            db.session.commit()
            
            # Submit form response
            response_data = {
                "actual_acc": 85,
                "actual_time": 5,
                "actual_mod": 0
            }
            
            submit_result = Tasks_Service.create_form_task_response(
                task_id, test_user.id, response_data
            )
            
            # Check result
            assert submit_result[1] in (200, 201)
            response_json = submit_result[0].get_json()
            assert response_json.get("sub_task_id") is not None
            
            # Verify sub-task was created
            sub_task_id = response_json["sub_task_id"]
            sub_task = Sub_Task.query.get(sub_task_id)
            assert sub_task is not None
            assert sub_task.actual_acc == 85
            assert sub_task.actual_time == 5
            assert sub_task.actual_mod == 0


class TestFormTaskIntegration:
    """Integration tests for complete form task workflow."""
    
    def test_complete_form_task_workflow(self, app, test_user, form_template, system_settings):
        """Test complete workflow: create task -> submit response."""
        with app.app_context():
            # Step 1: Create form task
            create_data = {
                "task_name": "Integration Test Task",
                "description": "Testing complete workflow",
                "form_template_id": form_template.id,
                "category_id": 1,
                "admin_field_values": {
                    "target_qty": 100,
                    "task_desc": "Integration test"
                }
            }
            
            create_result = Tasks_Service.create_main_task_with_form(create_data)
            assert create_result[1] == 201
            task_id = create_result[0].get_json()["task_id"]
            
            # Step 2: Verify task was created with form template
            task = Main_Task.query.get(task_id)
            assert task.form_template_id == form_template.id
            
            # Step 3: Create IPCR for user
            ipcr = IPCR(
                user_id=test_user.id,
                period=system_settings.current_period_id
            )
            db.session.add(ipcr)
            db.session.commit()
            
            # Step 4: User submits response
            response_data = {
                "actual_acc": 95,
                "actual_time": 4,
                "actual_mod": 0
            }
            
            submit_result = Tasks_Service.create_form_task_response(
                task_id, test_user.id, response_data
            )
            assert submit_result[1] in (200, 201)
            
            # Step 5: Verify sub-task was created
            sub_task = Sub_Task.query.filter_by(main_task_id=task_id).first()
            assert sub_task is not None
            assert sub_task.actual_acc == 95
            
            # Step 6: Verify IPCR link
            assert sub_task.ipcr_id == ipcr.id
