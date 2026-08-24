import React, { useState, useEffect, useCallback } from 'react'
import {
  Database,
  Table2,
  Search,
  RefreshCw,
  Key,
  Link2,
  AlertCircle,
  CheckCircle2,
  FileCode,
  ArrowRight,
  Shield,
  Loader2
} from 'lucide-react'
import { schemaAPI, healthAPI } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function SchemaBrowser() {
  const [dbStatus, setDbStatus] = useState({ checked: false, connected: false, message: '' })
  const [schemas, setSchemas] = useState([])
  const [selectedSchema, setSelectedSchema] = useState('public')
  const [tables, setTables] = useState([])
  const [searchFilter, setSearchFilter] = useState('')
  const [selectedTable, setSelectedTable] = useState(null)
  const [loadingSchemas, setLoadingSchemas] = useState(false)
  const [loadingTables, setLoadingTables] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [error, setError] = useState(null)

  // Check database connection status
  const checkConnection = useCallback(async () => {
    try {
      const res = await healthAPI.checkDatabase()
      if (res.data?.status === 'healthy') {
        setDbStatus({ checked: true, connected: true, message: 'Connected to PostgreSQL' })
      } else {
        setDbStatus({ checked: true, connected: false, message: res.data?.database || 'Database unavailable' })
      }
    } catch (err) {
      setDbStatus({ checked: true, connected: false, message: 'Unable to connect to PostgreSQL backend' })
    }
  }, [])

  // Fetch available schemas
  const fetchSchemas = useCallback(async () => {
    setLoadingSchemas(true)
    setError(null)
    try {
      const res = await schemaAPI.getSchemas()
      const list = res.data || []
      setSchemas(list)
      if (list.length > 0 && !list.includes(selectedSchema)) {
        setSelectedSchema(list[0])
      }
    } catch (err) {
      console.error('Failed to fetch schemas:', err)
      setError('Failed to load database schemas. Ensure the backend and PostgreSQL are reachable.')
    } finally {
      setLoadingSchemas(false)
    }
  }, [selectedSchema])

  // Fetch single table detailed schema
  const fetchTableDetails = async (tableName, schemaToUse) => {
    const schema = schemaToUse || selectedSchema
    setLoadingDetails(true)
    setError(null)
    try {
      const response = await schemaAPI.getTableSchema(tableName, schema)
      setSelectedTable(response.data)
    } catch (err) {
      console.error('Failed to fetch table schema:', err)
      setError(`Failed to load schema details for table "${tableName}".`)
    } finally {
      setLoadingDetails(false)
    }
  }

  // Fetch tables for current schema
  const fetchTables = useCallback(async (schemaToUse) => {
    const schema = schemaToUse || selectedSchema
    setLoadingTables(true)
    setError(null)
    setSelectedTable(null)
    try {
      const response = await schemaAPI.getTables(schema)
      const tableList = response.data || []
      setTables(tableList)
      if (tableList.length > 0) {
        fetchTableDetails(tableList[0], schema)
      }
    } catch (err) {
      console.error('Failed to fetch tables:', err)
      setError(`Failed to load tables for schema "${schema}".`)
      setTables([])
    } finally {
      setLoadingTables(false)
    }
  }, [selectedSchema])

  // Initial load
  useEffect(() => {
    checkConnection()
    fetchSchemas()
  }, [checkConnection, fetchSchemas])

  // When schema changes, reload tables
  useEffect(() => {
    if (selectedSchema) {
      fetchTables(selectedSchema)
    }
  }, [selectedSchema, fetchTables])

  const handleRefresh = () => {
    checkConnection()
    fetchSchemas()
    fetchTables(selectedSchema)
  }

  const filteredTables = tables.filter(t =>
    t.toLowerCase().includes(searchFilter.toLowerCase().trim())
  )

  return (
    <div className="space-y-6">
      {/* Header & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            PostgreSQL Schema Browser
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Inspect PostgreSQL schemas, tables, column types, primary keys, and foreign key relationships.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {dbStatus.connected ? (
            <Badge variant="success" className="text-xs font-mono py-1 px-2.5 gap-1.5 font-normal">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Connected
            </Badge>
          ) : (
            <Badge variant="destructive" className="text-xs font-mono py-1 px-2.5 gap-1.5 font-normal">
              <AlertCircle className="h-3.5 w-3.5" />
              Database Offline
            </Badge>
          )}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="py-2.5 text-xs">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="h-6 text-xs px-1">
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Controls Bar: Schema Selector & Table Search */}
      <div className="rounded-lg border bg-card p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-medium text-muted-foreground text-xs">Database Schema:</span>
          <select
            id="schema-select"
            value={selectedSchema}
            onChange={(e) => setSelectedSchema(e.target.value)}
            disabled={loadingSchemas}
            className="h-8 rounded-md border border-input bg-background px-3 text-xs font-mono shadow-sm focus:outline-none focus:ring-1 focus:ring-ring font-medium"
          >
            {schemas.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
            {schemas.length === 0 && <option value="public">public</option>}
          </select>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search tables..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="h-8 pl-8 text-xs font-mono"
          />
        </div>
      </div>

      {/* Main Dual-Pane Browser Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-start">
        {/* Left Pane: Table List Sidebar */}
        <Card className="lg:col-span-1 shadow-xs border-border/80 overflow-hidden">
          <CardHeader className="p-3 bg-muted/40 border-b flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground font-mono flex items-center gap-1.5">
              <Table2 className="h-3.5 w-3.5" />
              Tables
            </CardTitle>
            <Badge variant="secondary" className="text-[10px] font-mono h-4 px-1.5">
              {tables.length}
            </Badge>
          </CardHeader>
          <CardContent className="p-1.5 max-h-[600px] overflow-y-auto">
            {loadingTables ? (
              <div className="p-6 text-center text-xs text-muted-foreground space-y-2">
                <Loader2 className="h-4 w-4 animate-spin mx-auto text-primary" />
                <span>Loading tables...</span>
              </div>
            ) : filteredTables.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                {tables.length === 0 ? 'No tables found in this schema.' : 'No matching tables.'}
              </div>
            ) : (
              <div className="space-y-0.5">
                {filteredTables.map(table => {
                  const isActive = selectedTable?.table_name === table
                  return (
                    <button
                      key={table}
                      type="button"
                      onClick={() => fetchTableDetails(table, selectedSchema)}
                      className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-mono transition-colors flex items-center justify-between ${isActive
                          ? 'bg-accent text-accent-foreground font-semibold shadow-2xs'
                          : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                        }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <FileCode className={`h-3.5 w-3.5 ${isActive ? 'text-primary' : 'text-muted-foreground/70'}`} />
                        <span className="truncate">{table}</span>
                      </div>
                      {isActive && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
                    </button>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Pane: Selected Table Schema Viewer */}
        <div className="lg:col-span-3 space-y-4">
          {loadingDetails ? (
            <Card className="p-12 text-center space-y-2 shadow-xs border-border/80">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-primary" />
              <div className="text-sm font-medium text-foreground">Loading table schema details...</div>
            </Card>
          ) : selectedTable ? (
            <Card className="shadow-xs border-border/80 overflow-hidden space-y-4">
              {/* Table Info Header */}
              <div className="p-4 bg-muted/30 border-b flex flex-wrap items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground border">
                      {selectedSchema}
                    </span>
                    <h2 className="font-mono text-base font-bold text-foreground">
                      {selectedTable.table_name}
                    </h2>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline" className="font-mono text-[11px]">
                    {selectedTable.columns?.length || 0} Columns
                  </Badge>
                  <Badge variant="outline" className="font-mono text-[11px] border-amber-500/30 text-amber-600 dark:text-amber-400 bg-amber-500/5">
                    {selectedTable.primary_keys?.length || 0} Primary Key
                  </Badge>
                  <Badge variant="outline" className="font-mono text-[11px] border-purple-500/30 text-purple-600 dark:text-purple-400 bg-purple-500/5">
                    {selectedTable.foreign_keys?.length || 0} Foreign Keys
                  </Badge>
                </div>
              </div>

              <div className="p-4 pt-0 space-y-4">
                {/* Primary Keys Summary */}
                {selectedTable.primary_keys && selectedTable.primary_keys.length > 0 && (
                  <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-2.5 px-3 flex items-center gap-2.5 text-xs">
                    <Key className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                    <span className="font-medium text-amber-900 dark:text-amber-200">Primary Key:</span>
                    <div className="flex items-center gap-1.5 flex-wrap font-mono">
                      {selectedTable.primary_keys.map(pk => (
                        <Badge key={pk} variant="outline" className="text-[11px] bg-background border-amber-500/30 text-amber-700 dark:text-amber-300">
                          {pk}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Foreign Keys Summary */}
                {selectedTable.foreign_keys && selectedTable.foreign_keys.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                      <Link2 className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
                      <span>Foreign Key Relationships ({selectedTable.foreign_keys.length}):</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                      {selectedTable.foreign_keys.map((fk, idx) => (
                        <div key={idx} className="p-2 rounded-md border bg-muted/20 flex items-center justify-between gap-2">
                          <span className="text-primary font-semibold">{fk.column_name}</span>
                          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                          <span className="text-foreground">
                            <strong>{fk.foreign_table_name}</strong>.{fk.foreign_column_name}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Columns Table */}
                <div className="rounded-md border bg-card overflow-hidden">
                  <Table>
                    <TableHeader className="bg-muted/40">
                      <TableRow className="hover:bg-transparent">
                        <TableHead className="font-mono text-xs w-[25%]">Column</TableHead>
                        <TableHead className="font-mono text-xs w-[22%]">Data Type</TableHead>
                        <TableHead className="text-xs w-[16%]">Constraints</TableHead>
                        <TableHead className="text-xs w-[12%]">Nullable</TableHead>
                        <TableHead className="text-xs w-[12%]">Max Length</TableHead>
                        <TableHead className="font-mono text-xs w-[13%]">Default</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedTable.columns?.map(column => {
                        const isPk = selectedTable.primary_keys?.includes(column.column_name) || column.is_primary_key
                        const fkRelation = selectedTable.foreign_keys?.find(
                          fk => fk.column_name === column.column_name
                        )

                        return (
                          <TableRow key={column.column_name} className={`text-xs hover:bg-muted/30 ${isPk ? 'bg-amber-500/5' : ''}`}>
                            <TableCell className="font-mono font-medium text-foreground">
                              {column.column_name}
                            </TableCell>
                            <TableCell>
                              <code className="font-mono text-[11px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                                {column.data_type}
                              </code>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                {isPk && (
                                  <Badge variant="warning" className="text-[10px] h-4.5 px-1 font-mono">
                                    PK
                                  </Badge>
                                )}
                                {fkRelation && (
                                  <Badge
                                    variant="purple"
                                    className="text-[10px] h-4.5 px-1 font-mono"
                                    title={`Foreign Key -> ${fkRelation.foreign_table_name}.${fkRelation.foreign_column_name}`}
                                  >
                                    FK
                                  </Badge>
                                )}
                                {!isPk && !fkRelation && <span className="text-muted-foreground/60">—</span>}
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={column.is_nullable ? "secondary" : "outline"}
                                className={`text-[10px] font-mono ${!column.is_nullable ? 'border-border text-foreground font-semibold' : 'text-muted-foreground'}`}
                              >
                                {column.is_nullable ? 'YES' : 'NO'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-muted-foreground font-mono text-xs">
                              {column.character_maximum_length != null ? column.character_maximum_length : '—'}
                            </TableCell>
                            <TableCell className="text-muted-foreground font-mono text-[11px] truncate max-w-[120px]" title={column.column_default}>
                              {column.column_default ? column.column_default : '—'}
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </Card>
          ) : (
            <Card className="p-12 text-center space-y-2 shadow-xs border-border/80">
              <div className="h-10 w-10 rounded-full bg-muted/60 text-muted-foreground flex items-center justify-center mx-auto">
                <Table2 className="h-5 w-5" />
              </div>
              <div className="text-sm font-medium text-foreground">Select a table</div>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                Select a table from the sidebar to inspect its columns, types, constraints, and relationships.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default SchemaBrowser
