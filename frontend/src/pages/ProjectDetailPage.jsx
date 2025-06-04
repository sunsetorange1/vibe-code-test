// frontend/src/pages/ProjectDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getProject, getProjectTasks } from '../services/api';
import { Container, Row, Col, Button, Table, Spinner, Alert, Card } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext';
import { ADMIN, CONSULTANT } from '../constants/roles';

function ProjectDetailPage() {
  const { projectId } = useParams();
  const { user } = useAuth(); // Get current user from AuthContext

  const [project, setProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loadingProject, setLoadingProject] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [error, setError] = useState(null);

  const loadProjectDetails = useCallback(async () => {
    try {
      setLoadingProject(true);
      const projectData = await getProject(projectId);
      setProject(projectData);
      setError(null);
    } catch (err) {
      setError(err.message || `Failed to load project details for ID ${projectId}.`);
      setProject(null);
    } finally {
      setLoadingProject(false);
    }
  }, [projectId]);

  const loadTasks = useCallback(async () => {
    try {
      setLoadingTasks(true);
      const tasksData = await getProjectTasks(projectId);
      setTasks(tasksData);
    } catch (err) {
      setError(prevError => prevError ? `${prevError}\n${err.message}` : (err.message || `Failed to load tasks for project ID ${projectId}.`));
      setTasks([]);
    } finally {
      setLoadingTasks(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadProjectDetails();
    loadTasks();
  }, [loadProjectDetails, loadTasks]);

  // Determine if the "Create New Task" button should be visible
  let canCreateTask = false;
  if (user && project) { // Ensure user and project data are loaded
    if (user.role === ADMIN) {
      canCreateTask = true;
    } else if (user.role === CONSULTANT && project.owner_id === user.id) {
      canCreateTask = true;
    }
  }

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

  if (error && !project) {
    return (
      <Container className="mt-3">
        <Alert variant="danger">
          <Alert.Heading>Error Loading Project</Alert.Heading>
          <p>{error.split('\n')[0]}</p> {/* Show only the primary error if project failed */}
        </Alert>
      </Container>
    );
  }

  if (!project) {
      return <Container className="mt-3"><Alert variant="warning">Project not found.</Alert></Container>;
  }

  const pageError = error && error.includes("tasks for project ID") ? error.split('\n').find(e => e.includes("tasks for project ID")) : null;


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
          {/* Future: Add Edit Project button here, wrapped in ShowForRole or similar logic */}
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>Tasks</h2>
        {canCreateTask && (
          <Button as={Link} to={`/projects/${projectId}/tasks/create`} variant="success">
            Create New Task
          </Button>
        )}
      </div>
      {loadingTasks && (
        <div className="text-center">
          <Spinner animation="border" role="status" size="sm">
            <span className="visually-hidden">Loading tasks...</span>
          </Spinner>
          <p>Loading tasks...</p>
        </div>
      )}
      {pageError && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible>
              <Alert.Heading>Error Loading Tasks</Alert.Heading>
              <p>{pageError}</p>
          </Alert>
      )}
      {!loadingTasks && tasks.length === 0 && !pageError && (
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
