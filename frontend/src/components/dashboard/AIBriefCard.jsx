import { Sparkles, AlertTriangle, ShieldCheck, CheckCircle2, FileText } from 'lucide-react'

export default function AIBriefCard({ investigation, ruleId }) {
  if (!investigation) {
    return (
      <div className="reconciliation-facts-card" style={{ borderStyle: 'dashed' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
          <ShieldCheck size={16} />
          <span style={{ fontSize: '0.8125rem' }}>
            No AI investigation required for this transaction. Deterministically resolved.
          </span>
        </div>
      </div>
    )
  }

  const isCrossCurrency = ruleId === 'RULE_04_CROSS_CURRENCY_CHECK'
  const confidencePercent = investigation.confidence
    ? Math.round(Number(investigation.confidence) * 100)
    : 0

  return (
    <div className="ai-brief-card">
      {/* Header */}
      <div className="ai-brief-header">
        <span className="ai-brief-badge">
          <Sparkles size={14} /> AI Advisory Brief
        </span>
        <span className="badge badge-rule" style={{ color: 'var(--status-ai)' }}>
          {investigation.confidence_tier} CONFIDENCE
        </span>
      </div>

      {/* Advisory Guardrail Disclaimer */}
      <div className="ai-advisory-disclaimer">
        <strong>Advisory AI Triage:</strong> Hypothesized root-cause intelligence. The deterministic ledger status and rule classification remain strictly immutable until manual controller sign-off.
      </div>

      {/* Cross-Currency Warning if RULE_04 */}
      {isCrossCurrency && (
        <div className="ai-nostro-warning">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <AlertTriangle size={15} />
            <span>Nostro Multi-Currency Conversion Policy</span>
          </div>
          Foreign exchange rate conversion requires Nostro controller sign-off. AI cannot approve cross-currency conversions.
        </div>
      )}

      {/* Metric Row: Classification & Confidence */}
      <div className="ai-metric-row">
        <div className="ai-metric-box">
          <span className="fact-label">Classification</span>
          <span className="fact-value" style={{ fontSize: '0.8125rem', color: 'var(--status-ai)' }}>
            {investigation.classification}
          </span>
        </div>

        <div className="ai-metric-box">
          <span className="fact-label">Confidence Score</span>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <span className="fact-value">{investigation.confidence}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{confidencePercent}%</span>
          </div>
          <div className="ai-confidence-meter">
            <div
              className="ai-confidence-bar"
              style={{ width: `${Math.min(confidencePercent, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Root Cause Analysis Narrative */}
      <div className="drawer-section">
        <span className="section-title">
          <FileText size={13} /> Root Cause Analysis
        </span>
        <div className="ai-reasoning-block">
          {investigation.root_cause_analysis}
        </div>
      </div>

      {/* Recommended Action */}
      <div className="drawer-section">
        <span className="section-title">
          <CheckCircle2 size={13} /> Recommended Controller Action
        </span>
        <div
          style={{
            padding: '10px 14px',
            borderRadius: '8px',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8125rem',
            fontWeight: 700,
            color: 'var(--brand-primary)',
          }}
        >
          {investigation.recommended_action}
        </div>
      </div>

      {/* Evidence Citations */}
      {investigation.evidence_used && investigation.evidence_used.length > 0 && (
        <div className="drawer-section">
          <span className="section-title">Evidence Cited (Operational Inputs)</span>
          <ul className="evidence-list">
            {investigation.evidence_used.map((ev, idx) => (
              <li key={idx} className="evidence-item">
                {ev}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
