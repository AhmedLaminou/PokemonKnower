import React from 'react';
import './index.css';
import App from './App';

const root = document.getElementById('root');
if (root) {
  const ReactDOM = require('react-dom/client');
  const appRoot = ReactDOM.createRoot(root);
  appRoot.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
