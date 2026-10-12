# Data Model — WanderWallet (PS-08)

## Canonical Tables Used (D1–D14)

| # | Table | Prefix | Purpose |
|---|-------|--------|---------|
| D1 | `languages` | `lng_` | BCP-47 language support |
| D2 | `currencies` | `cur_` | ISO-4217 currencies |
| D3 | `countries` | `cnt_` | Country master |
| D4 | `cities` | `cty_` | City master with WGS-84 coords |
| D5 | `users` | `usr_` | Registered travellers |
| D6 | `trips` | `trp_` | Trip metadata |
| D7 | `trip_members` | `tmb_` | Who is on each trip |
| D8 | `budgets` | `bud_` | Budget + per-category caps *(extended)* |
| D9 | `fx_rates` | `fxr_` | FX rate snapshots |
| D10 | `expenses` | `exp_` | Individual expense records |
| D11 | `expense_splits` | `spl_` | Per-person splits |
| D12 | `receipts` | `rcp_` | OCR receipt images |
| D13 | `itineraries` | `itn_` | Day-by-day itinerary |
| D14 | `itinerary_items` | `itm_` | Individual itinerary activities |

## Extensions (New Columns Added — R1 Compliant)

### `budgets` — Mandatory Enhancement: Category Caps

| Column | Type | Reason |
|--------|------|--------|
| `bud_accommodation_cap` | `DECIMAL(12,2)` | Per-category spend cap for accommodation |
| `bud_transport_cap` | `DECIMAL(12,2)` | Per-category spend cap for transport |
| `bud_food_cap` | `DECIMAL(12,2)` | Per-category spend cap for food/dining |
| `bud_activities_cap` | `DECIMAL(12,2)` | Per-category spend cap for activities |
| `bud_misc_cap` | `DECIMAL(12,2)` | Per-category spend cap for miscellaneous |
| `bud_alert_threshold_pct` | `DECIMAL(5,2)` | % of cap at which breach alert fires (default 80%) |

### `expenses` — AI Traceability

| Column | Type | Reason |
|--------|------|--------|
| `exp_home_amount` | `DECIMAL(12,2)` | Converted amount in trip home currency |
| `exp_home_currency` | `TEXT` | Trip home currency code |
| `exp_fx_rate_id` | `TEXT` | FK to `fx_rates` record used for conversion |
| `exp_fx_rate_used` | `DECIMAL(18,6)` | Snapshot of rate at time of entry (immutable) |
| `exp_entered_via` | `TEXT` | `manual`, `ocr`, `nl_parse`, `import` |
| `exp_source_text` | `TEXT` | Raw NL input (for NL-parse traceability) |

### `receipts` — OCR Fields

| Column | Type | Reason |
|--------|------|--------|
| `rcp_image_data` | `TEXT` | Base64 image for demo (no CDN dependency) |
| `rcp_ocr_raw_text` | `TEXT` | Full OCR text output from Tesseract |
| `rcp_ocr_merchant` | `TEXT` | Extracted merchant name |
| `rcp_ocr_amount` | `DECIMAL(12,2)` | Extracted amount |
| `rcp_ocr_currency` | `TEXT` | Extracted currency code |
| `rcp_ocr_date` | `TEXT` | Extracted date |
| `rcp_ocr_category` | `TEXT` | Inferred category |
| `rcp_ocr_confidence` | `DECIMAL(5,2)` | Extraction confidence 0–100 |
| `rcp_ocr_processed_at` | `TEXT` | ISO-8601 timestamp of processing |

## Data Rules Enforced

| Rule | How Enforced |
|------|-------------|
| R1 (No deletions) | All canonical columns preserved; only additive |
| R2 (Prefixed IDs) | `usr_`, `trp_`, `bud_`, `exp_`, `spl_`, `tmb_`, `fxr_`, `rcp_`, `cur_`, `cnt_`, `cty_`, `lng_`, `itn_`, `itm_` |
| R3 (Decimal money) | `DECIMAL(12,2)` for all amounts; `bignumber.js` in backend math |
| R4 (ISO-8601 dates) | `_at` fields = ISO-8601 with offset; `_date` fields = zoneless date string |
| R5 (Snake case enums) | All CHECK constraints use lowercase snake_case values |
| R6 (BCP-47 languages) | `lng_code` enforced as BCP-47: `en-IN`, `hi-IN`, `kn-IN` |
| R7 (WGS-84 coords) | `lat`/`lng` stored as REAL to 6 decimal places |
| R8 (Soft deletes) | All tables use `status` column + `updated_at`; no DELETE statements in business logic |

## Boundary Rules Enforced in Code

| Rule | Location | Test |
|------|----------|------|
| `exp_amount > 0` | SQL CHECK + `backend/src/middleware/validators.js` | `tests/boundary.test.py` |
| `bud_total_amount > 0` | SQL CHECK + budget validator | `tests/boundary.test.py` |
| `bud_alert_threshold_pct BETWEEN 1 AND 100` | SQL CHECK + budget validator | `tests/boundary.test.py` |
| Category cap breach alert | `backend/src/services/breach_detector.py` | `tests/hard_proof.test.py` |
| FX conversion precision | `backend/src/services/fx_service.py` using `decimal.Decimal` | `tests/hard_proof.test.py` |
| `spl_share_amount >= 0` | SQL CHECK + split validator | `tests/boundary.test.py` |

## Demo Scenario: Food Cap Breach

```
Trip: Goa Trip 2026 (home currency: INR)
Budget food_cap: ₹6,000.00
Alert threshold: 80% = ₹4,800.00

Expense 1: Lunch at Beach Shack     ₹2,500.00 INR   → food total: ₹2,500.00  (OK)
Expense 2: Fancy Seafood Dinner     $55.00 USD       
           Converted: 55 × 83.50   = ₹4,592.50 INR  → food total: ₹7,092.50  ← BREACH!
           
Alert fired:
  category:      food
  cap:           ₹6,000.00
  current_spend: ₹7,092.50
  overshoot:     ₹1,092.50
  message:       "FOOD CAP BREACHED! Spent ₹7,092.50 against cap of ₹6,000.00 (Overshoot: ₹1,092.50)"
```
