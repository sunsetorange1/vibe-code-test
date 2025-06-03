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
