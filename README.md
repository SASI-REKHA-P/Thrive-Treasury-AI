# Thrive Treasury AI

> **AI-Assisted Treasury Reconciliation & Exception Intelligence**

**Live Demo:** https://thrive-treasury-ai-front.onrender.com/app  
**Backend API:** https://thrive-treasury-ai.onrender.com/docs

---

## 1. Overview

In modern fintech, digital commerce, and treasury operations, payment gateways and acquirers generate transaction-side capture logs, while banking partners and custodial settlement networks produce settlement-side deposit feeds. Discrepancies naturally occur due to payment gateway processing fees (MDR), multi-day settlement windows, cross-currency foreign exchange variances, uncaptured authorizations, and duplicate settlement deposits.

Finance controllers are tasked with identifying variances, investigating root causes, and resolving discrepancies under strict audit and compliance standards.

**Thrive Treasury AI** demonstrates a **deterministic-first** treasury reconciliation platform paired with **selective AI exception investigation** and an **interactive human controller review workflow**. Deterministic financial rules serve as the authoritative source of truth, while an AI investigation copilot provides contextual advisory briefings for ambiguous variances. Every action is captured in an chronological in-memory audit trail with instant export capabilities for banking partner dispute resolution.

---

## 2. Key Capabilities

* **Multi-Source Data Ingestion & Normalization**: Validates heterogeneous payment and settlement payloads into standardized, timezone-aware Decimal data models.
* **Deterministic Reconciliation Engine**: Executes prioritized, rule-based matching logic across exact matches, expected fee deductions, date tolerances, currency mismatches, missing deposits, duplicate settlements, and amount discrepancies.
* **Ground-Truth Benchmark Evaluation**: Validates reconciliation accuracy against an isolated, 120-transaction benchmark dataset without leakage into operational runtime.
* **Selective AI Exception Investigation**: Intelligently routes ambiguous exceptions (amount variances and cross-currency conversions) to an AI investigator while bypassing standard records to minimize token consumption and latency.
* **Human-in-the-Loop Review Workflow**: Empowers finance controllers to review AI hypotheses, approve fee adjustments, apply manual overrides, or escalate banking disputes.
* **Auditable Operational Lifecycle**: Logs every controller review and lifecycle milestone chronologically with timestamp, actor, decision, and notes.
* **Treasury Exports & Dispute Packets**: Generates downloadable full reconciliation ledgers (CSV), acquirer dispute packets (CSV), single-case dispute packages (JSON), and compliance audit trails (CSV).
* **Modern Finance Controller Workspace**: Professional React dashboard providing real-time telemetry, transaction search, rule filtering, detailed slide-over drawers, benchmark evaluation views, and audit logs.
* **REST API Layer**: Clean, documented FastAPI endpoints exposing pipeline runs, metric retrieval, review actions, and export downloads.

---

## 3. Architecture

### Operational Processing Pipeline

```text
Operational Payment Records (120) + Settlement Records (117)
                         ↓
                    Data Loader
                         ↓
                     Normalizer
                         ↓
        Deterministic Reconciliation Engine
       (Authoritative Status, Rule ID, Variance)
                         ↓
            Selective AI Investigation
     (13 Eligible Cases Evaluated as Advisory Only)
                         ↓
            Human Controller Review
     (Approve Advisory | Override | Escalate Dispute)
                         ↓
           Audit Trail & Export Service
                         ↓
                   FastAPI API
                         ↓
        React Finance Controller Dashboard
```

### Isolated Benchmark & Evaluation Flow

```text
       Reconciliation Engine Output
                    ↓
             Batch Evaluator ←─── Ground Truth Benchmark (120 Records)
                    ↓              (Isolated in data/ground_truth_120.json)
Accuracy Metrics (100%) | Confusion Matrix | Category Breakdown
```

> **Ground-Truth Isolation**: The ground-truth benchmark dataset is consumed exclusively by the `BatchEvaluator` to measure performance. The operational reconciliation engine, the AI investigator service, and the export generator never access ground truth.

