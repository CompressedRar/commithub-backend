from flask import Blueprint, jsonify, request
from app import db, limiter
from utils.decorators import log_action, token_required
from models.User import Profile, User
from services.User.users_service import Users

profiles = Blueprint("profiles", __name__, url_prefix="/api/v1/profiles")


# Profile CRUD
@profiles.route("/", methods=["GET"])
@token_required(allowed_roles=["administrator", "president"])
def list_profiles():
    """List all profiles with their users"""
    return Users.list_all_profiles()


@profiles.route("/<profile_id>", methods=["GET"])
@token_required(allowed_roles=["administrator", "president"])
def get_profile_detail(profile_id):
    """Get profile details with all linked users"""
    return Users.get_profile_with_users(profile_id)


@profiles.route("", methods=["POST"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="CREATE", target="PROFILE")
def create_profile():
    """Create a new profile"""
    print("creating profile")
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400
    return Users.create_profile(data)


@profiles.route("/<profile_id>", methods=["PATCH"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="UPDATE", target="PROFILE")
def update_profile_info(profile_id):
    """Update profile information"""
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400
    return Users.update_profile(profile_id, data)


@profiles.route("/<profile_id>", methods=["DELETE"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="DELETE", target="PROFILE")
def delete_profile(profile_id):
    """Delete a profile (and all associated users)"""
    return Users.delete_profile(profile_id)


# Users in Profile Management
@profiles.route("/<profile_id>/users", methods=["GET"])
@token_required(allowed_roles=["administrator", "president"])
def list_profile_users(profile_id):
    """List all users in a profile"""
    return Users.get_profile_users(profile_id)


@profiles.route("/<profile_id>/users", methods=["POST"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="CREATE", target="USER")
def create_user_in_profile(profile_id):
    """Create a new user in a profile"""
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400
    return Users.create_user_in_profile(profile_id, data)


@profiles.route("/<profile_id>/users/<user_id>", methods=["PATCH"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="UPDATE", target="USER")
def update_user_in_profile(profile_id, user_id):
    """Update a user in a profile"""
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400
    return Users.update_user_in_profile(profile_id, user_id, data)


@profiles.route("/<profile_id>/users/<user_id>", methods=["DELETE"])
@token_required(allowed_roles=["administrator", "president"])
@log_action(action="DELETE", target="USER")
def delete_user_from_profile(profile_id, user_id):
    """Delete a user from a profile"""
    return Users.delete_user_from_profile(profile_id, user_id)
