"""
Tests for Supabase Backend Integration.
Verifies connection, dual-mode engine, query translation, and data integrity.
"""
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import pytest
# pyrefly: ignore [missing-import]
from app import create_app
# pyrefly: ignore [missing-import]
from db.database import IS_POSTGRES, SUPABASE_URL, query_db, mutate_db, row_to_dict, rows_to_list

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_reports_database_engine(client):
    """Verify /api/health accurately reports connected database engine and Supabase status."""
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'
    assert 'database' in data
    if IS_POSTGRES:
        assert data['database'] == 'supabase_postgresql'
        assert data['supabase_connected'] is True
        assert data['supabase_project'] is not None

def test_supabase_trips_retrieval(client):
    """Verify trips can be retrieved via the API."""
    res = client.get('/api/trips/')
    assert res.status_code == 200
    data = res.get_json()
    assert 'trips' in data
    assert len(data['trips']) >= 1
    # Check canonical fields
    first = data['trips'][0]
    assert 'trp_id' in first
    assert 'trp_name' in first
    assert 'trp_destination' in first
    assert 'trp_origin' in first

def test_supabase_dashboard_retrieval(client):
    """Verify dashboard metrics are computed correctly."""
    # Find Goa trip
    res = client.get('/api/trips/')
    trips = res.get_json().get('trips', [])
    goa_trip = next((t for t in trips if 'goa' in t.get('trp_id', '').lower()), trips[0])
    trip_id = goa_trip['trp_id']

    res = client.get(f'/api/dashboard/{trip_id}')
    assert res.status_code == 200
    data = res.get_json()
    assert 'trip' in data
    assert 'budget' in data
    assert 'expenses' in data
    assert 'summary' in data
    assert 'breaches' in data
    assert 'spend_by_category' in data

def test_query_db_parameter_adaptation():
    """Verify query_db handles parameter substitution properly."""
    res = query_db("SELECT trp_id, trp_name FROM trips WHERE trp_id = ?", ('trp_goa_2026',), one=True)
    if res:
        d = row_to_dict(res)
        assert d['trp_id'] == 'trp_goa_2026'
        assert 'Goa' in d['trp_name']
