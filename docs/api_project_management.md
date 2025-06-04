# API Documentation - Project Management

This document outlines the API endpoints related to project management.

## Project Management Routes

### Create Project

*   **POST** `/api/projects`
*   **Description:** Creates a new project.
*   **Authentication:** JWT Bearer token required.
*   **Request Body:**
    ```json
    {
        "name": "string (required)",
        "description": "string (optional)",
        "status": "string (optional, default: 'active')",
        "start_date": "string (optional, ISO format YYYY-MM-DD, e.g., '2023-10-26')",
        "end_date": "string (optional, ISO format YYYY-MM-DD, e.g., '2024-10-26')",
        "priority": "string (optional, default: 'Medium', e.g., 'High', 'Medium', 'Low')",
        "project_type": "string (optional, e.g., 'External Audit', 'Internal Review', 'Bug Bounty')"
    }
    ```
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:**
        ```json
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "status": "string",
            "start_date": "string (ISO format YYYY-MM-DD) or null",
            "end_date": "string (ISO format YYYY-MM-DD) or null",
            "owner_id": "integer",
            "priority": "string",
            "project_type": "string or null"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing project name. Invalid date format (must be YYYY-MM-DD).
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.

### Get All Projects for Current User

*   **GET** `/api/projects`
*   **Description:** Retrieves all projects owned by the currently authenticated user.
*   **Authentication:** JWT Bearer token required.
*   **Request Body:** None.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of project objects.
        ```json
        [
            {
                "id": "integer",
                "name": "string",
                "description": "string",
                "status": "string",
                "start_date": "string (ISO format YYYY-MM-DD) or null",
                "end_date": "string (ISO format YYYY-MM-DD) or null",
                "owner_id": "integer",
                "priority": "string",
                "project_type": "string or null"
            }
            // ... more projects
        ]
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.

### Get Project by ID

*   **GET** `/api/projects/{project_id}`
*   **Description:** Retrieves a specific project by its ID. The user must be the owner of the project.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to retrieve.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "status": "string",
            "start_date": "string (ISO format YYYY-MM-DD) or null",
            "end_date": "string (ISO format YYYY-MM-DD) or null",
            "owner_id": "integer",
            "priority": "string",
            "project_type": "string or null"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to access this project (not the owner).
    *   `404 Not Found`: Project with the given ID not found.

### Update Project

*   **PUT** `/api/projects/{project_id}`
*   **Description:** Updates an existing project. The user must be the owner of the project. Fields not provided in the request body will retain their current values.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to update.
*   **Request Body:**
    ```json
    {
        "name": "string (optional)",
        "description": "string (optional)",
        "status": "string (optional)",
        "start_date": "string (optional, ISO format YYYY-MM-DD, e.g., '2023-10-26', can be null or empty string to clear the date)",
        "end_date": "string (optional, ISO format YYYY-MM-DD, e.g., '2024-10-26', can be null or empty string to clear the date)",
        "priority": "string (optional, e.g., 'High', 'Medium', 'Low')",
        "project_type": "string (optional, e.g., 'External Audit', 'Internal Review', 'Bug Bounty', can be null or empty string to clear)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The updated project object.
        ```json
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "status": "string",
            "start_date": "string (ISO format YYYY-MM-DD) or null",
            "end_date": "string (ISO format YYYY-MM-DD) or null",
            "owner_id": "integer",
            "priority": "string",
            "project_type": "string or null"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Invalid date format (must be YYYY-MM-DD).
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to update this project (not the owner).
    *   `404 Not Found`: Project with the given ID not found.

### Delete Project

*   **DELETE** `/api/projects/{project_id}`
*   **Description:** Deletes a specific project by its ID. The user must be the owner of the project.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to delete.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "msg": "Project deleted successfully"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to delete this project (not the owner).
    *   `404 Not Found`: Project with the given ID not found.
