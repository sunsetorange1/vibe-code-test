// frontend/src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom'; // Link for future use
import { useAuth } from '../contexts/AuthContext';
import { Form, Button, Container, Alert, Card } from 'react-bootstrap';

function LoginPage() {
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      // The login function in AuthContext expects (emailOrUsername, password)
      // Backend auth_routes.py uses 'username' for login field which can be email or username.
      await login(emailOrUsername, password);
      navigate('/projects'); // Redirect to a protected route on success
    } catch (err) {
      setError(err.message || 'Failed to login. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container className="mt-5 d-flex justify-content-center">
      <Card style={{ width: '30rem' }}>
        <Card.Body>
          <Card.Title as="h2" className="text-center mb-4">Login</Card.Title>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="loginEmailOrUsername">
              <Form.Label>Email address or Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter email or username"
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                required
                autoFocus
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="loginPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </Form.Group>
            <div className="d-grid">
              <Button variant="primary" type="submit" disabled={submitting}>
                {submitting ? 'Logging in...' : 'Login'}
              </Button>
            </div>
          </Form>
          {/* Optional: Add Link to a registration page if available */}
          <div className="text-center mt-3">
            Don't have an account? <Link to="/register">Sign Up</Link>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}

export default LoginPage;
