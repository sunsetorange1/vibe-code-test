from flask import request, jsonify, redirect, url_for, current_app, session as flask_session
from flask_jwt_extended import create_access_token
from flask_dance.contrib.azure import azure # The blueprint instance
from . import db
from .models import User
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

@auth_bp.route("/sso/azure/callback") # This is the route name we gave to redirect_to for flask-dance
def sso_azure_callback():
    # Check if Azure AD authentication was successful (Flask-Dance stores token in session)
    if not azure.authorized:
        # This can happen if the user denies consent or there's an OAuth error
        current_app.logger.warning("Azure AD authorization failed or was denied.")
        # Redirect to a frontend page indicating login failure
        # For now, let's return an error, frontend would handle this better
        return jsonify({"msg": "Azure AD authorization failed. Please try again."}), 401

    try:
        # Fetch user information from Microsoft Graph API using the token Flask-Dance obtained
        account_info_resp = azure.get("/v1.0/me?$select=id,displayName,mail,userPrincipalName,surname,givenName")
        account_info_resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        account_info = account_info_resp.json()

        azure_oid = account_info.get("id")
        email = account_info.get("mail") or account_info.get("userPrincipalName") # Fallback to UPN if mail is null

        if not azure_oid or not email:
            current_app.logger.error(f"Azure AD OID or email not found in Graph API response: {account_info}")
            return jsonify({"msg": "Could not retrieve essential user info from Microsoft. Please try again."}), 500

        # Try to find user by Azure OID
        user = User.query.filter_by(azure_oid=azure_oid).first()

        if not user:
            # If no user with this OID, try to find by email (in case they registered locally before)
            user = User.query.filter_by(email=email).first()
            if user:
                # User exists with this email, link their account to Azure OID
                user.azure_oid = azure_oid
                current_app.logger.info(f"Linking existing user {email} with Azure OID {azure_oid}")
            else:
                # New user: Create one
                username_from_sso = account_info.get("displayName") or email.split('@')[0]

                counter = 0
                original_username = username_from_sso
                while User.query.filter_by(username=username_from_sso).first():
                    counter += 1
                    username_from_sso = f"{original_username}{counter}"
                    if counter > 10: # Safety break
                        current_app.logger.error(f"Could not generate unique username for SSO user {email}")
                        return jsonify({"msg": "Error creating user profile. Username conflict."}), 500

                user = User(
                    email=email,
                    username=username_from_sso,
                    azure_oid=azure_oid
                    # Password hash can be null as they use SSO
                )
                db.session.add(user)
                current_app.logger.info(f"Creating new user {email} from Azure AD SSO with OID {azure_oid}")

        db.session.commit()

        # User is now found or created. Issue our application's JWT.
        access_token = create_access_token(identity=user.id)

        # For a real app, redirect to a frontend page with the token
        # For now, just return the token
        return jsonify(access_token=access_token), 200

    except Exception as e:
        current_app.logger.error(f"Error in Azure AD callback: {str(e)}", exc_info=True)
        if "azure_oauth_token" in flask_session:
            del flask_session["azure_oauth_token"]
        return jsonify({"msg": f"An error occurred during SSO processing: {str(e)}"}), 500
