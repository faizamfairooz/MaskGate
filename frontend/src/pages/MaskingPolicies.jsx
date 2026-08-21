import React, { useState, useEffect, useCallback } from 'react'
import { maskingAPI, schemaAPI } from '../services/api'

function MaskingPolicies() {
  const [policies, setPolicies] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loadingPolicies, setLoadingPolicies] = useState(false)
  const [loadingRecs, setLoadingRecs] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [actionLoading, setActionLoading] = useState({}) // { [recId]: 'approving' | 'rejecting' }
  const [tab, setTab] = useState('review') // 'review' or 'policies'
  const [viewMode, setViewMode] = useState('cards') // 'cards' or 'table'
  const [statusFilter, setStatusFilter] = useState('PENDING')
  const [tableFilter, setTableFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [message, setMessage] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)
  const [fetchError, setFetchError] = useState(null)

  // Policy Creation Form State
  const [availableSchemas, setAvailableSchemas] = useState(['public'])
  const [selectedSchema, setSelectedSchema] = useState('public')
  const [availableTables, setAvailableTables] = useState([])
  const [availableColumns, setAvailableColumns] = useState([])
  const [availableStrategies, setAvailableStrategies] = useState({})
  const [loadingSchemas, setLoadingSchemas] = useState(false)
  const [loadingTables, setLoadingTables] = useState(false)
  const [loadingColumns, setLoadingColumns] = useState(false)
  const [creatingPolicy, setCreatingPolicy] = useState(false)
  const [selectedTable, setSelectedTable] = useState('')
  const [selectedColumn, setSelectedColumn] = useState('')
  const [selectedStrategy, setSelectedStrategy] = useState('EMAIL')
  const [selectedSensitivity, setSelectedSensitivity] = useState('MEDIUM')
  const [policyDescription, setPolicyDescription] = useState('')

  // Policy Edit Modal State
  const [editingPolicy, setEditingPolicy] = useState(null)
  const [editStrategy, setEditStrategy] = useState('EMAIL')
  const [editSensitivity, setEditSensitivity] = useState('MEDIUM')
  const [editDescription, setEditDescription] = useState('')
  const [editVisibleChars, setEditVisibleChars] = useState(2)
  const [editBinSize, setEditBinSize] = useState(1000)
  const [editTokenLength, setEditTokenLength] = useState(16)
  const [editNoiseLevel, setEditNoiseLevel] = useState(0.1)
  const [editHashAlgorithm, setEditHashAlgorithm] = useState('sha256')
  const [editError, setEditError] = useState(null)
  const [savingEdit, setSavingEdit] = useState(false)

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

  const fetchSchemas = useCallback(async () => {
    setLoadingSchemas(true)
    try {
      const response = await schemaAPI.getSchemas()
      const list = response.data || ['public']
      setAvailableSchemas(list.length > 0 ? list : ['public'])
    } catch (error) {
      console.error('Failed to fetch schemas:', error)
    } finally {
      setLoadingSchemas(false)
    }
  }, [])

  const fetchStrategies = useCallback(async () => {
    try {
      const response = await maskingAPI.getStrategies()
      setAvailableStrategies(response.data || {})
    } catch (error) {
      console.error('Failed to fetch strategies:', error)
    }
  }, [])

  const fetchTables = useCallback(async (schema = 'public') => {
    setLoadingTables(true)
    try {
      const response = await schemaAPI.getTables(schema)
      setAvailableTables(response.data || [])
    } catch (error) {
      console.error('Failed to fetch tables:', error)
    } finally {
      setLoadingTables(false)
    }
  }, [])

  const handleSchemaChange = async (newSchema) => {
    setSelectedSchema(newSchema)
    setSelectedTable('')
    setSelectedColumn('')
    setAvailableColumns([])
    await fetchTables(newSchema)
  }

  const handleTableChange = async (newTable) => {
    setSelectedTable(newTable)
    setSelectedColumn('')
    setAvailableColumns([])

    if (!newTable) {
      return
    }

    setLoadingColumns(true)
    try {
      const response = await schemaAPI.getTableSchema(newTable, selectedSchema || 'public')
      const cols = response.data?.columns || []
      setAvailableColumns(cols)
    } catch (error) {
      console.error('Failed to load table columns:', error)
      showNotification(`Failed to load columns for table "${newTable}"`, true)
    } finally {
      setLoadingColumns(false)
    }
  }

  const handleCreatePolicy = async (e) => {
    if (e) e.preventDefault()
    if (!selectedTable) {
      showNotification('Please select a table', true)
      return
    }
    if (!selectedColumn) {
      showNotification('Please select a column', true)
      return
    }
    if (!selectedStrategy) {
      showNotification('Please select a masking strategy', true)
      return
    }

    setCreatingPolicy(true)
    try {
      const payload = {
        name: `${selectedTable}.${selectedColumn}`,
        description: policyDescription.trim() || `Manual policy for ${selectedTable}.${selectedColumn}`,
        table_name: selectedTable,
        column_name: selectedColumn,
        schema_name: selectedSchema || 'public',
        strategy: selectedStrategy,
        sensitivity: selectedSensitivity || 'MEDIUM',
        status: 'ACTIVE',
        source: 'admin_manual',
        is_active: true
      }
      await maskingAPI.createPolicy(payload)
      showNotification(`Policy created successfully. Database-level masking is now active for "${selectedTable}.${selectedColumn}".`)
      setSelectedColumn('')
      setPolicyDescription('')
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to create policy:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to create masking policy'
      showNotification(detail, true)
    } finally {
      setCreatingPolicy(false)
    }
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
    setFetchError(null)
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
      const detail = error.response?.data?.detail || error.message || 'Failed to load AI recommendations'
      setFetchError(detail)
    } finally {
      setLoadingRecs(false)
    }
  }, [statusFilter, tableFilter])

  useEffect(() => {
    fetchPolicies()
    fetchSchemas()
    fetchStrategies()
    fetchTables(selectedSchema)
  }, [fetchPolicies, fetchSchemas, fetchStrategies, fetchTables, selectedSchema])

  useEffect(() => {
    fetchRecommendations()
  }, [fetchRecommendations])

  const handleAnalyzeAndQueue = async () => {
    setAnalyzing(true)
    try {
      const res = await maskingAPI.analyzeAndQueue({ schema: 'public' })
      const count = res.data?.length || 0
      showNotification(`AI Schema Analysis complete. Queued ${count} recommendation(s) for administrator review.`)
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
    setActionLoading((prev) => ({ ...prev, [id]: 'approving' }))
    try {
      const res = await maskingAPI.approveRecommendation(id)
      showNotification(`Recommendation approved. Database-level masking is now active for "${table || res.data.table_name}.${column || res.data.column_name}".`)
      await fetchRecommendations()
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to approve recommendation:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to approve recommendation'
      showNotification(detail, true)
    } finally {
      setActionLoading((prev) => {
        const copy = { ...prev }
        delete copy[id]
        return copy
      })
    }
  }

  const handleReject = async (id, table, column) => {
    setActionLoading((prev) => ({ ...prev, [id]: 'rejecting' }))
    try {
      await maskingAPI.rejectRecommendation(id)
      showNotification(`Recommendation rejected for "${table}.${column}". No policy created.`)
      await fetchRecommendations()
    } catch (error) {
      console.error('Failed to reject recommendation:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to reject recommendation'
      showNotification(detail, true)
    } finally {
      setActionLoading((prev) => {
        const copy = { ...prev }
        delete copy[id]
        return copy
      })
    }
  }

  const handleDeletePolicy = async (policyId, policyName) => {
    try {
      await maskingAPI.deletePolicy(policyId)
      showNotification(`Policy "${policyName || policyId}" deactivated successfully. Database-level protection removed.`)
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to delete policy:', error)
      const detail = error.response?.data?.detail || error.message || 'Failed to delete policy'
      showNotification(detail, true)
    }
  }

  const handleOpenEdit = (policy) => {
    setEditingPolicy(policy)
    setEditStrategy(policy.strategy || 'EMAIL')
    setEditSensitivity(policy.sensitivity || 'MEDIUM')
    setEditDescription(policy.description || '')

    let rawParams = policy.parameters
    if (typeof rawParams === 'string') {
      try {
        rawParams = JSON.parse(rawParams)
      } catch (e) {
        rawParams = {}
      }
    }
    const params = typeof rawParams === 'object' && rawParams !== null ? rawParams : {}
    setEditVisibleChars(params.visible_chars !== undefined ? params.visible_chars : 2)
    setEditBinSize(params.bin_size !== undefined ? params.bin_size : 1000)
    setEditTokenLength(params.token_length !== undefined ? params.token_length : 16)
    setEditNoiseLevel(params.noise_level !== undefined ? params.noise_level : 0.1)
    setEditHashAlgorithm(params.algorithm || 'sha256')
    setEditError(null)
    setSavingEdit(false)
  }

  const handleCloseEdit = () => {
    setEditingPolicy(null)
    setEditError(null)
    setSavingEdit(false)
  }

  const validateEditForm = () => {
    const strat = (editStrategy || '').toUpperCase()
    if (!strat) {
      return 'Please select a masking strategy.'
    }

    if (strat === 'PARTIAL' || strat === 'PARTIAL_MASK') {
      const vis = parseInt(editVisibleChars, 10)
      if (isNaN(vis) || vis < 1) {
        return 'Visible characters (visible_chars) must be a positive integer of at least 1.'
      }
      if (vis > 20) {
        return 'Visible characters (visible_chars) cannot exceed 20.'
      }
    }

    if (strat === 'GENERALIZATION') {
      const bin = parseFloat(editBinSize)
      if (isNaN(bin) || bin <= 0) {
        return 'Bin size (bin_size) must be a positive number greater than 0.'
      }
    }

    if (strat === 'TOKENIZATION') {
      const tok = parseInt(editTokenLength, 10)
      if (isNaN(tok) || tok < 8) {
        return 'Token length (token_length) must be at least 8.'
      }
      if (tok > 64) {
        return 'Token length (token_length) cannot exceed 64.'
      }
    }

    if (strat === 'NOISE_ADDITION') {
      const noise = parseFloat(editNoiseLevel)
      if (isNaN(noise) || noise < 0 || noise > 1) {
        return 'Noise level (noise_level) must be between 0.0 and 1.0 (e.g. 0.1 for ±10%).'
      }
    }

    return null
  }

  const buildParametersPayload = (strat) => {
    const s = (strat || '').toUpperCase()
    if (s === 'PARTIAL' || s === 'PARTIAL_MASK') {
      return { visible_chars: parseInt(editVisibleChars, 10) || 2 }
    }
    if (s === 'GENERALIZATION') {
      return { bin_size: parseFloat(editBinSize) || 1000 }
    }
    if (s === 'TOKENIZATION') {
      return { token_length: parseInt(editTokenLength, 10) || 16 }
    }
    if (s === 'NOISE_ADDITION') {
      return { noise_level: parseFloat(editNoiseLevel) || 0.1 }
    }
    if (s === 'HASH') {
      return { algorithm: editHashAlgorithm || 'sha256' }
    }
    return {}
  }

  const extractApiErrorMessage = (error, fallback = 'Failed to update policy') => {
    if (!error) return fallback
    if (error.response?.status === 404) {
      return `Policy #${editingPolicy?.id || ''} was not found in PostgreSQL. It may have been deleted by another administrator.`
    }
    if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      return 'Network connection failed. Unable to reach MaskGate backend service.'
    }
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (typeof detail === 'string') {
        if (detail.includes('Traceback (most recent call last):')) {
          const lines = detail.trim().split('\n')
          return lines[lines.length - 1] || fallback
        }
        return detail
      }
      if (Array.isArray(detail)) {
        return detail.map((d) => d.msg || d.message || JSON.stringify(d)).join('; ')
      }
      if (typeof detail === 'object') {
        return detail.message || JSON.stringify(detail)
      }
    }
    if (error.message) {
      return error.message
    }
    return fallback
  }

  const handleSaveEdit = async (e) => {
    if (e) e.preventDefault()
    if (!editingPolicy) return

    // Pre-flight client-side validation
    const validationError = validateEditForm()
    if (validationError) {
      setEditError(validationError)
      return
    }

    setEditError(null)
    setSavingEdit(true)

    try {
      const params = buildParametersPayload(editStrategy)
      const updatePayload = {
        strategy: editStrategy,
        sensitivity: editSensitivity,
        description: editDescription.trim(),
        parameters: params,
      }

      const res = await maskingAPI.updatePolicy(editingPolicy.id, updatePayload)
      const updatedPolicy = res.data

      // Immediately update local state so table updates synchronously
      setPolicies((prev) =>
        prev.map((p) => (p.id === editingPolicy.id ? { ...p, ...updatedPolicy } : p))
      )

      // Local and backend update confirmed
      const pName = updatedPolicy.name || `${updatedPolicy.table_name}.${updatedPolicy.column_name}`
      showNotification(`Policy "${pName}" updated successfully. Database-level protection has been updated.`)

      handleCloseEdit()
      await fetchPolicies()
    } catch (error) {
      console.error('Failed to update policy:', error)
      const errorMsg = extractApiErrorMessage(error, 'Failed to update masking policy')
      setEditError(errorMsg)
      showNotification(errorMsg, true)

      if (error.response?.status === 404) {
        await fetchPolicies()
      }
    } finally {
      setSavingEdit(false)
    }
  }

  // Filter recommendations based on search query
  const filteredRecommendations = recommendations.filter((rec) => {
    if (!searchQuery.trim()) return true
    const query = searchQuery.toLowerCase()
    const tableMatch = (rec.table_name || '').toLowerCase().includes(query)
    const colMatch = (rec.column_name || '').toLowerCase().includes(query)
    const typeMatch = (rec.data_type || '').toLowerCase().includes(query)
    const stratMatch = (rec.recommended_strategy || '').toLowerCase().includes(query)
    const reasonMatch = (rec.rationale || '').toLowerCase().includes(query)
    return tableMatch || colMatch || typeMatch || stratMatch || reasonMatch
  })

  const pendingCount = recommendations.filter((r) => r.status?.toUpperCase() === 'PENDING').length
  const approvedCount = recommendations.filter((r) => r.status?.toUpperCase() === 'APPROVED').length
  const rejectedCount = recommendations.filter((r) => r.status?.toUpperCase() === 'REJECTED').length

  const getStrategyBadgeClass = (strategy) => {
    const s = (strategy || '').toUpperCase()
    if (s.includes('EMAIL')) return 'badge-strategy badge-strategy-email'
    if (s.includes('PHONE')) return 'badge-strategy badge-strategy-phone'
    if (s.includes('PARTIAL')) return 'badge-strategy badge-strategy-partial'
    if (s.includes('REDACT')) return 'badge-strategy badge-strategy-redact'
    return 'badge-strategy badge-strategy-none'
  }

  const getSensitivityBadgeClass = (level) => {
    const l = (level || '').toUpperCase()
    if (l === 'HIGH') return 'badge-high'
    if (l === 'MEDIUM') return 'badge-medium'
    return 'badge-low'
  }

  const getConfidenceBadgeClass = (conf) => {
    const c = (conf || 'HIGH').toUpperCase()
    if (c === 'HIGH') return 'badge-conf-high'
    if (c === 'MEDIUM') return 'badge-conf-medium'
    return 'badge-conf-low'
  }

  const formatPolicyParameters = (policy) => {
    let params = policy.parameters
    if (typeof params === 'string') {
      try {
        params = JSON.parse(params)
      } catch (e) {
        params = null
      }
    }
    if (!params || typeof params !== 'object' || Object.keys(params).length === 0) {
      return null
    }
    return Object.entries(params)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ')
  }

  return (
    <div className="masking-policies-page" style={{ padding: '1.5rem', maxWidth: '1440px', margin: '0 auto' }}>
      {/* Header with Conceptual Flow Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: '700', color: '#0f172a', margin: '0 0 0.25rem 0' }}>
            Data Masking Policy Management
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', margin: 0 }}>
            GenAI analyzes database schema metadata to recommend sensitive columns and masking strategies. Admin explicitly reviews and approves or rejects each recommendation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
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
              padding: '0.6rem 1.25rem',
              borderRadius: '6px',
              fontWeight: '600',
              cursor: analyzing ? 'not-allowed' : 'pointer',
              boxShadow: '0 2px 4px rgba(37,99,235,0.2)',
            }}
          >
            {analyzing && <span className="spinner" style={{ width: '14px', height: '14px', borderTopColor: 'white' }} />}
            <span>{analyzing ? 'Analyzing Schema with AI...' : 'Run AI Schema Analysis'}</span>
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => { fetchPolicies(); fetchRecommendations(); }}
            title="Refresh policies and recommendations"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <span>↻</span> Refresh
          </button>
        </div>
      </div>

      {/* Conceptual Flow Infographic Bar */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '0.75rem 1.25rem',
        marginBottom: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem',
        fontSize: '0.85rem',
        color: '#475569'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: '700', color: '#1e293b' }}>Architecture Flow:</span>
          <span>Database Schema</span>
          <span style={{ color: '#94a3b8' }}>→</span>
          <span style={{ color: '#2563eb', fontWeight: '600' }}>AI Analysis</span>
          <span style={{ color: '#94a3b8' }}>→</span>
          <span style={{ color: '#7c3aed', fontWeight: '600' }}>AI Recommendations</span>
          <span style={{ color: '#94a3b8' }}>→</span>
          <span style={{ color: '#0d9488', fontWeight: '600' }}>Admin Review</span>
          <span style={{ color: '#94a3b8' }}>→</span>
          <span style={{ color: '#16a34a', fontWeight: '700' }}>DB-Level Masking Active</span>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
          LLM recommends strategies; Administrator approves and enforces database-level policies.
        </div>
      </div>

      {/* Overview Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b', fontWeight: '700', letterSpacing: '0.5px' }}>
            Pending AI Reviews
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: pendingCount > 0 ? '#d97706' : '#0f172a', marginTop: '0.25rem' }}>
            {pendingCount}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Awaiting administrator decision
          </div>
        </div>

        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b', fontWeight: '700', letterSpacing: '0.5px' }}>
            Approved Recommendations
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#16a34a', marginTop: '0.25rem' }}>
            {approvedCount}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            DB-level masking automatically applied
          </div>
        </div>

        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b', fontWeight: '700', letterSpacing: '0.5px' }}>
            Total Active Policies
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#2563eb', marginTop: '0.25rem' }}>
            {policies.length}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Enforced database-level protection
          </div>
        </div>

        <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b', fontWeight: '700', letterSpacing: '0.5px' }}>
            Rejected Recommendations
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: '700', color: '#991b1b', marginTop: '0.25rem' }}>
            {rejectedCount}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.2rem' }}>
            Excluded from masking policies
          </div>
        </div>
      </div>

      {/* Notifications */}
      {message && (
        <div style={{ padding: '0.85rem 1.25rem', marginBottom: '1.25rem', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: '8px', color: '#065f46', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>✓</span> {message}
        </div>
      )}
      {errorMessage && (
        <div style={{ padding: '0.85rem 1.25rem', marginBottom: '1.25rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>Notice:</span> {errorMessage}
        </div>
      )}

      {/* Main Tabs */}
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
          <span>AI Recommendations</span>
          <span style={{ background: pendingCount > 0 ? '#fef3c7' : '#e2e8f0', color: pendingCount > 0 ? '#92400e' : '#475569', padding: '0.15rem 0.55rem', borderRadius: '9999px', fontSize: '0.78rem', fontWeight: '700' }}>
            {recommendations.length}
          </span>
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
          <span>Active Masking Policies</span>
          <span style={{ background: '#dcfce7', color: '#166534', padding: '0.15rem 0.55rem', borderRadius: '9999px', fontSize: '0.78rem', fontWeight: '700' }}>
            {policies.length}
          </span>
        </button>
      </div>

      {/* TAB 1: AI MASKING RECOMMENDATIONS */}
      {tab === 'review' && (
        <div>
          {/* Controls & Filter Bar */}
          <div style={{ background: 'white', padding: '1rem 1.25rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              {/* Status Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label htmlFor="status-filter" style={{ fontWeight: '600', fontSize: '0.88rem', color: '#334155' }}>
                  Status:
                </label>
                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{ padding: '0.45rem 0.8rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.88rem', background: '#f8fafc', color: '#0f172a', fontWeight: '500', cursor: 'pointer' }}
                >
                  <option value="PENDING">Pending Review (Awaiting Decision)</option>
                  <option value="APPROVED">Approved (Active Policies)</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ALL">All Statuses</option>
                </select>
              </div>

              {/* Table Filter */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label htmlFor="table-filter" style={{ fontWeight: '600', fontSize: '0.88rem', color: '#334155' }}>
                  Table:
                </label>
                <input
                  id="table-filter"
                  type="text"
                  placeholder="Filter by table name..."
                  value={tableFilter}
                  onChange={(e) => setTableFilter(e.target.value)}
                  style={{ padding: '0.45rem 0.8rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.88rem', width: '180px' }}
                />
              </div>

              {/* Search Box */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label htmlFor="search-recommendations" style={{ fontWeight: '600', fontSize: '0.88rem', color: '#334155' }}>
                  Search:
                </label>
                <input
                  id="search-recommendations"
                  type="text"
                  placeholder="Search column, strategy, rationale..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ padding: '0.45rem 0.8rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.88rem', width: '220px' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {/* View Toggle */}
              <div style={{ display: 'inline-flex', background: '#f1f5f9', padding: '0.2rem', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <button
                  type="button"
                  onClick={() => setViewMode('cards')}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '4px',
                    border: 'none',
                    background: viewMode === 'cards' ? 'white' : 'transparent',
                    color: viewMode === 'cards' ? '#0f172a' : '#64748b',
                    fontWeight: viewMode === 'cards' ? '600' : '500',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    boxShadow: viewMode === 'cards' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                  }}
                >
                  Cards View
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('table')}
                  style={{
                    padding: '0.35rem 0.75rem',
                    borderRadius: '4px',
                    border: 'none',
                    background: viewMode === 'table' ? 'white' : 'transparent',
                    color: viewMode === 'table' ? '#0f172a' : '#64748b',
                    fontWeight: viewMode === 'table' ? '600' : '500',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    boxShadow: viewMode === 'table' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                  }}
                >
                  Table View
                </button>
              </div>

              <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
                Showing <strong>{filteredRecommendations.length}</strong> of <strong>{recommendations.length}</strong>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loadingRecs && (
            <div style={{ padding: '3.5rem 1.5rem', textAlign: 'center', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <div className="spinner" style={{ width: '28px', height: '28px', borderColor: '#cbd5e1', borderTopColor: '#2563eb', marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '600', color: '#0f172a', margin: '0 0 0.35rem 0' }}>
                Loading AI Recommendations...
              </h3>
              <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 0 }}>
                Retrieving analyzed PostgreSQL schema suggestions and review queue.
              </p>
            </div>
          )}

          {/* Error State */}
          {!loadingRecs && fetchError && (
            <div style={{ padding: '2.5rem 1.5rem', textAlign: 'center', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca', color: '#991b1b' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '700', margin: '0 0 0.5rem 0' }}>
                Failed to Load Recommendations
              </h3>
              <p style={{ maxWidth: '500px', margin: '0 auto 1.25rem auto', fontSize: '0.9rem', color: '#7f1d1d' }}>
                {fetchError}
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={fetchRecommendations}
                style={{ background: '#dc2626', color: 'white', border: 'none', padding: '0.55rem 1.2rem', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}
              >
                ↻ Retry Loading
              </button>
            </div>
          )}

          {/* Empty State */}
          {!loadingRecs && !fetchError && filteredRecommendations.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3.5rem 1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#0f172a', margin: '0 0 0.5rem 0' }}>
                {recommendations.length === 0 ? 'No AI Recommendations Queued' : 'No Matching Recommendations'}
              </h3>
              <p style={{ color: '#64748b', maxWidth: '480px', margin: '0 auto 1.5rem auto', fontSize: '0.92rem' }}>
                {recommendations.length === 0
                  ? 'Run AI Schema Analysis to inspect PostgreSQL tables and generate intelligent masking recommendations.'
                  : 'Try clearing or modifying your table filter, status filter, or search query.'}
              </p>
              {recommendations.length === 0 ? (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleAnalyzeAndQueue}
                  disabled={analyzing}
                  style={{
                    background: '#2563eb',
                    color: 'white',
                    border: 'none',
                    padding: '0.65rem 1.4rem',
                    borderRadius: '6px',
                    fontWeight: '600',
                    cursor: analyzing ? 'not-allowed' : 'pointer',
                  }}
                >
                  Scan Database Schema with AI
                </button>
              ) : (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => { setStatusFilter('ALL'); setTableFilter(''); setSearchQuery(''); }}
                  style={{ padding: '0.55rem 1.2rem' }}
                >
                  Clear All Filters
                </button>
              )}
            </div>
          )}

          {/* View Mode 1: Detailed Cards View */}
          {!loadingRecs && !fetchError && filteredRecommendations.length > 0 && viewMode === 'cards' && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: '1.25rem' }}>
              {filteredRecommendations.map((rec) => {
                const isPending = rec.status?.toUpperCase() === 'PENDING'
                const isApproved = rec.status?.toUpperCase() === 'APPROVED'
                const isRejected = rec.status?.toUpperCase() === 'REJECTED'
                const isActioning = actionLoading[rec.id]

                return (
                  <div
                    key={rec.id}
                    className="recommendation-card"
                    style={{
                      borderLeft: isPending ? '4px solid #f59e0b' : isApproved ? '4px solid #16a34a' : '4px solid #ef4444',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      {/* Top Bar: Target Table.Column & Status */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.85rem' }}>
                        <div>
                          <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b', fontWeight: '700', letterSpacing: '0.5px' }}>
                            Target Column
                          </div>
                          <div style={{ fontSize: '1.15rem', fontWeight: '700', color: '#0f172a', marginTop: '0.15rem' }}>
                            <code>{rec.table_name}.{rec.column_name}</code>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div>
                          {isPending && (
                            <span className="status-badge-pending">
                              Pending Review
                            </span>
                          )}
                          {isApproved && (
                            <span className="status-badge-approved">
                              Approved
                            </span>
                          )}
                          {isRejected && (
                            <span className="status-badge-rejected">
                              Rejected
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Details Grid */}
                      <div style={{ background: '#f8fafc', padding: '0.85rem', borderRadius: '6px', border: '1px solid #f1f5f9', marginBottom: '0.85rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.65rem', fontSize: '0.84rem' }}>
                        <div>
                          <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem', fontWeight: '600' }}>Detected Type:</span>
                          <span className="data-type-badge" style={{ marginTop: '0.15rem', display: 'inline-block' }}>
                            {rec.data_type || 'text'}
                          </span>
                        </div>

                        <div>
                          <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem', fontWeight: '600' }}>Sensitivity:</span>
                          <span className={getSensitivityBadgeClass(rec.sensitivity)} style={{ marginTop: '0.15rem', display: 'inline-block' }}>
                            {rec.sensitivity || 'MEDIUM'}
                          </span>
                        </div>

                        <div>
                          <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem', fontWeight: '600' }}>Confidence:</span>
                          <span className={getConfidenceBadgeClass(rec.confidence)} style={{ marginTop: '0.15rem', display: 'inline-block' }}>
                            {rec.confidence || 'HIGH'}
                          </span>
                        </div>

                        <div>
                          <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem', fontWeight: '600' }}>Source:</span>
                          <span style={{ color: '#475569', fontSize: '0.8rem', marginTop: '0.15rem', display: 'inline-block' }}>
                            {rec.source || 'llm'}
                          </span>
                        </div>
                      </div>

                      {/* Recommendation Strategy Highlight */}
                      <div style={{ marginBottom: '0.85rem' }}>
                        <span style={{ color: '#475569', fontSize: '0.8rem', fontWeight: '700', display: 'block', marginBottom: '0.35rem' }}>
                          Recommended Masking Strategy:
                        </span>
                        <span className={getStrategyBadgeClass(rec.recommended_strategy)}>
                          {rec.recommended_strategy}
                        </span>
                      </div>

                      {/* Rationale */}
                      <div style={{ marginBottom: '1.25rem', fontSize: '0.84rem', color: '#475569' }}>
                        <span style={{ fontWeight: '700', color: '#334155' }}>Reason / Rationale: </span>
                        <span>{rec.rationale || 'Identified potential sensitive identifier via schema analysis.'}</span>
                      </div>
                    </div>

                    {/* Admin Action Buttons */}
                    <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '0.85rem', display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', alignItems: 'center' }}>
                      {isPending ? (
                        <>
                          <button
                            type="button"
                            onClick={() => handleReject(rec.id, rec.table_name, rec.column_name)}
                            disabled={Boolean(isActioning)}
                            style={{
                              background: 'white',
                              border: '1px solid #fca5a5',
                              color: '#dc2626',
                              padding: '0.45rem 0.9rem',
                              borderRadius: '6px',
                              fontWeight: '600',
                              fontSize: '0.85rem',
                              cursor: isActioning ? 'not-allowed' : 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            {isActioning === 'rejecting' ? 'Rejecting...' : 'Reject'}
                          </button>

                          <button
                            type="button"
                            onClick={() => handleApprove(rec.id, rec.table_name, rec.column_name)}
                            disabled={Boolean(isActioning)}
                            style={{
                              background: '#16a34a',
                              border: 'none',
                              color: 'white',
                              padding: '0.45rem 1.1rem',
                              borderRadius: '6px',
                              fontWeight: '600',
                              fontSize: '0.85rem',
                              cursor: isActioning ? 'not-allowed' : 'pointer',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              boxShadow: '0 1px 2px rgba(22,163,74,0.2)',
                              transition: 'all 0.15s ease',
                            }}
                          >
                            {isActioning === 'approving' ? 'Approving...' : 'Approve'}
                          </button>
                        </>
                      ) : isApproved ? (
                        <span style={{ color: '#166534', fontWeight: '600', fontSize: '0.82rem', background: '#dcfce7', border: '1px solid #bbf7d0', padding: '0.25rem 0.65rem', borderRadius: '4px' }}>
                          DB-level masking: Automatically applied
                        </span>
                      ) : (
                        <span style={{ color: '#991b1b', fontWeight: '600', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          Rejected by Admin
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* View Mode 2: Table View */}
          {!loadingRecs && !fetchError && filteredRecommendations.length > 0 && viewMode === 'table' && (
            <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                  <thead style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                    <tr>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Table</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Column</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Detected Type</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Sensitivity</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Confidence</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Recommendation</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Rationale</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Status</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569', textAlign: 'right' }}>Admin Decision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecommendations.map((rec) => {
                      const isPending = rec.status?.toUpperCase() === 'PENDING'
                      const isApproved = rec.status?.toUpperCase() === 'APPROVED'
                      const isRejected = rec.status?.toUpperCase() === 'REJECTED'
                      const isActioning = actionLoading[rec.id]

                      return (
                        <tr key={rec.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <code style={{ fontWeight: '700', color: '#0f172a' }}>{rec.table_name}</code>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <code style={{ fontWeight: '700', color: '#2563eb' }}>{rec.column_name}</code>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className="data-type-badge">{rec.data_type || 'text'}</span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={getSensitivityBadgeClass(rec.sensitivity)}>
                              {rec.sensitivity}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={getConfidenceBadgeClass(rec.confidence)}>
                              {rec.confidence || 'HIGH'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={getStrategyBadgeClass(rec.recommended_strategy)}>
                              {rec.recommended_strategy}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', maxWidth: '280px', color: '#475569', fontSize: '0.83rem' }}>
                            {rec.rationale || '—'}
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            {isPending ? (
                              <span className="status-badge-pending">Pending</span>
                            ) : isApproved ? (
                              <span className="status-badge-approved">Approved</span>
                            ) : (
                              <span className="status-badge-rejected">Rejected</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            {isPending ? (
                              <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                                <button
                                  type="button"
                                  onClick={() => handleApprove(rec.id, rec.table_name, rec.column_name)}
                                  disabled={Boolean(isActioning)}
                                  style={{
                                    background: '#16a34a',
                                    color: 'white',
                                    border: 'none',
                                    padding: '0.35rem 0.75rem',
                                    borderRadius: '5px',
                                    fontWeight: '600',
                                    fontSize: '0.82rem',
                                    cursor: isActioning ? 'not-allowed' : 'pointer',
                                  }}
                                >
                                  {isActioning === 'approving' ? '...' : 'Approve'}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleReject(rec.id, rec.table_name, rec.column_name)}
                                  disabled={Boolean(isActioning)}
                                  style={{
                                    background: '#ef4444',
                                    color: 'white',
                                    border: 'none',
                                    padding: '0.35rem 0.75rem',
                                    borderRadius: '5px',
                                    fontWeight: '600',
                                    fontSize: '0.82rem',
                                    cursor: isActioning ? 'not-allowed' : 'pointer',
                                  }}
                                >
                                  {isActioning === 'rejecting' ? '...' : 'Reject'}
                                </button>
                              </div>
                            ) : isApproved ? (
                              <span style={{ color: '#166534', fontWeight: '600', fontSize: '0.82rem' }}>
                                Approved — DB-level masking active
                              </span>
                            ) : isRejected ? (
                              <span style={{ color: '#ef4444', fontWeight: '600', fontSize: '0.82rem' }}>
                                Rejected
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
            </div>
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE MASKING POLICIES & CREATION FORM */}
      {tab === 'policies' && (
        <div>
          {/* Header Info */}
          <div style={{ background: 'white', padding: '1rem 1.25rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.1rem', fontWeight: '700', color: '#0f172a' }}>
                Active Masking Rules Enforced
              </h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                These approved rules are enforced deterministically by MaskGate to sanitize sensitive PostgreSQL column outputs.
              </p>
            </div>
            <div style={{ fontSize: '0.88rem', fontWeight: '700', color: '#166534', background: '#dcfce7', padding: '0.35rem 0.85rem', borderRadius: '9999px', border: '1px solid #bbf7d0' }}>
              {policies.length} Active Policies
            </div>
          </div>

          {/* Manual Policy Creation Form */}
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '1.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
            <div style={{ marginBottom: '1rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.75rem' }}>
              <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.05rem', fontWeight: '700', color: '#0f172a' }}>
                Manual Policy Creator
              </h3>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                Directly define a custom policy by selecting a PostgreSQL table and column.
              </p>
            </div>

            {/* Database-Level Protection Notice Banner */}
            <div style={{
              background: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '6px',
              padding: '0.65rem 0.95rem',
              marginBottom: '1.25rem',
              fontSize: '0.85rem',
              color: '#166534',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem'
            }}>
              <span style={{ fontWeight: '700' }}>Database-Level Protection:</span>
              <span>When this policy is created, MaskGate automatically applies PostgreSQL database-level masking to the selected column.</span>
            </div>

            <form onSubmit={handleCreatePolicy} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                {/* Schema Dropdown */}
                <div>
                  <label htmlFor="policy-schema-select" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Schema:
                  </label>
                  <select
                    id="policy-schema-select"
                    value={selectedSchema}
                    onChange={(e) => handleSchemaChange(e.target.value)}
                    disabled={loadingSchemas || creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#f8fafc',
                      color: '#0f172a',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    {availableSchemas.map((sch) => (
                      <option key={sch} value={sch}>{sch}</option>
                    ))}
                  </select>
                </div>

                {/* Table Dropdown */}
                <div>
                  <label htmlFor="policy-table-select" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Table:
                  </label>
                  <select
                    id="policy-table-select"
                    value={selectedTable}
                    onChange={(e) => handleTableChange(e.target.value)}
                    disabled={loadingTables || creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#f8fafc',
                      color: '#0f172a',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="">[ Select table ▼ ]</option>
                    {availableTables.map((tbl) => (
                      <option key={tbl} value={tbl}>{tbl}</option>
                    ))}
                  </select>
                </div>

                {/* Column Dropdown */}
                <div>
                  <label htmlFor="policy-column-select" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Column:
                  </label>
                  <select
                    id="policy-column-select"
                    value={selectedColumn}
                    onChange={(e) => setSelectedColumn(e.target.value)}
                    disabled={!selectedTable || loadingColumns || creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: !selectedTable ? '#f1f5f9' : '#f8fafc',
                      color: !selectedTable ? '#94a3b8' : '#0f172a',
                      fontWeight: '500',
                      cursor: !selectedTable ? 'not-allowed' : 'pointer'
                    }}
                  >
                    <option value="">
                      {loadingColumns
                        ? 'Loading columns...'
                        : !selectedTable
                        ? '[ Select table first ]'
                        : '[ Select column ▼ ]'}
                    </option>
                    {availableColumns.map((col) => {
                      const colName = typeof col === 'string' ? col : col.column_name
                      const colType = typeof col === 'object' && col.data_type ? ` (${col.data_type})` : ''
                      return (
                        <option key={colName} value={colName}>
                          {colName}{colType}
                        </option>
                      )
                    })}
                  </select>
                </div>

                {/* Masking Strategy Dropdown */}
                <div>
                  <label htmlFor="policy-strategy-select" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Masking Strategy:
                  </label>
                  <select
                    id="policy-strategy-select"
                    value={selectedStrategy}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                    disabled={creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#f8fafc',
                      color: '#0f172a',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    {Object.keys(availableStrategies).length > 0 ? (
                      Object.entries(availableStrategies).map(([stratKey, desc]) => (
                        <option key={stratKey} value={stratKey}>
                          {stratKey} - {desc}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="EMAIL">EMAIL - Mask email address</option>
                        <option value="PHONE_LAST4">PHONE_LAST4 - Mask phone number</option>
                        <option value="PARTIAL">PARTIAL - Preserve edge characters</option>
                        <option value="REDACT">REDACT - Full redaction</option>
                        <option value="DO_NOT_SHOW">DO_NOT_SHOW - Exclude column from results</option>
                        <option value="NONE">NONE - Original unmasked</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              {/* Policy Description / Rationale & Submit Button */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px', gap: '1rem', alignItems: 'flex-end' }}>
                <div>
                  <label htmlFor="policy-description-input" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Policy Description (Optional):
                  </label>
                  <input
                    id="policy-description-input"
                    type="text"
                    value={policyDescription}
                    onChange={(e) => setPolicyDescription(e.target.value)}
                    placeholder="e.g. Mask patient email for dev queries"
                    disabled={creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#f8fafc',
                      color: '#0f172a',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    id="create-policy-btn"
                    disabled={!selectedTable || !selectedColumn || !selectedStrategy || creatingPolicy}
                    style={{
                      width: '100%',
                      padding: '0.55rem 1rem',
                      background: (!selectedTable || !selectedColumn || !selectedStrategy || creatingPolicy) ? '#94a3b8' : '#2563eb',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontWeight: '600',
                      fontSize: '0.88rem',
                      cursor: (!selectedTable || !selectedColumn || !selectedStrategy || creatingPolicy) ? 'not-allowed' : 'pointer',
                      transition: 'background-color 0.15s ease',
                      height: '38px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.4rem'
                    }}
                  >
                    {creatingPolicy && <span className="spinner" style={{ width: '14px', height: '14px', borderTopColor: 'white' }} />}
                    <span>{creatingPolicy ? 'Creating...' : 'Create Policy'}</span>
                  </button>
                </div>
              </div>

              {/* DO_NOT_SHOW explanation alert */}
              {selectedStrategy.toUpperCase() === 'DO_NOT_SHOW' && (
                <div style={{ padding: '0.65rem 0.85rem', background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '0.85rem', color: '#92400e', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span><strong>DO_NOT_SHOW:</strong> Column will not be returned to the query result. Query rewriter projects permitted columns before PostgreSQL execution where safe, with in-memory exclusion fallback.</span>
                </div>
              )}
            </form>
          </div>

          {/* Active Policies Table */}
          {loadingPolicies ? (
            <div style={{ padding: '3rem 1rem', textAlign: 'center', color: '#64748b' }}>
              <div className="spinner" style={{ width: '24px', height: '24px', borderColor: '#cbd5e1', borderTopColor: '#2563eb', marginBottom: '0.75rem' }} />
              <div>Loading active policies...</div>
            </div>
          ) : policies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3.5rem 1.5rem', background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '600', color: '#0f172a', margin: '0 0 0.5rem 0' }}>
                No Active Masking Policies
              </h3>
              <p style={{ color: '#64748b', maxWidth: '450px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
                Switch to the AI Recommendations tab to approve recommended rules or create a custom policy above.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setTab('review')}
                style={{
                  background: '#2563eb',
                  color: 'white',
                  border: 'none',
                  padding: '0.6rem 1.25rem',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Go to AI Recommendations Queue
              </button>
            </div>
          ) : (
            <div style={{ background: 'white', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.03)' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                  <thead style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                    <tr>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Policy Name</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Schema</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Table</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Column</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Strategy</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Parameters</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Sensitivity</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Database Protection</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Status</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569' }}>Source</th>
                      <th style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#475569', textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {policies.map((policy) => {
                      const paramsFormatted = formatPolicyParameters(policy)
                      return (
                        <tr key={policy.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '0.75rem 1rem', fontWeight: '600', color: '#0f172a' }}>
                            <div>{policy.name || `${policy.table_name}.${policy.column_name}`}</div>
                            {policy.description && policy.description !== policy.name && (
                              <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 'normal', marginTop: '0.15rem' }}>
                                {policy.description}
                              </div>
                            )}
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
                            <span className={getStrategyBadgeClass(policy.strategy)}>
                              {policy.strategy}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            {paramsFormatted ? (
                              <span style={{
                                display: 'inline-block',
                                background: '#f1f5f9',
                                color: '#334155',
                                padding: '0.2rem 0.5rem',
                                borderRadius: '4px',
                                fontSize: '0.78rem',
                                fontFamily: 'monospace',
                                border: '1px solid #e2e8f0'
                              }}>
                                {paramsFormatted}
                              </span>
                            ) : (
                              <span style={{ color: '#94a3b8', fontSize: '0.82rem' }}>—</span>
                            )}
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className={getSensitivityBadgeClass(policy.sensitivity)}>
                              {policy.sensitivity || 'MEDIUM'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              background: '#f0fdf4',
                              color: '#166534',
                              border: '1px solid #bbf7d0',
                              padding: '0.2rem 0.55rem',
                              borderRadius: '4px',
                              fontSize: '0.78rem',
                              fontWeight: '600'
                            }}>
                              Automatically applied
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem' }}>
                            <span className="status-badge-approved">
                              {policy.status || 'ACTIVE'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 1rem', color: '#64748b', fontSize: '0.8rem' }}>
                            {policy.source || 'ai_recommendation'}
                          </td>
                          <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                            <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                              <button
                                type="button"
                                id={`edit-policy-btn-${policy.id}`}
                                onClick={() => handleOpenEdit(policy)}
                                style={{
                                  background: 'white',
                                  border: '1px solid #93c5fd',
                                  color: '#2563eb',
                                  padding: '0.35rem 0.75rem',
                                  borderRadius: '5px',
                                  fontSize: '0.82rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '0.3rem',
                                  transition: 'all 0.15s ease',
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                id={`deactivate-policy-btn-${policy.id}`}
                                onClick={() => handleDeletePolicy(policy.id, policy.name)}
                                style={{
                                  background: 'white',
                                  border: '1px solid #fca5a5',
                                  color: '#dc2626',
                                  padding: '0.35rem 0.75rem',
                                  borderRadius: '5px',
                                  fontSize: '0.82rem',
                                  fontWeight: '600',
                                  cursor: 'pointer',
                                  transition: 'all 0.15s ease',
                                }}
                              >
                                Deactivate
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hardened Edit Policy Modal */}
      {editingPolicy && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          backdropFilter: 'blur(2px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            maxWidth: '560px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '1.75rem',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid #e2e8f0'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.85rem' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '700', color: '#0f172a' }}>
                  Edit Masking Policy
                </h3>
                <div style={{ fontSize: '0.84rem', color: '#64748b', marginTop: '0.25rem' }}>
                  Modify masking strategy and runtime parameters
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseEdit}
                disabled={savingEdit}
                aria-label="Close modal"
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: '6px',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.1rem',
                  cursor: savingEdit ? 'not-allowed' : 'pointer',
                  color: '#64748b'
                }}
              >
                ✕
              </button>
            </div>

            {/* Error Notification inside Modal */}
            {editError && (
              <div style={{
                marginBottom: '1.25rem',
                padding: '0.75rem 1rem',
                background: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '8px',
                color: '#991b1b',
                fontSize: '0.88rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.75rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>{editError}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setEditError(null)}
                  style={{ background: 'none', border: 'none', color: '#991b1b', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold' }}
                >
                  ✕
                </button>
              </div>
            )}

            <form onSubmit={handleSaveEdit}>
              {/* Target Details Card */}
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '0.85rem 1rem',
                marginBottom: '1.25rem',
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '0.75rem'
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Target Column
                  </div>
                  <div style={{ marginTop: '0.25rem', fontSize: '0.9rem', color: '#0f172a' }}>
                    <code>{editingPolicy.schema_name || 'public'}.{editingPolicy.table_name}.<strong style={{ color: '#2563eb' }}>{editingPolicy.column_name}</strong></code>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Database Protection
                  </div>
                  <div style={{ marginTop: '0.25rem', fontSize: '0.85rem', color: '#166534', fontWeight: '600' }}>
                    DB-level masking active
                  </div>
                </div>
              </div>

              {/* Strategy & Sensitivity Selection */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
                <div>
                  <label htmlFor="edit-policy-strategy" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Masking Strategy: <span style={{ color: '#dc2626' }}>*</span>
                  </label>
                  <select
                    id="edit-policy-strategy"
                    value={editStrategy}
                    onChange={(e) => {
                      setEditStrategy(e.target.value)
                      setEditError(null)
                    }}
                    disabled={savingEdit}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    <optgroup label="Core Strategies">
                      <option value="EMAIL">EMAIL — Mask username, preserve domain</option>
                      <option value="PHONE_LAST4">PHONE_LAST4 — Preserve last 4 digits</option>
                      <option value="PARTIAL">PARTIAL — Preserve edge characters</option>
                      <option value="REDACT">REDACT — Full asterisk redaction</option>
                      <option value="DO_NOT_SHOW">DO_NOT_SHOW — Hide column from output</option>
                      <option value="NONE">NONE — Return raw unmasked value</option>
                    </optgroup>
                    <optgroup label="Extended Strategies">
                      <option value="GENERALIZATION">GENERALIZATION — Convert to numeric ranges</option>
                      <option value="TOKENIZATION">TOKENIZATION — Random token replacement</option>
                      <option value="NOISE_ADDITION">NOISE_ADDITION — Add percentage noise</option>
                      <option value="HASH">HASH — Deterministic hash</option>
                      <option value="SSN_MASK">SSN_MASK — Mask SSN (***-**-1234)</option>
                      <option value="CREDIT_CARD_MASK">CREDIT_CARD_MASK — Mask CC (****-****-****-1234)</option>
                      <option value="DATE_MASK">DATE_MASK — Preserve year (YYYY-01-01)</option>
                    </optgroup>
                  </select>
                </div>

                <div>
                  <label htmlFor="edit-policy-sensitivity" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                    Sensitivity Level:
                  </label>
                  <select
                    id="edit-policy-sensitivity"
                    value={editSensitivity}
                    onChange={(e) => setEditSensitivity(e.target.value)}
                    disabled={savingEdit}
                    style={{
                      width: '100%',
                      padding: '0.55rem 0.75rem',
                      borderRadius: '6px',
                      border: '1px solid #cbd5e1',
                      fontSize: '0.88rem',
                      background: '#ffffff',
                      color: '#0f172a',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    <option value="HIGH">HIGH (Restricted / PII)</option>
                    <option value="MEDIUM">MEDIUM (Internal)</option>
                    <option value="LOW">LOW (General)</option>
                  </select>
                </div>
              </div>

              {/* Strategy-Specific Parameters Section */}
              <div style={{ marginBottom: '1.25rem', padding: '0.85rem 1rem', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.5rem' }}>
                  Strategy Configuration & Parameters
                </div>

                {/* PARTIAL Masking Parameters */}
                {(editStrategy.toUpperCase() === 'PARTIAL' || editStrategy.toUpperCase() === 'PARTIAL_MASK') && (
                  <div>
                    <label htmlFor="edit-visible-chars" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.3rem' }}>
                      Visible Edge Characters (<code>visible_chars</code>):
                    </label>
                    <input
                      id="edit-visible-chars"
                      type="number"
                      min="1"
                      max="20"
                      value={editVisibleChars}
                      onChange={(e) => {
                        setEditVisibleChars(e.target.value)
                        setEditError(null)
                      }}
                      disabled={savingEdit}
                      style={{
                        width: '100%',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.88rem',
                        boxSizing: 'border-box'
                      }}
                    />
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                      Preserves the first <code>{editVisibleChars || 2}</code> and last <code>{editVisibleChars || 2}</code> characters, replacing middle characters with asterisks (e.g. <code>jo***th</code>).
                    </div>
                  </div>
                )}

                {/* GENERALIZATION Parameters */}
                {(editStrategy.toUpperCase() === 'GENERALIZATION') && (
                  <div>
                    <label htmlFor="edit-bin-size" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.3rem' }}>
                      Bin Size Range (<code>bin_size</code>):
                    </label>
                    <input
                      id="edit-bin-size"
                      type="number"
                      min="1"
                      step="any"
                      value={editBinSize}
                      onChange={(e) => {
                        setEditBinSize(e.target.value)
                        setEditError(null)
                      }}
                      disabled={savingEdit}
                      style={{
                        width: '100%',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.88rem',
                        boxSizing: 'border-box'
                      }}
                    />
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                      Groups numeric values into bucket intervals of this size (e.g. <code>{editBinSize || 1000}</code> converts <code>5400</code> to <code>5000-6000</code>).
                    </div>
                  </div>
                )}

                {/* TOKENIZATION Parameters */}
                {(editStrategy.toUpperCase() === 'TOKENIZATION') && (
                  <div>
                    <label htmlFor="edit-token-length" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.3rem' }}>
                      Token Length (<code>token_length</code>):
                    </label>
                    <input
                      id="edit-token-length"
                      type="number"
                      min="8"
                      max="64"
                      value={editTokenLength}
                      onChange={(e) => {
                        setEditTokenLength(e.target.value)
                        setEditError(null)
                      }}
                      disabled={savingEdit}
                      style={{
                        width: '100%',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.88rem',
                        boxSizing: 'border-box'
                      }}
                    />
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                      Generates a random alphanumeric token of length <code>{editTokenLength || 16}</code> (min 8).
                    </div>
                  </div>
                )}

                {/* NOISE ADDITION Parameters */}
                {(editStrategy.toUpperCase() === 'NOISE_ADDITION') && (
                  <div>
                    <label htmlFor="edit-noise-level" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.3rem' }}>
                      Noise Level (<code>noise_level</code>, 0.0 - 1.0):
                    </label>
                    <input
                      id="edit-noise-level"
                      type="number"
                      min="0.0"
                      max="1.0"
                      step="0.01"
                      value={editNoiseLevel}
                      onChange={(e) => {
                        setEditNoiseLevel(e.target.value)
                        setEditError(null)
                      }}
                      disabled={savingEdit}
                      style={{
                        width: '100%',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.88rem',
                        boxSizing: 'border-box'
                      }}
                    />
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                      Adds random variation scaled by <code>{editNoiseLevel || 0.1}</code> (e.g. 0.1 represents ±10% variation).
                    </div>
                  </div>
                )}

                {/* HASH Parameters */}
                {(editStrategy.toUpperCase() === 'HASH') && (
                  <div>
                    <label htmlFor="edit-hash-algo" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.3rem' }}>
                      Hash Algorithm (<code>algorithm</code>):
                    </label>
                    <select
                      id="edit-hash-algo"
                      value={editHashAlgorithm}
                      onChange={(e) => setEditHashAlgorithm(e.target.value)}
                      disabled={savingEdit}
                      style={{
                        width: '100%',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '6px',
                        border: '1px solid #cbd5e1',
                        fontSize: '0.88rem',
                        background: '#ffffff',
                        cursor: 'pointer'
                      }}
                    >
                      <option value="sha256">SHA-256 (Default)</option>
                      <option value="md5">MD5 (Fast / PL/pgSQL)</option>
                      <option value="sha512">SHA-512 (High Security)</option>
                    </select>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.35rem' }}>
                      Replaces data with deterministic one-way cryptographic hash.
                    </div>
                  </div>
                )}

                {/* EMAIL Notice */}
                {(editStrategy.toUpperCase() === 'EMAIL' || editStrategy.toUpperCase() === 'EMAIL_MASK') && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>Email Masking:</strong> Preserves the first character of username and the domain (e.g. <code>j***@example.com</code>). No extra parameters required.</span>
                  </div>
                )}

                {/* PHONE_LAST4 Notice */}
                {(editStrategy.toUpperCase() === 'PHONE_LAST4' || editStrategy.toUpperCase() === 'PHONE' || editStrategy.toUpperCase() === 'PHONE_MASK' || editStrategy.toUpperCase() === 'LAST4') && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>Phone Masking:</strong> Preserves the last 4 digits and masks all preceding numbers (e.g. <code>***-***-1234</code>). No extra parameters required.</span>
                  </div>
                )}

                {/* REDACT Notice */}
                {(editStrategy.toUpperCase() === 'REDACT' || editStrategy.toUpperCase() === 'REDACTION') && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>Full Redaction:</strong> Replaces the entire value with asterisks <code>***</code> of equal length. No extra parameters required.</span>
                  </div>
                )}

                {/* DO_NOT_SHOW Notice */}
                {(editStrategy.toUpperCase() === 'DO_NOT_SHOW' || editStrategy.toUpperCase() === 'DONOTSHOW' || editStrategy.toUpperCase() === 'HIDE' || editStrategy.toUpperCase() === 'HIDDEN') && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>Exclude Column:</strong> Replaces output with <code>[HIDDEN]</code> and excludes raw data from query results. No extra parameters required.</span>
                  </div>
                )}

                {/* NONE Notice */}
                {(editStrategy.toUpperCase() === 'NONE' || editStrategy.toUpperCase() === 'NO_MASK') && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>No Masking:</strong> Returns original raw PostgreSQL values without modification. No extra parameters required.</span>
                  </div>
                )}

                {/* SSN / CC / Date Notice */}
                {['SSN_MASK', 'CREDIT_CARD_MASK', 'DATE_MASK'].includes(editStrategy.toUpperCase()) && (
                  <div style={{ fontSize: '0.85rem', color: '#334155', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span><strong>Deterministic Standard:</strong> Built-in pattern applied automatically at database level. No extra parameters required.</span>
                  </div>
                )}
              </div>

              {/* Description / Rationale */}
              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="edit-policy-desc" style={{ display: 'block', fontWeight: '600', fontSize: '0.85rem', color: '#334155', marginBottom: '0.35rem' }}>
                  Description / Security Rationale:
                </label>
                <input
                  id="edit-policy-desc"
                  type="text"
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  placeholder="e.g. Mask patient email addresses for privacy compliance"
                  disabled={savingEdit}
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.88rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              {/* Database Protection Notice */}
              <div style={{
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: '8px',
                padding: '0.75rem 1rem',
                marginBottom: '1.5rem',
                fontSize: '0.84rem',
                color: '#166534',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span><strong>Database protection:</strong> Saving this policy automatically updates its PostgreSQL database-level masking behavior.</span>
              </div>

              {/* Modal Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                <button
                  type="button"
                  onClick={handleCloseEdit}
                  disabled={savingEdit}
                  style={{
                    padding: '0.55rem 1.15rem',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    background: 'white',
                    color: '#475569',
                    fontWeight: '600',
                    fontSize: '0.88rem',
                    cursor: savingEdit ? 'not-allowed' : 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="save-edit-policy-btn"
                  disabled={savingEdit}
                  style={{
                    padding: '0.55rem 1.35rem',
                    borderRadius: '6px',
                    border: 'none',
                    background: savingEdit ? '#94a3b8' : '#2563eb',
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '0.88rem',
                    cursor: savingEdit ? 'not-allowed' : 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.4rem'
                  }}
                >
                  {savingEdit ? (
                    <>
                      <span className="spinner" style={{ width: '14px', height: '14px', borderTopColor: 'white' }} />
                      Saving Policy Changes...
                    </>
                  ) : (
                    'Save Policy Changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default MaskingPolicies
