import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import { store } from './app/store';
import { Provider } from 'react-redux';
import * as serviceWorker from './serviceWorker';

import * as Sentry from '@sentry/react';
import { Integrations } from '@sentry/tracing';

if (process.env.REACT_APP_SENTRY_DSN_URL !== undefined) {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN_URL,
    integrations: [new Integrations.BrowserTracing()],
  });
}

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
