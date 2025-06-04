// frontend/src/hooks/useHasRole.js
import { useAuth } from '../contexts/AuthContext';

export const useHasRole = (requiredRoles) => {
  const { user, isAuthenticated, isLoading } = useAuth(); // Added isLoading from useAuth

  // If auth state is still loading, we can't reliably determine role yet.
  // Depending on desired behavior, could return false or a specific "loading" state.
  // For now, returning false as role is not yet confirmed.
  if (isLoading) {
    return false;
  }

  if (!isAuthenticated || !user || !user.role) {
    return false;
  }

  if (!Array.isArray(requiredRoles)) {
    console.warn('useHasRole: requiredRoles parameter should be an array of strings.');
    return false;
  }

  if (requiredRoles.length === 0) {
    console.warn('useHasRole: requiredRoles array is empty. This will deny access by default.');
    return false;
  }

  return requiredRoles.includes(user.role);
};
