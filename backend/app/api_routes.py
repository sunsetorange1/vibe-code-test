from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User
from . import db # Import db instance
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_profile():
    current_user_id = get_jwt_identity() # This will be the user.id we stored in the token
    user = db.session.get(User, current_user_id) # Updated to use db.session.get()

    if not user:
        # This case should ideally not be reached if tokens are managed correctly
        # and refer to existing users. Could indicate a deleted user after token issuance.
        return jsonify({"msg": "User not found for the given token identity"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200
