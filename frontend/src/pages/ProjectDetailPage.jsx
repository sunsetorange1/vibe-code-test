// frontend/src/pages/ProjectDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProject, getProjectTasks } from '../services/api';
import { Container, Row, Col, Button, Table, Spinner, Alert, Card } from 'react-bootstrap';

function ProjectDetailPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadProjectDetails() {
      try {
        setLoadingProject(true);
        const projectData = await getProject(projectId);
        setProject(projectData);
        setError(null); // Clear previous errors
      } catch (err) {
        setError(err.message || `Failed to load project details for ID ${projectId}.`);
        setProject(null);
      } finally {
        setLoadingProject(false);
      }
    }

    async function loadTasks() {
      try {
        setLoadingTasks(true);
        const tasksData = await getProjectTasks(projectId);
        setTasks(tasksData);
        // If project error occurred, this might clear it if tasks load successfully.
        // setError(null);
      } catch (err) {
        setError(prevError => prevError ? `${prevError}\n${err.message}` : (err.message || `Failed to load tasks for project ID ${projectId}.`));
        setTasks([]);
      } finally {
        setLoadingTasks(false);
      }
    }

    loadProjectDetails();
    loadTasks();
  }, [projectId]);

  if (loadingProject) {
    return (
      <Container className="mt-3 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading project details...</span>
        </Spinner>
        <p>Loading project details...</p>
      </Container>
    );
  }

  if (error && !project) { // Show critical error if project details failed to load
    return (
      <Container className="mt-3">
        <Alert variant="danger">
          <Alert.Heading>Error Loading Project</Alert.Heading>
          <p>{error}</p>
        </Alert>
      </Container>
    );
  }

  if (!project) { // Should be caught by error state, but as a fallback
      return <Container className="mt-3"><Alert variant="warning">Project not found.</Alert></Container>;
  }

  return (
    <Container className="mt-3">
      <Card className="mb-4">
        <Card.Header as="h1">{project.name}</Card.Header>
        <Card.Body>
          <Card.Text><strong>Description:</strong> {project.description || 'N/A'}</Card.Text>
          <Row>
            <Col md={6}>
              <Card.Text><strong>Status:</strong> {project.status}</Card.Text>
              <Card.Text><strong>Priority:</strong> {project.priority}</Card.Text>
            </Col>
            <Col md={6}>
              <Card.Text><strong>Project Type:</strong> {project.project_type || 'N/A'}</Card.Text>
              <Card.Text><strong>Start Date:</strong> {project.start_date || 'N/A'}</Card.Text>
              <Card.Text><strong>End Date:</strong> {project.end_date || 'N/A'}</Card.Text>
            </Col>
          </Row>
          {/* Future: Add Edit Project button here */}
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>Tasks</h2>
        <Button as={Link} to={`/projects/${projectId}/tasks/create`} variant="success">
          Create New Task
        </Button>
      </div>
      {loadingTasks && (
        <div className="text-center">
          <Spinner animation="border" role="status" size="sm">
            <span className="visually-hidden">Loading tasks...</span>
          </Spinner>
          <p>Loading tasks...</p>
        </div>
      )}
      {error && tasks.length === 0 && ( // Display error related to tasks if tasks couldn't be loaded
          <Alert variant="danger">
              <Alert.Heading>Error Loading Tasks</Alert.Heading>
              <p>{error.includes("tasks") ? error : "An error occurred while loading tasks."}</p>
          </Alert>
      )}
      {!loadingTasks && tasks.length === 0 && (!error || !error.includes("tasks")) && (
        <Alert variant="info">No tasks found for this project. Why not create one?</Alert>
      )}
      {!loadingTasks && tasks.length > 0 && (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Description</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Reminder Sent</th>
              <th>Assigned To (ID)</th>
              {/* Add more headers if needed, e.g., for actions */}
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>
                  <Link to={`/projects/${projectId}/tasks/${task.id}`}>{task.title}</Link>
                </td>
                <td>{task.description || 'N/A'}</td>
                <td>{task.status}</td>
                <td>{task.priority}</td>
                <td>{task.due_date_reminder_sent ? 'Yes' : 'No'}</td>
                <td>{task.assigned_to_id || 'Unassigned'}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}

export default ProjectDetailPage;
