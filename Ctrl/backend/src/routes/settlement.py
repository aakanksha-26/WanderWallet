"""Settlement API."""
from flask import Blueprint, jsonify
from services.settlement_service import compute_settlement

settlement_bp = Blueprint('settlement', __name__)

@settlement_bp.route('/<trip_id>', methods=['GET'])
def get_settlement(trip_id):
    return jsonify(compute_settlement(trip_id))
