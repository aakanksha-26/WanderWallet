-- =============================================================
--  WanderWallet — Seed Data
--  Demo: Goa Trip 2026 with INR budget, foreign-currency expenses
--  Includes a USD food expense that breaches the food category cap
-- =============================================================

-- Languages
INSERT OR IGNORE INTO languages VALUES
  ('lng_en_in','en-IN','English (India)','English (India)','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('lng_hi_in','hi-IN','Hindi','हिन्दी','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('lng_kn_in','kn-IN','Kannada','ಕನ್ನಡ','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Currencies
INSERT OR IGNORE INTO currencies VALUES
  ('cur_inr','INR','Indian Rupee','₹',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cur_usd','USD','US Dollar','$',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cur_eur','EUR','Euro','€',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cur_thb','THB','Thai Baht','฿',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cur_gbp','GBP','British Pound','£',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cur_sgd','SGD','Singapore Dollar','S$',2,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Countries
INSERT OR IGNORE INTO countries VALUES
  ('cnt_in','IN','India','cur_inr',20.593684,78.962880,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cnt_us','US','United States','cur_usd',37.090240,-95.712891,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cnt_th','TH','Thailand','cur_thb',15.870032,100.992541,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Cities
INSERT OR IGNORE INTO cities VALUES
  ('cty_blr','Bengaluru','cnt_in',12.971599,77.594566,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cty_goa','Goa','cnt_in',15.299326,74.123996,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cty_bkk','Bangkok','cnt_th',13.756331,100.501765,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('cty_mum','Mumbai','cnt_in',19.075984,72.877656,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Users (Team CtrlFreaks demo members)
INSERT OR IGNORE INTO users VALUES
  ('usr_anil_001','Anil Kumar','anil@ctrlfreaks.dev','+91-9876543210',NULL,'INR','lng_en_in','en-IN','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('usr_lavanya_002','Lavanya Sharma','lavanya@ctrlfreaks.dev','+91-9876543211',NULL,'INR','lng_en_in','en-IN','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('usr_rahul_003','Rahul Menon','rahul@ctrlfreaks.dev','+91-9876543212',NULL,'INR','lng_en_in','en-IN','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('usr_priya_004','Priya Nair','priya@ctrlfreaks.dev','+91-9876543213',NULL,'INR','lng_kn_in','kn-IN','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Trip: Goa Group Trip 2026
INSERT OR IGNORE INTO trips VALUES
  ('trp_goa_2026','Goa Trip 2026 🏖️','usr_anil_001','Goa, India','cty_goa','INR',
   '2026-10-01','2026-10-07',NULL,'Group trip to Goa for KV Hackathon celebration!',
   'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Trip Members
INSERT OR IGNORE INTO trip_members VALUES
  ('tmb_001','trp_goa_2026','usr_anil_001','owner',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('tmb_002','trp_goa_2026','usr_lavanya_002','member',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('tmb_003','trp_goa_2026','usr_rahul_003','member',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('tmb_004','trp_goa_2026','usr_priya_004','member',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Budget with Category Caps (INR) — food cap intentionally low to trigger breach in demo
INSERT OR IGNORE INTO budgets VALUES
  ('bud_goa_2026','trp_goa_2026',
   50000.00,'INR',
   18000.00,    -- accommodation_cap
   8000.00,     -- transport_cap
   6000.00,     -- food_cap  ← WILL BE BREACHED by the USD dinner expense
   10000.00,    -- activities_cap
   4000.00,     -- misc_cap
   80.00,       -- alert_threshold_pct
   'Goa trip 2026 budget with per-category caps',
   'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- FX Rates (snapshot 2026-10-01)
INSERT OR IGNORE INTO fx_rates VALUES
  ('fxr_usd_inr_20261001','USD','INR',83.500000,'2026-10-01','manual','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('fxr_eur_inr_20261001','EUR','INR',91.250000,'2026-10-01','manual','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('fxr_thb_inr_20261001','THB','INR',2.350000,'2026-10-01','manual','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('fxr_gbp_inr_20261001','GBP','INR',106.750000,'2026-10-01','manual','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('fxr_inr_inr_20261001','INR','INR',1.000000,'2026-10-01','manual','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expenses (mix of INR + foreign currency)
-- Expense 1: Hotel (INR) — within accommodation cap
INSERT OR IGNORE INTO expenses VALUES
  ('exp_001','trp_goa_2026','usr_anil_001','Beach Resort - 3 nights','accommodation',
   15000.00,'INR',15000.00,'INR','fxr_inr_inr_20261001',1.000000,
   '2026-10-01',NULL,NULL,'equal','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense 2: Food - INR lunch (INR ₹2,500 — within 6000 cap so far)
INSERT OR IGNORE INTO expenses VALUES
  ('exp_002','trp_goa_2026','usr_lavanya_002','Lunch at Beach Shack','food',
   2500.00,'INR',2500.00,'INR','fxr_inr_inr_20261001',1.000000,
   '2026-10-02',NULL,NULL,'equal','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense 3: Transport (INR ₹3,000) — within transport cap
INSERT OR IGNORE INTO expenses VALUES
  ('exp_003','trp_goa_2026','usr_rahul_003','Cab from Airport','transport',
   3000.00,'INR',3000.00,'INR','fxr_inr_inr_20261001',1.000000,
   '2026-10-01',NULL,NULL,'equal','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense 4: FOREIGN CURRENCY — USD $55 dinner (= ₹4,592.50 @ 83.50)
-- This pushes food total to ₹2,500 + ₹4,592.50 = ₹7,092.50 → BREACHES ₹6,000 food cap!
INSERT OR IGNORE INTO expenses VALUES
  ('exp_004','trp_goa_2026','usr_anil_001','Fancy Seafood Dinner (USD)','food',
   55.00,'USD',4592.50,'INR','fxr_usd_inr_20261001',83.500000,
   '2026-10-03','Paid in USD at tourist restaurant',NULL,'equal','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense 5: Activities (INR ₹4,500)
INSERT OR IGNORE INTO expenses VALUES
  ('exp_005','trp_goa_2026','usr_priya_004','Scuba Diving Session','activities',
   4500.00,'INR',4500.00,'INR','fxr_inr_inr_20261001',1.000000,
   '2026-10-04',NULL,NULL,'equal','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense 6: EUR grocery (extra demo of multi-currency)
INSERT OR IGNORE INTO expenses VALUES
  ('exp_006','trp_goa_2026','usr_lavanya_002','Duty-Free Chocolates (EUR)','misc',
   12.00,'EUR',1095.00,'INR','fxr_eur_inr_20261001',91.250000,
   '2026-10-05','Bought at airport duty free',NULL,'none','manual',NULL,'active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Expense Splits for exp_001 (hotel — 4 members equal)
INSERT OR IGNORE INTO expense_splits VALUES
  ('spl_001_a','exp_001','usr_anil_001',3750.00,25.00,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('spl_001_b','exp_001','usr_lavanya_002',3750.00,25.00,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('spl_001_c','exp_001','usr_rahul_003',3750.00,25.00,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('spl_001_d','exp_001','usr_priya_004',3750.00,25.00,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Splits for exp_004 (USD dinner — 3 members: Anil paid)
INSERT OR IGNORE INTO expense_splits VALUES
  ('spl_004_a','exp_004','usr_anil_001',1530.83,33.33,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('spl_004_b','exp_004','usr_lavanya_002',1530.84,33.34,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('spl_004_c','exp_004','usr_rahul_003',1530.83,33.33,0,NULL,'active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

-- Itinerary
INSERT OR IGNORE INTO itineraries VALUES
  ('itn_goa_2026','trp_goa_2026','Goa 2026 Itinerary','7-day Goa adventure plan','active',
   strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));

INSERT OR IGNORE INTO itinerary_items VALUES
  ('itm_001','itn_goa_2026',1,'2026-10-01','Arrive at Goa Airport & Check-in','flight','Dabolim Airport','cty_goa',15.380833,73.831389,'14:00','16:00',NULL,NULL,NULL,'Flight GoAir G8-401','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('itm_002','itn_goa_2026',2,'2026-10-02','Calangute & Baga Beach Day','activity','Calangute Beach','cty_goa',15.544425,73.752418,'09:00','18:00',NULL,NULL,NULL,'','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('itm_003','itn_goa_2026',3,'2026-10-03','Old Goa Heritage Tour','activity','Old Goa Church','cty_goa',15.501100,73.911400,'10:00','17:00',NULL,NULL,NULL,'','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  ('itm_004','itn_goa_2026',4,'2026-10-04','Scuba Diving at Grande Island','activity','Grande Island','cty_goa',15.374980,73.698710,'08:00','14:00',4500.00,'INR',NULL,'Book in advance','active',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'));
