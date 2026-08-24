import React from 'react'
import { Shield, AlertCircle, Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

export function EditPolicyDialog({
  isOpen,
  onClose,
  editingPolicy,
  editStrategy,
  setEditStrategy,
  editSensitivity,
  setEditSensitivity,
  editDescription,
  setEditDescription,
  editVisibleChars,
  setEditVisibleChars,
  editBinSize,
  setEditBinSize,
  editTokenLength,
  setEditTokenLength,
  editNoiseLevel,
  setEditNoiseLevel,
  editHashAlgorithm,
  setEditHashAlgorithm,
  editError,
  setEditError,
  savingEdit,
  onSaveEdit,
}) {
  if (!editingPolicy) return null

  return (
    <Dialog open={isOpen} onOpenChange={(open) => { if (!open && !savingEdit) onClose(); }}>
      <DialogContent className="sm:max-w-[540px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold">Edit Masking Policy</DialogTitle>
          <DialogDescription className="text-xs">
            Modify masking strategy and runtime parameters for this database column.
          </DialogDescription>
        </DialogHeader>

        {/* Target Details Card */}
        <div className="rounded-lg border bg-muted/40 p-3 grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-muted-foreground text-[11px] uppercase tracking-wider block font-mono">
              Target Column
            </span>
            <div className="font-mono font-medium text-foreground mt-0.5">
              {editingPolicy.schema_name || 'public'}.{editingPolicy.table_name}.
              <strong className="text-primary">{editingPolicy.column_name}</strong>
            </div>
          </div>
          <div>
            <span className="text-muted-foreground text-[11px] uppercase tracking-wider block font-mono">
              Database Protection
            </span>
            <div className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium mt-0.5">
              <Shield className="h-3.5 w-3.5" />
              <span>DB-level masking active</span>
            </div>
          </div>
        </div>

        {/* Error Alert inside Modal */}
        {editError && (
          <Alert variant="destructive" className="py-2 text-xs">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">{editError}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={onSaveEdit} className="space-y-4 text-xs">
          {/* Strategy & Sensitivity Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label htmlFor="edit-strategy" className="font-medium text-foreground text-xs">
                Masking Strategy <span className="text-destructive">*</span>
              </label>
              <select
                id="edit-strategy"
                value={editStrategy}
                onChange={(e) => {
                  setEditStrategy(e.target.value)
                  setEditError(null)
                }}
                disabled={savingEdit}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring font-mono"
              >
                <optgroup label="Core Strategies">
                  <option value="EMAIL">EMAIL — Mask username, keep domain</option>
                  <option value="PHONE_LAST4">PHONE_LAST4 — Keep last 4 digits</option>
                  <option value="PARTIAL">PARTIAL — Preserve edge chars</option>
                  <option value="REDACT">REDACT — Full redaction</option>
                  <option value="DO_NOT_SHOW">DO_NOT_SHOW — Hide column</option>
                  <option value="NONE">NONE — Raw unmasked value</option>
                </optgroup>
                <optgroup label="Extended Strategies">
                  <option value="GENERALIZATION">GENERALIZATION — Range buckets</option>
                  <option value="TOKENIZATION">TOKENIZATION — Random token</option>
                  <option value="NOISE_ADDITION">NOISE_ADDITION — Percentage noise</option>
                  <option value="HASH">HASH — Deterministic hash</option>
                  <option value="SSN_MASK">SSN_MASK — Mask SSN</option>
                  <option value="CREDIT_CARD_MASK">CREDIT_CARD_MASK — Mask CC</option>
                  <option value="DATE_MASK">DATE_MASK — Preserve year</option>
                </optgroup>
              </select>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="edit-sensitivity" className="font-medium text-foreground text-xs">
                Sensitivity Level
              </label>
              <select
                id="edit-sensitivity"
                value={editSensitivity}
                onChange={(e) => setEditSensitivity(e.target.value)}
                disabled={savingEdit}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                <option value="HIGH">HIGH (Restricted / PII)</option>
                <option value="MEDIUM">MEDIUM (Internal)</option>
                <option value="LOW">LOW (General)</option>
              </select>
            </div>
          </div>

          {/* Strategy-Specific Parameters Box */}
          <div className="rounded-md border border-border/80 bg-muted/20 p-3 space-y-2">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block font-mono">
              Strategy Configuration
            </span>

            {/* PARTIAL */}
            {(editStrategy.toUpperCase() === 'PARTIAL' || editStrategy.toUpperCase() === 'PARTIAL_MASK') && (
              <div className="space-y-1">
                <label htmlFor="edit-vis-chars" className="font-medium text-xs">
                  Visible Edge Characters (<code>visible_chars</code>):
                </label>
                <Input
                  id="edit-vis-chars"
                  type="number"
                  min="1"
                  max="20"
                  value={editVisibleChars}
                  onChange={(e) => { setEditVisibleChars(e.target.value); setEditError(null); }}
                  disabled={savingEdit}
                  className="h-8 text-xs font-mono"
                />
                <p className="text-[11px] text-muted-foreground">
                  Preserves first and last {editVisibleChars || 2} characters (e.g. <code>jo***th</code>).
                </p>
              </div>
            )}

            {/* GENERALIZATION */}
            {editStrategy.toUpperCase() === 'GENERALIZATION' && (
              <div className="space-y-1">
                <label htmlFor="edit-bin-size" className="font-medium text-xs">
                  Bin Size Range (<code>bin_size</code>):
                </label>
                <Input
                  id="edit-bin-size"
                  type="number"
                  min="1"
                  step="any"
                  value={editBinSize}
                  onChange={(e) => { setEditBinSize(e.target.value); setEditError(null); }}
                  disabled={savingEdit}
                  className="h-8 text-xs font-mono"
                />
                <p className="text-[11px] text-muted-foreground">
                  Groups numeric values into bucket intervals (e.g. <code>5400</code> to <code>5000-6000</code>).
                </p>
              </div>
            )}

            {/* TOKENIZATION */}
            {editStrategy.toUpperCase() === 'TOKENIZATION' && (
              <div className="space-y-1">
                <label htmlFor="edit-tok-len" className="font-medium text-xs">
                  Token Length (<code>token_length</code>, 8-64):
                </label>
                <Input
                  id="edit-tok-len"
                  type="number"
                  min="8"
                  max="64"
                  value={editTokenLength}
                  onChange={(e) => { setEditTokenLength(e.target.value); setEditError(null); }}
                  disabled={savingEdit}
                  className="h-8 text-xs font-mono"
                />
                <p className="text-[11px] text-muted-foreground">
                  Generates random alphanumeric token of length {editTokenLength || 16}.
                </p>
              </div>
            )}

            {/* NOISE_ADDITION */}
            {editStrategy.toUpperCase() === 'NOISE_ADDITION' && (
              <div className="space-y-1">
                <label htmlFor="edit-noise-lvl" className="font-medium text-xs">
                  Noise Level (<code>noise_level</code>, 0.0 - 1.0):
                </label>
                <Input
                  id="edit-noise-lvl"
                  type="number"
                  min="0.0"
                  max="1.0"
                  step="0.01"
                  value={editNoiseLevel}
                  onChange={(e) => { setEditNoiseLevel(e.target.value); setEditError(null); }}
                  disabled={savingEdit}
                  className="h-8 text-xs font-mono"
                />
                <p className="text-[11px] text-muted-foreground">
                  Adds percentage noise variation (e.g. 0.1 represents ±10%).
                </p>
              </div>
            )}

            {/* HASH */}
            {editStrategy.toUpperCase() === 'HASH' && (
              <div className="space-y-1">
                <label htmlFor="edit-hash-algo" className="font-medium text-xs">
                  Hash Algorithm (<code>algorithm</code>):
                </label>
                <select
                  id="edit-hash-algo"
                  value={editHashAlgorithm}
                  onChange={(e) => setEditHashAlgorithm(e.target.value)}
                  disabled={savingEdit}
                  className="flex h-8 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm font-mono"
                >
                  <option value="sha256">SHA-256 (Default)</option>
                  <option value="md5">MD5 (Fast / PL/pgSQL)</option>
                  <option value="sha512">SHA-512 (High Security)</option>
                </select>
              </div>
            )}

            {/* Static notices for EMAIL, PHONE, REDACT, DO_NOT_SHOW, NONE */}
            {['EMAIL', 'EMAIL_MASK'].includes(editStrategy.toUpperCase()) && (
              <p className="text-muted-foreground text-[11px]">
                Preserves the first character of username and the domain (e.g. <code>j***@example.com</code>).
              </p>
            )}
            {['PHONE_LAST4', 'PHONE', 'LAST4'].includes(editStrategy.toUpperCase()) && (
              <p className="text-muted-foreground text-[11px]">
                Preserves the last 4 digits and masks preceding numbers (e.g. <code>***-***-1234</code>).
              </p>
            )}
            {['REDACT', 'REDACTION'].includes(editStrategy.toUpperCase()) && (
              <p className="text-muted-foreground text-[11px]">
                Full redaction with asterisks <code>***</code>.
              </p>
            )}
            {['DO_NOT_SHOW', 'HIDE'].includes(editStrategy.toUpperCase()) && (
              <p className="text-muted-foreground text-[11px]">
                Excludes the column completely from query output.
              </p>
            )}
            {['NONE', 'NO_MASK'].includes(editStrategy.toUpperCase()) && (
              <p className="text-muted-foreground text-[11px]">
                Returns raw unmasked PostgreSQL values.
              </p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label htmlFor="edit-desc" className="font-medium text-foreground text-xs">
              Security Rationale / Description
            </label>
            <Input
              id="edit-desc"
              type="text"
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="e.g. Mask patient email for privacy compliance"
              disabled={savingEdit}
              className="h-9 text-xs"
            />
          </div>

          {/* Informational Callout */}
          <div className="p-2.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-[11px] flex items-center gap-2">
            <Shield className="h-4 w-4 shrink-0" />
            <span>
              <strong>Database Protection:</strong> Saving this policy automatically updates its PostgreSQL DB-level masking function.
            </span>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              disabled={savingEdit}
              className="text-xs h-8"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={savingEdit}
              className="text-xs h-8 gap-1.5"
            >
              {savingEdit && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>{savingEdit ? 'Saving...' : 'Save Policy Changes'}</span>
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
