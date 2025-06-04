// frontend/src/pages/CreateTaskPage.jsx
import React, { useState, useEffect } from 'react'; // Added useEffect
import { useParams, useNavigate } from 'react-router-dom';
import { createTask, getUsers } from '../services/api'; // Added getUsers
import { Form, Button, Container, Alert } from 'react-bootstrap';

function CreateTaskPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'pending', // Default status
    priority: 'Medium', // Default priority
    assigned_to_id: '', // Keep as empty string for "Unassigned" or "Select" option
    due_date: '',
    // due_date_reminder_sent is not set at creation, defaults to false on backend/model
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadUsers() {
      setLoadingUsers(true);
      try {
        const userData = await getUsers(); // getUsers should be authenticated via api.js
        setUsers(userData || []); // Ensure userData is not null/undefined before setting
      } catch (error) {
        console.error("Failed to fetch users:", error);
        // Optionally set an error state for users loading, e.g., setError("Failed to load users for assignment.");
        setUsers([]); // Set to empty array on error
      } finally {
        setLoadingUsers(false);
      }
    }
    loadUsers();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.title) {
      setError("Task title is required.");
      return;
    }
    setSubmitting(true);
    setError(null);

    const taskData = { ...formData };
    if (!taskData.description) delete taskData.description;

    // Handle assigned_to_id: if it's an empty string, delete it so backend can set to null or handle as unassigned
    if (taskData.assigned_to_id === "") {
        delete taskData.assigned_to_id;
    } else {
        const parsedId = parseInt(taskData.assigned_to_id, 10);
        if (isNaN(parsedId)) {
             setError("Invalid User ID selected for assignee."); // Should not happen with select
             setSubmitting(false);
             return;
        }
        taskData.assigned_to_id = parsedId;
    }
    if (!taskData.due_date) delete taskData.due_date;

    try {
      await createTask(projectId, taskData);
      navigate(`/projects/${projectId}`); // Navigate back to project detail page
    } catch (err) {
      setError(err.message || 'Failed to create task.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container className="mt-3">
      <h1>Create New Task for Project {projectId}</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="taskTitle">
          <Form.Label>Title <span className="text-danger">*</span></Form.Label>
          <Form.Control
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="taskDescription">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            name="description"
            value={formData.description}
            onChange={handleChange}
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="taskStatus">
          <Form.Label>Status</Form.Label>
          <Form.Select name="status" value={formData.status} onChange={handleChange}>
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="review">Review</option>
            <option value="completed">Completed</option>
            <option value="on_hold">On Hold</option>
            <option value="cancelled">Cancelled</option>
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-3" controlId="taskPriority">
          <Form.Label>Priority</Form.Label>
          <Form.Select name="priority" value={formData.priority} onChange={handleChange}>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-3" controlId="taskAssignedToId">
          <Form.Label>Assigned To (Optional)</Form.Label>
          <Form.Select
            name="assigned_to_id"
            value={formData.assigned_to_id}
            onChange={handleChange}
            disabled={loadingUsers}
          >
            <option value="">Select Assignee (Optional)</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.username} ({user.email})
              </option>
            ))}
          </Form.Select>
          {loadingUsers && <Form.Text>Loading users...</Form.Text>}
        </Form.Group>

        <Form.Group className="mb-3" controlId="taskDueDate">
          <Form.Label>Due Date (Optional)</Form.Label>
          <Form.Control
            type="date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
          />
        </Form.Group>

        <Button variant="primary" type="submit" disabled={submitting || loadingUsers}>
          {submitting ? 'Creating Task...' : 'Create Task'}
        </Button>
      </Form>
    </Container>
  );
}

export default CreateTaskPage;
