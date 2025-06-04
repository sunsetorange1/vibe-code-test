# API Documentation - Task Management

This document outlines the API endpoints related to task management within projects.

## Task Management Routes

### Apply Baseline to Project

*   **POST** `/api/projects/{project_id}/apply_baseline/{baseline_id}`
*   **Description:** Applies all task definitions from a specified baseline to a project. Tasks that already exist in the project (matched by `task_definition_id`) will not be duplicated.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can apply to any project.
    *   `Consultant`: Can only apply to projects they own.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project to apply the baseline to.
    *   `baseline_id` (integer, required): The ID of the baseline to apply.
*   **Request Body:** None.
*   **Success Response:**
    *   **Code:** `201 Created` (if new tasks were added) or `200 OK` (if no new tasks were added).
    *   **Content:** Message indicating the outcome.
        ```json
        {
            "msg": "X tasks from baseline 'Baseline Name' applied to project 'Project Name'."
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Project, Baseline, or authenticated user not found.

### Create Ad-hoc Task for Project

*   **POST** `/api/projects/{project_id}/tasks`
*   **Description:** Creates a new ad-hoc (not from a baseline) task within a specific project.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can create tasks for any project.
    *   `Consultant`: Can only create tasks for projects they own.
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
    *   **Content:** The created task object. (Includes all fields listed in request body plus `id`, `project_id`, `task_definition_id`, `created_at`, `updated_at`).
*   **Error Responses:**
    *   `400 Bad Request`: Missing task title. Assignee user not found. Invalid date format.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Project or authenticated user not found.

### Get All Tasks for a Project

*   **GET** `/api/projects/{project_id}/tasks`
*   **Description:** Retrieves all tasks associated with a specific project. Access depends on role and project ownership/grants.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view tasks for any project.
    *   `Consultant`: Can only view tasks for projects they own.
    *   `Read-Only`: Access currently restricted if not project owner (pending grant system). Will receive 403 if not owner/admin.
*   **Path Parameters:**
    *   `project_id` (integer, required): The ID of the project whose tasks are to be retrieved.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of task objects. (Each object includes `id`, `title`, `description`, `status`, `project_id`, `assigned_to_id`, `due_date`, `task_definition_id`, `priority`, `due_date_reminder_sent`, `created_at`, `updated_at`).
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Project or authenticated user not found.

### Get Task by ID

*   **GET** `/api/tasks/{task_id}`
*   **Description:** Retrieves a specific task by its ID. Access depends on role and ownership/grants of the parent project.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view any task.
    *   `Consultant`: Can only view tasks in projects they own.
    *   `Read-Only`: Access currently restricted if not project owner (pending grant system). Will receive 403 if not owner/admin for the project.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to retrieve.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The task object. (Includes all fields as listed in "Get All Tasks").
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Task or authenticated user not found.
    *   `500 Internal Server Error`: Associated project not found.

### Update Task

*   **PUT** `/api/tasks/{task_id}`
*   **Description:** Updates an existing task.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can update any task.
    *   `Consultant`: Can only update tasks in projects they own.
    *   *(Note: Task assignees, if they are `Read-Only`, cannot update tasks via this endpoint under the current RBAC rules).*
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to update.
*   **Request Body:**
    ```json
    {
        "title": "string (optional)",
        "description": "string (optional)",
        "status": "string (optional)",
        "due_date": "string (optional, ISO format YYYY-MM-DD, can be null or empty to clear)",
        "assigned_to_id": "integer or null (optional)",
        "priority": "string (optional, e.g., 'High', 'Medium', 'Low')",
        "due_date_reminder_sent": "boolean (optional)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The updated task object. (Includes all fields).
*   **Error Responses:**
    *   `400 Bad Request`: Assignee user not found. Invalid date format. Invalid boolean value.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Task or authenticated user not found.
    *   `500 Internal Server Error`: Associated project not found.

*Note: No DELETE endpoint for tasks was found in `task_api_routes.py`.*
