# API Authentication and User Endpoints

This document outlines the authentication endpoints and related user profile API.

## Authentication Endpoints

All authentication endpoints are prefixed with `/auth`.

### 1. User Registration

*   **Endpoint:** `POST /auth/register`
*   **Description:** Registers a new user.
*   **Request Body (JSON):**
    ```json
    {
        "username": "yourusername",
        "email": "user@example.com",
        "password": "yourpassword"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
        "msg": "User created successfully",
        "user": {
            "id": 1,
            "username": "yourusername",
            "email": "user@example.com"
        }
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing JSON, or missing `username`, `email`, or `password`.
        ```json
        {"msg": "Missing JSON in request"}
        ```
        ```json
        {"msg": "Missing username, email, or password"}
        ```
    *   `400 Bad Request`: Username or email already exists.
        ```json
        {"msg": "Username already exists"}
        ```
        ```json
        {"msg": "Email already exists"}
        ```

### 2. User Login

*   **Endpoint:** `POST /auth/login`
*   **Description:** Authenticates an existing user and returns a JWT.
*   **Request Body (JSON):**
    ```json
    {
        "username": "yourusername",
        "password": "yourpassword"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // JWT string
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing JSON, or missing `username` or `password`.
    *   `401 Unauthorized`: Bad username or password.
        ```json
        {"msg": "Bad username or password"}
        ```

## User Profile API

Endpoints related to user profiles are prefixed with `/api`. These endpoints require authentication (a valid JWT Bearer token in the `Authorization` header).

### 1. Get Current User Profile

*   **Endpoint:** `GET /api/me`
*   **Description:** Retrieves the profile information of the currently authenticated user.
*   **Headers:**
    *   `Authorization: Bearer <your_access_token>`
*   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "username": "yourusername",
        "email": "user@example.com"
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: Missing or invalid JWT.
    *   `404 Not Found`: User associated with JWT not found (should be rare if token is valid).

## Microsoft Azure AD SSO

These endpoints facilitate user authentication via Microsoft Azure Active Directory.

### 1. Initiate SSO Login

*   **Endpoint:** `GET /auth/sso/azure/login`
*   **Description:** Initiates the Microsoft Azure AD authentication flow. The user's browser will be redirected to the Microsoft login page. This URL is automatically provided by the Flask-Dance Azure blueprint.
*   **Request Parameters:** None.
*   **Response:** A redirect (302) to Microsoft's authentication service.

### 2. SSO Callback

*   **Endpoint:** `GET /auth/sso/azure/callback`
*   **Description:** This is the callback URL that Azure AD redirects to after the user authenticates with Microsoft. The application backend handles the token exchange with Azure AD, fetches user information, creates or links the user account in the local database, and then issues a local application JWT.
    *This endpoint is primarily handled by the browser redirecting from Microsoft and is not typically called directly by a client API consumer after the initial setup.*
*   **Success Response (200 OK, after successful internal processing and JWT issuance):**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // Local application JWT string
    }
    ```
    *(Note: In a full web application, this endpoint might redirect the user to a frontend page, possibly embedding the token in the URL or a secure cookie, rather than returning JSON directly. The current implementation returns JSON for consistency with the local login endpoint).*
*   **Error Responses:**
    *   `401 Unauthorized`: If Azure AD authorization failed or was denied by the user.
        ```json
        {"msg": "Azure AD authorization failed. Please try again."}
        ```
    *   `500 Internal Server Error`: If there was an issue fetching user information from Microsoft, creating/linking the user, or other server-side errors during processing.
        ```json
        {"msg": "Could not retrieve essential user info from Microsoft. Please try again."}
        ```
        ```json
        {"msg": "An error occurred during SSO processing: <specific_error_details>"}
        ```
