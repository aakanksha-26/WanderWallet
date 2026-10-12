"""
Dashboard API — trip summary, budget vs actual, per-category breakdown.
"""

from flask import Blueprint, jsonify, request
from decimal import Decimal
from db.database import query_db, rows_to_list, row_to_dict
from services.breach_detector import check_breach
from services.fx_service import get_all_rates

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/<trip_id>', methods=['GET'])
def get_dashboard(trip_id):
    """Full trip dashboard: budget, expenses, breaches, members."""
    trip = row_to_dict(query_db(
        "SELECT * FROM trips WHERE trp_id = ? AND status != 'cancelled'",
        (trip_id,), one=True
    ))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    budget = row_to_dict(query_db(
        "SELECT * FROM budgets WHERE bud_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    ))

    expenses = rows_to_list(query_db(
        """SELECT e.*, u.usr_name as payer_name
           FROM expenses e
           JOIN users u ON u.usr_id = e.exp_payer_id
           WHERE e.exp_trip_id = ? AND e.status = 'active'
           ORDER BY e.exp_date DESC""",
        (trip_id,)
    ))

    members = rows_to_list(query_db(
        """SELECT tm.*, u.usr_name, u.usr_email, u.usr_avatar_url
           FROM trip_members tm
           JOIN users u ON u.usr_id = tm.tmb_user_id
           WHERE tm.tmb_trip_id = ? AND tm.status = 'active'""",
        (trip_id,)
    ))

    # Breach analysis
    breach_data = check_breach(trip_id)

    # Spend by category
    spend_by_category = {}
    spend_by_currency = {}
    for exp in expenses:
        cat = exp['exp_category']
        amt = float(exp['exp_home_amount'])
        spend_by_category[cat] = spend_by_category.get(cat, 0.0) + amt

        orig_cur = exp['exp_currency']
        spend_by_currency[orig_cur] = spend_by_currency.get(orig_cur, 0.0) + float(exp['exp_amount'])

    # Daily spend trend
    daily_spend = {}
    for exp in expenses:
        d = exp['exp_date']
        daily_spend[d] = daily_spend.get(d, 0.0) + float(exp['exp_home_amount'])

    # FX rates
    home_currency = trip['trp_home_currency']
    fx_rates = {}
    try:
        fx_rates = get_all_rates(home_currency)
    except Exception:
        pass

    total_spent = breach_data.get('total_spent', 0.0)
    total_cap = breach_data.get('total_cap', 0.0)

    # AI Recommendations
    from services.recommendation_service import get_ai_recommendations
    recs_data = {}
    try:
        recs_data = get_ai_recommendations(trip_id)
    except Exception:
        pass

    return jsonify({
        'trip': trip,
        'budget': budget,
        'expenses': expenses,
        'members': members,
        'summary': {
            'total_spent': total_spent,
            'total_budget': total_cap,
            'remaining': round(total_cap - total_spent, 2),
            'pct_used': breach_data.get('total_pct', 0.0),
            'expense_count': len(expenses),
            'member_count': len(members),
            'home_currency': home_currency,
        },
        'spend_by_category': spend_by_category,
        'spend_by_currency': spend_by_currency,
        'daily_spend': dict(sorted(daily_spend.items())),
        'category_summary': breach_data.get('category_summary', {}),
        'breaches': breach_data.get('breaches', []),
        'fx_rates': fx_rates,
        'recommendations': recs_data,
    })

