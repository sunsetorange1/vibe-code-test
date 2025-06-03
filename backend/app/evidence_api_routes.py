from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.project_models import Project, ProjectTask, Evidence
from app.models import User # For type hinting or direct use if necessary

evidence_api_bp = Blueprint('evidence_api', __name__, url_prefix='/api')

@evidence_api_bp.route('/tasks/<int:task_id>/evidence', methods=['POST'])
@jwt_required()
def add_evidence_to_task(task_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    project = db.session.get(Project, task.project_id)
    if not project: # Should not happen if DB is consistent
         return jsonify({"msg": "Associated project not found, cannot determine permissions"}), 500

    # Permission: Project owner or task assignee can add evidence
    if project.owner_id != current_user_id and task.assigned_to_id != current_user_id:
        return jsonify({"msg": "Unauthorized to add evidence to this task"}), 403

    if not data or not data.get('file_name'):
        return jsonify({"msg": "Missing evidence file_name"}), 400

    new_evidence = Evidence(
        project_task_id=task_id,
        uploaded_by_id=current_user_id,
        file_name=data['file_name'],
        file_path=data.get('file_path'),
        storage_identifier=data.get('storage_identifier'),
        tool_type=data.get('tool_type'),
        notes=data.get('notes')
    )
    db.session.add(new_evidence)
    db.session.commit()

    evidence_data = {
        "id": new_evidence.id,
        "project_task_id": new_evidence.project_task_id,
        "uploaded_by_id": new_evidence.uploaded_by_id,
        "file_name": new_evidence.file_name,
        "file_path": new_evidence.file_path,
        "storage_identifier": new_evidence.storage_identifier,
        "tool_type": new_evidence.tool_type,
        "notes": new_evidence.notes,
        "upload_date": new_evidence.upload_date.isoformat()
    }
    return jsonify(evidence_data), 201

@evidence_api_bp.route('/tasks/<int:task_id>/evidence', methods=['GET'])
@jwt_required()
def get_task_evidence(task_id):
    current_user_id = get_jwt_identity()
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found"}), 500

    if project.owner_id != current_user_id and task.assigned_to_id != current_user_id:
        return jsonify({"msg": "Unauthorized to view evidence for this task"}), 403

    evidences = Evidence.query.filter_by(project_task_id=task_id).all()
    evidences_data = [{
        "id": e.id, "project_task_id": e.project_task_id, "uploaded_by_id": e.uploaded_by_id,
        "file_name": e.file_name, "file_path": e.file_path, "storage_identifier": e.storage_identifier,
        "tool_type": e.tool_type, "notes": e.notes, "upload_date": e.upload_date.isoformat()
    } for e in evidences]
    return jsonify(evidences_data), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>', methods=['GET'])
@jwt_required()
def get_evidence_detail(evidence_id):
    current_user_id = get_jwt_identity()
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
        return jsonify({"msg": "Associated task not found"}), 500

    project = db.session.get(Project, task.project_id)
    if not project:
        return jsonify({"msg": "Associated project not found"}), 500

    if (project.owner_id != current_user_id and
            task.assigned_to_id != current_user_id and
            evidence.uploaded_by_id != current_user_id):
        return jsonify({"msg": "Unauthorized to view this evidence"}), 403

    evidence_data = {
        "id": evidence.id, "project_task_id": evidence.project_task_id, "uploaded_by_id": evidence.uploaded_by_id,
        "file_name": evidence.file_name, "file_path": evidence.file_path, "storage_identifier": evidence.storage_identifier,
        "tool_type": evidence.tool_type, "notes": evidence.notes, "upload_date": evidence.upload_date.isoformat()
    }
    return jsonify(evidence_data), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>', methods=['DELETE'])
@jwt_required()
def delete_evidence(evidence_id):
    current_user_id = get_jwt_identity()
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
         return jsonify({"msg": "Associated task not found, cannot determine permissions"}), 500

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found, cannot determine permissions"}), 500

    if project.owner_id != current_user_id and evidence.uploaded_by_id != current_user_id:
        return jsonify({"msg": "Unauthorized to delete this evidence"}), 403

    # Note: Actual file deletion from storage is not handled here.
    # e.g., os.remove(evidence.file_path) or delete_from_cloud_storage(evidence.storage_identifier)

    db.session.delete(evidence)
    db.session.commit()
    return jsonify({"msg": "Evidence deleted successfully"}), 200
