# API Documentation - Project Management

This document outlines the API endpoints related to project management.

## Project Management Routes

### Create Project

*   **POST** `/api/projects`
*   **Description:** Creates a new project. The project's `owner_id` will be set to the ID of the authenticated user making the request.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
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
    *   `403 Forbidden`: User's role is not authorized (e.g., `Read-Only` user attempting to create).

### Get All Projects

*   **GET** `/api/projects`
*   **Description:** Retrieves a list of projects based on the user's role.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view all projects.
    *   `Consultant`: Can view only projects they own.
    *   `Read-Only`: Currently views no projects via this general list (pending grant system implementation).
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
    *   `404 Not Found`: If the authenticated user is not found in the database.

### Get Project by ID

*   **GET** `/api/projects/{project_id}`
*   **Description:** Retrieves a specific project by its ID. Access depends on user role and project ownership (or future grants).
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view any project.
    *   `Consultant`: Can only view projects they own.
    *   `Read-Only`: Currently denied access to specific projects via this endpoint unless they own it (which is unlikely for a strict RO role) or a future grant system allows it. Will receive a 403 if not owner/admin.
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
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Project with the given ID not found, or authenticated user not found in DB.

### Update Project

*   **PUT** `/api/projects/{project_id}`
*   **Description:** Updates an existing project.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can update any project.
    *   `Consultant`: Can only update projects they own.
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
    *   `403 Forbidden`: User's role not permitted, or Consultant attempting to update a project they don't own.
    *   `404 Not Found`: Project with the given ID not found.

### Delete Project

*   **DELETE** `/api/projects/{project_id}`
*   **Description:** Deletes a specific project by its ID.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator` only.
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
    *   `403 Forbidden`: User's role is not `Administrator`.
    *   `404 Not Found`: Project with the given ID not found.
