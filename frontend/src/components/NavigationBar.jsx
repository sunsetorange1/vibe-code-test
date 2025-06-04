// frontend/src/components/NavigationBar.jsx
import React from 'react';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ShowForRole } from '../components'; // Use index import
import { ADMIN } from '../constants/roles'; // Import ADMIN constant

function NavigationBar() {
  const { isAuthenticated, user, logout, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error("Failed to logout:", error);
    }
  };

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
      <Container>
        <Navbar.Brand as={Link} to="/">My Sec Platform</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Home</Nav.Link>
            {isAuthenticated && (
              <Nav.Link as={Link} to="/projects">Projects</Nav.Link>
            )}
            <ShowForRole roles={[ADMIN]}>
              <Nav.Link as={Link} to="/admin">Admin Panel</Nav.Link>
            </ShowForRole>
            {/* Example: Add a link to Users page if user has ADMIN or CONSULTANT role */}
            {/* <ShowForRole roles={[ADMIN, CONSULTANT]}>
              <Nav.Link as={Link} to="/users">Users</Nav.Link>
            </ShowForRole> */}
          </Nav>
          <Nav>
            {isLoading ? (
              <Navbar.Text>Loading...</Navbar.Text>
            ) : isAuthenticated ? (
              <>
                <Navbar.Text className="me-2">
                  Signed in as: {user?.username || user?.email || 'User'} ({user?.role || 'No role'})
                </Navbar.Text>
                <Button variant="outline-light" onClick={handleLogout}>Logout</Button>
              </>
            ) : (
              <Nav.Link as={Link} to="/login">Login</Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default NavigationBar;
