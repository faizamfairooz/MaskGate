import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import SchemaBrowser from './pages/SchemaBrowser'
import MaskingPolicies from './pages/MaskingPolicies'
import QueryEditor from './pages/QueryEditor'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="maskgate-ui-theme">
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/schema" element={<SchemaBrowser />} />
          <Route path="/masking" element={<MaskingPolicies />} />
          <Route path="/query" element={<QueryEditor />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  )
}

export default App
