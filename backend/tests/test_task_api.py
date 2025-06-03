import json
from app.project_models import ProjectTask, Project, Baseline, TaskDefinition, User
from app import db # Use the db instance from app module

def test_apply_baseline_to_project(client, auth_user_and_headers, sample_project, sample_baseline, sample_task_definition):
    owner, headers = auth_user_and_headers
    assert sample_project.owner_id == owner.id

    rv = client.post(f'/api/projects/{sample_project.id}/apply_baseline/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"

    tasks = ProjectTask.query.filter_by(project_id=sample_project.id, task_definition_id=sample_task_definition.id).all()
    assert len(tasks) == 1
    assert tasks[0].title == sample_task_definition.title

    rv = client.post(f'/api/projects/{sample_project.id}/apply_baseline/{sample_baseline.id}', headers=headers)
    assert rv.status_code == 200
    assert "already been applied" in rv.get_json()['msg']
    tasks_after_reapply = ProjectTask.query.filter_by(project_id=sample_project.id, task_definition_id=sample_task_definition.id).all()
    assert len(tasks_after_reapply) == 1

def test_create_ad_hoc_task(client, auth_user_and_headers, sample_project): # Removed project_owner_user as it's in auth_user_and_headers
    owner, headers = auth_user_and_headers
    assert sample_project.owner_id == owner.id

    # Ensure assignee_user is created within this test's db session if not existing
    assignee_email = "assignee_task@example.com"
    assignee_user = User.query.filter_by(email=assignee_email).first()
    if not assignee_user:
        assignee_user = User(username="assignee_user_for_task", email=assignee_email)
        assignee_user.set_password("password")
        db.session.add(assignee_user)
        db.session.commit()

    payload = {
        "title": "Ad-hoc Task Alpha",
        "description": "Details for ad-hoc task Alpha",
        "assigned_to_id": assignee_user.id,
        "status": "in_progress",
        "due_date": "2024-12-31"
    }
    rv = client.post(f'/api/projects/{sample_project.id}/tasks', json=payload, headers=headers)
    assert rv.status_code == 201, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['assigned_to_id'] == assignee_user.id
    assert data['status'] == "in_progress"
    assert data['due_date'] == "2024-12-31"

    task = db.session.get(ProjectTask, data['id']) # Use imported db
    assert task is not None
    assert task.project_id == sample_project.id

def test_get_project_tasks(client, auth_user_and_headers, sample_project_task, sample_project): # Added sample_project for context
    owner, headers = auth_user_and_headers
    # Ensure sample_project_task belongs to a project owned by owner
    # The sample_project fixture is owned by project_owner_user, which is 'owner' here.
    # The sample_project_task fixture uses sample_project.
    assert sample_project_task.project.owner_id == owner.id

    rv = client.get(f'/api/projects/{sample_project_task.project_id}/tasks', headers=headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1 # sample_project_task should be there
    assert any(t['id'] == sample_project_task.id for t in data)


def test_get_specific_task_by_owner(client, auth_user_and_headers, sample_project_task):
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    if sample_project_task.assigned_to_id == owner.id: # Ensure owner is not also assignee for this specific test case
        sample_project_task.assigned_to_id = None
    db.session.commit()

    rv = client.get(f'/api/tasks/{sample_project_task.id}', headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == sample_project_task.title

def test_get_specific_task_by_assignee(client, auth_user_and_headers, sample_project_task):
    assignee, headers = auth_user_and_headers
    sample_project_task.assigned_to_id = assignee.id
    # Ensure owner is NOT the assignee for this specific test case
    project = db.session.get(Project, sample_project_task.project_id)
    if project.owner_id == assignee.id:
        # Need a different owner if assignee is also the default project_owner_user
        new_owner = User(username="temp_owner", email="temp_owner@example.com")
        new_owner.set_password("pass")
        db.session.add(new_owner)
        db.session.commit()
        project.owner_id = new_owner.id
    db.session.commit()


    rv = client.get(f'/api/tasks/{sample_project_task.id}', headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == sample_project_task.title

def test_update_task_status_by_assignee(client, auth_user_and_headers, sample_project_task):
    assignee, headers = auth_user_and_headers
    sample_project_task.assigned_to_id = assignee.id
     # Ensure owner is NOT the assignee for this specific test case
    project = db.session.get(Project, sample_project_task.project_id)
    if project.owner_id == assignee.id:
        new_owner = User(username="temp_owner_for_update", email="temp_owner_update@example.com")
        new_owner.set_password("pass")
        db.session.add(new_owner)
        db.session.commit()
        project.owner_id = new_owner.id
    db.session.commit()


    payload = {"status": "in_review", "description": "Assignee updated description for review"}
    rv = client.put(f'/api/tasks/{sample_project_task.id}', json=payload, headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['status'] == "in_review"
    assert data['description'] == "Assignee updated description for review"

    updated_task = db.session.get(ProjectTask, sample_project_task.id) # Use imported db
    assert updated_task.status == "in_review"

def test_update_task_fully_by_owner(client, auth_user_and_headers, sample_project_task):
    owner, headers = auth_user_and_headers
    project = db.session.get(Project, sample_project_task.project_id)
    project.owner_id = owner.id
    if sample_project_task.assigned_to_id == owner.id:
        sample_project_task.assigned_to_id = None
    db.session.commit()

    new_assignee_email = "newassignee_task_update@example.com"
    new_assignee = User.query.filter_by(email=new_assignee_email).first()
    if not new_assignee:
        new_assignee = User(username="new_assignee_for_task_update", email=new_assignee_email)
        new_assignee.set_password("test")
        db.session.add(new_assignee)
        db.session.commit()


    payload = {
        "title": "Owner Completely Updated Title",
        "status": "completed",
        "description": "Owner's final description.",
        "assigned_to_id": new_assignee.id,
        "due_date": "2025-01-01"
    }
    rv = client.put(f'/api/tasks/{sample_project_task.id}', json=payload, headers=headers)
    assert rv.status_code == 200, f"Response: {rv.data.decode()}"
    data = rv.get_json()
    assert data['title'] == payload['title']
    assert data['status'] == payload['status']
    assert data['assigned_to_id'] == new_assignee.id
    assert data['due_date'] == "2025-01-01"

    updated_task = db.session.get(ProjectTask, sample_project_task.id) # Use imported db
    assert updated_task.title == payload['title']
