import os # Added import os
import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity # get_jwt_identity is used
from werkzeug.utils import secure_filename
from app import db
from app.project_models import Project, ProjectTask, Evidence # Project and ProjectTask are used
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # User and role constants
from app.auth_decorators import admin_required, consultant_or_admin_required, any_authenticated_user_required # Auth decorators
from app.services.storage_service import LocalStorageService

evidence_api_bp = Blueprint('evidence_api', __name__, url_prefix='/api')

def is_allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())

@evidence_api_bp.route('/tasks/<int:task_id>/evidence', methods=['POST'])
@consultant_or_admin_required # Consultants or Admins can add evidence
def add_evidence_to_task(task_id):
    data = request.form.to_dict() # Get metadata from form fields
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404
    if not acting_user: # Should be caught by decorator
         return jsonify({"msg": "Authenticated user not found"}), 401

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found"}), 500

    if acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only add evidence to tasks in their own projects"}), 403
    # Admin access is implicitly allowed by the decorator.

    # File handling logic starts here
    if 'file' not in request.files:
        return jsonify({"msg": "No file part in the request"}), 400

    file_storage = request.files['file']
    if not file_storage or not file_storage.filename:
        return jsonify({"msg": "No file selected or filename is empty"}), 400

    if not is_allowed_file(file_storage.filename):
        allowed_ext_list = list(current_app.config.get('ALLOWED_EXTENSIONS', []))
        return jsonify({"msg": f"File type not allowed. Allowed: {', '.join(allowed_ext_list)}"}), 400

    storage_service = LocalStorageService()

    # Sanitize original filename before storing it in the DB
    original_safe_filename = secure_filename(file_storage.filename)

    # Define a subfolder structure
    subfolder = os.path.join("projects", str(project.id), "tasks", str(task.id))

    filename_prefix = data.get('tool_type', 'evidence') if data.get('tool_type') else 'evidence'

    relative_file_path = storage_service.save(
        file_storage,
        subfolder=subfolder,
        desired_filename_prefix=filename_prefix
    )

    if not relative_file_path:
        return jsonify({"msg": "Could not save file. Check server logs."}), 500

    new_evidence = Evidence(
        project_task_id=task_id,
        uploaded_by_id=current_user_jwt_id, # Use the ID of the authenticated user
        file_name=original_safe_filename,
        file_path=relative_file_path,
        storage_identifier=relative_file_path,
        tool_type=data.get('tool_type'),
        notes=data.get('notes'),
        mime_type=file_storage.mimetype
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
        "upload_date": new_evidence.upload_date.isoformat(),
        "mime_type": new_evidence.mime_type,
        "verified": new_evidence.verified
    }
    return jsonify(evidence_data), 201

