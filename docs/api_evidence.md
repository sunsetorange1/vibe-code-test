# API Documentation - Evidence Management

This document outlines the API endpoints related to evidence management for project tasks. Evidence is typically a file uploaded to support task completion.

## Evidence Management Routes

### Add Evidence to Task

*   **POST** `/api/tasks/{task_id}/evidence`
*   **Description:** Uploads a file as evidence for a specific task. The request must be `multipart/form-data`. The user must be the project owner or assigned to the task. `mime_type` is automatically detected from the uploaded file. `verified` defaults to `false`.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task to which this evidence will be added.
*   **Request Body (multipart/form-data):**
    *   `file` (file, required): The evidence file to upload.
    *   `tool_type` (string, optional): The type of tool or method used to generate the evidence (e.g., "nessus_scan", "screenshot").
    *   `notes` (string, optional): Any notes or description for the evidence.
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:** The created evidence object.
        ```json
        {
            "id": "integer",
            "project_task_id": "integer",
            "uploaded_by_id": "integer",
            "file_name": "string (original name of the uploaded file)",
            "file_path": "string (path where the file is stored internally)",
            "storage_identifier": "string (identifier for storage, often same as file_path)",
            "tool_type": "string or null",
            "notes": "string or null",
            "upload_date": "string (ISO 8601 datetime)",
            "mime_type": "string (e.g., 'application/pdf', 'image/png')",
            "verified": "boolean (defaults to false)"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: No file part in request, no file selected, file type not allowed.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to add evidence to this task.
    *   `404 Not Found`: Task with the given ID not found.
    *   `500 Internal Server Error`: Could not save file. Associated project not found.

### Get All Evidence for a Task

*   **GET** `/api/tasks/{task_id}/evidence`
*   **Description:** Retrieves all evidence records associated with a specific task. The user must be the project owner or assigned to the task.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_id` (integer, required): The ID of the task for which to retrieve evidence.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of evidence objects.
        ```json
        [
            {
                "id": "integer",
                "project_task_id": "integer",
                "uploaded_by_id": "integer",
                "file_name": "string",
                "file_path": "string",
                "storage_identifier": "string",
                "tool_type": "string or null",
                "notes": "string or null",
                "upload_date": "string (ISO 8601 datetime)",
                "mime_type": "string",
                "verified": "boolean"
            }
            // ... more evidence records
        ]
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to view evidence for this task.
    *   `404 Not Found`: Task with the given ID not found.
    *   `500 Internal Server Error`: Associated project not found.

### Get Evidence Detail by ID

*   **GET** `/api/evidence/{evidence_id}`
*   **Description:** Retrieves a specific evidence record by its ID. The user must be the project owner, assigned to the parent task, or the user who uploaded the evidence.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `evidence_id` (integer, required): The ID of the evidence to retrieve.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The evidence object.
        ```json
        {
            "id": "integer",
            "project_task_id": "integer",
            "uploaded_by_id": "integer",
            "file_name": "string",
            "file_path": "string",
            "storage_identifier": "string",
            "tool_type": "string or null",
            "notes": "string or null",
            "upload_date": "string (ISO 8601 datetime)",
            "mime_type": "string",
            "verified": "boolean"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to view this evidence.
    *   `404 Not Found`: Evidence with the given ID not found.
    *   `500 Internal Server Error`: Associated task or project not found.

### Update Evidence Metadata

*   **PUT** `/api/evidence/{evidence_id}`
*   **Description:** Updates metadata for a specific evidence item, such as notes or verification status. File content itself cannot be changed with this endpoint.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `evidence_id` (integer, required): The ID of the evidence to update.
*   **Request Body:**
    ```json
    {
        "notes": "string (optional, new notes for the evidence)",
        "verified": "boolean (optional, new verification status)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The updated evidence object.
        ```json
        {
            "id": "integer",
            "project_task_id": "integer",
            "uploaded_by_id": "integer",
            "file_name": "string",
            "file_path": "string",
            "storage_identifier": "string",
            "tool_type": "string or null",
            "notes": "string or null (updated)",
            "upload_date": "string (ISO 8601 datetime)",
            "mime_type": "string",
            "verified": "boolean (updated)"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Invalid boolean value for verified.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to update this evidence (not project owner or original uploader).
    *   `404 Not Found`: Evidence with the given ID not found.
    *   `500 Internal Server Error`: Associated task or project not found.
*   **Permissions:** Only the project owner or the user who originally uploaded the evidence can update it.

### Delete Evidence

*   **DELETE** `/api/evidence/{evidence_id}`
*   **Description:** Deletes a specific evidence record and its associated file from storage. The user must be the project owner or the user who uploaded the evidence.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `evidence_id` (integer, required): The ID of the evidence to delete.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "msg": "Evidence deleted successfully"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to delete this evidence.
    *   `404 Not Found`: Evidence with the given ID not found.
    *   `500 Internal Server Error`: Associated task or project not found. Failure to delete file from storage (metadata might still be deleted).

### Download Evidence File

*   **GET** `/api/evidence/{evidence_id}/download`
*   **Description:** Downloads the file associated with a specific evidence record. The user must be the project owner, assigned to the parent task, or the user who uploaded the evidence.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `evidence_id` (integer, required): The ID of the evidence whose file is to be downloaded.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The file as an attachment.
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to download this evidence file.
    *   `404 Not Found`: Evidence record not found, no file associated with the record, or file not found on server.
    *   `500 Internal Server Error`: Associated task or project not found. File download service not configured. Error sending file.
