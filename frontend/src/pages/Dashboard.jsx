import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldCheck,
  Database,
  Terminal,
  Shield,
  Layers,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Activity,
  Table2,
  Lock,
  ArrowUpRight
} from 'lucide-react'
import { healthAPI, schemaAPI, maskingAPI } from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

function Dashboard() {
  const [dbStatus, setDbStatus] = useState('Checking...')
  const [tableCount, setTableCount] = useState('—')
  const [policyCount, setPolicyCount] = useState('—')

  useEffect(() => {
    healthAPI.checkDatabase()
      .then((res) => setDbStatus(res.data.status === 'healthy' ? 'Connected' : 'Unavailable'))
      .catch(() => setDbStatus('Unavailable'))

    schemaAPI.getTables()
      .then((res) => setTableCount(String(res.data.length)))
      .catch(() => setTableCount('—'))

    maskingAPI.getPolicies()
      .then((res) => setPolicyCount(String(res.data.length)))
      .catch(() => setPolicyCount('—'))
  }, [])

  const isDbConnected = dbStatus === 'Connected'
  const numericPolicyCount = parseInt(policyCount, 10)
  const isProtectionActive = isDbConnected && !isNaN(numericPolicyCount) && numericPolicyCount > 0

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Security Overview
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            PostgreSQL dynamic data masking console and AI-assisted sensitive schema protection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isDbConnected ? (
            <Badge variant="success" className="text-xs font-mono py-1 px-2.5 gap-1.5 font-normal">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              PostgreSQL Online
            </Badge>
          ) : (
            <Badge variant="destructive" className="text-xs font-mono py-1 px-2.5 gap-1.5 font-normal">
              <AlertCircle className="h-3.5 w-3.5" />
              PostgreSQL Offline
            </Badge>
          )}
        </div>
      </div>

      {/* KPI Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Card 1: Database Status */}
        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Database Status</span>
            <Database className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="my-2">
            <div className={`text-2xl font-bold font-mono ${isDbConnected ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'} flex items-center gap-2`}>
              {dbStatus}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">PostgreSQL backend connection</p>
          </div>
          <div className="pt-2 border-t text-[11px]">
            {isDbConnected ? (
              <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Ready for query execution
              </span>
            ) : (
              <span className="text-rose-600 dark:text-rose-400 font-medium flex items-center gap-1">
                <AlertCircle className="h-3 w-3" /> Check database connection
              </span>
            )}
          </div>
        </Card>

        {/* Card 2: Database Protection */}
        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Database Protection</span>
            <Shield className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="my-2">
            <div className={`text-2xl font-bold font-mono ${isProtectionActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-foreground'}`}>
              {isProtectionActive ? 'Active' : isDbConnected ? 'Ready' : 'Unavailable'}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {isProtectionActive ? 'DB-level masking enforced' : 'No active policies'}
            </p>
          </div>
          <div className="pt-2 border-t text-[11px]">
            <span className="text-muted-foreground">
              {isProtectionActive ? 'Automated PostgreSQL wrapper' : 'Awaiting policy creation'}
            </span>
          </div>
        </Card>

        {/* Card 3: Active Policies */}
        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Active Policies</span>
            <Lock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="my-2">
            <div className="text-2xl font-bold font-mono text-blue-600 dark:text-blue-400">
              {policyCount}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Enforced masking rules</p>
          </div>
          <div className="pt-2 border-t text-[11px] flex items-center justify-between">
            <span className="text-muted-foreground">Protected columns</span>
            <Link to="/masking" className="text-primary hover:underline font-medium flex items-center gap-0.5">
              Manage <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>

        {/* Card 4: Monitored Tables */}
        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Monitored Tables</span>
            <Table2 className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="my-2">
            <div className="text-2xl font-bold font-mono text-foreground">
              {tableCount}
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5">Database tables in schema</p>
          </div>
          <div className="pt-2 border-t text-[11px] flex items-center justify-between">
            <span className="text-muted-foreground">public schema</span>
            <Link to="/schema" className="text-primary hover:underline font-medium flex items-center gap-0.5">
              Explore <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </Card>
      </div>

      {/* Security Architecture & Masking Pipeline Card */}
      <Card className="shadow-xs border-border/80">
        <CardHeader className="p-4 pb-3">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" />
            MaskGate End-to-End Security Architecture
          </CardTitle>
          <CardDescription className="text-xs">
            How PostgreSQL metadata is analyzed by GenAI and protected by automatic DB-level masking before query returns.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2.5 font-mono text-xs">
            {/* Step 1 */}
            <div className="p-3 rounded-lg border bg-muted/20 space-y-1">
              <div className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
                <Database className="h-3 w-3" /> Step 1
              </div>
              <div className="font-semibold text-foreground text-xs">PostgreSQL Schema</div>
              <p className="text-[11px] text-muted-foreground font-sans">
                Metadata extracted: tables, columns, data types, PK/FK.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5 space-y-1">
              <div className="text-[10px] uppercase font-bold text-blue-700 dark:text-blue-300 flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Step 2
              </div>
              <div className="font-semibold text-blue-900 dark:text-blue-200 text-xs">GenAI Analysis</div>
              <p className="text-[11px] text-muted-foreground font-sans">
                LLM recommends sensitive columns and masking strategies.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5 space-y-1">
              <div className="text-[10px] uppercase font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1">
                <Shield className="h-3 w-3" /> Step 3
              </div>
              <div className="font-semibold text-amber-900 dark:text-amber-200 text-xs">Admin Review</div>
              <p className="text-[11px] text-muted-foreground font-sans">
                Administrator explicitly reviews and approves/rejects policies.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 space-y-1">
              <div className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                <ShieldCheck className="h-3 w-3" /> Step 4
              </div>
              <div className="font-semibold text-emerald-900 dark:text-emerald-200 text-xs">DB-Level Masking</div>
              <p className="text-[11px] text-muted-foreground font-sans">
                PostgreSQL masking functions automatically applied behind the scenes.
              </p>
            </div>

            {/* Step 5 */}
            <div className="p-3 rounded-lg border bg-muted/20 space-y-1">
              <div className="text-[10px] uppercase font-bold text-muted-foreground flex items-center gap-1">
                <Terminal className="h-3 w-3" /> Step 5
              </div>
              <div className="font-semibold text-foreground text-xs">Protected Queries</div>
              <p className="text-[11px] text-muted-foreground font-sans">
                Developer executes SQL with deterministic masking & AI runtime detection.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Action Hub */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between hover:border-primary/50 transition-colors">
          <div className="space-y-1.5">
            <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-primary">
              <Shield className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm text-foreground">Masking Policies</h3>
            <p className="text-xs text-muted-foreground">
              Review AI recommendations, approve new rules, or manage active database protection.
            </p>
          </div>
          <div className="pt-3 mt-2">
            <Button asChild size="sm" variant="outline" className="w-full text-xs h-8 justify-between">
              <Link to="/masking">
                <span>Manage Policies</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </Card>

        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between hover:border-primary/50 transition-colors">
          <div className="space-y-1.5">
            <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-primary">
              <Terminal className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm text-foreground">SQL Query Workbench</h3>
            <p className="text-xs text-muted-foreground">
              Execute read-only queries with two-stage masking and inspect live protected results.
            </p>
          </div>
          <div className="pt-3 mt-2">
            <Button asChild size="sm" variant="outline" className="w-full text-xs h-8 justify-between">
              <Link to="/query">
                <span>Open Workbench</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </Card>

        <Card className="p-4 shadow-xs border-border/80 flex flex-col justify-between hover:border-primary/50 transition-colors">
          <div className="space-y-1.5">
            <div className="h-8 w-8 rounded-md bg-muted flex items-center justify-center text-primary">
              <Database className="h-4 w-4" />
            </div>
            <h3 className="font-semibold text-sm text-foreground">Schema Browser</h3>
            <p className="text-xs text-muted-foreground">
              Inspect PostgreSQL schemas, table definitions, primary keys, and foreign key relations.
            </p>
          </div>
          <div className="pt-3 mt-2">
            <Button asChild size="sm" variant="outline" className="w-full text-xs h-8 justify-between">
              <Link to="/schema">
                <span>Explore Schema</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
