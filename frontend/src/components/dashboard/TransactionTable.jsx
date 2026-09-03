import { CheckCircle2, AlertOctagon, Clock, Sparkles, UserCheck } from 'lucide-react'

function StatusBadge({ status }) {
  switch (status) {
    case 'MATCHED':
      return (
        <span className="badge badge-matched">
          <CheckCircle2 size={12} /> Matched
        </span>
      )
    case 'EXCEPTION':
      return (
        <span className="badge badge-exception">
          <AlertOctagon size={12} /> Exception
        </span>
      )
    case 'PENDING_REVIEW':
      return (
        <span className="badge badge-pending-review">
          <Clock size={12} /> Pending Review
        </span>
      )
    default:
      return <span className="badge">{status}</span>
  }
}

function formatRule(ruleId) {
  if (!ruleId) return 'N/A'
  return ruleId.replace(/^RULE_\d+_/, '').replace(/_/g, ' ')
}

export default function TransactionTable({
  transactions,
  selectedTransaction,
  onSelectTransaction,
  isLoading,
}) {
  if (isLoading) {
    return (
      <div className="table-container">
        <div className="state-container">
          <span className="state-title">Loading Ledger Data...</span>
          <span className="state-desc">Fetching transaction records from deterministic engine</span>
        </div>
      </div>
    )
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="table-container">
        <div className="state-container">
          <span className="state-title">No Transactions Found</span>
          <span className="state-desc">No records match the selected status, rule, or query filters.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="table-container">
      <div className="table-scroll">
        <table className="ledger-table" aria-label="Reconciliation Ledger">
          <thead>
            <tr>
              <th scope="col">Order ID</th>
              <th scope="col">Status</th>
              <th scope="col">Reconciliation Rule</th>
              <th scope="col" style={{ textAlign: 'right' }}>Payment Gross</th>
              <th scope="col" style={{ textAlign: 'right' }}>Bank Deposit</th>
              <th scope="col" style={{ textAlign: 'right' }}>Variance</th>
              <th scope="col">Intelligence & Triage</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => {
              const isSelected = selectedTransaction && selectedTransaction.order_id === txn.order_id
              const diffNum = Number(txn.difference) || 0
              const isAiInvestigated = txn.ai_status === 'INVESTIGATED' || txn.requires_ai

              return (
                <tr
                  key={txn.order_id}
                  onClick={() => onSelectTransaction(txn)}
                  className={isSelected ? 'row-selected' : ''}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      onSelectTransaction(txn)
                    }
                  }}
                  role="button"
                  aria-label={`View transaction ${txn.order_id}`}
                >
                  <td className="order-id-cell">{txn.order_id}</td>
                  <td>
                    <StatusBadge status={txn.status} />
                  </td>
                  <td>
                    <span className="badge badge-rule" title={txn.rule_id}>
                      {formatRule(txn.rule_id)}
                    </span>
                  </td>
                  <td className="amount-cell">
                    {txn.payment_amount != null
                      ? `${txn.payment_currency} ${txn.payment_amount}`
                      : '—'}
                  </td>
                  <td className="amount-cell">
                    {txn.settlement_amount != null
                      ? `${txn.settlement_currency} ${txn.settlement_amount}`
                      : '—'}
                  </td>
                  <td className={`variance-cell ${diffNum !== 0 ? 'var-diff' : 'var-zero'}`}>
                    {diffNum !== 0 ? `${diffNum > 0 ? '+' : ''}${txn.difference}` : '0.00'}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {isAiInvestigated && (
                        <span className="badge badge-ai" title="Investigated by Advisory AI">
                          <Sparkles size={11} /> AI Brief
                        </span>
                      )}
                      {txn.requires_human_review && (
                        <span className="badge badge-human-review" title="Requires Human Controller Review">
                          <UserCheck size={11} /> Review Req.
                        </span>
                      )}
                      {!isAiInvestigated && !txn.requires_human_review && (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Auto-cleared</span>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
