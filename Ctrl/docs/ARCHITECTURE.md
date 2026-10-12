# Architecture — WanderWallet

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                  WanderWallet                          │
│              KogniVera Hackathon 2026                   │
└─────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  FRONTEND (frontend/src/)                          │
│  HTML5 + Vanilla CSS + Vanilla JS                  │
│                                                    │
│  Pages:                                            │
│  • Dashboard    — KPI cards, budget ring,          │
│                   category bars, recent expenses   │
│  • Expenses     — Full list with FX badges         │
│  • Budget       — Set caps, live cap status        │
│  • Settlement   — Balance matrix + transactions    │
│  • AI Features  — OCR, NL, Forecast, CFO Chat      │
│                                                    │
│  Components:                                       │
│  • Breach Alert Banners (dismissible, persistent)  │
│  • Add Expense Modal (with FX conversion preview)  │
│  • Toast Notification System                       │
└──────────────────┬─────────────────────────────────┘
                   │ HTTP (JSON REST API)
                   │ CORS from file:// and localhost
                   ▼
┌────────────────────────────────────────────────────┐
│  BACKEND (backend/src/)                            │
│  Python 3.11 + Flask 3.x                          │
│                                                    │
│  REST Endpoints:                                   │
│  GET  /api/health                                  │
│  GET  /api/trips/                                  │
│  POST /api/trips/                                  │
│  GET  /api/dashboard/:trip_id                      │
│  GET  /api/expenses/?trip_id=                      │
│  POST /api/expenses/           ← FX + breach check│
│  GET  /api/budgets/:trip_id                        │
│  POST /api/budgets/                                │
│  GET  /api/fx/rates?target=INR                     │
│  GET  /api/fx/convert?from=USD&to=INR&amount=55    │
│  GET  /api/settlement/:trip_id                     │
│  POST /api/ai/ocr                                  │
│  POST /api/ai/parse-nl                             │
│  GET  /api/ai/forecast/:trip_id                    │
│  POST /api/ai/cfo-chat                             │
│                                                    │
│  Core Services:                                    │
│  • breach_detector.py   — Decimal math cap check   │
│  • fx_service.py        — Multi-currency conversion│
│  • settlement_service.py — Greedy balance settle   │
└──────────────────┬─────────────────────────────────┘
                   │ Supabase PostgreSQL (or SQLite3 fallback)
                   │ decimal.Decimal arithmetic
                   ▼
┌────────────────────────────────────────────────────┐
│  DATA LAYER (data-model/ + Supabase)               │
│  • Supabase PostgreSQL (Live cloud database)       │
│  • SQLite 3 — tripwallet.db (offline fallback)     │
│                                                    │
│  14 canonical tables (PS-08 schema)                │
│  • users, trips, trip_members                      │
│  • budgets (+ category caps extension)             │
│  • expenses (+ home_amount, fx_rate_used)          │
│  • expense_splits                                  │
│  • fx_rates, currencies, countries, cities         │
│  • receipts (+ OCR fields)                         │
│  • itineraries, itinerary_items                    │
│  • languages                                       │
│                                                    │
│  Seed: Goa Trip 2026 + global demo destinations   │
└──────────────────┬─────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│  AI LAYER (ai/ + backend/src/routes/ai_routes.py)  │
│                                                    │
│  1. Receipt OCR (ai_routes.py → /api/ai/ocr)       │
│     • Tesseract.js (if installed)                  │
│     • Pattern-matching fallback (regex)            │
│     • Outputs: merchant, amount, currency, date,   │
│       category, confidence score                   │
│                                                    │
│  2. NL Expense Parser (/api/ai/parse-nl)           │
│     • Regex + keyword tokenizer                    │
│     • Resolves member names from trip_members DB   │
│     • Parses: "₹1500 dinner split with Lavanya"    │
│                                                    │
│  3. Spend Forecasting (/api/ai/forecast/:id)       │
│     • Recency-weighted burn rate algorithm         │
│     • Projects end-of-trip total spend             │
│     • Risk levels: low/medium/high/critical        │
│                                                    │
│  4. CFO Chat (/api/ai/cfo-chat)                    │
│     • Rule-based NLU with intent detection         │
│     • Grounded in real DB numbers (no hallucination│
│     • Handles: can I afford, budget status,        │
│       breach status, spending advice               │
└────────────────────────────────────────────────────┘
```

## Data Flow: Adding a Foreign-Currency Expense

```
User submits: $55 USD food expense
     │
     ▼
POST /api/expenses/
     │
     ├─ 1. Validate amount > 0, category valid
     │
     ├─ 2. FX Conversion (fx_service.py)
     │      Lookup fx_rates: USD→INR @ 83.500000
     │      home_amount = Decimal('55.00') × Decimal('83.500000')
     │                  = Decimal('4592.50')  ← exact, no float drift
     │
     ├─ 3. Breach Preview (breach_detector.py)
     │      current food spend = ₹2,500.00
     │      + new home_amount  = ₹4,592.50
     │      total food         = ₹7,092.50
     │      food_cap           = ₹6,000.00
     │      overshoot          = ₹1,092.50  ← BREACH!
     │
     ├─ 4. INSERT into expenses (with home_amount, fx_rate_used)
     │
     ├─ 5. CREATE expense_splits (largest-remainder equal split)
     │
     └─ 6. Return breach alert payload:
            {
              "alert": true,
              "category": "food",
              "category_cap": 6000.00,
              "current_spend": 7092.50,
              "overshoot": 1092.50,
              "message": "FOOD CAP BREACHED! ..."
            }
```

## Technology Choices

| Layer | Technology | Why |
|---|---|---|
| Frontend | HTML + Vanilla CSS + Vanilla JS | Zero build deps, file:// runnable, instant demo |
| Backend | Python 3.11 + Flask 3.x | Available on Mac without install, fast to run |
| Database | SQLite 3 (WAL mode) | Zero server, easy seed, portable |
| Money math | `decimal.Decimal` | Exact precision, no IEEE float drift (R3) |
| ORM | Raw SQLite3 driver | Full control, no ORM schema drift |
| OCR | Tesseract + Pattern regex | Tesseract if installed, regex fallback always works |
| Styles | Vanilla CSS custom properties | No build step, portable |
