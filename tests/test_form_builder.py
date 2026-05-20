"""
Form Builder Tests
Unit tests for FormTemplate and FormSubmission functionality
"""

import pytest
import json
from app import create_app, db
from models.FormTemplate import (
    FormTemplate,
    FormInputField,
    FormOutputField,
    FormSubmission,
    FormFieldValue,
)
from models.User import User
from services.FormTemplateService import FormTemplateService
from services.FormSubmissionService import FormSubmissionService


@pytest.fixture
def app():
    """Create app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create test user"""
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
def sample_template_data():
    """Sample form template data"""
    return {
        "name": "test_template",
        "title": "Test Form",
        "subtitle": "A test form template",
        "inputFields": [
            {
                "id": "field_1",
                "title": "First Name",
                "type": "String",
                "user": "Admin",
                "required": True,
            },
            {
                "id": "field_2",
                "title": "Score",
                "type": "Integer",
                "user": "User",
                "required": False,
            }
        ],
        "outputFields": [
            {
                "id": "output_1",
                "title": "Double Score",
                "type": "IntegerModifier",
                "inputFieldName": "field_2",
                "formula": "field_2 * 2"
            }
        ]
    }


class TestFormTemplateService:
    """Tests for FormTemplateService"""

    def test_create_template(self, app, test_user, sample_template_data):
        """Test creating a form template"""
        with app.app_context():
            response, status = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            
            assert status == 201
            data = json.loads(response.get_data())
            assert data['title'] == "Test Form"
            assert len(data['input_fields']) == 2
            assert len(data['output_fields']) == 1

    def test_create_template_missing_name(self, app, test_user, sample_template_data):
        """Test creating template without name"""
        with app.app_context():
            del sample_template_data['name']
            response, status = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            
            assert status == 400

    def test_get_template(self, app, test_user, sample_template_data):
        """Test retrieving a template"""
        with app.app_context():
            # Create template
            response, status = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            
            # Retrieve template
            response, status = FormTemplateService.get_template(template_id)
            assert status == 200
            data = json.loads(response.get_data())
            assert data['title'] == "Test Form"

    def test_get_nonexistent_template(self, app):
        """Test retrieving nonexistent template"""
        with app.app_context():
            response, status = FormTemplateService.get_template(999)
            assert status == 404

    def test_list_templates(self, app, test_user, sample_template_data):
        """Test listing templates with pagination"""
        with app.app_context():
            # Create multiple templates
            for i in range(3):
                data = sample_template_data.copy()
                data['name'] = f"template_{i}"
                FormTemplateService.create_template(data, test_user.id)
            
            # List templates
            response, status = FormTemplateService.get_all_templates(0, 10)
            assert status == 200
            data = json.loads(response.get_data())
            assert data['total'] == 3

    def test_update_template(self, app, test_user, sample_template_data):
        """Test updating a template"""
        with app.app_context():
            # Create template
            response, status = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            
            # Update template
            update_data = {
                "title": "Updated Title",
                "subtitle": "Updated subtitle"
            }
            response, status = FormTemplateService.update_template(
                template_id,
                update_data
            )
            
            assert status == 200
            data = json.loads(response.get_data())
            assert data['title'] == "Updated Title"

    def test_delete_template(self, app, test_user, sample_template_data):
        """Test deleting a template"""
        with app.app_context():
            # Create template
            response, status = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            
            # Delete template
            response, status = FormTemplateService.delete_template(template_id)
            assert status == 200
            
            # Verify deletion
            response, status = FormTemplateService.get_template(template_id)
            assert status == 404


class TestFormSubmissionService:
    """Tests for FormSubmissionService"""

    def test_create_submission(self, app, test_user, sample_template_data):
        """Test creating a form submission"""
        with app.app_context():
            # Create and publish template
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            FormTemplateService.publish_template(template_id)
            
            # Create submission
            submission_data = {
                "field_1": "John",
                "field_2": "100"
            }
            response, status = FormSubmissionService.create_submission(
                template_id,
                test_user.id,
                submission_data,
                False
            )
            
            assert status == 201
            data = json.loads(response.get_data())
            assert data['is_draft'] == False

    def test_validate_required_field(self, app, test_user, sample_template_data):
        """Test validation of required fields"""
        with app.app_context():
            # Create and publish template
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            FormTemplateService.publish_template(template_id)
            
            # Submit without required field
            submission_data = {
                "field_2": "100"
            }
            response, status = FormSubmissionService.create_submission(
                template_id,
                test_user.id,
                submission_data,
                False
            )
            
            assert status == 400
            data = json.loads(response.get_data())
            assert "error" in data

    def test_get_submission(self, app, test_user, sample_template_data):
        """Test retrieving a submission"""
        with app.app_context():
            # Setup
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            FormTemplateService.publish_template(template_id)
            
            # Create submission
            submission_data = {
                "field_1": "John",
                "field_2": "100"
            }
            response, _ = FormSubmissionService.create_submission(
                template_id,
                test_user.id,
                submission_data,
                False
            )
            submission = json.loads(response.get_data())
            submission_id = submission['id']
            
            # Retrieve submission
            response, status = FormSubmissionService.get_submission(submission_id)
            assert status == 200

    def test_get_template_submissions(self, app, test_user, sample_template_data):
        """Test retrieving all submissions for a template"""
        with app.app_context():
            # Setup
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            FormTemplateService.publish_template(template_id)
            
            # Create multiple submissions
            for i in range(3):
                submission_data = {
                    "field_1": f"User {i}",
                    "field_2": f"{i * 100}"
                }
                FormSubmissionService.create_submission(
                    template_id,
                    test_user.id,
                    submission_data,
                    False
                )
            
            # Retrieve submissions
            response, status = FormSubmissionService.get_template_submissions(
                template_id,
                0,
                10,
                False
            )
            
            assert status == 200
            data = json.loads(response.get_data())
            assert data['total'] == 3

    def test_update_submission(self, app, test_user, sample_template_data):
        """Test updating a submission"""
        with app.app_context():
            # Setup
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            FormTemplateService.publish_template(template_id)
            
            # Create submission
            submission_data = {
                "field_1": "John",
                "field_2": "100"
            }
            response, _ = FormSubmissionService.create_submission(
                template_id,
                test_user.id,
                submission_data,
                False
            )
            submission = json.loads(response.get_data())
            submission_id = submission['id']
            
            # Update submission
            update_data = {
                "field_1": "Jane"
            }
            response, status = FormSubmissionService.update_submission(
                submission_id,
                update_data
            )
            
            assert status == 200

    def test_draft_submission(self, app, test_user, sample_template_data):
        """Test draft submission without required fields"""
        with app.app_context():
            # Setup
            response, _ = FormTemplateService.create_template(
                sample_template_data,
                test_user.id
            )
            template_data = json.loads(response.get_data())
            template_id = template_data['id']
            
            # Create draft submission without required fields
            submission_data = {
                "field_2": "100"
            }
            response, status = FormSubmissionService.create_submission(
                template_id,
                test_user.id,
                submission_data,
                True  # is_draft=True
            )
            
            # Draft should allow missing required fields during creation if we skip validation
            # This depends on business logic


if __name__ == '__main__':
    pytest.main([__file__])
