import { Search, Sparkles } from 'lucide-react'

const RULES = [
  { value: 'ALL', label: 'All Rules' },
  { value: 'RULE_01_EXACT_MATCH', label: 'RULE 01: Exact Match' },
  { value: 'RULE_02_EXPECTED_FEE', label: 'RULE 02: Expected Fee' },
  { value: 'RULE_03_DATE_TOLERANCE', label: 'RULE 03: Date Tolerance' },
  { value: 'RULE_04_CROSS_CURRENCY_CHECK', label: 'RULE 04: Cross Currency' },
  { value: 'RULE_05_MISSING_SETTLEMENT', label: 'RULE 05: Missing Settlement' },
  { value: 'RULE_06_DUPLICATE_CHECK', label: 'RULE 06: Duplicate Check' },
  { value: 'RULE_07_CURRENCY_MISMATCH', label: 'RULE 07: Currency Mismatch' },
  { value: 'RULE_08_AMOUNT_MISMATCH', label: 'RULE 08: Amount Mismatch' },
]

export default function FilterBar({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  ruleFilter,
  onRuleChange,
  aiOnlyFilter,
  onAiOnlyChange,
  totalCount,
  filteredCount,
}) {
  return (
    <div className="filter-bar-card">
      <div className="filter-left-group">
        {/* Order ID Search */}
        <div className="search-input-wrapper">
          <Search size={14} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search Order ID (e.g. ORD-8494)..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            aria-label="Search transactions by Order ID"
          />
        </div>

        {/* Status Pills */}
        <div className="status-pills-group" role="group" aria-label="Filter by Status">
          {['ALL', 'MATCHED', 'EXCEPTION', 'PENDING_REVIEW'].map((st) => (
            <button
              key={st}
              type="button"
              className={`status-pill-btn ${statusFilter === st ? 'active' : ''}`}
              onClick={() => onStatusChange(st)}
            >
              {st === 'ALL' ? 'All Status' : st.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Rule Dropdown */}
        <select
          className="rule-select-dropdown"
          value={ruleFilter}
          onChange={(e) => onRuleChange(e.target.value)}
          aria-label="Filter by Reconciliation Rule"
        >
          {RULES.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>

        {/* AI Filter Toggle */}
        <label className="ai-toggle-label">
          <input
            type="checkbox"
            checked={aiOnlyFilter}
            onChange={(e) => onAiOnlyChange(e.target.checked)}
          />
          <Sparkles size={13} color="var(--status-ai)" />
          <span>AI Investigated Only</span>
        </label>
      </div>

      <div className="filter-right-group">
        <span className="results-count-text">
          Showing <strong>{filteredCount}</strong> of {totalCount} records
        </span>
      </div>
    </div>
  )
}
