import React from 'react';

import { Route, Redirect, RouteProps} from 'react-router-dom';

import { useAppSelector } from '../app/hooks';
import { isAuthenticated } from '../features/auth';

interface Props extends RouteProps {
  redirect: string;
}

const PrivateRoute: React.FC<Props> = (props) => {
  const {children, redirect, ...rest} = props;

  const authenticated = useAppSelector(isAuthenticated);

  return (
    <Route
      {...rest}
      render={({ location }) =>
        authenticated ? (
          children
        ) : (
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
