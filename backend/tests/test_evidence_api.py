import os
import uuid # For mocking save return value
from unittest.mock import patch, MagicMock
import pytest # For parametrize
from flask import current_app
from werkzeug.datastructures import FileStorage # For type hint and direct creation
from io import BytesIO
from app.services.storage_service import LocalStorageService # Import the service

from app.project_models import Evidence, ProjectTask, User, Project
from app import db

def test_add_evidence_to_task_by_owner(client, auth_user_and_headers, sample_project_task):
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    sample_project_task.assigned_to_id = None
    db.session.commit()

    file_content = b"owner uploaded content"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename="owner_evidence.txt", content_type="text/plain")

    form_data = {
        'tool_type': 'OwnerTool',
        'notes': 'Owner uploaded this evidence.',
        'file': mock_fs
    }

    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                     data=form_data, headers=headers, content_type='multipart/form-data')

    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "owner_evidence.txt"
    assert data['uploaded_by_id'] == owner.id
    assert data['tool_type'] == 'OwnerTool'

    evidence = db.session.get(Evidence, data['id'])
    assert evidence is not None
    assert evidence.project_task_id == sample_project_task.id
    assert evidence.file_path is not None

def test_add_evidence_to_task_by_assignee(client, auth_user_and_headers, sample_project_task, another_user_data):
    assignee, headers = auth_user_and_headers
    sample_project_task.assigned_to_id = assignee.id

    project = db.session.get(Project, sample_project_task.project_id)
    if project.owner_id == assignee.id:
        other_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not other_owner:
            other_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            other_owner.set_password(another_user_data["password"]) # Corrected
            db.session.add(other_owner); db.session.commit()
        project.owner_id = other_owner.id
    db.session.commit()

    mock_fs = FileStorage(stream=BytesIO(b"assignee data"), filename="assignee_evidence.log", content_type="text/plain")
    form_data = {'tool_type': 'AssigneeTool', 'notes': 'Assignee stuff', 'file': mock_fs}

    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                     data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "assignee_evidence.log"
    assert data['uploaded_by_id'] == assignee.id

def test_get_task_evidence(client, auth_user_and_headers, sample_project_task):
    uploader, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = uploader.id
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="test_evidence_list.txt", file_path="dummy/path.txt")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/tasks/{sample_project_task.id}/evidence', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(e['id'] == evidence.id for e in data)

def test_get_specific_evidence_detail_by_uploader(client, auth_user_and_headers, sample_project_task, another_user_data):
    uploader, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)

    if project.owner_id == uploader.id:
        distinct_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not distinct_owner:
            distinct_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            distinct_owner.set_password(another_user_data["password"]) # Corrected
            db.session.add(distinct_owner); db.session.commit()
        project.owner_id = distinct_owner.id
    if sample_project_task.assigned_to_id == uploader.id:
        sample_project_task.assigned_to_id = None
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="detail_evidence_test.txt", file_path="dummy/detail.txt")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/evidence/{evidence.id}', headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "detail_evidence_test.txt"

def test_delete_evidence_uploader(client, auth_user_and_headers, sample_project_task, another_user_data):
    uploader, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    if project.owner_id == uploader.id:
        distinct_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not distinct_owner:
            distinct_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            distinct_owner.set_password(another_user_data["password"]) # Corrected
            db.session.add(distinct_owner); db.session.commit()
        project.owner_id = distinct_owner.id

    sample_project_task.assigned_to_id = None
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="to_delete_by_uploader.txt", file_path="dummy/delete_me.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    with patch('app.services.storage_service.LocalStorageService.delete') as mock_storage_delete:
        mock_storage_delete.return_value = True
        rv = client.delete(f'/api/evidence/{evidence_id}', headers=headers)

    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    assert db.session.get(Evidence, evidence_id) is None
    mock_storage_delete.assert_called_once_with(evidence.file_path)

def test_delete_evidence_project_owner(client, auth_user_and_headers, sample_project_task, another_user_data):
    project_owner, headers = auth_user_and_headers

    uploader = User.query.filter_by(email=another_user_data['email']).first()
    if not uploader:
        uploader = User(username=another_user_data['username'], email=another_user_data['email'])
        uploader.set_password(another_user_data['password']) # Corrected
        db.session.add(uploader); db.session.commit()
    assert project_owner.id != uploader.id

    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = project_owner.id
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="owner_can_delete_this.txt", file_path="dummy/owner_del.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    with patch('app.services.storage_service.LocalStorageService.delete') as mock_storage_delete:
        mock_storage_delete.return_value = True
        rv = client.delete(f'/api/evidence/{evidence_id}', headers=headers)

    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    assert db.session.get(Evidence, evidence_id) is None
    mock_storage_delete.assert_called_once_with(evidence.file_path)

