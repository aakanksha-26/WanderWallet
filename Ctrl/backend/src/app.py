"""
WanderWallet — Backend API Server
Flask REST API with SQLite database, decimal math, and AI services.
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from db.database import init_db
from routes.trips import trips_bp
from routes.expenses import expenses_bp
from routes.budgets import budgets_bp
from routes.fx import fx_bp
from routes.ai_routes import ai_bp
from routes.receipts import receipts_bp
from routes.settlement import settlement_bp
from routes.dashboard import dashboard_bp
from routes.itineraries import itineraries_bp
from routes.hotels import hotels_bp
from routes.transit import transit_bp


def create_app():
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False

    # CORS — allow frontend dev server
    CORS(app, origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "null",  # file:// protocol for demo
    ], supports_credentials=True)

    # Register blueprints
    app.register_blueprint(trips_bp,      url_prefix='/api/trips')
    app.register_blueprint(expenses_bp,   url_prefix='/api/expenses')
    app.register_blueprint(budgets_bp,    url_prefix='/api/budgets')
    app.register_blueprint(fx_bp,         url_prefix='/api/fx')
    app.register_blueprint(ai_bp,         url_prefix='/api/ai')
    app.register_blueprint(receipts_bp,   url_prefix='/api/receipts')
    app.register_blueprint(settlement_bp, url_prefix='/api/settlement')
    app.register_blueprint(dashboard_bp,  url_prefix='/api/dashboard')
    app.register_blueprint(itineraries_bp, url_prefix='/api/itineraries')
    app.register_blueprint(hotels_bp,     url_prefix='/api/hotels')
    app.register_blueprint(transit_bp,    url_prefix='/api/transit')

    # Health check & Root Endpoints
    from db.database import IS_POSTGRES, SUPABASE_URL

    @app.route('/api/health')
    def health():
        return {
            'status': 'ok',
            'service': 'WanderWallet Backend',
            'version': '1.0.0',
            'database': 'supabase_postgresql' if IS_POSTGRES else 'sqlite',
            'supabase_connected': bool(IS_POSTGRES),
            'supabase_project': SUPABASE_URL if IS_POSTGRES else None
        }

    @app.route('/')
    @app.route('/api')
    @app.route('/api/')
    def root_dashboard():
        from flask import request, jsonify, render_template_string
        accept = request.headers.get('Accept', '')
        if 'application/json' in accept and 'text/html' not in accept:
            return jsonify({
                'service': 'WanderWallet Backend API',
                'status': 'online',
                'version': '1.0.0',
                'port': int(os.getenv('PORT', 5001)),
                'database': 'supabase_postgresql' if IS_POSTGRES else 'sqlite',
                'supabase_connected': bool(IS_POSTGRES),
                'supabase_project': SUPABASE_URL if IS_POSTGRES else None,
                'frontend_url': 'http://localhost:3000',
                'endpoints': {
                    'health': '/api/health',
                    'trips': '/api/trips/',
                    'expenses': '/api/expenses/',
                    'budgets': '/api/budgets/',
                    'fx': '/api/fx/',
                    'ai': '/api/ai/',
                    'receipts': '/api/receipts/',
                    'settlement': '/api/settlement/<trip_id>',
                    'dashboard': '/api/dashboard/<trip_id>',
                    'itineraries': '/api/itineraries/<trip_id>',
                    'hotels': '/api/hotels/<trip_id>',
                    'transit': '/api/transit/<trip_id>'
                }
            })

        db_name = "Supabase PostgreSQL (Cloud)" if IS_POSTGRES else "SQLite (Local Fallback)"
        db_badge = "Connected 🟢" if IS_POSTGRES else "Active 🟡"
        port_num = os.getenv('PORT', '5001')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WanderWallet Backend API — Online</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #7A1F3D;
      --primary-dark: #4A0E22;
      --accent-gold: #D4A017;
      --bg: #0D0408;
      --surface: #1E0A14;
      --surface-border: rgba(212,160,23,0.22);
      --text: #FDFBF7;
      --text-muted: #A38C96;
      --success: #22c55e;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 0%, #360B1C 0%, var(--bg) 75%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem 1.5rem;
    }}
    .card {{
      background: rgba(30, 10, 20, 0.85);
      border: 1px solid var(--surface-border);
      border-radius: 24px;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6), 0 0 40px rgba(122, 31, 61, 0.35);
      max-width: 680px;
      width: 100%;
      padding: 2.75rem;
      text-align: center;
      animation: fadeIn 0.4s ease-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(14px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.4);
      color: var(--success);
      font-size: 0.82rem;
      font-weight: 700;
      padding: 0.35rem 0.95rem;
      border-radius: 999px;
      margin-bottom: 1.25rem;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 10px var(--success);
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
      0% {{ transform: scale(1); opacity: 1; }}
      50% {{ transform: scale(1.4); opacity: 0.6; }}
      100% {{ transform: scale(1); opacity: 1; }}
    }}
    h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 0.6rem;
      background: linear-gradient(135deg, #FFF 40%, var(--accent-gold) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    p.lead {{
      color: var(--text-muted);
      font-size: 0.98rem;
      line-height: 1.6;
      margin-bottom: 2rem;
    }}
    .info-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      margin-bottom: 2rem;
      text-align: left;
    }}
    .info-box {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 14px;
      padding: 1rem 1.15rem;
    }}
    .info-box label {{
      display: block;
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.25rem;
    }}
    .info-box span {{
      font-size: 0.92rem;
      font-weight: 600;
      color: #fff;
    }}
    .actions {{
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }}
    .btn-main {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.6rem;
      background: linear-gradient(135deg, var(--primary) 0%, #9e2a50 100%);
      color: white;
      text-decoration: none;
      font-weight: 700;
      font-size: 1.05rem;
      padding: 0.95rem 1.75rem;
      border-radius: 14px;
      border: 1px solid rgba(212,160,23,0.3);
      box-shadow: 0 8px 24px rgba(122, 31, 61, 0.45);
      transition: all 0.2s ease;
    }}
    .btn-main:hover {{
      transform: translateY(-2px);
      box-shadow: 0 12px 30px rgba(122, 31, 61, 0.65);
      background: linear-gradient(135deg, #902447 0%, #b8335f 100%);
    }}
    .quick-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      justify-content: center;
      margin-top: 1.5rem;
    }}
    .pill-link {{
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.78rem;
      padding: 0.35rem 0.75rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.09);
      border-radius: 8px;
      transition: all 0.15s ease;
    }}
    .pill-link:hover {{
      color: #fff;
      border-color: var(--accent-gold);
      background: rgba(212, 160, 23, 0.1);
    }}
    .note {{
      margin-top: 1.5rem;
      font-size: 0.76rem;
      color: #7e6973;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="status-badge">
      <div class="status-dot"></div>
      API Server Online & Healthy
    </div>
    <h1>WanderWallet Backend</h1>
    <p class="lead">Autonomous Multi-Currency Travel CFO REST Engine with Decimal Financial Math, Tesseract OCR, and Cloud Supabase DB.</p>

    <div class="info-grid">
      <div class="info-box">
        <label>Active Port</label>
        <span>http://localhost:{port_num}</span>
      </div>
      <div class="info-box">
        <label>Database Engine</label>
        <span>{db_name} ({db_badge})</span>
      </div>
      <div class="info-box">
        <label>API Version</label>
        <span>v1.0.0 (Production Ready)</span>
      </div>
      <div class="info-box">
        <label>Active Blueprints</label>
        <span>11 Core Microservices</span>
      </div>
    </div>

    <div class="actions">
      <a href="http://localhost:3000" class="btn-main">
        🚀 Launch WanderWallet Web App (localhost:3000)
      </a>
    </div>

    <div class="quick-links">
      <a href="/api/health" class="pill-link">🩺 /api/health</a>
      <a href="/api/trips/" class="pill-link">✈️ /api/trips</a>
      <a href="/api/dashboard/trp_goa_2026" class="pill-link">📊 /api/dashboard/trp_goa_2026</a>
      <a href="/api/itineraries/trp_goa_2026" class="pill-link">🗓️ /api/itineraries</a>
      <a href="/api/hotels/trp_goa_2026" class="pill-link">🏨 /api/hotels</a>
      <a href="/api/transit/trp_goa_2026" class="pill-link">🚆 /api/transit</a>
      <a href="/api/settlement/trp_goa_2026" class="pill-link">🤝 /api/settlement</a>
      <a href="/api/ai/recommendations/trp_goa_2026" class="pill-link">🤖 /api/ai/recommendations</a>
    </div>

    <p class="note">💡 Running on port {port_num} (port 5000 is reserved by macOS AirPlay Receiver).</p>
  </div>
</body>
</html>
"""
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    # Initialize database
    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    print(f"🚀 WanderWallet Backend running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
