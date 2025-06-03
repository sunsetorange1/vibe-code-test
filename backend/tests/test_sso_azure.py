import json
import time # Import time for token expiry
from unittest.mock import patch, MagicMock
from flask import session as flask_session, current_app # Import current_app to access config for scopes
from app.models import User
from app import db

def test_sso_azure_callback_new_user(client, mock_azure_ad_graph_api_response, mock_azure_ad_user_info):
    with client.session_transaction() as http_session:
        mock_token = {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
                "scope": current_app.config.get("AZURE_AD_SCOPES", []), # Already a list in config
            "expires_at": time.time() + 3600
        }
        http_session['azure_oauth_token'] = mock_token

    with patch('requests_oauthlib.oauth2_session.OAuth2Session.get') as mock_session_get:
        mock_session_get.return_value = mock_azure_ad_graph_api_response

        rv = client.get('/auth/sso/azure/callback')

        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}. Response: {rv.data.decode()}"
        json_data = rv.get_json()
        assert "access_token" in json_data

        user = User.query.filter_by(azure_oid=mock_azure_ad_user_info['id']).first()
        assert user is not None
        assert user.email == mock_azure_ad_user_info['mail']
        assert user.username == mock_azure_ad_user_info['displayName']
        assert user.password_hash is None

def test_sso_azure_callback_existing_user_link_oid(client, new_user_data, mock_azure_ad_graph_api_response, mock_azure_ad_user_info):
    local_user = User(
        username=new_user_data['username'],
        email=mock_azure_ad_user_info['mail']
    )
    local_user.set_password(new_user_data['password'])
    db.session.add(local_user)
    db.session.commit()
    original_user_id = local_user.id
    assert local_user.azure_oid is None

    with client.session_transaction() as http_session:
        mock_token = {"access_token": "mock", "token_type": "Bearer", "expires_in": 3600, "expires_at": time.time() + 3600, "scope": current_app.config.get("AZURE_AD_SCOPES", [])}
        http_session['azure_oauth_token'] = mock_token

    with patch('requests_oauthlib.oauth2_session.OAuth2Session.get') as mock_session_get:
        mock_session_get.return_value = mock_azure_ad_graph_api_response

        rv = client.get('/auth/sso/azure/callback')

        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}. Response: {rv.data.decode()}"
        retrieved_user = db.session.get(User, original_user_id)
        assert retrieved_user is not None
        assert retrieved_user.azure_oid == mock_azure_ad_user_info['id']
        assert retrieved_user.id == original_user_id

def test_sso_azure_callback_existing_sso_user_login(client, mock_azure_ad_graph_api_response, mock_azure_ad_user_info):
    sso_user = User(
        username=mock_azure_ad_user_info['displayName'],
        email=mock_azure_ad_user_info['mail'],
        azure_oid=mock_azure_ad_user_info['id']
    )
    db.session.add(sso_user)
    db.session.commit()

    with client.session_transaction() as http_session:
        mock_token = {"access_token": "mock", "token_type": "Bearer", "expires_in": 3600, "expires_at": time.time() + 3600, "scope": current_app.config.get("AZURE_AD_SCOPES", [])}
        http_session['azure_oauth_token'] = mock_token

    with patch('requests_oauthlib.oauth2_session.OAuth2Session.get') as mock_session_get:
        mock_session_get.return_value = mock_azure_ad_graph_api_response

        rv = client.get('/auth/sso/azure/callback')
        assert rv.status_code == 200, f"Expected 200, got {rv.status_code}. Response: {rv.data.decode()}"
        json_data = rv.get_json()
        assert "access_token" in json_data

def test_sso_azure_callback_unauthorized(client):
    with client.session_transaction() as http_session:
        if 'azure_oauth_token' in http_session: # Ensure not authorized
            del http_session['azure_oauth_token']

    rv = client.get('/auth/sso/azure/callback')
    assert rv.status_code == 401
    assert "Azure AD authorization failed" in rv.get_json()['msg']

def test_sso_azure_callback_graph_api_fails(client):
    with client.session_transaction() as http_session:
        mock_token = {"access_token": "mock", "token_type": "Bearer", "expires_in": 3600, "expires_at": time.time() + 3600, "scope": current_app.config.get("AZURE_AD_SCOPES", [])}
        http_session['azure_oauth_token'] = mock_token

    with patch('requests_oauthlib.oauth2_session.OAuth2Session.get') as mock_session_get:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Graph API Error")
        mock_response.json.return_value = {"error": "Simulated Graph API Error"}
        mock_session_get.return_value = mock_response

        rv = client.get('/auth/sso/azure/callback')
        assert rv.status_code == 500
        assert "An error occurred during SSO processing: Graph API Error" in rv.get_json()['msg']

def test_sso_azure_callback_missing_essential_info_from_graph(client, mock_azure_ad_user_info):
    incomplete_info = mock_azure_ad_user_info.copy()
    del incomplete_info['id']

    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self): return self.json_data
        def raise_for_status(self):
            if self.status_code >= 400: raise Exception(f"HTTP Error {self.status_code}")

    modified_graph_response = MockResponse(json_data=incomplete_info, status_code=200)

    with client.session_transaction() as http_session:
        mock_token = {"access_token": "mock", "token_type": "Bearer", "expires_in": 3600, "expires_at": time.time() + 3600, "scope": current_app.config.get("AZURE_AD_SCOPES", [])}
        http_session['azure_oauth_token'] = mock_token

    with patch('requests_oauthlib.oauth2_session.OAuth2Session.get') as mock_session_get:
        mock_session_get.return_value = modified_graph_response

        rv = client.get('/auth/sso/azure/callback')
        assert rv.status_code == 500
        assert "Could not retrieve essential user info" in rv.get_json()['msg']