def test_delete_evidence_unauthorized(client, auth_user_and_headers, sample_project_task, another_user_data):
    project_owner_for_setup, _ = auth_user_and_headers

    uploader_email = another_user_data['email']
    uploader = User.query.filter_by(email=uploader_email).first()
    if not uploader:
        uploader = User(username=another_user_data['username'], email=uploader_email)
        uploader.set_password(another_user_data['password']) # Corrected
        db.session.add(uploader); db.session.commit()

    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = project_owner_for_setup.id
    sample_project_task.assigned_to_id = None
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="cannot_delete.txt", file_path="dummy/no_delete.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    third_user_payload = {"username": "thirdparty_deleter", "email": "third_deleter@example.com", "password": "password"}
    client.post('/auth/register', json=third_user_payload)
    login_rv = client.post('/auth/login', json={"username": third_user_payload['username'], "password": "password"})
    third_party_headers = {"Authorization": f"Bearer {login_rv.get_json()['access_token']}"}

    rv = client.delete(f'/api/evidence/{evidence_id}', headers=third_party_headers)
    assert rv.status_code == 403
    assert db.session.get(Evidence, evidence_id) is not None

# --- New tests for file operations ---

@pytest.mark.parametrize("mock_file_storage", [{"filename": "good_upload.txt", "content": b"text content"}], indirect=True)
def test_upload_evidence_file_success_with_mocked_service(client, auth_user_and_headers, sample_project_task, mock_file_storage): # Corrected fixture name
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    db.session.commit()

    form_data = {'tool_type': 'Manual', 'notes': 'A test upload', 'file': mock_file_storage}

    with patch('app.evidence_api_routes.LocalStorageService.save') as mock_save:
        unique_id = uuid.uuid4().hex
        expected_filename_on_disk = f"Manual_{unique_id}.txt" # Assuming .txt from mock_file_storage
        expected_relative_path = os.path.join("projects", str(project.id), "tasks", str(sample_project_task.id), expected_filename_on_disk)
        mock_save.return_value = expected_relative_path

        rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                        data=form_data, headers=headers, content_type='multipart/form-data')

    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "good_upload.txt"
    assert data['file_path'] == expected_relative_path
    mock_save.assert_called_once()
    args_passed, kwargs_passed = mock_save.call_args
    assert kwargs_passed.get('desired_filename_prefix') == 'Manual'
    assert isinstance(args_passed[0], FileStorage)
    assert args_passed[0].filename == "good_upload.txt"

@pytest.mark.parametrize("mock_file_storage", [{"filename": "bad_extension.exe", "content": b"binary"}], indirect=True)
def test_upload_evidence_file_type_not_allowed(client, auth_user_and_headers, sample_project_task, mock_file_storage): # Corrected fixture name
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    db.session.commit()

    form_data = {'file': mock_file_storage, 'tool_type': 'Exploit'}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                    data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 400
    assert "File type not allowed" in rv.get_json()['msg']

def test_upload_evidence_file_too_large(client, auth_user_and_headers, sample_project_task): # Corrected fixture name
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    db.session.commit()

    large_content = b"A" * (current_app.config['MAX_CONTENT_LENGTH'] + 1)
    large_file = FileStorage(stream=BytesIO(large_content), filename="large_file.txt")

    form_data = {'file': large_file}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence',
                    data=form_data, headers=headers, content_type='multipart/form-data')
    assert rv.status_code == 413

def test_download_evidence_file(client, auth_user_and_headers, sample_project_task): # Corrected fixture name, removed db
    viewer, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = viewer.id
    db.session.commit()

    file_content = b"Actual downloadable content."
    original_filename = "download_test.txt"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename=original_filename)

    storage_service = LocalStorageService()
    subfolder = os.path.join("projects", str(project.id), "tasks", str(sample_project_task.id))
    relative_path = storage_service.save(mock_fs, subfolder=subfolder, desired_filename_prefix="download")
    assert relative_path is not None

    evidence_record = Evidence(
        project_task_id=sample_project_task.id, uploaded_by_id=viewer.id,
        file_name=original_filename, file_path=relative_path
    )
    db.session.add(evidence_record)
    db.session.commit()

    rv = client.get(f'/api/evidence/{evidence_record.id}/download', headers=headers)

    assert rv.status_code == 200
    assert rv.data == file_content
    assert rv.headers.get("Content-Disposition") == f"attachment; filename={original_filename}" # Corrected: no quotes

def test_delete_evidence_with_actual_file_cleanup(client, auth_user_and_headers, sample_project_task, temp_upload_folder): # Corrected fixture name, removed db
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    db.session.commit()

    storage_service = LocalStorageService()
    file_content = b"Content to be deleted with record."
    original_filename = "delete_me_fully.txt"
    mock_fs = FileStorage(stream=BytesIO(file_content), filename=original_filename)
    subfolder = os.path.join("projects", str(project.id), "tasks", str(sample_project_task.id))
    relative_path = storage_service.save(mock_fs, subfolder=subfolder, desired_filename_prefix="delete_op")
    assert relative_path is not None

    full_physical_path = storage_service.get_full_path(relative_path)
    assert os.path.exists(full_physical_path)

    evidence_record = Evidence(
        project_task_id=sample_project_task.id, uploaded_by_id=owner.id,
        file_name=original_filename, file_path=relative_path
    )
    db.session.add(evidence_record)
    db.session.commit()
    evidence_id = evidence_record.id

    rv = client.delete(f'/api/evidence/{evidence_id}', headers=headers)

    assert rv.status_code == 200
    assert db.session.get(Evidence, evidence_id) is None
    assert not os.path.exists(full_physical_path)
