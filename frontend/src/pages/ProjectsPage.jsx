// frontend/src/pages/ProjectsPage.jsx
import React, { useState, useEffect } from 'react';
import { getProjects } from '../services/api';
import { Container, Table, Button, Spinner, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { ShowForRole } from '../components'; // Adjusted path assuming components/index.js is used
import { ADMIN, CONSULTANT } from '../constants/roles';

function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadProjects() {
      try {
        setLoading(true);
        const data = await getProjects();
        setProjects(data);
        setError(null);
      } catch (err) {
        setError(err.message || 'An unexpected error occurred.');
        setProjects([]); // Clear projects on error
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, []);

  if (loading) {
    return (
      <Container className="mt-3 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p>Loading projects...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-3">
        <Alert variant="danger">
          <Alert.Heading>Error Loading Projects</Alert.Heading>
          <p>{error}</p>
          {/* You could add a retry button here */}
        </Alert>
      </Container>
    );
  }

  return (
    <Container className="mt-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Projects</h1>
        <ShowForRole roles={[ADMIN, CONSULTANT]}>
          <Button as={Link} to="/projects/create" variant="primary">
            Create New Project
          </Button>
        </ShowForRole>
      </div>
      {projects.length === 0 && !loading && !error && (
        <Alert variant="info">No projects found. Why not create one?</Alert>
      )}
      {projects.length > 0 && (
        <Table striped bordered hover responsive>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Description</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Project Type</th>
              {/* Add more headers if needed, e.g., for actions */}
            </tr>
          </thead>
          <tbody>
            {projects.map((project) => (
              <tr key={project.id}>
                <td>{project.id}</td>
                <td>
                  <Link to={`/projects/${project.id}`}>{project.name}</Link>
                </td>
                <td>{project.description}</td>
                <td>{project.status}</td>
                <td>{project.priority}</td>
                <td>{project.project_type}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Container>
  );
}

export default ProjectsPage;
