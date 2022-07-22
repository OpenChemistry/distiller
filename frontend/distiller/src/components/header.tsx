import React from 'react';

import { useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';

import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import { Button, IconButton } from '@mui/material';
import UserIcon from '@mui/icons-material/AccountCircle';
import { styled } from '@mui/material/styles';

import { isAuthenticated } from '../features/auth';
import { AUTH_PATH } from '../routes';

import logo from '../logo.png';

const LogoImage = styled('img')(({ theme }) => ({
  height: theme.spacing(5),
}));

const Title = styled('img')(({ theme }) => ({
  flexGrow: 1,
}));

const HeaderComponent: React.FC = () => {
  const authenticated = useAppSelector(isAuthenticated);

  const location: any = useLocation();

  const navigate = useNavigate();

  const onLogoClick = () => {
    if (location.state !== null) {
      const { from } = location.state;
      navigate(from);
    } else {
      const microscope = location.pathname.split('/')[1];
      navigate(`/${microscope}`);
    }
  };

  const onUserClick = () => {
    navigate(`${AUTH_PATH}`, { state: { from: location } });
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
