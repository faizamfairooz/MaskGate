import React, { useState, useEffect } from 'react'
import { maskingAPI } from '../services/api'

function MaskingPolicies() {
  const [policies, setPolicies] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [tab, setTab] = useState('policies')

  useEffect(() => {
    fetchPolicies()
    fetchRecommendations()
  }, [])

  const fetchPolicies = async () => {
    setLoading(true)
    try {
      const response = await maskingAPI.getPolicies()
      setPolicies(response.data)
    } catch (error) {
      console.error('Failed to fetch policies:', error)
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
      name: formData.get('name'),
      description: formData.get('description'),
      table_name: formData.get('table_name'),
      column_name: formData.get('column_name'),
      strategy: formData.get('strategy')
    }

    try {
      await maskingAPI.createPolicy(policyData)
      setShowForm(false)
      fetchPolicies()
    } catch (error) {
      console.error('Failed to create policy:', error)
    }
  }

  const handleDeletePolicy = async (policyId) => {
    try {
      await maskingAPI.deletePolicy(policyId)
      fetchPolicies()
    } catch (error) {
      console.error('Failed to delete policy:', error)
    }
  }

  const handleApprove = async (id) => {
    try {
      await maskingAPI.approveRecommendation(id)
      fetchPolicies()
      fetchRecommendations()
    } catch (error) {
      console.error('Failed to approve:', error)
    }
  }

  const handleReject = async (id) => {
    try {
      await maskingAPI.rejectRecommendation(id)
      fetchRecommendations()
    } catch (error) {
      console.error('Failed to reject:', error)
    }
  }

  return (
    <div className="masking-policies">
      <h2>Masking Policies</h2>
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
          <button type="button" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : 'Create New Policy'}
          </button>

          {showForm && (
            <form onSubmit={handleCreatePolicy} className="policy-form">
              <input name="name" placeholder="Policy Name" required />
              <input name="description" placeholder="Description" required />
              <input name="table_name" placeholder="Table Name" required />
              <input name="column_name" placeholder="Column Name" required />
              <select name="strategy" required>
                <option value="">Select Strategy</option>
                <option value="redaction">Redaction</option>
                <option value="partial_mask">Partial Mask</option>
                <option value="hash">Hash</option>
                <option value="email_mask">Email Mask</option>
                <option value="phone_mask">Phone Mask</option>
                <option value="ssn_mask">SSN Mask</option>
                <option value="credit_card_mask">Credit Card Mask</option>
              </select>
              <button type="submit">Create Policy</button>
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
                {policies.map(policy => (
                  <tr key={policy.id}>
                    <td>{policy.name}</td>
                    <td>{policy.table_name}</td>
                    <td>{policy.column_name}</td>
                    <td>{policy.strategy}</td>
                    <td>
                      <button type="button" onClick={() => handleDeletePolicy(policy.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
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
            {recommendations.map(rec => (
              <tr key={rec.id}>
                <td>{rec.table_name}</td>
                <td>{rec.column_name}</td>
                <td>{rec.sensitivity}</td>
                <td>{rec.recommended_strategy}</td>
                <td>
                  <button type="button" onClick={() => handleApprove(rec.id)}>Approve</button>
                  <button type="button" onClick={() => handleReject(rec.id)}>Reject</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default MaskingPolicies
