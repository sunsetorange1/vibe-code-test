from . import db # From app/__init__.py
from app.models import User # Assuming User model is in app/models.py
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(64), nullable=False, default='active') # e.g., 'active', 'planning', 'in_progress', 'completed', 'on_hold'
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Assuming 'user' is the tablename for User model
    priority = db.Column(db.String(64), nullable=True, default='Medium')
    project_type = db.Column(db.String(128), nullable=True)

    owner = db.relationship('User', backref=db.backref('owned_projects', lazy='dynamic'))
    tasks = db.relationship('ProjectTask', backref='project', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Project {self.name}>'

class Baseline(db.Model):
    __tablename__ = 'baseline'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    creator = db.relationship('User', backref=db.backref('created_baselines', lazy='dynamic'))
    task_definitions = db.relationship('TaskDefinition', backref='baseline', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Baseline {self.name}>'

class TaskDefinition(db.Model):
    __tablename__ = 'task_definition'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(128), nullable=True)
    baseline_id = db.Column(db.Integer, db.ForeignKey('baseline.id'), nullable=False)
    # No direct relationship back to Baseline needed here as it's covered by Baseline.task_definitions

    def __repr__(self):
        return f'<TaskDefinition {self.title}>'

class ProjectTask(db.Model):
    __tablename__ = 'project_task'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    task_definition_id = db.Column(db.Integer, db.ForeignKey('task_definition.id'), nullable=True)

    title = db.Column(db.String(255), nullable=False) # Can be copied from TaskDefinition or custom
    description = db.Column(db.Text, nullable=True) # Can be copied or custom
    status = db.Column(db.String(64), nullable=False, default='pending') # 'pending', 'in_progress', 'review', 'completed', 'on_hold', 'cancelled'
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(64), nullable=True, default='Medium')
    due_date_reminder_sent = db.Column(db.Boolean, nullable=True, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee = db.relationship('User', backref=db.backref('assigned_tasks', lazy='dynamic'))
    task_definition = db.relationship('TaskDefinition', backref=db.backref('project_tasks', lazy='dynamic'))
    # project relationship is via backref from Project.tasks
    evidences = db.relationship('Evidence', backref='task', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ProjectTask {self.title}>'

class Evidence(db.Model):
    __tablename__ = 'evidence'
    id = db.Column(db.Integer, primary_key=True)
    project_task_id = db.Column(db.Integer, db.ForeignKey('project_task.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    file_name = db.Column(db.String(255), nullable=False) # Original name
    file_path = db.Column(db.String(1024), nullable=True) # Path in storage, or storage ID
    storage_identifier = db.Column(db.String(1024), nullable=True) # Specific key for cloud storage if used
    tool_type = db.Column(db.String(128), nullable=True) # e.g., 'Nessus', 'Burp', 'Nuclei', 'Manual', 'Screenshot'
    notes = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mime_type = db.Column(db.String(128), nullable=True)
    verified = db.Column(db.Boolean, nullable=True, default=False)

    uploader = db.relationship('User', backref=db.backref('uploaded_evidences', lazy='dynamic'))
    # task relationship is via backref from ProjectTask.evidences

    def __repr__(self):
        return f'<Evidence {self.file_name} for Task {self.project_task_id}>'
