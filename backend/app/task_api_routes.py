from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.project_models import Project, Baseline, TaskDefinition, ProjectTask
from app.models import User
from app.project_api_routes import parse_date # Re-use date parsing utility

task_api_bp = Blueprint('task_api', __name__, url_prefix='/api')

# --- ProjectTask Endpoints ---

@task_api_bp.route('/projects/<int:project_id>/apply_baseline/<int:baseline_id>', methods=['POST'])
@jwt_required()
def apply_baseline_to_project(project_id, baseline_id):
    current_user_id = get_jwt_identity()
    project = db.session.get(Project, project_id)
    baseline = db.session.get(Baseline, baseline_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if not baseline:
        return jsonify({"msg": "Baseline not found"}), 404

    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to modify this project"}), 403

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
@jwt_required()
def create_ad_hoc_task(project_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to add tasks to this project"}), 403
    if not data or not data.get('title'):
        return jsonify({"msg": "Missing task title"}), 400

    new_task = ProjectTask(
        project_id=project_id,
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'pending'),
        due_date=parse_date(data.get('due_date'))
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
        "created_at": new_task.created_at.isoformat(),
        "updated_at": new_task.updated_at.isoformat()
    }
    return jsonify(task_data), 201

@task_api_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def get_project_tasks(project_id):
    current_user_id = get_jwt_identity()
    project = db.session.get(Project, project_id)

    if not project:
        return jsonify({"msg": "Project not found"}), 404
    if project.owner_id != current_user_id:
        return jsonify({"msg": "Unauthorized to view tasks for this project"}), 403

    tasks = ProjectTask.query.filter_by(project_id=project_id).all()
    tasks_data = [{
        "id": t.id, "title": t.title, "description": t.description, "status": t.status,
        "project_id": t.project_id, "assigned_to_id": t.assigned_to_id,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "task_definition_id": t.task_definition_id,
        "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat()
    } for t in tasks]
    return jsonify(tasks_data), 200

@task_api_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_user_id = get_jwt_identity()
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    project = db.session.get(Project, task.project_id)
    if not project or (task.assigned_to_id != current_user_id and project.owner_id != current_user_id):
        return jsonify({"msg": "Unauthorized to view this task"}), 403

    task_data = {
        "id": task.id, "title": task.title, "description": task.description, "status": task.status,
        "project_id": task.project_id, "assigned_to_id": task.assigned_to_id,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "task_definition_id": task.task_definition_id,
        "created_at": task.created_at.isoformat(), "updated_at": task.updated_at.isoformat()
    }
    return jsonify(task_data), 200

@task_api_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    task = db.session.get(ProjectTask, task_id)

    if not task:
        return jsonify({"msg": "Task not found"}), 404

    project = db.session.get(Project, task.project_id)
    if not project: # Should not happen if DB is consistent
         return jsonify({"msg": "Associated project not found"}), 500

    can_update_fully = project.owner_id == current_user_id
    can_update_status_descr = task.assigned_to_id == current_user_id or can_update_fully

    if not can_update_status_descr: # Basic check if user has any rights at all
        return jsonify({"msg": "Unauthorized to update this task"}), 403

    if can_update_fully:
        task.title = data.get('title', task.title)
        if 'assigned_to_id' in data:
            assignee_id = data.get('assigned_to_id')
            if assignee_id:
                assignee = db.session.get(User, assignee_id)
                if not assignee:
                    return jsonify({"msg": f"Assignee user with id {assignee_id} not found"}), 400
                task.assigned_to_id = assignee.id
            else: # Allow unassigning
                task.assigned_to_id = None
        if 'due_date' in data:
            task.due_date = parse_date(data.get('due_date'))

    # Fields updatable by assignee or owner
    if 'description' in data:
        task.description = data.get('description')
    if 'status' in data:
        task.status = data.get('status')

    db.session.commit()

    updated_task_data = {
        "id": task.id, "title": task.title, "description": task.description, "status": task.status,
        "project_id": task.project_id, "assigned_to_id": task.assigned_to_id,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "task_definition_id": task.task_definition_id,
        "created_at": task.created_at.isoformat(), "updated_at": task.updated_at.isoformat()
    }
    return jsonify(updated_task_data), 200
