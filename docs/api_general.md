# API Documentation - General

This document outlines general API endpoints.

## General User API Routes

### Get Current User Profile

*   **GET** `/api/me`
*   **Description:** Retrieves the profile information of the currently authenticated user.
*   **Authentication:** JWT Bearer token required in Authorization header.
*   **Request Body:** None.
*   **Path Parameters:** None.
*   **Query Parameters:** None.
*   **Success Response:**
    *   **Code:** `200 OK`
    *   **Content:**
        ```json
        {
            "id": "integer",
            "username": "string",
            "email": "string"
        }
        ```
*   **Error Responses:**
    *   `401 Unauthorized`: JWT is missing, invalid, or expired.
    *   `404 Not Found`: User associated with the JWT token identity not found (should be rare if tokens are managed correctly).
