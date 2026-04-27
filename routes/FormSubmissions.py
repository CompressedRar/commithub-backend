"""
Form Submission Routes
API endpoints for submitting forms and managing submissions.
"""

from flask import Blueprint, request, jsonify
from services.FormSubmissionService import FormSubmissionService
from utils.decorators import log_action, token_required

# Create blueprint
form_submissions_bp = Blueprint("form_submissions", __name__, url_prefix="/api/v1/form-submissions")


@form_submissions_bp.route("", methods=["POST"])
@token_required()
@log_action(action="CREATE_FORM_SUBMISSION", target="FormSubmission")
def create_form_submission():
    """
    Create a new form submission.
    
    Request body:
    {
        "template_id": int,
        "fieldValues": {
            "field_id": "value",
            ...
        },
        "isDraft": boolean (optional, default: false)
    }
    """
    data = request.get_json()
    template_id = data.get("template_id")
    field_values = data.get("fieldValues", {})
    is_draft = data.get("isDraft", False)
    
    if not template_id:
        return jsonify({"error": "template_id is required"}), 400
    
    return FormSubmissionService.create_submission(
        template_id,
        24,
        field_values,
        is_draft
    )


@form_submissions_bp.route("/<int:submission_id>", methods=["GET"])
@token_required()
def get_form_submission(submission_id):
    """Get a specific form submission by ID"""
    return FormSubmissionService.get_submission(submission_id)


@form_submissions_bp.route("/template/<int:template_id>", methods=["GET"])
@token_required(allowed_roles=["administrator", "head"])
def get_template_submissions(template_id):
    """
    Get all submissions for a specific template.
    
    Query parameters:
    - skip: Number of submissions to skip (default: 0)
    - limit: Number of submissions to return (default: 20)
    - includeDrafts: Include draft submissions (default: false)
    """
    skip = request.args.get("skip", default=0, type=int)
    limit = request.args.get("limit", default=20, type=int)
    include_drafts = request.args.get("includeDrafts", default="false").lower() == "true"
    
    return FormSubmissionService.get_template_submissions(template_id, skip, limit, include_drafts)


@form_submissions_bp.route("/user/<int:user_id>", methods=["GET"])
@token_required()
def get_user_submissions(user_id):
    """
    Get all submissions by a specific user.
    
    Query parameters:
    - templateId: Filter by template ID (optional)
    - skip: Number of submissions to skip (default: 0)
    - limit: Number of submissions to return (default: 20)
    """
    
    template_id = request.args.get("templateId", default=None, type=int)
    skip = request.args.get("skip", default=0, type=int)
    limit = request.args.get("limit", default=20, type=int)
    
    return FormSubmissionService.get_user_submissions(user_id, template_id, skip, limit)


@form_submissions_bp.route("/<int:submission_id>", methods=["PUT"])
@token_required()
@log_action(action="UPDATE_FORM_SUBMISSION", target="FormSubmission")
def update_form_submission(submission_id):
    """
    Update a form submission's field values.
    
    Request body:
    {
        "fieldValues": {
            "field_id": "new_value",
            ...
        },
        "isDraft": boolean (optional)
    }
    """
    data = request.get_json()
    field_values = data.get("fieldValues", {})
    is_draft = data.get("isDraft")
    
    return FormSubmissionService.update_submission(submission_id, field_values, is_draft)


@form_submissions_bp.route("/<int:submission_id>", methods=["DELETE"])
@token_required()
@log_action(action="DELETE_FORM_SUBMISSION", target="FormSubmission")
def delete_form_submission(submission_id):
    """Delete a form submission"""
    return FormSubmissionService.delete_submission(submission_id)


@form_submissions_bp.route("/template/<int:template_id>/stats", methods=["GET"])
@token_required(allowed_roles=["administrator", "head"])
def get_submission_stats(template_id):
    """
    Get submission statistics for a template.
    
    Returns:
    {
        "template_id": int,
        "total_submissions": int,
        "completed_submissions": int,
        "draft_submissions": int
    }
    """
    return FormSubmissionService.get_submission_stats(template_id)
