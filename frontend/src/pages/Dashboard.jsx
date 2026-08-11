import React, { useEffect, useState } from 'react'
import { healthAPI, schemaAPI, maskingAPI } from '../services/api'

function Dashboard() {
  const [dbStatus, setDbStatus] = useState('Checking...')
  const [tableCount, setTableCount] = useState('—')
  const [policyCount, setPolicyCount] = useState('—')

  useEffect(() => {
    healthAPI.checkDatabase()
      .then((res) => setDbStatus(res.data.status === 'healthy' ? 'Connected' : 'Unavailable'))
      .catch(() => setDbStatus('Unavailable'))

    schemaAPI.getTables()
      .then((res) => setTableCount(String(res.data.length)))
      .catch(() => setTableCount('—'))

    maskingAPI.getPolicies()
      .then((res) => setPolicyCount(String(res.data.length)))
      .catch(() => setPolicyCount('—'))
  }, [])

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>Database Status</h3>
          <p className="stat-value">{dbStatus}</p>
        </div>
        <div className="stat-card">
          <h3>Active Policies</h3>
          <p className="stat-value">{policyCount}</p>
        </div>
        <div className="stat-card">
          <h3>Demo Tables</h3>
          <p className="stat-value">{tableCount}</p>
        </div>
        <div className="stat-card">
          <h3>API</h3>
          <p className="stat-value">/api/v1</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
