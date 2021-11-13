import React, {useEffect} from 'react';

import {
  BrowserRouter as Router,
  Routes,
  Route,
} from "react-router-dom";

import { CssBaseline } from '@material-ui/core';

import './App.css';
import PrivateRoute from './routes/private';
import {
  HOME_PATH,
  AUTH_PATH,
  SCANS_PATH,
} from './routes';
import ScansPage from './pages/scans';
import AuthPage from './pages/auth';
import ScanPage from './pages/scan';
import HeaderComponent from './components/header';
import { useAppDispatch } from './app/hooks';
import {restoreSession} from './features/auth';

import { ThemeProvider, createTheme } from '@material-ui/core/styles';

const theme = createTheme();

function App() {
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(restoreSession());
  }, [dispatch])

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <div className="app">
          <CssBaseline/>
          <div className="header">
            <HeaderComponent/>
          </div>
          <div className="content">
            <div className="inner-content">
              <Routes>
                <Route path={AUTH_PATH} element={<AuthPage/>}/>
                <Route
                  path={`${SCANS_PATH}/:scanId`}
                  element={
                    <PrivateRoute>
                      <ScanPage/>
                    </PrivateRoute>
                  }
                />
                <Route
                  path={HOME_PATH}
                  element={
                    <PrivateRoute>
                      <ScansPage/>
                    </PrivateRoute>
                  }
                />
              </Routes>
            </div>
          </div>
          <div className="navigation">
          </div>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
