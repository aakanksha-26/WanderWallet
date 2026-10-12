"""Trips API routes."""
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, rows_to_list, row_to_dict

trips_bp = Blueprint('trips', __name__)

@trips_bp.route('/', methods=['GET'])
def list_trips():
    rows = rows_to_list(query_db(
        "SELECT t.*, u.usr_name as owner_name FROM trips t JOIN users u ON u.usr_id = t.trp_owner_id WHERE t.status != 'cancelled' ORDER BY t.trp_start_date DESC"
    ))
    return jsonify({'trips': rows, 'count': len(rows)})

@trips_bp.route('/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    row = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not row: return jsonify({'error': 'Trip not found'}), 404
    return jsonify(row)

@trips_bp.route('/', methods=['POST'])
def create_trip():
    data = request.get_json(force=True)
    required = ['name', 'owner_id', 'destination', 'start_date', 'end_date']
    for f in required:
        if not data.get(f): return jsonify({'error': f'Missing: {f}'}), 400
    trp_id = f"trp_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    mutate_db(
        "INSERT INTO trips (trp_id,trp_name,trp_owner_id,trp_destination,trp_home_currency,trp_start_date,trp_end_date,trp_description,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (trp_id, data['name'], data['owner_id'], data['destination'],
         data.get('home_currency','INR'), data['start_date'], data['end_date'],
         data.get('description'), 'active', now, now)
    )
    return jsonify({'trip_id': trp_id, 'message': 'Trip created'}), 201

@trips_bp.route('/<trip_id>/currency', methods=['POST'])
def update_trip_currency(trip_id):
    """Switch primary trip currency and recalculate expenses and budget."""
    data = request.get_json(force=True)
    new_cur = data.get('currency', '').upper()
    if not new_cur:
        return jsonify({'error': 'currency is required'}), 400

    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    old_cur = trip['trp_home_currency']
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # Update trip
    mutate_db("UPDATE trips SET trp_home_currency = ?, updated_at = ? WHERE trp_id = ?", (new_cur, now, trip_id))

    # Recalculate expenses home amounts
    from decimal import Decimal
    from services.fx_service import convert
    expenses = rows_to_list(query_db("SELECT * FROM expenses WHERE exp_trip_id = ? AND status='active'", (trip_id,)))
    for exp in expenses:
        orig_amt = Decimal(str(exp['exp_amount']))
        orig_cur = exp['exp_currency']
        try:
            converted, rate = convert(orig_amt, orig_cur, new_cur, exp.get('exp_date'))
            mutate_db(
                "UPDATE expenses SET exp_home_amount = ?, exp_home_currency = ?, exp_fx_rate_used = ?, updated_at = ? WHERE exp_id = ?",
                (str(converted), new_cur, str(rate), now, exp['exp_id'])
            )
        except Exception:
            pass

    # Recalculate budget total and caps if currencies differ
    if old_cur != new_cur:
        budget = row_to_dict(query_db("SELECT * FROM budgets WHERE bud_trip_id = ? AND status='active'", (trip_id,), one=True))
        if budget:
            try:
                new_bud_total, _ = convert(Decimal(str(budget['bud_total_amount'])), old_cur, new_cur)
                mutate_db(
                    "UPDATE budgets SET bud_total_amount = ?, bud_currency = ?, updated_at = ? WHERE bud_id = ?",
                    (str(new_bud_total), new_cur, now, budget['bud_id'])
                )
            except Exception:
                pass

    return jsonify({
        'trip_id': trip_id,
        'old_currency': old_cur,
        'new_currency': new_cur,
        'message': f'Trip primary currency converted to {new_cur}.'
    })


@trips_bp.route('/users', methods=['GET'])
def list_users():
    rows = rows_to_list(query_db("SELECT usr_id,usr_name,usr_email FROM users WHERE status='active'"))
    return jsonify({'users': rows})