@evidence_api_bp.route('/tasks/<int:task_id>/evidence', methods=['GET'])
@any_authenticated_user_required
def get_task_evidence(task_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found"}), 500

    if acting_user.role == ADMIN:
        pass # Admin can view evidence for any task
    elif acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only view evidence for tasks in their own projects"}), 403
    elif acting_user.role == READ_ONLY:
        # TODO: Implement grant-based access for Read-Only users
        if project.owner_id != acting_user.id:
             return jsonify({"msg": "Read-Only access to evidence requires specific project grant"}), 403
    else: # Should not happen
        return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    evidences = Evidence.query.filter_by(project_task_id=task_id).all()
    evidences_data = [{
        "id": e.id, "project_task_id": e.project_task_id, "uploaded_by_id": e.uploaded_by_id,
        "file_name": e.file_name, "file_path": e.file_path, "storage_identifier": e.storage_identifier,
        "tool_type": e.tool_type, "notes": e.notes, "upload_date": e.upload_date.isoformat(),
        "mime_type": e.mime_type, "verified": e.verified
    } for e in evidences]
    return jsonify(evidences_data), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>', methods=['GET'])
@any_authenticated_user_required
def get_evidence_detail(evidence_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
        return jsonify({"msg": "Associated task not found"}), 500
    project = db.session.get(Project, task.project_id)
    if not project:
        return jsonify({"msg": "Associated project not found"}), 500

    if acting_user.role == ADMIN:
        pass # Admin can view any evidence
    elif acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only view this evidence if it belongs to their project"}), 403
    elif acting_user.role == READ_ONLY:
        # TODO: Grant-based access
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Read-Only access to this evidence requires specific project grant"}), 403
    else: # Should not happen
        return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    evidence_data = {
        "id": evidence.id, "project_task_id": evidence.project_task_id, "uploaded_by_id": evidence.uploaded_by_id,
        "file_name": evidence.file_name, "file_path": evidence.file_path, "storage_identifier": evidence.storage_identifier,
        "tool_type": evidence.tool_type, "notes": evidence.notes, "upload_date": evidence.upload_date.isoformat(),
        "mime_type": evidence.mime_type, "verified": evidence.verified
    }
    return jsonify(evidence_data), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>', methods=['DELETE'])
@consultant_or_admin_required # Only Admin or Consultant (on own project) can delete
def delete_evidence(evidence_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
         return jsonify({"msg": "Associated task not found"}), 500

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found"}), 500

    if acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id: # and evidence.uploaded_by_id != acting_user.id: (Removed uploader check based on prompt focus)
            return jsonify({"msg": "Consultant can only delete evidence in their own projects"}), 403
    # Admin can delete any (implicit from decorator)

    storage_service = LocalStorageService()
    if evidence.file_path: # Or storage_identifier
        if not storage_service.delete(evidence.file_path):
            # Log the error but proceed to delete metadata, or decide if this is a hard fail
            current_app.logger.warning(f"Failed to delete file {evidence.file_path} from storage for evidence ID {evidence.id}. Metadata will still be deleted.")
            # Depending on policy, you might choose to return an error here:
            # return jsonify({"msg": "Failed to delete file from storage. Metadata not deleted."}), 500


    db.session.delete(evidence)
    db.session.commit()
    return jsonify({"msg": "Evidence deleted successfully"}), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>', methods=['PUT'])
@consultant_or_admin_required # Only Admin or Consultant (on own project) can update
def update_evidence_metadata(evidence_id):
    data = request.get_json()
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
        return jsonify({"msg": "Associated task not found"}), 500

    project = db.session.get(Project, task.project_id)
    if not project:
        return jsonify({"msg": "Associated project not found"}), 500

    if acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id: # and evidence.uploaded_by_id != acting_user.id: (Removed uploader check for now)
            return jsonify({"msg": "Consultant can only update evidence in their own projects"}), 403
    # Admin can update any (implicit from decorator)

    if 'notes' in data:
        evidence.notes = data.get('notes')
    if 'verified' in data:
        evidence.verified = bool(data.get('verified')) # Ensure boolean

    db.session.commit()

    updated_evidence_data = {
        "id": evidence.id,
        "project_task_id": evidence.project_task_id,
        "uploaded_by_id": evidence.uploaded_by_id,
        "file_name": evidence.file_name,
        "file_path": evidence.file_path,
        "storage_identifier": evidence.storage_identifier,
        "tool_type": evidence.tool_type,
        "notes": evidence.notes,
        "upload_date": evidence.upload_date.isoformat(),
        "mime_type": evidence.mime_type,
        "verified": evidence.verified
    }
    return jsonify(updated_evidence_data), 200

@evidence_api_bp.route('/evidence/<int:evidence_id>/download', methods=['GET'])
@any_authenticated_user_required # Similar to get_evidence_detail for view permissions
def download_evidence_file(evidence_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    evidence = db.session.get(Evidence, evidence_id)

    if not evidence:
        return jsonify({"msg": "Evidence not found"}), 404
    if not evidence.file_path: # Check if there is a file to download
        return jsonify({"msg": "No file associated with this evidence record"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    task = db.session.get(ProjectTask, evidence.project_task_id)
    if not task:
        current_app.logger.error(f"Consistency issue: Task ID {evidence.project_task_id} not found for evidence ID {evidence.id}")
        return jsonify({"msg": "Associated task not found"}), 500

    project = db.session.get(Project, task.project_id)
    if not project:
        current_app.logger.error(f"Consistency issue: Project ID {task.project_id} not found for task ID {task.id}")
        return jsonify({"msg": "Associated project not found"}), 500

    # Permission check based on role and project ownership (or grant system for RO)
    if acting_user.role == ADMIN:
        pass # Admin can download any evidence file
    elif acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only download evidence from their own projects"}), 403
    elif acting_user.role == READ_ONLY:
        # TODO: Grant-based access
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Read-Only access to download evidence requires specific project grant"}), 403
    else: # Should not happen
        return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    storage_service = LocalStorageService()
    upload_dir_abs = current_app.config.get('UPLOAD_FOLDER')

    if not upload_dir_abs:
        current_app.logger.error("UPLOAD_FOLDER is not configured, cannot download file.")
        return jsonify({"msg": "File download service not configured."}), 500

    # Use storage_service.get_full_path to verify the path is safe and file exists physically
    # This method already joins upload_dir_abs with evidence.file_path and checks for traversal
    full_physical_path = storage_service.get_full_path(evidence.file_path)

    if not full_physical_path or not os.path.exists(full_physical_path) or not os.path.isfile(full_physical_path):
        current_app.logger.warning(f"File for evidence {evidence.id} not found at physical path: {full_physical_path} (logical path: {evidence.file_path})")
        return jsonify({"msg": "File not found on server"}), 404

    try:
        # send_from_directory needs directory and the filename/path relative to that directory
        # evidence.file_path is already relative to UPLOAD_FOLDER
        return send_from_directory(
            directory=upload_dir_abs,
            path=evidence.file_path,
            as_attachment=True,
            download_name=evidence.file_name # Use original (sanitized) name for download
        )
    except FileNotFoundError:
        current_app.logger.error(f"send_from_directory FileNotFoundError: dir='{upload_dir_abs}', path='{evidence.file_path}'")
        return jsonify({"msg": "File not found during send operation"}), 404
    except Exception as e:
        current_app.logger.error(f"Error sending file for evidence {evidence.id}: {e}", exc_info=True)
        return jsonify({"msg": "Error sending file"}), 500
