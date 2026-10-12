# WanderWallet 💰✈️

**KogniVera Hackathon 2026** | **Team CtrlFreaks** | **MVJ College of Engineering**

[![PS-08](https://img.shields.io/badge/Problem%20Statement-PS--08%20WanderWallet-burgundy)](.)
[![Python](https://img.shields.io/badge/Backend-Python%203.11%20+%20Flask-blue)](.)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Hard%20Proof-green)](.)

---

## 1. Team & Problem Statement

| Field | Value |
|---|---|
| **Team** | CtrlFreaks |
| **College** | MVJ College of Engineering, Bengaluru |
| **PS ID** | PS-08 |
| **PS Title** | WanderWallet — Smart Budget & Expense Companion |
| **Repository** | `kv-hack2026-ctrl-freaks` |

**Members:** Anil Kumar · Lavanya Sharma · Rahul Menon · Priya Nair

---

## 2. What We Built

- ✅ **Add expenses** with category, currency (INR/USD/EUR/GBP/THB), payer — every foreign-currency expense is converted to home currency via `fx_rates` using `decimal.Decimal` (zero float drift)
- ✅ **Category Caps & Breach Alert (Mandatory Enhancement)** — per-category caps (food/transport/accommodation/activities/misc) with visible, dismissible alert naming category, cap, spend, and overshoot; demo proves breach via USD food expense
- ✅ **Group cost-splitting** — equal and custom splits using Largest-Remainder method; per-person balances; greedy settlement transaction minimizer
- ✅ **Multi-currency live conversion** — FX rates table (INR, USD, EUR, GBP, THB, SGD); convert endpoint
- ✅ **Budget-vs-actual view** — animated budget ring, category bar chart, daily spend trend, KPI cards with remaining/overshoot
- ✅ **AI Receipt OCR** — Tesseract.js + pattern-regex fallback; extracts merchant, amount, currency, date, category; pre-fills expense form
- ✅ **AI Natural Language Entry** — parse "₹1500 dinner split with Lavanya and Rahul" → structured expense with member resolution
- ✅ **AI Spend Forecasting** — recency-weighted daily burn rate → projected end-of-trip total + risk level (low/medium/high/critical)
- ✅ **AI Travel CFO Chat** — grounded Q&A ("Can I afford scuba?") using exact DB numbers, no hallucination

---

## 3. Architecture

```
Frontend (HTML + CSS + JS, file:// or localhost:3000)
    ↕ JSON REST API (CORS)
Backend (Python 3.11 + Flask 3.x, localhost:5001)
    ├── breach_detector.py  — decimal.Decimal cap math
    ├── fx_service.py       — currency conversion
    └── settlement_service.py
    ↕ Supabase PostgreSQL (Live cloud DB) / SQLite3 (offline fallback)
Data Model (14 canonical PS-08 tables)
    + AI Layer (OCR / NL Parser / Forecast / CFO Chat)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full diagram and data flow.

---

## 4. Data Model

All **14 canonical PS-08 tables** used, field names unchanged (R1):

| Table | Prefix | Role |
|---|---|---|
| `languages` | `lng_` | BCP-47 language support |
| `currencies` | `cur_` | ISO-4217 currencies |
| `countries` | `cnt_` | Country master (WGS-84 coords) |
| `cities` | `cty_` | City master |
| `users` | `usr_` | Registered travellers |
| `trips` | `trp_` | Trip metadata |
| `trip_members` | `tmb_` | Group membership |
| **`budgets`** | `bud_` | **Extended: + 5 category cap columns** |
| `fx_rates` | `fxr_` | FX rate snapshots (6dp) |
| **`expenses`** | `exp_` | **Extended: + home_amount, fx_rate_used** |
| `expense_splits` | `spl_` | Per-person equal/custom splits |
| `receipts` | `rcp_` | OCR receipt images + extracted fields |
| `itineraries` | `itn_` | Day-by-day trip plan |
| `itinerary_items` | `itm_` | Individual activities |

**Extensions documented in** [data-model/DATA_MODEL.md](data-model/DATA_MODEL.md).

**Boundary rules enforced in code:** `exp_amount > 0`, `bud_total_amount > 0`, `alert_threshold_pct 1–100`, `spl_share_amount >= 0`, all FX rates > 0 — see `backend/src/middleware/validators.py` and `tests/hard_proof.test.py`.

---

## 5. AI Features

| Feature | Mechanism | Grounding |
|---|---|---|
| **Receipt OCR** | Tesseract + regex pattern extractor | Processes actual image pixels; regex extracts amounts via known receipt layouts |
| **NL Expense Entry** | Regex tokenizer + keyword NLU | Resolves member names against `trip_members` table; parses currency symbols, amounts, categories from free text |
| **Spend Forecasting** | Recency-weighted burn rate algorithm | Uses actual `expenses` daily aggregates from DB; projects remaining×burn_rate |
| **CFO Chat** | Rule-based intent engine + DB-grounded numbers | All amounts pulled from live DB; no LLM hallucination — deterministic rule dispatch |

---

## 6. Run It Locally

### Prerequisites
- Python 3.11+ (`python3 --version`)
- SQLite3 (bundled with Python)
- Optional: Tesseract OCR (`brew install tesseract` on Mac)

### Steps

```bash
# 1. Clone
git clone https://github.com/mvj-ce/kv-hack2026-ctrl-freaks.git
cd kv-hack2026-ctrl-freaks

# 2. Setup environment
cp .env.example .env

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Start backend (auto-creates + seeds DB on first run)
cd backend/src
python3 app.py
# → Connected to Supabase PostgreSQL (or local SQLite fallback)
# → API running at http://localhost:5001 (port 5000 reserved by macOS AirPlay)

# 5. Open frontend (in a new terminal)
cd ../../frontend/src
python3 -m http.server 3000
# → Open http://localhost:3000

# OR open frontend/src/index.html directly in browser (file:// works)
```

---

## 7. Demo Path

> **Goal**: Show a per-category cap being breached by a foreign-currency expense.

1. Open **http://localhost:3000** → Dashboard shows **Goa Trip 2026** with pre-seeded data
2. **Budget tab** → See food cap = ₹6,000 · accommodation cap = ₹18,000 (already set in seed)
3. **Dashboard** → Observe 🔴 Breach Banner: *"FOOD CAP BREACHED! Spent ₹7,092.50 against cap of ₹6,000.00 (Overshoot: ₹1,092.50)"*
4. **Expenses tab** → See "Fancy Seafood Dinner (USD)" — $55.00 USD = ₹4,592.50 @ 83.50 rate, badge shows "FX"
5. **+ Add Expense** → Enter $30 USD food expense → submitting shows fresh breach alert with updated numbers
6. **AI Features tab** → Click *"Try Demo Receipt"* → OCR extracts merchant/amount/category; click *"Use This in Expense Form"*
7. Type `"₹1500 lunch split with Lavanya and Rahul"` → NL parser resolves names, opens pre-filled form
8. Ask CFO: *"Can I afford a ₹2000 spa session?"* → Gets exact remaining balance answer
9. **Settlement tab** → Click *"Calculate Settlement"* → See who owes whom with minimum transactions

---

## 8. Tests / Proof

### Run All Tests

```bash
cd /path/to/kv-hack2026-ctrl-freaks
python3 -m pytest tests/hard_proof.test.py -v
```

### Hard Proof Test Coverage

| Test Class | What It Proves |
|---|---|
| `TestFXConversionAccuracy` | USD $55 × 83.50 = ₹4,592.50 exactly (Decimal, not float) |
| `TestCategoryCapBreach` | **HARD PROOF**: USD expense triggers food cap breach; alert names category/cap/spend/overshoot |
| `TestBoundaryRules` | `amount > 0`, `threshold 1–100`, splits ≥ 0, soft deletes (R8) |
| `TestDataModelConformance` | All 14 tables exist; prefixed IDs (R2); BCP-47 langs; ISO-4217 currencies; WGS-84 coords (R7) |
| `TestSettlement` | Split sums equal expense home_amount (±₹0.01 largest-remainder) |

### Expected Output

```
tests/hard_proof.test.py::TestFXConversionAccuracy::test_usd_to_inr_conversion_exact PASSED
tests/hard_proof.test.py::TestFXConversionAccuracy::test_eur_to_inr_conversion_exact PASSED
tests/hard_proof.test.py::TestFXConversionAccuracy::test_inr_to_inr_rate_is_one PASSED
tests/hard_proof.test.py::TestFXConversionAccuracy::test_fx_rate_stored_as_6dp PASSED
tests/hard_proof.test.py::TestFXConversionAccuracy::test_seed_usd_expense_home_amount PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_food_cap_is_set PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_food_category_total_includes_usd_expense PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_food_spend_exceeds_cap PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_overshoot_arithmetic PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_breach_alert_payload_structure PASSED
tests/hard_proof.test.py::TestCategoryCapBreach::test_foreign_currency_expense_triggers_breach PASSED
tests/hard_proof.test.py::TestBoundaryRules::... PASSED (6 tests)
tests/hard_proof.test.py::TestDataModelConformance::... PASSED (6 tests)
tests/hard_proof.test.py::TestSettlement::test_total_splits_equal_expense_home_amount PASSED

======== 22 passed in 0.XXs ========
```

### The Hard Proof Statement

> **Food cap (₹6,000.00) is breached by adding a USD $55.00 foreign-currency dinner expense.**
> Converted at FX rate 83.500000 → ₹4,592.50 (exact Decimal arithmetic).
> Food total = ₹2,500.00 (INR lunch) + ₹4,592.50 (USD dinner) = **₹7,092.50**.
> Alert fires naming: category=food, cap=₹6,000.00, spend=₹7,092.50, overshoot=₹1,092.50.
> Without the USD expense, food (₹2,500) is within cap. The foreign-currency expense is the trigger.
