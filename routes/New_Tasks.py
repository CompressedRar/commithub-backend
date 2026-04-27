from flask import Blueprint, request, jsonify
from models.FormTemplate import TaskResponse
from services.FormSubmissionService import FormSubmissionService
from utils.decorators import log_action, token_required

# Blueprint for Tasks
tasks_bp = Blueprint("btasks", __name__, url_prefix="/api/v1/btasks")

@tasks_bp.route("", methods=["POST"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="CREATE_TASK", target="Task")
def create_task():
    """
    Create a new task (Admin defines task using template)

    Request body:
    {
        "template_id": int,
        "title": string,
        "description": string,
        "values": {
            "field_id": value
        }
    }
    """
    try:
        data = request.get_json()
        print(f"Received task creation request: {data}")

        template_id = data.get("template_id")
        if not template_id:
            return jsonify({"error": "template_id is required"}), 400

        return FormSubmissionService.create_task(
            template_id=template_id,
            created_by=24,  # replace with current user from token
            data=data,
            category_id=data.get("category_id")  # optional category assignment
        )
    except Exception as e:
        print(f"Error creating task: {e}")
        return jsonify({"error": str(e)}), 500

@tasks_bp.route("/template/<int:template_id>", methods=["GET"])
@token_required()
def get_tasks(template_id):
    """
    Get all tasks for a template
    """
    return FormSubmissionService.get_tasks(template_id)


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@token_required()
def get_task(task_id):
    """
    Get a specific task
    """
    return FormSubmissionService.get_task(task_id)

@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="UPDATE_TASK", target="Task")
def update_task(task_id):
    """
    Update a task

    Request body:
    {
        "title": string (optional),
        "description": string (optional),
        "values": {
            "field_id": value
        }
    }
    """
    data = request.get_json()

    return FormSubmissionService.update_task(task_id, data)


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@token_required(allowed_roles=["administrator", "head"])
@log_action(action="DELETE_TASK", target="Task")
def delete_task(task_id):
    """
    Delete a task
    """
    return FormSubmissionService.delete_task(task_id)

@tasks_bp.route("/<int:task_id>/submit", methods=["POST"])
@token_required()
@log_action(action="SUBMIT_TASK_RESPONSE", target="TaskResponse")
def submit_task(task_id):
    """
    Submit user response to a task

    Request body:
    {
        "values": {
            "field_id": value
        }
    }
    """
    data = request.get_json()

    payload = {
        "user_id": 24,  # replace with current user
        "task_id": task_id,
        "values": data.get("values", {})
    }

    return FormSubmissionService.create_task_submission(payload)

@tasks_bp.route("/<int:task_id>/responses", methods=["GET"])
@token_required(allowed_roles=["administrator", "head"])
def get_task_responses(task_id):
    """
    Get all responses for a task
    """
    return FormSubmissionService.get_task_responses(task_id)

@tasks_bp.route("/user/<int:user_id>", methods=["GET"])
@token_required()
def get_user_task_responses(user_id):
    """
    Get all task responses of a user
    """
    return FormSubmissionService.get_user_task_responses(user_id)



@staticmethod
def get_task_responses(task_id):
    responses = TaskResponse.query.filter_by(task_id=task_id).all()
    return jsonify([r.to_dict() for r in responses]), 200


@staticmethod
def get_user_task_responses(user_id):
    responses = TaskResponse.query.filter_by(submitted_by=user_id).all()
    return jsonify([r.to_dict() for r in responses]), 200


