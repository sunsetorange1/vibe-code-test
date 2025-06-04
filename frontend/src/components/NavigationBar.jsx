// frontend/src/components/NavigationBar.jsx
import React from 'react';
import { Navbar, Nav, Container, Button } from 'react-bootstrap'; // Added Button for logout
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function NavigationBar() {
  const { isAuthenticated, user, logout, isLoading } = useAuth(); // Assuming isLoading from AuthContext
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout(); // AuthContext logout clears local state and storage
      navigate('/login');
    } catch (error) {
      console.error("Failed to logout:", error);
      // Handle logout error if necessary, though typically client-side logout is straightforward
    }
  };

  // Optional: Don't render anything or render a minimal bar if auth state is still loading
  // This might prevent a flicker if the user is authenticated but isLoading is briefly true.
  // For this iteration, we'll allow the flicker to simplify, but this is a good spot for enhancement.
  // if (isLoading) {
  //   return (
  //     <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
  //       <Container>
  //         <Navbar.Brand as={Link} to="/">My Sec Platform</Navbar.Brand>
  //         <Navbar.Text>Loading user...</Navbar.Text>
  //       </Container>
  //     </Navbar>
  //   );
  // }

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-3">
      <Container>
        <Navbar.Brand as={Link} to="/">My Sec Platform</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            <Nav.Link as={Link} to="/">Home</Nav.Link>
            {isAuthenticated && ( // Show Projects link only if authenticated
              <Nav.Link as={Link} to="/projects">Projects</Nav.Link>
            )}
            {/* Example: Add a link to Users page if authenticated */}
            {/* {isAuthenticated && (
              <Nav.Link as={Link} to="/users">Users</Nav.Link> // Assuming /users is a protected route
            )} */}
          </Nav>
          <Nav>
            {isLoading ? (
              <Navbar.Text>Loading...</Navbar.Text>
            ) : isAuthenticated ? (
              <>
                <Navbar.Text className="me-2">
                  Signed in as: {user?.username || user?.email || 'User'}
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
