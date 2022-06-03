import React, { useEffect } from 'react';

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { CssBaseline } from '@mui/material';

import './App.css';
import PrivateRoute from './routes/private';
import DefaultMicroscope from './routes/default';
import { HOME_PATH, AUTH_PATH, SCANS_PATH } from './routes';
import ScansPage from './pages/scans';
import AuthPage from './pages/auth';
import ScanPage from './pages/scan';
import HeaderComponent from './components/header';
import { useAppDispatch } from './app/hooks';
import { restoreSession } from './features/auth';

import {
  ThemeProvider,
  Theme,
  StyledEngineProvider,
  createTheme,
} from '@mui/material/styles';

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

const theme = createTheme();

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
            <div className="content">
              <div className="inner-content">
                <Routes>
                  <Route
                    path={`/:microscope${SCANS_PATH}/:scanId`}
                    element={
                      <PrivateRoute>
                        <ScanPage />
                      </PrivateRoute>
                    }
                  />
                  <Route
                    path={'/:microscope'}
                    element={
                      <PrivateRoute>
                        <ScansPage />
                      </PrivateRoute>
                    }
                  />
                  Change underscore to dashes in url ...
                  <Route
                    path={`${SCANS_PATH}/:scanId`}
                    element={<DefaultMicroscope />}
                  />
                  <Route path={SCANS_PATH} element={<DefaultMicroscope />} />
                  <Route path={HOME_PATH} element={<DefaultMicroscope />} />
                  <Route path={AUTH_PATH} element={<AuthPage />} />
                </Routes>
              </div>
            </div>
            <div className="navigation"></div>
          </div>
        </Router>
      </ThemeProvider>
    </StyledEngineProvider>
  );
}

export default App;
