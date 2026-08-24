import React from 'react'
import { Plus, Shield, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function CreatePolicyDialog({
  isOpen,
  onOpenChange,
  availableSchemas,
  selectedSchema,
  onSchemaChange,
  availableTables,
  selectedTable,
  onTableChange,
  availableColumns,
  selectedColumn,
  setSelectedColumn,
  availableStrategies,
  selectedStrategy,
  setSelectedStrategy,
  selectedSensitivity,
  setSelectedSensitivity,
  policyDescription,
  setPolicyDescription,
  creatingPolicy,
  handleCreatePolicy,
  loadingSchemas,
  loadingTables,
  loadingColumns,
}) {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" className="h-8 gap-1.5 text-xs">
          <Plus className="h-3.5 w-3.5" />
          Create New Policy
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold">Define Custom Masking Policy</DialogTitle>
          <DialogDescription className="text-xs">
            Directly configure PostgreSQL column protection with deterministic masking strategies.
          </DialogDescription>
        </DialogHeader>

        {/* Database Protection Callout Banner */}
        <div className="p-2.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
          <Shield className="h-4 w-4 shrink-0" />
          <span>
            <strong>Database Protection:</strong> A PostgreSQL DB-level masking function will be automatically created and attached for this policy.
          </span>
        </div>

        <form onSubmit={handleCreatePolicy} className="space-y-3.5 text-xs">
          {/* Schema & Table Row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label htmlFor="create-schema-select" className="font-medium text-foreground text-xs">
                Schema
              </label>
              <select
                id="create-schema-select"
                value={selectedSchema}
                onChange={(e) => onSchemaChange(e.target.value)}
                disabled={loadingSchemas || creatingPolicy}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm font-mono"
              >
                {availableSchemas.map((sch) => (
                  <option key={sch} value={sch}>{sch}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="create-table-select" className="font-medium text-foreground text-xs">
                Table <span className="text-destructive">*</span>
              </label>
              <select
                id="create-table-select"
                value={selectedTable}
                onChange={(e) => onTableChange(e.target.value)}
                disabled={loadingTables || creatingPolicy}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm font-mono"
              >
                <option value="">[ Select table ]</option>
                {availableTables.map((tbl) => (
                  <option key={tbl} value={tbl}>{tbl}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Column & Strategy Row */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label htmlFor="create-column-select" className="font-medium text-foreground text-xs">
                Target Column <span className="text-destructive">*</span>
              </label>
              <select
                id="create-column-select"
                value={selectedColumn}
                onChange={(e) => setSelectedColumn(e.target.value)}
                disabled={!selectedTable || loadingColumns || creatingPolicy}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm font-mono disabled:opacity-50"
              >
                <option value="">
                  {loadingColumns
                    ? 'Loading columns...'
                    : !selectedTable
                    ? '[ Select table first ]'
                    : '[ Select column ]'}
                </option>
                {availableColumns.map((col) => {
                  const colName = typeof col === 'string' ? col : col.column_name
                  const colType = typeof col === 'object' && col.data_type ? ` (${col.data_type})` : ''
                  return (
                    <option key={colName} value={colName}>
                      {colName}{colType}
                    </option>
                  )
                })}
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="create-strategy-select" className="font-medium text-foreground text-xs">
                Masking Strategy <span className="text-destructive">*</span>
              </label>
              <select
                id="create-strategy-select"
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                disabled={creatingPolicy}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm font-mono"
              >
                {Object.keys(availableStrategies).length > 0 ? (
                  Object.entries(availableStrategies).map(([stratKey, desc]) => (
                    <option key={stratKey} value={stratKey}>
                      {stratKey} - {desc}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="EMAIL">EMAIL - Mask email address</option>
                    <option value="PHONE_LAST4">PHONE_LAST4 - Mask phone number</option>
                    <option value="PARTIAL">PARTIAL - Preserve edge characters</option>
                    <option value="REDACT">REDACT - Full redaction</option>
                    <option value="DO_NOT_SHOW">DO_NOT_SHOW - Exclude column</option>
                    <option value="NONE">NONE - Original unmasked</option>
                  </>
                )}
              </select>
            </div>
          </div>

          {/* Sensitivity & Description */}
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <label htmlFor="create-sensitivity-select" className="font-medium text-foreground text-xs">
                Sensitivity
              </label>
              <select
                id="create-sensitivity-select"
                value={selectedSensitivity}
                onChange={(e) => setSelectedSensitivity(e.target.value)}
                disabled={creatingPolicy}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm"
              >
                <option value="HIGH">HIGH (PII)</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>

            <div className="col-span-2 space-y-1.5">
              <label htmlFor="create-description-input" className="font-medium text-foreground text-xs">
                Description (Optional)
              </label>
              <Input
                id="create-description-input"
                type="text"
                value={policyDescription}
                onChange={(e) => setPolicyDescription(e.target.value)}
                placeholder="e.g. Mask patient email for dev queries"
                disabled={creatingPolicy}
                className="h-9 text-xs"
              />
            </div>
          </div>

          {/* DO_NOT_SHOW notice */}
          {selectedStrategy.toUpperCase() === 'DO_NOT_SHOW' && (
            <p className="text-[11px] text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 p-2 rounded border border-amber-500/20">
              <strong>DO_NOT_SHOW:</strong> This column will be hidden from developer query outputs.
            </p>
          )}

          <DialogFooter className="gap-2 sm:gap-0 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onOpenChange(false)}
              disabled={creatingPolicy}
              className="text-xs h-8"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              id="create-policy-btn"
              disabled={!selectedTable || !selectedColumn || !selectedStrategy || creatingPolicy}
              className="text-xs h-8 gap-1.5"
            >
              {creatingPolicy && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>{creatingPolicy ? 'Creating...' : 'Create Policy'}</span>
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
