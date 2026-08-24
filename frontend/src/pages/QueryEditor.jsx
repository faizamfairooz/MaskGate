import React, { useState } from 'react'
import {
  Terminal,
  Play,
  Copy,
  Check,
  ShieldCheck,
  Sparkles,
  AlertCircle,
  Database,
  ArrowRight,
  Clock,
  Rows,
  Layers,
  FileCode2,
  Lock
} from 'lucide-react'
import { queryAPI } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

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
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Terminal className="h-5 w-5 text-primary" />
            SQL Query Workbench
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Execute read-only SQL queries against PostgreSQL protected by database-level masking and runtime detection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs font-mono py-1 px-2.5 gap-1.5 border-emerald-500/30 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="h-3.5 w-3.5" />
            Application-Controlled Security
          </Badge>
        </div>
      </div>

      {/* Two-Stage Execution & Masking Pipeline Diagram */}
      <div className="rounded-lg border border-border/80 bg-muted/20 p-3.5 space-y-2 text-xs">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="font-semibold text-foreground text-xs uppercase tracking-wider font-mono">
            Two-Stage Execution & Masking Architecture
          </span>
          <span className="text-[11px] text-muted-foreground">
            Strictly read-only SELECT • Stage 1 DB-Level Masking • Stage 2 Runtime AI Detection
          </span>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto py-1 font-mono text-[11px]">
          <div className="bg-background border px-2.5 py-1 rounded shadow-2xs font-medium whitespace-nowrap text-foreground flex items-center gap-1.5">
            <FileCode2 className="h-3 w-3 text-muted-foreground" />
            1. User SQL
          </div>
          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
          <div className="bg-background border px-2.5 py-1 rounded shadow-2xs font-medium whitespace-nowrap text-foreground flex items-center gap-1.5">
            <Lock className="h-3 w-3 text-amber-500" />
            2. Policy & Limit Hardening
          </div>
          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
          <div className="bg-purple-500/10 border border-purple-500/20 text-purple-700 dark:text-purple-300 px-2.5 py-1 rounded font-medium whitespace-nowrap flex items-center gap-1.5">
            <Database className="h-3 w-3" />
            3. PostgreSQL Execute
          </div>
          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 px-2.5 py-1 rounded font-semibold whitespace-nowrap flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5" />
            4. Stage 1: DB-Level Masking
          </div>
          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
          <div className="bg-amber-500/10 border border-amber-500/20 text-amber-700 dark:text-amber-300 px-2.5 py-1 rounded font-medium whitespace-nowrap flex items-center gap-1.5">
            <Sparkles className="h-3 w-3" />
            5. Stage 2: Runtime AI Detection
          </div>
          <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
          <div className="bg-background border px-2.5 py-1 rounded shadow-2xs font-semibold whitespace-nowrap text-foreground">
            6. Protected Results
          </div>
        </div>
      </div>

      {/* Main SQL Editor Card */}
      <Card className="shadow-xs overflow-hidden border-border/80">
        {/* Editor Toolbar & Sample Query Presets */}
        <div className="p-2.5 px-4 bg-muted/40 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-medium text-muted-foreground text-xs mr-1">Quick Templates:</span>
            {SAMPLE_QUERIES.map((preset, idx) => (
              <Button
                key={idx}
                type="button"
                variant={query === preset.query ? "secondary" : "outline"}
                size="sm"
                onClick={() => setQuery(preset.query)}
                title={preset.description}
                className="h-7 text-[11px] font-mono px-2"
              >
                {preset.name}
              </Button>
            ))}
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleCopyQuery}
            className="h-7 text-xs text-muted-foreground hover:text-foreground gap-1 self-end sm:self-auto"
          >
            {copiedQuery ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
            <span>{copiedQuery ? 'Copied' : 'Copy SQL'}</span>
          </Button>
        </div>

        {/* Textarea Code Box */}
        <form onSubmit={executeQuery}>
          <div className="p-0">
            <textarea
              id="sql-query-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your SQL SELECT query here..."
              rows={7}
              spellCheck={false}
              className="w-full p-4 font-mono text-sm bg-background text-foreground resize-y outline-none border-0 focus:ring-0 leading-relaxed"
            />
          </div>

          {/* Masking Controls & Run Query Bar */}
          <div className="p-3 px-4 bg-muted/30 border-t flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
            <div className="space-y-2">
              {/* Option 1: Apply Approved Masking Policies */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <Checkbox
                  id="toggle-apply-masking"
                  checked={applyMasking}
                  onCheckedChange={(checked) => setApplyMasking(Boolean(checked))}
                />
                <span className="font-medium text-foreground">Stage 1: Apply Approved Masking Policies</span>
                <Badge variant="success" className="text-[10px] py-0 px-1.5 h-4.5 font-normal">
                  DB-Level Masking
                </Badge>
              </label>

              {/* Option 2: Detect Suspicious Sensitive Data */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <Checkbox
                  id="toggle-mask-suspicious"
                  checked={maskSuspicious}
                  onCheckedChange={(checked) => setMaskSuspicious(Boolean(checked))}
                />
                <span className="font-medium text-foreground">Stage 2: Detect Suspicious Sensitive Data</span>
                <Badge variant="warning" className="text-[10px] py-0 px-1.5 h-4.5 font-normal">
                  Runtime AI
                </Badge>
              </label>
            </div>

            <Button
              type="submit"
              id="execute-query-btn"
              disabled={loading || !query.trim()}
              className="h-9 px-5 gap-2 text-xs font-semibold shadow-xs shrink-0"
            >
              {loading ? (
                <>
                  <span className="h-3.5 w-3.5 rounded-full border-2 border-primary-foreground border-t-transparent animate-spin" />
                  <span>Executing Query...</span>
                </>
              ) : (
                <>
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Run Query</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>

      {/* Query Results Viewport */}
      {results && (
        <div className="space-y-4">
          {results.error ? (
            /* Error Card */
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle className="text-sm font-semibold">Query Execution Error</AlertTitle>
              <AlertDescription className="text-xs space-y-1 mt-1">
                <p className="font-mono">{results.error}</p>
                <p className="text-[11px] opacity-80">
                  Tip: Ensure your query is a valid read-only SELECT statement with accessible PostgreSQL tables.
                </p>
              </AlertDescription>
            </Alert>
          ) : (
            /* Results Panel */
            <Card className="overflow-hidden shadow-xs border-border/80">
              {/* Results Metric Header */}
              <div className="p-3 px-4 bg-muted/40 border-b flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant="outline" className="font-mono text-[11px] gap-1 bg-background">
                    <Rows className="h-3 w-3 text-muted-foreground" />
                    {results.row_count} rows
                  </Badge>

                  <Badge variant="outline" className="font-mono text-[11px] gap-1 bg-background">
                    <Clock className="h-3 w-3 text-muted-foreground" />
                    {(results.execution_time * 1000).toFixed(1)} ms
                  </Badge>

                  {results.masked_columns && results.masked_columns.length > 0 ? (
                    <Badge variant="success" className="font-mono text-[11px] gap-1">
                      <ShieldCheck className="h-3 w-3" />
                      {results.masked_columns.length} column(s) masked ({results.masked_columns.join(', ')})
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="font-mono text-[11px]">
                      No columns masked
                    </Badge>
                  )}

                  {!hasOuterLimit(query) && (
                    <Badge variant="outline" className="text-[11px] border-blue-500/30 text-blue-600 dark:text-blue-400 bg-blue-500/5">
                      Safe Default LIMIT (100)
                    </Badge>
                  )}
                </div>

                {results.runtime_detection_summary && (
                  <Badge variant="warning" className="text-[11px] gap-1">
                    <Sparkles className="h-3 w-3" />
                    Runtime Detection: {results.runtime_detection_summary}
                  </Badge>
                )}
              </div>

              {/* Data Table */}
              {results.rows.length === 0 ? (
                <div className="p-12 text-center space-y-1">
                  <div className="text-sm font-medium text-foreground">No rows returned</div>
                  <div className="text-xs text-muted-foreground">The query executed successfully but produced zero matching rows.</div>
                </div>
              ) : (
                <div className="max-h-[520px] overflow-auto">
                  <Table>
                    <TableHeader className="sticky top-0 bg-muted/90 backdrop-blur z-10">
                      <TableRow className="hover:bg-transparent border-b">
                        {results.columns.map((column) => {
                          const isMasked = results.masked_columns && results.masked_columns.includes(column)
                          return (
                            <TableHead
                              key={column}
                              className={`font-mono text-xs ${isMasked ? 'text-emerald-700 dark:text-emerald-300 bg-emerald-500/15 font-semibold' : 'text-foreground'}`}
                            >
                              <div className="flex items-center gap-1.5">
                                <span>{column}</span>
                                {isMasked && (
                                  <Badge variant="success" className="text-[10px] h-4 px-1.5 font-mono uppercase tracking-wider font-bold">
                                    masked
                                  </Badge>
                                )}
                              </div>
                            </TableHead>
                          )
                        })}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.rows.map((row, rowIndex) => (
                        <TableRow key={rowIndex} className="text-xs hover:bg-muted/30">
                          {row.map((cell, cellIndex) => {
                            const colName = results.columns[cellIndex]
                            const isMasked = results.masked_columns && results.masked_columns.includes(colName)
                            return (
                              <TableCell
                                key={cellIndex}
                                className={`font-mono text-xs whitespace-nowrap ${isMasked ? 'bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-200 font-semibold' : ''}`}
                              >
                                {cell === null ? (
                                  <span className="text-muted-foreground/60 italic font-sans text-[11px]">NULL</span>
                                ) : (
                                  String(cell)
                                )}
                              </TableCell>
                            )
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

export default QueryEditor
