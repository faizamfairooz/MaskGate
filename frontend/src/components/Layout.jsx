import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  ShieldCheck,
  LayoutDashboard,
  Database,
  Shield,
  Terminal,
  Activity,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import { healthAPI } from '@/services/api'
import { ThemeToggle } from '@/components/theme/ThemeToggle'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

function Layout({ children }) {
  const location = useLocation()
  const [dbHealthy, setDbHealthy] = useState(null)

  useEffect(() => {
    let isMounted = true
    healthAPI
      .checkDatabase()
      .then((res) => {
        if (isMounted) {
          setDbHealthy(res.data?.status === 'healthy')
        }
      })
      .catch(() => {
        if (isMounted) {
          setDbHealthy(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [location.pathname])

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/schema', label: 'Schema Browser', icon: Database },
    { path: '/masking', label: 'Masking Policies', icon: Shield },
    { path: '/query', label: 'Query Editor', icon: Terminal }
  ]

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col antialiased">
      {/* Top Console Navigation Bar */}
      <header className="sticky top-0 z-40 w-full border-b border-border/60 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
          {/* Brand Logo & Subtitle */}
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2.5 transition-opacity hover:opacity-90">
              <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center shadow-sm">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm tracking-tight">MaskGate</span>
                <span className="hidden sm:inline-flex text-[11px] font-mono text-muted-foreground border border-border px-1.5 py-0.5 rounded bg-muted/40">
                  PostgreSQL Security Gateway
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                      isActive
                        ? "bg-accent text-accent-foreground font-semibold shadow-xs"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    )}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
            </nav>
          </div>

          {/* Right Header: System Status & Theme Toggle */}
          <div className="flex items-center gap-3">
            {/* DB Health Pill */}
            <div className="flex items-center">
              {dbHealthy === true ? (
                <Badge
                  variant="outline"
                  className="gap-1.5 text-[11px] font-normal py-0.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  PostgreSQL Connected
                </Badge>
              ) : dbHealthy === false ? (
                <Badge
                  variant="outline"
                  className="gap-1.5 text-[11px] font-normal py-0.5 border-destructive/30 bg-destructive/10 text-destructive"
                >
                  <AlertCircle className="h-3 w-3" />
                  Database Offline
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1.5 text-[11px] font-normal py-0.5 text-muted-foreground">
                  <Activity className="h-3 w-3 animate-spin" />
                  Checking DB...
                </Badge>
              )}
            </div>

            <div className="h-4 w-px bg-border" />

            <ThemeToggle />
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="md:hidden flex items-center justify-around border-t border-border px-2 py-1.5 bg-muted/20">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex flex-col items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium transition-colors",
                  isActive
                    ? "text-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </header>

      {/* Main App Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>

      {/* Footer / Console Sub-Bar */}
      <footer className="border-t border-border/60 py-3 bg-muted/20 text-muted-foreground text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-mono font-medium">MaskGate v1.0</span>
            <span>•</span>
            <span>GenAI-Assisted PostgreSQL Dynamic Data Masking Gateway</span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-3 w-3" /> Two-Stage Masking Active
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
