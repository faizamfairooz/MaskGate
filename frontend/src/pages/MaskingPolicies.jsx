import React, { useState, useEffect, useCallback } from 'react'
import { maskingAPI } from '../services/api'

function MaskingPolicies() {
  const [policies, setPolicies] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loadingPolicies, setLoadingPolicies] = useState(false)
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [tab, setTab] = useState('review') // 'review' or 'policies'
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [tableFilter, setTableFilter] = useState('')
  const [message, setMessage] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  const showNotification = (msg, isError = false) => {
    if (isError) {
      setErrorMessage(msg)
      setMessage(null)
    } else {
      setMessage(msg)
      setErrorMessage(null)
    }
    setTimeout(() => {
      setMessage(null)
      setErrorMessage(null)
    }, 5000)
  }

  const fetchPolicies = useCallback(async () => {
    setLoadingPolicies(true)
    try {
      const response = await maskingAPI.getPolicies('ACTIVE')
      setPolicies(response.data || [])
    } catch (error) {
      console.error('Failed to fetch policies:', error)
    } finally {
      setLoadingPolicies(false)
    }
  }, [])

  const fetchRecommendations = useCallback(async () => {
    setLoadingRecs(true)
    try {
      const params = {}
      if (statusFilter && statusFilter !== 'ALL') {
        params.status = statusFilter
      }
      if (tableFilter.trim()) {
        params.table_name = tableFilter.trim()
      }
      const response = await maskingAPI.getRecommendations(params)
      setRecommendations(response.data || [])
    } catch (error) {
      console.error('Failed to fetch recommendations:', error)
    } finally {
      setLoadingRecs(false)
    }
  }, [statusFilter, tableFilter])

  useEffect(() => {
    fetchPolicies()
  }, [fetchPolicies])

  useEffect(() => {
    fetchRecommendations()
  }, [fetchRecommendations])

  const handleAnalyzeAndQueue = async () => {
    setAnalyzing(true)
    try {
      const res = await maskingAPI.analyzeAndQueue({ schema: 'public' })
      const count = res.data?.length || 0
      showNotification(`AI Schema Analysis complete! Queued ${count} recommendation(s) for review.`)
      await fetchRecommendations()
    } catch (error) {
      console.error('Failed to analyze schema:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to run schema analysis'
      showNotification(detail, true)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleApprove = async (id, table, column) => {
    try {
      const res = await maskingAPI.approveRecommendation(id)
      showNotification(`Approved! Created active masking policy for "${table || res.data.table_name}.${column || res.data.column_name}".`)
      await fetchRecommendations()
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to approve recommendation:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to approve recommendation'
      showNotification(detail, true)
    }
  }

  const handleReject = async (id, table, column) => {
    try {
      await maskingAPI.rejectRecommendation(id)
      showNotification(`Rejected recommendation for "${table}.${column}". No policy created.`)
      await fetchRecommendations()
    } catch (error) {
      console.error('Failed to reject recommendation:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to reject recommendation'
      showNotification(detail, true)
    }
  }

  const handleDeletePolicy = async (policyId, policyName) => {
    try {
      await maskingAPI.deletePolicy(policyId)
      showNotification(`Policy "${policyName || policyId}" deactivated successfully`)
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to delete policy:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to delete policy'
      showNotification(detail, true)
    }
  }

  const pendingCount = recommendations.filter(r => r.status?.toUpperCase() === 'PENDING').length

  const getSensitivityBadgeClass = (level) => {
    const l = (level || '').toUpperCase()
    if (l === 'HIGH') return 'badge-high'
    if (l === 'MEDIUM') return 'badge-medium'
    return 'badge-low'
  }

  return (
    <div className="masking-policies-page" style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: '700', color: '#0f172a', margin: '0 0 0.25rem 0' }}>
            Data Masking Policy Management
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', margin: 0 }}>
            Review GenAI masking recommendations, approve or reject policies, and manage active PostgreSQL masking rules.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleAnalyzeAndQueue}
            disabled={analyzing}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: '#2563eb',
              color: 'white',
              border: 'none',
              padding: '0.6rem 1.2rem',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: analyzing ? 'not-allowed' : 'pointer',
            }}
          >
            <span>{analyzing ? '⏳' : '⚡'}</span>
            {analyzing ? 'Analyzing Schema...' : 'Run AI Schema Analysis'}
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => { fetchPolicies(); fetchRecommendations(); }}
            title="Refresh policies and recommendations"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Alerts */}
      {message && (
        <div style={{ padding: '0.85rem 1.25rem', marginBottom: '1.25rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '8px', color: '#065f46', fontWeight: '500' }}>
          ✓ {message}
        </div>
      )}
      {errorMessage && (
        <div style={{ padding: '0.85rem 1.25rem', marginBottom: '1.25rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontWeight: '500' }}>
          ⚠️ {errorMessage}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '1.5rem', gap: '0.5rem' }}>
        <button
          type="button"
          onClick={() => setTab('review')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: tab === 'review' ? '3px solid #2563eb' : '3px solid transparent',
            color: tab === 'review' ? '#2563eb' : '#64748b',
            fontWeight: '600',
            fontSize: '0.95rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>🤖 AI Recommendation Review Queue</span>
          {statusFilter === 'PENDING' && (
            <span style={{ background: '#dbeafe', color: '#1e40af', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.78rem' }}>
              {recommendations.length}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setTab('policies')}
          style={{
            padding: '0.75rem 1.25rem',
            background: 'none',
            border: 'none',
            borderBottom: tab === 'policies' ? '3px solid #2563eb' : '3px solid transparent',
            color: tab === 'policies' ? '#2563eb' : '#64748b',
            fontWeight: '600',
            fontSize: '0.95rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span>🛡️ Active Masking Policies</span>
          <span style={{ background: '#dcfce7', color: '#166534', padding: '0.15rem 0.5rem', borderRadius: '9999px', fontSize: '0.78rem' }}>
            {policies.length}
          </span>
        </button>
      </div>

      {/* TAB 1: AI REVIEW QUEUE */}
      {tab === 'review' && (
        <div>
          {/* Filter Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'white', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label htmlFor="status-filter" style={{ fontWeight: '600', fontSize: '0.88rem', color: '#334155' }}>Status Filter:</label>
                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.88rem', background: '#f8fafc' }}
                >
                  <option value="PENDING">Pending Review (Awaiting Decision)</option>
                  <option value="APPROVED">Approved (Policies Created)</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ALL">All Statuses</option>
                </select>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label htmlFor="table-filter" style={{ fontWeight: '600', fontSize: '0.88rem', color: '#334155' }}>Table Filter:</label>
                <input
                  id="table-filter"
                  type="text"
                  placeholder="e.g. patients"
                  value={tableFilter}
                  onChange={(e) => setTableFilter(e.target.value)}
                  style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
              Showing <strong>{recommendations.length}</strong> recommendation(s)
            </div>
          </div>

          {/* Recommendations Table */}
          {loadingRecs ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading AI recommendations...</div>
          ) : recommendations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🔍</div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#0f172a', margin: '0 0 0.5rem 0' }}>
                No recommendations found
              </h3>
              <p style={{ color: '#64748b', maxWidth: '450px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
                {statusFilter === 'PENDING'
                  ? 'All AI recommendations have been reviewed, or no analysis has been executed yet.'
                  : 'No recommendations match the selected filters.'}
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleAnalyzeAndQueue}
                disabled={analyzing}
                style={{
                  background: '#2563eb',
                  color: 'white',
                  border: 'none',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: analyzing ? 'not-allowed' : 'pointer',
                }}
              >
                ⚡ Scan Database Schema with AI
              </button>
            </div>
          ) : (
            <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                <thead style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <tr>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Table</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Column</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Data Type</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Sensitivity</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Recommended Strategy</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Rationale</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Source</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569', textAlign: 'right' }}>Admin Decision</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.map((rec) => {
                    const isPending = rec.status?.toUpperCase() === 'PENDING'
                    const isApproved = rec.status?.toUpperCase() === 'APPROVED'
                    const isRejected = rec.status?.toUpperCase() === 'REJECTED'

                    return (
                      <tr key={rec.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <code style={{ fontWeight: '600', color: '#0f172a' }}>{rec.table_name}</code>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <code style={{ fontWeight: '600', color: '#2563eb' }}>{rec.column_name}</code>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span className="data-type-badge">{rec.data_type || 'text'}</span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '0.2rem 0.55rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: '700',
                              background: rec.sensitivity?.toUpperCase() === 'HIGH' ? '#fee2e2' : rec.sensitivity?.toUpperCase() === 'MEDIUM' ? '#fef3c7' : '#ecfdf5',
                              color: rec.sensitivity?.toUpperCase() === 'HIGH' ? '#991b1b' : rec.sensitivity?.toUpperCase() === 'MEDIUM' ? '#92400e' : '#065f46',
                              border: rec.sensitivity?.toUpperCase() === 'HIGH' ? '1px solid #fca5a5' : rec.sensitivity?.toUpperCase() === 'MEDIUM' ? '1px solid #fde68a' : '1px solid #a7f3d0',
                            }}
                          >
                            {rec.sensitivity}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span style={{ fontWeight: '600', background: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0', color: '#334155' }}>
                            {rec.recommended_strategy}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem', maxWidth: '300px', color: '#475569', fontSize: '0.83rem' }}>
                          {rec.rationale || '—'}
                        </td>
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <span style={{ fontSize: '0.78rem', color: '#64748b', background: '#f8fafc', border: '1px solid #e2e8f0', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                            {rec.source || 'llm'}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                          {isPending ? (
                            <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                              <button
                                type="button"
                                onClick={() => handleApprove(rec.id, rec.table_name, rec.column_name)}
                                style={{
                                  background: '#16a34a',
                                  color: 'white',
                                  border: 'none',
                                  padding: '0.35rem 0.75rem',
                                  borderRadius: '5px',
                                  fontWeight: '600',
                                  fontSize: '0.82rem',
                                  cursor: 'pointer',
                                }}
                              >
                                ✓ Approve
                              </button>
                              <button
                                type="button"
                                onClick={() => handleReject(rec.id, rec.table_name, rec.column_name)}
                                style={{
                                  background: '#ef4444',
                                  color: 'white',
                                  border: 'none',
                                  padding: '0.35rem 0.75rem',
                                  borderRadius: '5px',
                                  fontWeight: '600',
                                  fontSize: '0.82rem',
                                  cursor: 'pointer',
                                }}
                              >
                                ✗ Reject
                              </button>
                            </div>
                          ) : isApproved ? (
                            <span style={{ color: '#16a34a', fontWeight: '600', fontSize: '0.82rem' }}>
                              ✓ Approved (Active)
                            </span>
                          ) : isRejected ? (
                            <span style={{ color: '#ef4444', fontWeight: '600', fontSize: '0.82rem' }}>
                              ✗ Rejected
                            </span>
                          ) : (
                            <span>{rec.status}</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE MASKING POLICIES */}
      {tab === 'policies' && (
        <div>
          <div style={{ background: 'white', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.1rem', fontWeight: '600', color: '#0f172a' }}>
                Active Masking Rules
              </h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                These approved policies are enforced by MaskGate to dynamically mask PostgreSQL columns before data is returned.
              </p>
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: '600', color: '#166534', background: '#dcfce7', padding: '0.3rem 0.8rem', borderRadius: '9999px' }}>
              {policies.length} Active Policies
            </div>
          </div>

          {loadingPolicies ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading active policies...</div>
          ) : policies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🛡️</div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#0f172a', margin: '0 0 0.5rem 0' }}>
                No active masking policies
              </h3>
              <p style={{ color: '#64748b', maxWidth: '450px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
                Switch to the AI Review Queue to approve recommended masking policies.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setTab('review')}
                style={{
                  background: '#2563eb',
                  color: 'white',
                  border: 'none',
                  padding: '0.6rem 1.2rem',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Go to AI Review Queue
              </button>
            </div>
          ) : (
            <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                <thead style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                  <tr>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Policy Name</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Schema</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Table</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Column</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Strategy</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Sensitivity</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Status</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Source</th>
                    <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((policy) => (
                    <tr key={policy.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#0f172a' }}>
                        {policy.name || `${policy.table_name}.${policy.column_name}`}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#64748b' }}>
                        <code>{policy.schema_name || 'public'}</code>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <code>{policy.table_name}</code>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <code style={{ color: '#2563eb', fontWeight: '600' }}>{policy.column_name}</code>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ fontWeight: '600', background: '#f1f5f9', padding: '0.2rem 0.5rem', borderRadius: '4px', border: '1px solid #e2e8f0', color: '#334155' }}>
                          {policy.strategy}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '0.2rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '700',
                            background: policy.sensitivity?.toUpperCase() === 'HIGH' ? '#fee2e2' : '#fef3c7',
                            color: policy.sensitivity?.toUpperCase() === 'HIGH' ? '#991b1b' : '#92400e',
                          }}
                        >
                          {policy.sensitivity || 'MEDIUM'}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ background: '#dcfce7', color: '#166534', padding: '0.2rem 0.55rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: '700', border: '1px solid #bbf7d0' }}>
                          {policy.status || 'ACTIVE'}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#64748b', fontSize: '0.8rem' }}>
                        {policy.source || 'ai_recommendation'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                        <button
                          type="button"
                          onClick={() => handleDeletePolicy(policy.id, policy.name)}
                          style={{
                            background: 'white',
                            border: '1px solid #fca5a5',
                            color: '#dc2626',
                            padding: '0.3rem 0.65rem',
                            borderRadius: '4px',
                            fontSize: '0.8rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                          }}
                        >
                          Deactivate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default MaskingPolicies
