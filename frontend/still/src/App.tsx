import React from 'react';

import {
  BrowserRouter as Router,
  Switch,
  Route,
} from "react-router-dom";

import { CssBaseline } from '@material-ui/core';

import './App.css';
import HomePage from './pages/home';
import PrivateRoute from './routes/private';
import {
  HOME_PATH,
  AUTH_PATH,
  SCANS_PATH,
} from './routes';
import ScansPage from './pages/scans';
import AuthPage from './pages/auth';
import HeaderComponent from './components/header';
import NavigationComponent from './components/navigation';

function App() {
  return (
    <Router>
      <div className="app">
        <CssBaseline/>
        <div className="header">
          <HeaderComponent/>
        </div>
        <div className="content">
          <Switch>
            <Route path={AUTH_PATH}>
              <AuthPage/>
            </Route>
            <PrivateRoute path={SCANS_PATH} redirect={AUTH_PATH}>
              <ScansPage/>
            </PrivateRoute>
            <Route path={HOME_PATH}>
              <HomePage/>
            </Route>
          </Switch>
        </div>
        <div className="navigation">
          <NavigationComponent/>
        </div>
      </div>
    </Router>
  );
}

export default App;
