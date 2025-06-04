import json
from app.project_models import Baseline, TaskDefinition
from app.models import User, ADMIN, CONSULTANT, READ_ONLY
from app import db

# Use auth_consultant_user_and_headers for actions requiring consultant/admin roles.
# sample_baseline and sample_task_definition fixtures are now created by consultant_user.

def test_create_baseline(client, auth_consultant_user_and_headers, consultant_user):
    # Renamed creator to consultant_creator for clarity
    consultant_creator, headers = auth_consultant_user_and_headers
    payload = {"name": "New Security Baseline Alpha by Consultant", "description": "Standard security checks Alpha"}
    rv = client.post('/api/baselines', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['name'] == payload['name']
    assert data['created_by_id'] == consultant_creator.id # consultant_user is aliased as consultant_creator

    baseline = db.session.get(Baseline, data['id'])
    assert baseline is not None

def test_create_baseline_duplicate_name(client, auth_consultant_user_and_headers, sample_baseline):
    # sample_baseline is created by consultant_user
    consultant_creator, headers = auth_consultant_user_and_headers
    assert sample_baseline.created_by_id == consultant_creator.id

    payload = {"name": sample_baseline.name, "description": "Attempting duplicate name"}
    rv = client.post('/api/baselines', json=payload, headers=headers)
    assert rv.status_code == 400 # Assuming endpoint prevents duplicate names
    assert "already exists" in rv.get_json()['msg']

# GET operations might be accessible by any authenticated user, depending on future RBAC on these routes.
# For now, using auth_consultant_user_and_headers to ensure the user has rights if routes become restricted.
# If GETs are public or for all roles, auth_user_and_headers (READ_ONLY) could also work if they can see these.
def test_get_baselines(client, auth_consultant_user_and_headers, sample_baseline):
    _, headers = auth_consultant_user_and_headers # Using consultant to ensure they can see their own.
    rv = client.get('/api/baselines', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(b['id'] == sample_baseline.id and b['name'] == sample_baseline.name for b in data)

def test_get_specific_baseline(client, auth_consultant_user_and_headers, sample_baseline, sample_task_definition):
    _, headers = auth_consultant_user_and_headers
    rv = client.get(f'/api/baselines/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == sample_baseline.name
    assert data['id'] == sample_baseline.id
    assert len(data['task_definitions']) >= 1
    assert any(td['id'] == sample_task_definition.id for td in data['task_definitions'])

def test_create_task_definition_for_baseline(client, auth_consultant_user_and_headers, sample_baseline):
    consultant_creator, headers = auth_consultant_user_and_headers
    assert sample_baseline.created_by_id == consultant_creator.id

    payload = {"title": "New Task Def for Baseline B by Consultant", "category": "Audit"}
    rv = client.post(f'/api/baselines/{sample_baseline.id}/task_definitions', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['baseline_id'] == sample_baseline.id

    td = db.session.get(TaskDefinition, data['id'])
    assert td is not None

def test_create_task_definition_unauthorized_baseline(client, sample_baseline, default_user_data, default_read_only_user):
    # Attempt by a READ_ONLY user (default_read_only_user) to add task_def to consultant's baseline.
    # Ensure default_read_only_user exists
    # db.session.add(default_read_only_user) # User is created by its fixture
    # db.session.commit()

    login_rv = client.post('/auth/login', json={
        "username": default_user_data['username'], # from default_user_data for default_read_only_user
        "password": default_user_data['password']
    })
    assert login_rv.status_code == 200, f"Login failed for default_read_only_user: {login_rv.data.decode()}"
    other_headers = {"Authorization": f"Bearer {login_rv.get_json()['access_token']}"}

    assert sample_baseline.creator.role == CONSULTANT # sample_baseline owned by consultant
    assert default_read_only_user.role == READ_ONLY
    assert sample_baseline.created_by_id != default_read_only_user.id


    payload = {"title": "Task by wrong role user", "category": "Test"}
    rv = client.post(f'/api/baselines/{sample_baseline.id}/task_definitions', json=payload, headers=other_headers)
    # This will depend on how RBAC is applied to this endpoint. Assuming 403 if READ_ONLY cannot add.
    # If the route is not yet protected by new RBAC, it might pass or give 403 based on old logic.
    # For now, assuming future RBAC will make this 403. Current code has a check for baseline creator.
    assert rv.status_code == 403

def test_update_task_definition(client, auth_consultant_user_and_headers, sample_task_definition):
    consultant_creator, headers = auth_consultant_user_and_headers
    # sample_task_definition is on sample_baseline, created by consultant_user
    assert sample_task_definition.baseline.created_by_id == consultant_creator.id

    payload = {"title": "Updated Task Def Title X by Consultant", "description": "Updated desc X."}
    rv = client.put(f'/api/task_definitions/{sample_task_definition.id}', json=payload, headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == "Updated Task Def Title X by Consultant"

    updated_td = db.session.get(TaskDefinition, sample_task_definition.id)
    assert updated_td.description == "Updated desc X."

def test_delete_task_definition(client, auth_consultant_user_and_headers, sample_task_definition):
    consultant_creator, headers = auth_consultant_user_and_headers
    assert sample_task_definition.baseline.created_by_id == consultant_creator.id
    task_def_id_to_delete = sample_task_definition.id

    rv = client.delete(f'/api/task_definitions/{task_def_id_to_delete}', headers=headers)
    assert rv.status_code == 200
    assert db.session.get(TaskDefinition, task_def_id_to_delete) is None
