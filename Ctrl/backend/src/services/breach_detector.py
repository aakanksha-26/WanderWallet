"""
Breach Detector Service — Category Caps & Budget Breach Alert Engine
All arithmetic uses Python's decimal.Decimal for exact precision (R3).
"""

from decimal import Decimal, ROUND_HALF_UP
from db.database import query_db, rows_to_list

CATEGORY_CAP_COLUMNS = {
    'accommodation': 'bud_accommodation_cap',
    'transport':     'bud_transport_cap',
    'food':          'bud_food_cap',
    'activities':    'bud_activities_cap',
    'misc':          'bud_misc_cap',
}

MONEY_DP = Decimal('0.01')  # 2 decimal places


def check_breach(trip_id: str, new_expense: dict | None = None) -> dict:
    """
    Calculate category spend totals for a trip and check for cap breaches.
    
    Args:
        trip_id: The trp_ prefixed trip ID.
        new_expense: Optional dict with keys: category, home_amount (Decimal/str)
                     to simulate adding a new expense before committing.

    Returns:
        dict with keys:
          - breaches: list of breach objects (one per breached category/total)
          - category_summary: dict of category → {spent, cap, status}
          - total_spent: Decimal
          - total_cap: Decimal
          - total_pct: Decimal
    """
    # Fetch budget
    budget = query_db(
        "SELECT * FROM budgets WHERE bud_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    )
    if not budget:
        return {'breaches': [], 'category_summary': {}, 'error': 'No budget found'}

    budget = dict(budget)
    total_cap = Decimal(str(budget['bud_total_amount']))
    alert_pct = Decimal(str(budget['bud_alert_threshold_pct'])) / Decimal('100')

    # Fetch all active expenses for this trip
    expenses = rows_to_list(query_db(
        """SELECT exp_category, exp_home_amount 
           FROM expenses 
           WHERE exp_trip_id = ? AND status = 'active'""",
        (trip_id,)
    ))

    # Optionally add the new expense being submitted
    if new_expense:
        expenses.append({
            'exp_category': new_expense['category'],
            'exp_home_amount': str(new_expense['home_amount'])
        })

    # Aggregate spend by category using Decimal
    category_spend: dict[str, Decimal] = {}
    total_spent = Decimal('0.00')

    for exp in expenses:
        cat = exp['exp_category']
        amt = Decimal(str(exp['exp_home_amount'])).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
        category_spend[cat] = category_spend.get(cat, Decimal('0.00')) + amt
        total_spent += amt

    # Check breaches
    breaches = []
    category_summary = {}

    for cat, cap_col in CATEGORY_CAP_COLUMNS.items():
        cap_value = budget.get(cap_col)
        spent = category_spend.get(cat, Decimal('0.00'))

        if cap_value is not None:
            cap = Decimal(str(cap_value)).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
            threshold = (cap * alert_pct).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
            pct_used = ((spent / cap) * Decimal('100')).quantize(Decimal('0.1'))

            status = 'ok'
            if spent > cap:
                status = 'breached'
            elif spent >= threshold:
                status = 'warning'

            category_summary[cat] = {
                'spent': float(spent),
                'cap': float(cap),
                'threshold': float(threshold),
                'pct_used': float(pct_used),
                'status': status,
            }

            if status in ('breached', 'warning'):
                overshoot = max(Decimal('0.00'), spent - cap)
                breaches.append({
                    'alert': True,
                    'type': status,
                    'category': cat,
                    'category_cap': float(cap),
                    'current_spend': float(spent),
                    'overshoot': float(overshoot),
                    'currency': budget['bud_currency'],
                    'pct_used': float(pct_used),
                    'dismissible': True,
                    'message': _format_message(cat, cap, spent, overshoot, status, budget['bud_currency']),
                })
        else:
            # No cap set for this category
            category_summary[cat] = {
                'spent': float(category_spend.get(cat, Decimal('0.00'))),
                'cap': None,
                'threshold': None,
                'pct_used': None,
                'status': 'no_cap',
            }

    # Check total budget breach
    total_threshold = (total_cap * alert_pct).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
    total_pct = ((total_spent / total_cap) * Decimal('100')).quantize(Decimal('0.1')) if total_cap > 0 else Decimal('0')

    if total_spent > total_cap:
        overshoot = total_spent - total_cap
        breaches.insert(0, {
            'alert': True,
            'type': 'breached',
            'category': 'total_budget',
            'category_cap': float(total_cap),
            'current_spend': float(total_spent),
            'overshoot': float(overshoot),
            'currency': budget['bud_currency'],
            'pct_used': float(total_pct),
            'dismissible': True,
            'message': f"TOTAL BUDGET BREACHED! Spent {budget['bud_currency']} {total_spent:,.2f} "
                       f"against total budget of {budget['bud_currency']} {total_cap:,.2f} "
                       f"(Overshoot: {budget['bud_currency']} {overshoot:,.2f})",
        })
    elif total_spent >= total_threshold:
        breaches.insert(0, {
            'alert': True,
            'type': 'warning',
            'category': 'total_budget',
            'category_cap': float(total_cap),
            'current_spend': float(total_spent),
            'overshoot': 0.0,
            'currency': budget['bud_currency'],
            'pct_used': float(total_pct),
            'dismissible': True,
            'message': f"Budget Warning: Used {total_pct}% of total budget ({budget['bud_currency']} {total_spent:,.2f} / {total_cap:,.2f})",
        })

    return {
        'breaches': breaches,
        'category_summary': category_summary,
        'total_spent': float(total_spent),
        'total_cap': float(total_cap),
        'total_pct': float(total_pct),
        'alert_threshold_pct': float(alert_pct * 100),
    }


def _format_message(cat: str, cap: Decimal, spent: Decimal, overshoot: Decimal,
                    status: str, currency: str) -> str:
    cat_label = cat.upper().replace('_', ' ')
    sym = _currency_symbol(currency)
    if status == 'breached':
        return (
            f"{cat_label} CAP BREACHED! "
            f"Spent {sym}{spent:,.2f} against cap of {sym}{cap:,.2f} "
            f"(Overshoot: {sym}{overshoot:,.2f})"
        )
    else:
        pct = ((spent / cap) * 100).quantize(Decimal('0.1'))
        return (
            f"{cat_label} Warning: Used {pct}% of {sym}{cap:,.2f} cap "
            f"({sym}{spent:,.2f} spent)"
        )


def _currency_symbol(code: str) -> str:
    symbols = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 'THB': '฿', 'SGD': 'S$'}
    return symbols.get(code, code + ' ')
