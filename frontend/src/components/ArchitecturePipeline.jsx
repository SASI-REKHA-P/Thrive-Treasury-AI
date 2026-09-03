import { useState, useEffect, useRef } from 'react'
import {
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Database,
  SlidersHorizontal,
  Binary,
  GitBranch,
  Sparkles,
  UserCheck,
  ClipboardList,
  CheckCircle2,
  AlertTriangle,
  Check,
  CreditCard,
  Building2
} from 'lucide-react'

const DEMO_WATERMARK = 'Sample Batch #2026-DEMO · Demonstration Data Only'

const PIPELINE_STAGES = [
  {
    stepIndex: 0,
    displayNum: '01',
    stepLabel: 'STEP 01 / 07',
    id: 'input',
    title: 'Data Sources & Ingestion',
    subtext: 'Payment Gateway Feeds & Bank Clearing Journals',
    icon: Database,
    operation: 'Asynchronous ingestion of raw checkout webhook events and bank settlement batch exports.',
    principle: 'Financial data originates in disparate formats, timing windows, and bank protocols.',
  },
  {
    stepIndex: 1,
    displayNum: '02',
    stepLabel: 'STEP 02 / 07',
    id: 'normalization',
    title: 'Canonical Normalization',
    subtext: 'Standardize Fields, Timestamps & References',
    icon: SlidersHorizontal,
    operation: 'Sanitizing reference keys, standardizing UTC timestamps, and mapping ISO currencies into canonical schema.',
    principle: 'Never compare un-sanitized financial records across different processing protocols.',
  },
  {
    stepIndex: 2,
    displayNum: '03',
    stepLabel: 'STEP 03 / 07',
    id: 'deterministic',
    title: 'Deterministic Rule Engine',
    subtext: 'Rule #01: Exact Match (No AI Required)',
    icon: Binary,
    operation: 'Comparing exact mathematical equivalence across amount, reference ID, and date window.',
    principle: 'Deterministic rules handle predictable transactions without requiring AI reasoning.',
  },
  {
    stepIndex: 3,
    displayNum: '04',
    stepLabel: 'STEP 04 / 07',
    id: 'decision',
    title: 'Decision Branch Gate',
    subtext: 'Zero Variance Match vs Discrepancy Split',
    icon: GitBranch,
    operation: 'Branching: ORD-8492 auto-clears to MATCHED. ORD-8493 & ORD-8494 branch to EXCEPTION.',
    principle: 'Clear records clear immediately; only records with variance or ambiguity proceed downstream.',
  },
  {
    stepIndex: 4,
    displayNum: '05',
    stepLabel: 'STEP 05 / 07',
    id: 'ai_investigation',
    title: 'AI Exception Investigation',
    subtext: 'Contextual Contract & Fee Modeling',
    icon: Sparkles,
    operation: 'AI analyzes fee models (MDR + GST) for ORD-8493 and inspects FX delay for ORD-8494.',
    principle: 'AI investigates the ambiguity by generating explanatory hypotheses from fee schedules.',
  },
  {
    stepIndex: 5,
    displayNum: '06',
    stepLabel: 'STEP 06 / 07',
    id: 'human_review',
    title: 'Human Review Queue',
    subtext: 'Ambiguity Threshold Governance',
    icon: UserCheck,
    operation: 'ORD-8494 FX timing variance crosses ambiguity threshold: safely routed to treasury specialist.',
    principle: 'When confidence is insufficient, uncertain financial cases are decided by a human.',
  },
  {
    stepIndex: 6,
    displayNum: '07',
    stepLabel: 'STEP 07 / 07',
    id: 'audit_trail',
    title: 'Chronological Audit Trail',
    subtext: 'Structured Action Log & Decision History',
    icon: ClipboardList,
    operation: 'Chronologically recording all actions: 1 Matched, 1 AI Explained, 1 Pending Review.',
    principle: 'A clear reconciliation state, ready for review and audit.',
  },
]