---

## 4. Deterministic Reconciliation

The deterministic engine is the **sole authoritative source of truth** for:
* Reconciliation Status (`MATCHED`, `EXCEPTION`, `PENDING_REVIEW`)
* Applied Rule Identifier (`RULE_01` through `RULE_08`)
* Quantitative Variance and Deterministic Explanation

The AI investigator operates in a strictly **advisory** capacity. AI hypotheses and confidence scores cannot alter or override the deterministic reconciliation status.

### Selective AI Routing Policy
* **13 of 120 records** are routed for AI investigation:
 * **8 Amount Mismatch Cases (`RULE_08_AMOUNT_MISMATCH`)**: Investigated to distinguish unaccounted merchant processing fees from genuine banking variances. High-confidence cases (confidence ≥ 0.85 and variance ≤ ₹500) may be auto-triaged; lower-confidence or higher-variance cases remain subject to human review. 
  * **5 Cross-Currency Cases (`RULE_04_CROSS_CURRENCY_CHECK`)**: Investigated for Nostro foreign exchange exposure and implied conversion rates. In accordance with treasury risk controls, cross-currency cases remain flagged for **mandatory human controller review**.
* **107 records bypass AI**: Exact matches, standard fee deductions, date tolerances, missing settlements, duplicates, and currency mismatches are resolved deterministically, eliminating token overhead.

---

## 5. Benchmark Results

Evaluated against the synthetic 120-transaction benchmark dataset (`data/ground_truth_120.json`):

| Metric | Benchmark Result |
| :--- | :--- |
| **Total Records Processed** | `120` |
| **Deterministically Matched** | `85` |
| **Flagged Exceptions** | `30` |
| **Pending Controller Review** | `5` |
| **Rule Classification Accuracy** | **`100.00%`** |
| **Status Resolution Accuracy** | **`100.00%`** |
| **Deterministic Resolution Rate** | **`70.83%`** |
| **Selective AI Investigations** | `13` (107 bypassed) |

### Confusion Matrix
* **True Positives (Correctly Matched)**: `85`
* **True Negatives (Correctly Quarantined)**: `35`
* **False Positives (Erroneously Matched)**: `0`
* **False Negatives (Erroneously Quarantined)**: `0`

