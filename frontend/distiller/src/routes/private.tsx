import React from 'react';

import { Route, Redirect, RouteProps} from 'react-router-dom';

import { useAppSelector } from '../app/hooks';
import { authStatus } from '../features/auth';

interface Props extends RouteProps {
  redirect: string;
}

const PrivateRoute: React.FC<Props> = (props) => {
  const {children, redirect, ...rest} = props;

  const status = useAppSelector(authStatus);

  return (
    <Route
      {...rest}
      render={({ location }) =>
        status === 'authenticated'
        ? (children)
        : status === 'unknown'
        ? null
        : (
          <Redirect
            to={{
              pathname: redirect,
              state: { from: location }
            }}
          />
        )
      }
    />
  );
}

export default PrivateRoute;
