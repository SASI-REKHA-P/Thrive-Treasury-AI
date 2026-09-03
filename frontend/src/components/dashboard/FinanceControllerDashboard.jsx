import { useState, useEffect, useMemo } from 'react'
import {
  runPipeline,
  getTransactions,
  getTransaction,
  getEvaluationMetrics,
  checkHealth,
  submitReviewDecision,
  getAuditTrail,
  clearAuditTrail,
} from '../../api/client'

import DashboardHeader from './DashboardHeader'
import MetricCards from './MetricCards'
import FilterBar from './FilterBar'
import TransactionTable from './TransactionTable'
import TransactionDrawer from './TransactionDrawer'
import EvaluationView from './EvaluationView'
import AuditTrailView from './AuditTrailView'
import { AlertTriangle, Play, Sparkles, AlertOctagon } from 'lucide-react'
import './dashboard.css'

export default function FinanceControllerDashboard({ onNavigateHome }) {
  const [runSummary, setRunSummary] = useState(null)
  const [allTransactions, setAllTransactions] = useState([])
  const [evaluation, setEvaluation] = useState(null)
  const [auditEvents, setAuditEvents] = useState([])
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [activeTab, setActiveTab] = useState('ledger') // 'ledger' | 'queue' | 'evaluation' | 'audit'

  // Loading & Error States
  const [isRunning, setIsRunning] = useState(false)
  const [isLoadingTxns, setIsLoadingTxns] = useState(false)
  const [isLoadingEval, setIsLoadingEval] = useState(false)
  const [isLoadingAudit, setIsLoadingAudit] = useState(false)
  const [error, setError] = useState(null)
  const [backendHealthy, setBackendHealthy] = useState(false)

  // Ledger Filter States
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [ruleFilter, setRuleFilter] = useState('ALL')
  const [aiOnlyFilter, setAiOnlyFilter] = useState(false)

  // 1. Check Backend Health on Mount
  useEffect(() => {
    let isMounted = true
    checkHealth()
      .then(() => {
        if (isMounted) setBackendHealthy(true)
      })
      .catch(() => {
        if (isMounted) {
          setBackendHealthy(false)
          setError('Backend API is currently offline on port 8000. Start backend with uvicorn app.main:app.')
        }
      })
    return () => {
      isMounted = false
    }
  }, [])

  // 2. Fetch Latest Pipeline Run Data & Audit Trail on Mount
  useEffect(() => {
    let isMounted = true

    getTransactions()
      .then((txns) => {
        if (!isMounted) return
        setAllTransactions(txns || [])

        if (txns && txns.length > 0) {
          const total = txns.length
          const matched = txns.filter((t) => t.status === 'MATCHED').length
          const exceptions = txns.filter((t) => t.status === 'EXCEPTION').length
          const pendingReview = txns.filter((t) => t.status === 'PENDING_REVIEW').length
          const aiInvestigated = txns.filter((t) => t.ai_status === 'INVESTIGATED' || t.requires_ai).length

          setRunSummary((prev) => prev || {
            run_id: 'RUN-CURRENT',
            total,
            matched,
            exceptions,
            pending_review: pendingReview,
            ai_investigated: aiInvestigated,
            processing_time_ms: '0.00',
          })
        }

        getEvaluationMetrics()
          .then((evalData) => {
            if (isMounted) setEvaluation(evalData)
          })
          .catch(() => {})
          .finally(() => {
            if (isMounted) setIsLoadingEval(false)
          })

        getAuditTrail()
          .then((evts) => {
            if (isMounted) setAuditEvents(evts || [])
          })
          .catch(() => {})
          .finally(() => {
            if (isMounted) setIsLoadingAudit(false)
          })
      })
      .catch((err) => {
        if (!isMounted) return
        if (err.status === 404) {
          setAllTransactions([])
          setRunSummary(null)
          setEvaluation(null)
          setAuditEvents([])
        } else {
          setError(err.message || 'Failed to load transaction data.')
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingTxns(false)
          setIsLoadingEval(false)
          setIsLoadingAudit(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [])

  // Fetch Audit Trail Helper
  const fetchAuditEvents = () => {
    setIsLoadingAudit(true)
    getAuditTrail()
      .then((evts) => setAuditEvents(evts || []))
      .catch(() => {})
      .finally(() => setIsLoadingAudit(false))
  }

  // Clear Audit Trail Helper
  const handleClearAuditTrail = async () => {
    setIsLoadingAudit(true)
    try {
      await clearAuditTrail()
      setAuditEvents([])
    } finally {
      setIsLoadingAudit(false)
    }
  }

  // 3. Trigger Full Pipeline Run

  const handleTriggerRun = async () => {
    setIsRunning(true)
    setIsLoadingTxns(true)
    setIsLoadingEval(true)
    setIsLoadingAudit(true)
    setError(null)
    try {
      const summary = await runPipeline()
      setRunSummary(summary)

      // Fetch all transactions, evaluation metrics, and audit events
      const [txns, evalData, evts] = await Promise.all([
        getTransactions(),
        getEvaluationMetrics().catch(() => null),
        getAuditTrail().catch(() => []),
      ])

      setAllTransactions(txns || [])
      setEvaluation(evalData)
      setAuditEvents(evts || [])
      setSelectedTransaction(null)
    } catch (err) {
      setError(err.message || 'Reconciliation pipeline run failed.')
    } finally {
      setIsRunning(false)
      setIsLoadingTxns(false)
      setIsLoadingEval(false)
      setIsLoadingAudit(false)
    }
  }

  // 4. Submit Human Controller Review Decision
  const handleSubmitDecision = async (orderId, payload) => {
    const res = await submitReviewDecision(orderId, payload)

    // Update transaction in memory
    setAllTransactions((prev) =>
      prev.map((t) =>
        t.order_id === orderId
          ? { ...t, human_review_status: res.resulting_human_review_status }
          : t
      )
    )

    // Update selected transaction if drawer is open
    setSelectedTransaction((prev) =>
      prev && prev.order_id === orderId
        ? { ...prev, human_review_status: res.resulting_human_review_status }
        : prev
    )

    // Refresh audit trail
    fetchAuditEvents()
    return res
  }

  // 5. Select Transaction & Open Drawer
  const handleSelectTransaction = async (txn) => {
    // If full investigation is not yet attached, fetch from single transaction endpoint
    if (!txn.ai_investigation && (txn.ai_status === 'INVESTIGATED' || txn.requires_ai)) {
      try {
        const fullTxn = await getTransaction(txn.order_id)
        setSelectedTransaction(fullTxn)
        return
      } catch {
        // fallback to existing object
      }
    }
    setSelectedTransaction(txn)
  }

  // 6. Filter Transactions for Tab 1 (Ledger)
  const filteredTransactions = useMemo(() => {
    return allTransactions.filter((txn) => {
      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.trim().toUpperCase()
        if (!txn.order_id.toUpperCase().includes(query)) {
          return false
        }
      }
      // Status filter
      if (statusFilter !== 'ALL' && txn.status !== statusFilter) {
        return false
      }
      // Rule filter
      if (ruleFilter !== 'ALL' && txn.rule_id !== ruleFilter) {
        return false
      }
      // AI filter
      if (aiOnlyFilter) {
        const isAi = txn.ai_status === 'INVESTIGATED' || txn.requires_ai
        if (!isAi) return false
      }
      return true
    })
  }, [allTransactions, searchQuery, statusFilter, ruleFilter, aiOnlyFilter])

  // 7. Filter Unresolved Transactions for Tab 2 (Action Queue)
  // When a controller resolves a case, it is removed from the active triage queue
  const unresolvedTransactions = useMemo(() => {
    return allTransactions.filter(
      (t) => (t.status === 'EXCEPTION' || t.status === 'PENDING_REVIEW') && t.human_review_status !== 'RESOLVED'
    )
  }, [allTransactions])

  const aiQueueTransactions = useMemo(() => {
    return unresolvedTransactions.filter((t) => t.ai_status === 'INVESTIGATED' || t.requires_ai)
  }, [unresolvedTransactions])

  const operationalExceptions = useMemo(() => {
    return unresolvedTransactions.filter((t) => t.ai_status !== 'INVESTIGATED' && !t.requires_ai)
  }, [unresolvedTransactions])

  return (
    <div className="dashboard-layout">
      <main className="dashboard-main-container">
        {/* Top Header & Trigger Action */}
        <DashboardHeader
          runSummary={runSummary}
          isRunning={isRunning}
          onTriggerRun={handleTriggerRun}
          backendHealthy={backendHealthy}
          onNavigateHome={onNavigateHome}
        />

        {/* Global Error Banner */}
        {error && (
          <div className="error-alert-bar" role="alert">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* KPI Cards Row */}
        <MetricCards runSummary={runSummary} />

        {/* Initial Empty State (if no run has been executed yet) */}
        {!runSummary && !isRunning && !isLoadingTxns && (
          <div className="table-container">
            <div className="state-container">
              <div className="state-icon-wrapper">
                <Play size={24} />
              </div>
              <h2 className="state-title">No Reconciliation Run Yet</h2>
              <p className="state-desc">
                The operational batch (120 payments, 117 settlements) is staged and ready. Click <strong>&quot;Run Reconciliation&quot;</strong> above to execute deterministic normalization, multi-step rule matching, and selective AI exception intelligence.
              </p>
              <button
                type="button"
                onClick={handleTriggerRun}
                className="btn-trigger-run"
                style={{ marginTop: '12px' }}
              >
                <Play size={16} fill="currentColor" />
                <span>Execute Batch Pipeline</span>
              </button>
            </div>
          </div>
        )}

        {/* Operational Dashboard Body (visible when run exists) */}
        {runSummary && (
          <>
            {/* Tab Navigation */}
            <div className="dashboard-tab-bar" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'ledger'}
                className={`tab-btn ${activeTab === 'ledger' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('ledger')}
              >
                <span>Reconciliation Ledger</span>
                <span className="tab-badge">{allTransactions.length}</span>
              </button>

              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'queue'}
                className={`tab-btn ${activeTab === 'queue' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('queue')}
              >
                <span>Controller Action Queue</span>
                <span className="tab-badge" style={{ color: '#e11d48' }}>
                  {unresolvedTransactions.length}
                </span>
              </button>

              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'evaluation'}
                className={`tab-btn ${activeTab === 'evaluation' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('evaluation')}
              >
                <span>Evaluation & Benchmark</span>
                <span className="tab-badge">100%</span>
              </button>

              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'audit'}
                className={`tab-btn ${activeTab === 'audit' ? 'tab-active' : ''}`}
                onClick={() => setActiveTab('audit')}
              >
                <span>Audit Trail</span>
                <span className="tab-badge" style={{ color: 'var(--brand-primary)' }}>
                  {auditEvents.length}
                </span>
              </button>
            </div>

            {/* TAB 1: Reconciliation Ledger */}
            {activeTab === 'ledger' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <FilterBar
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  statusFilter={statusFilter}
                  onStatusChange={setStatusFilter}
                  ruleFilter={ruleFilter}
                  onRuleChange={setRuleFilter}
                  aiOnlyFilter={aiOnlyFilter}
                  onAiOnlyChange={setAiOnlyFilter}
                  totalCount={allTransactions.length}
                  filteredCount={filteredTransactions.length}
                />

                <TransactionTable
                  transactions={filteredTransactions}
                  selectedTransaction={selectedTransaction}
                  onSelectTransaction={handleSelectTransaction}
                  isLoading={isLoadingTxns}
                />
              </div>
            )}

            {/* TAB 2: Controller Action Queue */}
            {activeTab === 'queue' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div
                  style={{
                    backgroundColor: 'var(--bg-card)',
                    border: '1px solid var(--border-card)',
                    borderRadius: '12px',
                    padding: '16px 20px',
                    fontSize: '0.8125rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                  }}
                >
                  <strong>Controller Action Queue:</strong> Shows the active {unresolvedTransactions.length} unresolved transactions requiring human attention. Resolved cases are automatically removed from this queue and recorded in the audit trail.
                </div>

                {/* Section A: AI Advisory Queue */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={16} color="var(--status-ai)" />
                    <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                      AI-Investigated Exceptions ({aiQueueTransactions.length} Active Cases)
                    </h3>
                  </div>

                  <TransactionTable
                    transactions={aiQueueTransactions}
                    selectedTransaction={selectedTransaction}
                    onSelectTransaction={handleSelectTransaction}
                    isLoading={isLoadingTxns}
                  />
                </div>

                {/* Section B: Hard Operational Exceptions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertOctagon size={16} color="#e11d48" />
                    <h3 style={{ fontSize: '0.9375rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                      Operational Exceptions & Routing Errors ({operationalExceptions.length} Active Cases)
                    </h3>
                  </div>

                  <TransactionTable
                    transactions={operationalExceptions}
                    selectedTransaction={selectedTransaction}
                    onSelectTransaction={handleSelectTransaction}
                    isLoading={isLoadingTxns}
                  />
                </div>
              </div>
            )}

            {/* TAB 3: Evaluation & Benchmark */}
            {activeTab === 'evaluation' && (
              <EvaluationView evaluation={evaluation} isLoading={isLoadingEval} />
            )}

            {/* TAB 4: Audit Trail */}
            {activeTab === 'audit' && (
              <AuditTrailView
                auditEvents={auditEvents}
                onRefresh={fetchAuditEvents}
                onClear={handleClearAuditTrail}
                isLoading={isLoadingAudit}
              />
            )}

          </>
        )}

        {/* Transaction Detail Slide-Over Drawer */}
        {selectedTransaction && (
          <TransactionDrawer
            transaction={selectedTransaction}
            onClose={() => setSelectedTransaction(null)}
            onSubmitDecision={handleSubmitDecision}
          />
        )}
      </main>
    </div>
  )
}
