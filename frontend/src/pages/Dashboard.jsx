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

  const isDbConnected = dbStatus === 'Connected'
  const numericPolicyCount = parseInt(policyCount, 10)
  const isProtectionActive = isDbConnected && !isNaN(numericPolicyCount) && numericPolicyCount > 0

  return (
    <div className="dashboard">
      <h2>System Dashboard</h2>
      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>Database Status</h3>
          <p className="stat-value" style={{ color: isDbConnected ? '#166534' : '#991b1b' }}>
            {dbStatus}
          </p>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
            PostgreSQL Connection
          </div>
        </div>

        <div className="stat-card">
          <h3>Database Protection</h3>
          <p className="stat-value" style={{ color: isProtectionActive ? '#166534' : '#475569' }}>
            {isProtectionActive ? 'Active' : isDbConnected ? 'Ready' : 'Unavailable'}
          </p>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
            {isProtectionActive ? 'DB-level masking enabled' : 'No active policies'}
          </div>
        </div>

        <div className="stat-card">
          <h3>Active Policies</h3>
          <p className="stat-value" style={{ color: '#2563eb' }}>
            {policyCount}
          </p>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
            Enforced masking rules
          </div>
        </div>

        <div className="stat-card">
          <h3>Monitored Tables</h3>
          <p className="stat-value" style={{ color: '#0f172a' }}>
            {tableCount}
          </p>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
            Database tables in schema
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
