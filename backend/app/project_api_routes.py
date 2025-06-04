from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.project_models import Project
from app.models import User # For fetching project owner if needed for validation
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
@jwt_required()
def create_project():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    if not data or not data.get('name'):
        return jsonify({"msg": "Missing project name"}), 400

    new_project = Project(
        name=data['name'],
        description=data.get('description'),
        status=data.get('status', 'active'), # Default status
        start_date=parse_date(data.get('start_date')),
        end_date=parse_date(data.get('end_date')),
        owner_id=current_user_id,
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
@jwt_required()
def get_projects():
    current_user_id = get_jwt_identity()
    user_projects = Project.query.filter_by(owner_id=current_user_id).all()

    projects_data = []
    for p in user_projects:
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
@jwt_required()
def get_project(project_id):
    current_user_id = get_jwt_identity()
    # Use db.session.get for primary key lookup as recommended
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to access this project"}), 403

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
@jwt_required()
def update_project(project_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to update this project"}), 403

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
@jwt_required()
def delete_project(project_id):
    current_user_id = get_jwt_identity()
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404

    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to delete this project"}), 403

    db.session.delete(project)
    db.session.commit()
    return jsonify({"msg": "Project deleted successfully"}), 200
