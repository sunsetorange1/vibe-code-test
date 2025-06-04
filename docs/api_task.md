# API Documentation - Task Management

This document outlines the API endpoints related to task management within projects.

## Task Management Routes

### Apply Baseline to Project

*   **POST** `/api/projects/{project_id}/apply_baseline/{baseline_id}`
*   **Description:** Applies all task definitions from a specified baseline to a project. Tasks that already exist in the project (matched by `task_definition_id`) will not be duplicated. The user must be the owner of the project.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to apply the baseline to.
    *   `baseline_id` (integer, required): The ID of the baseline to apply.
*   **Request Body:** None.
*   **Success Response:**
    *   **Code:** `201 Created` (if new tasks were added) or `200 OK` (if no new tasks were added, e.g., baseline empty or tasks already exist).
    *   **Content:**
        ```json
        {
            "msg": "X tasks from baseline 'Baseline Name' applied to project 'Project Name'." // (201 Created)
        }
        ```
        or
        ```json
        {
            "msg": "All tasks from this baseline have already been applied to this project or the baseline is empty." // (200 OK)
        }
        ```
        or
        ```json
        {
            "msg": "Baseline has no task definitions to apply." // (200 OK)
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to modify this project (not the owner).
    *   `404 Not Found`: Project or Baseline with the given ID not found.

### Create Ad-hoc Task for Project

*   **POST** `/api/projects/{project_id}/tasks`
*   **Description:** Creates a new ad-hoc (not from a baseline) task within a specific project. The user must be the owner of the project.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to which this task will be added.
*   **Request Body:**
    ```json
    {
        "title": "string (required)",
        "description": "string (optional)",
        "status": "string (optional, default: 'pending')",
        "due_date": "string (optional, ISO format YYYY-MM-DD, e.g., '2024-03-15')",
        "assigned_to_id": "integer (optional, ID of the user to assign this task to)",
        "priority": "string (optional, default: 'Medium', e.g., 'High', 'Medium', 'Low')",
        "due_date_reminder_sent": "boolean (optional, default: false)"
    }
    ```
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:** The created task object.
        ```json
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "status": "string",
            "project_id": "integer",
            "assigned_to_id": "integer or null",
            "due_date": "string (ISO format YYYY-MM-DD) or null",
            "task_definition_id": null, // This is null for ad-hoc tasks
            "priority": "string",
            "due_date_reminder_sent": "boolean",
            "created_at": "string (ISO 8601 datetime)",
            "updated_at": "string (ISO 8601 datetime)"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing task title. Assignee user not found. Invalid date format.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to add tasks to this project (not the owner).
    *   `404 Not Found`: Project with the given ID not found.

### Get All Tasks for a Project

*   **GET** `/api/projects/{project_id}/tasks`
*   **Description:** Retrieves all tasks associated with a specific project. The user must be the owner of the project.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project whose tasks are to be retrieved.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of task objects.
        ```json
        [
            {
                "id": "integer",
                "title": "string",
                "description": "string",
                "status": "string",
                "project_id": "integer",
                "assigned_to_id": "integer or null",
                "due_date": "string (ISO format YYYY-MM-DD) or null",
                "task_definition_id": "integer or null",
                "priority": "string",
                "due_date_reminder_sent": "boolean",
                "created_at": "string (ISO 8601 datetime)",
                "updated_at": "string (ISO 8601 datetime)"
            }
            // ... more tasks
        ]
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to view tasks for this project (not the owner).
    *   `404 Not Found`: Project with the given ID not found.

### Get Task by ID

*   **GET** `/api/tasks/{task_id}`
*   **Description:** Retrieves a specific task by its ID. The user must be either the owner of the project to which the task belongs or the user assigned to the task.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to retrieve.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The task object.
        ```json
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "status": "string",
            "project_id": "integer",
            "assigned_to_id": "integer or null",
            "due_date": "string (ISO format YYYY-MM-DD) or null",
            "task_definition_id": "integer or null",
            "priority": "string",
            "due_date_reminder_sent": "boolean",
            "created_at": "string (ISO 8601 datetime)",
            "updated_at": "string (ISO 8601 datetime)"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to view this task.
    *   `404 Not Found`: Task with the given ID not found.

### Update Task

*   **PUT** `/api/tasks/{task_id}`
*   **Description:** Updates an existing task.
    *   The project owner can update all fields: `title`, `description`, `status`, `due_date`, `assigned_to_id`, `priority`, `due_date_reminder_sent`.
    *   The user assigned to the task can only update `description` and `status`.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to update.
*   **Request Body:**
    ```json
    {
        "title": "string (optional, owner only)",
        "description": "string (optional, owner or assignee)",
        "status": "string (optional, owner or assignee)",
        "due_date": "string (optional, ISO format YYYY-MM-DD, owner only, can be null or empty to clear)",
        "assigned_to_id": "integer or null (optional, owner only)",
        "priority": "string (optional, owner only, e.g., 'High', 'Medium', 'Low')",
        "due_date_reminder_sent": "boolean (optional, owner only)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The updated task object.
        ```json
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "status": "string",
            "project_id": "integer",
            "assigned_to_id": "integer or null",
            "due_date": "string (ISO format YYYY-MM-DD) or null",
            "task_definition_id": "integer or null",
            "priority": "string",
            "due_date_reminder_sent": "boolean",
            "created_at": "string (ISO 8601 datetime)",
            "updated_at": "string (ISO 8601 datetime)"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Assignee user not found. Invalid date format. Invalid boolean value for reminder.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to update this task or specific fields.
    *   `404 Not Found`: Task with the given ID not found.
    *   `500 Internal Server Error`: Associated project not found (should be rare).

*Note: No DELETE endpoint for tasks was found in `task_api_routes.py`.*
