/**
 * Thrive Treasury AI - Frontend API Client
 * Uses native fetch with relative `/api` endpoints routed via Vite development proxy.
 */

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function request(path, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  let response
  try {
    response = await fetch(path, config)
  } catch (err) {
    throw new ApiError(
      `Network error communicating with backend: ${err.message}. Ensure backend is running on port 8000.`,
      0,
      null
    )
  }

  let data
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json()
    } catch {
      data = null
    }
  } else {
    data = await response.text()
  }


  if (!response.ok) {
    const errorDetail = (data && data.detail) || response.statusText || 'API request failed'
    throw new ApiError(errorDetail, response.status, data)
  }

  return data
}

/**
 * Health check endpoint
 */
export async function checkHealth() {
  return request('/api/health')
}

/**
 * Execute complete operational reconciliation pipeline
 */
export async function runPipeline() {
  return request('/api/reconciliation/run', {
    method: 'POST',
  })
}

/**
 * Query transactions with optional filters
 * @param {Object} filters - { status, rule_id, requires_ai }
 */
export async function getTransactions(filters = {}) {
  const params = new URLSearchParams()
  if (filters.status && filters.status !== 'ALL') {
    params.append('status', filters.status)
  }
  if (filters.rule_id && filters.rule_id !== 'ALL') {
    params.append('rule_id', filters.rule_id)
  }
  if (filters.requires_ai !== undefined && filters.requires_ai !== null && filters.requires_ai !== 'ALL') {
    params.append('requires_ai', String(filters.requires_ai))
  }

  const queryString = params.toString()
  const path = queryString ? `/api/reconciliation/transactions?${queryString}` : '/api/reconciliation/transactions'
  return request(path)
}

/**
 * Fetch a single transaction result by order ID
 * @param {string} orderId
 */
export async function getTransaction(orderId) {
  return request(`/api/reconciliation/transactions/${encodeURIComponent(orderId)}`)
}

/**
 * Fetch the AI investigation brief for an investigated order
 * @param {string} orderId
 */
export async function getInvestigation(orderId) {
  return request(`/api/investigations/${encodeURIComponent(orderId)}`)
}

/**
 * Fetch batch evaluation metrics computed against ground truth
 */
export async function getEvaluationMetrics() {
  return request('/api/evaluation/metrics')
}

/**
 * Submit an authoritative controller review decision
 * @param {string} orderId
 * @param {Object} payload - { action, actor, notes }
 */
export async function submitReviewDecision(orderId, payload) {
  return request(`/api/reconciliation/review/${encodeURIComponent(orderId)}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/**
 * Retrieve chronological audit trail events
 * @param {string} [orderId]
 */
export async function getAuditTrail(orderId = null) {
  const path = orderId
    ? `/api/reconciliation/audit-trail?order_id=${encodeURIComponent(orderId)}`
    : '/api/reconciliation/audit-trail'
  return request(path)
}

/**
 * Clear all in-memory audit trail events
 */
export async function clearAuditTrail() {
  return request('/api/reconciliation/audit-trail', {
    method: 'DELETE',
  })
}


/**
 * Browser-native download helper utilizing standard Blob and URL APIs
 * @param {string} endpoint
 * @param {string} fallbackFilename
 */
async function downloadFile(endpoint, fallbackFilename) {
  const response = await fetch(endpoint)
  if (!response.ok) {
    let errorDetail = `Download failed with HTTP ${response.status}`
    try {
      const errJson = await response.json()
      if (errJson.detail) errorDetail = errJson.detail
    } catch {
      // ignore
    }
    const error = new Error(errorDetail)
    error.status = response.status
    throw error
  }

  // Determine filename from Content-Disposition header if available
  let filename = fallbackFilename
  const disposition = response.headers.get('Content-Disposition')
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^";]+)"?/)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  const blob = await response.blob()
  const objectUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.style.display = 'none'
  a.href = objectUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(objectUrl)
  document.body.removeChild(a)
}

/**
 * Download full operational reconciliation ledger as CSV
 */
export async function downloadLedgerCSV() {
  return downloadFile('/api/reconciliation/export/ledger', 'reconciliation_ledger.csv')
}

/**
 * Download active acquirer dispute packet as CSV
 */
export async function downloadDisputesCSV() {
  return downloadFile('/api/reconciliation/export/disputes', 'acquirer_dispute_packet.csv')
}

/**
 * Download single case dispute package as JSON
 * @param {string} orderId
 */
export async function downloadSingleCaseDispute(orderId) {
  return downloadFile(
    `/api/reconciliation/export/disputes/${encodeURIComponent(orderId)}`,
    `dispute_packet_${orderId}.json`
  )
}

/**
 * Download compliance audit trail as CSV
 */
export async function downloadAuditTrailCSV() {
  return downloadFile('/api/reconciliation/export/audit-trail', 'audit_trail.csv')
}


