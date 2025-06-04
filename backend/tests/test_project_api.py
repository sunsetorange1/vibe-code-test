import json
from app.project_models import Project
from app.models import User # Import User model
from app import db # Use the db instance from app module

def test_create_project(client, auth_user_and_headers):
    owner, headers = auth_user_and_headers
    payload = {
        "name": "New Awesome Project",
        "description": "Desc for awesome project",
        "status": "planning",
        "priority": "High",
        "project_type": "External Pentest"
    }
    rv = client.post('/api/projects', json=payload, headers=headers)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['name'] == payload['name']
    assert data['owner_id'] == owner.id
    assert data['status'] == 'planning'
    assert data['priority'] == 'High'
    assert data['project_type'] == 'External Pentest'

    project = db.session.get(Project, data['id']) # Use imported db
    assert project is not None
    assert project.priority == 'High'
    assert project.project_type == 'External Pentest'

    # Test default priority and null project_type
    payload_default = {"name": "Project With Defaults", "description": "Testing defaults"}
    rv_default = client.post('/api/projects', json=payload_default, headers=headers)
    assert rv_default.status_code == 201
    data_default = rv_default.get_json()
    assert data_default['name'] == payload_default['name']
    assert data_default['priority'] == 'Medium' # Default value
    assert data_default['project_type'] is None # Default is None

def test_get_projects_owned(client, auth_user_and_headers, sample_project):
    owner, headers = auth_user_and_headers
    rv = client.get('/api/projects', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) >= 1

    found_project = next((p for p in data if p['id'] == sample_project.id), None)
    assert found_project is not None
    assert found_project['name'] == sample_project.name
    assert found_project['owner_id'] == owner.id
    assert 'priority' in found_project # Check new fields are present
    assert 'project_type' in found_project
    assert found_project['priority'] == sample_project.priority # Assuming sample_project has default 'Medium'
    assert found_project['project_type'] == sample_project.project_type # Assuming sample_project has None

def test_get_specific_project_owner(client, auth_user_and_headers, sample_project):
    owner, headers = auth_user_and_headers
    assert sample_project.owner_id == owner.id

    rv = client.get(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == sample_project.name
    assert data['priority'] == sample_project.priority
    assert data['project_type'] == sample_project.project_type

def test_get_specific_project_unauthorized(client, sample_project, another_user_data, project_owner_user):
    # project_owner_user is the owner of sample_project
    # Create and login as 'another_user'
    # Ensure another_user_data is used to create a distinct user in the db for this test
    another_user = User.query.filter_by(email=another_user_data['email']).first()
    if not another_user:
        client.post('/auth/register', json=another_user_data) # Register the other user

    login_rv = client.post('/auth/login', json={
        "username": another_user_data['username'],
        "password": another_user_data['password']
    })
    assert login_rv.status_code == 200, f"Login failed for other_user: {login_rv.data.decode()}"
    other_access_token = login_rv.get_json()['access_token']
    other_headers = {"Authorization": f"Bearer {other_access_token}"}

    rv = client.get(f'/api/projects/{sample_project.id}', headers=other_headers)
    assert rv.status_code == 403

def test_update_project_owner(client, auth_user_and_headers, sample_project):
    owner, headers = auth_user_and_headers
    assert sample_project.owner_id == owner.id

    payload = {
        "name": "Updated Project Name",
        "status": "in_progress",
        "description": "New Description",
        "priority": "Low",
        "project_type": "Compliance Check"
    }
    rv = client.put(f'/api/projects/{sample_project.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == "Updated Project Name"
    assert data['status'] == "in_progress"
    assert data['description'] == "New Description"
    assert data['priority'] == "Low"
    assert data['project_type'] == "Compliance Check"

    updated_project = db.session.get(Project, sample_project.id) # Use imported db
    assert updated_project.name == "Updated Project Name"
    assert updated_project.status == "in_progress"
    assert updated_project.priority == "Low"
    assert updated_project.project_type == "Compliance Check"

    # Test updating only one of the new fields
    payload_partial = {"priority": "Very High"}
    rv_partial = client.put(f'/api/projects/{sample_project.id}', json=payload_partial, headers=headers)
    assert rv_partial.status_code == 200
    data_partial = rv_partial.get_json()
    assert data_partial['priority'] == "Very High"
    assert data_partial['project_type'] == "Compliance Check" # Should remain from previous update
    assert data_partial['name'] == "Updated Project Name" # Should remain

def test_delete_project_owner(client, auth_user_and_headers, sample_project):
    owner, headers = auth_user_and_headers
    assert sample_project.owner_id == owner.id
    project_id_to_delete = sample_project.id

    rv = client.delete(f'/api/projects/{project_id_to_delete}', headers=headers)
    assert rv.status_code == 200
    assert db.session.get(Project, project_id_to_delete) is None # Use imported db

def test_delete_project_unauthorized(client, sample_project, another_user_data):
    # Ensure another_user_data is used to create a distinct user
    another_user = User.query.filter_by(email=another_user_data['email']).first()
    if not another_user:
        client.post('/auth/register', json=another_user_data)

    login_rv = client.post('/auth/login', json={
        "username": another_user_data['username'],
        "password": another_user_data['password']
    })
    assert login_rv.status_code == 200, f"Login failed for other_user: {login_rv.data.decode()}"
    other_access_token = login_rv.get_json()['access_token']
    other_headers = {"Authorization": f"Bearer {other_access_token}"}

    rv = client.delete(f'/api/projects/{sample_project.id}', headers=other_headers)
    assert rv.status_code == 403
    assert db.session.get(Project, sample_project.id) is not None # Use imported db
