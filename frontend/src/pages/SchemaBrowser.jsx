import React, { useState, useEffect } from 'react'
import { schemaAPI } from '../services/api'

function SchemaBrowser() {
  const [tables, setTables] = useState([])
  const [selectedTable, setSelectedTable] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchTables()
  }, [])

  const fetchTables = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await schemaAPI.getTables()
      setTables(response.data)
    } catch (error) {
      console.error('Failed to fetch tables:', error)
      setError('Failed to load tables. Please check database connection.')
    } finally {
      setLoading(false)
    }
  }

  const fetchTableSchema = async (tableName) => {
    setError(null)
    try {
      const response = await schemaAPI.getTableSchema(tableName)
      setSelectedTable(response.data)
    } catch (error) {
      console.error('Failed to fetch table schema:', error)
      setError('Failed to load table schema.')
    }
  }

  return (
    <div className="schema-browser">
      <h2>PostgreSQL Schema Browser</h2>
      {error && <div className="error-message">{error}</div>}
      <div className="schema-content">
        <div className="tables-list">
          <h3>Tables</h3>
          {loading ? (
            <p>Loading...</p>
          ) : (
            <ul>
              {tables.map(table => (
                <li
                  key={table}
                  onClick={() => fetchTableSchema(table)}
                  className={selectedTable?.table_name === table ? 'active' : ''}
                >
                  {table}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="table-details">
          {selectedTable ? (
            <div>
              <h3>{selectedTable.table_name}</h3>
              
              {selectedTable.primary_keys.length > 0 && (
                <div className="keys-section">
                  <strong>Primary Keys:</strong> {selectedTable.primary_keys.join(', ')}
                </div>
              )}
              
              {selectedTable.foreign_keys.length > 0 && (
                <div className="keys-section">
                  <strong>Foreign Keys:</strong>
                  <ul className="foreign-keys-list">
                    {selectedTable.foreign_keys.map((fk, index) => (
                      <li key={index}>
                        {fk.column_name} → {fk.foreign_table_name}.{fk.foreign_column_name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              <table className="schema-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Nullable</th>
                    <th>Max Length</th>
                    <th>Default</th>
                    <th>Primary Key</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedTable.columns.map(column => (
                    <tr key={column.column_name}>
                      <td className="column-name">{column.column_name}</td>
                      <td className="data-type">{column.data_type}</td>
                      <td>{column.is_nullable ? 'Yes' : 'No'}</td>
                      <td>{column.character_maximum_length || '-'}</td>
                      <td>{column.column_default || '-'}</td>
                      <td>{column.is_primary_key ? '✓' : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>Select a table to view its schema</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default SchemaBrowser
