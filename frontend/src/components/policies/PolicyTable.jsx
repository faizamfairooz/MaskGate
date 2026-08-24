import React from 'react'
import { ShieldCheck, Edit, Trash2, Shield } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function PolicyTable({
  policies,
  onOpenEdit,
  onDeletePolicy,
  getStrategyBadgeVariant,
  getSensitivityBadgeVariant,
  formatPolicyParameters,
}) {
  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="text-xs font-mono">Policy Target</TableHead>
            <TableHead className="text-xs font-mono">Schema</TableHead>
            <TableHead className="text-xs">Strategy</TableHead>
            <TableHead className="text-xs">Parameters</TableHead>
            <TableHead className="text-xs">Sensitivity</TableHead>
            <TableHead className="text-xs">Database Protection</TableHead>
            <TableHead className="text-xs">Status</TableHead>
            <TableHead className="text-xs">Source</TableHead>
            <TableHead className="text-right text-xs">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {policies.map((policy) => {
            const paramsFormatted = formatPolicyParameters(policy)
            return (
              <TableRow key={policy.id} className="text-xs">
                <TableCell className="font-mono">
                  <div className="font-semibold text-foreground">
                    {policy.table_name}.<span className="text-primary">{policy.column_name}</span>
                  </div>
                  {policy.description && policy.description !== policy.name && (
                    <div className="text-[11px] text-muted-foreground font-sans truncate max-w-xs mt-0.5" title={policy.description}>
                      {policy.description}
                    </div>
                  )}
                </TableCell>
                <TableCell className="font-mono text-muted-foreground">
                  {policy.schema_name || 'public'}
                </TableCell>
                <TableCell>
                  <Badge variant={getStrategyBadgeVariant(policy.strategy)} className="font-mono text-[11px]">
                    {policy.strategy}
                  </Badge>
                </TableCell>
                <TableCell>
                  {paramsFormatted ? (
                    <code className="font-mono text-[11px] bg-muted/60 text-muted-foreground px-1.5 py-0.5 rounded border border-border/40">
                      {paramsFormatted}
                    </code>
                  ) : (
                    <span className="text-muted-foreground/60">—</span>
                  )}
                </TableCell>
                <TableCell>
                  <Badge variant={getSensitivityBadgeVariant(policy.sensitivity)} className="text-[10px]">
                    {policy.sensitivity || 'MEDIUM'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="success" className="text-[10px] gap-1 font-normal py-0.5">
                    <ShieldCheck className="h-3 w-3" />
                    Automatically applied
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-[10px] font-mono border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                    {policy.status || 'ACTIVE'}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-[11px] font-mono">
                  {policy.source || 'ai_recommendation'}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onOpenEdit(policy)}
                      className="h-7 px-2 text-xs gap-1"
                    >
                      <Edit className="h-3 w-3" />
                      Edit
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onDeletePolicy(policy.id, policy.name)}
                      className="h-7 px-2 text-xs text-destructive border-destructive/30 hover:bg-destructive/10 gap-1"
                    >
                      <Trash2 className="h-3 w-3" />
                      Deactivate
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
