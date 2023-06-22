import React, { useEffect } from 'react';

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { CssBaseline } from '@mui/material';

import './App.css';
import PrivateRoute from './routes/private';
import DefaultMicroscope from './routes/default';
import {
  HOME_PATH,
  AUTH_PATH,
  SCANS_PATH,
  SCANS,
  SESSIONS_PATH,
  SESSIONS,
} from './routes';
import ScansPage from './pages/scans';
import AuthPage from './pages/auth';
import ScanPage from './pages/scan';
import SessionPage from './pages/session';
import SessionsPage from './pages/sessions';
import HeaderComponent from './components/header';
import FooterComponent from './components/footer';
import NavigationComponent from './components/navigation';
import { useAppDispatch, useShouldShowNavigation } from './app/hooks';
import { restoreSession } from './features/auth';
import {
  ThemeProvider,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

const theme = createTheme();

const NavigationAndRoutes: React.FC = () => {
  const showNavigation = useShouldShowNavigation();

  return (
    <div className="content">
      <div className="inner-content">
        <Routes>
          <Route
            path={`/:microscope/${SESSIONS}`}
            element={
              <PrivateRoute>
                <SessionsPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SESSIONS}/:jobId`}
            element={
              <PrivateRoute>
                <SessionPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SESSIONS}/:jobId/${SCANS}/:scanId`}
            element={
              <PrivateRoute>
                <ScanPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SCANS}/:scanId`}
            element={
              <PrivateRoute>
                <ScanPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SCANS}`}
            element={
              <PrivateRoute>
                <ScansPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/`}
            element={
              <PrivateRoute>
                <ScansPage />
              </PrivateRoute>
            }
          />
          <Route
            path={`${SCANS_PATH}/:scanId`}
            element={<DefaultMicroscope />}
          />
          <Route path={SESSIONS_PATH} element={<DefaultMicroscope />} />
          <Route path={SCANS_PATH} element={<DefaultMicroscope />} />
          <Route path={AUTH_PATH} element={<AuthPage />} />
          <Route path={HOME_PATH} element={<DefaultMicroscope />} />
        </Routes>
      </div>
      {showNavigation && (
        <div className="navigation">
          <NavigationComponent />
        </div>
      )}
    </div>
  );
};

function App() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(restoreSession());
  }, [dispatch]);

  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={theme}>
        <Router>
          <div className="app">
            <CssBaseline />
            <div className="header">
              <HeaderComponent />
            </div>
            <NavigationAndRoutes />
            <div className="footer">
              <FooterComponent />
            </div>
          </div>
        </Router>
      </ThemeProvider>
    </StyledEngineProvider>
  );
}

export default App;
