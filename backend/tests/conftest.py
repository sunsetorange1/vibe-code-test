import pytest
from app import create_app, db
from app.models import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for testing forms if any; not strictly needed here but good practice
    JWT_SECRET_KEY = 'test-jwt-secret-key' # Consistent JWT secret for tests

@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    # Establish an application context before accessing the logger.
    with app.app_context():
        # You can configure logging further here if needed for tests.
        # For now, just ensuring the context is active.
        pass
    return app

@pytest.fixture(scope='function') # Changed to function scope for db isolation
def client(app):
    with app.app_context(): # Ensure app context for db operations
        db.create_all() # Create tables for each test function
        with app.test_client() as client:
            yield client
        db.session.remove() # Clean up session
        db.drop_all()       # Drop tables after each test function

@pytest.fixture(scope='function')
def init_database(app): # No client needed, just app context
    with app.app_context():
        # db.create_all() # Done in client fixture now
        yield db # provide the db object if needed by tests
        # db.session.remove() # Handled by client fixture's teardown
        # db.drop_all()       # Handled by client fixture's teardown

@pytest.fixture(scope='function')
def new_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }
