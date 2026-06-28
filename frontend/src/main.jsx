import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { resetDemoOnPageLoad } from './utils/demoStorage.js';
import './styles/tokens.css';
import './index.css';

resetDemoOnPageLoad();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
