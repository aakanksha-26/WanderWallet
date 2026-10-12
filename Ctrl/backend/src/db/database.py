"""
Database initialization and connection management.
Supports both PostgreSQL (Supabase) and SQLite with WAL mode.
Provides connection pooling, SQL parameter translation, and table syncing.
"""

import os
import re
import datetime
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')

# Supabase Client integration
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
supabase_client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"⚠️ Supabase SDK init warning: {e}")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SCHEMA_PATH = BASE_DIR / 'data-model' / 'schema.sql'
SEED_PATH = BASE_DIR / 'data-model' / 'seed' / 'seed_data.sql'

db_url = os.getenv('DATABASE_URL', '').strip()
IS_POSTGRES = False
DB_PATH = BASE_DIR / 'backend' / 'tripwallet.db'

if db_url and not db_url.startswith(('postgresql://', 'postgres://')):
    DB_PATH = Path(db_url)
elif db_url and (db_url.startswith('postgresql://') or db_url.startswith('postgres://')):
    try:
        import psycopg2
        import psycopg2.extras
        # Test PostgreSQL connection with a short timeout
        _test_conn = psycopg2.connect(db_url, connect_timeout=3)
        _test_conn.close()
        IS_POSTGRES = True
    except Exception as _err:
        print(f"⚠️ PostgreSQL/Supabase unreachable ({_err}). Falling back to local SQLite.")
        IS_POSTGRES = False

import sqlite3
if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras


def adapt_query(query: str) -> str:
    """Adapt SQLite syntax to PostgreSQL when running on Postgres."""
    if not IS_POSTGRES:
        return query
    
    q = query
    # 1. ALTER TABLE ADD COLUMN -> ADD COLUMN IF NOT EXISTS
    q = re.sub(r'ALTER TABLE\s+(\w+)\s+ADD COLUMN\s+(\w+)', r'ALTER TABLE \1 ADD COLUMN IF NOT EXISTS \2', q, flags=re.IGNORECASE)
    
    # 2. INSERT OR REPLACE INTO budgets
    if re.search(r'INSERT\s+OR\s+REPLACE\s+INTO\s+budgets', q, re.IGNORECASE):
        q = re.sub(r'INSERT\s+OR\s+REPLACE\s+INTO\s+budgets', 'INSERT INTO budgets', q, flags=re.IGNORECASE)
        q += ''' ON CONFLICT (bud_trip_id) DO UPDATE SET
            bud_total_amount = EXCLUDED.bud_total_amount,
            bud_currency = EXCLUDED.bud_currency,
            bud_accommodation_cap = EXCLUDED.bud_accommodation_cap,
            bud_transport_cap = EXCLUDED.bud_transport_cap,
            bud_food_cap = EXCLUDED.bud_food_cap,
            bud_activities_cap = EXCLUDED.bud_activities_cap,
            bud_misc_cap = EXCLUDED.bud_misc_cap,
            bud_alert_threshold_pct = EXCLUDED.bud_alert_threshold_pct,
            bud_notes = EXCLUDED.bud_notes,
            status = EXCLUDED.status,
            updated_at = EXCLUDED.updated_at'''
    # 3. INSERT OR REPLACE INTO fx_rates
    elif re.search(r'INSERT\s+OR\s+REPLACE\s+INTO\s+fx_rates', q, re.IGNORECASE):
        q = re.sub(r'INSERT\s+OR\s+REPLACE\s+INTO\s+fx_rates', 'INSERT INTO fx_rates', q, flags=re.IGNORECASE)
        q += ''' ON CONFLICT (fxr_from_currency, fxr_to_currency, fxr_rate_date) DO UPDATE SET
            fxr_rate = EXCLUDED.fxr_rate,
            updated_at = EXCLUDED.updated_at'''
    # 4. INSERT OR IGNORE INTO
    elif re.search(r'INSERT\s+OR\s+IGNORE\s+INTO', q, re.IGNORECASE):
        q = re.sub(r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT INTO', q, flags=re.IGNORECASE)
        q += ' ON CONFLICT DO NOTHING'
    
    # 5. Convert ? placeholders to %s
    q = q.replace('?', '%s')
    return q


def get_db():
    """Return a connection."""
    if IS_POSTGRES:
        conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        import sqlite3
        conn = sqlite3.connect(
            str(DB_PATH),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


def init_db():
    """Ensure database schema is initialized."""
    if IS_POSTGRES:
        conn = get_db()
        try:
            cur = conn.cursor()
            # Ensure unique index on budgets(bud_trip_id)
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_budgets_trip_id ON budgets(bud_trip_id);")
            conn.commit()
            print("✅ Supabase PostgreSQL ready at", db_url.split('@')[-1])
        except Exception as e:
            conn.rollback()
            print(f"❌ PostgreSQL init error: {e}")
            raise
        finally:
            conn.close()
    else:
        import sqlite3
        db_exists = DB_PATH.exists()
        conn = get_db()
        try:
            with open(SCHEMA_PATH, 'r') as f:
                conn.executescript(f.read())
            if not db_exists:
                print("📦 Seeding SQLite database...")
                with open(SEED_PATH, 'r') as f:
                    conn.executescript(f.read())
                print("✅ SQLite database seeded successfully.")
            conn.commit()
            print(f"✅ SQLite database ready at {DB_PATH}")
        except Exception as e:
            print(f"❌ SQLite init error: {e}")
            raise
        finally:
            conn.close()


def query_db(query, args=(), one=False):
    """Execute a SELECT query and return results."""
    conn = get_db()
    try:
        adapted_q = adapt_query(query)
        if IS_POSTGRES:
            cur = conn.cursor()
            cur.execute(adapted_q, args)
            rv = cur.fetchall()
            return (rv[0] if rv else None) if one else rv
        else:
            cur = conn.execute(adapted_q, args)
            rv = cur.fetchall()
            return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()


def mutate_db(query, args=()):
    """Execute an INSERT/UPDATE/DELETE and return lastrowid or affected count."""
    conn = get_db()
    try:
        adapted_q = adapt_query(query)
        if IS_POSTGRES:
            cur = conn.cursor()
            cur.execute(adapted_q, args)
            conn.commit()
            return cur.rowcount
        else:
            cur = conn.execute(adapted_q, args)
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def executemany_db(query, args_list):
    """Execute a query for multiple rows."""
    conn = get_db()
    try:
        adapted_q = adapt_query(query)
        if IS_POSTGRES:
            cur = conn.cursor()
            cur.executemany(adapted_q, args_list)
            conn.commit()
        else:
            conn.executemany(adapted_q, args_list)
            conn.commit()
    finally:
        conn.close()


def row_to_dict(row):
    """Convert DB row to plain dict with normalized types."""
    if row is None:
        return None
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, (datetime.datetime, datetime.date)):
            d[k] = v.isoformat()
    return d


def rows_to_list(rows):
    """Convert list of DB rows to list of dicts."""
    if not rows:
        return []
    return [row_to_dict(r) for r in rows]
