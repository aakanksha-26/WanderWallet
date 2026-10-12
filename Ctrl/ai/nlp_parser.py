"""
Natural Language Expense Parser — Standalone Module
Parses strings like "₹1500 dinner split with Lavanya and Rahul"
into structured expense fields.
"""

import re
from datetime import date

CURRENCY_MAP = {
    '₹': 'INR', 'rs': 'INR', 'inr': 'INR', 'rupee': 'INR', 'rupees': 'INR',
    '$': 'USD', 'usd': 'USD', 'dollar': 'USD',
    '€': 'EUR', 'eur': 'EUR', 'euro': 'EUR',
    '£': 'GBP', 'gbp': 'GBP', 'pound': 'GBP',
    '฿': 'THB', 'thb': 'THB', 'baht': 'THB',
}

CATEGORY_KEYWORDS = {
    'food':          ['dinner', 'lunch', 'breakfast', 'food', 'meal', 'cafe', 'restaurant',
                      'coffee', 'drink', 'pizza', 'biryani', 'snack', 'ate', 'eating'],
    'transport':     ['cab', 'taxi', 'uber', 'ola', 'bus', 'train', 'flight', 'auto',
                      'rickshaw', 'fuel', 'petrol', 'travel', 'transport', 'ride', 'boat'],
    'accommodation': ['hotel', 'resort', 'stay', 'room', 'hostel', 'airbnb', 'checkout', 'lodge'],
    'activities':    ['diving', 'tour', 'trek', 'hike', 'museum', 'beach', 'adventure', 'activity',
                      'show', 'ticket', 'spa', 'yoga', 'safari', 'snorkel'],
    'shopping':      ['bought', 'purchase', 'shopping', 'market', 'souvenir', 'clothes', 'bag', 'shop'],
    'health':        ['medicine', 'pharmacy', 'medical', 'doctor', 'hospital', 'clinic', 'tablet'],
}


def parse_nl_expense(text: str, members: list | None = None) -> dict:
    """
    Parse a natural language expense string.

    Args:
        text: Input string e.g. "₹1500 dinner split with Lavanya and Rahul"
        members: List of dicts with keys 'usr_id' and 'usr_name' for name resolution.

    Returns:
        dict with keys: amount, currency, category, title, split_members (ids),
                        split_members_raw (names), split_type, date, confidence
    """
    text_lower = text.lower()

    # ── Currency detection ────────────────────────────────────────────────
    currency = 'INR'
    for sym, cur in sorted(CURRENCY_MAP.items(), key=lambda x: -len(x[0])):
        if sym in text_lower:
            currency = cur
            break

    # ── Amount extraction ────────────────────────────────────────────────
    amount = None
    amount_match = re.search(r'[\d,]+(?:\.\d+)?', text)
    if amount_match:
        try:
            amount = float(amount_match.group().replace(',', ''))
        except ValueError:
            pass

    # ── Category inference ───────────────────────────────────────────────
    category = 'misc'
    best_score = 0
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            category = cat

    # ── Title extraction ─────────────────────────────────────────────────
    title = text
    for sym in ['₹', '$', '€', '£', '฿']:
        title = title.replace(sym, ' ')
    title = re.sub(r'\b\d[\d,.]*\b', '', title)
    stop = {'add', 'added', 'split', 'between', 'with', 'and', 'or', 'paid', 'pay', 'for',
            'inr', 'usd', 'eur', 'gbp', 'thb', 'rs', 'rupees', 'rupee', 'dollar', 'euro'}
    words = [w for w in re.sub(r'[^\w\s]', '', title).split() if w.lower() not in stop]
    title = ' '.join(words).strip().title() or 'Expense'

    # ── Split member extraction ───────────────────────────────────────────
    split_members_raw = []
    split_match = re.search(
        r'split\s+(?:between\s+|with\s+|among\s+)?([\w\s,&]+?)(?:\s+equally|\s+equal|$)',
        text, re.IGNORECASE
    )
    if split_match:
        raw = split_match.group(1)
        names = re.split(r'[,&]|\band\b', raw, flags=re.IGNORECASE)
        split_members_raw = [n.strip() for n in names if n.strip() and len(n.strip()) > 1]

    # Resolve to user IDs
    split_user_ids = []
    if split_members_raw and members:
        for raw_name in split_members_raw:
            for member in members:
                if raw_name.lower() in member.get('usr_name', '').lower():
                    split_user_ids.append(member['usr_id'])
                    break

    # Confidence
    confidence = min(100.0,
                     40.0 * bool(amount) +
                     20.0 * (best_score > 0) +
                     20.0 * (len(title) > 3) +
                     20.0 * bool(split_members_raw))

    return {
        'amount': amount,
        'currency': currency,
        'category': category,
        'title': title,
        'split_members': split_user_ids,
        'split_members_raw': split_members_raw,
        'split_type': 'equal' if split_user_ids else 'none',
        'date': str(date.today()),
        'entered_via': 'nl_parse',
        'confidence': round(confidence, 1),
    }
