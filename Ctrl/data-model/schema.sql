-- =============================================================
--  WanderWallet — Canonical Data Model (PS-08)
--  All 14 canonical tables. Field names unchanged (R1).
--  Money: DECIMAL(12,2) + ISO-4217 code (R3).
--  Timestamps: _at fields (R4). Dates: _date fields (R4).
--  Soft deletes via status + updated_at (R8).
--  Prefixed opaque IDs (R2). Snake_case enums (R5).
--  WGS-84 lat/lng to 6dp (R7). BCP-47 language tags (R6).
-- =============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─── D1: languages ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS languages (
    lng_id          TEXT        PRIMARY KEY,          -- e.g. 'lng_en_in'
    lng_code        TEXT        NOT NULL UNIQUE,      -- BCP-47: 'en-IN'
    lng_name        TEXT        NOT NULL,
    lng_native_name TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','inactive')),
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D2: currencies ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS currencies (
    cur_id          TEXT        PRIMARY KEY,          -- e.g. 'cur_inr'
    cur_code        TEXT        NOT NULL UNIQUE,      -- ISO-4217: 'INR'
    cur_name        TEXT        NOT NULL,
    cur_symbol      TEXT        NOT NULL,
    cur_decimal_places INTEGER  NOT NULL DEFAULT 2,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','inactive')),
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D3: countries ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS countries (
    cnt_id          TEXT        PRIMARY KEY,          -- e.g. 'cnt_in'
    cnt_code        TEXT        NOT NULL UNIQUE,      -- ISO-3166-1 alpha-2
    cnt_name        TEXT        NOT NULL,
    cnt_currency_id TEXT        REFERENCES currencies(cur_id),
    cnt_lat         REAL,                             -- WGS-84, 6dp
    cnt_lng         REAL,                             -- WGS-84, 6dp
    status          TEXT        NOT NULL DEFAULT 'active',
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D4: cities ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cities (
    cty_id          TEXT        PRIMARY KEY,          -- e.g. 'cty_blr'
    cty_name        TEXT        NOT NULL,
    cty_country_id  TEXT        NOT NULL REFERENCES countries(cnt_id),
    cty_lat         REAL,                             -- WGS-84, 6dp
    cty_lng         REAL,                             -- WGS-84, 6dp
    status          TEXT        NOT NULL DEFAULT 'active',
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D5: users ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    usr_id              TEXT    PRIMARY KEY,          -- e.g. 'usr_anil_001'
    usr_name            TEXT    NOT NULL,
    usr_email           TEXT    NOT NULL UNIQUE,
    usr_phone           TEXT,
    usr_avatar_url      TEXT,
    usr_home_currency   TEXT    NOT NULL DEFAULT 'INR' REFERENCES currencies(cur_code),
    usr_language_id     TEXT    REFERENCES languages(lng_id),
    usr_preferred_lang  TEXT    NOT NULL DEFAULT 'en-IN',    -- BCP-47
    status              TEXT    NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','inactive','suspended')),
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D6: trips ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trips (
    trp_id              TEXT    PRIMARY KEY,          -- e.g. 'trp_goa_2026'
    trp_name            TEXT    NOT NULL,
    trp_owner_id        TEXT    NOT NULL REFERENCES users(usr_id),
    trp_destination     TEXT    NOT NULL,
    trp_city_id         TEXT    REFERENCES cities(cty_id),
    trp_home_currency   TEXT    NOT NULL DEFAULT 'INR',
    trp_start_date      TEXT    NOT NULL,             -- ISO-8601 date (zoneless)
    trp_end_date        TEXT    NOT NULL,
    trp_cover_url       TEXT,
    trp_description     TEXT,
    status              TEXT    NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','completed','cancelled','draft')),
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D7: trip_members ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS trip_members (
    tmb_id          TEXT        PRIMARY KEY,
    tmb_trip_id     TEXT        NOT NULL REFERENCES trips(trp_id),
    tmb_user_id     TEXT        NOT NULL REFERENCES users(usr_id),
    tmb_role        TEXT        NOT NULL DEFAULT 'member'
                                CHECK(tmb_role IN ('owner','admin','member')),
    tmb_joined_at   TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','left','removed')),
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(tmb_trip_id, tmb_user_id)
);

-- ─── D8: budgets ─────────────────────────────────────────────
--  Core + mandatory Category Caps extension
CREATE TABLE IF NOT EXISTS budgets (
    bud_id                  TEXT        PRIMARY KEY,
    bud_trip_id             TEXT        NOT NULL UNIQUE REFERENCES trips(trp_id),
    bud_total_amount        DECIMAL(12,2) NOT NULL CHECK(bud_total_amount > 0),
    bud_currency            TEXT        NOT NULL DEFAULT 'INR',
    -- Category caps (Mandatory Enhancement)
    bud_accommodation_cap   DECIMAL(12,2) DEFAULT NULL,
    bud_transport_cap       DECIMAL(12,2) DEFAULT NULL,
    bud_food_cap            DECIMAL(12,2) DEFAULT NULL,
    bud_activities_cap      DECIMAL(12,2) DEFAULT NULL,
    bud_misc_cap            DECIMAL(12,2) DEFAULT NULL,
    bud_alert_threshold_pct DECIMAL(5,2)  NOT NULL DEFAULT 80.00
                                CHECK(bud_alert_threshold_pct BETWEEN 1 AND 100),
    bud_notes               TEXT,
    status                  TEXT        NOT NULL DEFAULT 'active'
                                CHECK(status IN ('active','archived')),
    created_at              TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at              TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D9: fx_rates ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fx_rates (
    fxr_id              TEXT        PRIMARY KEY,
    fxr_from_currency   TEXT        NOT NULL,         -- ISO-4217
    fxr_to_currency     TEXT        NOT NULL,         -- ISO-4217
    fxr_rate            DECIMAL(18,6) NOT NULL CHECK(fxr_rate > 0),
    fxr_rate_date       TEXT        NOT NULL,         -- ISO-8601 date
    fxr_source          TEXT        NOT NULL DEFAULT 'manual',
    status              TEXT        NOT NULL DEFAULT 'active',
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(fxr_from_currency, fxr_to_currency, fxr_rate_date)
);

-- ─── D10: expenses ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    exp_id              TEXT        PRIMARY KEY,
    exp_trip_id         TEXT        NOT NULL REFERENCES trips(trp_id),
    exp_payer_id        TEXT        NOT NULL REFERENCES users(usr_id),
    exp_title           TEXT        NOT NULL,
    exp_category        TEXT        NOT NULL
                            CHECK(exp_category IN (
                                'accommodation','transport','food',
                                'activities','misc','shopping','health','entertainment'
                            )),
    exp_amount          DECIMAL(12,2) NOT NULL CHECK(exp_amount > 0),
    exp_currency        TEXT        NOT NULL,          -- ISO-4217 (original)
    exp_home_amount     DECIMAL(12,2) NOT NULL,       -- converted to home currency
    exp_home_currency   TEXT        NOT NULL,          -- trip home currency
    exp_fx_rate_id      TEXT        REFERENCES fx_rates(fxr_id),
    exp_fx_rate_used    DECIMAL(18,6),                -- snapshot of rate used
    exp_date            TEXT        NOT NULL,          -- ISO-8601 date
    exp_notes           TEXT,
    exp_receipt_id      TEXT,                         -- FK set after receipt upload
    exp_split_type      TEXT        NOT NULL DEFAULT 'equal'
                            CHECK(exp_split_type IN ('equal','custom','none')),
    exp_entered_via     TEXT        NOT NULL DEFAULT 'manual'
                            CHECK(exp_entered_via IN ('manual','ocr','nl_parse','import')),
    exp_source_text     TEXT,                         -- NL input that was parsed
    status              TEXT        NOT NULL DEFAULT 'active'
                            CHECK(status IN ('active','deleted','disputed')),
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D11: expense_splits ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS expense_splits (
    spl_id              TEXT        PRIMARY KEY,
    spl_expense_id      TEXT        NOT NULL REFERENCES expenses(exp_id),
    spl_user_id         TEXT        NOT NULL REFERENCES users(usr_id),
    spl_share_amount    DECIMAL(12,2) NOT NULL CHECK(spl_share_amount >= 0),
    spl_share_pct       DECIMAL(5,2),
    spl_is_settled      INTEGER     NOT NULL DEFAULT 0 CHECK(spl_is_settled IN (0,1)),
    spl_settled_at      TEXT,
    status              TEXT        NOT NULL DEFAULT 'active',
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(spl_expense_id, spl_user_id)
);

-- ─── D12: receipts ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS receipts (
    rcp_id              TEXT        PRIMARY KEY,
    rcp_expense_id      TEXT        REFERENCES expenses(exp_id),
    rcp_trip_id         TEXT        NOT NULL REFERENCES trips(trp_id),
    rcp_image_url       TEXT,
    rcp_image_data      TEXT,                         -- base64 for demo
    rcp_ocr_raw_text    TEXT,
    rcp_ocr_merchant    TEXT,
    rcp_ocr_amount      DECIMAL(12,2),
    rcp_ocr_currency    TEXT,
    rcp_ocr_date        TEXT,
    rcp_ocr_category    TEXT,
    rcp_ocr_confidence  DECIMAL(5,2),
    rcp_ocr_processed_at TEXT,
    status              TEXT        NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending','processed','failed','linked')),
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D13: itineraries ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS itineraries (
    itn_id          TEXT        PRIMARY KEY,
    itn_trip_id     TEXT        NOT NULL REFERENCES trips(trp_id),
    itn_title       TEXT        NOT NULL,
    itn_notes       TEXT,
    status          TEXT        NOT NULL DEFAULT 'active',
    created_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── D14: itinerary_items ────────────────────────────────────
CREATE TABLE IF NOT EXISTS itinerary_items (
    itm_id              TEXT        PRIMARY KEY,
    itm_itinerary_id    TEXT        NOT NULL REFERENCES itineraries(itn_id),
    itm_day_number      INTEGER     NOT NULL CHECK(itm_day_number >= 1),
    itm_item_date       TEXT        NOT NULL,          -- ISO-8601 date
    itm_title           TEXT        NOT NULL,
    itm_type            TEXT        NOT NULL DEFAULT 'activity'
                            CHECK(itm_type IN ('flight','hotel','activity','transport','meal','other')),
    itm_location        TEXT,
    itm_city_id         TEXT        REFERENCES cities(cty_id),
    itm_lat             REAL,                          -- WGS-84, 6dp
    itm_lng             REAL,                          -- WGS-84, 6dp
    itm_start_time      TEXT,
    itm_end_time        TEXT,
    itm_estimated_cost  DECIMAL(12,2),
    itm_currency        TEXT,
    itm_booking_ref     TEXT,
    itm_notes           TEXT,
    status              TEXT        NOT NULL DEFAULT 'active',
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- ─── Indexes for query performance ───────────────────────────
CREATE INDEX IF NOT EXISTS idx_expenses_trip    ON expenses(exp_trip_id);
CREATE INDEX IF NOT EXISTS idx_expenses_payer   ON expenses(exp_payer_id);
CREATE INDEX IF NOT EXISTS idx_expenses_cat     ON expenses(exp_category);
CREATE INDEX IF NOT EXISTS idx_expenses_date    ON expenses(exp_date);
CREATE INDEX IF NOT EXISTS idx_splits_expense   ON expense_splits(spl_expense_id);
CREATE INDEX IF NOT EXISTS idx_splits_user      ON expense_splits(spl_user_id);
CREATE INDEX IF NOT EXISTS idx_members_trip     ON trip_members(tmb_trip_id);
CREATE INDEX IF NOT EXISTS idx_fxr_pair_date    ON fx_rates(fxr_from_currency, fxr_to_currency, fxr_rate_date);
CREATE INDEX IF NOT EXISTS idx_receipts_trip    ON receipts(rcp_trip_id);
