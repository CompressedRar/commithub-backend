"""
FormTemplate Service Layer
Handles business logic for form template operations with proper error handling.
Follows Separation of Concerns principle.
"""

from app import db
from flask import jsonify
from models.FormTemplate import (
    FormTemplate,
    FormInputField,
    FormOutputField,
    FormSubmission,
    FormFieldValue,
)
from sqlalchemy import exc


class FormTemplateService:
    """Service class for FormTemplate CRUD operations and business logic"""

    @staticmethod
    def create_template(data, created_by):
        """
        Create a new form template with input/output fields.
        
        Args:
            data: Dictionary containing template configuration
            created_by: User ID of template creator
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            # Validate required fields
            if not data.get("name") or not data.get("title"):
                return jsonify({"error": "Template name and title are required"}), 400

            # Check if template name already exists
            existing = FormTemplate.query.filter_by(name=data["name"]).first()
            if existing:
                return jsonify({"error": "Template name already exists"}), 409

            # Create template
            template = FormTemplate(
                name=data["name"],
                title=data["title"],
                subtitle=data.get("subtitle", ""),
                description=data.get("description", ""),
                logo_url=data.get("logoUrl"),
                grid_rows=data.get("gridRows", 3),
                grid_columns=data.get("gridColumns", 3),
                field_mapping=data.get("fieldMapping"),
                created_by=created_by,
                is_active=True,
            )

            db.session.add(template)
            db.session.flush()  # Get the template ID before adding fields

            # Add input fields
            input_fields = data.get("inputFields", [])
            for idx, field_data in enumerate(input_fields):
                input_field = FormInputField(
                    template_id=template.id,
                    field_id=field_data.get("id", f"field_{idx}"),
                    title=field_data.get("title", ""),
                    placeholder=field_data.get("placeholder", ""),
                    description=field_data.get("description", ""),
                    name=field_data.get("name", ""),
                    field_type=field_data.get("type", "String"),
                    user_type=field_data.get("user", "Admin"),
                    is_required=field_data.get("required", False),
                    validation_rules=field_data.get("validationRules"),
                    order=idx,
                )
                db.session.add(input_field)

            # Add output fields
            output_fields = data.get("outputFields", [])
            for idx, field_data in enumerate(output_fields):
                output_field = FormOutputField(
                    template_id=template.id,
                    field_id=field_data.get("id", f"output_{idx}"),
                    title=field_data.get("title", ""),
                    output_type=field_data.get("type", "IntegerModifier"),
                    input_field_name=field_data.get("inputFieldName"),
                    formula=field_data.get("formula"),
                    cases=field_data.get("cases"),
                    order=idx,
                )
                db.session.add(output_field)

            db.session.commit()
            return jsonify(template.to_dict()), 201

        except exc.IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Database integrity error - duplicate name or invalid data"}), 409
        except exc.DataError:
            db.session.rollback()
            return jsonify({"error": "Invalid data format"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to create template: {str(e)}"}), 500

    @staticmethod
    def get_template(template_id):
        """
        Get a template by ID with all its fields.
        
        Args:
            template_id: Template ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            print("Template:", template.to_dict())
            return jsonify(template.to_dict()), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve template: {str(e)}"}), 500

    @staticmethod
    def get_all_templates(skip=0, limit=20, is_active=None):
        """
        Get all templates with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Number of records to return
            is_active: Filter by active status (optional)
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            query = FormTemplate.query
            
            if is_active is not None:
                query = query.filter_by(is_active=is_active)
            
            total = query.count()
            templates = query.offset(skip).limit(limit).all()
            
            return jsonify({
                "templates": [t.to_dict_summary() for t in templates],
                "total": total,
                "skip": skip,
                "limit": limit,
            }), 200
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve templates: {str(e)}"}), 500

    @staticmethod
    def update_template(template_id, data):
        """
        Update an existing template and its fields.
        
        Args:
            template_id: Template ID
            data: Dictionary with updates
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            print(data.get("gridCols"))
            if not template:
                return jsonify({"error": "Template not found"}), 404

            # Update basic fields
            if "title" in data:
                template.title = data["title"]
            if "subtitle" in data:
                template.subtitle = data["subtitle"]
            if "description" in data:
                template.description = data["description"]
            if "logoUrl" in data:
                template.logo_url = data["logoUrl"]
            if "gridRows" in data:
                template.grid_rows = data["gridRows"]
            if "gridCols" in data:
                template.grid_columns = data["gridCols"]
            if "fieldMapping" in data:
                template.field_mapping = data["fieldMapping"]
            if "isPublished" in data:
                template.is_published = data["isPublished"]

            # Update input fields if provided
            if "inputFields" in data:
                fields = FormInputField.query.filter_by(template_id=template_id).all()
                for f in fields:
                    db.session.delete(f)

                for idx, field_data in enumerate(data["inputFields"]):
                    input_field = FormInputField(
                        template_id=template_id,
                        field_id=field_data.get("field_id", f"field_{idx}"),
                        title=field_data.get("title", ""),
                        placeholder=field_data.get("placeholder", ""),
                        description=field_data.get("description", ""),
                        name=field_data.get("name", ""),
                        field_type=field_data.get("type", "String"),
                        user_type=field_data.get("user", "Admin"),
                        is_required=field_data.get("required", False),
                        validation_rules=field_data.get("validationRules"),
                        order=idx,
                    )
                    db.session.add(input_field)

            # Update output fields if provided
            if "outputFields" in data:
                FormOutputField.query.filter_by(template_id=template_id).delete()

                for idx, field_data in enumerate(data["outputFields"]):
                    output_field = FormOutputField(
                        template_id=template_id,
                        field_id=field_data.get("field_id", f"output_{idx}"),
                        title=field_data.get("title", ""),
                        output_type=field_data.get("type", "IntegerModifier"),
                        input_field_name=field_data.get("inputFieldName"),
                        formula=field_data.get("formula"),
                        cases=field_data.get("cases"),
                        order=idx,
                    )
                    db.session.add(output_field)

            db.session.commit()
            return jsonify(template.to_dict()), 200

        except exc.IntegrityError as e:
            print(str(e.orig))
            print(f"IntegrityError occurred: {e}")
            db.session.rollback()
            return jsonify({"error": "Database integrity error"}), 409
        except Exception as e:
            print(f"Exception occurred: {e}")
            db.session.rollback()
            return jsonify({"error": f"Failed to update template: {str(e)}"}), 500

    @staticmethod
    def delete_template(template_id):
        """
        Delete a template and cascade delete related records.
        
        Args:
            template_id: Template ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            db.session.delete(template)
            db.session.commit()
            return jsonify({"message": "Template deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete template: {str(e)}"}), 500

    @staticmethod
    def publish_template(template_id):
        """
        Publish a template (make it available for submissions).
        
        Args:
            template_id: Template ID
            
        Returns:
            Tuple[dict, int] - Response JSON and HTTP status code
        """
        try:
            template = FormTemplate.query.get(template_id)
            if not template:
                return jsonify({"error": "Template not found"}), 404

            template.is_published = True
            db.session.commit()
            return jsonify(template.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to publish template: {str(e)}"}), 500
