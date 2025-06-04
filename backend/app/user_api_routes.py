# backend/app/user_api_routes.py
from flask import Blueprint, jsonify, current_app # Added current_app
# from flask_jwt_extended import jwt_required # Removed as role_required handles JWT verification
from app.models import User, ADMIN, CONSULTANT # Import User and role constants
from app.auth_decorators import role_required # Import the new decorator
# from app import db # db import not strictly needed for this specific route if only using User.query

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/users')

@user_api_bp.route('', methods=['GET'])
# @jwt_required() # Replaced by role_required
@role_required([ADMIN, CONSULTANT]) # Apply new role-based decorator
def get_users():
    try:
        users = User.query.all()
        # Ensure password hashes are not included in the response
        users_data = [{"id": u.id, "username": u.username, "email": u.email} for u in users]
        return jsonify(users_data), 200
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve users: {str(e)}")
        return jsonify({"msg": "Failed to retrieve users", "error": str(e)}), 500
