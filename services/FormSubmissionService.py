"""
FormSubmission Service Layer
Handles business logic for form submissions and field value operations.
"""

from app import db
from flask import jsonify
from models.FormTemplate import (
    FormTemplate,
    FormInputField,
    FormSubmission,
    FormFieldValue,
    TaskResponse,
    Task
)
from sqlalchemy import exc
import json


class FormSubmissionService:
    """Service class for FormSubmission operations and field validation"""

    @staticmethod
    def validate_field_value(input_field, value):
        """
        Validate a field value against input field constraints.
        
        Args:
            input_field: FormInputField instance
            value: Value to validate
            
        Returns:
            Tuple[bool, str] - (is_valid, error_message)
        """
        # Check required fields
        if input_field.is_required and (value is None or value == ""):
            return False, f"Field '{input_field.title}' is required"

        if value is None or value == "":
            return True, ""

        # Type-specific validation
        field_type = input_field.field_type
        
        try:
            if field_type == "Integer":
                int(value)
            elif field_type == "Number":
                float(value)
            elif field_type == "Email":
                # Basic email validation
                if "@" not in str(value):
                    return False, f"Invalid email format in '{input_field.title}'"
            elif field_type == "Date":
                # Basic date validation - could be enhanced
                pass
            
            # Check validation rules
            if input_field.validation_rules:
                rules = input_field.validation_rules
                
                # Check min/max for numeric fields
                if field_type in ["Integer", "Number"]:
                    val = float(value)
                    if "min" in rules and val < rules["min"]:
                        return False, f"Value must be >= {rules['min']} in '{input_field.title}'"
                    if "max" in rules and val > rules["max"]:
                        return False, f"Value must be <= {rules['max']} in '{input_field.title}'"
                
                # Check pattern for string fields
                if field_type == "String" and "pattern" in rules:
                    import re
                    if not re.match(rules["pattern"], str(value)):
                        return False, f"Value does not match required pattern in '{input_field.title}'"
            
            return True, ""
        except ValueError:
            return False, f"Invalid value type for '{input_field.title}' (expected {field_type})"

    @staticmethod
    def create_submission(template_id, submitted_by, field_values, is_draft=False):
        """
        Create a new form submission with field values.
        
        Args:
            template_id: FormTemplate ID
            submitted_by: User ID of submitter
            field_values: Dictionary of field_id -> value mappings
            is_draft: Whether to save as draft
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            print("Creating submission for template:", template_id)
            print("Field values:", field_values)
            # Verify template exists and is published
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404
            
            if not is_draft and not template.is_published:
                return jsonify({"error": "Template is not published"}), 400

            # Validate all field values
            validation_errors = []
            field_mapping = {}  # Map field_id to input_field

            for input_field in template.input_fields:
                field_mapping[input_field.field_id] = input_field
                value = field_values.get(input_field.field_id)
                
                is_valid, error_msg = FormSubmissionService.validate_field_value(input_field, value)
                if not is_valid:
                    validation_errors.append(error_msg)

            if validation_errors:
                return jsonify({"error": "Validation failed", "errors": validation_errors}), 400

            # Create submission
            submission = FormSubmission(
                template_id=template_id,
                submitted_by=submitted_by,
                is_draft=is_draft,
            )
            db.session.add(submission)
            db.session.flush()  # Get submission ID

            # Add field values
            for field_id, value in field_values.items():
                print(field_mapping.keys(), str(value["id"]))
                input_field = field_mapping.get(str(value["field_id"]))

                if input_field:
                    # Convert value to JSON string for storage
                    value_str = value["value"] if value is not None else None
                    
                    field_value = FormFieldValue(
                        submission_id=submission.id,
                        input_field_id=input_field.id,
                        value=value_str,
                    ) 
                    print("created field value:", field_value.to_dict())
                    db.session.add(field_value)

            db.session.commit()
            print("Submission created with ID:", submission.to_dict())
            return jsonify(submission.to_dict()), 201

        except exc.IntegrityError as e:
            print(f"IntegrityError occurred: {e}")
            db.session.rollback()
            return jsonify({"error": "Database integrity error"}), 409
        except Exception as e:
            print(f"Exception occurred: {e}")
            db.session.rollback()
            return jsonify({"error": f"Failed to create submission: {str(e)}"}), 500

    @staticmethod
    def get_submission(submission_id):
        """
        Get a submission by ID with all field values.
        
        Args:
            submission_id: Submission ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            submission = FormSubmission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404
            return jsonify(submission.to_dict()), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve submission: {str(e)}"}), 500

    @staticmethod
    def get_template_submissions(template_id, skip=0, limit=20, include_drafts=False):
        """
        Get all submissions for a template with pagination.
        
        Args:
            template_id: Template ID
            skip: Number of records to skip
            limit: Number of records to return
            include_drafts: Include draft submissions
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            query = FormSubmission.query.filter_by(template_id=template_id).all()
            
            
            total = len(query)

            return jsonify({
                "submissions": [s.to_dict() for s in query],
                "total": total,
                "skip": skip,
                "limit": limit,
            }), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve submissions: {str(e)}"}), 500

    @staticmethod
    def get_user_submissions(user_id, template_id=None, skip=0, limit=20):
        """
        Get all submissions by a specific user.
        
        Args:
            user_id: User ID
            template_id: Optional filter by template ID
            skip: Number of records to skip
            limit: Number of records to return
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            query = FormSubmission.query.filter_by(submitted_by=user_id)
            
            if template_id:
                query = query.filter_by(template_id=template_id)
            
            total = query.count()
            submissions = query.offset(skip).limit(limit).order_by(
                FormSubmission.submission_date.desc()
            ).all()

            return jsonify({
                "submissions": [s.to_dict() for s in submissions],
                "total": total,
                "skip": skip,
                "limit": limit,
            }), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve submissions: {str(e)}"}), 500

    @staticmethod
    def update_submission(submission_id, field_values, is_draft=None):
        """
        Update a submission's field values.
        
        Args:
            submission_id: Submission ID
            field_values: Dictionary of field_id -> value mappings
            is_draft: Optional update draft status
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            submission = FormSubmission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404

            # Validate field values
            template = submission.template
            validation_errors = []
            field_mapping = {}

            for input_field in template.input_fields:
                field_mapping[input_field.field_id] = input_field
                if input_field.field_id in field_values:
                    value = field_values[input_field.field_id]
                    is_valid, error_msg = FormSubmissionService.validate_field_value(input_field, value)
                    if not is_valid:
                        validation_errors.append(error_msg)

            if validation_errors:
                return jsonify({"error": "Validation failed", "errors": validation_errors}), 400

            # Update field values
            for field_id, value in field_values.items():
                input_field = field_mapping.get(field_id)
                if input_field:
                    field_value = FormFieldValue.query.filter_by(
                        submission_id=submission_id,
                        input_field_id=input_field.id
                    ).first()
                    
                    value_str = json.dumps(value) if value is not None else None
                    
                    if field_value:
                        field_value.value = value_str
                    else:
                        field_value = FormFieldValue(
                            submission_id=submission_id,
                            input_field_id=input_field.id,
                            value=value_str,
                        )
                        db.session.add(field_value)

            # Update draft status if provided
            if is_draft is not None:
                submission.is_draft = is_draft

            db.session.commit()
            return jsonify(submission.to_dict()), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update submission: {str(e)}"}), 500

    @staticmethod
    def delete_submission(submission_id):
        """
        Delete a submission and its field values.
        
        Args:
            submission_id: Submission ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            submission = FormSubmission.query.get(submission_id)
            if not submission:
                return jsonify({"error": "Submission not found"}), 404

            db.session.delete(submission)
            db.session.commit()
            return jsonify({"message": "Submission deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete submission: {str(e)}"}), 500

    @staticmethod
    def get_submission_stats(template_id):
        """
        Get statistics for submissions on a template.
        
        Args:
            template_id: Template ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            total_submissions = FormSubmission.query.filter_by(template_id=template_id).count()
            draft_submissions = FormSubmission.query.filter_by(
                template_id=template_id,
                is_draft=True
            ).count()
            completed_submissions = total_submissions - draft_submissions

            return jsonify({
                "template_id": template_id,
                "total_submissions": total_submissions,
                "completed_submissions": completed_submissions,
                "draft_submissions": draft_submissions,
            }), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve stats: {str(e)}"}), 500


    @staticmethod
    def create_task_submission(data):
        try:
            new_response = TaskResponse(
                submitted_by=data["user_id"],
                task_id=data["task_id"],
                values=data["values"]
            )

            db.session.add(new_response)
            db.session.commit()

            return jsonify(new_response.to_dict()), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
        
    
    @staticmethod
    def create_task(template_id, created_by, data, category_id=None):
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            # Only validate ADMIN fields
            admin_fields = {
                f.field_id: f for f in template.input_fields if f.user_type == "Admin"
            }

            validation_errors = []

            for field_id, field in admin_fields.items():
                value = data.get("values", {}).get(field_id)
                is_valid, error = FormSubmissionService.validate_field_value(field, value)

                if not is_valid:
                    validation_errors.append(error)

            if validation_errors:
                return jsonify({"error": "Validation failed", "errors": validation_errors}), 400

            task = Task(
                template_id=template_id,
                created_by=created_by,
                title=" ",
                description=data.get("description"),
                values=data.get("values", {}),
                category_id=category_id
            )

            db.session.add(task)
            db.session.commit()

            return jsonify(task.to_dict()), 201

        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
        
    @staticmethod
    def get_tasks(template_id):
        try:
            tasks = Task.query.filter_by(template_id=template_id).all()

            return jsonify({
                "tasks": [t.to_dict() for t in tasks],
                "total": len(tasks)
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @staticmethod
    def get_task(task_id):
        try:
            task = Task.query.get(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404

            return jsonify(task.to_dict()), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    @staticmethod
    def update_task(task_id, data):
        try:
            task = Task.query.get(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404

            template = task.template

            admin_fields = {
                f.field_id: f for f in template.input_fields if f.user_type == "Admin"
            }

            validation_errors = []

            for field_id, value in data.get("values", {}).items():
                field = admin_fields.get(field_id)
                if field:
                    is_valid, error = FormSubmissionService.validate_field_value(field, value)
                    if not is_valid:
                        validation_errors.append(error)

            if validation_errors:
                return jsonify({"error": "Validation failed", "errors": validation_errors}), 400

            task.title = data.get("title", task.title)
            task.description = data.get("description", task.description)

            if "values" in data:
                task.values = data["values"]

            db.session.commit()

            return jsonify(task.to_dict()), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
        
    @staticmethod
    def delete_task(task_id):
        try:
            task = Task.query.get(task_id)
            if not task:
                return jsonify({"error": "Task not found"}), 404

            db.session.delete(task)
            db.session.commit()

            return jsonify({"message": "Task deleted"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
