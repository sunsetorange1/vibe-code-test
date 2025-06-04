# backend/app/user_api_routes.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import User # Assuming User model is in app/models.py
from app import db # For potential logging or direct db access if needed beyond User.query

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/users')

@user_api_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    try:
        users = User.query.all()
        # Ensure password hashes are not included in the response
        users_data = [{"id": u.id, "username": u.username, "email": u.email} for u in users]
        return jsonify(users_data), 200
    except Exception as e:
        # In a real app, you'd use current_app.logger.error(f"Failed to retrieve users: {e}")
        # For now, just returning a generic error
        return jsonify({"msg": "Failed to retrieve users", "error": str(e)}), 500
