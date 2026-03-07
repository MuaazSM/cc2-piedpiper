import './styles/globals.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

// Test imports one by one — uncomment each line, save, check browser
// If browser goes white after uncommenting a line = THAT is the crash

import App from './App'
// import FoxMascot from './components/FoxMascot'
// import Sidebar from './components/layout/Sidebar'
// import Home from './pages/Home'
// import Shipments from './pages/Shipments'
// import Optimize from './pages/Optimize'
// import Scenarios from './pages/Scenarios'
// import Insights from './pages/Insights'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)