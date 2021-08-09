import React from 'react';

import { useHistory } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import { Button, IconButton } from '@material-ui/core';
import UserIcon from '@material-ui/icons/AccountCircle';
import { makeStyles } from '@material-ui/core/styles';

import { isAuthenticated } from '../features/auth';
import { HOME_PATH, AUTH_PATH } from '../routes';

import logo from '../logo.png';

const useStyles = makeStyles((theme) => ({
  logo: {
    height: theme.spacing(5)
  },
  title: {
    flexGrow: 1
  }
}));

const HeaderComponent: React.FC = () => {
  const classes = useStyles();

  const authenticated = useAppSelector(isAuthenticated);

  const history = useHistory();

  const onLogoClick = () => {
    history.push(HOME_PATH);
  }

  const onUserClick = () => {
    history.push(AUTH_PATH);
  }

  return (
    <AppBar color='transparent' position='static'>
      <Toolbar>
        <Button onClick={onLogoClick}>
          <img className={classes.logo} src={logo} alt='logo' />
        </Button>
        <div className={classes.title}/>
        {
          authenticated
          ? <IconButton onClick={onUserClick}>
              <UserIcon/>
            </IconButton>
          : <Button onClick={onUserClick}>
              Log In
            </Button>
        }
      </Toolbar>
    </AppBar>
  )
}

export default HeaderComponent;
