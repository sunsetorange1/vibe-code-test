import json
from app.project_models import Baseline, TaskDefinition
from app.models import User # Import User if needed for type hints or direct use
from app import db # Use the db instance from app module

def test_create_baseline(client, auth_user_and_headers):
    creator, headers = auth_user_and_headers
    payload = {"name": "New Security Baseline Alpha", "description": "Standard security checks Alpha"}
    rv = client.post('/api/baselines', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['name'] == payload['name']
    assert data['created_by_id'] == creator.id

    baseline = db.session.get(Baseline, data['id']) # Use imported db
    assert baseline is not None

def test_create_baseline_duplicate_name(client, auth_user_and_headers, sample_baseline):
    creator, headers = auth_user_and_headers
    # sample_baseline is created by project_owner_user (aliased as creator here)
    assert sample_baseline.created_by_id == creator.id

    payload = {"name": sample_baseline.name, "description": "Attempting duplicate name"}
    rv = client.post('/api/baselines', json=payload, headers=headers)
    assert rv.status_code == 400
    assert "already exists" in rv.get_json()['msg']

def test_get_baselines(client, auth_headers, sample_baseline):
    rv = client.get('/api/baselines', headers=auth_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(b['id'] == sample_baseline.id and b['name'] == sample_baseline.name for b in data)

def test_get_specific_baseline(client, auth_headers, sample_baseline, sample_task_definition):
    rv = client.get(f'/api/baselines/{sample_baseline.id}', headers=auth_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == sample_baseline.name
    assert data['id'] == sample_baseline.id
    assert len(data['task_definitions']) >= 1
    assert any(td['id'] == sample_task_definition.id for td in data['task_definitions'])

def test_create_task_definition_for_baseline(client, auth_user_and_headers, sample_baseline):
    creator, headers = auth_user_and_headers
    assert sample_baseline.created_by_id == creator.id

    payload = {"title": "New Task Def for Baseline B", "category": "Audit"}
    rv = client.post(f'/api/baselines/{sample_baseline.id}/task_definitions', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['baseline_id'] == sample_baseline.id

    td = db.session.get(TaskDefinition, data['id']) # Use imported db
    assert td is not None

def test_create_task_definition_unauthorized_baseline(client, sample_baseline, another_user_data):
    # Register and log in as 'another_user'
    other_user = User.query.filter_by(email=another_user_data['email']).first()
    if not other_user:
        client.post('/auth/register', json=another_user_data)

    login_rv = client.post('/auth/login', json={
        "username": another_user_data['username'],
        "password": another_user_data['password']
    })
    assert login_rv.status_code == 200, f"Login failed for other_user: {login_rv.data.decode()}"
    other_headers = {"Authorization": f"Bearer {login_rv.get_json()['access_token']}"}

    payload = {"title": "Task by wrong user", "category": "Test"}
    rv = client.post(f'/api/baselines/{sample_baseline.id}/task_definitions', json=payload, headers=other_headers)
    assert rv.status_code == 403

def test_update_task_definition(client, auth_user_and_headers, sample_task_definition):
    creator, headers = auth_user_and_headers
    assert sample_task_definition.baseline.created_by_id == creator.id

    payload = {"title": "Updated Task Def Title X", "description": "Updated desc X."}
    rv = client.put(f'/api/task_definitions/{sample_task_definition.id}', json=payload, headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == "Updated Task Def Title X"

    updated_td = db.session.get(TaskDefinition, sample_task_definition.id) # Use imported db
    assert updated_td.description == "Updated desc X."

def test_delete_task_definition(client, auth_user_and_headers, sample_task_definition):
    creator, headers = auth_user_and_headers
    assert sample_task_definition.baseline.created_by_id == creator.id
    task_def_id_to_delete = sample_task_definition.id

    rv = client.delete(f'/api/task_definitions/{task_def_id_to_delete}', headers=headers)
    assert rv.status_code == 200
    assert db.session.get(TaskDefinition, task_def_id_to_delete) is None # Use imported db
