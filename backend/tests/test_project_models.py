from app.project_models import Project, Baseline, TaskDefinition, ProjectTask, Evidence
from app.models import User
from app import db as actual_db # Use the aliased db import
from datetime import date, datetime

# Model tests now use the 'db_session' fixture from conftest.py
# which provides the initialized 'actual_db' object and handles setup/teardown.

def test_create_project_model(db_session, consultant_user): # Changed to consultant_user
    project = Project(
        name="Model Test Project Alpha",
        owner_id=consultant_user.id, # Project owned by consultant
        status="planning",
        start_date=date(2024,1,1),
        description="Detailed description for Alpha."
    )
    db_session.session.add(project)
    db_session.session.commit()

    retrieved_project = db_session.session.get(Project, project.id)
    assert retrieved_project is not None
    assert retrieved_project.name == "Model Test Project Alpha"
    assert retrieved_project.owner.username == consultant_user.username # Check against consultant_user
    assert retrieved_project.status == "planning"
    assert retrieved_project.start_date == date(2024,1,1)
    assert retrieved_project.priority == 'Medium' # Test default priority

    retrieved_project.project_type = "Internal Audit"
    db_session.session.commit()
    updated_project = db_session.session.get(Project, project.id)
    assert updated_project.project_type == "Internal Audit"

def test_project_task_relationship(db_session, sample_project, sample_task_definition, consultant_user): # Changed to consultant_user
    # sample_project is owned by consultant_user, sample_task_definition is on consultant's baseline
    task = ProjectTask(
        project_id=sample_project.id,
        task_definition_id=sample_task_definition.id,
        title="Task for relationship test Beta",
        description="A task specifically for testing relationships.",
        status="pending",
        assigned_to_id=consultant_user.id, # Task assigned to consultant_user
        due_date=date(2024,12,31)
    )
    db_session.session.add(task)
    db_session.session.commit()

    assert task in sample_project.tasks.all()
    assert task.task_definition == sample_task_definition
    assert task.assignee == consultant_user # Assert against consultant_user
    # Check count accurately based on what's created in this test's scope
    assert sample_project.tasks.count() >= 1


def test_baseline_task_definition_relationship(db_session, sample_baseline):
    # sample_baseline is created by project_owner_user via db_session
    # sample_task_definition fixture might also add a taskdef.
    # We want to test adding new ones here.

    initial_count = sample_baseline.task_definitions.count()

    td1 = TaskDefinition(title="TD Gamma 1", baseline_id=sample_baseline.id, category="Cat Gamma")
    td2 = TaskDefinition(title="TD Gamma 2", baseline_id=sample_baseline.id, description="Desc Gamma")
    db_session.session.add_all([td1, td2])
    db_session.session.commit()

    baseline_task_defs = sample_baseline.task_definitions.all()
    assert len(baseline_task_defs) == initial_count + 2

    td1_found = any(td.title == "TD Gamma 1" for td in baseline_task_defs)
    td2_found = any(td.title == "TD Gamma 2" for td in baseline_task_defs)
    assert td1_found and td2_found

def test_task_evidence_relationship(db_session, sample_project_task, consultant_user): # Changed to consultant_user
    # sample_project_task is assigned to consultant_user by default from fixture
    ev = Evidence(
        project_task_id=sample_project_task.id,
        uploaded_by_id=consultant_user.id, # Evidence uploaded by consultant_user
        file_name="evidence_rel_test_delta.txt",
        tool_type="Manual",
        notes="Some notes for delta evidence."
    )
    db_session.session.add(ev)
    db_session.session.commit()

    assert ev in sample_project_task.evidences.all()
    assert ev.uploader == consultant_user # Assert against consultant_user
    assert sample_project_task.evidences.count() >= 1

def test_project_task_defaults_and_timestamps(db_session, sample_project):
    task = ProjectTask(title="Timestamp Test Task", project_id=sample_project.id)
    db_session.session.add(task)
    db_session.session.commit()

    assert task.id is not None
    assert task.status == 'pending'
    assert task.created_at is not None
    assert task.updated_at is not None
    assert isinstance(task.created_at, datetime)

    first_updated_at = task.updated_at
    task.description = "trigger update"
    db_session.session.add(task) # Add to session again to mark dirty
    db_session.session.commit()
    # To ensure time difference, might need a small sleep if precision is too high
    # For now, just checking it's not None and is a datetime
    assert task.updated_at is not None
    assert task.updated_at >= first_updated_at
    assert task.priority == 'Medium' # Test default priority
    assert task.due_date_reminder_sent is False # Test default reminder_sent


def test_evidence_defaults(db_session, sample_project_task, consultant_user): # Changed to consultant_user
    # sample_project_task is associated with consultant_user
    evidence = Evidence(
        project_task_id=sample_project_task.id,
        uploaded_by_id=consultant_user.id, # Evidence uploaded by consultant_user
        file_name="default_check.txt"
    )
    db_session.session.add(evidence)
    db_session.session.commit()
    assert evidence.id is not None
    assert evidence.upload_date is not None
    assert isinstance(evidence.upload_date, datetime)
    assert evidence.verified is False # Test default verified

    evidence.mime_type = "application/pdf"
    db_session.session.commit()
    updated_evidence = db_session.session.get(Evidence, evidence.id)
    assert updated_evidence.mime_type == "application/pdf"
