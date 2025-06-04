// frontend/src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext'; // Keep for eventual switch from fakeLogin
import { Form, Button, Container, Alert, Card } from 'react-bootstrap'; // Removed Row, Col as they weren't used directly in previous step's JSX

function LoginPage() {
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldError, setFieldError] = useState(''); // For client-side validation messages
  const [submitting, setSubmitting] = useState(false);
  // const { login } = useAuth(); // Will use fakeLogin as per current plan step
  const navigate = useNavigate();

  // Placeholder async function to simulate API call
  const fakeLogin = async (username, pwd) => {
    console.log("Attempting login for:", username);
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (!username || !pwd) {
          // This case should ideally be caught by client-side validation first
          reject(new Error("Username and password are required (from server)."));
        } else if (username === "testuser" && pwd === "password") { // Example credentials
          resolve({ message: "Login successful!" });
        } else if (username === "test@example.com" && pwd === "TestPassword123!") { // Previously created test user
          resolve({ message: "Login successful!" });
        }
        else {
          reject(new Error("Invalid username or password."));
        }
      }, 1500); // Simulate network delay
    });
  };

  const validateForm = () => {
    if (!emailOrUsername.trim() || !password.trim()) {
      setFieldError('Both username/email and password are required.');
      return false;
    }
    setFieldError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous server errors
    setFieldError(''); // Clear previous field errors

    if (!validateForm()) {
      return; // Stop submission if client-side validation fails
    }

    setSubmitting(true);
    try {
      // Using fakeLogin as per plan
      const response = await fakeLogin(emailOrUsername, password);
      // alert(`Login success: ${response.message}`); // For debugging, will be replaced by navigation
      navigate('/projects'); // Navigate to a protected route on success
    } catch (err) {
      // Error from fakeLogin
      setError(err.message || 'Failed to login. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Container fluid className="d-flex flex-column justify-content-center align-items-center p-0" style={{ minHeight: '100vh' }}>
      <Card className="login-card shadow-sm">
        <Card.Body className="p-4">
          <Card.Title as="h2" className="text-center mb-4">Login</Card.Title>

          {/* Display client-side validation error if present */}
          {fieldError && <Alert variant="warning" role="alert" id="loginFieldErrorAlert">{fieldError}</Alert>}

          {/* Display server-side/general error if present and no fieldError */}
          {error && !fieldError && <Alert variant="danger" role="alert">{error}</Alert>}

          <Form onSubmit={handleSubmit} noValidate aria-describedby={fieldError ? "loginFieldErrorAlert" : undefined}> {/* noValidate disables browser default validation */}
            <Form.Group className="mb-3" controlId="loginEmailOrUsername">
              <Form.Label>Email address or Username</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter email or username"
                value={emailOrUsername}
                onChange={(e) => setEmailOrUsername(e.target.value)}
                isInvalid={!!(fieldError && (fieldError.includes('Both') || fieldError.includes('username')))} // More specific check
                aria-describedby="usernameHelpBlock"
                autoFocus
              />
              {/* Example of more specific field error, not fully implemented here for brevity */}
              {/* <Form.Control.Feedback type="invalid" id="usernameHelpBlock">
                Please provide a username or email.
              </Form.Control.Feedback> */}
            </Form.Group>

            <Form.Group className="mb-3" controlId="loginPassword">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                isInvalid={!!(fieldError && (fieldError.includes('Both') || fieldError.includes('password')))} // More specific check
                aria-describedby="passwordHelpBlock"
              />
               {/* <Form.Control.Feedback type="invalid" id="passwordHelpBlock">
                Please provide a password.
              </Form.Control.Feedback> */}
            </Form.Group>
            <div className="d-grid mt-4">
              <Button variant="primary" type="submit" disabled={submitting} className="login-button">
                {submitting ? 'Logging in...' : 'Login'}
              </Button>
            </div>
          </Form>
          <div className="text-center mt-3">
            Don't have an account? <Link to="/register">Sign Up</Link>
          </div>
        </Card.Body>
      </Card>
    </Container>
  );
}

export default LoginPage;
