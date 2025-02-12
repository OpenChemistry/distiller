import React, { useEffect } from 'react';
import { Route, HashRouter, BrowserRouter, Routes } from 'react-router-dom';

import { CssBaseline } from '@mui/material';
import {
  StyledEngineProvider,
  ThemeProvider,
  createTheme,
} from '@mui/material/styles';
import './App.css';
import { useAppDispatch, useShouldShowNavigation } from './app/hooks';
import FooterComponent from './components/footer';
import HeaderComponent from './components/header';
import NavigationComponent from './components/navigation';
import { restoreSession } from './features/auth';
import AuthPage from './pages/auth';
import ScanPage from './pages/scan';
import ScansPage from './pages/scans';
import SessionPage from './pages/session';
import SessionsPage from './pages/sessions';
import InteractemPage from './pages/interactem';
import {
  AUTH_PATH,
  HOME_PATH,
  SCANS,
  SCANS_PATH,
  SESSIONS,
  SESSIONS_PATH,
  INTERACTEM,
  INTERACTEM_PATH,
} from './routes';
import DefaultMicroscope from './routes/default';
import PrivateRoute from './routes/private';
import { mockEndpoints } from './utils/mock';
import { isStatic } from './utils';

let Router = BrowserRouter;
if (isStatic()) {
  mockEndpoints();
  Router = HashRouter;
}

const theme = createTheme();

const NavigationAndRoutes: React.FC = () => {
  const showNavigation = useShouldShowNavigation();

  return (
    <div className="content">
      <div className="inner-content">
        <Routes>
          <Route
            path={`/:microscope/${INTERACTEM}`}
            element={
              <PrivateRoute>
                <InteractemPage />
              </PrivateRoute>
            }
          />
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
                <ScanPage mutable={!isStatic()} />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SCANS}/:scanId`}
            element={
              <PrivateRoute>
                <ScanPage mutable={!isStatic()} />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/${SCANS}`}
            element={
              <PrivateRoute>
                <ScansPage
                  allowExport={!isStatic()}
                  allowFilter={!isStatic()}
                  showDiskUsage={!isStatic()}
                  mutable={!isStatic()}
                />
              </PrivateRoute>
            }
          />
          <Route
            path={`/:microscope/`}
            element={
              <PrivateRoute>
                <ScansPage
                  allowExport={!isStatic()}
                  allowFilter={!isStatic()}
                  showDiskUsage={!isStatic()}
                  mutable={!isStatic()}
                />
              </PrivateRoute>
            }
          />
          <Route
            path={`${SCANS_PATH}/:scanId`}
            element={<DefaultMicroscope />}
          />
          <Route path={INTERACTEM_PATH} element={<DefaultMicroscope />} />
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
              <HeaderComponent showLogin={!isStatic()} />
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
