// frontend/src/pages/CreateProjectPage.jsx
import React, { useState } from 'react';
import { createProject } from '../services/api';
import { Form, Button, Container, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function CreateProjectPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'active', // Default status
    priority: 'Medium', // Default priority
    project_type: '',
    start_date: '',
    end_date: '',
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name) {
      setError("Project name is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      // Filter out empty date strings before sending
      const dataToSend = { ...formData };
      if (!dataToSend.start_date) delete dataToSend.start_date;
      if (!dataToSend.end_date) delete dataToSend.end_date;

      await createProject(dataToSend);
      navigate('/projects'); // Navigate to projects list on success
    } catch (err) {
      setError(err.message || 'Failed to create project.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container className="mt-3">
      <h1>Create New Project</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="projectName">
          <Form.Label>Project Name <span className="text-danger">*</span></Form.Label>
          <Form.Control
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectDescription">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            name="description"
            value={formData.description}
            onChange={handleChange}
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectStatus">
          <Form.Label>Status</Form.Label>
          <Form.Select name="status" value={formData.status} onChange={handleChange}>
            <option value="active">Active</option>
            <option value="planning">Planning</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="on_hold">On Hold</option>
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectPriority">
          <Form.Label>Priority</Form.Label>
          <Form.Select name="priority" value={formData.priority} onChange={handleChange}>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectType">
          <Form.Label>Project Type</Form.Label>
          <Form.Control
            type="text"
            name="project_type"
            value={formData.project_type}
            onChange={handleChange}
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectStartDate">
          <Form.Label>Start Date (Optional)</Form.Label>
          <Form.Control
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="projectEndDate">
          <Form.Label>End Date (Optional)</Form.Label>
          <Form.Control
            type="date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
          />
        </Form.Group>

        <Button variant="primary" type="submit" disabled={submitting}>
          {submitting ? 'Creating...' : 'Create Project'}
        </Button>
      </Form>
    </Container>
  );
}

export default CreateProjectPage;
