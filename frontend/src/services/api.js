// frontend/src/services/api.js
const API_BASE_URL = '/api'; // Adjust if your Flask app serves API under a different prefix

async function handleResponse(response, errorMessagePrefix) {
  if (!response.ok) {
    let errorMsg = `${errorMessagePrefix}: ${response.status} ${response.statusText}`;
    try {
      const errorData = await response.json();
      errorMsg = errorData.msg || errorMsg;
    } catch (e) {
      // Ignore if error response is not JSON or if response is not JSON at all
    }
    throw new Error(errorMsg);
  }
  // For DELETE requests or other non-JSON responses, check content type or status
  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return null; // Or return a success indicator like { success: true }
  }
  return response.json();
}

export async function getProjects() {
  const response = await fetch(`${API_BASE_URL}/projects`);
  return handleResponse(response, 'Failed to fetch projects');
}

export async function createProject(projectData) {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'Authorization': `Bearer ${localStorage.getItem('token')}` // Add if auth is ready
    },
    body: JSON.stringify(projectData),
  });
  return handleResponse(response, 'Failed to create project');
}

export async function getProject(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
  return handleResponse(response, `Failed to fetch project ${projectId}`);
}

export async function getProjectTasks(projectId) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`);
  return handleResponse(response, `Failed to fetch tasks for project ${projectId}`);
}

export async function createTask(projectId, taskData) {
  const response = await fetch(`${API_BASE_URL}/projects/${projectId}/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'Authorization': `Bearer ${localStorage.getItem('token')}` // Add if auth is ready
    },
    body: JSON.stringify(taskData),
  });
  return handleResponse(response, `Failed to create task for project ${projectId}`);
}

export async function getTask(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`);
  return handleResponse(response, `Failed to fetch task ${taskId}`);
}

export async function getTaskEvidence(taskId) {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/evidence`);
  return handleResponse(response, `Failed to fetch evidence for task ${taskId}`);
}

export async function addEvidence(taskId, formData) {
  // For FormData, browser sets Content-Type automatically with boundary
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/evidence`, {
    method: 'POST',
    // headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }, // Add if auth is ready
    body: formData,
  });
  return handleResponse(response, `Failed to add evidence for task ${taskId}`);
}

export async function updateEvidence(evidenceId, evidenceData) {
  const response = await fetch(`${API_BASE_URL}/evidence/${evidenceId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      // 'Authorization': `Bearer ${localStorage.getItem('token')}` // Add if auth is ready
    },
    body: JSON.stringify(evidenceData),
  });
  return handleResponse(response, `Failed to update evidence ${evidenceId}`);
}
