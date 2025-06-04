import pytest
from app import create_app, db as actual_db
from app.models import User, ADMIN, CONSULTANT, READ_ONLY # Import role constants
from app.project_models import Project, Baseline, TaskDefinition, ProjectTask
from config import Config
from cachelib.simple import SimpleCache
import tempfile
import shutil
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for simpler form testing if applicable
    JWT_SECRET_KEY = 'test-jwt-secret-key' # Consistent JWT secret for tests
    SESSION_TYPE = 'cachelib'
    SESSION_CACHELIB = SimpleCache(threshold=500, default_timeout=300)
    AZURE_AD_CLIENT_ID = "test_client_id"
    AZURE_AD_CLIENT_SECRET = "test_client_secret"
    AZURE_AD_TENANT_ID = "test_tenant_id"
    # Ensure UPLOAD_FOLDER is set for tests if file uploads are involved
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_uploads')


@pytest.fixture(scope='session')
def app():
    app_instance = create_app(TestConfig)
    # Create the UPLOAD_FOLDER if it doesn't exist, for this test session
    if not os.path.exists(app_instance.config['UPLOAD_FOLDER']):
        os.makedirs(app_instance.config['UPLOAD_FOLDER'])

    with app_instance.app_context():
        pass # Extensions are initialized here
    return app_instance

@pytest.fixture(scope='function')
def client(app):
    with app.app_context():
        actual_db.create_all()
        with app.test_client() as test_client:
            yield test_client
        actual_db.session.remove()
        actual_db.drop_all()
        # Clean up test_uploads folder after each test function if needed, or do it session-wide
        # For now, let it persist per session, cleaned by session fixture if added.

@pytest.fixture(scope='function')
def db_session(app): # For model tests or direct db interaction
    with app.app_context():
        actual_db.create_all()
        yield actual_db
        actual_db.session.remove()
        actual_db.drop_all()

# --- User and Auth Fixtures ---

@pytest.fixture(scope='function')
def default_user_data(): # Renamed from new_user_data for clarity
    return {"username": "defaultuser", "email": "default@example.com", "password": "password"}

@pytest.fixture(scope='function')
def admin_user_data():
    return {"username": "adminuser", "email": "admin@example.com", "password": "adminpassword"}

@pytest.fixture(scope='function')
def consultant_user_data():
    return {"username": "consultantuser", "email": "consultant@example.com", "password": "consultantpassword"}

@pytest.fixture(scope='function')
def another_user_data(): # For a generic second user, likely READ_ONLY by default
    return {"username": "otheruser", "email": "other@example.com", "password": "otherpassword"}

def _create_user_if_not_exists(db_session, userdata, role=READ_ONLY):
    user = User.query.filter_by(email=userdata['email']).first()
    if not user:
        user = User(username=userdata['username'], email=userdata['email'], role=role)
        user.set_password(userdata['password'])
        db_session.session.add(user)
        db_session.session.commit()
    elif user.role != role: # Ensure existing user has the specified role for the test
        user.role = role
        db_session.session.commit()
    return user

@pytest.fixture(scope='function')
def default_read_only_user(db_session, default_user_data): # Formerly project_owner_user
    return _create_user_if_not_exists(db_session, default_user_data, READ_ONLY)

@pytest.fixture(scope='function')
def admin_user(db_session, admin_user_data):
    return _create_user_if_not_exists(db_session, admin_user_data, ADMIN)

@pytest.fixture(scope='function')
def consultant_user(db_session, consultant_user_data):
    return _create_user_if_not_exists(db_session, consultant_user_data, CONSULTANT)

def _get_auth_headers_for_user(client, user, password):
    login_rv = client.post('/auth/login', json={"username": user.username, "password": password})
    login_data = login_rv.get_json()
    assert "access_token" in login_data, f"Login failed for {user.username}: {login_rv.data.decode()}"
    access_token = login_data['access_token']
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope='function')
def auth_user_and_headers(client, default_read_only_user, default_user_data): # This now represents a READ_ONLY user
    headers = _get_auth_headers_for_user(client, default_read_only_user, default_user_data['password'])
    return default_read_only_user, headers

