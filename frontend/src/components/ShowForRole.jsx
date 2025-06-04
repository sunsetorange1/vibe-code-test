// frontend/src/components/ShowForRole.jsx
import React from 'react';
import { useHasRole } from '../hooks/useHasRole';

const ShowForRole = ({ roles, children }) => {
  const userHasRequiredRole = useHasRole(roles);

  if (!userHasRequiredRole) {
    return null;
  }

  return <>{children}</>;
};

export default ShowForRole;
