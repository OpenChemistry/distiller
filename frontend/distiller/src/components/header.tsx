import React from 'react';

import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import { Button, IconButton } from '@mui/material';
import UserIcon from '@mui/icons-material/AccountCircle';
import { styled } from '@mui/material/styles';

import { isAuthenticated } from '../features/auth';
import { HOME_PATH, AUTH_PATH } from '../routes';

import logo from '../logo.png';

const LogoImage = styled('img')(({ theme }) => ({
  height: theme.spacing(5),
}));

const Title = styled('img')(({ theme }) => ({
  flexGrow: 1,
}));

const HeaderComponent: React.FC = () => {
  const authenticated = useAppSelector(isAuthenticated);

  const navigate = useNavigate();

  const onLogoClick = () => {
    navigate(HOME_PATH);
  };

  const onUserClick = () => {
    navigate(AUTH_PATH);
  };

  return (
    <AppBar color="transparent" position="static">
      <Toolbar>
        <Button onClick={onLogoClick}>
          <LogoImage src={logo} alt="logo" />
        </Button>
        <Title />
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