const DEMO_TRANSACTIONS = [
  {
    id: 'ORD-8492',
    name: 'Record A',
    subtitle: 'Standard Checkout Payment',
    paymentAmount: '₹4,200.00',
    settlementAmount: '₹4,200.00',
    variance: '₹0.00',
    currency: 'INR',
    ruleApplied: 'Rule #01: Exact Match',
    finalStatus: 'MATCHED',
    finalBadgeClass: 'badge-matched',
    note: 'Deterministic rules handle predictable transactions without requiring AI reasoning.',
    stepOperations: [
      { op: 'Ingesting raw payment & bank journal records', qual: 'Standby' },
      { op: 'Normalized auth reference: PG_AUTH_8492', qual: 'Normalized' },
      { op: 'Evaluating Rule #01: Exact mathematical equivalence', qual: 'Evaluating' },
      { op: 'MATCHED: Zero variance auto-cleared (No AI)', qual: 'Matched' },
      { op: 'Bypassed AI reasoning (Not required for exact matches)', qual: 'Matched' },
      { op: 'Bypassed human review queue (Zero ambiguity)', qual: 'Matched' },
      { op: 'Logged in Chronological Audit Trail: MATCHED', qual: 'Matched' },
    ],
  },
  {
    id: 'ORD-8493',
    name: 'Record B',
    subtitle: 'Enterprise SaaS Subscription',
    paymentAmount: '₹15,000.00',
    settlementAmount: '₹14,646.00',
    variance: '-₹354.00',
    currency: 'INR',
    ruleApplied: 'Rule #01: Delta Detected',
    finalStatus: 'AI EXPLAINED',
    finalBadgeClass: 'badge-ai',
    note: 'AI investigated fee schedule: 2.0% MDR (₹300) + 18% GST (₹54) explains -₹354 variance.',
    aiBreakdown: {
      mdr: '₹300.00 (2.0% MDR)',
      gst: '₹54.00 (18% GST on MDR)',
      total: '₹354.00',
    },
    stepOperations: [
      { op: 'Ingesting customer payment & net settlement deposit', qual: 'Standby' },
      { op: 'Normalized fee schedule: Standard Payment Gateway MDR', qual: 'Normalized' },
      { op: 'Rule #01: Flagged variance of -₹354.00', qual: 'Delta Detected' },
      { op: 'EXCEPTION: Routed to AI reasoning channel', qual: 'Exception' },
      { op: 'AI investigated: 2% MDR (₹300) + 18% GST (₹54) = ₹354 explained', qual: 'High Confidence' },
      { op: 'Resolved with fee context: Rate schedule conforms', qual: 'High Confidence' },
      { op: 'Logged in Chronological Audit Trail: AI EXPLAINED', qual: 'High Confidence' },
    ],
  },
  {
    id: 'ORD-8494',
    name: 'Record C',
    subtitle: 'Cross-Border Advisory Fee',
    paymentAmount: '$500.00 USD',
    settlementAmount: '₹41,200.00 INR',
    variance: 'FX Divergence',
    currency: 'USD / INR',
    ruleApplied: 'Rule #04: Cross-Currency Check',
    finalStatus: 'PENDING REVIEW',
    finalBadgeClass: 'badge-review',
    note: 'Exchange-rate timing creates an ambiguity that requires human review.',
    fxDetails: {
      bookingRate: '83.10',
      settlementRate: '82.40',
      delay: '48 hours',
    },
    stepOperations: [
      { op: 'Ingesting cross-border USD invoice & INR settlement', qual: 'Standby' },
      { op: 'Normalized dual currency timestamps & booking rate', qual: 'Normalized' },
      { op: 'Rule #04: Spot exchange-rate divergence identified', qual: 'Delta Detected' },
      { op: 'EXCEPTION: Ambiguous FX settlement timing', qual: 'Exception' },
      { op: 'AI analyzed: 48h settlement delay rate lag (82.40 vs 83.10)', qual: 'Investigating' },
      { op: 'ROUTED TO HUMAN REVIEW: Ambiguity threshold exceeded', qual: 'Review Required' },
      { op: 'Logged in Chronological Audit Trail: PENDING REVIEW', qual: 'Review Required' },
    ],
  },
]

