import React from 'react';

import UserIcon from '@mui/icons-material/AccountCircle';
import { Button, IconButton, Typography } from '@mui/material';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import { styled } from '@mui/material/styles';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../app/hooks';
import { isAuthenticated } from '../features/auth';
import {
  microscopesSelectors,
  microscopesState,
} from '../features/microscopes';
import logo from '../logo.png';
import { AUTH_PATH } from '../routes';
import { getMicroscope } from '../utils/microscopes';

const LogoImage = styled('img')(({ theme }) => ({
  height: theme.spacing(5),
}));

const Title = styled('img')(({ theme }) => ({
  flexGrow: 1,
}));

type Props = {
  showLogin?: boolean;
};

const HeaderComponent: React.FC<Props> = (props) => {
  const { showLogin = true } = props;
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

  let microscope = null;
  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state)),
  );
  if (authenticated) {
    const microscopeName = location.pathname.split('/')[1];
    microscope = getMicroscope(microscopes, microscopeName);
  }

  return (
    <AppBar color="transparent" position="static">
      <Toolbar>
        <Button onClick={onLogoClick}>
          <LogoImage src={logo} alt="logo" />
        </Button>
        {authenticated && (
          <Typography variant="h5" color="text.secondary">
            {microscope !== null ? microscope.name : ''}
          </Typography>
        )}
        <Title />
        {showLogin && (
          <React.Fragment>
            {authenticated ? (
              <IconButton onClick={onUserClick} size="large">
                <UserIcon />
              </IconButton>
            ) : (
              <Button onClick={onUserClick}>Log In</Button>
            )}
          </React.Fragment>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default HeaderComponent;
