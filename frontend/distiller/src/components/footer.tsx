import React from 'react';

import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import Icon from '@mui/material/Icon';
import kitware from '../kitware.svg';

const KitwareLogoIcon: React.FC = () => {
  return (
    <Icon sx={{ width: 100 }}>
      <img src={kitware} alt="Kitware Logo" />
    </Icon>
  );
};

const FooterComponent: React.FC = () => {
  return (
    <BottomNavigation>
      <BottomNavigationAction
        icon={<KitwareLogoIcon />}
        href="https://kitware.com/"
        disableRipple={true}
      />
    </BottomNavigation>
  );
};

export default FooterComponent;