export default function ArchitecturePipeline() {
  const [activeStep, setActiveStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [activeTxnIndex, setActiveTxnIndex] = useState(1) // Default focus on Record B (shows AI exception)
  const timerRef = useRef(null)

  const currentStage = PIPELINE_STAGES[activeStep]
  const currentTxn = DEMO_TRANSACTIONS[activeTxnIndex]
  const currentOp = currentTxn.stepOperations[activeStep]

  // Auto-run loop: advances smoothly at ~2.5s cadence
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current)
      return
    }

    timerRef.current = setInterval(() => {
      setActiveStep((prev) => {
        if (prev >= PIPELINE_STAGES.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 2500)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPlaying])

  const handleTogglePlay = () => {
    if (activeStep >= PIPELINE_STAGES.length - 1) {
      setActiveStep(0)
      setIsPlaying(true)
    } else {
      setIsPlaying((prev) => !prev)
    }
  }

  const handleReset = () => {
    setIsPlaying(false)
    setActiveStep(0)
  }

  const handlePrev = () => {
    setIsPlaying(false)
    setActiveStep((prev) => Math.max(0, prev - 1))
  }

  const handleNext = () => {
    setIsPlaying(false)
    setActiveStep((prev) => Math.min(PIPELINE_STAGES.length - 1, prev + 1))
  }

  const handleStepSelect = (index) => {
    setIsPlaying(false)
    setActiveStep(index)
  }

  return (
    <section className="architecture-theater-section" id="architecture" aria-label="Interactive Architecture Demonstration">
      <div className="architecture-theater-container">
        {/* Section Header */}
        <div className="section-header">
          <div className="section-tag">Interactive Architecture Theater</div>
          <h2 className="section-title">The Architecture Behind Every Decision</h2>
          <p className="section-description">
            Thrive Treasury AI uses the simplest reliable reasoning layer for each financial exception —
            deterministic rules first, AI when ambiguity exists, and human review when uncertainty remains.
          </p>
        </div>

        {/* Demo Watermark & Active Layer Banner */}
        <div className="theater-status-bar">
          <div className="watermark-chip">
            <span className="watermark-pulse-dot"></span>
            <span>{DEMO_WATERMARK}</span>
          </div>
          <div className="active-layer-indicator" aria-live="polite">
            <span className="layer-tag-label">Active Layer:</span>
            <span className="layer-tag-val">{currentStage.stepLabel} · {currentStage.title}</span>
          </div>
        </div>

        {/* Playback Control Deck & Step Scrubber */}
        <div className="theater-control-deck">
          <div className="deck-playback-buttons">
            <button
              type="button"
              className="deck-btn deck-btn-nav"
              onClick={handlePrev}
              disabled={activeStep === 0}
              aria-label="Previous step"
              title="Previous step"
            >
              <ChevronLeft size={16} />
              <span>Previous</span>
            </button>

            <button
              type="button"
              className={`deck-btn deck-btn-play ${isPlaying ? 'is-playing' : ''}`}
              onClick={handleTogglePlay}
              aria-label={isPlaying ? 'Pause architecture' : 'Run Architecture'}
            >
              {isPlaying ? (
                <>
                  <Pause size={16} />
                  <span>Pause</span>
                </>
              ) : (
                <>
                  <Play size={16} />
                  <span>{activeStep >= PIPELINE_STAGES.length - 1 ? 'Replay Architecture' : 'Run Architecture'}</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="deck-btn deck-btn-nav"
              onClick={handleReset}
              aria-label="Reset to Step 1"
              title="Reset to Step 01"
            >
              <RotateCcw size={15} />
              <span>Reset</span>
            </button>

            <button
              type="button"
              className="deck-btn deck-btn-nav"
              onClick={handleNext}
              disabled={activeStep === PIPELINE_STAGES.length - 1}
              aria-label="Next step"
              title="Next step"
            >
              <span>Next</span>
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Direct Step Scrubber: STEP 01 / 07 to STEP 07 / 07 */}
          <div className="deck-scrubber-tabs" role="tablist" aria-label="Pipeline Step Scrubber">
            {PIPELINE_STAGES.map((stage, idx) => {
              const isActive = idx === activeStep
              const isCompleted = idx < activeStep

              return (
                <button
                  key={stage.id}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`scrubber-tab ${isActive ? 'tab-active' : ''} ${isCompleted ? 'tab-completed' : ''}`}
                  onClick={() => handleStepSelect(idx)}
                >
                  <span className="tab-num">{stage.stepLabel}</span>
                  <span className="tab-name">{stage.title}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Compact Secondary Transaction Inspector (Telemetry Bar) */}
        <div className="theater-telemetry-bar">
          <div className="telemetry-txn-selector">
            <span className="telemetry-label">Tracked Transaction:</span>
            <div className="telemetry-chips-group">
              {DEMO_TRANSACTIONS.map((txn, idx) => (
                <button
                  key={txn.id}
                  type="button"
                  className={`txn-chip ${activeTxnIndex === idx ? 'chip-active' : ''}`}
                  onClick={() => setActiveTxnIndex(idx)}
                  title={`Inspect ${txn.name} (${txn.id})`}
                >
                  <span className="chip-name">{txn.name}:</span>
                  <span className="chip-id">{txn.id}</span>
                  <span className="chip-amt font-mono">{txn.paymentAmount}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="telemetry-live-operation">
            <div className="telemetry-op-group">
              <span className="op-flag">Processing at Layer {currentStage.displayNum}:</span>
              <span className="op-text">
                <span className="op-bullet">▶</span>
                <strong>{currentOp.op}</strong>
              </span>
            </div>
            <div className="telemetry-status-pill">
              <span className="status-label">Status:</span>
              <span className={`status-val-pill ${currentOp.qual.toLowerCase().replace(/\s+/g, '-')}`}>
                {currentOp.qual}
              </span>
            </div>
          </div>
        </div>

        {/* ====================================================================
            THE SPATIAL ARCHITECTURE CANVAS (PRIMARY DOMINANT VIEWPORT)
           ==================================================================== */}
        <div className="spatial-pipeline-canvas" aria-label="Living Architecture Stage">
          
          {/* STAGE 1: DUAL DATA SOURCES (PAYMENT + SETTLEMENT) */}
          <div className={`spatial-stage-block stage-sources ${activeStep === 0 ? 'stage-active' : ''} ${activeStep > 0 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 01</span>
              <h3 className="stage-block-title">DATA SOURCES & INGESTION</h3>
              {activeStep > 0 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>

            <div className="data-sources-grid">
              {/* Payment Records Feed Card */}
              <div className="source-card payment-source">
                <div className="source-card-header">
                  <div className="source-icon-box blue">
                    <CreditCard size={18} />
                  </div>
                  <div>
                    <h4 className="source-title">Payment Records Feed</h4>
                    <span className="source-sub">Checkout & Webhook Event Feeds</span>
                  </div>
                </div>
                <div className="source-records-preview font-mono">
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">ORD-8492</span>
                    <span className="pill-val">₹4,200.00</span>
                  </div>
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">ORD-8493</span>
                    <span className="pill-val">₹15,000.00</span>
                  </div>
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">ORD-8494</span>
                    <span className="pill-val">$500.00 USD</span>
                  </div>
                </div>
              </div>

              {/* Settlement Journal Feed Card */}
              <div className="source-card settlement-source">
                <div className="source-card-header">
                  <div className="source-icon-box indigo">
                    <Building2 size={18} />
                  </div>
                  <div>
                    <h4 className="source-title">Settlement Journal Feed</h4>
                    <span className="source-sub">Bank Clearing & Processor Payouts</span>
                  </div>
                </div>
                <div className="source-records-preview font-mono">
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">SET-9011</span>
                    <span className="pill-val">₹4,200.00</span>
                  </div>
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">SET-9012</span>
                    <span className="pill-val">₹14,646.00</span>
                  </div>
                  <div className={`source-record-pill ${activeStep === 0 ? 'pulse-ingest' : ''}`}>
                    <span className="pill-id">SET-9013</span>
                    <span className="pill-val">₹41,200.00</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Converging SVG Flow Beams from Stage 1 into Stage 2 */}
          <div className="spatial-connector-junction">
            <svg className="connector-svg" viewBox="0 0 400 40" preserveAspectRatio="none">
              <path
                d="M 100 0 C 100 25, 200 15, 200 40"
                className={`connector-line ${activeStep >= 1 ? 'line-active' : ''}`}
              />
              <path
                d="M 300 0 C 300 25, 200 15, 200 40"
                className={`connector-line ${activeStep >= 1 ? 'line-active' : ''}`}
              />
            </svg>
          </div>

          {/* STAGE 2: CANONICAL NORMALIZATION */}
          <div className={`spatial-stage-block stage-normalization ${activeStep === 1 ? 'stage-active' : ''} ${activeStep > 1 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 02</span>
              <div className="stage-title-group">
                <SlidersHorizontal size={20} className="stage-icon-inline text-purple" />
                <h3 className="stage-block-title">CANONICAL NORMALIZATION LAYER</h3>
              </div>
              {activeStep > 1 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>
            <p className="stage-block-desc">
              Standardizes raw gateway payloads and bank clearing exports: UTC timestamps, normalized auth references,
              and ISO currency pairs are mapped to canonical models before any matching logic runs.
            </p>
            <div className="normalization-tags font-mono">
              <span className="norm-tag">✓ Auth Key: PG_AUTH_8492</span>
              <span className="norm-tag">✓ Rate Card: 2.0% MDR + 18% GST</span>
              <span className="norm-tag">✓ Timezone: UTC Standardized</span>
            </div>
          </div>

          {/* Flow Beam 2 -> 3 */}
          <div className={`spatial-beam-vertical ${activeStep >= 2 ? 'beam-active' : ''}`}></div>

          {/* STAGE 3: DETERMINISTIC RULE ENGINE */}
          <div className={`spatial-stage-block stage-rules ${activeStep === 2 ? 'stage-active' : ''} ${activeStep > 2 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 03</span>
              <div className="stage-title-group">
                <Binary size={20} className="stage-icon-inline text-indigo" />
                <h3 className="stage-block-title">DETERMINISTIC RULE ENGINE</h3>
              </div>
              {activeStep > 2 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>
            <p className="stage-block-desc">
              <strong>Rule #01 (Exact Match):</strong> Evaluates mathematical identity across Amount, Currency, and Auth ID.
              Deterministic rules handle predictable transactions without requiring AI reasoning.
            </p>
            <div className="rules-evaluation-strip font-mono">
              <div className={`rule-eval-card ${activeStep >= 2 ? 'pass-rule' : ''}`}>
                <span className="rule-name">ORD-8492 Evaluation:</span>
                <span className="rule-result text-emerald">₹4,200.00 == ₹4,200.00 · EXACT MATCH</span>
              </div>
              <div className={`rule-eval-card ${activeStep >= 2 ? 'delta-rule' : ''}`}>
                <span className="rule-name">ORD-8493 & ORD-8494:</span>
                <span className="rule-result text-amber">Non-Zero Delta Detected · Passed to Decision Gate</span>
              </div>
            </div>
          </div>

          {/* Flow Beam 3 -> 4 */}
          <div className={`spatial-beam-vertical ${activeStep >= 3 ? 'beam-active' : ''}`}></div>

          {/* STAGE 4: DECISION BRANCH GATE (THE CRITICAL SPLIT) */}
          <div className={`spatial-stage-block stage-decision ${activeStep === 3 ? 'stage-active' : ''} ${activeStep > 3 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 04</span>
              <div className="stage-title-group">
                <GitBranch size={20} className="stage-icon-inline text-gold" />
                <h3 className="stage-block-title">DECISION BRANCH GATE</h3>
              </div>
              {activeStep > 3 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>
            <p className="stage-block-desc">
              Does the record satisfy Rule #01 exact matching? The architecture branches immediately based on verified mathematical facts.
            </p>

            {/* THE SPATIAL BRANCHING VIEWPORT */}
            <div className="spatial-branch-fork">
              {/* LEFT BRANCH: MATCHED OUTCOME */}
              <div className={`branch-card branch-matched-card ${activeStep >= 3 ? 'branch-live' : ''}`}>
                <div className="branch-card-header">
                  <CheckCircle2 size={20} className="text-emerald" />
                  <h4 className="branch-title text-emerald">BRANCH: MATCHED</h4>
                </div>
                <div className="matched-packet-box font-mono">
                  <div className="packet-main">
                    <span className="packet-order">ORD-8492</span>
                    <span className="packet-amounts">₹4,200.00 → ₹4,200.00</span>
                  </div>
                  <span className="packet-subtext text-emerald">✓ AUTO-CLEARED · ZERO AI REQUIRED</span>
                </div>
                <p className="branch-rationale">
                  Instant clearance. Straightforward financial reconciliation bypasses LLM latency and processing costs entirely.
                </p>
              </div>

              {/* RIGHT BRANCH: EXCEPTION CHANNEL */}
              <div className={`branch-card branch-exception-card ${activeStep >= 3 ? 'branch-live' : ''}`}>
                <div className="branch-card-header">
                  <AlertTriangle size={20} className="text-amber" />
                  <h4 className="branch-title text-amber">BRANCH: EXCEPTION CHANNEL</h4>
                </div>
                <div className="exception-packet-box font-mono">
                  <div className="packet-pair">
                    <span className="packet-order">ORD-8493:</span>
                    <span className="packet-amounts">₹15,000 vs ₹14,646 (Delta: -₹354.00)</span>
                  </div>
                  <div className="packet-pair">
                    <span className="packet-order">ORD-8494:</span>
                    <span className="packet-amounts">$500 USD vs ₹41,200 INR (FX Divergence)</span>
                  </div>
                </div>
                <p className="branch-rationale text-amber">
                  ▼ Routed downstream into Contextual AI Exception Investigation
                </p>
              </div>
            </div>
          </div>

          {/* Flow Beam 4 -> 5 (Continues from Exception Branch) */}
          <div className={`spatial-beam-vertical ${activeStep >= 4 ? 'beam-active' : ''}`}></div>

          {/* STAGE 5: AI EXCEPTION INVESTIGATION */}
          <div className={`spatial-stage-block stage-ai ${activeStep === 4 ? 'stage-active' : ''} ${activeStep > 4 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 05</span>
              <div className="stage-title-group">
                <Sparkles size={20} className="stage-icon-inline text-purple" />
                <h3 className="stage-block-title">AI EXCEPTION INVESTIGATION LAYER</h3>
              </div>
              {activeStep > 4 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>
            <p className="stage-block-desc">
              AI is invoked strictly for exceptions. Contextual models analyze gateway contracts, fee schedules,
              and timing lags to explain why discrepancies occurred.
            </p>

            {/* Detailed AI Reasoning Cards */}
            <div className="ai-investigation-grid">
              {/* Record B Breakdown: MDR + GST Fee Model */}
              <div className="ai-reasoning-card card-ord-8493">
                <div className="reasoning-card-header">
                  <span className="reasoning-target font-mono">Target: ORD-8493 (Enterprise SaaS)</span>
                  <span className="confidence-pill purple">High Confidence</span>
                </div>
                <div className="reasoning-amounts font-mono">
                  <span>Payment: <strong>₹15,000.00</strong></span>
                  <span>Settlement: <strong>₹14,646.00</strong></span>
                  <span className="text-amber">Difference: <strong>-₹354.00</strong></span>
                </div>
                <div className="arithmetic-breakdown-box font-mono">
                  <div className="arith-line">
                    <span>MDR Fee (2.0% of ₹15,000):</span>
                    <strong>₹300.00</strong>
                  </div>
                  <div className="arith-line">
                    <span>GST on MDR (18.0% of ₹300):</span>
                    <strong>₹54.00</strong>
                  </div>
                  <div className="arith-divider"></div>
                  <div className="arith-line arith-total">
                    <span>Total Explained Fee Difference:</span>
                    <strong className="text-purple">₹354.00</strong>
                  </div>
                </div>
                <p className="ai-hypothesis-quote">
                  "The settlement difference aligns with a 2.0% MDR of ₹300.00 plus 18% GST on the MDR of ₹54.00, explaining the ₹354.00 variance."
                </p>
                <div className="reasoning-footer">
                  <span className="footer-status-pill text-purple">Outcome: AI EXPLAINED</span>
                  <span className="footer-note font-mono">Verified against rate card</span>
                </div>
              </div>

              {/* Record C Context: Cross-Border FX Timing Lag */}
              <div className="ai-reasoning-card card-ord-8494">
                <div className="reasoning-card-header">
                  <span className="reasoning-target font-mono">Target: ORD-8494 (Cross-Border Invoice)</span>
                  <span className="confidence-pill amber">Review Required</span>
                </div>
                <div className="reasoning-amounts font-mono">
                  <span>Payment: <strong>$500.00 USD</strong></span>
                  <span>Settlement: <strong>₹41,200.00 INR</strong></span>
                </div>
                <div className="fx-context-box font-mono">
                  <div className="fx-line">
                    <span>Booking Spot Rate:</span>
                    <strong>83.10 INR/USD</strong>
                  </div>
                  <div className="fx-line">
                    <span>Settlement Clearing Rate:</span>
                    <strong>82.40 INR/USD</strong>
                  </div>
                  <div className="fx-line">
                    <span>Settlement Delay:</span>
                    <strong>48 hours</strong>
                  </div>
                </div>
                <p className="ai-hypothesis-quote text-amber">
                  "Exchange-rate timing creates an ambiguity that requires human review."
                </p>
                <div className="reasoning-footer">
                  <span className="footer-status-pill text-amber">Outcome: PENDING HUMAN REVIEW</span>
                  <span className="footer-note font-mono">Ambiguity threshold exceeded</span>
                </div>
              </div>
            </div>
          </div>

          {/* Flow Beam 5 -> 6 */}
          <div className={`spatial-beam-vertical ${activeStep >= 5 ? 'beam-active' : ''}`}></div>

          {/* STAGE 6: HUMAN REVIEW QUEUE */}
          <div className={`spatial-stage-block stage-human ${activeStep === 5 ? 'stage-active' : ''} ${activeStep > 5 ? 'stage-completed' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 06</span>
              <div className="stage-title-group">
                <UserCheck size={20} className="stage-icon-inline text-amber" />
                <h3 className="stage-block-title">HUMAN REVIEW QUEUE</h3>
              </div>
              {activeStep > 5 && <span className="stage-completed-badge"><Check size={14} /> Completed</span>}
            </div>
            <p className="stage-block-desc">
              The platform never guesses on uncertain financial items. When ambiguity exists, cases are escalated
              with full context to treasury specialists for final determination.
            </p>

            <div className="human-queue-display">
              <div className="queue-escalation-card font-mono">
                <div className="queue-card-top">
                  <div className="queue-id-group">
                    <span className="queue-badge-amber">ESCALATED</span>
                    <strong className="queue-order">ORD-8494</strong>
                    <span className="queue-amounts">$500.00 USD → ₹41,200.00 INR</span>
                  </div>
                  <span className="confidence-pill amber">Review Required</span>
                </div>
                <div className="queue-reason-callout">
                  <AlertTriangle size={16} className="text-amber flex-shrink-0" />
                  <span><strong>Escalation Reason:</strong> "Exchange-rate timing creates an ambiguity that requires human review."</span>
                </div>
                <div className="queue-footer-policy">
                  <strong>Governance Policy:</strong> Autonomous clearing prevented. Treasury sign-off required for settlement variances exceeding rate tolerance.
                </div>
              </div>
            </div>
          </div>

          {/* Flow Beam 6 -> 7 */}
          <div className={`spatial-beam-vertical ${activeStep >= 6 ? 'beam-active' : ''}`}></div>

          {/* STAGE 7: CHRONOLOGICAL AUDIT TRAIL */}
          <div className={`spatial-stage-block stage-audit ${activeStep === 6 ? 'stage-active' : ''}`}>
            <div className="stage-meta-header">
              <span className="stage-num-tag">STAGE 07</span>
              <div className="stage-title-group">
                <ClipboardList size={20} className="stage-icon-inline text-blue" />
                <h3 className="stage-block-title">CHRONOLOGICAL AUDIT TRAIL</h3>
              </div>
              <span className="confidence-pill blue">Structured Action Log</span>
            </div>
            <p className="stage-block-desc">
              Every decision, rule result, AI reasoning hypothesis, and human escalation is permanently committed
              into a verifiable chronological history.
            </p>

            {/* Timeline Breakdown clearly distinguishing all 3 outcomes */}
            <div className="audit-timeline-grid font-mono">
              {/* Record 1: MATCHED */}
              <div className="audit-timeline-item item-matched">
                <div className="timeline-col-num">01</div>
                <div className="timeline-col-order">ORD-8492</div>
                <div className="timeline-col-amounts">₹4,200.00 → ₹4,200.00</div>
                <div className="timeline-col-badge">
                  <span className="audit-badge badge-matched">MATCHED</span>
                </div>
                <div className="timeline-col-desc">Rule #01: Exact Match · Zero AI Latency</div>
              </div>

              {/* Record 2: AI EXPLAINED */}
              <div className="audit-timeline-item item-ai">
                <div className="timeline-col-num">02</div>
                <div className="timeline-col-order">ORD-8493</div>
                <div className="timeline-col-amounts">₹15,000.00 vs ₹14,646.00</div>
                <div className="timeline-col-badge">
                  <span className="audit-badge badge-ai">AI EXPLAINED</span>
                </div>
                <div className="timeline-col-desc">Explained -₹354 variance: ₹300 MDR (2%) + ₹54 GST (18%)</div>
              </div>

              {/* Record 3: PENDING REVIEW */}
              <div className="audit-timeline-item item-review">
                <div className="timeline-col-num">03</div>
                <div className="timeline-col-order">ORD-8494</div>
                <div className="timeline-col-amounts">$500.00 USD → ₹41,200.00 INR</div>
                <div className="timeline-col-badge">
                  <span className="audit-badge badge-review">PENDING REVIEW</span>
                </div>
                <div className="timeline-col-desc">FX 48h Timing Variance · In Treasury Reviewer Queue</div>
              </div>
            </div>

            <div className="audit-resolution-footer">
              <span className="audit-resolution-text">
                ✓ A clear reconciliation state, ready for review and audit.
              </span>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
