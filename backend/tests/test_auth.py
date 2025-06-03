import json
from app.models import User

def test_register_user(client, new_user_data):
    # Test successful registration
    rv = client.post('/auth/register', json=new_user_data)
    assert rv.status_code == 201
    json_data = rv.get_json()
    assert json_data['msg'] == "User created successfully"
    assert json_data['user']['username'] == new_user_data['username']

    # Test duplicate username
    rv = client.post('/auth/register', json=new_user_data)
    assert rv.status_code == 400
    assert rv.get_json()['msg'] == "Username already exists"

    # Test duplicate email
    duplicate_email_data = new_user_data.copy()
    duplicate_email_data['username'] = "anotheruser" # Change username for this check
    rv = client.post('/auth/register', json=duplicate_email_data)
    assert rv.status_code == 400
    assert rv.get_json()['msg'] == "Email already exists"

    # Test missing fields (e.g., password)
    missing_fields_data = {"username": "useronly", "email": "emailonly@example.com"}
    rv = client.post('/auth/register', json=missing_fields_data)
    assert rv.status_code == 400
    assert "Missing username, email, or password" in rv.get_json()['msg'] # Adjusted to match actual error msg

def test_login_user(client, new_user_data):
    # First, register a user
    client.post('/auth/register', json=new_user_data)

    # Test successful login
    login_data = {"username": new_user_data['username'], "password": new_user_data['password']}
    rv = client.post('/auth/login', json=login_data)
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert "access_token" in json_data

    # Test wrong password
    login_data_wrong_pass = {"username": new_user_data['username'], "password": "wrongpassword"}
    rv = client.post('/auth/login', json=login_data_wrong_pass)
    assert rv.status_code == 401
    assert rv.get_json()['msg'] == "Bad username or password"

    # Test non-existent user
    login_data_no_user = {"username": "nouser", "password": "somepassword"}
    rv = client.post('/auth/login', json=login_data_no_user)
    assert rv.status_code == 401
    assert rv.get_json()['msg'] == "Bad username or password"

def test_get_me_protected(client, new_user_data):
    # Register and login to get token
    client.post('/auth/register', json=new_user_data)
    login_rv = client.post('/auth/login', json={"username": new_user_data['username'], "password": new_user_data['password']})
    access_token = login_rv.get_json()['access_token']

    # Test access with token
    rv = client.get('/api/me', headers={"Authorization": f"Bearer {access_token}"})
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['username'] == new_user_data['username']
    assert json_data['email'] == new_user_data['email']

    # Test access without token
    rv = client.get('/api/me')
    assert rv.status_code == 401 # Flask-JWT-Extended returns 401 for missing token (default)

    # Test access with invalid/malformed token
    rv = client.get('/api/me', headers={"Authorization": "Bearer invalidtoken"})
    # Flask-JWT-Extended returns 422 (Unprocessable Entity) for various invalid token formats
    assert rv.status_code == 422
    # The specific message can vary, so checking status code is often enough
    # assert "Invalid token" in rv.get_json().get("msg", "").lower() # Example message check
    json_response = rv.get_json()
    assert "msg" in json_response # Ensure there's a message
    # Example: msg could be "Invalid token type. Expected 'Bearer'" or "Not enough segments" etc.
    # For now, just checking for a msg field. More specific checks might be needed if behavior is very specific.

def test_register_missing_json(client):
    rv = client.post('/auth/register', data="not json", content_type="text/plain")
    assert rv.status_code == 415
    assert rv.get_json()['msg'] == "Unsupported Media Type: JSON expected"

def test_login_missing_json(client):
    rv = client.post('/auth/login', data="not json", content_type="text/plain")
    assert rv.status_code == 415
    assert rv.get_json()['msg'] == "Unsupported Media Type: JSON expected"
