import { Layers, CheckCircle2, AlertOctagon, Clock, Sparkles } from 'lucide-react'

export default function MetricCards({ runSummary }) {
  if (!runSummary) {
    return null
  }

  const total = Number(runSummary.total) || 0
  const matched = Number(runSummary.matched) || 0
  const exceptions = Number(runSummary.exceptions) || 0
  const pendingReview = Number(runSummary.pending_review) || 0
  const aiInvestigated = Number(runSummary.ai_investigated) || 0

  const clearanceRate = total > 0 ? ((matched / total) * 100).toFixed(2) : '0.00'
  const exceptionRate = total > 0 ? ((exceptions / total) * 100).toFixed(2) : '0.00'
  const pendingRate = total > 0 ? ((pendingReview / total) * 100).toFixed(2) : '0.00'
  const aiTriageRate = total > 0 ? ((aiInvestigated / total) * 100).toFixed(2) : '0.00'

  return (
    <div className="metric-cards-grid">
      {/* 1. Total Volume */}
      <div className="kpi-card kpi-total">
        <div className="kpi-card-header">
          <span className="kpi-title">Total Volume</span>
          <div className="kpi-icon-wrapper">
            <Layers size={18} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value">{total}</span>
          <span className="kpi-rate">Txns</span>
        </div>
        <span className="kpi-subtitle">Operational batch processed</span>
      </div>

      {/* 2. Deterministic Clearance */}
      <div className="kpi-card kpi-matched">
        <div className="kpi-card-header">
          <span className="kpi-title">Deterministic Clearance</span>
          <div className="kpi-icon-wrapper">
            <CheckCircle2 size={18} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value">{matched}</span>
          <span className="kpi-rate">{clearanceRate}%</span>
        </div>
        <span className="kpi-subtitle">Auto-cleared without human review</span>
      </div>

      {/* 3. Exceptions Isolated */}
      <div className="kpi-card kpi-exception">
        <div className="kpi-card-header">
          <span className="kpi-title">Exceptions Isolated</span>
          <div className="kpi-icon-wrapper">
            <AlertOctagon size={18} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value">{exceptions}</span>
          <span className="kpi-rate">{exceptionRate}%</span>
        </div>
        <span className="kpi-subtitle">Discrepancies safely quarantined</span>
      </div>

      {/* 4. Pending Review */}
      <div className="kpi-card kpi-review">
        <div className="kpi-card-header">
          <span className="kpi-title">Pending Review</span>
          <div className="kpi-icon-wrapper">
            <Clock size={18} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value">{pendingReview}</span>
          <span className="kpi-rate">{pendingRate}%</span>
        </div>
        <span className="kpi-subtitle">Nostro / Cross-currency triage</span>
      </div>

      {/* 5. AI Triage Queue */}
      <div className="kpi-card kpi-ai">
        <div className="kpi-card-header">
          <span className="kpi-title">AI Triage Queue</span>
          <div className="kpi-icon-wrapper">
            <Sparkles size={18} />
          </div>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-value">{aiInvestigated}</span>
          <span className="kpi-rate">{aiTriageRate}%</span>
        </div>
        <span className="kpi-subtitle">Selective advisory briefs generated</span>
      </div>
    </div>
  )
}
