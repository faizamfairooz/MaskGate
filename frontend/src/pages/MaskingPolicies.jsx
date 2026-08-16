import React, { useState, useEffect } from 'react'
import { maskingAPI } from '../services/api'

function MaskingPolicies() {
  const [policies, setPolicies] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [tab, setTab] = useState('policies')
  const [message, setMessage] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

  useEffect(() => {
    fetchPolicies()
    fetchRecommendations()
  }, [])

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
    }, 4000)
  }

  const fetchPolicies = async () => {
    setLoading(true)
    try {
      const response = await maskingAPI.getPolicies()
      setPolicies(response.data)
    } catch (error) {
      console.error('Failed to fetch policies:', error)
      showNotification('Failed to fetch policies', true)
    } finally {
      setLoading(false)
    }
  }

  const fetchRecommendations = async () => {
    try {
      const response = await maskingAPI.getRecommendations({ status: 'pending' })
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to fetch recommendations:', error)
    }
  }

  const handleCreatePolicy = async (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const policyData = {
      name: formData.get('name')?.trim(),
      description: formData.get('description')?.trim(),
      table_name: formData.get('table_name')?.trim(),
      column_name: formData.get('column_name')?.trim(),
      strategy: formData.get('strategy')
    }

    try {
      await maskingAPI.createPolicy(policyData)
      setShowForm(false)
      showNotification(`Policy "${policyData.name}" created successfully!`)
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to create policy:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to create policy'
      showNotification(detail, true)
    }
  }

  const handleDeletePolicy = async (policyId, policyName) => {
    try {
      await maskingAPI.deletePolicy(policyId)
      showNotification(`Policy "${policyName || policyId}" deleted successfully`)
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to delete policy:', error)
      showNotification('Failed to delete policy', true)
    }
  }

  const handleApprove = async (id) => {
    try {
      await maskingAPI.approveRecommendation(id)
      showNotification('Recommendation approved successfully')
      fetchPolicies()
      fetchRecommendations()
    } catch (error) {
      console.error('Failed to approve:', error)
      showNotification('Failed to approve recommendation', true)
    }
  }

  const handleReject = async (id) => {
    try {
      await maskingAPI.rejectRecommendation(id)
      showNotification('Recommendation rejected')
      fetchRecommendations()
    } catch (error) {
      console.error('Failed to reject:', error)
      showNotification('Failed to reject recommendation', true)
    }
  }

  return (
    <div className="masking-policies">
      <h2>Masking Policies</h2>

      {message && <div className="alert alert-success" style={{ padding: '0.75rem', marginBottom: '1rem', background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e', borderRadius: '6px', color: '#4ade80' }}>{message}</div>}
      {errorMessage && <div className="alert alert-error" style={{ padding: '0.75rem', marginBottom: '1rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '6px', color: '#f87171' }}>{errorMessage}</div>}

      <div className="tabs">
        <button type="button" onClick={() => setTab('policies')} className={tab === 'policies' ? 'active' : ''}>
          Approved policies
        </button>
        <button type="button" onClick={() => setTab('review')} className={tab === 'review' ? 'active' : ''}>
          Review queue ({recommendations.length})
        </button>
      </div>

      {tab === 'policies' && (
        <>
          <div style={{ marginBottom: '1rem' }}>
            <button type="button" className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
              {showForm ? 'Cancel' : '+ Create New Policy'}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleCreatePolicy} className="policy-form" style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', maxWidth: '500px' }}>
              <input name="name" placeholder="Policy Name (e.g. Doctor Name Masking)" required />
              <input name="description" placeholder="Description (e.g. Mask doctor names in appointments)" required />
              <input name="table_name" placeholder="Table Name (e.g. appointments)" required />
              <input name="column_name" placeholder="Column Name (e.g. doctor_name)" required />
              <select name="strategy" required defaultValue="partial_mask">
                <option value="partial_mask">Partial Mask (e.g. J***n)</option>
                <option value="redact">Redaction (e.g. ********)</option>
                <option value="email_mask">Email Mask (e.g. j***@domain.com)</option>
                <option value="phone_mask">Phone Mask (e.g. *******1234)</option>
                <option value="hash">Hash (e.g. SHA-256)</option>
                <option value="date_mask">Date Mask (e.g. YYYY-01-01)</option>
                <option value="ssn_mask">SSN Mask</option>
                <option value="credit_card_mask">Credit Card Mask</option>
                <option value="tokenization">Tokenization</option>
                <option value="noise_addition">Noise Addition (Numeric)</option>
                <option value="generalization">Generalization (Range)</option>
              </select>
              <button type="submit" className="btn btn-success">Save Policy</button>
            </form>
          )}

          {loading ? (
            <p>Loading...</p>
          ) : (
            <table className="policies-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Table</th>
                  <th>Column</th>
                  <th>Strategy</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {policies.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', opacity: 0.7 }}>No active masking policies found</td>
                  </tr>
                ) : (
                  policies.map(policy => (
                    <tr key={policy.id}>
                      <td><strong>{policy.name}</strong></td>
                      <td><code>{policy.table_name}</code></td>
                      <td><code>{policy.column_name}</code></td>
                      <td><span className="badge badge-strategy">{policy.strategy}</span></td>
                      <td>
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => handleDeletePolicy(policy.id, policy.name)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </>
      )}

      {tab === 'review' && (
        <table className="policies-table">
          <thead>
            <tr>
              <th>Table</th>
              <th>Column</th>
              <th>Sensitivity</th>
              <th>Strategy</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {recommendations.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', opacity: 0.7 }}>No pending recommendations</td>
              </tr>
            ) : (
              recommendations.map(rec => (
                <tr key={rec.id}>
                  <td><code>{rec.table_name}</code></td>
                  <td><code>{rec.column_name}</code></td>
                  <td><span className={`badge badge-${rec.sensitivity.toLowerCase()}`}>{rec.sensitivity}</span></td>
                  <td>{rec.recommended_strategy}</td>
                  <td>
                    <button type="button" className="btn btn-success btn-sm" onClick={() => handleApprove(rec.id)}>Approve</button>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleReject(rec.id)} style={{ marginLeft: '0.5rem' }}>Reject</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default MaskingPolicies
