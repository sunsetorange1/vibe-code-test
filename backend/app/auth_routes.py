from flask import request, jsonify
from flask_jwt_extended import create_access_token # Added import
from . import db # From app/__init__.py
from .models import User # From app/models.py
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        return jsonify({"msg": "Unsupported Media Type: JSON expected"}), 415
    data = request.get_json()
    if not data: # This check might now be somewhat redundant if request.is_json is false, but good for empty JSON {}
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"msg": "Missing username, email, or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User created successfully", "user": {"id": user.id, "username": user.username, "email": user.email}}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Unsupported Media Type: JSON expected"}), 415
    data = request.get_json()
    if not data: # Similar redundancy check as above
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id) # Using user.id as identity
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401 # Unauthorized
