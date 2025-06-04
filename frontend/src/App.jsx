// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavigationBar from './components/NavigationBar';
import HomePage from './pages/HomePage';
import ProjectsPage from './pages/ProjectsPage';
import CreateProjectPage from './pages/CreateProjectPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import CreateTaskPage from './pages/CreateTaskPage';
import TaskDetailPage from './pages/TaskDetailPage'; // Import Task Detail Page
import { Container } from 'react-bootstrap';
import './App.css'; // Keep or remove default App.css styling as needed

function App() {
  return (
    <Router>
      <NavigationBar />
      <Container className="mt-4"> {/* Add some margin top for content below navbar */}
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/projects" element={<ProjectsPage />} />
                  <Route path="/projects/create" element={<CreateProjectPage />} />
                  <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
                  <Route path="/projects/:projectId/tasks/create" element={<CreateTaskPage />} />
                  <Route path="/projects/:projectId/tasks/:taskId" element={<TaskDetailPage />} />
          {/* Define other routes here later */}
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
