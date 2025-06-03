import pytest
from app import create_app, db
from app.models import User
from config import Config
from cachelib.simple import SimpleCache # Import SimpleCache at module level

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = 'test-jwt-secret-key'

    # Flask-Session with CacheLib for tests
    SESSION_TYPE = 'cachelib'
    SESSION_CACHELIB = SimpleCache(threshold=500, default_timeout=300) # Initialize instance

    # Dummy Azure AD config
    AZURE_AD_CLIENT_ID = "test_client_id"
    AZURE_AD_CLIENT_SECRET = "test_client_secret"
    AZURE_AD_TENANT_ID = "test_tenant_id"
    # AZURE_AD_SCOPES is inherited from Config and should be a list there.

@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    with app.app_context():
        pass
    return app

@pytest.fixture(scope='function')
def client(app):
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def init_database(app):
    with app.app_context():
        yield db

@pytest.fixture(scope='function')
def new_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }

@pytest.fixture(scope='function')
def mock_azure_ad_user_info():
    return {
        "id": "mock_azure_oid_123",
        "displayName": "Azure Test User",
        "mail": "azure.test@example.com",
        "userPrincipalName": "azure.test@example.com"
    }

@pytest.fixture(scope='function')
def mock_azure_ad_graph_api_response(mock_azure_ad_user_info):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error {self.status_code}")
    return MockResponse(json_data=mock_azure_ad_user_info, status_code=200)
