/**
 * Thrive Treasury AI - Demonstration Dataset
 * Labeled strictly for frontend architectural simulation.
 * This is demonstration data only, not actual system performance metrics.
 */

export const DEMO_BATCH_META = {
  batchId: 'BATCH-2026-DEMO',
  tag: 'Sample Batch #2026-DEMO · Demonstration Data Only',
  description: 'Sample multi-source batch containing 3 representative transaction cases',
}

export const DEMO_RECORDS = {
  recordA: {
    id: 'rec-a',
    orderId: 'ORD-8492',
    description: 'Standard Gateway Checkout',
    paymentAmount: '₹4,200.00',
    settlementAmount: '₹4,200.00',
    difference: '₹0.00',
    result: 'MATCHED',
    rule: 'Rule #01 · Exact Match',
    aiUsed: 'No',
    status: 'matched',
    confidence: 'High Confidence',
    takeaway: 'Straightforward records don\'t need AI.',
  },
  recordB: {
    id: 'rec-b',
    orderId: 'ORD-8493',
    description: 'Enterprise Subscription',
    paymentAmount: '₹15,000.00',
    settlementAmount: '₹14,646.00',
    difference: '-₹354.00',
    result: 'AI INVESTIGATED',
    status: 'ai_investigated',
    confidence: 'High Confidence',
    aiUsed: 'Yes',
    breakdown: {
      mdrRate: '2.0%',
      mdrAmount: '₹300.00',
      gstRate: '18% on MDR',
      gstAmount: '₹54.00',
      totalExplained: '₹354.00',
    },
    aiExplanation:
      'The settlement difference aligns with a 2.0% MDR of ₹300.00 plus 18% GST on the MDR of ₹54.00, explaining the ₹354.00 variance.',
    takeaway: 'AI investigates the ambiguity.',
  },
  recordC: {
    id: 'rec-c',
    orderId: 'ORD-8494',
    description: 'Cross-Border Consultation',
    paymentAmount: '$500.00 USD',
    settlementAmount: '₹41,200.00 INR',
    settlementRate: '82.40',
    bookingRate: '83.10',
    settlementDelay: '48h',
    difference: 'FX Rate Divergence',
    result: 'REVIEW REQUIRED',
    status: 'human_review',
    confidence: 'Review Required',
    aiUsed: 'Yes (Confidence Insufficient)',
    reason:
      'Exchange-rate timing creates an ambiguity that requires human review.',
    takeaway: 'When confidence isn\'t enough, a human decides.',
  },
}

export const SIMULATION_STEPS = [
  {
    stepNumber: '01',
    id: 'ingest',
    label: 'Ingest',
    title: 'Financial Feeds Ingested',
    headline: 'Financial data doesn\'t always agree.',
    description:
      'Payment records from checkout gateways and settlement journals from banking partners arrive in varying formats, timezones, and batch frequencies.',
    systemState: 'Preparing demonstration records · Comparing payment and settlement records',
  },
  {
    stepNumber: '02',
    id: 'match',
    label: 'Deterministic Match',
    title: 'Deterministic Rules Applied',
    headline: 'Straightforward records don\'t need AI.',
    description:
      'Order ORD-8492 pairs ₹4,200.00 with ₹4,200.00. Rule #01 (Exact Match) evaluates instantly. No AI required.',
    systemState: 'Applying deterministic rules · Exact match identified',
  },
  {
    stepNumber: '03',
    id: 'discrepancy',
    label: 'Exception Detected',
    title: 'Discrepancy Isolated',
    headline: 'But what happens when they don\'t match?',
    description:
      'Order ORD-8493 records a payment of ₹15,000.00 against a settlement deposit of ₹14,646.00. The engine flags a -₹354.00 variance.',
    systemState: 'Exception detected · Discrepancy isolated for investigation',
  },
  {
    stepNumber: '04',
    id: 'ai_analysis',
    label: 'AI Investigation',
    title: 'Contextual AI Investigation',
    headline: 'AI investigates the ambiguity.',
    description:
      'The AI engine examines processing schedules: 2.0% MDR (₹300.00) plus 18% GST (₹54.00) perfectly explains the -₹354.00 variance with high confidence.',
    systemState: 'AI investigating · Discrepancy context generated',
  },
  {
    stepNumber: '05',
    id: 'human_review',
    label: 'Human Review',
    title: 'Human Review Escalation',
    headline: 'When confidence isn\'t enough, a human decides.',
    description:
      'Order ORD-8494 displays an FX conversion variance (rate 82.40 vs 83.10) over a 48h settlement delay. The ambiguity threshold routes it directly to the treasury review queue.',
    systemState: 'Review required · Escalated to treasury queue',
  },
  {
    stepNumber: '06',
    id: 'audit',
    label: 'Resolution & Audit',
    title: 'Audited Reconciliation State',
    headline: 'A clear reconciliation state, ready for review and audit.',
    description:
      'Three records, three appropriate outcomes: 1 Matched deterministically, 1 AI Investigated with full fee context, 1 Escalated for human oversight.',
    systemState: 'Demo reconciliation complete · Ready for review and audit',
  },
]
