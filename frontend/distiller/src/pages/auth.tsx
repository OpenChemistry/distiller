import React, { FormEvent, MouseEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import Avatar from '@mui/material/Avatar';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { styled } from '@mui/material/styles';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { getUser, isAuthenticated, login, logout } from '../features/auth';

const Paper = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(8),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
}));

const StyledAvatar = styled(Avatar)(({ theme }) => ({
  margin: theme.spacing(1),
  backgroundColor: theme.palette.secondary.light,
}));

const SubmitButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(3, 0, 2),
}));

const Form = styled('form')(({ theme }) => ({
  width: '100%', // Fix IE 11 issue.
  marginTop: theme.spacing(1),
}));

const AuthPage: React.FC = () => {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');

  const authState = useAppSelector((state) => state.auth.status);

  const authenticated = useAppSelector(isAuthenticated);
  const user = useAppSelector(getUser);
  const dispatch = useAppDispatch();

  const [error, setError] = React.useState('');

  const navigate = useNavigate();
  const location: any = useLocation();

  const { from } = location.state || { from: { pathname: '/' } };

  const onLogin = (e: FormEvent) => {
    e.preventDefault();
    setError('');

    dispatch(login({ username, password, from })).then((res) => {
      if (res.type === login.fulfilled.toString()) {
        navigate(from, { replace: true });
      } else {
        setError('Unable to login with the provided credentials.');
      }
    });
  };

  const onLogout = async (_e: MouseEvent) => {
    await dispatch(logout());
    navigate(from, { replace: true });
  };

  return (
    <React.Fragment>
      <Paper>
        <StyledAvatar>
          <LockOutlinedIcon />
        </StyledAvatar>
        {authenticated ? (
          <React.Fragment>
            <Typography component="h1" variant="h5">
              {user?.username}
            </Typography>
            <SubmitButton
              fullWidth
              variant="contained"
              color="primary"
              onClick={onLogout}
            >
              Sign out
            </SubmitButton>
          </React.Fragment>
        ) : (
          <React.Fragment>
            <Typography component="h1" variant="h5">
              Sign in
            </Typography>
            <Form noValidate onSubmit={onLogin}>
              <TextField
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                variant="outlined"
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                error={error.length > 0}
                autoFocus
              />
              <TextField
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                variant="outlined"
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                error={error.length > 0}
              />
              <SubmitButton
                type="submit"
                fullWidth
                variant="contained"
                color="primary"
                disabled={
                  username.length === 0 ||
                  password.length === 0 ||
                  authState === 'authenticating'
                }
              >
                Sign In
              </SubmitButton>
              <Typography color="error">{error}</Typography>
            </Form>
          </React.Fragment>
        )}
      </Paper>
    </React.Fragment>
  );
};

export default AuthPage;
