from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.project_models import Baseline, TaskDefinition
from app.models import User # For created_by_id

baseline_api_bp = Blueprint('baseline_api', __name__, url_prefix='/api')

# --- Baseline Endpoints ---
@baseline_api_bp.route('/baselines', methods=['POST'])
@jwt_required()
def create_baseline():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    if not data or not data.get('name'):
        return jsonify({"msg": "Missing baseline name"}), 400

    # Check for existing baseline name
    if Baseline.query.filter_by(name=data['name']).first():
        return jsonify({"msg": f"Baseline with name '{data['name']}' already exists"}), 400


    new_baseline = Baseline(
        name=data['name'],
        description=data.get('description'),
        created_by_id=current_user_id
    )
    db.session.add(new_baseline)
    db.session.commit()

    baseline_data = {
        "id": new_baseline.id,
        "name": new_baseline.name,
        "description": new_baseline.description,
        "created_by_id": new_baseline.created_by_id
    }
    return jsonify(baseline_data), 201

@baseline_api_bp.route('/baselines', methods=['GET'])
@jwt_required()
def get_baselines():
    baselines = Baseline.query.all()
    baselines_data = [{
        "id": b.id,
        "name": b.name,
        "description": b.description,
        "created_by_id": b.created_by_id
    } for b in baselines]
    return jsonify(baselines_data), 200

@baseline_api_bp.route('/baselines/<int:baseline_id>', methods=['GET'])
@jwt_required()
def get_baseline(baseline_id):
    baseline = db.session.get(Baseline, baseline_id) # Use db.session.get
    if not baseline:
        return jsonify({"msg": "Baseline not found"}), 404

    task_definitions_data = [{
        "id": td.id,
        "title": td.title,
        "description": td.description,
        "category": td.category
    } for td in baseline.task_definitions]

    baseline_data = {
        "id": baseline.id,
        "name": baseline.name,
        "description": baseline.description,
        "created_by_id": baseline.created_by_id,
        "task_definitions": task_definitions_data
    }
    return jsonify(baseline_data), 200

# --- TaskDefinition Endpoints (nested under baselines for creation) ---
@baseline_api_bp.route('/baselines/<int:baseline_id>/task_definitions', methods=['POST'])
@jwt_required()
def create_task_definition(baseline_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()

    baseline = db.session.get(Baseline, baseline_id)
    if not baseline:
        return jsonify({"msg": "Baseline not found"}), 404

    # Optional: Permission check - only creator can add tasks to baseline
    if baseline.created_by_id != current_user_id:
        return jsonify({"msg": "Unauthorized to add tasks to this baseline"}), 403

    if not data or not data.get('title'):
        return jsonify({"msg": "Missing task definition title"}), 400

    new_task_def = TaskDefinition(
        title=data['title'],
        description=data.get('description'),
        category=data.get('category'),
        baseline_id=baseline_id
    )
    db.session.add(new_task_def)
    db.session.commit()

    task_def_data = {
        "id": new_task_def.id,
        "title": new_task_def.title,
        "description": new_task_def.description,
        "category": new_task_def.category,
        "baseline_id": new_task_def.baseline_id
    }
    return jsonify(task_def_data), 201

# Standalone TaskDefinition endpoints for update/delete
@baseline_api_bp.route('/task_definitions/<int:task_def_id>', methods=['PUT'])
@jwt_required()
def update_task_definition(task_def_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()
    task_def = db.session.get(TaskDefinition, task_def_id)

    if not task_def:
        return jsonify({"msg": "Task definition not found"}), 404

    # Optional: Permission check - only creator of parent baseline can modify task_def
    if task_def.baseline.created_by_id != current_user_id:
         return jsonify({"msg": "Unauthorized to update this task definition"}), 403

    task_def.title = data.get('title', task_def.title)
    task_def.description = data.get('description', task_def.description)
    task_def.category = data.get('category', task_def.category)

    db.session.commit()

    updated_task_def_data = {
        "id": task_def.id,
        "title": task_def.title,
        "description": task_def.description,
        "category": task_def.category,
        "baseline_id": task_def.baseline_id
    }
    return jsonify(updated_task_def_data), 200

@baseline_api_bp.route('/task_definitions/<int:task_def_id>', methods=['DELETE'])
@jwt_required()
def delete_task_definition(task_def_id):
    current_user_id = get_jwt_identity()
    task_def = db.session.get(TaskDefinition, task_def_id)

    if not task_def:
        return jsonify({"msg": "Task definition not found"}), 404

    # Optional: Permission check - only creator of parent baseline can delete task_def
    if task_def.baseline.created_by_id != current_user_id:
         return jsonify({"msg": "Unauthorized to delete this task definition"}), 403

    db.session.delete(task_def)
    db.session.commit()
    return jsonify({"msg": "Task definition deleted successfully"}), 200