*(Note: These figures represent benchmark verification on the project's standardized synthetic dataset and do not represent production or live financial results).*

---

## 6. Human Controller Review

For quarantined exceptions and pending reviews, the Finance Controller Dashboard provides an authoritative review workflow:
* **Review AI Advisory**: Controllers inspect the deterministic record alongside the AI root cause analysis, evidence citations, and confidence tiers.
* **Action: `APPROVE_ADVISORY`**: Resolves the workflow item based on verified AI root cause findings.
* **Action: `MANUAL_OVERRIDE`**: Resolves the workflow item with controller audit commentary following out-of-band verification.
* **Action: `ESCALATE_DISPUTE`**: Moves the workflow state to `ESCALATED`, routing the item for formal acquirer dispute generation.
* **Integrity Guard**: Controller actions update `human_review_status` without mutating the underlying deterministic reconciliation status (`status`) or rule (`rule_id`).

---

## 7. Audit Trail

Every state transition and controller action is recorded in an in-memory audit store tracking:
* High-resolution UTC timestamp
* Actor identifier (e.g., `SYSTEM:ORCHESTRATOR`, `Lead Finance Controller`)
* Event type (`BATCH_LOADED`, `DECISION_RECORDED`, etc.)
* Associated transaction `order_id` and rule `rule_id`
* Detailed notes and operational context

The audit trail can be inspected chronologically, filtered by order reference, downloaded as CSV, or cleared via the controller workspace.

---

## 8. Exports

Finance teams can export operational data directly from the dashboard:
* **Reconciliation Ledger (`reconciliation_ledger.csv`)**: Complete 120-record operational reconciliation ledger with exact Decimal amounts, statuses, and AI advisory fields.
* **Acquirer Dispute Packet (`acquirer_dispute_packet.csv`)**: Filtered strictly to transactions that have been explicitly escalated (`ESCALATE_DISPUTE`) by a controller, incorporating controller notes and AI evidence citations.
* **Single-Case Dispute File (`dispute_packet_{order_id}.json`)**: Comprehensive dispute file for an individual escalated case, downloadable from the transaction detail drawer.
* **Compliance Audit Trail (`audit_trail.csv`)**: Chronological audit log of all system and controller activities.

---

## 9. Technology Stack

### Backend
* **Python 3.10+**
* **FastAPI**: Asynchronous REST API framework
* **Pydantic v2**: Strict financial data modeling and validation
* **Uvicorn**: ASGI web server
* **Pytest**: Automated test suite (92 unit and integration tests)
* **HTTPX**: HTTP client for health testing and external AI provider calls

### Frontend
* **React 19**: Interactive single-page interface
* **Vite**: Frontend tooling and development server
* **Lucide React**: Financial and operational iconography
* **Vanilla CSS**: Responsive, tokenized styling system (no heavy UI frameworks)

---

## 10. Project Structure

```text
Thrive-Treasury-AI/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI route controllers (reconciliation, evaluation)
│   │   ├── core/            # Configuration and settings
│   │   ├── models/          # Pydantic schemas (normalized, reconciliation, audit)
│   │   ├── schemas/         # Health schemas
│   │   ├── services/        # Business logic (engine, evaluator, investigator, export, audit)
│   │   └── main.py          # FastAPI application initialization
│   ├── tests/               # 92 automated tests
│   └── requirements.txt     # Python dependencies
├── data/
│   ├── synthetic_batch_120.json   # 120 payments and 117 settlement records
│   └── ground_truth_120.json      # Isolated 120-record benchmark dataset
├── docs/                          # Project documentation
├── frontend/
│   ├── src/
│   │   ├── api/             # API client and browser download helpers
│   │   ├── components/      # React components (Dashboard, Drawers, Modals, Views)
│   │   ├── App.jsx          # Root view and routing
│   │   └── main.jsx         # React application entry point
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       # Vite proxy configuration (/api -> :8000)
├── .gitignore
└── README.md
```

---

## 11. Quick Start

### Prerequisites
* Python 3.10 or higher
* Node.js 18 or higher (with npm)

### Step 1: Start Backend (Terminal 1)

```powershell
cd C:\Users\sasir\OneDrive\Desktop\Thrive-Treasury-AI\backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

*The backend API will be available at `http://127.0.0.1:8000` (interactive Swagger documentation at `http://127.0.0.1:8000/docs`).*

### Step 2: Start Frontend (Terminal 2)

```powershell
cd C:\Users\sasir\OneDrive\Desktop\Thrive-Treasury-AI\frontend
npm install
npm run dev
```

*The React frontend will launch on `http://localhost:5173`. Navigate to `http://localhost:5173/app` to access the Finance Controller Workspace.*

*(Note: The frontend automatically routes `/api` requests to `http://localhost:8000` through the Vite proxy. For optional live Google Gemini AI calls, set the `GEMINI_API_KEY` environment variable in your terminal session before starting the backend).*

---

## 12. Testing

### Run Backend Tests (92 Tests Passing)
```powershell
cd C:\Users\sasir\OneDrive\Desktop\Thrive-Treasury-AI\backend
pytest -v
```

### Run Frontend Linting & Production Build
```powershell
cd C:\Users\sasir\OneDrive\Desktop\Thrive-Treasury-AI\frontend
npm run lint
npm run build
```

---

## 13. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System liveness health check |
| `POST` | `/api/reconciliation/run` | Triggers the complete reconciliation pipeline |
| `GET` | `/api/reconciliation/transactions` | Retrieves operational reconciliation results with filtering |
| `GET` | `/api/reconciliation/transactions/{order_id}` | Retrieves an individual transaction result by Order ID |
| `GET` | `/api/investigations/{order_id}` | Retrieves AI investigation briefing for an eligible order |
| `GET` | `/api/evaluation/metrics` | Computes benchmark metrics against isolated ground truth |
| `POST` | `/api/reconciliation/review/{order_id}` | Records an authoritative controller review decision |
| `GET` | `/api/reconciliation/audit-trail` | Retrieves chronological audit trail events |
| `DELETE` | `/api/reconciliation/audit-trail` | Resets the in-memory audit event log |
| `GET` | `/api/reconciliation/export/ledger` | Downloads full reconciliation ledger CSV |
| `GET` | `/api/reconciliation/export/disputes` | Downloads acquirer dispute packet CSV (escalated cases) |
| `GET` | `/api/reconciliation/export/disputes/{order_id}` | Downloads single-case dispute file JSON |
| `GET` | `/api/reconciliation/export/audit-trail` | Downloads compliance audit trail CSV |

---

## 14. Safety & Design Principles

1. **Deterministic-First Foundation**: Financial statuses and numerical variances are established strictly by deterministic rules.
2. **Advisory-Only AI**: Machine learning and LLM outputs are confined to hypothesis generation and evidence synthesis. AI cannot silently alter financial records.
3. **Ground-Truth Isolation**: Operational services cannot access or leak benchmark answers.
4. **Mandatory Human Review for High-Risk Cases**: Cross-currency Nostro clearing cases (`RULE_04`) are restricted from auto-clearance.
5. **Auditable Controller Actions**: Every controller override or escalation creates a timestamped event.
6. **Synthetic Benchmark Data**: All batch records are synthetic; no production data or personally identifiable information is used.
7. **Zero Hardcoded Secrets**: No credentials, API tokens, or keys are committed to source control.

---

## 15. Current MVP Limitations

* **In-Memory State**: Pipeline state and audit logs are retained in memory during process execution and reset when the backend process restarts.
* **Single-Tenant Scope**: Multi-tenant isolation and user authentication (RBAC / JWT) are omitted in this MVP.
* **Synthetic Datasets**: The demo operates on a synthetic 120-transaction batch designed for standardized evaluation.
* **Demonstration Platform**: This repository is a buildathon proof-of-concept demonstrating architecture and workflows rather than a certified production accounting system.

---

## 16. Demo Walkthrough

1. **Access Workspace**: Open `http://localhost:5173/app` in your browser.
2. **Run Reconciliation**: Click **"Run Reconciliation"** to execute the pipeline.
3. **Verify Clearance**: Confirm telemetry cards display **120 Total Transactions**, **85 Matched (70.83% auto-cleared)**, **30 Exceptions**, and **5 Pending Review**.
4. **Filter AI Investigations**: Toggle the **"AI Investigated"** filter to isolate the 13 cases routed for advisory analysis.
5. **Inspect Cross-Currency Case**: Select transaction `ORD-8494` (Rule 04 Nostro Cross-Currency).
6. **Review Findings**: Inspect the deterministic checks and amounts, followed by the separate **AI Advisory Brief** highlighting foreign exchange exposure.
7. **Execute Controller Decision**: Click **"Escalate Acquirer Dispute"**, enter a review note, and confirm.
8. **Observe Queue Progression**: Watch the controller action queue dynamically update ($35 \to 34$ remaining).
9. **Review Audit Trail**: Switch to the **"Audit Trail"** tab to view the immutable logged decision event with actor, timestamp, and notes.
10. **Inspect Benchmark Accuracy**: Open the **"Evaluation & Benchmark"** tab to verify the **100% Rule and Status Accuracy** against ground truth.
11. **Download Dispute Packet**: Click **"Export" $\to$ "Acquirer Dispute Packet (CSV)"** in the header to download the generated banking dispute document containing your escalated case.
