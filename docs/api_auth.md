# API Documentation - Authentication

This document outlines the API endpoints related to user authentication and authorization.

## Authentication Routes

### Register New User

*   **POST** `/auth/register`
*   **Description:** Creates a new user account.
*   **Authentication:** None required.
*   **Request Body:**
    ```json
    {
        "username": "string (required)",
        "email": "string (required)",
        "password": "string (required)"
    }
    ```
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:**
        ```json
        {
            "msg": "User created successfully",
            "user": {
                "id": "integer",
                "username": "string",
                "email": "string"
            }
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing username, email, or password. Username or email already exists. Missing JSON in request.
    *   `415 Unsupported Media Type`: Request body is not JSON.

### Login User

*   **POST** `/auth/login`
*   **Description:** Authenticates an existing user and returns a JWT access token.
*   **Authentication:** None required.
*   **Request Body:**
    ```json
    {
        "username": "string (required)",
        "password": "string (required)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "access_token": "string (JWT)"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing username or password. Missing JSON in request.
    *   `401 Unauthorized`: Bad username or password.
    *   `415 Unsupported Media Type`: Request body is not JSON.

### Azure AD SSO Callback

*   **GET** `/auth/sso/azure/callback`
*   **Description:** Handles the callback from Azure AD after single sign-on (SSO) authentication. If successful, it finds an existing user by Azure Object ID (OID) or email, or creates a new user if one doesn't exist. It then issues a JWT access token for the application.
*   **Authentication:** None directly (relies on Azure AD session and the redirect from Azure).
*   **Request Body:** None.
*   **Query Parameters:** Azure AD will append query parameters like `code`, `state`, `session_state` as part of the OAuth 2.0 authorization code flow. These are handled by the `flask-dance` library.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "access_token": "string (JWT)"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: Azure AD authorization failed or was denied by the user.
    *   `500 Internal Server Error`: Could not retrieve essential user information from Microsoft Graph API (e.g., OID or email missing). Error creating a user profile due to username conflict or other database issues. Other unexpected errors during SSO processing.
