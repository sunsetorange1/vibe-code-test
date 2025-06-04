// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavigationBar from './components/NavigationBar';
import HomePage from './pages/HomePage';
import ProjectsPage from './pages/ProjectsPage';
import CreateProjectPage from './pages/CreateProjectPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import CreateTaskPage from './pages/CreateTaskPage';
import TaskDetailPage from './pages/TaskDetailPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage'; // Import RegisterPage
import ProtectedRoute from './components/ProtectedRoute'; // Import ProtectedRoute
import { Container } from 'react-bootstrap';
import './App.css';

function App() {
  return (
    <Router>
      <NavigationBar />
      <Container fluid className="mt-4">
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} /> {/* New Route */}
          <Route path="/" element={<HomePage />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}> {/* Parent route for protected content */}
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/create" element={<CreateProjectPage />} />
            <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            <Route path="/projects/:projectId/tasks/create" element={<CreateTaskPage />} />
            <Route path="/projects/:projectId/tasks/:taskId" element={<TaskDetailPage />} />
            {/* Add any other future protected routes here, e.g., a /users page */}
            {/* <Route path="/users" element={<UsersPage />} /> */}
          </Route>

          {/* Optional: Add a 404 Not Found route here */}
          {/* <Route path="*" element={<NotFoundPage />} /> */}
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
