"""FX Rates API."""
from flask import Blueprint, request, jsonify
from db.database import query_db, rows_to_list
from services.fx_service import convert, get_all_rates
from decimal import Decimal

fx_bp = Blueprint('fx', __name__)

@fx_bp.route('/rates', methods=['GET'])
def get_rates():
    target = request.args.get('target', 'INR')
    rate_date = request.args.get('date')
    rates = get_all_rates(target, rate_date)
    return jsonify({'target_currency': target, 'rates': rates})

@fx_bp.route('/convert', methods=['GET'])
def convert_currency():
    from_cur = request.args.get('from', 'USD').upper()
    to_cur = request.args.get('to', 'INR').upper()
    amount = request.args.get('amount', '1')
    rate_date = request.args.get('date')
    try:
        converted, rate = convert(amount, from_cur, to_cur, rate_date)
        return jsonify({
            'from': from_cur,
            'to': to_cur,
            'amount': float(amount),
            'converted': float(converted),
            'rate': float(rate),
            'formatted': f"{from_cur} {float(amount):,.2f} = {to_cur} {float(converted):,.2f} (@ {float(rate):.4f})"
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@fx_bp.route('/supported', methods=['GET'])
def get_supported_currencies():
    """List of supported currencies with symbols and names."""
    currencies = [
        {'code': 'INR', 'symbol': '₹', 'name': 'Indian Rupee', 'flag': '🇮🇳'},
        {'code': 'USD', 'symbol': '$', 'name': 'US Dollar', 'flag': '🇺🇸'},
        {'code': 'EUR', 'symbol': '€', 'name': 'Euro', 'flag': '🇪🇺'},
        {'code': 'GBP', 'symbol': '£', 'name': 'British Pound', 'flag': '🇬🇧'},
        {'code': 'THB', 'symbol': '฿', 'name': 'Thai Baht', 'flag': '🇹🇭'},
        {'code': 'SGD', 'symbol': 'S$', 'name': 'Singapore Dollar', 'flag': '🇸🇬'},
        {'code': 'JPY', 'symbol': '¥', 'name': 'Japanese Yen', 'flag': '🇯🇵'},
        {'code': 'AED', 'symbol': 'د.إ', 'name': 'UAE Dirham', 'flag': '🇦🇪'},
        {'code': 'AUD', 'symbol': 'A$', 'name': 'Australian Dollar', 'flag': '🇦🇺'},
        {'code': 'CAD', 'symbol': 'C$', 'name': 'Canadian Dollar', 'flag': '🇨🇦'},
        {'code': 'CHF', 'symbol': 'CHF', 'name': 'Swiss Franc', 'flag': '🇨🇭'},
    ]
    return jsonify({'currencies': currencies})


@fx_bp.route('/live-rates', methods=['GET'])
def get_live_rates():
    """Fetch live rates from ExchangeRate-API with base currency."""
    base = request.args.get('base', 'USD').upper()
    import json
    import urllib.request
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        req = urllib.request.Request(url, headers={'User-Agent': 'TripWalletAI/1.0'})
        with urllib.request.urlopen(req, timeout=3.5) as res:
            if res.status == 200:
                data = json.loads(res.read().decode('utf-8'))
                return jsonify({
                    'base': base,
                    'last_updated': data.get('time_last_update_utc'),
                    'rates': data.get('rates', {})
                })
    except Exception as e:
        # Fallback to local rates
        rates = get_all_rates(base)
        return jsonify({'base': base, 'rates': rates, 'source': 'local_fallback'})

