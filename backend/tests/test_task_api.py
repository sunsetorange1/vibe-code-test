import json
from app.project_models import ProjectTask, Project, Baseline, TaskDefinition, User
from app.models import ADMIN, CONSULTANT, READ_ONLY # For setting roles
from app import db

# === Apply Baseline Tests ===
def test_apply_baseline_to_project_consultant_owner(client, auth_consultant_user_and_headers, sample_project, sample_baseline, sample_task_definition):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project.owner_id == consultant.id # sample_project is owned by consultant

    rv = client.post(f'/api/projects/{sample_project.id}/apply_baseline/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    # ... (rest of assertions for successful application)

def test_apply_baseline_to_project_admin(client, auth_admin_user_and_headers, sample_project, sample_baseline, sample_task_definition):
    # sample_project owned by consultant_user
    # sample_task_definition is linked to sample_baseline
    admin, headers = auth_admin_user_and_headers
    assert sample_project.owner_id != admin.id
    assert sample_baseline.task_definitions.count() > 0 # Ensure baseline has tasks

    rv = client.post(f'/api/projects/{sample_project.id}/apply_baseline/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"

def test_apply_baseline_to_project_readonly_denied(client, auth_user_and_headers, sample_project, sample_baseline):
    _, headers = auth_user_and_headers # READ_ONLY user
    rv = client.post(f'/api/projects/{sample_project.id}/apply_baseline/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 403

# === Create Ad-hoc Task Tests ===
def test_create_ad_hoc_task_consultant_owner(client, auth_consultant_user_and_headers, sample_project, consultant_user, default_read_only_user):
    owner_consultant, headers = auth_consultant_user_and_headers
    assert sample_project.owner_id == owner_consultant.id

    assignee = default_read_only_user # Assign task to a READ_ONLY user for variety

    payload = {"title": "Consultant Ad-hoc Task", "assigned_to_id": assignee.id, "priority": "High"}
    rv = client.post(f'/api/projects/{sample_project.id}/tasks', json=payload, headers=headers)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['priority'] == "High"
    assert data['project_id'] == sample_project.id

def test_create_ad_hoc_task_admin(client, auth_admin_user_and_headers, sample_project, admin_user):
    # sample_project owned by consultant_user
    _, headers = auth_admin_user_and_headers
    payload = {"title": "Admin Ad-hoc Task"}
    rv = client.post(f'/api/projects/{sample_project.id}/tasks', json=payload, headers=headers)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['title'] == payload['title']

def test_create_ad_hoc_task_readonly_denied(client, auth_user_and_headers, sample_project):
    _, headers = auth_user_and_headers # READ_ONLY user
    payload = {"title": "ReadOnly Ad-hoc Task Attempt"}
    rv = client.post(f'/api/projects/{sample_project.id}/tasks', json=payload, headers=headers)
    assert rv.status_code == 403

# === Get Project Tasks Tests ===
def test_get_project_tasks_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant.id
    rv = client.get(f'/api/projects/{sample_project_task.project_id}/tasks', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert any(t['id'] == sample_project_task.id for t in data)

def test_get_project_tasks_admin(client, auth_admin_user_and_headers, sample_project_task):
    _, headers = auth_admin_user_and_headers
    rv = client.get(f'/api/projects/{sample_project_task.project_id}/tasks', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert any(t['id'] == sample_project_task.id for t in data)

def test_get_project_tasks_readonly_denied(client, auth_user_and_headers, sample_project_task):
    # sample_project_task project is owned by consultant_user
    _, headers = auth_user_and_headers # READ_ONLY user
    rv = client.get(f'/api/projects/{sample_project_task.project_id}/tasks', headers=headers)
    assert rv.status_code == 403 # Access denied as per new rules

# === Get Specific Task Tests ===
def test_get_specific_task_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant.id
    rv = client.get(f'/api/tasks/{sample_project_task.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['id'] == sample_project_task.id

def test_get_specific_task_admin(client, auth_admin_user_and_headers, sample_project_task):
    _, headers = auth_admin_user_and_headers
    rv = client.get(f'/api/tasks/{sample_project_task.id}', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['id'] == sample_project_task.id

def test_get_specific_task_readonly_denied(client, auth_user_and_headers, sample_project_task):
    # sample_project_task project is owned by consultant_user
    _, headers = auth_user_and_headers # READ_ONLY user
    rv = client.get(f'/api/tasks/{sample_project_task.id}', headers=headers)
    assert rv.status_code == 403

# === Update Task Tests ===
def test_update_task_consultant_owner(client, auth_consultant_user_and_headers, sample_project_task):
    consultant, headers = auth_consultant_user_and_headers
    assert sample_project_task.project.owner_id == consultant.id
    payload = {"title": "Updated by Consultant Owner", "status": "completed", "priority": "Low"}
    rv = client.put(f'/api/tasks/{sample_project_task.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['status'] == payload['status']
    assert data['priority'] == payload['priority']

def test_update_task_admin(client, auth_admin_user_and_headers, sample_project_task):
    _, headers = auth_admin_user_and_headers
    payload = {"title": "Updated by Admin", "description": "Admin was here."}
    rv = client.put(f'/api/tasks/{sample_project_task.id}', json=payload, headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['description'] == payload['description']

def test_update_task_readonly_denied(client, auth_user_and_headers, sample_project_task):
    _, headers = auth_user_and_headers # READ_ONLY user
    payload = {"title": "Attempted Update by ReadOnly"}
    rv = client.put(f'/api/tasks/{sample_project_task.id}', json=payload, headers=headers)
    assert rv.status_code == 403

# Test that a consultant cannot update tasks in a project they don't own
def test_update_task_consultant_not_owner_denied(client, auth_consultant_user_and_headers, admin_user):
    consultant, headers = auth_consultant_user_and_headers

    # Create a project and task owned by Admin
    project_by_admin = Project(name="Admin Project for Task Update Test", owner_id=admin_user.id)
    db.session.add(project_by_admin)
    db.session.commit()
    task_in_admin_project = ProjectTask(title="Task in Admin Project", project_id=project_by_admin.id)
    db.session.add(task_in_admin_project)
    db.session.commit()

    payload = {"title": "Consultant attempt on Admin's task"}
    rv = client.put(f'/api/tasks/{task_in_admin_project.id}', json=payload, headers=headers)
    assert rv.status_code == 403
    assert "Consultant can only update tasks in their own projects" in rv.get_json()['msg']

# The old test_update_task_status_by_assignee is no longer valid with RBAC as assignees (if RO) cannot update.
# If specific fields are updatable by assignees with certain roles, that needs new logic/decorators.
# Current rules: Admin or (Consultant owning project) can update.
# If an assigned user happens to be a Consultant who owns the project, they can update.
# If an assigned user is RO, they cannot update via this endpoint.
# If an assigned user is Admin, they can update.
# This is now covered by the above tests.
