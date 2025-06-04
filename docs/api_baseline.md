# API Documentation - Baseline Management

This document outlines the API endpoints related to baseline management.

## Baseline Routes

### Create Baseline

*   **POST** `/api/baselines`
*   **Description:** Creates a new baseline.
*   **Authentication:** JWT Bearer token required.
*   **Request Body:**
    ```json
    {
        "name": "string (required)",
        "description": "string (optional)"
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
            "created_by_id": "integer"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing baseline name. Baseline with the same name already exists.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.

### Get All Baselines

*   **GET** `/api/baselines`
*   **Description:** Retrieves all available baselines.
*   **Authentication:** JWT Bearer token required.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of baseline objects.
        ```json
        [
            {
                "id": "integer",
                "name": "string",
                "description": "string",
                "created_by_id": "integer"
            }
            // ... more baselines
        ]
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.

### Get Baseline by ID

*   **GET** `/api/baselines/{baseline_id}`
*   **Description:** Retrieves a specific baseline by its ID, including its associated task definitions.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `baseline_id` (integer, required): The ID of the baseline to retrieve.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "id": "integer",
            "name": "string",
            "description": "string",
            "created_by_id": "integer",
            "task_definitions": [
                {
                    "id": "integer",
                    "title": "string",
                    "description": "string",
                    "category": "string"
                }
                // ... more task definitions
            ]
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `404 Not Found`: Baseline with the given ID not found.

## Task Definition Routes (within a Baseline)

### Create Task Definition for Baseline

*   **POST** `/api/baselines/{baseline_id}/task_definitions`
*   **Description:** Creates a new task definition and associates it with a specific baseline. The authenticated user must be the creator of the baseline.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `baseline_id` (integer, required): The ID of the baseline to which this task definition will be added.
*   **Request Body:**
    ```json
    {
        "title": "string (required)",
        "description": "string (optional)",
        "category": "string (optional)"
    }
    ```
*   **Success Response:**
    *   **Code:** `201 Created`
    *   **Content:**
        ```json
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "category": "string",
            "baseline_id": "integer"
        }
        ```
*   **Error Responses:**
    *   `400 Bad Request`: Missing task definition title.
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to add tasks to this baseline (not the creator).
    *   `404 Not Found`: Baseline with the given ID not found.

### Update Task Definition

*   **PUT** `/api/task_definitions/{task_def_id}`
*   **Description:** Updates an existing task definition. The authenticated user must be the creator of the parent baseline.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_def_id` (integer, required): The ID of the task definition to update.
*   **Request Body:**
    ```json
    {
        "title": "string (optional)",
        "description": "string (optional)",
        "category": "string (optional)"
    }
    ```
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** The updated task definition object.
        ```json
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "category": "string",
            "baseline_id": "integer"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to update this task definition (not the creator of the parent baseline).
    *   `404 Not Found`: Task definition with the given ID not found.

### Delete Task Definition

*   **DELETE** `/api/task_definitions/{task_def_id}`
*   **Description:** Deletes a specific task definition. The authenticated user must be the creator of the parent baseline.
*   **Authentication:** JWT Bearer token required.
*   **Path Parameters:**
    *   `task_def_id` (integer, required): The ID of the task definition to delete.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "msg": "Task definition deleted successfully"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User is not authorized to delete this task definition (not the creator of the parent baseline).
    *   `404 Not Found`: Task definition with the given ID not found.
