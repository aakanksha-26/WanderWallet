"""
FX Rate Service — Currency Conversion using decimal.Decimal (R3)
All monetary arithmetic is exact — no floating point.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from db.database import query_db, row_to_dict

MONEY_DP = Decimal('0.01')
RATE_DP  = Decimal('0.000001')  # 6dp for FX rates


def get_rate(from_currency: str, to_currency: str, rate_date: str | None = None) -> Decimal:
    """
    Fetch FX rate from DB. Falls back to today if no date provided.
    Returns 1.000000 if currencies are the same.
    Raises ValueError if rate not found.
    """
    if from_currency == to_currency:
        return Decimal('1.000000')

    if rate_date is None:
        rate_date = str(date.today())

    # Try exact date first
    row = query_db(
        """SELECT fxr_rate FROM fx_rates
           WHERE fxr_from_currency = ? AND fxr_to_currency = ?
             AND fxr_rate_date <= ? AND status = 'active'
           ORDER BY fxr_rate_date DESC LIMIT 1""",
        (from_currency, to_currency, rate_date), one=True
    )

    if row:
        return Decimal(str(row['fxr_rate'])).quantize(RATE_DP)

    # Try inverse rate
    inv_row = query_db(
        """SELECT fxr_rate FROM fx_rates
           WHERE fxr_from_currency = ? AND fxr_to_currency = ?
             AND fxr_rate_date <= ? AND status = 'active'
           ORDER BY fxr_rate_date DESC LIMIT 1""",
        (to_currency, from_currency, rate_date), one=True
    )

    if inv_row:
        return (Decimal('1') / Decimal(str(inv_row['fxr_rate']))).quantize(RATE_DP)

    # Try live rate from ExchangeRate-API
    live_rate = fetch_and_store_live_rate(from_currency, to_currency, rate_date)
    if live_rate is not None:
        return live_rate

    # Fallback table if offline
    for (f, t), r in FALLBACK_RATES.items():
        if f == from_currency and t == to_currency:
            return r
        if t == from_currency and f == to_currency:
            return (Decimal('1') / r).quantize(RATE_DP)

    raise ValueError(
        f"No FX rate found for {from_currency} → {to_currency} on or before {rate_date}"
    )


def fetch_and_store_live_rate(from_currency: str, to_currency: str, rate_date: str | None = None) -> Decimal | None:
    """Fetch live exchange rate from ExchangeRate-API and cache in fx_rates table."""
    import json
    import urllib.request
    import uuid
    from datetime import datetime, timezone
    from db.database import mutate_db

    try:
        url = f"https://open.er-api.com/v6/latest/{from_currency}"
        req = urllib.request.Request(url, headers={'User-Agent': 'TripWalletAI/1.0'})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                rates = data.get('rates', {})
                if to_currency in rates:
                    rate_val = Decimal(str(rates[to_currency])).quantize(RATE_DP)
                    # Cache in DB
                    now_date = rate_date or str(date.today())
                    now_ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    fxr_id = f"fxr_{uuid.uuid4().hex[:12]}"
                    try:
                        mutate_db(
                            """INSERT OR REPLACE INTO fx_rates
                               (fxr_id, fxr_from_currency, fxr_to_currency, fxr_rate, fxr_rate_date, status, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
                            (fxr_id, from_currency, to_currency, str(rate_val), now_date, now_ts, now_ts)
                        )
                    except Exception:
                        pass
                    return rate_val
    except Exception:
        pass
    return None


FALLBACK_RATES = {
    ('USD', 'INR'): Decimal('83.500000'),
    ('EUR', 'INR'): Decimal('91.250000'),
    ('GBP', 'INR'): Decimal('106.000000'),
    ('THB', 'INR'): Decimal('2.350000'),
    ('SGD', 'INR'): Decimal('62.000000'),
    ('JPY', 'INR'): Decimal('0.550000'),
    ('AED', 'INR'): Decimal('22.750000'),
    ('AUD', 'INR'): Decimal('54.500000'),
    ('CAD', 'INR'): Decimal('61.200000'),
    ('CHF', 'INR'): Decimal('94.800000'),
}


def convert(amount: Decimal | str | float,
            from_currency: str,
            to_currency: str,
            rate_date: str | None = None) -> tuple[Decimal, Decimal]:
    """
    Convert amount from from_currency to to_currency.
    
    Returns:
        (converted_amount, rate_used)  — both as Decimal
    """
    amount = Decimal(str(amount)).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
    rate = get_rate(from_currency, to_currency, rate_date)
    converted = (amount * rate).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
    return converted, rate


def get_all_rates(target_currency: str, rate_date: str | None = None) -> dict:
    """Return all available rates to target_currency."""
    if rate_date is None:
        rate_date = str(date.today())

    rows = query_db(
        """SELECT fxr_from_currency, fxr_rate, fxr_rate_date 
           FROM fx_rates
           WHERE fxr_to_currency = ? AND fxr_rate_date <= ? AND status = 'active'
           ORDER BY fxr_from_currency, fxr_rate_date DESC""",
        (target_currency, rate_date)
    )

    rates = {}
    for row in rows:
        cur = row['fxr_from_currency']
        if cur not in rates:  # already sorted by date desc
            rates[cur] = float(Decimal(str(row['fxr_rate'])).quantize(RATE_DP))

    rates[target_currency] = 1.0
    return rates
