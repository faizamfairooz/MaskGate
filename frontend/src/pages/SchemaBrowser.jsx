import React, { useState, useEffect, useCallback } from 'react'
import { schemaAPI, healthAPI } from '../services/api'

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
        // Auto-select first table for immediate visibility
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
    <div className="schema-browser">
      {/* Header & Connection Status */}
      <div className="browser-header">
        <div>
          <h2>PostgreSQL Schema Browser</h2>
          <p className="subtitle">
            Inspect PostgreSQL schemas, tables, data types, primary keys, and foreign key relationships.
          </p>
        </div>
        <div className="header-actions">
          <span className={`status-pill ${dbStatus.connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {dbStatus.connected ? 'PostgreSQL Connected' : 'Database Offline'}
          </span>
          <button className="btn-secondary" onClick={handleRefresh} title="Refresh schema metadata">
            ↻ Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)} className="btn-dismiss">×</button>
        </div>
      )}

      {/* Schema Selector & Global Controls */}
      <div className="schema-controls-bar">
        <div className="control-group">
          <label htmlFor="schema-select"><strong>Database Schema:</strong></label>
          <select
            id="schema-select"
            value={selectedSchema}
            onChange={(e) => setSelectedSchema(e.target.value)}
            disabled={loadingSchemas}
          >
            {schemas.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
            {schemas.length === 0 && <option value="public">public</option>}
          </select>
        </div>
        <div className="control-group search-group">
          <input
            type="text"
            placeholder="Search tables..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {/* Main Content: Tables Sidebar & Table Schema Viewer */}
      <div className="schema-content">
        {/* Tables list */}
        <div className="tables-list">
          <div className="tables-list-header">
            <h3>Tables</h3>
            <span className="badge">{tables.length}</span>
          </div>

          {loadingTables ? (
            <div className="loading-state">Loading tables...</div>
          ) : filteredTables.length === 0 ? (
            <div className="empty-state">
              {tables.length === 0 ? 'No tables found in this schema.' : 'No matching tables.'}
            </div>
          ) : (
            <ul className="table-items">
              {filteredTables.map(table => {
                const isActive = selectedTable?.table_name === table
                return (
                  <li
                    key={table}
                    onClick={() => fetchTableDetails(table, selectedSchema)}
                    className={`table-item ${isActive ? 'active' : ''}`}
                  >
                    <span className="table-icon">📄</span>
                    <span className="table-name-text">{table}</span>
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        {/* Table Details */}
        <div className="table-details">
          {loadingDetails ? (
            <div className="loading-state">Loading table schema details...</div>
          ) : selectedTable ? (
            <div>
              {/* Table Info Header */}
              <div className="table-info-header">
                <div>
                  <span className="schema-tag">{selectedSchema}</span>
                  <h3>{selectedTable.table_name}</h3>
                </div>
                <div className="table-stats">
                  <span className="stat-tag">{selectedTable.columns?.length || 0} Columns</span>
                  <span className="stat-tag">{selectedTable.primary_keys?.length || 0} PK</span>
                  <span className="stat-tag">{selectedTable.foreign_keys?.length || 0} FK</span>
                </div>
              </div>

              {/* Primary Keys Summary */}
              {selectedTable.primary_keys && selectedTable.primary_keys.length > 0 && (
                <div className="keys-section pk-section">
                  <div className="keys-section-title">
                    <span className="key-icon pk-icon">🔑</span>
                    <strong>Primary Key:</strong>
                  </div>
                  <div className="key-chips">
                    {selectedTable.primary_keys.map(pk => (
                      <span key={pk} className="chip pk-chip">{pk}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Foreign Keys Summary */}
              {selectedTable.foreign_keys && selectedTable.foreign_keys.length > 0 && (
                <div className="keys-section fk-section">
                  <div className="keys-section-title">
                    <span className="key-icon fk-icon">🔗</span>
                    <strong>Foreign Keys ({selectedTable.foreign_keys.length}):</strong>
                  </div>
                  <div className="fk-grid">
                    {selectedTable.foreign_keys.map((fk, idx) => (
                      <div key={idx} className="fk-card">
                        <span className="fk-source">{fk.column_name}</span>
                        <span className="fk-arrow">➔</span>
                        <span className="fk-target">
                          <strong>{fk.foreign_table_name}</strong>.{fk.foreign_column_name}
                        </span>
                        {fk.constraint_name && (
                          <span className="fk-constraint" title={fk.constraint_name}>
                            ({fk.constraint_name})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Columns Table */}
              <div className="table-wrapper">
                <table className="schema-table">
                  <thead>
                    <tr>
                      <th style={{ width: '25%' }}>Column</th>
                      <th style={{ width: '22%' }}>Data Type</th>
                      <th style={{ width: '15%' }}>Constraints</th>
                      <th style={{ width: '13%' }}>Nullable</th>
                      <th style={{ width: '12%' }}>Max Length</th>
                      <th style={{ width: '13%' }}>Default</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedTable.columns?.map(column => {
                      const isPk = selectedTable.primary_keys?.includes(column.column_name) || column.is_primary_key
                      const fkRelation = selectedTable.foreign_keys?.find(
                        fk => fk.column_name === column.column_name
                      )

                      return (
                        <tr key={column.column_name} className={isPk ? 'pk-row' : ''}>
                          <td className="column-name-cell">
                            <span className="column-name">{column.column_name}</span>
                          </td>
                          <td>
                            <code className="data-type-badge">{column.data_type}</code>
                          </td>
                          <td>
                            <div className="constraints-badges">
                              {isPk && <span className="badge badge-pk" title="Primary Key">PK</span>}
                              {fkRelation && (
                                <span
                                  className="badge badge-fk"
                                  title={`Foreign Key -> ${fkRelation.foreign_table_name}.${fkRelation.foreign_column_name}`}
                                >
                                  FK
                                </span>
                              )}
                              {!isPk && !fkRelation && <span className="text-muted">—</span>}
                            </div>
                          </td>
                          <td>
                            <span className={`null-pill ${column.is_nullable ? 'nullable' : 'not-nullable'}`}>
                              {column.is_nullable ? 'YES' : 'NO'}
                            </span>
                          </td>
                          <td className="text-muted">
                            {column.character_maximum_length != null ? column.character_maximum_length : '—'}
                          </td>
                          <td className="default-val-cell">
                            {column.column_default ? (
                              <code className="default-code" title={column.column_default}>
                                {column.column_default}
                              </code>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="empty-selection">
              <div className="empty-icon">📊</div>
              <p>Select a table from the sidebar to inspect its columns, types, and constraints.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SchemaBrowser
