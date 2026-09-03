import { useState, useRef, useEffect } from 'react'
import {
  Play,
  RefreshCw,
  ArrowLeft,
  ShieldCheck,
  Cpu,
  Download,
  ChevronDown,
  FileSpreadsheet,
  AlertOctagon,
  History,
  AlertTriangle,
} from 'lucide-react'
import {
  downloadLedgerCSV,
  downloadDisputesCSV,
  downloadAuditTrailCSV,
} from '../../api/client'

export default function DashboardHeader({
  runSummary,
  isRunning,
  onTriggerRun,
  backendHealthy,
  onNavigateHome,
}) {
  const [exportOpen, setExportOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState(null)
  const dropdownRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setExportOpen(false)
      }
    }
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setExportOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  const handleExport = async (exportFn, label) => {
    setIsExporting(true)
    setExportError(null)
    setExportOpen(false)
    try {
      await exportFn()
    } catch (err) {
      setExportError(err.message || `Failed to export ${label}.`)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="dashboard-header-card">
      <div className="header-left">
        <div className="header-breadcrumbs">
          <button
            onClick={onNavigateHome}
            className="header-breadcrumbs-btn"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--brand-primary)',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: 0,
              fontSize: '0.8125rem',
              fontWeight: 600,
            }}
          >
            <ArrowLeft size={14} /> Back to Public Landing
          </button>
          <span>/</span>
          <span>Workspace</span>
        </div>

        <div className="header-title-row">
          <h1>Finance Controller Workspace</h1>
          <div className="header-telemetry-pills">
            <span className={`telemetry-pill ${backendHealthy ? 'live-pulse' : ''}`}>
              <ShieldCheck size={13} color={backendHealthy ? '#10b981' : '#94a3b8'} />
              {backendHealthy ? 'Core API Online' : 'Connecting API...'}
            </span>
            <span className="telemetry-pill">
              <Cpu size={13} />
              Deterministic Engine
            </span>
            {runSummary && (
              <>
                <span className="telemetry-pill">
                  Run ID: {runSummary.run_id}
                </span>
                <span className="telemetry-pill">
                  Latency: {runSummary.processing_time_ms} ms
                </span>
              </>
            )}
          </div>
        </div>

        {exportError && (
          <div
            style={{
              marginTop: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: '#e11d48',
            }}
          >
            <AlertTriangle size={13} />
            <span>{exportError}</span>
          </div>
        )}
      </div>

      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Export Dropdown */}
        <div className="export-dropdown-wrapper" ref={dropdownRef} style={{ position: 'relative' }}>
          <button
            type="button"
            className="status-pill-btn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              opacity: !runSummary || isRunning || isExporting ? 0.6 : 1,
              cursor: !runSummary || isRunning || isExporting ? 'not-allowed' : 'pointer',
            }}
            disabled={!runSummary || isRunning || isExporting}
            onClick={() => setExportOpen((prev) => !prev)}
            aria-expanded={exportOpen}
            aria-haspopup="true"
          >
            {isExporting ? (
              <RefreshCw size={14} className="spin-icon" />
            ) : (
              <Download size={14} />
            )}
            <span>Export</span>
            <ChevronDown size={13} />
          </button>

          {exportOpen && (
            <div
              className="export-dropdown-menu"
              role="menu"
              style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                right: 0,
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border-card)',
                borderRadius: '10px',
                boxShadow: 'var(--shadow-lg)',
                minWidth: '240px',
                zIndex: 50,
                padding: '6px',
                display: 'flex',
                flexDirection: 'column',
                gap: '2px',
              }}
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => handleExport(downloadLedgerCSV, 'Reconciliation Ledger')}
                className="export-menu-item"
              >
                <FileSpreadsheet size={14} color="var(--brand-primary)" />
                <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.8125rem' }}>Reconciliation Ledger</span>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>All 120 batch records (CSV)</span>
                </div>
              </button>

              <button
                type="button"
                role="menuitem"
                onClick={() => handleExport(downloadDisputesCSV, 'Dispute Packet')}
                className="export-menu-item"
              >
                <AlertOctagon size={14} color="#e11d48" />
                <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.8125rem' }}>Acquirer Dispute Packet</span>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Escalated cases only (CSV)</span>
                </div>
              </button>

              <button
                type="button"
                role="menuitem"
                onClick={() => handleExport(downloadAuditTrailCSV, 'Audit Trail')}
                className="export-menu-item"
              >
                <History size={14} color="var(--status-ai)" />
                <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.8125rem' }}>Compliance Audit Trail</span>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Traceable decision log (CSV)</span>
                </div>
              </button>
            </div>
          )}
        </div>

        {/* Run Pipeline Button */}
        <button
          type="button"
          onClick={onTriggerRun}
          disabled={isRunning || isExporting}
          className="btn-trigger-run"
          aria-label="Run Reconciliation Pipeline"
        >
          {isRunning ? (
            <>
              <RefreshCw size={16} className="spin-icon" />
              <span>Processing Batch...</span>
            </>
          ) : (
            <>
              <Play size={16} fill="currentColor" />
              <span>Run Reconciliation</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