@pytest.fixture(scope='function')
def auth_admin_user_and_headers(client, admin_user, admin_user_data):
    headers = _get_auth_headers_for_user(client, admin_user, admin_user_data['password'])
    return admin_user, headers

@pytest.fixture(scope='function')
def auth_consultant_user_and_headers(client, consultant_user, consultant_user_data):
    headers = _get_auth_headers_for_user(client, consultant_user, consultant_user_data['password'])
    return consultant_user, headers

# Simplified auth_headers for READ_ONLY user (matches old auth_headers behavior)
@pytest.fixture(scope='function')
def auth_headers(auth_user_and_headers):
    _, headers = auth_user_and_headers
    return headers

# --- Sample Data Fixtures (adjust ownership) ---

@pytest.fixture(scope='function')
def sample_project(db_session, consultant_user): # Default project owned by a consultant
    project = Project.query.filter_by(name="Test Project 1", owner_id=consultant_user.id).first()
    if not project:
        project = Project(name="Test Project 1", owner_id=consultant_user.id, description="A test project by consultant")
        db_session.session.add(project)
        db_session.session.commit()
    return project

@pytest.fixture(scope='function')
def sample_baseline(db_session, consultant_user): # Default baseline created by a consultant
    baseline = Baseline.query.filter_by(name="Test Baseline 1", created_by_id=consultant_user.id).first()
    if not baseline:
        baseline = Baseline(name="Test Baseline 1", created_by_id=consultant_user.id, description="A test baseline by consultant")
        db_session.session.add(baseline)
        db_session.session.commit()
    return baseline

@pytest.fixture(scope='function')
def sample_task_definition(db_session, sample_baseline):
    td = TaskDefinition.query.filter_by(title="Test Task Def 1", baseline_id=sample_baseline.id).first()
    if not td:
        td = TaskDefinition(title="Test Task Def 1", baseline_id=sample_baseline.id, category="Test Category")
        db_session.session.add(td)
        db_session.session.commit()
    return td

@pytest.fixture(scope='function')
def sample_project_task(db_session, sample_project, consultant_user):  # Task in consultant's project, assigned to consultant
    task = ProjectTask.query.filter_by(title="Test Project Task 1", project_id=sample_project.id).first()
    if not task:
        task = ProjectTask(
            title="Test Project Task 1",
            project_id=sample_project.id,
            assigned_to_id=consultant_user.id # Default task assigned to the consultant owner
        )
        db_session.session.add(task)
        db_session.session.commit()
    return task

# --- Mocking and Utility Fixtures ---

@pytest.fixture(scope='function')
def mock_azure_ad_user_info():
    return {"id": "mock_azure_oid_123", "displayName": "Azure Test User", "mail": "azure.test@example.com", "userPrincipalName": "azure.test@example.com"}

@pytest.fixture(scope='function')
def mock_azure_ad_graph_api_response(mock_azure_ad_user_info):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data; self.status_code = status_code
        def json(self): return self.json_data
        def raise_for_status(self):
            if self.status_code >= 400: raise Exception(f"HTTP Error {self.status_code}")
    return MockResponse(json_data=mock_azure_ad_user_info, status_code=200)

@pytest.fixture(scope='function')
def temp_upload_folder(app):
    original_upload_folder = app.config.get('UPLOAD_FOLDER')
    temp_dir_base = tempfile.mkdtemp(prefix="pytest_temp_uploads_")
    app.config['UPLOAD_FOLDER'] = temp_dir_base
    yield temp_dir_base
    app.config['UPLOAD_FOLDER'] = original_upload_folder
    shutil.rmtree(temp_dir_base)

@pytest.fixture
def mock_file_storage(request):
    params = getattr(request, "param", {})
    filename = params.get("filename", "test_file.txt")
    content = params.get("content", b"Hello, world!")
    content_type = params.get("content_type", "text/plain")
    stream = BytesIO(content)
    fs = FileStorage(stream=stream, filename=filename, content_type=content_type)
    return fs
