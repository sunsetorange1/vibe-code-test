# API Documentation - Evidence Management

This document outlines the API endpoints related to evidence management for project tasks. Evidence is typically a file uploaded to support task completion.

## Evidence Management Routes

### Add Evidence to Task

*   **POST** `/api/tasks/{task_id}/evidence`
*   **Description:** Uploads a file as evidence for a specific task. `mime_type` is automatically detected. `verified` defaults to `false`.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can add evidence to any task in any project.
    *   `Consultant`: Can only add evidence to tasks in projects they own.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to which this evidence will be added.
*   **Request Body (multipart/form-data):** (As before)
*   **Success Response:** (As before, includes `mime_type`, `verified`)
*   **Error Responses:**
    *   `400 Bad Request`: No file part, no file selected, file type not allowed.
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found in DB.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Task not found.
    *   `500 Internal Server Error`: File save error, or associated project not found.

### Get All Evidence for a Task

*   **GET** `/api/tasks/{task_id}/evidence`
*   **Description:** Retrieves all evidence records for a specific task. Access depends on role and project ownership/grants.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view evidence for any task.
    *   `Consultant`: Can only view evidence for tasks in projects they own.
    *   `Read-Only`: Access currently restricted if not project owner (pending grant system). Will receive 403 if not owner/admin for the project.
*   **Path Parameters:** (As before)
*   **Success Response:** (As before, array of evidence objects with `mime_type`, `verified`)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found.
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Task not found.
    *   `500 Internal Server Error`: Associated project not found.

### Get Evidence Detail by ID

*   **GET** `/api/evidence/{evidence_id}`
*   **Description:** Retrieves a specific evidence record. Access depends on role and project ownership/grants of the parent task's project.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can view any evidence.
    *   `Consultant`: Can only view evidence in projects they own.
    *   `Read-Only`: Access currently restricted (pending grant system). Will receive 403 if not owner/admin for the project.
*   **Path Parameters:** (As before)
*   **Success Response:** (As before, evidence object with `mime_type`, `verified`)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found.
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Evidence not found.
    *   `500 Internal Server Error`: Associated task or project not found.

### Update Evidence Metadata

*   **PUT** `/api/evidence/{evidence_id}`
*   **Description:** Updates metadata (notes, verification status) for an evidence item.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can update any evidence.
    *   `Consultant`: Can only update evidence in projects they own.
*   **Path Parameters:** (As before)
*   **Request Body:** (As before - `notes`, `verified`)
*   **Success Response:** (As before, updated evidence object with `mime_type`, `verified`)
*   **Error Responses:**
    *   `400 Bad Request`: Invalid boolean for `verified`.
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Evidence not found.
    *   `500 Internal Server Error`: Associated task or project not found.

### Delete Evidence

*   **DELETE** `/api/evidence/{evidence_id}`
*   **Description:** Deletes an evidence record and its associated file.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can delete any evidence.
    *   `Consultant`: Can only delete evidence in projects they own.
*   **Path Parameters:** (As before)
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found.
    *   `403 Forbidden`: User's role not permitted or Consultant does not own the project.
    *   `404 Not Found`: Evidence not found.
    *   `500 Internal Server Error`: Associated task/project not found, or file deletion error.

### Download Evidence File

*   **GET** `/api/evidence/{evidence_id}/download`
*   **Description:** Downloads the file associated with an evidence record. Access depends on role and project ownership/grants.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only`.
    *   `Administrator`: Can download any evidence file.
    *   `Consultant`: Can only download evidence from projects they own.
    *   `Read-Only`: Access currently restricted (pending grant system). Will receive 403 if not owner/admin for the project.
*   **Path Parameters:** (As before)
*   **Success Response:** (As before - file attachment)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT missing/invalid, or authenticated user not found.
    *   `403 Forbidden`: User's role and ownership/grants do not permit access.
    *   `404 Not Found`: Evidence/file not found on server.
    *   `500 Internal Server Error`: Associated task/project not found, or download service configuration error.
