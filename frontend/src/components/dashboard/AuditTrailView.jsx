import { useState } from 'react'
import {
  History,
  Search,
  RefreshCw,
  UserCheck,
  ShieldCheck,
  Cpu,
  AlertTriangle,
  Trash2,
  X,
} from 'lucide-react'
import { clearAuditTrail } from '../../api/client'

function EventTypeBadge({ eventType }) {
  switch (eventType) {
    case 'DECISION_RECORDED':
      return (
        <span className="badge badge-ai" style={{ fontWeight: 700 }}>
          <UserCheck size={11} /> Controller Decision
        </span>
      )
    case 'BATCH_LOADED':
      return (
        <span className="badge badge-matched">
          <Cpu size={11} /> Batch Loaded
        </span>
      )
    case 'EXCEPTION_DETECTED':
      return (
        <span className="badge badge-exception">
          <AlertTriangle size={11} /> Exception Flagged
        </span>
      )
    case 'HUMAN_REVIEW_QUEUED':
      return (
        <span className="badge badge-pending-review">
          <History size={11} /> Review Queued
        </span>
      )
    default:
      return <span className="badge badge-rule">{eventType}</span>
  }
}

export default function AuditTrailView({
  auditEvents = [],
  onRefresh,
  onClear,
  isLoading,
}) {
  const [filterOrderId, setFilterOrderId] = useState('')
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [isClearing, setIsClearing] = useState(false)
  const [clearError, setClearError] = useState(null)

  const filteredEvents = auditEvents.filter((ev) => {
    if (!filterOrderId.trim()) return true
    const query = filterOrderId.trim().toUpperCase()
    return ev.order_id && ev.order_id.toUpperCase().includes(query)
  })

  const handleConfirmClear = async () => {
    if (isClearing) return
    setIsClearing(true)
    setClearError(null)
    try {
      if (onClear) {
        await onClear()
      } else {
        await clearAuditTrail()
      }
      setShowConfirmModal(false)
    } catch (err) {
      setClearError(err.message || 'Failed to clear audit trail.')
    } finally {
      setIsClearing(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Error Alert Bar */}
      {clearError && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '10px',
            backgroundColor: 'rgba(225, 29, 72, 0.1)',
            border: '1px solid rgba(225, 29, 72, 0.25)',
            color: '#e11d48',
            fontSize: '0.8125rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
          role="alert"
        >
          <AlertTriangle size={16} />
          <span>{clearError}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="filter-bar-card">
        <div className="filter-left-group">
          <div className="search-input-wrapper">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Filter audit events by Order ID..."
              value={filterOrderId}
              onChange={(e) => setFilterOrderId(e.target.value)}
              aria-label="Filter audit events by Order ID"
            />
          </div>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Showing <strong>{filteredEvents.length}</strong> logged events
          </span>
        </div>

        <div className="filter-right-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading || isClearing}
            className="status-pill-btn active"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={13} className={isLoading ? 'spin-icon' : ''} />
            <span>Refresh Audit Log</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setClearError(null)
              setShowConfirmModal(true)
            }}
            disabled={isLoading || isClearing || auditEvents.length === 0}
            className="status-pill-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              color: auditEvents.length === 0 ? 'var(--text-muted)' : '#e11d48',
              opacity: auditEvents.length === 0 ? 0.5 : 1,
              cursor: auditEvents.length === 0 || isClearing ? 'not-allowed' : 'pointer',
            }}
            aria-label="Clear All Audit Events"
          >
            <Trash2 size={13} />
            <span>Clear All</span>
          </button>
        </div>
      </div>

      {/* Empty State */}
      {filteredEvents.length === 0 && (
        <div className="table-container">
          <div className="state-container">
            <div className="state-icon-wrapper">
              <History size={24} />
            </div>
            <h3 className="state-title">No Audit Events Recorded Yet</h3>
            <p className="state-desc">
              Audit events are recorded when operational batch cycles occur and when finance controllers submit review decisions on quarantined transactions.
            </p>
          </div>
        </div>
      )}

      {/* Audit Events Timeline / Table */}
      {filteredEvents.length > 0 && (
        <div className="table-container">
          <div className="table-scroll">
            <table className="ledger-table" aria-label="Audit Trail Events">
              <thead>
                <tr>
                  <th scope="col">Timestamp (UTC)</th>
                  <th scope="col">Event Type</th>
                  <th scope="col">Order Ref</th>
                  <th scope="col">Actor</th>
                  <th scope="col">Decision / Action</th>
                  <th scope="col">Operational Notes</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((evt) => {
                  const details = evt.details || {}
                  const formattedTime = new Date(evt.timestamp).toLocaleString('en-US', {
                    timeZone: 'UTC',
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                  })

                  return (
                    <tr key={evt.event_id}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {formattedTime} UTC
                      </td>
                      <td>
                        <EventTypeBadge eventType={evt.event_type} />
                      </td>
                      <td className="order-id-cell">
                        {evt.order_id || 'BATCH'}
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          {evt.actor.startsWith('SYSTEM') ? (
                            <ShieldCheck size={13} color="var(--brand-primary)" />
                          ) : (
                            <UserCheck size={13} color="var(--status-ai)" />
                          )}
                          <span>{evt.actor}</span>
                        </div>
                      </td>
                      <td>
                        {details.action ? (
                          <span className="badge badge-rule" style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>
                            {details.action}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>
                      <td style={{ maxWidth: '340px', whiteSpace: 'normal', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {details.notes ? (
                          <span>{details.notes}</span>
                        ) : details.total ? (
                          <span>Batch clearance run processed {details.total} transactions ({details.matched} matched, {details.exceptions} exceptions).</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Standard event recorded.</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div
          className="drawer-backdrop"
          onClick={() => !isClearing && setShowConfirmModal(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Confirm Clear Audit Trail"
        >
          <div
            className="modal-card"
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '460px',
              margin: 'auto',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              borderRadius: '16px',
              boxShadow: 'var(--shadow-lg)',
              overflow: 'hidden',
              animation: 'fadeIn 0.2s ease',
            }}
          >
            {/* Modal Header */}
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
                <Trash2 size={18} color="#e11d48" />
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Clear Audit Trail
                </h3>
              </div>
              <button
                type="button"
                onClick={() => !isClearing && setShowConfirmModal(false)}
                disabled={isClearing}
                className="drawer-close-btn"
                aria-label="Close dialog"
              >
                <X size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Are you sure you want to clear all in-memory audit trail events?
              </p>

              <div
                style={{
                  padding: '12px 14px',
                  borderRadius: '10px',
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-muted)',
                  lineHeight: 1.4,
                }}
              >
                This will reset the audit event log ({auditEvents.length} recorded events).
                Reconciliation results, transaction classifications, and controller decisions remain completely intact.
              </div>

              {/* Modal Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  className="status-pill-btn"
                  onClick={() => setShowConfirmModal(false)}
                  disabled={isClearing}
                  style={{ padding: '8px 16px', fontSize: '0.8125rem' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-trigger-run"
                  onClick={handleConfirmClear}
                  disabled={isClearing}
                  style={{
                    backgroundColor: '#e11d48',
                    borderColor: '#e11d48',
                    padding: '8px 16px',
                    fontSize: '0.8125rem',
                  }}
                >
                  {isClearing ? (
                    <>
                      <RefreshCw size={14} className="spin-icon" />
                      <span>Clearing...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 size={14} />
                      <span>Yes, Clear All</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
