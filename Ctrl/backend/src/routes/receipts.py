"""Receipts API."""
from flask import Blueprint, jsonify
from db.database import rows_to_list, query_db

receipts_bp = Blueprint('receipts', __name__)

@receipts_bp.route('/trip/<trip_id>', methods=['GET'])
def list_receipts(trip_id):
    rows = rows_to_list(query_db(
        "SELECT rcp_id,rcp_ocr_merchant,rcp_ocr_amount,rcp_ocr_currency,rcp_ocr_date,rcp_ocr_category,rcp_ocr_confidence,status,created_at FROM receipts WHERE rcp_trip_id = ? ORDER BY created_at DESC",
        (trip_id,)
    ))
    return jsonify({'receipts': rows})
