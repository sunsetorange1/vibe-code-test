# backend/app/auth_decorators.py
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # Import User and role constants

def role_required(required_roles):
    """
    Decorator to ensure the user has one of the required roles.
    `required_roles` should be a list of role strings (e.g., [ADMIN, CONSULTANT]).
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user:
                return jsonify(msg="User not found with provided token identity."), 404 # Should not happen if token is valid

            if user.role not in required_roles:
                return jsonify(msg=f"Access denied: User does not have one of the required roles ({', '.join(required_roles)}). Current role: {user.role}."), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Decorator to ensure the user has the ADMIN role."""
    @wraps(fn)
    @role_required([ADMIN]) # Use the more general role_required
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def consultant_or_admin_required(fn):
    """Decorator to ensure the user has either CONSULTANT or ADMIN role."""
    @wraps(fn)
    @role_required([CONSULTANT, ADMIN]) # Use the more general role_required
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)
    return wrapper

def any_authenticated_user_required(fn):
    """Decorator to ensure any authenticated user can access, regardless of specific role."""
    @wraps(fn)
    @role_required([ADMIN, CONSULTANT, READ_ONLY]) # All defined roles
    def wrapper(*args, **kwargs):
        # This effectively just checks if the JWT is valid and the user exists with any of the defined roles.
        # If a user could exist without a role or with a role not in USER_ROLES, this would need adjustment
        # or just rely on verify_jwt_in_request() and fetching the user.
        return fn(*args, **kwargs)
    return wrapper

# More granular checks can also be done inside the route handlers if needed,
# for example, checking if a consultant owns a specific resource.
# The decorators handle the "can this type of user generally access this action?" part.
