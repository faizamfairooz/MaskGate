import React, { useState } from 'react'
import { queryAPI } from '../services/api'

const SAMPLE_QUERIES = [
  {
    name: 'Patients (Basic SELECT)',
    query: 'SELECT * FROM patients LIMIT 5',
    description: 'Retrieves patient records with deterministic masking on email and phone.'
  },
  {
    name: 'Multi-Table JOIN (Patients & Records)',
    query: 'SELECT p.patient_id, p.full_name, p.email, p.phone, m.diagnosis, m.visit_date\nFROM patients p\nJOIN medical_records m ON p.patient_id = m.patient_id\nLIMIT 5;',
    description: 'Demonstrates multi-table policy resolution across joined tables.'
  },
  {
    name: 'Unbounded SELECT (Safe Default LIMIT)',
    query: 'SELECT patient_id, full_name, email, blood_group FROM patients',
    description: 'Demonstrates automatic enforcement of the safe default LIMIT (100).'
  },
  {
    name: 'Users Table',
    query: 'SELECT id, username, email, full_name FROM users LIMIT 5',
    description: 'Queries user metadata with active masking policies applied.'
  }
]

function QueryEditor() {
  const [query, setQuery] = useState('SELECT * FROM patients LIMIT 5')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [applyMasking, setApplyMasking] = useState(true)
  const [maskSuspicious, setMaskSuspicious] = useState(false)
  const [copiedQuery, setCopiedQuery] = useState(false)

  const executeQuery = async (e) => {
    if (e) e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setResults(null)

    try {
      const response = await queryAPI.execute({
        query: query.trim(),
        apply_masking: applyMasking,
        mask_suspicious: maskSuspicious
      })
      setResults(response.data)
    } catch (error) {
      const detail = error.response?.data?.detail || error.message || 'Query execution failed'
      setResults({ error: detail })
    } finally {
      setLoading(false)
    }
  }

  const handleCopyQuery = () => {
    navigator.clipboard.writeText(query)
    setCopiedQuery(true)
    setTimeout(() => setCopiedQuery(false), 2000)
  }

  const hasOuterLimit = (sql) => {
    return /\bLIMIT\b/i.test(sql)
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      {/* Header & Title */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: '0 0 0.25rem 0', fontSize: '1.6rem', fontWeight: '800', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>⚡</span> SQL Query Editor
          </h1>
          <p style={{ margin: 0, color: '#64748b', fontSize: '0.92rem' }}>
            Execute SELECT queries against PostgreSQL with deterministic data masking and runtime sensitive data detection.
          </p>
        </div>

        {/* Security Assurances Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '0.4rem 0.85rem', borderRadius: '8px', fontSize: '0.82rem', color: '#166534', fontWeight: '600' }}>
          <span>🛡️</span>
          <span>Security Engine: <strong>Application-Controlled</strong> (LLM does NOT execute SQL)</span>
        </div>
      </div>

      {/* Query Pipeline Explanation Banner */}
      <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Execution & Masking Pipeline
          </span>
          <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
            Strictly read-only SELECT • Stage 1 Deterministic • Stage 2 Optional AI
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.25rem', fontSize: '0.83rem', fontWeight: '600' }}>
          <div style={{ background: '#e0f2fe', color: '#0369a1', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            1. User SQL
          </div>
          <span style={{ color: '#94a3b8' }}>→</span>
          <div style={{ background: '#f1f5f9', color: '#334155', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            2. Policy & Limit Hardening
          </div>
          <span style={{ color: '#94a3b8' }}>→</span>
          <div style={{ background: '#f3e8ff', color: '#6b21a8', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            3. PostgreSQL Execute
          </div>
          <span style={{ color: '#94a3b8' }}>→</span>
          <div style={{ background: '#dcfce7', color: '#166534', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            4. Deterministic Masking
          </div>
          <span style={{ color: '#94a3b8' }}>→</span>
          <div style={{ background: '#ffedd5', color: '#c2410c', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            5. Runtime AI Detection (Opt)
          </div>
          <span style={{ color: '#94a3b8' }}>→</span>
          <div style={{ background: '#e2e8f0', color: '#0f172a', padding: '0.35rem 0.65rem', borderRadius: '6px', whiteSpace: 'nowrap' }}>
            6. Safe Result
          </div>
        </div>
      </div>

      {/* Main Query Form */}
      <div style={{ background: 'white', border: '1px solid #cbd5e1', borderRadius: '10px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)', marginBottom: '1.5rem', overflow: 'hidden' }}>
        {/* Editor Toolbar & Sample Queries */}
        <div style={{ padding: '0.75rem 1rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: '600', color: '#475569' }}>Quick Templates:</span>
            {SAMPLE_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(preset.query)}
                title={preset.description}
                style={{
                  background: query === preset.query ? '#e2e8f0' : 'white',
                  border: '1px solid #cbd5e1',
                  borderRadius: '5px',
                  padding: '0.25rem 0.55rem',
                  fontSize: '0.78rem',
                  fontWeight: '600',
                  color: '#1e293b',
                  cursor: 'pointer'
                }}
              >
                {preset.name}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={handleCopyQuery}
              style={{
                background: 'white',
                border: '1px solid #cbd5e1',
                borderRadius: '5px',
                padding: '0.25rem 0.6rem',
                fontSize: '0.78rem',
                color: '#475569',
                cursor: 'pointer',
                fontWeight: '500'
              }}
            >
              {copiedQuery ? '✓ Copied' : '📋 Copy SQL'}
            </button>
          </div>
        </div>

        {/* Textarea Code Area */}
        <form onSubmit={executeQuery}>
          <div style={{ position: 'relative' }}>
            <textarea
              id="sql-query-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your SQL SELECT query here..."
              rows={8}
              spellCheck={false}
              style={{
                width: '100%',
                padding: '1rem',
                fontSize: '0.95rem',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                lineHeight: '1.5',
                border: 'none',
                outline: 'none',
                resize: 'vertical',
                boxSizing: 'border-box',
                background: '#ffffff',
                color: '#0f172a'
              }}
            />
          </div>

          {/* Masking Controls & Submit Section */}
          <div style={{ padding: '1rem', background: '#f8fafc', borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              {/* Option 1: Apply Approved Masking Policies */}
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.88rem', color: '#1e293b', fontWeight: '600' }}>
                <input
                  type="checkbox"
                  id="toggle-apply-masking"
                  checked={applyMasking}
                  onChange={(e) => setApplyMasking(e.target.checked)}
                  style={{ width: '16px', height: '16px', accentColor: '#2563eb', cursor: 'pointer' }}
                />
                <span>Apply Approved Masking Policies</span>
                <span style={{ fontSize: '0.75rem', fontWeight: '500', color: '#64748b', background: '#e2e8f0', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                  Deterministic Engine
                </span>
              </label>

              {/* Option 2: Detect Suspicious Sensitive Data */}
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.88rem', color: '#1e293b', fontWeight: '600' }}>
                <input
                  type="checkbox"
                  id="toggle-mask-suspicious"
                  checked={maskSuspicious}
                  onChange={(e) => setMaskSuspicious(e.target.checked)}
                  style={{ width: '16px', height: '16px', accentColor: '#ea580c', cursor: 'pointer' }}
                />
                <span>Detect Suspicious Sensitive Data</span>
                <span style={{ fontSize: '0.75rem', fontWeight: '500', color: '#c2410c', background: '#ffedd5', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                  Runtime AI & Heuristics
                </span>
              </label>
            </div>

            {/* Run Button */}
            <div>
              <button
                type="submit"
                id="execute-query-btn"
                disabled={loading || !query.trim()}
                style={{
                  padding: '0.65rem 1.5rem',
                  background: loading || !query.trim() ? '#94a3b8' : '#2563eb',
                  color: 'white',
                  border: 'none',
                  borderRadius: '7px',
                  fontWeight: '700',
                  fontSize: '0.95rem',
                  cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
                }}
              >
                <span>{loading ? '⏳' : '▶'}</span>
                <span>{loading ? 'Executing Query...' : 'Run Query'}</span>
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Query Results Section */}
      {results && (
        <div style={{ marginTop: '1.5rem' }}>
          {results.error ? (
            /* Error Card */
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '1.25rem', color: '#991b1b' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: '700', fontSize: '1rem', marginBottom: '0.35rem' }}>
                <span>❌</span> Query Error
              </div>
              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.5' }}>
                {results.error}
              </p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', color: '#b91c1c' }}>
                Tip: Ensure your query is a valid read-only SELECT statement and contains valid syntax.
              </p>
            </div>
          ) : (
            /* Success Results View */
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '10px', overflow: 'hidden', boxShadow: '0 1px 4px rgba(0,0,0,0.03)' }}>
              {/* Results Metadata Summary Bar */}
              <div style={{ padding: '1rem 1.25rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                {/* Stats Badges */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#f1f5f9', padding: '0.3rem 0.65rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: '600', color: '#334155' }}>
                    <span>📊</span>
                    <span>{results.row_count} rows</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#f1f5f9', padding: '0.3rem 0.65rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: '600', color: '#334155' }}>
                    <span>⏱️</span>
                    <span>{(results.execution_time * 1000).toFixed(1)} ms</span>
                  </div>

                  {results.masked_columns && results.masked_columns.length > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#dcfce7', color: '#166534', padding: '0.3rem 0.65rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: '700', border: '1px solid #bbf7d0' }}>
                      <span>🛡️</span>
                      <span>{results.masked_columns.length} columns masked ({results.masked_columns.join(', ')})</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#f1f5f9', color: '#64748b', padding: '0.3rem 0.65rem', borderRadius: '6px', fontSize: '0.85rem', fontWeight: '500' }}>
                      <span>🛡️</span>
                      <span>No columns masked</span>
                    </div>
                  )}

                  {!hasOuterLimit(query) && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#e0f2fe', color: '#0369a1', padding: '0.3rem 0.65rem', borderRadius: '6px', fontSize: '0.82rem', fontWeight: '600' }}>
                      <span>🔒</span>
                      <span>Safe Default LIMIT Enforced</span>
                    </div>
                  )}
                </div>

                {/* Runtime Summary Pill */}
                {results.runtime_detection_summary && (
                  <div style={{ fontSize: '0.82rem', background: '#ffedd5', color: '#9a3412', border: '1px solid #fed7aa', padding: '0.3rem 0.65rem', borderRadius: '6px', fontWeight: '600' }}>
                    🔍 {results.runtime_detection_summary}
                  </div>
                )}
              </div>

              {/* Data Table */}
              {results.rows.length === 0 ? (
                <div style={{ padding: '3rem 1rem', textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📭</div>
                  <div style={{ fontWeight: '600', color: '#1e293b' }}>No rows returned</div>
                  <div style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>The query executed successfully but produced zero matching rows.</div>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', maxHeight: '500px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
                    <thead style={{ background: '#f1f5f9', position: 'sticky', top: 0, zIndex: 10 }}>
                      <tr>
                        {results.columns.map((column) => {
                          const isMasked = results.masked_columns && results.masked_columns.includes(column)
                          return (
                            <th
                              key={column}
                              style={{
                                padding: '0.75rem 1rem',
                                fontWeight: '700',
                                color: isMasked ? '#166534' : '#1e293b',
                                borderBottom: '2px solid #cbd5e1',
                                background: isMasked ? '#ecfdf5' : '#f1f5f9',
                                whiteSpace: 'nowrap'
                              }}
                            >
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                                <span>{column}</span>
                                {isMasked && <span style={{ fontSize: '0.75rem' }} title="Masked column">🛡️</span>}
                              </div>
                            </th>
                          )
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      {results.rows.map((row, rowIndex) => (
                        <tr
                          key={rowIndex}
                          style={{
                            borderBottom: '1px solid #f1f5f9',
                            background: rowIndex % 2 === 0 ? '#ffffff' : '#f8fafc'
                          }}
                        >
                          {row.map((cell, cellIndex) => {
                            const colName = results.columns[cellIndex]
                            const isMasked = results.masked_columns && results.masked_columns.includes(colName)
                            return (
                              <td
                                key={cellIndex}
                                style={{
                                  padding: '0.65rem 1rem',
                                  color: cell === null ? '#94a3b8' : '#0f172a',
                                  fontFamily: typeof cell === 'number' ? 'ui-monospace, monospace' : 'inherit',
                                  whiteSpace: 'nowrap',
                                  background: isMasked ? (rowIndex % 2 === 0 ? '#f0fdf4' : '#e6fbee') : undefined
                                }}
                              >
                                {cell === null ? (
                                  <em style={{ color: '#94a3b8' }}>NULL</em>
                                ) : (
                                  String(cell)
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default QueryEditor
