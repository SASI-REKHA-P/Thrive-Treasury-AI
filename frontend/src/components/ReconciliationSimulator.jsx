import { useState, useEffect, useRef } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  Sparkles,
  UserCheck,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  GitMerge,
  Cpu,
  Binary
} from 'lucide-react'
import { DEMO_BATCH_META, DEMO_RECORDS, SIMULATION_STEPS } from '../data/demoData'

export default function ReconciliationSimulator({
  activeStep: controlledStep,
  onStepChange,
  className = '',
}) {
  const [internalStep, setInternalStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const timerRef = useRef(null)

  const isControlled = controlledStep !== undefined
  const activeStepIndex = isControlled ? controlledStep : internalStep
  const currentStep = SIMULATION_STEPS[activeStepIndex] || SIMULATION_STEPS[0]

  const setStep = (index) => {
    if (isControlled && onStepChange) {
      onStepChange(index)
    } else {
      setInternalStep(index)
    }
  }

  // Play / Pause auto sequence loop
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current)
      return
    }

    timerRef.current = setInterval(() => {
      const next = activeStepIndex + 1
      if (next >= SIMULATION_STEPS.length) {
        setIsPlaying(false)
      } else {
        if (isControlled && onStepChange) {
          onStepChange(next)
        } else {
          setInternalStep(next)
        }
      }
    }, 2600)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPlaying, isControlled, activeStepIndex, onStepChange])

  const togglePlay = () => {
    if (activeStepIndex >= SIMULATION_STEPS.length - 1) {
      setStep(0)
      setIsPlaying(true)
    } else {
      setIsPlaying((prev) => !prev)
    }
  }

  const handleReset = () => {
    setIsPlaying(false)
    setStep(0)
  }

  return (
    <div className={`simulator-container ${className}`} id="simulation" aria-label="Interactive Financial Reconciliation Simulator">
      {/* Top Demonstration Watermark Header */}
      <div className="simulator-header-bar">
        <div className="demo-badge">
          <span className="demo-badge-dot"></span>
          <span className="demo-badge-text">{DEMO_BATCH_META.tag}</span>
        </div>
        <div className="system-status-indicator" role="status" aria-live="polite">
          <span className="system-status-label">Engine State:</span>
          <span className="system-status-text">{currentStep.systemState}</span>
        </div>
      </div>

      {/* Primary Simulator Control Panel */}
      <div className="simulator-control-panel">
        <div className="playback-actions">
          <button
            type="button"
            className={`btn-play-pause ${isPlaying ? 'active' : ''}`}
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause simulation' : 'Play demonstration run'}
          >
            {isPlaying ? (
              <>
                <Pause size={16} />
                <span>Pause</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>{activeStepIndex >= SIMULATION_STEPS.length - 1 ? 'Replay Run' : 'Play Run'}</span>
              </>
            )}
          </button>

          <button
            type="button"
            className="btn-reset"
            onClick={handleReset}
            aria-label="Reset simulation to initial state"
            title="Reset to Step 01"
          >
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>
        </div>

        {/* 6 Step Pills */}
        <div className="step-pills-nav" role="tablist" aria-label="Simulation state steps">
          {SIMULATION_STEPS.map((step, idx) => {
            const isActive = idx === activeStepIndex
            const isCompleted = idx < activeStepIndex

            return (
              <button
                key={step.id}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`step-pill ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                onClick={() => {
                  setIsPlaying(false)
                  setStep(idx)
                }}
              >
                <span className="pill-num">{step.stepNumber}</span>
                <span className="pill-name">{step.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Living Simulation Chamber */}
      <div className="simulator-stage-chamber">
        {/* Ambient glow responsive to active step */}
        <div className={`chamber-glow step-${activeStepIndex}`}></div>

        {/* Stage Grid: Left (Payment) - Center (Engine) - Right (Settlement) */}
        <div className="chamber-grid">
          {/* LEFT RAIL: Payment Records */}
          <div className="chamber-rail payment-rail">
            <div className="rail-header">
              <div className="rail-title-group">
                <span className="rail-title">Payment Records</span>
                <span className="rail-subtitle">Gateway & txn logs</span>
              </div>
              <span className="rail-count">3 records</span>
            </div>

            <div className="records-stream">
              {/* Record A: ORD-8492 */}
              <div
                className={`record-card ${activeStepIndex >= 1 ? 'is-matched' : ''} ${
                  activeStepIndex === 1 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">{DEMO_RECORDS.recordA.orderId}</span>
                  <span className="record-currency">{DEMO_RECORDS.recordA.currency}</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordA.paymentAmount}</div>
                <div className="record-desc">{DEMO_RECORDS.recordA.description}</div>
                {activeStepIndex >= 1 && (
                  <div className="record-status-tag tag-matched">
                    <CheckCircle2 size={12} />
                    <span>Exact Match</span>
                  </div>
                )}
              </div>

              {/* Record B: ORD-8493 */}
              <div
                className={`record-card ${activeStepIndex >= 2 ? 'is-discrepancy' : ''} ${
                  activeStepIndex === 2 || activeStepIndex === 3 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">{DEMO_RECORDS.recordB.orderId}</span>
                  <span className="record-currency">{DEMO_RECORDS.recordB.currency}</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordB.paymentAmount}</div>
                <div className="record-desc">{DEMO_RECORDS.recordB.description}</div>
                {activeStepIndex >= 2 && (
                  <div className="record-status-tag tag-warning">
                    <AlertTriangle size={12} />
                    <span>Difference: {DEMO_RECORDS.recordB.difference}</span>
                  </div>
                )}
              </div>

              {/* Record C: ORD-8494 */}
              <div
                className={`record-card ${activeStepIndex >= 4 ? 'is-review' : ''} ${
                  activeStepIndex === 4 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">{DEMO_RECORDS.recordC.orderId}</span>
                  <span className="record-currency">{DEMO_RECORDS.recordC.currency}</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordC.paymentAmount}</div>
                <div className="record-desc">{DEMO_RECORDS.recordC.description}</div>
                {activeStepIndex >= 4 && (
                  <div className="record-status-tag tag-review">
                    <UserCheck size={12} />
                    <span>Review Required</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* CENTER: THRIVE Reconciliation Engine */}
          <div className="chamber-center">
            <div className={`engine-box step-focus-${activeStepIndex}`}>
              <div className="engine-brand-header">
                <div className="engine-logo-dot"></div>
                <span className="engine-title">THRIVE</span>
                <span className="engine-tagline">Reconciliation Engine</span>
              </div>

              {/* Engine Architecture Modules: Deterministic Rules + AI Exception Reasoning */}
              <div className="engine-modules">
                {/* Module 1: Deterministic Rules */}
                <div className={`engine-submodule rules-submodule ${activeStepIndex === 1 ? 'active-pulse' : ''}`}>
                  <div className="submodule-header">
                    <Binary size={15} className="submodule-icon" />
                    <span className="submodule-title">DETERMINISTIC RULES</span>
                  </div>
                  <div className="submodule-status">
                    {activeStepIndex >= 1 ? 'Rule #01: Exact Match · Passed' : 'Rule evaluation standby'}
                  </div>
                </div>

                <div className="engine-module-divider">
                  <span>+</span>
                </div>

                {/* Module 2: AI Exception Reasoning */}
                <div className={`engine-submodule ai-submodule ${activeStepIndex === 3 ? 'active-pulse' : ''}`}>
                  <div className="submodule-header">
                    <Cpu size={15} className="submodule-icon" />
                    <span className="submodule-title">AI EXCEPTION REASONING</span>
                  </div>
                  <div className="submodule-status">
                    {activeStepIndex === 3 ? 'Contextual MDR + GST analysis' : activeStepIndex >= 4 ? 'Context generated' : 'Idle (invoked on ambiguity)'}
                  </div>
                </div>
              </div>

              {/* Real-time Central Processing Indicator */}
              <div className="engine-realtime-badge">
                {activeStepIndex === 0 && <span className="state-text">Ready · Ingesting Records</span>}
                {activeStepIndex === 1 && (
                  <span className="state-text state-green">
                    <CheckCircle2 size={13} />
                    Rule #01 Applied · AI Not Required
                  </span>
                )}
                {activeStepIndex === 2 && (
                  <span className="state-text state-amber">
                    <AlertTriangle size={13} />
                    Discrepancy Isolated · -₹354.00
                  </span>
                )}
                {activeStepIndex === 3 && (
                  <span className="state-text state-purple">
                    <Sparkles size={13} />
                    AI Investigating Fee Variance
                  </span>
                )}
                {activeStepIndex === 4 && (
                  <span className="state-text state-review">
                    <ShieldAlert size={13} />
                    Ambiguity Threshold · Routing to Human
                  </span>
                )}
                {activeStepIndex === 5 && (
                  <span className="state-text state-green">
                    <CheckCircle2 size={13} />
                    Ready for Review and Audit
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT RAIL: Settlement Feed */}
          <div className="chamber-rail settlement-rail">
            <div className="rail-header">
              <div className="rail-title-group">
                <span className="rail-title">Settlement Feed</span>
                <span className="rail-subtitle">Bank & processor feed</span>
              </div>
              <span className="rail-count">3 entries</span>
            </div>

            <div className="records-stream">
              {/* Settlement A: Matches ORD-8492 */}
              <div
                className={`record-card ${activeStepIndex >= 1 ? 'is-matched' : ''} ${
                  activeStepIndex === 1 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">SET-9011</span>
                  <span className="record-currency">INR</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordA.settlementAmount}</div>
                <div className="record-desc">Bank payout batch #B901</div>
                {activeStepIndex >= 1 && (
                  <div className="record-status-tag tag-matched">
                    <CheckCircle2 size={12} />
                    <span>Matched Ref</span>
                  </div>
                )}
              </div>

              {/* Settlement B: Net Payout for ORD-8493 */}
              <div
                className={`record-card ${activeStepIndex >= 2 ? 'is-discrepancy' : ''} ${
                  activeStepIndex === 2 || activeStepIndex === 3 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">SET-9012</span>
                  <span className="record-currency">INR</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordB.settlementAmount}</div>
                <div className="record-desc">Net settlement deposit</div>
                {activeStepIndex >= 2 && (
                  <div className="record-status-tag tag-warning">
                    <AlertTriangle size={12} />
                    <span>Variance: -₹354.00</span>
                  </div>
                )}
              </div>

              {/* Settlement C: INR deposit for USD order */}
              <div
                className={`record-card ${activeStepIndex >= 4 ? 'is-review' : ''} ${
                  activeStepIndex === 4 ? 'is-focus' : ''
                }`}
              >
                <div className="record-top">
                  <span className="record-id">SET-9013</span>
                  <span className="record-currency">INR</span>
                </div>
                <div className="record-amount">{DEMO_RECORDS.recordC.settlementAmount}</div>
                <div className="record-desc">Rate 82.40 · 48h settlement delay</div>
                {activeStepIndex >= 4 && (
                  <div className="record-status-tag tag-review">
                    <UserCheck size={12} />
                    <span>FX Rate Variance</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic Contextual Focus Drawer (Steps 2, 3, 4, 5) */}
        <div className="chamber-context-area">
          {/* STEP 2: DETERMINISTIC MATCH DETAILS */}
          {activeStepIndex === 1 && (
            <div className="context-card match-context-card animate-fade-in">
              <div className="context-card-header">
                <div className="context-card-badge green">
                  <CheckCircle2 size={15} />
                  <span>RECORD A · DETERMINISTIC MATCH</span>
                </div>
                <span className="confidence-pill green">{DEMO_RECORDS.recordA.confidence}</span>
              </div>
              <div className="context-math-row">
                <div className="math-item">
                  <span className="math-label">Payment:</span>
                  <span className="math-val">{DEMO_RECORDS.recordA.paymentAmount}</span>
                </div>
                <span className="math-operator">→</span>
                <div className="math-item">
                  <span className="math-label">Settlement:</span>
                  <span className="math-val">{DEMO_RECORDS.recordA.settlementAmount}</span>
                </div>
                <span className="math-operator">=</span>
                <div className="math-item">
                  <span className="math-label">Difference:</span>
                  <span className="math-val green-text">{DEMO_RECORDS.recordA.difference}</span>
                </div>
              </div>
              <div className="context-detail-note">
                <strong>Result: MATCHED</strong> — Verified via {DEMO_RECORDS.recordA.rule}.
                <span className="ai-not-required-badge">AI Used: No</span>
              </div>
            </div>
          )}

          {/* STEP 3 & 4: AI EXCEPTION INVESTIGATION */}
          {(activeStepIndex === 2 || activeStepIndex === 3) && (
            <div className="context-card ai-context-card animate-fade-in">
              <div className="context-card-header">
                <div className="context-card-badge purple">
                  <Sparkles size={15} />
                  <span>RECORD B · {activeStepIndex === 2 ? 'DISCREPANCY DETECTED' : 'AI EXCEPTION INVESTIGATION'}</span>
                </div>
                <span className="confidence-pill purple">{DEMO_RECORDS.recordB.confidence}</span>
              </div>

              {/* Arithmetic Breakdown */}
              <div className="arithmetic-card">
                <div className="arithmetic-inputs">
                  <div className="math-item">
                    <span className="math-label">Payment Amount:</span>
                    <span className="math-val">{DEMO_RECORDS.recordB.paymentAmount}</span>
                  </div>
                  <div className="math-item">
                    <span className="math-label">Settlement Amount:</span>
                    <span className="math-val">{DEMO_RECORDS.recordB.settlementAmount}</span>
                  </div>
                  <div className="math-item">
                    <span className="math-label">Difference:</span>
                    <span className="math-val red-text">{DEMO_RECORDS.recordB.difference}</span>
                  </div>
                </div>

                {activeStepIndex === 3 && (
                  <div className="ai-breakdown-details animate-slide-down">
                    <div className="breakdown-title">
                      <Cpu size={14} />
                      <span>AI Investigation Breakdown:</span>
                    </div>
                    <div className="breakdown-grid">
                      <div className="breakdown-line">
                        <span>MDR (2%):</span>
                        <strong>{DEMO_RECORDS.recordB.breakdown.mdrAmount}</strong>
                      </div>
                      <div className="breakdown-line">
                        <span>GST on MDR (18% of ₹300):</span>
                        <strong>{DEMO_RECORDS.recordB.breakdown.gstAmount}</strong>
                      </div>
                      <div className="breakdown-divider"></div>
                      <div className="breakdown-line total-line">
                        <span>Total Explained Difference:</span>
                        <strong className="purple-text">{DEMO_RECORDS.recordB.breakdown.totalExplained}</strong>
                      </div>
                    </div>
                    <p className="ai-quote">"{DEMO_RECORDS.recordB.aiExplanation}"</p>
                    <div className="ai-status-footer">
                      <span>Status: <strong>AI Investigated</strong></span>
                      <span>AI Used: <strong>Yes</strong></span>
                      <span className="demo-data-pill">Demonstration Data</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 5: HUMAN REVIEW ESCALATION */}
          {activeStepIndex === 4 && (
            <div className="context-card review-context-card animate-fade-in">
              <div className="context-card-header">
                <div className="context-card-badge amber">
                  <UserCheck size={15} />
                  <span>RECORD C · HUMAN-IN-THE-LOOP ESCALATION</span>
                </div>
                <span className="confidence-pill amber">{DEMO_RECORDS.recordC.confidence}</span>
              </div>
              <div className="review-details-grid">
                <div className="review-stat">
                  <span className="stat-label">Order:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.orderId}</span>
                </div>
                <div className="review-stat">
                  <span className="stat-label">Payment:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.paymentAmount}</span>
                </div>
                <div className="review-stat">
                  <span className="stat-label">Settlement:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.settlementAmount}</span>
                </div>
                <div className="review-stat">
                  <span className="stat-label">Settlement Rate:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.settlementRate}</span>
                </div>
                <div className="review-stat">
                  <span className="stat-label">Booking Rate:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.bookingRate}</span>
                </div>
                <div className="review-stat">
                  <span className="stat-label">Settlement Delay:</span>
                  <span className="stat-val">{DEMO_RECORDS.recordC.settlementDelay}</span>
                </div>
              </div>
              <div className="review-reason-box">
                <AlertTriangle size={16} className="amber-icon" />
                <span><strong>Reason:</strong> "{DEMO_RECORDS.recordC.reason}"</span>
              </div>
              <div className="review-footer-note">
                Status: <strong>Review Required</strong> · Uncertain cases are safely escalated rather than blindly automated.
              </div>
            </div>
          )}

          {/* STEP 6: AUDITED RESOLUTION SUMMARY */}
          {activeStepIndex === 5 && (
            <div className="context-card audit-context-card animate-fade-in">
              <div className="context-card-header">
                <div className="context-card-badge green">
                  <GitMerge size={15} />
                  <span>RECONCILIATION SUMMARY · SAMPLE BATCH</span>
                </div>
                <span className="confidence-pill blue">Ready for Review and Audit</span>
              </div>

              <div className="audit-outcomes-list">
                <div className="outcome-row">
                  <div className="outcome-item-badge green">
                    <CheckCircle2 size={14} />
                    <span>{DEMO_RECORDS.recordA.orderId}</span>
                  </div>
                  <span className="outcome-detail">₹4,200.00 → ₹4,200.00</span>
                  <span className="outcome-action green-text">MATCHED (Rule #01 · Deterministic)</span>
                </div>

                <div className="outcome-row">
                  <div className="outcome-item-badge purple">
                    <Sparkles size={14} />
                    <span>{DEMO_RECORDS.recordB.orderId}</span>
                  </div>
                  <span className="outcome-detail">₹15,000.00 vs ₹14,646.00</span>
                  <span className="outcome-action purple-text">AI INVESTIGATED (-₹354 MDR+GST fee explained)</span>
                </div>

                <div className="outcome-row">
                  <div className="outcome-item-badge amber">
                    <UserCheck size={14} />
                    <span>{DEMO_RECORDS.recordC.orderId}</span>
                  </div>
                  <span className="outcome-detail">$500.00 vs ₹41,200.00</span>
                  <span className="outcome-action amber-text">REVIEW REQUIRED (FX delay variance)</span>
                </div>
              </div>

              <div className="audit-representation-flow">
                <span className="flow-title">Audit Log Representation:</span>
                <div className="flow-steps">
                  <span className="flow-step">Ingested</span>
                  <ArrowRight size={13} className="flow-arrow" />
                  <span className="flow-step">Compared</span>
                  <ArrowRight size={13} className="flow-arrow" />
                  <span className="flow-step">Investigated</span>
                  <ArrowRight size={13} className="flow-arrow" />
                  <span className="flow-step active">Reviewed</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
