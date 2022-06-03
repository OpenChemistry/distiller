import React from 'react';

import { Navigate, useLocation } from 'react-router-dom';

const DefaultMicroscope = () => {
  const location = useLocation();
  const microscopeLocation = { ...location };
  microscopeLocation.pathname = `/4dcamera${location.pathname}`;

  return <Navigate to={microscopeLocation} replace />;
};

export default DefaultMicroscope;
