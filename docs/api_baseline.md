# API Documentation - Baseline Management

This document outlines the API endpoints related to baseline management.

## Baseline Routes

### Create Baseline

*   **POST** `/api/baselines`
*   **Description:** Creates a new baseline. The `created_by_id` will be set to the ID of the authenticated user.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
*   **Request Body:**
    ```json
    {
        "name": "string (required)",
        "description": "string (optional)"
    }
    ```
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:** (As before)
*   **Error Responses:**
    *   `400 Bad Request`: Missing baseline name. Baseline with the same name already exists.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role is not authorized.

### Get All Baselines

*   **GET** `/api/baselines`
*   **Description:** Retrieves all available baselines.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only` (Any authenticated user).
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.

### Get Baseline by ID

*   **GET** `/api/baselines/{baseline_id}`
*   **Description:** Retrieves a specific baseline by its ID, including its associated task definitions.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`, `Read-Only` (Any authenticated user).
*   **Path Parameters:** (As before)
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `404 Not Found`: Baseline with the given ID not found.

## Task Definition Routes (within a Baseline)

### Create Task Definition for Baseline

*   **POST** `/api/baselines/{baseline_id}/task_definitions`
*   **Description:** Creates a new task definition and associates it with a specific baseline.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can add task definitions to any baseline.
    *   `Consultant`: Can only add task definitions to baselines they created.
*   **Path Parameters:** (As before)
*   **Request Body:** (As before)
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `400 Bad Request`: Missing task definition title.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant is not the creator of the baseline.
    *   `404 Not Found`: Baseline with the given ID not found.

### Update Task Definition

*   **PUT** `/api/task_definitions/{task_def_id}`
*   **Description:** Updates an existing task definition.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can update any task definition.
    *   `Consultant`: Can only update task definitions belonging to baselines they created.
*   **Path Parameters:** (As before)
*   **Request Body:** (As before)
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant is not the creator of the parent baseline.
    *   `404 Not Found`: Task definition with the given ID not found.

### Delete Task Definition

*   **DELETE** `/api/task_definitions/{task_def_id}`
*   **Description:** Deletes a specific task definition.
*   **Authentication:** JWT Bearer token required.
*   **Required Roles:** `Administrator`, `Consultant`.
    *   `Administrator`: Can delete any task definition.
    *   `Consultant`: Can only delete task definitions belonging to baselines they created.
*   **Path Parameters:** (As before)
*   **Success Response:** (As before)
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role not permitted or Consultant is not the creator of the parent baseline.
    *   `404 Not Found`: Task definition with the given ID not found.
