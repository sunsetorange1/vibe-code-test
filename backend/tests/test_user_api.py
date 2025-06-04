# backend/tests/test_user_api.py
import pytest
from app.models import User
from app import db # Actual db instance for direct manipulation

def test_get_users_unauthenticated(client):
    response = client.get('/api/users')
    assert response.status_code == 401 # Expecting 401 if JWT is missing or invalid

# Test with a consultant user, who should have access
def test_get_users_as_consultant(client, auth_consultant_user_and_headers, db_session, consultant_user):
    # consultant_user is the authenticated user from the fixture
    _, headers = auth_consultant_user_and_headers

    # Create another user to ensure a list is returned and to check multiple users
    user2_username = 'user2_for_user_api_test' # Make username unique for this test
    user2_email = 'user2_api@example.com'

    # Check if user2 already exists from a previous failed run or different test
    existing_user2 = User.query.filter_by(username=user2_username).first()
    if existing_user2:
        user2 = existing_user2
    else:
        user2 = User(username=user2_username, email=user2_email)
        user2.set_password('password123')
        db_session.session.add(user2)
        db_session.session.commit()

    response = client.get('/api/users', headers=headers)
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)

    # Verify that consultant_user (authenticated user) and user2 are in the response
    usernames_in_response = [u['username'] for u in data]
    emails_in_response = [u['email'] for u in data]

    assert consultant_user.username in usernames_in_response
    assert consultant_user.email in emails_in_response

    assert user2.username in usernames_in_response
    assert user2.email in emails_in_response

    # Check that sensitive information like password hashes is not present
    for user_data in data:
        assert 'password_hash' not in user_data # or just 'password' depending on model field name
        assert 'password' not in user_data

    # Clean up the specific user created in this test, if desired and if not handled by global teardown
    # db_session.session.delete(user2) # Be careful if this user was pre-existing
    # db_session.session.commit()
    # For now, relying on function-scoped db_session/client fixtures for teardown.
    # If user2 was pre-existing, deleting it here might affect other tests if they run in parallel or share state.
    # However, the check `if existing_user2:` handles this to some extent.
    # A truly robust approach would be to ensure user2 is deleted if it was created by this test.
    # For simplicity with current fixtures, we assume teardown handles it or that usernames are unique enough.

# Test with a read_only user, who should be denied access
def test_get_users_as_readonly_denied(client, auth_user_and_headers):
    # auth_user_and_headers provides a READ_ONLY user by default
    _, headers = auth_user_and_headers
    response = client.get('/api/users', headers=headers)
    assert response.status_code == 403
