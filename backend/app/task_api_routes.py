from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity # get_jwt_identity is used
from app import db
from app.project_models import Project, Baseline, TaskDefinition, ProjectTask
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # User and role constants
from app.auth_decorators import admin_required, consultant_or_admin_required, any_authenticated_user_required # Auth decorators
from app.project_api_routes import parse_date # Re-use date parsing utility

task_api_bp = Blueprint('task_api', __name__, url_prefix='/api')

# --- ProjectTask Endpoints ---

@task_api_bp.route('/projects/<int:project_id>/apply_baseline/<int:baseline_id>', methods=['POST'])
@consultant_or_admin_required
def apply_baseline_to_project(project_id, baseline_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    project = db.session.get(Project, project_id)
    baseline = db.session.get(Baseline, baseline_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if not baseline:
        return jsonify({"msg": "Baseline not found"}), 404
    if not acting_user: # Should be caught by decorator, but defensive check
        return jsonify({"msg": "Authenticated user not found"}), 401

    if acting_user.role == CONSULTANT and project.owner_id != acting_user.id:
        return jsonify({"msg": "Consultant can only apply baselines to their own projects"}), 403
    # Admin access is implicitly allowed by the decorator

    tasks_from_baseline = baseline.task_definitions.all()
    if not tasks_from_baseline:
        return jsonify({"msg": "Baseline has no task definitions to apply."}), 200

    newly_created_tasks_count = 0
    for td in tasks_from_baseline:
        existing_task = ProjectTask.query.filter_by(
            project_id=project_id,
            task_definition_id=td.id
        ).first()

        if not existing_task:
            new_task = ProjectTask(
                project_id=project_id,
                task_definition_id=td.id,
                title=td.title,
                description=td.description,
                status='pending'
            )
            db.session.add(new_task)
            newly_created_tasks_count += 1

    if newly_created_tasks_count > 0:
        db.session.commit()
        return jsonify({"msg": f"{newly_created_tasks_count} tasks from baseline '{baseline.name}' applied to project '{project.name}'."}), 201
    else:
        return jsonify({"msg": "All tasks from this baseline have already been applied to this project or the baseline is empty."}), 200


@task_api_bp.route('/projects/<int:project_id>/tasks', methods=['POST'])
@consultant_or_admin_required
def create_ad_hoc_task(project_id):
    data = request.get_json()
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    if acting_user.role == CONSULTANT and project.owner_id != acting_user.id:
        return jsonify({"msg": "Consultant can only add tasks to their own projects"}), 403
    # Admin access is implicitly allowed by the decorator

    if not data or not data.get('title'):
        return jsonify({"msg": "Missing task title"}), 400

    new_task = ProjectTask(
        project_id=project_id,
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'pending'),
        due_date=parse_date(data.get('due_date')),
        priority=data.get('priority', 'Medium'),
        due_date_reminder_sent=data.get('due_date_reminder_sent', False)
    )

    if data.get('assigned_to_id'):
        assignee = db.session.get(User, data.get('assigned_to_id'))
        if not assignee:
            return jsonify({"msg": f"Assignee user with id {data.get('assigned_to_id')} not found"}), 400
        new_task.assigned_to_id = assignee.id

    db.session.add(new_task)
    db.session.commit()

    task_data = {
        "id": new_task.id,
        "title": new_task.title,
        "description": new_task.description,
        "status": new_task.status,
        "project_id": new_task.project_id,
        "assigned_to_id": new_task.assigned_to_id,
        "due_date": new_task.due_date.isoformat() if new_task.due_date else None,
        "task_definition_id": new_task.task_definition_id,
        "priority": new_task.priority,
        "due_date_reminder_sent": new_task.due_date_reminder_sent,
        "created_at": new_task.created_at.isoformat(),
        "updated_at": new_task.updated_at.isoformat()
    }
    return jsonify(task_data), 201

@task_api_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@any_authenticated_user_required
def get_project_tasks(project_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    if acting_user.role == ADMIN:
        pass # Admin can see all tasks for any project
    elif acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only view tasks for their own projects"}), 403
    elif acting_user.role == READ_ONLY:
        # TODO: Implement grant-based access for Read-Only users
        # For now, deny if not admin or (consultant who owns project)
        # This effectively means they need a grant for now.
        if project.owner_id != acting_user.id: # This will typically be true for RO unless they somehow owned it.
             return jsonify({"msg": "Read-Only access to tasks requires specific project grant"}), 403
    else: # Should not happen
        return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    tasks = ProjectTask.query.filter_by(project_id=project_id).all()
    tasks_data = [{
        "id": t.id, "title": t.title, "description": t.description, "status": t.status,
        "project_id": t.project_id, "assigned_to_id": t.assigned_to_id,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "task_definition_id": t.task_definition_id,
        "priority": t.priority,
        "due_date_reminder_sent": t.due_date_reminder_sent,
        "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat()
    } for t in tasks]
    return jsonify(tasks_data), 200

@task_api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@any_authenticated_user_required
def get_task(task_id):
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    project = db.session.get(Project, task.project_id)
    if not project:
        return jsonify({"msg": "Associated project not found"}), 500 # Internal error if task has no project

    if acting_user.role == ADMIN:
        pass # Admin can see any task
    elif acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id: # Consultant must own the project
            # If task-specific assignment grants view, that logic would be here too
            return jsonify({"msg": "Consultant can only view tasks for their own projects"}), 403
    elif acting_user.role == READ_ONLY:
        # TODO: Grant-based access. For now, if not admin or project owner (consultant), deny.
        # Also, task assignee might have rights - this is where it gets complex.
        # Current logic: If not admin, and not consultant owner, then deny for RO.
        # A Read-Only user assigned to a task might still be denied here if they don't own the project.
        # This needs refinement if assignees (who could be RO) should view tasks they are assigned to.
        # For now, sticking to project-level ownership for Consultant/Admin, and grant-needed for RO.
        if project.owner_id != acting_user.id: # This will typically be true for RO
            return jsonify({"msg": "Read-Only access to task requires specific project grant"}), 403
    else: # Should not happen
        return jsonify({"msg": "Unauthorized: Unknown role"}), 403

    task_data = {
        "id": task.id, "title": task.title, "description": task.description, "status": task.status,
        "project_id": task.project_id, "assigned_to_id": task.assigned_to_id,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "task_definition_id": task.task_definition_id,
        "priority": task.priority,
        "due_date_reminder_sent": task.due_date_reminder_sent,
        "created_at": task.created_at.isoformat(), "updated_at": task.updated_at.isoformat()
    }
    return jsonify(task_data), 200

@task_api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@consultant_or_admin_required # Only Admin or Consultant can attempt to update
def update_task(task_id):
    data = request.get_json()
    current_user_jwt_id = get_jwt_identity()
    acting_user = User.query.get(current_user_jwt_id)
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404
    if not acting_user: # Should be caught by decorator
        return jsonify({"msg": "Authenticated user not found"}), 401

    project = db.session.get(Project, task.project_id)
    if not project:
         return jsonify({"msg": "Associated project not found"}), 500

    # Role-specific authorization for updating
    if acting_user.role == CONSULTANT:
        if project.owner_id != acting_user.id:
            return jsonify({"msg": "Consultant can only update tasks in their own projects"}), 403
    # Admin can update any task (implicit from decorator)

    # At this point, user is either Admin or Consultant owning the project.
    # They have full update rights on all fields.
    # The old logic distinguishing between 'can_update_fully' and 'can_update_status_descr'
    # is simplified as assignees (who might be Read-Only) are not granted update rights by this endpoint's decorator.
    # If assignees (e.g. Read-Only user) need to update specific fields like 'status',
    # a separate endpoint or more granular logic within this one would be needed.

    task.title = data.get('title', task.title)
    if 'description' in data: # Allow setting description to empty or None
        task.description = data.get('description', task.description)
    if 'status' in data:
        task.status = data.get('status', task.status)
    if 'priority' in data:
        task.priority = data.get('priority', task.priority)
    if 'due_date' in data: # Allow clearing date
        task.due_date = parse_date(data.get('due_date'))
    if 'assigned_to_id' in data:
        assignee_id = data.get('assigned_to_id')
        if assignee_id is not None: # Check for explicit null or actual ID
            assignee = db.session.get(User, assignee_id)
            if not assignee:
                return jsonify({"msg": f"Assignee user with id {assignee_id} not found"}), 400
            task.assigned_to_id = assignee.id
        else: # Allow unassigning by passing null for assigned_to_id
            task.assigned_to_id = None
    if 'due_date_reminder_sent' in data:
        task.due_date_reminder_sent = bool(data.get('due_date_reminder_sent'))

    db.session.commit()

    updated_task_data = {
        "id": task.id, "title": task.title, "description": task.description, "status": task.status,
        "project_id": task.project_id, "assigned_to_id": task.assigned_to_id,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "task_definition_id": task.task_definition_id,
        "priority": task.priority,
        "due_date_reminder_sent": task.due_date_reminder_sent,
        "created_at": task.created_at.isoformat(), "updated_at": task.updated_at.isoformat()
    }
    return jsonify(updated_task_data), 200
