import { Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import Layout from '@/components/layout/Layout'
import Home      from '@/pages/Home'
import Shipments from '@/pages/Shipments'
import Optimize  from '@/pages/Optimize'
import Scenarios from '@/pages/Scenarios'
import Insights  from '@/pages/Insights'

const PAGE_THEMES = {
  '/':          'home',
  '/shipments': 'shipments',
  '/optimize':  'optimize',
  '/scenarios': 'scenarios',
  '/insights':  'insights',
}

export default function App() {
  const location = useLocation()

  useEffect(() => {
    const theme = PAGE_THEMES[location.pathname] ?? 'home'
    document.body.setAttribute('data-page', theme)
  }, [location.pathname])

  return (
    <>
      <div className="page-bg" aria-hidden="true" style={{ zIndex: 0 }} />

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#141414',
            color: '#f5f5f5',
            border: '1px solid rgba(255,255,255,0.08)',
            fontFamily: "'DM Sans', sans-serif",
          },
        }}
      />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/shipments" element={<Layout><Shipments /></Layout>} />
        <Route path="/optimize"  element={<Layout><Optimize /></Layout>} />
        <Route path="/scenarios" element={<Layout><Scenarios /></Layout>} />
        <Route path="/insights"  element={<Layout><Insights /></Layout>} />
      </Routes>
    </>
  )
}