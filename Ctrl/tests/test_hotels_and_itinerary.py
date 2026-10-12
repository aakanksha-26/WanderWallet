"""Tests for Hotels, Recommendation Engine, Booking Links, Transit Route, and Itineraries."""
import sys
from pathlib import Path

# Add backend/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import pytest
# pyrefly: ignore [missing-import]
from app import create_app
# pyrefly: ignore [missing-import]
from db.database import init_db, query_db, mutate_db, row_to_dict

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_hotels_all_destinations(client):
    """Verify curated hotel recommendations exist for all demo trips."""
    destinations = ['goa', 'bali', 'paris', 'london', 'dubai', 'kashmir']
    for d in destinations:
        res = client.get(f'/api/hotels?destination={d}')
        assert res.status_code == 200
        data = res.get_json()
        assert 'hotels' in data
        assert len(data['hotels']) >= 4
        # Check recommendation badge, rating, price, and booking url
        has_rec = any(h.get('recommended') is True for h in data['hotels'])
        assert has_rec, f"Destination {d} should have at least one recommended hotel"
        for h in data['hotels']:
            assert 'name' in h
            assert 'price_per_night' in h
            assert 'currency' in h
            assert 'booking_url' in h
            assert h['booking_url'].startswith('http')
            assert 'recommendation_badge' in h
            assert 'recommendation_reason' in h
            assert 'amenities' in h

def test_transit_route_calculation(client):
    """Test start place and destination route planner."""
    res = client.get('/api/hotels?origin=Mumbai,%20India&destination=Goa,%20India')
    assert res.status_code == 200
    data = res.get_json()
    assert 'route' in data
    route = data['route']
    assert 'flight_badge' in route
    assert 'flight_fare' in route
    assert 'booking_link' in route

def test_add_hotel_to_itinerary(client):
    """Test adding a chosen hotel to trip itinerary."""
    res = client.post('/api/hotels/add-to-itinerary', json={
        'trip_id': 'trp_goa_2026',
        'day_number': 1,
        'hotel_id': 'htl_goa_taj'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert 'item_id' in data
    assert 'Taj Holiday Village' in data['hotel_name']

def test_update_trip_route(client):
    """Test updating journey route start place and destination."""
    res = client.post('/api/hotels/update-route', json={
        'trip_id': 'trp_goa_2026',
        'origin': 'Delhi, India',
        'destination': 'Goa, India'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['origin'] == 'Delhi, India'
    assert data['destination'] == 'Goa, India'
    assert len(data['hotels']) >= 4

def test_transit_api_all_destinations(client):
    """Verify transit data has flights, trains, metro, cabs, and booking links for all destinations."""
    for d in ['goa', 'bali', 'paris', 'london', 'dubai', 'kashmir']:
        res = client.get(f'/api/transit?destination={d}')
        assert res.status_code == 200
        data = res.get_json()
        assert len(data['flights']) >= 1
        assert len(data['trains']) >= 1
        assert len(data['metro']) >= 1
        assert len(data['cabs']) >= 1
        assert 'summary' in data
        assert 'fastest' in data['summary']
        assert 'eco_friendly' in data['summary']
        # Check flight details
        flt = data['flights'][0]
        assert 'carrier' in flt
        assert 'fare' in flt
        assert flt['booking_link'].startswith('http')
        # Check train details
        trn = data['trains'][0]
        assert 'name' in trn
        assert 'fare' in trn
        assert 'carbon_kg' in trn
        assert trn['booking_link'].startswith('http')
        # Check cab details
        cab = data['cabs'][0]
        assert 'provider' in cab
        assert 'fare_min' in cab

def test_transit_book_and_expense_actions(client):
    """Test planning transit into itinerary and logging transport expense."""
    # Plan transit into itinerary
    res1 = client.post('/api/transit/book-or-plan', json={
        'trip_id': 'trp_goa_2026',
        'day_number': 1,
        'title': 'Vande Bharat Express (Mumbai -> Goa)',
        'transit_type': 'transport',
        'fare': 2450.0,
        'currency': 'INR',
        'carbon_kg': 12.1,
        'duration': '7h 45m'
    })
    assert res1.status_code == 201
    assert 'item_id' in res1.get_json()

    # Log as transport expense
    res2 = client.post('/api/transit/log-expense', json={
        'trip_id': 'trp_goa_2026',
        'description': 'Uber Premier to Airport',
        'amount': 1250.0,
        'currency': 'INR'
    })
    assert res2.status_code == 201
    assert res2.get_json()['category'] == 'transport'

