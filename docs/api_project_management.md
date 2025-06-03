# API - Project and Task Management

This document outlines the API endpoints for managing projects, baselines, tasks, and evidence. All endpoints require JWT authentication.

## Table of Contents
- [Projects](#projects)
- [Baselines (Templates)](#baselines-templates)
- [Task Definitions](#task-definitions)
- [Project Tasks](#project-tasks)
- [Evidence](#evidence)

---

## Projects

Endpoints for managing pentest projects. Prefix: `/api/projects`

### 1. Create Project
*   **Endpoint:** `POST /api/projects`
*   **Description:** Creates a new project. The authenticated user becomes the owner.
*   **Request Body (JSON):**
    ```json
    {
        "name": "Project Alpha Q1",
        "description": "Web application security assessment for Alpha service.",
        "status": "planning", // Optional, default: 'active'. Others: 'planning', 'in_progress', 'completed', 'on_hold'
        "start_date": "2024-01-15", // Optional, ISO format (YYYY-MM-DD)
        "end_date": "2024-02-28"   // Optional, ISO format (YYYY-MM-DD)
    }
    ```
*   **Success Response (201 Created):** Project object (see Get Project Details).
*   **Error Responses:** `400 Bad Request` (e.g., missing name), `401 Unauthorized`.

### 2. List Projects
*   **Endpoint:** `GET /api/projects`
*   **Description:** Lists projects owned by the authenticated user.
*   **Success Response (200 OK):** Array of project objects.
    ```json
    [
        {
            "id": 1,
            "name": "Project Alpha Q1",
            "description": "...",
            "status": "planning",
            "start_date": "2024-01-15",
            "end_date": "2024-02-28",
            "owner_id": 123
        }
        // ... more projects
    ]
    ```
*   **Error Responses:** `401 Unauthorized`.

### 3. Get Project Details
*   **Endpoint:** `GET /api/projects/<project_id>`
*   **Description:** Retrieves details of a specific project. User must be the owner.
*   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Project Alpha Q1",
        "description": "...",
        "status": "planning",
        "start_date": "2024-01-15",
        "end_date": "2024-02-28",
        "owner_id": 123
        // tasks might be included here in future or via separate endpoint
    }
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 4. Update Project
*   **Endpoint:** `PUT /api/projects/<project_id>`
*   **Description:** Updates details of a specific project. User must be the owner.
*   **Request Body (JSON):** Partial project object with fields to update.
    ```json
    {
        "name": "Project Alpha Q1 (Revised)",
        "status": "in_progress"
    }
    ```
*   **Success Response (200 OK):** Updated project object.
*   **Error Responses:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 5. Delete Project
*   **Endpoint:** `DELETE /api/projects/<project_id>`
*   **Description:** Deletes a specific project. User must be the owner. Associated tasks and evidence will be cascade deleted.
*   **Success Response (200 OK):**
    ```json
    {"msg": "Project deleted successfully"}
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

---

## Baselines (Templates)

Endpoints for managing reusable baseline templates of tasks. Prefix: `/api`

### 1. Create Baseline
*   **Endpoint:** `POST /api/baselines`
*   **Description:** Creates a new baseline template. The authenticated user is set as the creator.
*   **Request Body (JSON):**
    ```json
    {
        "name": "Standard Web App Pentest Baseline", // Must be unique
        "description": "Common tasks for web application penetration testing."
    }
    ```
*   **Success Response (201 Created):** Baseline object.
*   **Error Responses:** `400 Bad Request` (e.g., missing or non-unique name), `401 Unauthorized`.

### 2. List Baselines
*   **Endpoint:** `GET /api/baselines`
*   **Description:** Lists all available baseline templates.
*   **Success Response (200 OK):** Array of baseline objects.
    ```json
    [
        {
            "id": 1,
            "name": "Standard Web App Pentest Baseline",
            "description": "...",
            "created_by_id": 123
        }
    ]
    ```
*   **Error Responses:** `401 Unauthorized`.

### 3. Get Baseline Details
*   **Endpoint:** `GET /api/baselines/<baseline_id>`
*   **Description:** Retrieves details of a specific baseline, including its task definitions.
*   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Standard Web App Pentest Baseline",
        "description": "...",
        "created_by_id": 123,
        "task_definitions": [
            {
                "id": 10,
                "title": "Perform XSS Testing",
                "description": "...",
                "category": "Web Application"
            }
            // ... more task definitions
        ]
    }
    ```
*   **Error Responses:** `401 Unauthorized`, `404 Not Found`.

---

## Task Definitions

Endpoints for managing task definitions within baselines. Prefix: `/api`

### 1. Add Task Definition to Baseline
*   **Endpoint:** `POST /api/baselines/<baseline_id>/task_definitions`
*   **Description:** Adds a new task definition to a specified baseline. User must be the creator of the baseline.
*   **Request Body (JSON):**
    ```json
    {
        "title": "SQL Injection Testing",
        "description": "Test for SQL injection vulnerabilities.",
        "category": "Web Application"
    }
    ```
*   **Success Response (201 Created):** TaskDefinition object.
*   **Error Responses:** `400 Bad Request` (e.g., missing title), `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (baseline).

### 2. Update Task Definition
*   **Endpoint:** `PUT /api/task_definitions/<task_def_id>`
*   **Description:** Updates an existing task definition. User must be the creator of the parent baseline.
*   **Request Body (JSON):** Partial TaskDefinition object.
*   **Success Response (200 OK):** Updated TaskDefinition object.
*   **Error Responses:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 3. Delete Task Definition
*   **Endpoint:** `DELETE /api/task_definitions/<task_def_id>`
*   **Description:** Deletes a task definition. User must be the creator of the parent baseline.
*   **Success Response (200 OK):**
    ```json
    {"msg": "Task definition deleted successfully"}
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

---

## Project Tasks

Endpoints for managing tasks within specific projects. Prefix: `/api`

### 1. Apply Baseline to Project
*   **Endpoint:** `POST /api/projects/<project_id>/apply_baseline/<baseline_id>`
*   **Description:** Creates project tasks for the given project from all task definitions in the specified baseline. Skips task definitions already applied to the project. User must be the project owner.
*   **Success Response (201 Created / 200 OK):**
    ```json
    // 201 if new tasks were created
    {"msg": "X tasks from baseline 'Y' applied to project 'Z'."}
    // 200 if baseline has no tasks or all tasks already applied
    {"msg": "Baseline has no task definitions to apply."}
    {"msg": "All tasks from this baseline have already been applied to this project."}
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (project or baseline).

### 2. Create Ad-Hoc Task in Project
*   **Endpoint:** `POST /api/projects/<project_id>/tasks`
*   **Description:** Creates a new ad-hoc (custom) task for a project. User must be the project owner.
*   **Request Body (JSON):**
    ```json
    {
        "title": "Perform manual review of new login feature",
        "description": "Focus on session management and input validation.",
        "status": "pending", // Optional, default: 'pending'
        "assigned_to_id": 456, // Optional, user ID
        "due_date": "2024-03-10" // Optional, ISO format
    }
    ```
*   **Success Response (201 Created):** ProjectTask object (see Get Project Task Details).
*   **Error Responses:** `400 Bad Request` (e.g., missing title, invalid assigned_to_id), `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (project).

### 3. List Tasks for Project
*   **Endpoint:** `GET /api/projects/<project_id>/tasks`
*   **Description:** Lists all tasks for a specific project. User must be the project owner.
*   **Success Response (200 OK):** Array of ProjectTask objects.
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 4. Get Project Task Details
*   **Endpoint:** `GET /api/tasks/<task_id>`
*   **Description:** Retrieves details of a specific project task. User must be the project owner or the assignee of the task.
*   **Success Response (200 OK):**
    ```json
    {
        "id": 101,
        "project_id": 1,
        "task_definition_id": 10, // Optional
        "title": "Perform XSS Testing",
        "description": "...",
        "status": "in_progress",
        "assigned_to_id": 456,
        "due_date": "2024-03-01",
        "created_at": "2024-01-20T10:00:00Z",
        "updated_at": "2024-01-25T14:30:00Z"
    }
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 5. Update Project Task
*   **Endpoint:** `PUT /api/tasks/<task_id>`
*   **Description:** Updates details of a specific project task.
        *   Project owner can update: `title`, `description`, `status`, `assigned_to_id`, `due_date`.
        *   Task assignee can update: `description`, `status`.
*   **Request Body (JSON):** Partial ProjectTask object.
*   **Success Response (200 OK):** Updated ProjectTask object.
*   **Error Responses:** `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

---

## Evidence

Endpoints for managing evidence (e.g., scan outputs, notes, files) associated with project tasks. Prefix: `/api`

### 1. Add Evidence to Task
*   **Endpoint:** `POST /api/tasks/<task_id>/evidence`
*   **Description:** Adds an evidence record to a specific task, including uploading an associated file. User must be project owner or task assignee.
*   **Request Body (multipart/form-data):**
    *   `file` (file part): The evidence file to upload (e.g., image, XML, TXT, PDF).
    *   `tool_type` (form field, optional): The type of tool that generated the evidence (e.g., "Nessus", "Manual").
    *   `notes` (form field, optional): Any notes about the evidence.
    *   *The `file_name` for the evidence record will be derived from the uploaded file's name (sanitized by the server).*
*   **Validations:**
    *   File type must be one of the allowed extensions (e.g., `txt, pdf, png, jpg, xml, json, log, nessus, burp` - see server config for full list).
    *   File size must not exceed the server's configured limit (e.g., 16MB - see server config).
*   **Success Response (201 Created):** Evidence object.
    ```json
    {
        "id": 1002,
        "project_task_id": 101,
        "uploaded_by_id": 123,
        "file_name": "sanitized_original_filename.xml", // Original filename, sanitized for storage as metadata
        "file_path": "projects/1/tasks/101/tool_type_or_evidence_uuid.xml", // Internal storage path relative to UPLOAD_FOLDER
        "storage_identifier": "projects/1/tasks/101/tool_type_or_evidence_uuid.xml", // Identifier for storage (same as file_path for local)
        "tool_type": "Nessus",
        "notes": "Scan results from initial network sweep.",
        "upload_date": "2024-01-28T12:00:00Z"
    }
    ```
*   **Error Responses:** `400 Bad Request` (e.g., no file, file type not allowed, missing task_id), `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (task), `413 Payload Too Large`, `500 Internal Server Error` (e.g., file save failure).

### 2. List Evidence for Task
*   **Endpoint:** `GET /api/tasks/<task_id>/evidence`
*   **Description:** Lists all evidence records for a specific task. User must be project owner or task assignee.
*   **Success Response (200 OK):** Array of Evidence objects.
    ```json
    [
        {
            "id": 1001,
            "project_task_id": 101,
            "uploaded_by_id": 123,
            "file_name": "nessus_scan_results.xml", // User-facing original filename (sanitized)
            "file_path": "projects/1/tasks/101/evidence_uuid.xml", // Internal path, may not be directly useful to client
            "storage_identifier": "projects/1/tasks/101/evidence_uuid.xml", // Internal identifier
            "tool_type": "Nessus",
            "notes": "...",
            "upload_date": "2024-01-26T11:00:00Z"
        }
    ]
    ```
    *(Note: `file_path` and `storage_identifier` are primarily for server-side use. Clients should rely on the `file_name` for display and the download endpoint for access.)*

### 3. Get Evidence Details
*   **Endpoint:** `GET /api/evidence/<evidence_id>`
*   **Description:** Retrieves details (metadata) of a specific evidence record. User must be project owner, parent task assignee, or the uploader of the evidence.
*   **Success Response (200 OK):** Evidence object (similar to "List Evidence" item structure).
    *(Note: `file_path` and `storage_identifier` are primarily for server-side use.)*
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.

### 4. Download Evidence File
*   **Endpoint:** `GET /api/evidence/<evidence_id>/download`
*   **Description:** Downloads the actual file associated with the evidence record. User must be project owner, parent task assignee, or the uploader of the evidence.
*   **Success Response (200 OK):** The file content, with `Content-Disposition: attachment; filename="original_filename.ext"` header.
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (evidence or file), `500 Internal Server Error`.

### 5. Delete Evidence
*   **Endpoint:** `DELETE /api/evidence/<evidence_id>`
*   **Description:** Deletes an evidence record and its associated file from storage. User must be project owner or the uploader of the evidence.
*   **Success Response (200 OK):**
    ```json
    {"msg": "Evidence deleted successfully"}
    ```
*   **Error Responses:** `401 Unauthorized`, `403 Forbidden`, `404 Not Found`.
