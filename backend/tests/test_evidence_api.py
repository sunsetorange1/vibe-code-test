import os
import uuid
from unittest.mock import patch
import pytest
from flask import current_app
from werkzeug.datastructures import FileStorage
from io import BytesIO
from app.services.storage_service import LocalStorageService
from app.project_models import Evidence, ProjectTask, User, Project
from app.models import ADMIN, CONSULTANT, READ_ONLY # For setting roles if needed
from app import db

# Test adding evidence by Consultant who owns the project
def test_add_evidence_to_task_by_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant_owner, headers = auth_consultant_user_and_headers
    # sample_project_task.project is owned by consultant_user via fixture default
    assert sample_project_task.project.owner_id == consultant_owner.id

    file_content = b"consultant uploaded content"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename="consultant_evidence.txt", content_type="text/plain")
    form_data = {'tool_type': 'ConsultantTool', 'notes': 'Consultant uploaded this.', 'file': mock_fs}

    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                     data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "consultant_evidence.txt"
    assert data['uploaded_by_id'] == consultant_owner.id
    assert data['mime_type'] == "text/plain"
    assert data['verified'] is False

# Test adding evidence by Admin to any project
def test_add_evidence_to_task_by_admin(client, auth_admin_user_and_headers, sample_project_task, admin_user):
    # sample_project_task is owned by consultant_user by default
    admin, headers = auth_admin_user_and_headers
    assert sample_project_task.project.owner_id != admin.id

    mock_fs = FileStorage(stream=BytesIO(b"admin content"), filename="admin_evidence.txt", content_type="text/plain")
    form_data = {'tool_type': 'AdminTool', 'notes': 'Admin uploaded this.', 'file': mock_fs}

    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                     data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['uploaded_by_id'] == admin.id

# Test READ_ONLY user cannot add evidence
def test_add_evidence_readonly_user_fails(client, auth_user_and_headers, sample_project_task):
    _, headers = auth_user_and_headers # auth_user_and_headers is READ_ONLY
    mock_fs = FileStorage(stream=BytesIO(b"ro content"), filename="ro_evidence.txt", content_type="text/plain")
    form_data = {'file': mock_fs}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', data=form_data, headers=headers)
    assert rv.status_code == 403

# Test getting evidence by Consultant owner
def test_get_task_evidence_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    Evidence.query.delete() # Clear previous evidence for cleaner assertion
    db.session.commit()
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_owner.id, file_name="evidence.txt", file_path="dummy.txt", mime_type="text/plain")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/tasks/{sample_project_task.id}/evidence', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) == 1
    assert data[0]['id'] == evidence.id

# Test getting evidence by Admin
def test_get_task_evidence_admin(client, auth_admin_user_and_headers, sample_project_task, consultant_user):
    admin, headers = auth_admin_user_and_headers
    # Evidence on consultant's project
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="evidence_for_admin.txt", file_path="dummy_admin.txt")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/tasks/{sample_project_task.id}/evidence', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert any(e['id'] == evidence.id for e in data)

# Test getting specific evidence by READ_ONLY user (fails as per new RBAC)
def test_get_specific_evidence_detail_readonly_fails(client, auth_user_and_headers, sample_project_task, consultant_user):
    _, headers = auth_user_and_headers # READ_ONLY user
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="detail.txt", file_path="dummy_detail.txt")
    db.session.add(evidence)
    db.session.commit()
    rv = client.get(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 403

# Test delete by Consultant owner
def test_delete_evidence_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_owner.id, file_name="delete_me.txt", file_path="dummy_del.txt")
    db.session.add(evidence)
    db.session.commit()
    with patch('app.services.storage_service.LocalStorageService.delete', return_value=True) as mock_delete:
        rv = client.delete(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 200
    mock_delete.assert_called_once()

# Test delete by Admin
def test_delete_evidence_admin(client, auth_admin_user_and_headers, sample_project_task, consultant_user):
    admin, headers = auth_admin_user_and_headers
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="admin_delete.txt", file_path="dummy_admin_del.txt")
    db.session.add(evidence)
    db.session.commit()
    with patch('app.services.storage_service.LocalStorageService.delete', return_value=True) as mock_delete:
        rv = client.delete(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 200
    mock_delete.assert_called_once()

# Test delete by READ_ONLY (fails)
def test_delete_evidence_readonly_fails(client, auth_user_and_headers, sample_project_task, consultant_user):
    _, headers = auth_user_and_headers
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="ro_delete_fail.txt", file_path="dummy_ro_del_fail.txt")
    db.session.add(evidence)
    db.session.commit()
    rv = client.delete(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 403

# Test update by Consultant owner
def test_update_evidence_metadata_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_owner.id, file_name="update_me.txt", notes="Initial")
    db.session.add(evidence)
    db.session.commit()
    payload = {"notes": "Updated by consultant owner", "verified": True}
    rv = client.put(f'/api/evidence/{evidence.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['notes'] == payload['notes']
    assert data['verified'] == payload['verified']

# Test update by Admin
def test_update_evidence_metadata_admin(client, auth_admin_user_and_headers, sample_project_task, consultant_user):
    admin, headers = auth_admin_user_and_headers
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="admin_update.txt", notes="Initial")
    db.session.add(evidence)
    db.session.commit()
    payload = {"notes": "Updated by admin", "verified": True}
    rv = client.put(f'/api/evidence/{evidence.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['notes'] == payload['notes']

# Test update by READ_ONLY (fails)
def test_update_evidence_metadata_readonly_fails(client, auth_user_and_headers, sample_project_task, consultant_user):
    _, headers = auth_user_and_headers
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name="ro_update_fail.txt")
    db.session.add(evidence)
    db.session.commit()
    payload = {"notes": "Attempt by RO", "verified": True}
    rv = client.put(f'/api/evidence/{evidence.id}', json=payload, headers=headers)
    assert rv.status_code == 403

