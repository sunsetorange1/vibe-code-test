# API Documentation - User Management

This document outlines API endpoints related to user management.

## User API Routes

### List All Users

*   **GET** `/api/users`
*   **Description:** Retrieves a list of all registered users. This endpoint is intended for Administrators and Consultants (e.g., for task assignment).
*   **Authentication:** JWT Bearer token required in Authorization header.
*   **Required Roles:** `Administrator`, `Consultant`.
*   **Request Body:** None.
*   **Path Parameters:** None.
*   **Query Parameters:** None.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:** An array of user objects.
        ```json
        [
            {
                "id": "integer",
                "username": "string",
                "email": "string"
            }
            // ... more users
        ]
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `403 Forbidden`: User's role is not `Administrator` or `Consultant`.
    *   `500 Internal Server Error`: An unexpected error occurred on the server while trying to retrieve users. (Includes `error` field with details if available).
