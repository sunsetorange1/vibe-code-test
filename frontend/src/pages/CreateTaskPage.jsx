// frontend/src/pages/CreateTaskPage.jsx
import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { createTask } from '../services/api';
import { Form, Button, Container, Alert } from 'react-bootstrap';

function CreateTaskPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'pending', // Default status
    priority: 'Medium', // Default priority
    assigned_to_id: '',
    due_date: '',
    // due_date_reminder_sent is not set at creation, defaults to false on backend/model
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

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

    // Prepare data, convert empty strings for optional fields to null or remove them
    const taskData = { ...formData };
    if (!taskData.description) delete taskData.description;
    if (!taskData.assigned_to_id) {
        delete taskData.assigned_to_id; // Send as undefined/null if empty
    } else {
        taskData.assigned_to_id = parseInt(taskData.assigned_to_id, 10);
        if (isNaN(taskData.assigned_to_id)) {
             setError("Assigned User ID must be a number.");
             setSubmitting(false);
             return;
        }
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
          <Form.Label>Assigned To (User ID - Optional)</Form.Label>
          <Form.Control
            type="number"
            name="assigned_to_id"
            value={formData.assigned_to_id}
            onChange={handleChange}
            placeholder="Enter User ID"
          />
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

        <Button variant="primary" type="submit" disabled={submitting}>
          {submitting ? 'Creating Task...' : 'Create Task'}
        </Button>
      </Form>
    </Container>
  );
}

export default CreateTaskPage;
