import React, { useEffect } from 'react';

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { CssBaseline } from '@mui/material';

import './App.css';
import PrivateRoute from './routes/private';
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
                  <Route path={AUTH_PATH} element={<AuthPage />} />
                  <Route
                    path={`${SCANS_PATH}/:scanId`}
                    element={
                      <PrivateRoute>
                        <ScanPage />
                      </PrivateRoute>
                    }
                  />
                  <Route
                    path={HOME_PATH}
                    element={
                      <PrivateRoute>
                        <ScansPage />
                      </PrivateRoute>
                    }
                  />
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
