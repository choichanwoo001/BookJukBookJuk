import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { initCatalog } from './bootstrap/catalogInit.js'

initCatalog().then(() => import('./App.jsx')).then(({ default: App }) => {
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
})
