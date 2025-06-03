import json
from app.project_models import Evidence, ProjectTask, User, Project
from app import db

def test_add_evidence_to_task_by_owner(client, auth_user_and_headers, sample_project_task):
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    sample_project_task.assigned_to_id = None
    db.session.commit()

    payload = {"file_name": "owner_scan_output.xml", "tool_type": "Nessus Scan"}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == payload['file_name']
    assert data['uploaded_by_id'] == owner.id

    evidence = db.session.get(Evidence, data['id'])
    assert evidence is not None
    assert evidence.project_task_id == sample_project_task.id

def test_add_evidence_to_task_by_assignee(client, auth_user_and_headers, sample_project_task, another_user_data):
    assignee, headers = auth_user_and_headers # 'assignee' is project_owner_user from conftest
    sample_project_task.assigned_to_id = assignee.id

    project = db.session.get(Project, sample_project_task.project_id)
    # Ensure project owner is different from assignee for this test
    if project.owner_id == assignee.id:
        other_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not other_owner:
            other_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            other_owner.set_password(another_user_data["password"])
            db.session.add(other_owner)
            db.session.commit()
        project.owner_id = other_owner.id
    db.session.commit()

    payload = {"file_name": "assignee_screenshot.png", "tool_type": "Manual Screenshot"}
    rv = client.post(f'/api/tasks/{sample_project_task.id}/evidence', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == payload['file_name']
    assert data['uploaded_by_id'] == assignee.id

def test_get_task_evidence(client, auth_user_and_headers, sample_project_task):
    viewer, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = viewer.id # Ensure current user is owner for permission to view
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=viewer.id, file_name="test_evidence_list.txt")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/tasks/{sample_project_task.id}/evidence', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(e['id'] == evidence.id for e in data)

def test_get_specific_evidence_detail_by_uploader(client, auth_user_and_headers, sample_project_task, another_user_data):
    uploader, headers = auth_user_and_headers # This is our current user, who will be the uploader

    # Setup: Ensure project owner and task assignee are DIFFERENT from the uploader
    project = db.session.get(Project, sample_project_task.project_id)

    # Create a distinct owner if current uploader is the project owner
    if project.owner_id == uploader.id:
        distinct_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not distinct_owner:
            distinct_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            distinct_owner.set_password(another_user_data["password"]) # Ensure password for potential future use
            db.session.add(distinct_owner)
            db.session.commit()
        project.owner_id = distinct_owner.id

    # Ensure task is not assigned or assigned to someone else (not uploader)
    if sample_project_task.assigned_to_id == uploader.id:
        sample_project_task.assigned_to_id = None # Or assign to distinct_owner if they exist

    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="detail_evidence_test.txt")
    db.session.add(evidence)
    db.session.commit()

    rv = client.get(f'/api/evidence/{evidence.id}', headers=headers) # Uploader should be able to get it
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['file_name'] == "detail_evidence_test.txt"
    assert data['id'] == evidence.id

def test_delete_evidence_uploader(client, auth_user_and_headers, sample_project_task, another_user_data):
    uploader, headers = auth_user_and_headers

    project = db.session.get(Project, sample_project_task.project_id)
    # Ensure uploader is not project owner for this specific test logic
    if project.owner_id == uploader.id:
        distinct_owner = User.query.filter_by(email=another_user_data["email"]).first()
        if not distinct_owner:
            distinct_owner = User(username=another_user_data["username"], email=another_user_data["email"])
            distinct_owner.set_password(another_user_data["password"])
            db.session.add(distinct_owner)
            db.session.commit()
        project.owner_id = distinct_owner.id

    sample_project_task.assigned_to_id = None # Ensure uploader is not assignee
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="to_delete_by_uploader.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    rv = client.delete(f'/api/evidence/{evidence_id}', headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    assert db.session.get(Evidence, evidence_id) is None

def test_delete_evidence_project_owner(client, auth_user_and_headers, sample_project_task, another_user_data):
    project_owner, headers = auth_user_and_headers

    uploader = User.query.filter_by(email=another_user_data['email']).first()
    if not uploader:
        uploader = User(username=another_user_data['username'], email=another_user_data['email'])
        uploader.set_password(another_user_data['password'])
        db.session.add(uploader)
        db.session.commit()
    assert project_owner.id != uploader.id # Ensure owner and uploader are different people

    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = project_owner.id
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="owner_can_delete_this.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    rv = client.delete(f'/api/evidence/{evidence_id}', headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    assert db.session.get(Evidence, evidence_id) is None

def test_delete_evidence_unauthorized(client, auth_user_and_headers, sample_project_task, another_user_data):
    project_owner_of_task, _ = auth_user_and_headers # This user owns the project via sample_project_task fixture chain

    # Uploader is 'another_user_data'
    uploader = User.query.filter_by(email=another_user_data['email']).first()
    if not uploader:
        uploader = User(username=another_user_data['username'], email=another_user_data['email'])
        uploader.set_password(another_user_data['password'])
        db.session.add(uploader)
        db.session.commit()

    # Ensure project_owner_of_task is the actual owner
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = project_owner_of_task.id
    sample_project_task.assigned_to_id = None # Ensure task not assigned to uploader or third party
    db.session.commit()

    evidence = Evidence(project_task_id=sample_project_task.id, uploaded_by_id=uploader.id, file_name="cannot_delete.txt")
    db.session.add(evidence)
    db.session.commit()
    evidence_id = evidence.id

    # Third user attempts delete
    third_user_payload = {"username": "thirdparty_deleter", "email": "third_deleter@example.com", "password": "password"}
    client.post('/auth/register', json=third_user_payload) # Register third_party
    login_rv = client.post('/auth/login', json={"username": third_user_payload['username'], "password": "password"})
    third_party_headers = {"Authorization": f"Bearer {login_rv.get_json()['access_token']}"}

    rv = client.delete(f'/api/evidence/{evidence_id}', headers=third_party_headers)
    assert rv.status_code == 403
    assert db.session.get(Evidence, evidence_id) is not None
