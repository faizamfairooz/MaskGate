import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldCheck,
  Shield,
  Sparkles,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  Clock,
  XCircle,
  LayoutGrid,
  List,
  Loader2,
  Database,
  ArrowRight
} from 'lucide-react'
import { maskingAPI, schemaAPI } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { RecommendationCard } from '@/components/policies/RecommendationCard'
import { RecommendationTable } from '@/components/policies/RecommendationTable'
import { PolicyTable } from '@/components/policies/PolicyTable'
import { EditPolicyDialog } from '@/components/policies/EditPolicyDialog'
import { CreatePolicyDialog } from '@/components/policies/CreatePolicyDialog'

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
  const [isCreateOpen, setIsCreateOpen] = useState(false)
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
      setIsCreateOpen(false)
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
      return `Policy #${editingPolicy?.id || ''} was not found in PostgreSQL.`
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

      setPolicies((prev) =>
        prev.map((p) => (p.id === editingPolicy.id ? { ...p, ...updatedPolicy } : p))
      )

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

  const getStrategyBadgeVariant = (strategy) => {
    const s = (strategy || '').toUpperCase()
    if (s.includes('EMAIL')) return 'info'
    if (s.includes('PHONE')) return 'purple'
    if (s.includes('PARTIAL')) return 'warning'
    if (s.includes('GENERALIZATION')) return 'cyan'
    if (s.includes('TOKENIZATION')) return 'indigo'
    if (s.includes('HASH')) return 'purple'
    if (s.includes('REDACT') || s.includes('DO_NOT_SHOW') || s.includes('SSN') || s.includes('CREDIT')) return 'destructive'
    return 'secondary'
  }

  const getSensitivityBadgeVariant = (level) => {
    const l = (level || '').toUpperCase()
    if (l === 'HIGH') return 'destructive'
    if (l === 'MEDIUM') return 'warning'
    return 'info'
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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Masking Policy Management
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Configure dynamic data masking rules and review GenAI-driven schema recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            onClick={handleAnalyzeAndQueue}
            disabled={analyzing}
            className="h-8 gap-1.5 text-xs shadow-xs"
          >
            {analyzing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Sparkles className="h-3.5 w-3.5" />
            )}
            <span>{analyzing ? 'Analyzing Schema...' : 'Run AI Schema Analysis'}</span>
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => { fetchPolicies(); fetchRecommendations(); }}
            className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Conceptual Architecture Workflow Banner */}
      <div className="rounded-lg border border-border/80 bg-muted/20 p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-wrap font-medium">
          <span className="text-muted-foreground font-semibold">Security Pipeline:</span>
          <span className="bg-background px-2 py-0.5 rounded border font-mono text-[11px]">Database Schema</span>
          <ArrowRight className="h-3 w-3 text-muted-foreground" />
          <span className="bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20 px-2 py-0.5 rounded font-mono text-[11px]">
            AI Analysis
          </span>
          <ArrowRight className="h-3 w-3 text-muted-foreground" />
          <span className="bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20 px-2 py-0.5 rounded font-mono text-[11px]">
            AI Recommendation
          </span>
          <ArrowRight className="h-3 w-3 text-muted-foreground" />
          <span className="bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 px-2 py-0.5 rounded font-mono text-[11px]">
            Admin Review
          </span>
          <ArrowRight className="h-3 w-3 text-muted-foreground" />
          <span className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20 px-2 py-0.5 rounded font-mono text-[11px] font-semibold flex items-center gap-1">
            <ShieldCheck className="h-3 w-3 text-emerald-600" />
            DB-Level Masking Active
          </span>
        </div>
        <div className="text-[11px] text-muted-foreground">
          LLM generates recommendations; PostgreSQL masking functions are applied automatically.
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card className="p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-muted-foreground">Pending Reviews</span>
            <Clock className="h-4 w-4 text-amber-500" />
          </div>
          <div className="text-xl font-bold font-mono text-foreground mt-1">
            {pendingCount}
          </div>
          <span className="text-[11px] text-muted-foreground">Awaiting admin decision</span>
        </Card>

        <Card className="p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-muted-foreground">Approved Rules</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-xl font-bold font-mono text-foreground mt-1">
            {approvedCount}
          </div>
          <span className="text-[11px] text-muted-foreground">DB masking applied</span>
        </Card>

        <Card className="p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-muted-foreground">Total Active Policies</span>
            <ShieldCheck className="h-4 w-4 text-primary" />
          </div>
          <div className="text-xl font-bold font-mono text-foreground mt-1">
            {policies.length}
          </div>
          <span className="text-[11px] text-muted-foreground">Enforced in database</span>
        </Card>

        <Card className="p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-muted-foreground">Rejected Rules</span>
            <XCircle className="h-4 w-4 text-destructive" />
          </div>
          <div className="text-xl font-bold font-mono text-foreground mt-1">
            {rejectedCount}
          </div>
          <span className="text-[11px] text-muted-foreground">Excluded from policies</span>
        </Card>
      </div>

      {/* Notifications / Feedback Alerts */}
      {message && (
        <Alert variant="success" className="py-2.5 text-xs">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}
      {errorMessage && (
        <Alert variant="destructive" className="py-2.5 text-xs">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      {/* Main Tabs Navigation */}
      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <div className="flex items-center justify-between border-b border-border/80 pb-2">
          <TabsList className="h-8 p-0.5 bg-muted/60">
            <TabsTrigger value="review" className="text-xs h-7 px-3 gap-1.5 data-[state=active]:bg-background">
              <span>AI Recommendations</span>
              <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4">
                {recommendations.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="policies" className="text-xs h-7 px-3 gap-1.5 data-[state=active]:bg-background">
              <span>Active Policies</span>
              <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4">
                {policies.length}
              </Badge>
            </TabsTrigger>
          </TabsList>

          {tab === 'policies' && (
            <CreatePolicyDialog
              isOpen={isCreateOpen}
              onOpenChange={setIsCreateOpen}
              availableSchemas={availableSchemas}
              selectedSchema={selectedSchema}
              onSchemaChange={handleSchemaChange}
              availableTables={availableTables}
              selectedTable={selectedTable}
              onTableChange={handleTableChange}
              availableColumns={availableColumns}
              selectedColumn={selectedColumn}
              setSelectedColumn={setSelectedColumn}
              availableStrategies={availableStrategies}
              selectedStrategy={selectedStrategy}
              setSelectedStrategy={setSelectedStrategy}
              selectedSensitivity={selectedSensitivity}
              setSelectedSensitivity={setSelectedSensitivity}
              policyDescription={policyDescription}
              setPolicyDescription={setPolicyDescription}
              creatingPolicy={creatingPolicy}
              handleCreatePolicy={handleCreatePolicy}
              loadingSchemas={loadingSchemas}
              loadingTables={loadingTables}
              loadingColumns={loadingColumns}
            />
          )}
        </div>

        {/* TAB 1: AI Recommendations Queue */}
        <TabsContent value="review" className="space-y-4 m-0">
          {/* Controls Bar */}
          <div className="rounded-lg border bg-card p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-3 flex-wrap">
              {/* Status Filter */}
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-muted-foreground text-xs">Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2.5 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-ring font-medium"
                >
                  <option value="PENDING">Pending Review</option>
                  <option value="APPROVED">Approved</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="ALL">All Statuses</option>
                </select>
              </div>

              {/* Table Filter */}
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-muted-foreground text-xs">Table:</span>
                <Input
                  type="text"
                  placeholder="Filter table..."
                  value={tableFilter}
                  onChange={(e) => setTableFilter(e.target.value)}
                  className="h-8 w-32 text-xs font-mono"
                />
              </div>

              {/* Free-text Search */}
              <div className="flex items-center gap-1.5">
                <div className="relative">
                  <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search column, rationale..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="h-8 pl-8 w-48 text-xs"
                  />
                </div>
              </div>
            </div>

            {/* View Mode & Counter */}
            <div className="flex items-center gap-3 justify-between md:justify-end">
              <span className="text-muted-foreground text-[11px]">
                Showing <strong>{filteredRecommendations.length}</strong> of <strong>{recommendations.length}</strong>
              </span>

              <div className="flex items-center rounded-md border bg-muted/40 p-0.5">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setViewMode('cards')}
                  className={`h-6 w-6 rounded-xs ${viewMode === 'cards' ? 'bg-background shadow-xs text-foreground' : 'text-muted-foreground'}`}
                  title="Card View"
                >
                  <LayoutGrid className="h-3.5 w-3.5" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => setViewMode('table')}
                  className={`h-6 w-6 rounded-xs ${viewMode === 'table' ? 'bg-background shadow-xs text-foreground' : 'text-muted-foreground'}`}
                  title="Table View"
                >
                  <List className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loadingRecs && (
            <Card className="p-8 text-center space-y-2">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
              <div className="text-sm font-medium text-foreground">Loading AI recommendations...</div>
              <p className="text-xs text-muted-foreground">Retrieving schema suggestions from PostgreSQL.</p>
            </Card>
          )}

          {/* Fetch Error */}
          {!loadingRecs && fetchError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle className="text-xs font-semibold">Failed to load recommendations</AlertTitle>
              <AlertDescription className="text-xs mt-1 flex items-center justify-between">
                <span>{fetchError}</span>
                <Button variant="outline" size="sm" onClick={fetchRecommendations} className="h-7 text-xs">
                  Retry
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {/* Empty State */}
          {!loadingRecs && !fetchError && filteredRecommendations.length === 0 && (
            <Card className="p-8 text-center space-y-3">
              <div className="h-10 w-10 rounded-full bg-muted/60 text-muted-foreground flex items-center justify-center mx-auto">
                <Sparkles className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-foreground">
                  {recommendations.length === 0 ? 'No AI Recommendations Queued' : 'No Matching Recommendations'}
                </h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  {recommendations.length === 0
                    ? 'Run AI Schema Analysis to inspect PostgreSQL tables and generate intelligent masking recommendations.'
                    : 'Try modifying your search query or status filter.'}
                </p>
              </div>
              {recommendations.length === 0 ? (
                <Button size="sm" onClick={handleAnalyzeAndQueue} disabled={analyzing} className="text-xs h-8 gap-1.5">
                  <Sparkles className="h-3.5 w-3.5" />
                  Scan Database Schema with AI
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setStatusFilter('ALL'); setTableFilter(''); setSearchQuery(''); }}
                  className="text-xs h-8"
                >
                  Clear Filters
                </Button>
              )}
            </Card>
          )}

          {/* Content: Cards View */}
          {!loadingRecs && !fetchError && filteredRecommendations.length > 0 && viewMode === 'cards' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              {filteredRecommendations.map((rec) => (
                <RecommendationCard
                  key={rec.id}
                  rec={rec}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  isActioning={actionLoading[rec.id]}
                  getStrategyBadgeVariant={getStrategyBadgeVariant}
                  getSensitivityBadgeVariant={getSensitivityBadgeVariant}
                />
              ))}
            </div>
          )}

          {/* Content: Table View */}
          {!loadingRecs && !fetchError && filteredRecommendations.length > 0 && viewMode === 'table' && (
            <RecommendationTable
              recommendations={filteredRecommendations}
              onApprove={handleApprove}
              onReject={handleReject}
              actionLoading={actionLoading}
              getStrategyBadgeVariant={getStrategyBadgeVariant}
              getSensitivityBadgeVariant={getSensitivityBadgeVariant}
            />
          )}
        </TabsContent>

        {/* TAB 2: Active Policies */}
        <TabsContent value="policies" className="space-y-4 m-0">
          {loadingPolicies ? (
            <Card className="p-8 text-center space-y-2">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
              <div className="text-sm font-medium text-foreground">Loading active policies...</div>
            </Card>
          ) : policies.length === 0 ? (
            <Card className="p-8 text-center space-y-3">
              <div className="h-10 w-10 rounded-full bg-muted/60 text-muted-foreground flex items-center justify-center mx-auto">
                <Shield className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-foreground">No Active Masking Policies</h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  Approve recommendations from the AI Queue or define a custom masking policy.
                </p>
              </div>
              <div className="flex items-center justify-center gap-2">
                <Button size="sm" onClick={() => setTab('review')} className="text-xs h-8">
                  Go to AI Recommendations Queue
                </Button>
                <Button variant="outline" size="sm" onClick={() => setIsCreateOpen(true)} className="text-xs h-8">
                  Create Custom Policy
                </Button>
              </div>
            </Card>
          ) : (
            <PolicyTable
              policies={policies}
              onOpenEdit={handleOpenEdit}
              onDeletePolicy={handleDeletePolicy}
              getStrategyBadgeVariant={getStrategyBadgeVariant}
              getSensitivityBadgeVariant={getSensitivityBadgeVariant}
              formatPolicyParameters={formatPolicyParameters}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Edit Policy Dialog */}
      <EditPolicyDialog
        isOpen={Boolean(editingPolicy)}
        onClose={handleCloseEdit}
        editingPolicy={editingPolicy}
        editStrategy={editStrategy}
        setEditStrategy={setEditStrategy}
        editSensitivity={editSensitivity}
        setEditSensitivity={setEditSensitivity}
        editDescription={editDescription}
        setEditDescription={setEditDescription}
        editVisibleChars={editVisibleChars}
        setEditVisibleChars={setEditVisibleChars}
        editBinSize={editBinSize}
        setEditBinSize={setEditBinSize}
        editTokenLength={editTokenLength}
        setEditTokenLength={setEditTokenLength}
        editNoiseLevel={editNoiseLevel}
        setEditNoiseLevel={setEditNoiseLevel}
        editHashAlgorithm={editHashAlgorithm}
        setEditHashAlgorithm={setEditHashAlgorithm}
        editError={editError}
        setEditError={setEditError}
        savingEdit={savingEdit}
        onSaveEdit={handleSaveEdit}
      />
    </div>
  )
}

export default MaskingPolicies
