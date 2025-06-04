import json
from app.project_models import Project
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # Import roles
from app import db

# === Create Project Tests ===
def test_create_project_as_consultant(client, auth_consultant_user_and_headers, consultant_user):
    _, headers = auth_consultant_user_and_headers
    payload = {"name": "Consultant Project", "priority": "High", "project_type": "Pentest"}
    rv = client.post('/api/projects', json=payload, headers=headers)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['name'] == payload['name']
    assert data['owner_id'] == consultant_user.id
    assert data['priority'] == 'High'
    project = db.session.get(Project, data['id'])
    assert project.owner_id == consultant_user.id

def test_create_project_as_admin(client, auth_admin_user_and_headers, admin_user):
    _, headers = auth_admin_user_and_headers
    payload = {"name": "Admin Project", "priority": "Low", "project_type": "Internal Review"}
    rv = client.post('/api/projects', json=payload, headers=headers)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['name'] == payload['name']
    assert data['owner_id'] == admin_user.id # Admin becomes owner when creating
    project = db.session.get(Project, data['id'])
    assert project.owner_id == admin_user.id

def test_create_project_as_readonly_denied(client, auth_user_and_headers): # auth_user is READ_ONLY
    _, headers = auth_user_and_headers
    payload = {"name": "ReadOnly Project Attempt"}
    rv = client.post('/api/projects', json=payload, headers=headers)
    assert rv.status_code == 403

