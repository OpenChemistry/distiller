import React, { FormEvent, MouseEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

import Avatar from '@material-ui/core/Avatar';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import LockOutlinedIcon from '@material-ui/icons/LockOutlined';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';

import { useAppDispatch, useAppSelector } from '../app/hooks';
import { login, logout, getUser, isAuthenticated } from '../features/auth';

const useStyles = makeStyles((theme) => ({
  paper: {
    marginTop: theme.spacing(8),
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  avatar: {
    margin: theme.spacing(1),
    backgroundColor: theme.palette.secondary.main,
  },
  form: {
    width: '100%', // Fix IE 11 issue.
    marginTop: theme.spacing(1),
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
}));

const AuthPage: React.FC = () => {
  const classes = useStyles();

  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');

  const authState = useAppSelector(state => state.auth.status);

  const authenticated = useAppSelector(isAuthenticated);
  const user = useAppSelector(getUser);
  const dispatch = useAppDispatch();

  const [error, setError] = React.useState('');

  const navigate = useNavigate();
  const location: any = useLocation();

  const { from } = location.state || { from: { pathname: "/" } };

  const onLogin = (e: FormEvent) => {
    e.preventDefault();
    setError('');

    dispatch(login({username, password})).then(res => {
      if (res.type === login.fulfilled.toString()) {
        navigate(from, { replace: true })
      } else {
        setError('Unable to login with the provided credentials.');
      }
    });
  }

  const onLogout = (_e: MouseEvent) => {
    dispatch(logout());
  }

  return (
    <React.Fragment>
    <div className={classes.paper}>
      <Avatar className={classes.avatar}>
        <LockOutlinedIcon />
      </Avatar>
      { authenticated
        ? <React.Fragment>
            <Typography component="h1" variant="h5">
              {user?.username}
            </Typography>
            <Button
              fullWidth
              variant="contained"
              color="primary"
              className={classes.submit}
              onClick={onLogout}
            >
              Sign out
            </Button>
          </React.Fragment>
        : <React.Fragment>
          <Typography component="h1" variant="h5">
            Sign in
          </Typography>
          <form className={classes.form} noValidate onSubmit={onLogin}>
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
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              className={classes.submit}
              disabled={(
                username.length === 0 ||
                password.length === 0 ||
                authState === 'authenticating'
              )}
            >
              Sign In
            </Button>
            <Typography color='error'>{error}</Typography>
          </form>
        </React.Fragment>
      }
    </div>
    </React.Fragment>
  )
}

export default AuthPage;
