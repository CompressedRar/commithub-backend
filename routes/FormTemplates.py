"""
Form Template Routes
API endpoints for managing form templates and their configuration.
"""

from flask import Blueprint, request, jsonify
from services.FormTemplateService import FormTemplateService
from models.FormTemplate import FormTemplate
from utils.decorators import log_action, token_required

# Create blueprint
form_templates_bp = Blueprint("form_templates", __name__, url_prefix="/api/v1/form-templates")


@form_templates_bp.route("", methods=["POST"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="CREATE_FORM_TEMPLATE", target="FormTemplate")
def create_form_template():
    """
    Create a new form template.
    
    Request body:
    {
        "name": "string (unique)",
        "title": "string",
        "subtitle": "string (optional)",
        "description": "string (optional)",
        "logoUrl": "string (optional)",
        "gridRows": int (default: 3),
        "gridColumns": int (default: 3),
        "fieldMapping": object (optional),
        "inputFields": [
            {
                "id": "field_id",
                "title": "string",
                "placeholder": "string",
                "description": "string",
                "name": "string",
                "type": "String|Integer|Number|Email|Date|Boolean|TextArea|Dropdown",
                "user": "Admin|User",
                "required": boolean,
                "validationRules": {} (optional)
            }
        ],
        "outputFields": [
            {
                "id": "output_id",
                "title": "string",
                "type": "IntegerModifier|CaseOutput|...",
                "inputFieldName": "string",
                "formula": "string (for IntegerModifier)",
                "cases": [] (for CaseOutput)
            }
        ]
    }
    """
    data = request.get_json()
    return FormTemplateService.create_template(data, 24)


@form_templates_bp.route("/<int:template_id>", methods=["GET"])
@token_required()
def get_form_template(template_id):
    """Get a specific form template by ID"""
    return FormTemplateService.get_template(template_id)


@form_templates_bp.route("", methods=["GET"])
@token_required()
def list_form_templates():
    """
    List all form templates with pagination.
    
    Query parameters:
    - skip: Number of templates to skip (default: 0)
    - limit: Number of templates to return (default: 20)
    - active: Filter by active status (optional: true|false)
    """
    skip = request.args.get("skip", default=0, type=int)
    limit = request.args.get("limit", default=20, type=int)
    active = request.args.get("active", default=None, type=lambda x: x.lower() == "true" if x else None)
    
    return FormTemplateService.get_all_templates(skip, limit, active)


@form_templates_bp.route("/<int:template_id>", methods=["PUT"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="UPDATE_FORM_TEMPLATE", target="FormTemplate")
def update_form_template( template_id):
    """
    Update a form template.
    
    Supports partial updates - only send fields that need to be changed.
    """
    data = request.get_json()
    return FormTemplateService.update_template(template_id, data)


@form_templates_bp.route("/<int:template_id>", methods=["PATCH"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="UPDATE_FORM_TEMPLATE", target="FormTemplate")
def patch_form_template(template_id):
    """
    Partially update a form template.
    
    Supports partial updates - only send fields that need to be changed.
    """
    data = request.get_json()
    return FormTemplateService.update_template(template_id, data)


@form_templates_bp.route("/<int:template_id>", methods=["DELETE"])
@token_required(allowed_roles=["administrator"])
@log_action(action="DELETE_FORM_TEMPLATE", target="FormTemplate")
def delete_form_template( template_id):
    """Delete a form template"""
    return FormTemplateService.delete_template(template_id)


@form_templates_bp.route("/<int:template_id>/publish", methods=["POST"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="PUBLISH_FORM_TEMPLATE", target="FormTemplate")
def publish_form_template(template_id):
    """Publish a form template (make it available for submissions)"""
    return FormTemplateService.publish_template(template_id)


@form_templates_bp.route("/<int:template_id>/duplicate", methods=["POST"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="DUPLICATE_FORM_TEMPLATE", target="FormTemplate")
def duplicate_form_template( template_id):
    """
    Duplicate a form template.
    
    Request body:
    {
        "name": "new template name"
    }
    """
    try:
        data = request.get_json()
        new_name = data.get("name")
        
        if not new_name:
            return jsonify({"error": "New template name is required"}), 400
        
        template = FormTemplate.query.get(template_id)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        # Prepare data for creation
        template_data = {
            "name": new_name,
            "title": template.title + " (Copy)",
            "subtitle": template.subtitle,
            "description": template.description,
            "logoUrl": template.logo_url,
            "gridRows": template.grid_rows,
            "gridColumns": template.grid_columns,
            "fieldMapping": template.field_mapping,
            "inputFields": [f.to_dict() for f in template.input_fields],
            "outputFields": [f.to_dict() for f in template.output_fields],
        }
        
        return FormTemplateService.create_template(template_data, 24)
    
    except Exception as e:
        return jsonify({"error": f"Failed to duplicate template: {str(e)}"}), 500
