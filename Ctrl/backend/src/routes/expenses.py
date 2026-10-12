"""
Expenses API routes — CRUD with FX conversion and breach detection.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, rows_to_list, row_to_dict
from services.fx_service import convert, get_rate
from services.breach_detector import check_breach

expenses_bp = Blueprint('expenses', __name__)
MONEY_DP = Decimal('0.01')

VALID_CATEGORIES = {
    'accommodation', 'transport', 'food',
    'activities', 'misc', 'shopping', 'health', 'entertainment'
}
VALID_SPLIT_TYPES = {'equal', 'custom', 'none'}
VALID_ENTERED_VIA = {'manual', 'ocr', 'nl_parse', 'import'}


@expenses_bp.route('/', methods=['GET'])
def list_expenses():
    trip_id = request.args.get('trip_id')
    if not trip_id:
        return jsonify({'error': 'trip_id is required'}), 400

    rows = rows_to_list(query_db(
        """SELECT e.*, u.usr_name as payer_name
           FROM expenses e
           JOIN users u ON u.usr_id = e.exp_payer_id
           WHERE e.exp_trip_id = ? AND e.status = 'active'
           ORDER BY e.exp_date DESC, e.created_at DESC""",
        (trip_id,)
    ))
    return jsonify({'expenses': rows, 'count': len(rows)})


@expenses_bp.route('/<exp_id>', methods=['GET'])
def get_expense(exp_id):
    row = row_to_dict(query_db(
        "SELECT * FROM expenses WHERE exp_id = ? AND status = 'active'",
        (exp_id,), one=True
    ))
    if not row:
        return jsonify({'error': 'Expense not found'}), 404
    
    splits = rows_to_list(query_db(
        """SELECT s.*, u.usr_name
           FROM expense_splits s
           JOIN users u ON u.usr_id = s.spl_user_id
           WHERE s.spl_expense_id = ? AND s.status = 'active'""",
        (exp_id,)
    ))
    row['splits'] = splits
    return jsonify(row)


@expenses_bp.route('/', methods=['POST'])
def create_expense():
    data = request.get_json(force=True)
    
    # ── Validation ──────────────────────────────────────────────────
    required = ['trip_id', 'payer_id', 'title', 'category', 'amount', 'currency', 'date']
    for f in required:
        if not data.get(f):
            return jsonify({'error': f'Missing required field: {f}'}), 400

    if data['category'] not in VALID_CATEGORIES:
        return jsonify({'error': f"Invalid category. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"}), 400

    try:
        amount = Decimal(str(data['amount'])).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
    except Exception:
        return jsonify({'error': 'Invalid amount'}), 400

    if amount <= 0:
        return jsonify({'error': 'Amount must be greater than 0'}), 400

    # ── FX Conversion ────────────────────────────────────────────────
    trip = row_to_dict(query_db(
        "SELECT trp_home_currency FROM trips WHERE trp_id = ? AND status = 'active'",
        (data['trip_id'],), one=True
    ))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    home_currency = trip['trp_home_currency']
    exp_currency = data['currency'].upper()

    try:
        home_amount, rate_used = convert(
            amount, exp_currency, home_currency, data.get('date')
        )
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Find FX rate record ID
    fx_rate_row = query_db(
        """SELECT fxr_id FROM fx_rates
           WHERE fxr_from_currency = ? AND fxr_to_currency = ?
             AND fxr_rate_date <= ? AND status = 'active'
           ORDER BY fxr_rate_date DESC LIMIT 1""",
        (exp_currency, home_currency, data.get('date', str(datetime.now(timezone.utc).date()))),
        one=True
    )
    fx_rate_id = fx_rate_row['fxr_id'] if fx_rate_row else None

    # ── Check breach BEFORE inserting (simulate) ─────────────────────
    breach_preview = check_breach(
        data['trip_id'],
        new_expense={'category': data['category'], 'home_amount': home_amount}
    )

    # ── Generate IDs ─────────────────────────────────────────────────
    exp_id = f"exp_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # ── Insert expense ────────────────────────────────────────────────
    mutate_db(
        """INSERT INTO expenses (
            exp_id, exp_trip_id, exp_payer_id, exp_title, exp_category,
            exp_amount, exp_currency, exp_home_amount, exp_home_currency,
            exp_fx_rate_id, exp_fx_rate_used, exp_date, exp_notes,
            exp_split_type, exp_entered_via, exp_source_text,
            status, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            exp_id, data['trip_id'], data['payer_id'], data['title'], data['category'],
            str(amount), exp_currency, str(home_amount), home_currency,
            fx_rate_id, str(rate_used), data['date'], data.get('notes'),
            data.get('split_type', 'equal'), data.get('entered_via', 'manual'),
            data.get('source_text'), 'active', now, now
        )
    )

    # ── Create splits ─────────────────────────────────────────────────
    split_result = _create_splits(exp_id, data, home_amount, now)
    if 'error' in split_result:
        return jsonify(split_result), 400

    # ── Final breach check (with inserted expense) ────────────────────
    breach_result = check_breach(data['trip_id'])

    return jsonify({
        'expense_id': exp_id,
        'amount': float(amount),
        'currency': exp_currency,
        'home_amount': float(home_amount),
        'home_currency': home_currency,
        'fx_rate_used': float(rate_used),
        'splits': split_result.get('splits', []),
        'breaches': breach_result['breaches'],
        'category_summary': breach_result['category_summary'],
    }), 201


