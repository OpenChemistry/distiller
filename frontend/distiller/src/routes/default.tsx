import React from 'react';

import { Navigate, useLocation } from 'react-router-dom';

import { useAppSelector } from '../app/hooks';
import { authStatus } from '../features/auth';
import { AUTH_PATH } from '../routes';

const DefaultMicroscope = () => {
  const location = useLocation();
  const microscopeLocation = { ...location };
  microscopeLocation.pathname = `/4dcamera${location.pathname}`;

  return <Navigate to={microscopeLocation} replace />;
};

export default DefaultMicroscope;
