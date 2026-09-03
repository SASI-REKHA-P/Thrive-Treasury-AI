import { useState, useEffect } from 'react'
import { X, ShieldCheck, AlertTriangle, CheckCircle2, UserCheck, RefreshCw } from 'lucide-react'

export default function ControllerActionModal({
  transaction,
  action,
  actionLabel,
  onClose,
  onSubmit,
}) {
  const [actor, setActor] = useState('Lead Finance Controller')
  const [notes, setNotes] = useState(() => {
    if (action === 'APPROVE_ADVISORY') {
      return transaction.ai_investigation
        ? `Approved based on AI root cause analysis: ${transaction.ai_investigation.recommended_action}.`
        : 'Approved deterministic fee/tolerance variance.'
    }
    if (action === 'MANUAL_OVERRIDE') {
      return 'Manual controller sign-off after direct bank account ledger verification.'
    }
    if (action === 'ESCALATE_DISPUTE') {
      return 'Escalated to banking operations desk for clearing dispute inquiry.'
    }
    return ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, isSubmitting])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!actor.trim()) {
      setError('Actor identifier is required.')
      return
    }

    setIsSubmitting(true)
    setError(null)
    try {
      await onSubmit({
        action,
        actor: actor.trim(),
        notes: notes.trim(),
      })
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to record controller decision.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="drawer-backdrop" onClick={() => !isSubmitting && onClose()}>
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Confirm Controller Decision"
        style={{
          width: '100%',
          maxWidth: '520px',
          margin: 'auto',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-card)',
          borderRadius: '16px',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserCheck size={18} color="var(--brand-primary)" />
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              Confirm Controller Decision
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="drawer-close-btn"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {error && (
            <div className="error-alert-bar" role="alert">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Target Transaction Summary */}
          <div
            style={{
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              padding: '12px 16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              fontSize: '0.8125rem',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Target Order:</span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>{transaction.order_id}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Action:</span>
              <span className="badge badge-ai" style={{ fontWeight: 700 }}>
                {actionLabel}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Deterministic Rule:</span>
              <span className="badge badge-rule">{transaction.rule_id}</span>
            </div>
          </div>

          {/* Actor Input */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="actor-input" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Controller Identifier / Username *
            </label>
            <input
              id="actor-input"
              type="text"
              required
              className="search-input"
              style={{ paddingLeft: '12px' }}
              value={actor}
              onChange={(e) => setActor(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* Notes Textarea */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label htmlFor="notes-input" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Operational Rationale & Audit Notes
            </label>
            <textarea
              id="notes-input"
              rows={3}
              className="search-input"
              style={{ padding: '10px 12px', resize: 'vertical', minHeight: '75px' }}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          {/* Safety Notice */}
          <div
            style={{
              fontSize: '0.6875rem',
              color: 'var(--text-muted)',
              backgroundColor: 'rgba(99, 102, 241, 0.06)',
              borderLeft: '3px solid var(--brand-primary)',
              padding: '8px 12px',
              borderRadius: '4px',
              lineHeight: 1.4,
            }}
          >
            <ShieldCheck size={13} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
            This action commits an authoritative human decision to the immutable audit trail. Deterministic reconciliation amounts and original rule findings remain preserved.
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
                background: 'transparent',
                color: 'var(--text-primary)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-trigger-run"
              style={{ padding: '8px 18px', fontSize: '0.8125rem' }}
            >
              {isSubmitting ? (
                <>
                  <RefreshCw size={14} className="spin-icon" />
                  <span>Recording Decision...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={14} />
                  <span>Commit Controller Decision</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
