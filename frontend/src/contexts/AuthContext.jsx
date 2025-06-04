// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
// Assuming an authService for API calls, or integrate directly
// For now, we'll sketch the login API call here, but it should ideally be in api.js or authService.js
import { login as apiLogin, getAuthenticatedUserProfile } from '../services/api'; // We'll need to add these to api.js

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    try {
      return storedUser ? JSON.parse(storedUser) : null;
    } catch (error) {
      console.error("Failed to parse stored user from localStorage:", error);
      localStorage.removeItem('user'); // Clear corrupted item
      return null;
    }
  });
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token')); // Initial state based on token
  const [isLoading, setIsLoading] = useState(true); // To manage initial loading state

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    // navigate('/login'); // Navigation should be handled by calling component or router
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
      getAuthenticatedUserProfile() // Uses token from localStorage via api.js's getToken
        .then(profile => {
          setUser(profile);
          localStorage.setItem('user', JSON.stringify(profile)); // Update stored user
          setIsAuthenticated(true);
        })
        .catch(() => { // Token might be invalid/expired
          logout(); // Clear stored token and user data
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false); // No token, not loading
    }
  }, [logout]);


  const login = async (emailOrUsername, password) => {
    try {
      // The backend /auth/login endpoint expects 'username' and 'password'
      const loginData = await apiLogin({ username: emailOrUsername, password });
      localStorage.setItem('token', loginData.access_token);
      setToken(loginData.access_token);

      // Fetch user profile after successful login
      const profile = await getAuthenticatedUserProfile(); // Uses new token now set in localStorage
      setUser(profile);
      localStorage.setItem('user', JSON.stringify(profile)); // Store user profile
      setIsAuthenticated(true); // Set after profile fetch is successful
      return profile;
    } catch (error) {
      logout(); // Clear any partial state on login failure
      throw error; // Re-throw to allow calling component to handle
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, login, logout, isLoading, setUser, setToken, setIsAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
};
