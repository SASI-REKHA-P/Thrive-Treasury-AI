import { useState, useEffect } from 'react'
import {
  X,
  CheckCircle2,
  AlertOctagon,
  Clock,
  ShieldAlert,
  Cpu,
  UserCheck,
  AlertTriangle,
  ArrowRight,
  Download,
  RefreshCw,
} from 'lucide-react'
import AIBriefCard from './AIBriefCard'
import ControllerActionModal from './ControllerActionModal'
import { downloadSingleCaseDispute } from '../../api/client'

export default function TransactionDrawer({
  transaction,
  onClose,
  onSubmitDecision,
}) {
  const [selectedAction, setSelectedAction] = useState(null)
  const [isExportingCase, setIsExportingCase] = useState(false)
  const [exportError, setExportError] = useState(null)


  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !selectedAction) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, selectedAction])

  if (!transaction) return null

  const diffNum = Number(transaction.difference) || 0
  const isReviewRequired = transaction.human_review_status === 'REVIEW_REQUIRED'
  const isResolved = transaction.human_review_status === 'RESOLVED'
  const isEscalated = transaction.human_review_status === 'ESCALATED'

  const primaryLabel = transaction.ai_investigation
    ? 'Approve AI Recommendation'
    : 'Sign-off / Resolve Review'

  return (
    <div className="drawer-backdrop" onClick={() => !selectedAction && onClose()}>
      <div
        className="drawer-panel"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={`Details for transaction ${transaction.order_id}`}
      >
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-header-left">
            <span className="drawer-order-id">{transaction.order_id}</span>
            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
              {transaction.status === 'MATCHED' && (
                <span className="badge badge-matched">
                  <CheckCircle2 size={11} /> Matched
                </span>
              )}
              {transaction.status === 'EXCEPTION' && (
                <span className="badge badge-exception">
                  <AlertOctagon size={11} /> Exception
                </span>
              )}
              {transaction.status === 'PENDING_REVIEW' && (
                <span className="badge badge-pending-review">
                  <Clock size={11} /> Pending Review
                </span>
              )}
              <span className="badge badge-rule">{transaction.rule_id}</span>
            </div>
          </div>

          <button
            type="button"
            className="drawer-close-btn"
            onClick={onClose}
            aria-label="Close transaction details"
          >
            <X size={18} />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body">
          {/* Workflow Status Banner */}
          {isResolved && (
            <div
              style={{
                padding: '12px 16px',
                borderRadius: '10px',
                backgroundColor: 'var(--status-match-bg)',
                border: '1px solid var(--status-match-border)',
                color: 'var(--status-match)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <CheckCircle2 size={16} />
              <span>
                <strong>Review Status: RESOLVED</strong> — Authoritative controller decision recorded. Deterministic status preserved.
              </span>
            </div>
          )}

          {isEscalated && (
            <div
              style={{
                padding: '14px 16px',
                borderRadius: '10px',
                backgroundColor: 'rgba(217, 119, 6, 0.12)',
                border: '1px solid rgba(217, 119, 6, 0.3)',
                color: '#d97706',
                fontSize: '0.8125rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                <AlertTriangle size={16} />
                <span>
                  <strong>Review Status: ESCALATED</strong> — Discrepancy sent for manual banking desk dispute handling.
                </span>
              </div>

              {exportError && (
                <span style={{ fontSize: '0.75rem', color: '#e11d48' }}>{exportError}</span>
              )}

              <button
                type="button"
                onClick={async () => {
                  setIsExportingCase(true)
                  setExportError(null)
                  try {
                    await downloadSingleCaseDispute(transaction.order_id)
                  } catch (err) {
                    setExportError(err.message || 'Failed to download dispute packet.')
                  } finally {
                    setIsExportingCase(false)
                  }
                }}
                disabled={isExportingCase}
                style={{
                  alignSelf: 'flex-start',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: '#d97706',
                  color: '#fff',
                  border: 'none',
                  padding: '7px 14px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: isExportingCase ? 'not-allowed' : 'pointer',
                  opacity: isExportingCase ? 0.7 : 1,
                }}
              >
                {isExportingCase ? (
                  <RefreshCw size={13} className="spin-icon" />
                ) : (
                  <Download size={13} />
                )}
                <span>Export Case Dispute File (JSON)</span>
              </button>
            </div>
          )}

          {/* Section 1: Deterministic Reconciliation Record */}
          <div className="drawer-section">
            <span className="section-title">
              <Cpu size={14} /> Deterministic Reconciliation Record
            </span>

            <div className="reconciliation-facts-card">
              <div className="facts-grid">
                <div className="fact-item">
                  <span className="fact-label">Payment Gross</span>
                  <span className="fact-value">
                    {transaction.payment_amount != null
                      ? `${transaction.payment_currency} ${transaction.payment_amount}`
                      : 'Missing'}
                  </span>
                </div>

                <div className="fact-item">
                  <span className="fact-label">Bank Settlement</span>
                  <span className="fact-value">
                    {transaction.settlement_amount != null
                      ? `${transaction.settlement_currency} ${transaction.settlement_amount}`
                      : 'Unsettled'}
                  </span>
                </div>

                <div className="fact-item">
                  <span className="fact-label">Variance</span>
                  <span
                    className="fact-value"
                    style={{ color: diffNum !== 0 ? '#e11d48' : 'inherit' }}
                  >
                    {diffNum !== 0 ? `${diffNum > 0 ? '+' : ''}${transaction.difference}` : '0.00'}
                  </span>
                </div>

                <div className="fact-item">
                  <span className="fact-label">Matched Settlement Ref</span>
                  <span className="fact-value" style={{ fontSize: '0.75rem' }}>
                    {transaction.settlement_ids && transaction.settlement_ids.length > 0
                      ? transaction.settlement_ids.join(', ')
                      : 'None'}
                  </span>
                </div>
              </div>

              {/* Deterministic Explanation */}
              <div className="fact-item" style={{ marginTop: '6px' }}>
                <span className="fact-label">Deterministic Reason</span>
                <span
                  style={{
                    fontSize: '0.8125rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.4,
                  }}
                >
                  {transaction.reason || 'Deterministic matching complete.'}
                </span>
              </div>

              {/* Checks Evaluated */}
              {transaction.checks && Object.keys(transaction.checks).length > 0 && (
                <div className="fact-item">
                  <span className="fact-label">Evaluated Checks</span>
                  <div className="checks-evaluated-group">
                    {Object.entries(transaction.checks).map(([chk, passed]) => (
                      <span
                        key={chk}
                        className={`check-pill ${passed ? 'check-pass' : 'check-fail'}`}
                      >
                        {passed ? '✓' : '✗'} {chk}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Human Review Status Warning if still review required */}
              {isReviewRequired && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: '#d97706',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    marginTop: '4px',
                  }}
                >
                  <ShieldAlert size={14} />
                  <span>Human review required prior to balance ledger sign-off</span>
                </div>
              )}
            </div>
          </div>

          {/* Section 2: AI Advisory Brief */}
          <div className="drawer-section">
            <span className="section-title">AI Exception Intelligence</span>
            <AIBriefCard
              investigation={transaction.ai_investigation}
              ruleId={transaction.rule_id}
            />
          </div>

          {/* Section 3: Controller Review Actions (Active when REVIEW_REQUIRED) */}
          {isReviewRequired && (
            <div className="drawer-section" style={{ marginTop: '8px' }}>
              <span className="section-title">
                <UserCheck size={14} color="var(--brand-primary)" /> Controller Review & Action
              </span>

              <div
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border-card)',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Take an authoritative controller action on this transaction:
                </span>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {/* Action 1: Approve Advisory / Sign-off */}
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedAction({
                        action: 'APPROVE_ADVISORY',
                        label: primaryLabel,
                      })
                    }
                    className="btn-trigger-run"
                    style={{ justifyContent: 'space-between' }}
                  >
                    <span>{primaryLabel}</span>
                    <ArrowRight size={14} />
                  </button>

                  {/* Action 2: Manual Override */}
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedAction({
                        action: 'MANUAL_OVERRIDE',
                        label: 'Manual Controller Override',
                      })
                    }
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      backgroundColor: 'var(--bg-secondary)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-primary)',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <span>Manual Override</span>
                    <ArrowRight size={14} />
                  </button>

                  {/* Action 3: Escalate Dispute */}
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedAction({
                        action: 'ESCALATE_DISPUTE',
                        label: 'Escalate Dispute to Banking Desk',
                      })
                    }
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 16px',
                      borderRadius: '10px',
                      backgroundColor: 'rgba(217, 119, 6, 0.08)',
                      border: '1px solid rgba(217, 119, 6, 0.25)',
                      color: '#d97706',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <span>Escalate Acquirer Dispute</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Confirmation Modal */}
        {selectedAction && (
          <ControllerActionModal
            transaction={transaction}
            action={selectedAction.action}
            actionLabel={selectedAction.label}
            onClose={() => setSelectedAction(null)}
            onSubmit={async (payload) => {
              if (onSubmitDecision) {
                await onSubmitDecision(transaction.order_id, payload)
              }
            }}
          />
        )}
      </div>
    </div>
  )
}
