import React from 'react';

import { useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import { Button, IconButton } from '@mui/material';
import UserIcon from '@mui/icons-material/AccountCircle';
import makeStyles from '@mui/styles/makeStyles';

import { isAuthenticated } from '../features/auth';
import { AUTH_PATH } from '../routes';

import logo from '../logo.png';

const useStyles = makeStyles((theme) => ({
  logo: {
    height: theme.spacing(5),
  },
  title: {
    flexGrow: 1,
  },
}));

const HeaderComponent: React.FC = () => {
  const classes = useStyles();

  const authenticated = useAppSelector(isAuthenticated);

  const location = useLocation();

  const navigate = useNavigate();

  const onLogoClick = () => {
    const microscope = location.pathname.split('/')[1];

    navigate(`/${microscope}`);
  };

  const onUserClick = () => {
    navigate(`${AUTH_PATH}`, { state: { from: location } });
  };

  return (
    <AppBar color="transparent" position="static">
      <Toolbar>
        <Button onClick={onLogoClick}>
          <img className={classes.logo} src={logo} alt="logo" />
        </Button>
        <div className={classes.title} />
        {authenticated ? (
          <IconButton onClick={onUserClick} size="large">
            <UserIcon />
          </IconButton>
        ) : (
          <Button onClick={onUserClick}>Log In</Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default HeaderComponent;
