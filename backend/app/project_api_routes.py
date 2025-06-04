from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity # get_jwt_identity is used
from app import db
from app.project_models import Project
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # User and role constants
from app.auth_decorators import admin_required, consultant_or_admin_required, any_authenticated_user_required
from datetime import date

project_api_bp = Blueprint('project_api', __name__, url_prefix='/api/projects')

def parse_date(date_string):
    if not date_string: # Handles empty string or None
        return None
    try:
        return date.fromisoformat(date_string)
    except (ValueError, TypeError): # Catch TypeError if date_string is not string-like
        return None # Or raise a specific error to be caught by error handler

@project_api_bp.route('', methods=['POST'])
@consultant_or_admin_required
def create_project():
    data = request.get_json()
    current_user_jwt_id = get_jwt_identity() # Renamed for clarity, though it's an ID

    if not data or not data.get('name'):
        return jsonify({"msg": "Missing project name"}), 400

    new_project = Project(
        name=data['name'],
        description=data.get('description'),
        status=data.get('status', 'active'), # Default status
        start_date=parse_date(data.get('start_date')),
        end_date=parse_date(data.get('end_date')),
        owner_id=current_user_jwt_id, # Owner is the logged-in consultant or admin creating it
        priority=data.get('priority', 'Medium'),
        project_type=data.get('project_type')
    )
    db.session.add(new_project)
    db.session.commit()

    project_data = {
        "id": new_project.id,
        "name": new_project.name,
        "description": new_project.description,
        "status": new_project.status,
        "start_date": new_project.start_date.isoformat() if new_project.start_date else None,
        "end_date": new_project.end_date.isoformat() if new_project.end_date else None,
        "owner_id": new_project.owner_id,
        "priority": new_project.priority,
        "project_type": new_project.project_type
    }
    return jsonify(project_data), 201

@project_api_bp.route('', methods=['GET'])
@any_authenticated_user_required
def get_projects():
    current_user_jwt_id = get_jwt_identity()
    user = User.query.get(current_user_jwt_id)

    if not user:
        return jsonify({"msg": "Authenticated user not found in database"}), 404

    projects_query = []
    if user.role == ADMIN:
        projects_query = Project.query.all()
    elif user.role == CONSULTANT:
        projects_query = Project.query.filter_by(owner_id=user.id).all()
    elif user.role == READ_ONLY:
        # For now, Read-Only users see no projects unless explicitly granted via a future grant system.
        projects_query = []
    else: # Should not happen if roles are well-defined
        projects_query = []

    projects_data = []
    for p in projects_query: # Iterate over the result of the query
        projects_data.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "start_date": p.start_date.isoformat() if p.start_date else None,
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "owner_id": p.owner_id,
            "priority": p.priority,
            "project_type": p.project_type
        })
    return jsonify(projects_data), 200

@project_api_bp.route('/<int:project_id>', methods=['GET'])
@any_authenticated_user_required
def get_project(project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({"msg": "Project not found"}), 404

    current_user_jwt_id = get_jwt_identity()
    user = User.query.get(current_user_jwt_id)

    if not user:
        return jsonify({"msg": "Authenticated user not found in database"}), 404

    if user.role == ADMIN:
        pass # Admin can access any project
    elif user.role == CONSULTANT:
        if project.owner_id != user.id:
            return jsonify({"msg": "Unauthorized: Consultant can only access their own projects"}), 403
    elif user.role == READ_ONLY:
        # TODO: Implement grant-based access check here.
        # For now, Read-Only cannot get project by ID unless a grant system is in place.
        # This could also be interpreted as: if they are not the owner (which they wouldn't be if role is strictly RO from start)
        # and no grant, then deny.
        return jsonify({"msg": "Unauthorized: Access to this project requires specific grants for Read-Only role"}), 403
    else: # Should not happen for well-defined roles
         return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        "owner_id": project.owner_id,
        "priority": project.priority,
        "project_type": project.project_type
    }
    return jsonify(project_data), 200

@project_api_bp.route('/<int:project_id>', methods=['PUT'])
@consultant_or_admin_required
def update_project(project_id):
    data = request.get_json()
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    current_user_jwt_id = get_jwt_identity()
    user = User.query.get(current_user_jwt_id)

    if not user: # Should ideally be caught by @jwt_required and user lookup in decorator
        return jsonify({"msg": "Authenticated user not found"}), 404

    if user.role == CONSULTANT and project.owner_id != user.id:
        return jsonify({"msg": "Unauthorized: Consultant can only update their own projects"}), 403
    # Admin can update any project (implicit from decorator & no further checks for admin role here)

    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.status = data.get('status', project.status)

    if 'priority' in data:
        project.priority = data.get('priority')
    if 'project_type' in data:
        project.project_type = data.get('project_type')

    # Allow clearing dates by passing an empty string or explicit null handled by parse_date
    if 'start_date' in data: # Check if key exists to allow setting to None
        project.start_date = parse_date(data.get('start_date'))
    if 'end_date' in data: # Check if key exists
        project.end_date = parse_date(data.get('end_date'))

    db.session.commit()

    updated_project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        "owner_id": project.owner_id,
        "priority": project.priority,
        "project_type": project.project_type
    }
    return jsonify(updated_project_data), 200

@project_api_bp.route('/<int:project_id>', methods=['DELETE'])
@admin_required # Only admins can delete projects
def delete_project(project_id):
    # current_user_id = get_jwt_identity() # Not strictly needed due to @admin_required
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    # No need to check ownership, admin can delete any.
    # If there were other roles that could delete specific projects,
    # more logic would be needed here after fetching the user object.

    db.session.delete(project)
    db.session.commit()
    return jsonify({"msg": "Project deleted successfully"}), 200
