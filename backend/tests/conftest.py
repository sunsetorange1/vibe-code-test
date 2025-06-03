import pytest
from app import create_app, db as actual_db # Rename to avoid conflict if a 'db' fixture is ever made
from app.models import User
from app.project_models import Project, Baseline, TaskDefinition, ProjectTask
from config import Config
from cachelib.simple import SimpleCache

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-jwt-secret-key'

    SESSION_TYPE = 'cachelib'
    SESSION_CACHELIB = SimpleCache(threshold=500, default_timeout=300)

    AZURE_AD_CLIENT_ID = "test_client_id"
    AZURE_AD_CLIENT_SECRET = "test_client_secret"
    AZURE_AD_TENANT_ID = "test_tenant_id"

@pytest.fixture(scope='session')
def app():
    app_instance = create_app(TestConfig)
    with app_instance.app_context(): # Ensure all extensions are initialized etc.
        pass
    return app_instance

@pytest.fixture(scope='function')
def client(app): # app fixture is session-scoped, client is function-scoped
    with app.app_context(): # Establish app context for this specific test function
        actual_db.create_all()
        with app.test_client() as test_client:
            yield test_client # Test client itself runs within app context
        actual_db.session.remove()
        actual_db.drop_all()

# This fixture is for tests that need db access but not necessarily the client
# e.g., model tests. It ensures app context and db setup/teardown.
@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        actual_db.create_all()
        yield actual_db # Provide the db object itself
        actual_db.session.remove()
        actual_db.drop_all()

@pytest.fixture(scope='function')
def new_user_data():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture(scope='function')
def another_user_data():
    return {"username": "otheruser", "email": "other@example.com", "password": "otherpassword"}

# This user is created once per test function if requested by an API test that needs an owner.
# API tests should use auth_user_and_headers which relies on this.
@pytest.fixture(scope='function')
def project_owner_user(db_session, new_user_data): # Depends on db_session for context
    user = User.query.filter_by(email=new_user_data['email']).first()
    if not user:
        user = User(username=new_user_data['username'], email=new_user_data['email'])
        user.set_password(new_user_data['password'])
        db_session.session.add(user)
        db_session.session.commit()
    return user

# For API tests needing authenticated headers and the user object
@pytest.fixture(scope='function')
def auth_user_and_headers(client, project_owner_user): # project_owner_user ensures user exists
    # No need to call /auth/register here as project_owner_user fixture handles user creation.
    login_rv = client.post('/auth/login', json={
        "username": project_owner_user.username,
        "password": "testpassword"
    })
    login_data = login_rv.get_json()
    assert "access_token" in login_data, f"Login failed in auth_user_and_headers: {login_rv.data.decode()}"
    access_token = login_data['access_token']
    headers = {"Authorization": f"Bearer {access_token}"}
    return project_owner_user, headers

# Simplified auth_headers just for cases where only headers are needed
@pytest.fixture(scope='function')
def auth_headers(auth_user_and_headers):
    _, headers = auth_user_and_headers
    return headers

@pytest.fixture(scope='function')
def sample_project(db_session, project_owner_user): # Depends on db_session
    project = Project(name="Test Project 1", owner_id=project_owner_user.id, description="A test project")
    db_session.session.add(project)
    db_session.session.commit()
    return project

@pytest.fixture(scope='function')
def sample_baseline(db_session, project_owner_user): # Depends on db_session
    baseline = Baseline(name="Test Baseline 1", created_by_id=project_owner_user.id, description="A test baseline")
    # Ensure name is unique for this test run, even though function scoped, good practice
    existing = Baseline.query.filter_by(name="Test Baseline 1").first()
    if existing: return existing # Avoid recreating if a previous test in same session didn't clean perfectly (shouldn't happen with function scope)
    db_session.session.add(baseline)
    db_session.session.commit()
    return baseline

@pytest.fixture(scope='function')
def sample_task_definition(db_session, sample_baseline): # Depends on db_session
    td = TaskDefinition(title="Test Task Def 1", baseline_id=sample_baseline.id, category="Test Category")
    db_session.session.add(td)
    db_session.session.commit()
    return td

@pytest.fixture(scope='function')
def sample_project_task(db_session, sample_project, project_owner_user):  # Depends on db_session
    task = ProjectTask(
        title="Test Project Task 1",
        project_id=sample_project.id,
        assigned_to_id=project_owner_user.id
    )
    db_session.session.add(task)
    db_session.session.commit()
    return task

# Azure AD mock fixtures (unchanged from previous correct version)
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