def _create_splits(exp_id: str, data: dict, home_amount: Decimal, now: str) -> dict:
    """Create expense splits based on split_type."""
    split_type = data.get('split_type', 'equal')
    members = data.get('split_members', [])
    custom_splits = data.get('custom_splits', {})

    if split_type == 'none':
        return {'splits': []}

    if split_type == 'equal':
        # Get all active trip members if not specified
        if not members:
            rows = rows_to_list(query_db(
                "SELECT tmb_user_id FROM trip_members WHERE tmb_trip_id = ? AND status = 'active'",
                (data['trip_id'],)
            ))
            members = [r['tmb_user_id'] for r in rows]

        if not members:
            return {'splits': []}

        n = len(members)
        # Largest-remainder method for exact split
        base_share = (home_amount / Decimal(str(n))).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
        remainder = home_amount - (base_share * Decimal(str(n)))
        
        splits_data = []
        for i, uid in enumerate(members):
            share = base_share + (MONEY_DP if i == 0 and remainder > 0 else Decimal('0'))
            spl_id = f"spl_{uuid.uuid4().hex[:12]}"
            pct = (Decimal('100') / Decimal(str(n))).quantize(Decimal('0.01'))
            splits_data.append({
                'spl_id': spl_id, 'spl_expense_id': exp_id,
                'spl_user_id': uid, 'spl_share_amount': str(share),
                'spl_share_pct': str(pct),
            })

    elif split_type == 'custom':
        splits_data = []
        for uid, amt in custom_splits.items():
            spl_id = f"spl_{uuid.uuid4().hex[:12]}"
            share = Decimal(str(amt)).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
            if share < 0:
                return {'error': 'Split amount cannot be negative'}
            splits_data.append({
                'spl_id': spl_id, 'spl_expense_id': exp_id,
                'spl_user_id': uid, 'spl_share_amount': str(share),
                'spl_share_pct': None,
            })
    else:
        return {'splits': []}

    # Bulk insert splits
    for s in splits_data:
        mutate_db(
            """INSERT INTO expense_splits
               (spl_id, spl_expense_id, spl_user_id, spl_share_amount, spl_share_pct,
                spl_is_settled, status, created_at, updated_at)
               VALUES (?,?,?,?,?,0,'active',?,?)""",
            (s['spl_id'], s['spl_expense_id'], s['spl_user_id'],
             s['spl_share_amount'], s.get('spl_share_pct'), now, now)
        )

    return {'splits': splits_data}


@expenses_bp.route('/<exp_id>', methods=['DELETE'])
def delete_expense(exp_id):
    """Soft delete (R8)."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    mutate_db(
        "UPDATE expenses SET status = 'deleted', updated_at = ? WHERE exp_id = ?",
        (now, exp_id)
    )
    return jsonify({'message': f'Expense {exp_id} deleted', 'status': 'deleted'})
