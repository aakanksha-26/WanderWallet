"""Budgets API."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, row_to_dict
from services.breach_detector import check_breach

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/<trip_id>', methods=['GET'])
def get_budget(trip_id):
    row = row_to_dict(query_db("SELECT * FROM budgets WHERE bud_trip_id = ? AND status='active'", (trip_id,), one=True))
    if not row: return jsonify({'error': 'No budget found for this trip'}), 404
    breach = check_breach(trip_id)
    row['breach_status'] = breach
    return jsonify(row)

@budgets_bp.route('/', methods=['POST'])
def create_budget():
    data = request.get_json(force=True)
    trip_id = data.get('trip_id')
    total = data.get('total_amount')
    if not trip_id or not total:
        return jsonify({'error': 'trip_id and total_amount required'}), 400
    try:
        total_dec = Decimal(str(total))
        if total_dec <= 0: raise ValueError
    except Exception:
        return jsonify({'error': 'total_amount must be a positive number'}), 400
    threshold = float(data.get('alert_threshold_pct', 80))
    if not (1 <= threshold <= 100):
        return jsonify({'error': 'alert_threshold_pct must be between 1 and 100'}), 400
    bud_id = f"bud_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    mutate_db(
        """INSERT OR REPLACE INTO budgets
           (bud_id,bud_trip_id,bud_total_amount,bud_currency,
            bud_accommodation_cap,bud_transport_cap,bud_food_cap,bud_activities_cap,bud_misc_cap,
            bud_alert_threshold_pct,bud_notes,status,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,'active',?,?)""",
        (bud_id, trip_id, str(total_dec), data.get('currency','INR'),
         data.get('accommodation_cap'), data.get('transport_cap'),
         data.get('food_cap'), data.get('activities_cap'), data.get('misc_cap'),
         threshold, data.get('notes'), now, now)
    )
    return jsonify({'budget_id': bud_id, 'message': 'Budget created'}), 201
