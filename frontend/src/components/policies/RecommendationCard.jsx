import React from 'react'
import { Check, X, Shield, Sparkles, Brain, Table2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function RecommendationCard({
  rec,
  onApprove,
  onReject,
  isActioning,
  getStrategyBadgeVariant,
  getSensitivityBadgeVariant
}) {
  const isPending = rec.status?.toUpperCase() === 'PENDING'
  const isApproved = rec.status?.toUpperCase() === 'APPROVED'
  const isRejected = rec.status?.toUpperCase() === 'REJECTED'

  const statusBorderClass = isPending
    ? 'border-l-4 border-l-amber-500'
    : isApproved
    ? 'border-l-4 border-l-emerald-500'
    : 'border-l-4 border-l-rose-500'

  return (
    <Card className={`flex flex-col justify-between border-border/80 hover:border-border transition-shadow shadow-xs ${statusBorderClass}`}>
      <CardHeader className="p-4 pb-3 space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1">
            <span className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
              Target Column
            </span>
            <div className="font-mono text-sm font-semibold flex items-center gap-1.5 text-foreground">
              <span>{rec.table_name}</span>
              <span className="text-muted-foreground">.</span>
              <span className="text-primary font-bold">{rec.column_name}</span>
            </div>
          </div>

          <div>
            {isPending && (
              <Badge variant="warning" className="text-[11px]">
                Pending Review
              </Badge>
            )}
            {isApproved && (
              <Badge variant="success" className="text-[11px]">
                Approved
              </Badge>
            )}
            {isRejected && (
              <Badge variant="destructive" className="text-[11px]">
                Rejected
              </Badge>
            )}
          </div>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 p-2.5 rounded-md bg-muted/40 border border-border/50 text-xs">
          <div>
            <span className="text-muted-foreground text-[11px] block">Detected Type:</span>
            <code className="font-mono text-xs font-medium text-foreground">
              {rec.data_type || 'text'}
            </code>
          </div>
          <div>
            <span className="text-muted-foreground text-[11px] block">Sensitivity:</span>
            <Badge variant={getSensitivityBadgeVariant(rec.sensitivity)} className="text-[10px] h-4.5 px-1.5 mt-0.5">
              {rec.sensitivity || 'MEDIUM'}
            </Badge>
          </div>
          <div>
            <span className="text-muted-foreground text-[11px] block">Confidence:</span>
            <span className="font-medium text-foreground text-[11px]">
              {rec.confidence || 'HIGH'}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground text-[11px] block">Source:</span>
            <span className="font-mono text-muted-foreground text-[11px] flex items-center gap-1">
              <Brain className="h-3 w-3 text-primary/70" />
              {rec.source || 'llm'}
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 pt-0 space-y-3">
        {/* Recommended Strategy */}
        <div className="space-y-1">
          <span className="text-[11px] font-medium text-muted-foreground block">
            Recommended Strategy:
          </span>
          <div className="flex items-center gap-2">
            <Badge variant={getStrategyBadgeVariant(rec.recommended_strategy)} className="font-mono text-xs">
              {rec.recommended_strategy}
            </Badge>
          </div>
        </div>

        {/* Rationale */}
        <div className="text-xs text-muted-foreground bg-muted/20 p-2 rounded border border-border/40 leading-relaxed">
          <span className="font-semibold text-foreground">Rationale: </span>
          {rec.rationale || 'Identified potential sensitive identifier via LLM schema analysis.'}
        </div>

        {/* Database Protection Indicator */}
        <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground font-mono pt-1">
          <Shield className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>PostgreSQL DB-level masking</span>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 border-t border-border flex items-center justify-end gap-2">
          {isPending ? (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onReject(rec.id, rec.table_name, rec.column_name)}
                disabled={Boolean(isActioning)}
                className="h-8 text-destructive border-destructive/30 hover:bg-destructive/10 hover:text-destructive text-xs gap-1"
              >
                <X className="h-3.5 w-3.5" />
                {isActioning === 'rejecting' ? 'Rejecting...' : 'Reject'}
              </Button>
              <Button
                type="button"
                variant="success"
                size="sm"
                onClick={() => onApprove(rec.id, rec.table_name, rec.column_name)}
                disabled={Boolean(isActioning)}
                className="h-8 text-xs gap-1 shadow-xs"
              >
                <Check className="h-3.5 w-3.5" />
                {isActioning === 'approving' ? 'Approving...' : 'Approve'}
              </Button>
            </>
          ) : isApproved ? (
            <Badge variant="success" className="text-[11px] py-0.5 gap-1 font-normal">
              <Shield className="h-3 w-3" />
              DB-level masking: Automatically applied
            </Badge>
          ) : (
            <Badge variant="destructive" className="text-[11px] py-0.5 font-normal">
              Rejected by Administrator
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
