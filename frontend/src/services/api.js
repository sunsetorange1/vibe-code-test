// frontend/src/services/api.js
const API_BASE_URL = '/api'; // Adjust if your Flask app serves API under a different prefix
const AUTH_BASE_URL = '/auth'; // Base URL for authentication routes

// Function to get token from localStorage
const getToken = () => localStorage.getItem('token');

// Centralized response handler
async function handleResponse(response, errorMessagePrefix) {
  if (!response.ok) {
    let errorMsg = `${errorMessagePrefix}: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMsg = errorData.msg || errorMsg; // Use backend's 'msg' field if available
    } catch (e) {
      // Ignore if error response is not JSON or parsing fails
    }
    throw new Error(errorMsg);
  }
  // Handle cases where response might be empty (e.g., 204 No Content)
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.indexOf("application/json") !== -1) {
    return response.json();
  }
  return null; // Or response.text() if plain text is expected for some non-JSON success
}

// Authentication API calls
export async function login(credentials) { // credentials: { username, password }
  const response = await fetch(`${AUTH_BASE_URL}/login`, { // Uses AUTH_BASE_URL
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });
  return handleResponse(response, 'Login failed'); // Returns { access_token }
}

export async function getAuthenticatedUserProfile() {
  const token = getToken();
  if (!token) return Promise.reject(new Error("No token found. Cannot fetch user profile."));

  const response = await fetch(`${API_BASE_URL}/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return handleResponse(response, 'Failed to fetch user profile');
}

// Generic function to create headers with Authorization if token exists
const createAuthHeaders = (isFormData = false) => {
  const token = getToken();
  const headers = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// --- Project API Calls ---
export async function getProjects() {
  const response = await fetch(`${API_BASE_URL}/projects`, { headers: createAuthHeaders() });
  return handleResponse(response, 'Failed to fetch projects');
}

export async function createProject(projectData) {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: createAuthHeaders(),
    body: JSON.stringify(projectData),
  });
  return handleResponse(response, 'Failed to create project');
}

export async function getProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, { headers: createAuthHeaders() });
  return handleResponse(response, `Failed to fetch project ${projectId}`);
}

// --- Task API Calls ---
export async function getProjectTasks(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`, { headers: createAuthHeaders() });
  return handleResponse(response, `Failed to fetch tasks for project ${projectId}`);
}

export async function createTask(projectId, taskData) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`, {
    method: 'POST',
    headers: createAuthHeaders(),
    body: JSON.stringify(taskData),
  });
  return handleResponse(response, `Failed to create task for project ${projectId}`);
}

export async function getTask(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, { headers: createAuthHeaders() });
  return handleResponse(response, `Failed to fetch task ${taskId}`);
}

// --- Evidence API Calls ---
export async function getTaskEvidence(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/evidence`, { headers: createAuthHeaders() });
  return handleResponse(response, `Failed to fetch evidence for task ${taskId}`);
}

export async function addEvidence(taskId, formData) {
  // For FormData, browser sets Content-Type automatically including the boundary
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/evidence`, {
    method: 'POST',
    headers: createAuthHeaders(true), // Pass true for FormData
    body: formData,
  });
  return handleResponse(response, `Failed to add evidence for task ${taskId}`);
}

export async function updateEvidence(evidenceId, evidenceData) {
  const response = await fetch(`${API_BASE_URL}/evidence/${evidenceId}`, {
    method: 'PUT',
    headers: createAuthHeaders(),
    body: JSON.stringify(evidenceData),
  });
  return handleResponse(response, `Failed to update evidence ${evidenceId}`);
}

export async function downloadEvidenceFile(evidenceId, originalFilename) {
  const token = getToken();
  const headers = {}; // No Content-Type needed for GET, but Auth is.
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/evidence/${evidenceId}/download`, {
      method: 'GET',
      headers: headers,
    });

    if (!response.ok) {
      // Attempt to parse error message if backend sends JSON for errors
      let errorMsg = `Failed to download file: ${response.status} ${response.statusText}`;
      try {
        // Check if response is JSON before trying to parse.
        // Some errors (like 500 from server if file not found by send_from_directory) might not be JSON.
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const errorData = await response.json();
            errorMsg = errorData.msg || errorMsg;
        }
      } catch (e) {
        // If response is not JSON or parsing fails, use the status text
      }
      throw new Error(errorMsg);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = originalFilename || 'download'; // Use provided filename or a default
    document.body.appendChild(a);
    a.click();

    // Clean up
    setTimeout(() => { // Timeout ensures download can start esp. on Firefox
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 100);

  } catch (error) {
    console.error('Download error in api.js:', error); // Log specific error location
    throw error; // Re-throw to be caught by UI if needed
  }
}

// --- User API Calls ---
export async function getUsers() {
    const response = await fetch(`${API_BASE_URL}/users`, { headers: createAuthHeaders() });
    return handleResponse(response, 'Failed to fetch users');
}
