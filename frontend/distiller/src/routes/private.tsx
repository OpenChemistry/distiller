import React from 'react';

import { Navigate, useLocation} from 'react-router-dom';

import { useAppSelector } from '../app/hooks';
import { authStatus } from '../features/auth';
import {
  AUTH_PATH
} from '../routes';

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  let location = useLocation();
  const status = useAppSelector(authStatus);

  if (status === 'authenticated') {
    return children;
  }
  else if (status === 'unknown') {
    return null;
  }

  return  <Navigate to={AUTH_PATH} state={{ from: location }} />
};

export default PrivateRoute;
