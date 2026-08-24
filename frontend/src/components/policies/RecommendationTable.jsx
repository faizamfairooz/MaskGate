import React from 'react'
import { Check, X, Shield, Brain } from 'lucide-react'
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

export function RecommendationTable({
  recommendations,
  onApprove,
  onReject,
  actionLoading,
  getStrategyBadgeVariant,
  getSensitivityBadgeVariant,
}) {
  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[140px] font-mono text-xs">Table</TableHead>
            <TableHead className="w-[140px] font-mono text-xs">Column</TableHead>
            <TableHead className="w-[110px] text-xs">Type</TableHead>
            <TableHead className="w-[110px] text-xs">Sensitivity</TableHead>
            <TableHead className="w-[140px] text-xs">Strategy</TableHead>
            <TableHead className="text-xs min-w-[200px]">Rationale</TableHead>
            <TableHead className="w-[110px] text-xs">Status</TableHead>
            <TableHead className="w-[180px] text-right text-xs">Admin Decision</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {recommendations.map((rec) => {
            const isPending = rec.status?.toUpperCase() === 'PENDING'
            const isApproved = rec.status?.toUpperCase() === 'APPROVED'
            const isRejected = rec.status?.toUpperCase() === 'REJECTED'
            const isActioning = actionLoading[rec.id]

            return (
              <TableRow key={rec.id} className="text-xs">
                <TableCell className="font-mono font-medium text-foreground">
                  {rec.table_name}
                </TableCell>
                <TableCell className="font-mono font-semibold text-primary">
                  {rec.column_name}
                </TableCell>
                <TableCell>
                  <code className="font-mono text-[11px] text-muted-foreground bg-muted/60 px-1.5 py-0.5 rounded">
                    {rec.data_type || 'text'}
                  </code>
                </TableCell>
                <TableCell>
                  <Badge variant={getSensitivityBadgeVariant(rec.sensitivity)} className="text-[10px]">
                    {rec.sensitivity || 'MEDIUM'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={getStrategyBadgeVariant(rec.recommended_strategy)} className="font-mono text-[11px]">
                    {rec.recommended_strategy}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground text-xs leading-relaxed max-w-xs truncate" title={rec.rationale}>
                  {rec.rationale || '—'}
                </TableCell>
                <TableCell>
                  {isPending ? (
                    <Badge variant="warning" className="text-[10px]">Pending</Badge>
                  ) : isApproved ? (
                    <Badge variant="success" className="text-[10px]">Approved</Badge>
                  ) : (
                    <Badge variant="destructive" className="text-[10px]">Rejected</Badge>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  {isPending ? (
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onReject(rec.id, rec.table_name, rec.column_name)}
                        disabled={Boolean(isActioning)}
                        className="h-7 px-2 text-xs text-destructive border-destructive/30 hover:bg-destructive/10"
                      >
                        <X className="h-3 w-3 mr-1" />
                        {isActioning === 'rejecting' ? '...' : 'Reject'}
                      </Button>
                      <Button
                        type="button"
                        variant="success"
                        size="sm"
                        onClick={() => onApprove(rec.id, rec.table_name, rec.column_name)}
                        disabled={Boolean(isActioning)}
                        className="h-7 px-2 text-xs"
                      >
                        <Check className="h-3 w-3 mr-1" />
                        {isActioning === 'approving' ? '...' : 'Approve'}
                      </Button>
                    </div>
                  ) : isApproved ? (
                    <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium text-[11px]">
                      <Shield className="h-3 w-3" /> DB Masking Active
                    </span>
                  ) : (
                    <span className="text-muted-foreground text-[11px]">
                      Excluded
                    </span>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
