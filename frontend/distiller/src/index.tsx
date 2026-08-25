import React from 'react';

import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';

import App from './App';
import { store } from './app/store';
import './index.css';
import * as serviceWorker from './serviceWorker';

window.addEventListener('vite:preloadError', (event) => {
  // A deployment may remove a lazy chunk referenced by an already open app.
  // Reload so index.html points to the current set of hashed assets.
  event.preventDefault();
  window.location.reload();
});

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>,
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
