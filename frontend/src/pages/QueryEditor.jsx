import React, { useState } from 'react'
import { queryAPI } from '../services/api'

function QueryEditor() {
  const [query, setQuery] = useState('SELECT * FROM customers LIMIT 5')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [applyMasking, setApplyMasking] = useState(true)
  const [maskSuspicious, setMaskSuspicious] = useState(false)

  const executeQuery = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResults(null)

    try {
      const response = await queryAPI.execute({
        query,
        apply_masking: applyMasking,
        mask_suspicious: maskSuspicious
      })
      setResults(response.data)
    } catch (error) {
      const detail = error.response?.data?.detail
      setResults({ error: detail || 'Query execution failed' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="query-editor">
      <h2>Query Editor</h2>
      <p className="hint">Only SELECT queries are allowed.</p>
      <form onSubmit={executeQuery} className="query-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your SQL query here..."
          rows={10}
        />
        <div className="query-options">
          <label>
            <input
              type="checkbox"
              checked={applyMasking}
              onChange={(e) => setApplyMasking(e.target.checked)}
            />
            Apply approved masking policies
          </label>
          <label>
            <input
              type="checkbox"
              checked={maskSuspicious}
              onChange={(e) => setMaskSuspicious(e.target.checked)}
            />
            Runtime sensitive-data detection
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Executing...' : 'Execute Query'}
          </button>
        </div>
      </form>

      {results && (
        <div className="query-results">
          {results.error ? (
            <p className="error">{results.error}</p>
          ) : (
            <div>
              <div className="results-info">
                <p>Rows: {results.row_count}</p>
                <p>Execution time: {results.execution_time.toFixed(3)}s</p>
                {results.masked_columns?.length > 0 && (
                  <p>Masked columns: {results.masked_columns.join(', ')}</p>
                )}
                {results.runtime_detection_summary && (
                  <p className="runtime-summary">{results.runtime_detection_summary}</p>
                )}
              </div>
              <table>
                <thead>
                  <tr>
                    {results.columns.map(column => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {results.rows.map((row, index) => (
                    <tr key={index}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex}>{String(cell)}</td>
                      ))}
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

export default QueryEditor