# File operations tests adapted for new RBAC
@pytest.mark.parametrize("mock_file_storage", [{"filename": "consultant_upload.txt", "content": b"c content", "content_type": "text/plain"}], indirect=True)
def test_upload_evidence_file_success_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task, mock_file_storage):
    consultant_owner, headers = auth_consultant_user_and_headers
    project = sample_project_task.project
    assert project.owner_id == consultant_owner.id
    form_data = {'tool_type': 'ConsultantTool', 'notes': 'Consultant upload', 'file': mock_file_storage}
    with patch('app.evidence_api_routes.LocalStorageService.save') as mock_save:
        mock_save.return_value = "mocked/path.txt"
        rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['file_name'] == mock_file_storage.filename
    assert data['mime_type'] == mock_file_storage.content_type

@pytest.mark.parametrize("mock_file_storage", [{"filename": "bad.exe", "content": b"binary", "content_type": "application/octet-stream"}], indirect=True)
def test_upload_evidence_file_type_not_allowed_by_consultant(client, auth_consultant_user_and_headers, sample_project_task, mock_file_storage):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    form_data = {'file': mock_file_storage}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', data=form_data, headers=headers)
    assert rv.status_code == 400 # File type check happens after role check

def test_upload_evidence_file_too_large_by_consultant(client, auth_consultant_user_and_headers, sample_project_task):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    large_content = b"A" * (current_app.config['MAX_CONTENT_LENGTH'] + 1)
    large_file = FileStorage(stream=BytesIO(large_content), filename="large.txt", content_type="text/plain")
    form_data = {'file': large_file}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', data=form_data, headers=headers)
    assert rv.status_code == 413 # Size check happens after role check

# Test download by Admin
def test_download_evidence_file_admin(client, auth_admin_user_and_headers, sample_project_task, consultant_user, temp_upload_folder):
    admin, headers = auth_admin_user_and_headers
    evidence_uploader = consultant_user
    file_content = b"Content for admin download."
    original_filename = "admin_download.txt"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename=original_filename, content_type="text/plain")
    storage_service = LocalStorageService()
    relative_path = storage_service.save(mock_fs, subfolder="test_subdir", desired_filename_prefix="admin_dl")
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=evidence_uploader.id, file_name=original_filename, file_path=relative_path, mime_type=mock_fs.mimetype)
    db.session.add(evidence); db.session.commit()
    rv = client.get(f'/api/evidence/{evidence.id}/download', headers=headers)
    assert rv.status_code == 200
    assert rv.data == file_content

# Test download by READ_ONLY (fails)
def test_download_evidence_file_readonly_fails(client, auth_user_and_headers, sample_project_task, consultant_user, temp_upload_folder):
    _, headers = auth_user_and_headers # READ_ONLY user
    evidence_uploader = consultant_user
    mock_fs = FileStorage(stream=BytesIO(b"content"), filename="ro_dl_fail.txt", content_type="text/plain")
    storage_service = LocalStorageService()
    relative_path = storage_service.save(mock_fs, subfolder="test_subdir", desired_filename_prefix="ro_dl_fail")
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=evidence_uploader.id, file_name=mock_fs.filename, file_path=relative_path, mime_type=mock_fs.mimetype)
    db.session.add(evidence); db.session.commit()
    rv = client.get(f'/api/evidence/{evidence.id}/download', headers=headers)
    assert rv.status_code == 403

# Test delete with file cleanup by Admin
def test_delete_evidence_by_admin_with_actual_file_cleanup(client, auth_admin_user_and_headers, sample_project_task, consultant_user, temp_upload_folder):
    admin, headers = auth_admin_user_and_headers
    storage_service = LocalStorageService()
    mock_fs = FileStorage(stream=BytesIO(b"delete this"), filename="admin_del_actual.txt", content_type="text/plain")
    relative_path = storage_service.save(mock_fs, subfolder="test_subdir_del", desired_filename_prefix="admin_del_op_actual")
    assert os.path.exists(storage_service.get_full_path(relative_path))
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_user.id, file_name=mock_fs.filename, file_path=relative_path, mime_type=mock_fs.mimetype)
    db.session.add(evidence); db.session.commit()
    rv = client.delete(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 200
    assert not os.path.exists(storage_service.get_full_path(relative_path))

# Test download by Consultant owner
def test_download_evidence_file_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task, temp_upload_folder):
    consultant_owner, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant_owner.id
    file_content = b"Consultant download content."
    original_filename = "consultant_download.txt"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename=original_filename, content_type="text/plain")
    storage_service = LocalStorageService()
    relative_path = storage_service.save(mock_fs, subfolder="test_subdir_consultant", desired_filename_prefix="consultant_dl")
    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=consultant_owner.id, file_name=original_filename, file_path=relative_path, mime_type=mock_fs.mimetype)
    db.session.add(evidence); db.session.commit()
    rv = client.get(f'/api/evidence/{evidence.id}/download', headers=headers)
    assert rv.status_code == 200
    assert rv.data == file_content
