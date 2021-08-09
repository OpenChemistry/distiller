import React from 'react';

import {
  BrowserRouter as Router,
  Switch,
  Route,
} from "react-router-dom";

import { CssBaseline } from '@material-ui/core';

import './App.css';
import PrivateRoute from './routes/private';
import {
  HOME_PATH,
  AUTH_PATH,
} from './routes';
import ScansPage from './pages/scans';
import AuthPage from './pages/auth';
import HeaderComponent from './components/header';

function App() {
  return (
    <Router>
      <div className="app">
        <CssBaseline/>
        <div className="header">
          <HeaderComponent/>
        </div>
        <div className="content">
          <div className="inner-content">
            <Switch>
              <Route path={AUTH_PATH}>
                <AuthPage/>
              </Route>
              <PrivateRoute path={HOME_PATH} redirect={AUTH_PATH}>
                <ScansPage/>
              </PrivateRoute>
            </Switch>
          </div>
        </div>
        <div className="navigation">
        </div>
      </div>
    </Router>
  );
}

export default App;