# === Get Projects (List) Tests ===
def test_get_projects_as_consultant(client, auth_consultant_user_and_headers, sample_project, consultant_user):
    # sample_project is owned by consultant_user
    _, headers = auth_consultant_user_and_headers
    # Create another project by another user (e.g. admin) that consultant should not see
    admin = User.query.filter_by(email="admin@example.com").first() # Assuming admin_user fixture ran or created it
    if admin:
        other_project = Project(name="AdminOnlyProject", owner_id=admin.id)
        db.session.add(other_project)
        db.session.commit()

    rv = client.get('/api/projects', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1 # At least sample_project
    assert any(p['id'] == sample_project.id for p in data)
    if admin:
        assert not any(p['name'] == "AdminOnlyProject" for p in data)

def test_get_projects_as_admin(client, auth_admin_user_and_headers, sample_project, consultant_user):
    _, headers = auth_admin_user_and_headers
    # Create another project by admin
    admin_user_obj = User.query.filter_by(email="admin@example.com").first() # from auth_admin_user_and_headers
    admin_project = Project(name="ProjectByAdminForListTest", owner_id=admin_user_obj.id)
    db.session.add(admin_project)
    db.session.commit()

    rv = client.get('/api/projects', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    project_ids = [p['id'] for p in data]
    assert sample_project.id in project_ids # Owned by consultant
    assert admin_project.id in project_ids # Owned by admin

def test_get_projects_as_readonly(client, auth_user_and_headers, sample_project):
    # READ_ONLY user should get an empty list as per current logic (no grants)
    _, headers = auth_user_and_headers
    rv = client.get('/api/projects', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

# === Get Specific Project Tests ===
def test_get_specific_project_consultant_owner(client, auth_consultant_user_and_headers, sample_project):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project.owner_id == consultant.id
    rv = client.get(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['id'] == sample_project.id

def test_get_specific_project_admin_can_view_others(client, auth_admin_user_and_headers, sample_project):
    # sample_project is owned by consultant_user
    _, headers = auth_admin_user_and_headers
    rv = client.get(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['id'] == sample_project.id

def test_get_specific_project_consultant_denied_for_others(client, auth_consultant_user_and_headers, admin_user):
    consultant, headers = auth_consultant_user_and_headers
    # Project owned by admin
    other_project = Project(name="AdminProjectForConsultantDeny", owner_id=admin_user.id)
    db.session.add(other_project)
    db.session.commit()
    rv = client.get(f'/api/projects/{other_project.id}', headers=headers)
    assert rv.status_code == 403

def test_get_specific_project_readonly_denied(client, auth_user_and_headers, sample_project):
    # sample_project owned by consultant_user
    _, headers = auth_user_and_headers # READ_ONLY user
    rv = client.get(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 403

# === Update Project Tests ===
def test_update_project_consultant_owner(client, auth_consultant_user_and_headers, sample_project):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project.owner_id == consultant.id
    payload = {"name": "Updated By Consultant Owner", "priority": "Critical"}
    rv = client.put(f'/api/projects/{sample_project.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == "Updated By Consultant Owner"
    assert data['priority'] == "Critical"

def test_update_project_admin_can_update_others(client, auth_admin_user_and_headers, sample_project):
    # sample_project owned by consultant_user
    _, headers = auth_admin_user_and_headers
    payload = {"name": "Updated By Admin", "status": "completed"}
    rv = client.put(f'/api/projects/{sample_project.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == "Updated By Admin"
    assert data['status'] == "completed"

def test_update_project_consultant_denied_for_others(client, auth_consultant_user_and_headers, admin_user):
    consultant, headers = auth_consultant_user_and_headers
    other_project = Project(name="AdminProjectForUpdateDeny", owner_id=admin_user.id)
    db.session.add(other_project)
    db.session.commit()
    payload = {"name": "Attempted Update By Consultant"}
    rv = client.put(f'/api/projects/{other_project.id}', json=payload, headers=headers)
    assert rv.status_code == 403

def test_update_project_readonly_denied(client, auth_user_and_headers, sample_project):
    _, headers = auth_user_and_headers # READ_ONLY user
    payload = {"name": "Attempted Update By ReadOnly"}
    rv = client.put(f'/api/projects/{sample_project.id}', json=payload, headers=headers)
    assert rv.status_code == 403

# === Delete Project Tests ===
def test_delete_project_admin(client, auth_admin_user_and_headers, sample_project):
    # sample_project owned by consultant_user
    _, headers = auth_admin_user_and_headers
    project_id = sample_project.id
    rv = client.delete(f'/api/projects/{project_id}', headers=headers)
    assert rv.status_code == 200
    assert db.session.get(Project, project_id) is None

def test_delete_project_consultant_denied(client, auth_consultant_user_and_headers, sample_project):
    _, headers = auth_consultant_user_and_headers
    rv = client.delete(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 403

def test_delete_project_readonly_denied(client, auth_user_and_headers, sample_project):
    _, headers = auth_user_and_headers # READ_ONLY user
    rv = client.delete(f'/api/projects/{sample_project.id}', headers=headers)
    assert rv.status_code == 403

# Existing unauthorized test, should still pass (another READ_ONLY user trying to access consultant's project)
def test_get_specific_project_unauthorized_default_user(client, sample_project, another_user_data, consultant_user):
    # sample_project is owned by consultant_user (from fixture default)
    # 'another_user' will be created with default READ_ONLY role

    # Ensure 'another_user' exists and has default role
    another_user = User.query.filter_by(email=another_user_data['email']).first()
    if not another_user:
        # Registering will give READ_ONLY role by default
        reg_rv = client.post('/auth/register', json=another_user_data)
        assert reg_rv.status_code == 201
        another_user_id = reg_rv.get_json()['user']['id']
        another_user = db.session.get(User, another_user_id)

    assert another_user.role == READ_ONLY
    assert sample_project.owner_id != another_user.id

    login_rv = client.post('/auth/login', json={
        "username": another_user_data['username'],
        "password": another_user_data['password']
    })
    assert login_rv.status_code == 200, f"Login failed for other_user: {login_rv.data.decode()}"
    other_headers = {"Authorization": f"Bearer {login_rv.get_json()['access_token']}"}

    rv = client.get(f'/api/projects/{sample_project.id}', headers=other_headers)
    assert rv.status_code == 403 # READ_ONLY user cannot access project they don't have grants to (and don't own)
