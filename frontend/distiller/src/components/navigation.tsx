import React from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import makeStyles from '@mui/styles/makeStyles';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import HomeIcon from '@mui/icons-material/Home';
import ScansIcon from '@mui/icons-material/List';

import { HOME_PATH, SCANS_PATH } from '../routes';

const useStyles = makeStyles({
  root: {
    width: '100%',
  },
});

type NavPath = {
  pathname: string;
  icon: React.ReactNode;
  label: string;
};

const PATHS: { [name: string]: NavPath } = (
  [
    { pathname: HOME_PATH, icon: <HomeIcon />, label: 'Home' },
    { pathname: SCANS_PATH, icon: <ScansIcon />, label: 'Scans' },
  ] as const
).reduce((paths, path) => {
  paths[path.pathname] = { ...path };
  return paths;
}, {} as { [name: string]: NavPath });

const NavigationComponent: React.FC = () => {
  const classes = useStyles();

  const location = useLocation();
  const navigate = useNavigate();

  return (
    <BottomNavigation
      value={location.pathname}
      onChange={(_event, pathname) => {
        navigate(pathname);
      }}
      showLabels
      className={classes.root}
    >
      {Object.values(PATHS).map(({ pathname, icon, label }) => (
        <BottomNavigationAction
          key={pathname}
          value={pathname}
          label={label}
          icon={icon}
        />
      ))}
    </BottomNavigation>
  );
};

export default NavigationComponent;
