import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

import { useAppDispatch, useAppSelector } from '../../app/hooks';
import { authStatus } from '../auth';
import { microscopesSelectors, microscopesState } from '../microscopes';
import { isStatic } from '../../utils';
import { getMicroscopeIdForPath } from '../../utils/microscopes';
import {
  connectNotifications,
  disconnectNotifications,
  notificationMicroscopeID,
} from '.';

const NotificationSubscription: React.FC = () => {
  const dispatch = useAppDispatch();
  const location = useLocation();
  const status = useAppSelector(authStatus);
  const activeMicroscopeID = useAppSelector(notificationMicroscopeID);
  const microscopes = useAppSelector((state) =>
    microscopesSelectors.selectAll(microscopesState(state)),
  );

  useEffect(() => {
    // Only connect notifications if not in static mode
    if (isStatic()) {
      return;
    }

    if (status !== 'authenticated') {
      if (activeMicroscopeID !== undefined) {
        dispatch(disconnectNotifications());
      }
      return;
    }

    if (microscopes.length === 0) {
      return;
    }

    let microscopeID;
    try {
      microscopeID = getMicroscopeIdForPath(microscopes, location.pathname);
    } catch {
      return;
    }

    if (microscopeID === activeMicroscopeID) {
      return;
    }

    dispatch(connectNotifications({ microscopeID }));
  }, [activeMicroscopeID, dispatch, location.pathname, microscopes, status]);

  return null;
};

export default NotificationSubscription;
