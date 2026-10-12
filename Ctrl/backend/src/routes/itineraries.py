"""Itinerary API routes — Day-by-day trip planner with interactive maps and price categorization."""
import uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, rows_to_list, row_to_dict

itineraries_bp = Blueprint('itineraries', __name__)

# Ensure itm_cost_tier column exists
try:
    mutate_db("ALTER TABLE itinerary_items ADD COLUMN itm_cost_tier TEXT")
except Exception:
    pass


def _classify_cost_tier(cost, currency='INR', explicit_tier=None):
    """Classify place into 'free', 'budget', or 'expensive'."""
    if explicit_tier in ('free', 'budget', 'expensive'):
        return explicit_tier
    if cost is None or cost == '' or float(cost or 0) == 0:
        return 'free'
    try:
        val = float(cost)
    except (ValueError, TypeError):
        return 'free'

    if val == 0:
        return 'free'

    thresholds = {
        'INR': 1500,
        'USD': 30,
        'EUR': 30,
        'GBP': 25,
        'AED': 100,
        'IDR': 300000,
        'THB': 1000,
        'SGD': 40,
        'JPY': 4500,
    }
    th = thresholds.get(currency or 'INR', 1500)
    return 'budget' if val <= th else 'expensive'


# ─── Itineraries CRUD ──────────────────────────────────────────────────────────

@itineraries_bp.route('/<trip_id>', methods=['GET'])
def get_itinerary(trip_id):
    """Get or auto-create the itinerary for a trip, with all day items and linked expenses."""
    itn = row_to_dict(query_db(
        "SELECT * FROM itineraries WHERE itn_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    ))
    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    if not itn:
        itn_id = f"itn_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        mutate_db(
            "INSERT INTO itineraries (itn_id, itn_trip_id, itn_title, itn_notes, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (itn_id, trip_id, f"{trip['trp_name']} Itinerary", None, 'active', now, now)
        )
        itn = row_to_dict(query_db("SELECT * FROM itineraries WHERE itn_id = ?", (itn_id,), one=True))

    # Fetch all items grouped by day
    items = rows_to_list(query_db(
        "SELECT * FROM itinerary_items WHERE itm_itinerary_id = ? AND status = 'active' ORDER BY itm_day_number, itm_start_time, itm_title",
        (itn['itn_id'],)
    ))

    cur = trip.get('trp_home_currency', 'INR')
    free_count = 0
    budget_count = 0
    expensive_count = 0
    total_est_cost = 0.0

    for itm in items:
        tier = itm.get('itm_cost_tier')
        if not tier:
            tier = _classify_cost_tier(itm.get('itm_estimated_cost'), itm.get('itm_currency') or cur)
            itm['itm_cost_tier'] = tier
        if tier == 'free':
            free_count += 1
        elif tier == 'budget':
            budget_count += 1
        elif tier == 'expensive':
            expensive_count += 1
        if itm.get('itm_estimated_cost'):
            total_est_cost += float(itm['itm_estimated_cost'])

    # Build day structure from trip dates
    days = _build_day_structure(trip, items)

    # Get expenses per day
    expenses = rows_to_list(query_db(
        "SELECT * FROM expenses WHERE exp_trip_id = ? AND status = 'active' ORDER BY exp_date",
        (trip_id,)
    ))
    expenses_by_date = {}
    for exp in expenses:
        d = exp.get('exp_date', '')
        expenses_by_date.setdefault(d, []).append(exp)

    # Attach expenses to days
    for day in days:
        day['expenses'] = expenses_by_date.get(day['date'], [])
        day['day_total'] = sum(float(e.get('exp_home_amount', 0)) for e in day['expenses'])

    return jsonify({
        'itinerary': itn,
        'days': days,
        'trip': trip,
        'total_items': len(items),
        'free_count': free_count,
        'budget_count': budget_count,
        'expensive_count': expensive_count,
        'total_est_cost': total_est_cost,
    })


def _build_day_structure(trip, items):
    """Build day-by-day structure from trip dates."""
    days = []
    if not trip:
        return days

    try:
        start = datetime.strptime(trip['trp_start_date'], '%Y-%m-%d')
        end = datetime.strptime(trip['trp_end_date'], '%Y-%m-%d')
    except (ValueError, TypeError):
        return days

    items_by_day = {}
    for itm in items:
        dn = itm['itm_day_number']
        items_by_day.setdefault(dn, []).append(itm)

    total_days = max(1, (end - start).days + 1)
    for i in range(total_days):
        day_date = start + timedelta(days=i)
        day_num = i + 1
        days.append({
            'day_number': day_num,
            'date': day_date.strftime('%Y-%m-%d'),
            'date_display': day_date.strftime('%a, %d %b %Y'),
            'items': items_by_day.get(day_num, []),
        })
    return days


# ─── Itinerary Items CRUD ──────────────────────────────────────────────────────

@itineraries_bp.route('/<trip_id>/items', methods=['POST'])
def add_item(trip_id):
    """Add an activity/place to a specific day of the trip itinerary."""
    data = request.get_json(force=True)

    # Auto-get or create itinerary
    itn = row_to_dict(query_db(
        "SELECT * FROM itineraries WHERE itn_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    ))
    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    if not itn:
        itn_id = f"itn_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        mutate_db(
            "INSERT INTO itineraries (itn_id, itn_trip_id, itn_title, itn_notes, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (itn_id, trip_id, f"{trip['trp_name']} Itinerary", None, 'active', now, now)
        )
        itn = {'itn_id': itn_id}

    day_number = int(data.get('day_number', 1))
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400

    # Calculate date from trip start + day_number
    try:
        start = datetime.strptime(trip['trp_start_date'], '%Y-%m-%d')
        item_date = (start + timedelta(days=day_number - 1)).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        item_date = trip.get('trp_start_date', '')

    cur = data.get('currency', trip.get('trp_home_currency', 'INR'))
    est_cost = data.get('estimated_cost')
    raw_tier = data.get('cost_tier')
    tier = _classify_cost_tier(est_cost, cur, raw_tier)
    if tier == 'free' and (est_cost is None or est_cost == ''):
        est_cost = 0

    itm_id = f"itm_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    mutate_db(
        """INSERT INTO itinerary_items
        (itm_id, itm_itinerary_id, itm_day_number, itm_item_date, itm_title, itm_type,
         itm_location, itm_lat, itm_lng, itm_start_time, itm_end_time,
         itm_estimated_cost, itm_currency, itm_notes, status, created_at, updated_at, itm_cost_tier)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (itm_id, itn['itn_id'], day_number, item_date, title,
         data.get('type', 'activity'),
         data.get('location', ''),
         data.get('lat'), data.get('lng'),
         data.get('start_time', ''),
         data.get('end_time', ''),
         est_cost,
         cur,
         data.get('notes', ''),
         'active', now, now, tier)
    )
    return jsonify({'item_id': itm_id, 'cost_tier': tier, 'message': 'Activity added'}), 201


@itineraries_bp.route('/<trip_id>/items/<item_id>', methods=['DELETE'])
def remove_item(trip_id, item_id):
    """Soft-delete an itinerary item."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    mutate_db(
        "UPDATE itinerary_items SET status = 'deleted', updated_at = ? WHERE itm_id = ?",
        (now, item_id)
    )
    return jsonify({'message': 'Item removed'})


@itineraries_bp.route('/<trip_id>/items/<item_id>', methods=['PATCH'])
def update_item(trip_id, item_id):
    """Update an itinerary item."""
    data = request.get_json(force=True)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    updates = []
    params = []
    field_map = {
        'title': 'itm_title', 'type': 'itm_type', 'location': 'itm_location',
        'lat': 'itm_lat', 'lng': 'itm_lng', 'start_time': 'itm_start_time',
        'end_time': 'itm_end_time', 'estimated_cost': 'itm_estimated_cost',
        'currency': 'itm_currency', 'notes': 'itm_notes', 'day_number': 'itm_day_number',
        'cost_tier': 'itm_cost_tier',
    }
    for key, col in field_map.items():
        if key in data:
            updates.append(f"{col} = ?")
            params.append(data[key])

    if not updates:
        return jsonify({'error': 'No fields to update'}), 400

    updates.append("updated_at = ?")
    params.append(now)
    params.append(item_id)

    mutate_db(f"UPDATE itinerary_items SET {', '.join(updates)} WHERE itm_id = ?", params)
    return jsonify({'message': 'Item updated'})


# ─── Seed Demo Itinerary ──────────────────────────────────────────────────────

@itineraries_bp.route('/<trip_id>/seed-demo', methods=['POST'])
def seed_demo_itinerary(trip_id):
    """Seed a demo itinerary with full activities for all days of the trip."""
    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    force = request.args.get('force') in ('true', '1') or (request.is_json and request.get_json(silent=True) and request.get_json().get('force'))

    # Check if itinerary items already exist
    existing = row_to_dict(query_db(
        "SELECT i.itn_id FROM itineraries i JOIN itinerary_items ii ON ii.itm_itinerary_id = i.itn_id WHERE i.itn_trip_id = ? AND i.status = 'active' AND ii.status = 'active' LIMIT 1",
        (trip_id,), one=True
    ))

    if existing and not force:
        # Check if the existing items cover fewer than 5 items
        count_res = row_to_dict(query_db(
            "SELECT count(*) as c FROM itinerary_items WHERE itm_itinerary_id = ? AND status = 'active'",
            (existing['itn_id'],), one=True
        ))
        if count_res and count_res['c'] >= 10:
            return jsonify({'message': 'Demo data already complete', 'skipped': True})
        # If less than 10, proceed to populate full itinerary
        force = True

    dest = (trip.get('trp_destination') or '').lower()

    # Pick destination-appropriate activities
    if 'bali' in dest:
        activities = _DEMO_BALI
    elif 'london' in dest:
        activities = _DEMO_LONDON
    elif 'paris' in dest:
        activities = _DEMO_PARIS
    elif 'dubai' in dest:
        activities = _DEMO_DUBAI
    elif 'kashmir' in dest:
        activities = _DEMO_KASHMIR
    else:
        activities = _DEMO_GOA  # fallback

    # Ensure itinerary exists
    itn = row_to_dict(query_db(
        "SELECT * FROM itineraries WHERE itn_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    ))
    if not itn:
        itn_id = f"itn_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        mutate_db(
            "INSERT INTO itineraries (itn_id, itn_trip_id, itn_title, itn_notes, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (itn_id, trip_id, f"{trip['trp_name']} Itinerary", None, 'active', now, now)
        )
    else:
        itn_id = itn['itn_id']

    if force:
        # Delete existing items for clean full replacement
        mutate_db("DELETE FROM itinerary_items WHERE itm_itinerary_id = ?", (itn_id,))

    try:
        start_date = datetime.strptime(trip['trp_start_date'], '%Y-%m-%d')
    except (ValueError, TypeError):
        start_date = datetime.now()

    cur = trip.get('trp_home_currency', 'INR')
    count = 0
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    for act in activities:
        day_num = act['day']
        item_date = (start_date + timedelta(days=day_num - 1)).strftime('%Y-%m-%d')
        itm_id = f"itm_{uuid.uuid4().hex[:12]}"
        tier = act.get('tier') or _classify_cost_tier(act.get('cost'), cur)
        mutate_db(
            """INSERT INTO itinerary_items
            (itm_id, itm_itinerary_id, itm_day_number, itm_item_date, itm_title, itm_type,
             itm_location, itm_lat, itm_lng, itm_start_time, itm_end_time,
             itm_estimated_cost, itm_currency, itm_notes, status, created_at, updated_at, itm_cost_tier)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (itm_id, itn_id, day_num, item_date, act['title'], act.get('type', 'activity'),
             act.get('location', ''), act.get('lat'), act.get('lng'),
             act.get('start', ''), act.get('end', ''),
             act.get('cost'), cur, act.get('notes', ''),
             'active', now, now, tier)
        )
        count += 1

    return jsonify({'message': f'Seeded {count} activities across all days', 'count': count}), 201


# ─── Demo Data per Destination (Categorized: Free, Budget-Friendly, Expensive) ──

_DEMO_GOA = [
    # Day 1: Arrival & Coastal Welcome
    {'day': 1, 'title': 'Dabolim Airport Arrival Cab', 'type': 'transport', 'location': 'Dabolim Airport, Goa', 'lat': 15.3809, 'lng': 73.8314, 'start': '10:00', 'end': '11:15', 'cost': 3500, 'tier': 'expensive', 'notes': 'Pre-booked private AC cab to North Goa'},
    {'day': 1, 'title': 'Check-in Taj Holiday Village Resort', 'type': 'hotel', 'location': 'Sinquerim, Candolim', 'lat': 15.5015, 'lng': 73.7690, 'start': '12:00', 'end': '13:00', 'cost': 8500, 'tier': 'expensive', 'notes': 'Heritage cottage resort by Sinquerim beach'},
    {'day': 1, 'title': 'Seafood Lunch at Fisherman\'s Wharf', 'type': 'meal', 'location': 'Cavelossim', 'lat': 15.1649, 'lng': 73.9384, 'start': '13:30', 'end': '15:00', 'cost': 1800, 'tier': 'budget', 'notes': 'Goan rawa fry kingfish, curry & poi'},
    {'day': 1, 'title': 'Sunset Walk & Photography at Baga Beach', 'type': 'activity', 'location': 'Baga Beach', 'lat': 15.5552, 'lng': 73.7518, 'start': '17:00', 'end': '19:00', 'cost': 0, 'tier': 'free', 'notes': 'Golden hour sunset, beach stroll & live shack music'},

    # Day 2: Historic Forts & High-Adrenaline Watersports
    {'day': 2, 'title': 'Aguada Fort & Sea Ramparts Walk', 'type': 'activity', 'location': 'Fort Aguada, Candolim', 'lat': 15.4921, 'lng': 73.7736, 'start': '08:30', 'end': '10:30', 'cost': 0, 'tier': 'free', 'notes': '17th-century Portuguese fortress overlooking Arabian sea'},
    {'day': 2, 'title': 'Parasailing & Jet Ski at Calangute', 'type': 'activity', 'location': 'Calangute Beach', 'lat': 15.5438, 'lng': 73.7554, 'start': '11:00', 'end': '13:30', 'cost': 3500, 'tier': 'expensive', 'notes': 'Tandem parasail + high-speed wave runner'},
    {'day': 2, 'title': 'Beachside Lunch at Britto\'s Shack', 'type': 'meal', 'location': 'Baga Beach Road', 'lat': 15.5530, 'lng': 73.7512, 'start': '14:00', 'end': '15:30', 'cost': 950, 'tier': 'budget', 'notes': 'Prawn balchão, chilled tender coconut & Bebinca'},

    # Day 3: UNESCO Heritage & Wilderness Waterfalls
    {'day': 3, 'title': 'Basilica of Bom Jesus & Se Cathedral', 'type': 'activity', 'location': 'Old Goa Churches, Velha Goa', 'lat': 15.5004, 'lng': 73.9113, 'start': '09:00', 'end': '11:30', 'cost': 0, 'tier': 'free', 'notes': 'World Heritage site — mortal remains of St. Francis Xavier'},
    {'day': 3, 'title': 'Archaeological Museum Guide & Entry', 'type': 'activity', 'location': 'Old Goa Convent', 'lat': 15.5028, 'lng': 73.9126, 'start': '11:30', 'end': '12:45', 'cost': 250, 'tier': 'budget', 'notes': 'Portraits of Portuguese viceroys & ancient artefacts'},
    {'day': 3, 'title': 'Dudhsagar Waterfalls Jeep Safari', 'type': 'activity', 'location': 'Dudhsagar Falls, Mollem', 'lat': 15.3144, 'lng': 74.3143, 'start': '13:30', 'end': '17:30', 'cost': 4500, 'tier': 'expensive', 'notes': '4x4 Bhagwan Mahavir jungle trek to milky cascade'},
    {'day': 3, 'title': 'Cliffside Sunset Dinner at Thalassa', 'type': 'meal', 'location': 'Vagator Cliff', 'lat': 15.5971, 'lng': 73.7350, 'start': '19:30', 'end': '22:00', 'cost': 3200, 'tier': 'expensive', 'notes': 'Greek fine dining, fire dancers & panoramic ocean views'},

    # Day 4: Spice Aromas & Sunset Ramparts
    {'day': 4, 'title': 'Sahakari Spice Plantation Tour & Buffet', 'type': 'activity', 'location': 'Curti, Ponda', 'lat': 15.4130, 'lng': 74.0350, 'start': '09:30', 'end': '13:00', 'cost': 1200, 'tier': 'budget', 'notes': 'Aromatic spice walk, elephant bathing & traditional Goan buffet'},
    {'day': 4, 'title': 'Chapora Fort Panoramic Lookout', 'type': 'activity', 'location': 'Chapora Fort, Vagator', 'lat': 15.6058, 'lng': 73.7364, 'start': '16:00', 'end': '17:45', 'cost': 0, 'tier': 'free', 'notes': 'Iconic Bollywood Dil Chahta Hai ramparts over Chapora river'},
    {'day': 4, 'title': 'Anjuna Flea Market Souvenirs & Crafts', 'type': 'activity', 'location': 'Anjuna Beach', 'lat': 15.5735, 'lng': 73.7407, 'start': '18:00', 'end': '20:30', 'cost': 1400, 'tier': 'budget', 'notes': 'Handcrafted silver, Tibetan bowls and spices'},

    # Day 5: Deep Sea Scuba & Casino Royalty
    {'day': 5, 'title': 'Certified Scuba Diving at Grande Island', 'type': 'activity', 'location': 'Grande Island, Marmagao', 'lat': 15.3750, 'lng': 73.8520, 'start': '07:30', 'end': '14:00', 'cost': 4500, 'tier': 'expensive', 'notes': 'Speedboat ride, dolphin spotting, underwater coral dive & lunch'},
    {'day': 5, 'title': 'Morjim Beach Olive Ridley Turtle Stroll', 'type': 'activity', 'location': 'Morjim Beach', 'lat': 15.6174, 'lng': 73.7371, 'start': '16:30', 'end': '18:30', 'cost': 0, 'tier': 'free', 'notes': 'Peaceful sanctuary beach known as Little Russia'},
    {'day': 5, 'title': 'Casino Pride Luxury Riverboat Gala', 'type': 'activity', 'location': 'Mandovi River, Panaji', 'lat': 15.4989, 'lng': 73.8278, 'start': '20:00', 'end': '23:30', 'cost': 3000, 'tier': 'expensive', 'notes': 'Floating luxury casino, live Bollywood dance & multi-cuisine buffet'},

    # Day 6: Portuguese Latin Quarter & Sunset Cruise
    {'day': 6, 'title': 'Fontainhas Latin Quarter Walking Tour', 'type': 'activity', 'location': 'Fontainhas, Panaji', 'lat': 15.4966, 'lng': 73.8322, 'start': '09:00', 'end': '11:30', 'cost': 0, 'tier': 'free', 'notes': 'Pastel-coloured 18th century colonial mansions & tiled streetscapes'},
    {'day': 6, 'title': 'Authentic Goan Thali at Viva Panjim', 'type': 'meal', 'location': 'Cortin, Panaji', 'lat': 15.4981, 'lng': 73.8315, 'start': '12:30', 'end': '14:00', 'cost': 550, 'tier': 'budget', 'notes': 'Traditional Portuguese-Goan heritage cafe in an ancestral villa'},
    {'day': 6, 'title': 'Mandovi River Luxury Yacht Sunset Cruise', 'type': 'activity', 'location': 'Santa Monica Jetty, Panaji', 'lat': 15.5020, 'lng': 73.8300, 'start': '17:00', 'end': '19:00', 'cost': 2500, 'tier': 'expensive', 'notes': 'Private cat-deck cruise with sparkling drinks and folk performance'},

    # Day 7: Peaceful Dawn & Airport Farewell
    {'day': 7, 'title': 'Miramar Beach Sunrise Breeze Stroll', 'type': 'activity', 'location': 'Miramar Beach, Panaji', 'lat': 15.4831, 'lng': 73.8078, 'start': '07:00', 'end': '08:30', 'cost': 0, 'tier': 'free', 'notes': 'Tranquil Arabian sea shore walk where river meets ocean'},
    {'day': 7, 'title': 'Healthy Breakfast at Artjuna Cafe', 'type': 'meal', 'location': 'Anjuna', 'lat': 15.5802, 'lng': 73.7431, 'start': '09:00', 'end': '10:30', 'cost': 650, 'tier': 'budget', 'notes': 'Smoothie bowls, shakshuka & freshly roasted artisanal coffee'},
    {'day': 7, 'title': 'Private Airport Chauffeur Drop-off', 'type': 'transport', 'location': 'Dabolim Airport', 'lat': 15.3809, 'lng': 73.8314, 'start': '12:00', 'end': '13:30', 'cost': 3500, 'tier': 'expensive', 'notes': 'Air-conditioned luxury sedan to airport terminal'},
]

_DEMO_BALI = [
    # Day 1
    {'day': 1, 'title': 'Airport Transfer to Seminyak', 'type': 'transport', 'location': 'Ngurah Rai Airport', 'lat': -8.7480, 'lng': 115.1675, 'start': '14:00', 'end': '15:00', 'cost': 350000, 'tier': 'expensive', 'notes': 'Private airport pickup'},
    {'day': 1, 'title': 'Check-in Alila Seminyak Resort', 'type': 'hotel', 'location': 'Seminyak Beach', 'lat': -8.6912, 'lng': 115.1565, 'start': '15:30', 'end': '16:30', 'cost': 2500000, 'tier': 'expensive', 'notes': 'Beachfront pool villa'},
    {'day': 1, 'title': 'Seminyak Beach Sunset Stroll', 'type': 'activity', 'location': 'Seminyak Beach', 'lat': -8.6900, 'lng': 115.1550, 'start': '17:30', 'end': '19:00', 'cost': 0, 'tier': 'free', 'notes': 'Golden sunset over Indian ocean'},
    # Day 2
    {'day': 2, 'title': 'Tegallalang Rice Terraces Viewpoint', 'type': 'activity', 'location': 'Tegallalang, Ubud', 'lat': -8.4312, 'lng': 115.2794, 'start': '08:00', 'end': '11:00', 'cost': 50000, 'tier': 'budget', 'notes': 'Iconic subak terraced rice fields'},
    {'day': 2, 'title': 'Ubud Monkey Forest Sanctuary', 'type': 'activity', 'location': 'Padangtegal, Ubud', 'lat': -8.5185, 'lng': 115.2587, 'start': '12:30', 'end': '14:30', 'cost': 80000, 'tier': 'budget', 'notes': 'Sacred temple in rainforest with macaques'},
    {'day': 2, 'title': 'Campuhan Ridge Walk at Twilight', 'type': 'activity', 'location': 'Campuhan, Ubud', 'lat': -8.5034, 'lng': 115.2546, 'start': '16:30', 'end': '18:00', 'cost': 0, 'tier': 'free', 'notes': 'Scenic panoramic ridge trail between two rivers'},
    # Day 3
    {'day': 3, 'title': 'Mount Batur Sunrise Volcano Trek', 'type': 'activity', 'location': 'Mount Batur, Kintamani', 'lat': -8.2417, 'lng': 115.3749, 'start': '03:00', 'end': '10:00', 'cost': 750000, 'tier': 'expensive', 'notes': 'Guided trek with volcanic crater steam breakfast'},
    {'day': 3, 'title': 'Tirta Empul Holy Water Temple', 'type': 'activity', 'location': 'Tampaksiring', 'lat': -8.4152, 'lng': 115.3153, 'start': '12:00', 'end': '14:00', 'cost': 50000, 'tier': 'budget', 'notes': 'Sacred balinese water purification ritual'},
    # Day 4
    {'day': 4, 'title': 'Nusa Penida Island Speedboat Day Tour', 'type': 'activity', 'location': 'Sanur Harbour to Nusa Penida', 'lat': -8.7275, 'lng': 115.5444, 'start': '07:00', 'end': '18:00', 'cost': 1200000, 'tier': 'expensive', 'notes': 'Kelingking T-Rex cliff, Broken Beach & Angel Billabong'},
    # Day 5
    {'day': 5, 'title': 'Kuta Beach Morning Surf Lesson', 'type': 'activity', 'location': 'Kuta Beach', 'lat': -8.7181, 'lng': 115.1671, 'start': '08:00', 'end': '10:30', 'cost': 250000, 'tier': 'budget', 'notes': 'Beginner wave coaching with certified instructor'},
    {'day': 5, 'title': 'Tanah Lot Ocean Temple Sunset', 'type': 'activity', 'location': 'Tanah Lot, Tabanan', 'lat': -8.6212, 'lng': 115.0868, 'start': '16:00', 'end': '19:00', 'cost': 60000, 'tier': 'budget', 'notes': 'Offshore ancient Hindu temple at dusk'},
    # Day 6
    {'day': 6, 'title': 'Saraswati Temple Water Palace Garden', 'type': 'activity', 'location': 'Jalan Raya Ubud', 'lat': -8.5050, 'lng': 115.2610, 'start': '09:00', 'end': '10:30', 'cost': 0, 'tier': 'free', 'notes': 'Lotus pond gardens and classical Balinese stone carving'},
    {'day': 6, 'title': 'Ayana Resort Rock Bar & Spa', 'type': 'activity', 'location': 'Jimbaran Bay', 'lat': -8.7875, 'lng': 115.1549, 'start': '15:30', 'end': '21:00', 'cost': 1800000, 'tier': 'expensive', 'notes': 'Seawater thalassotherapy pool and clifftop cocktails'},
    # Day 7
    {'day': 7, 'title': 'Jimbaran Fisherman Beach Morning Walk', 'type': 'activity', 'location': 'Jimbaran Bay', 'lat': -8.7700, 'lng': 115.1680, 'start': '08:00', 'end': '09:30', 'cost': 0, 'tier': 'free', 'notes': 'Traditional colourful jukung outrigger boats'},
    {'day': 7, 'title': 'Airport VIP Departure Transfer', 'type': 'transport', 'location': 'Ngurah Rai Airport', 'lat': -8.7480, 'lng': 115.1675, 'start': '11:30', 'end': '13:00', 'cost': 350000, 'tier': 'expensive', 'notes': 'Final transfer to departure terminal'},
]

_DEMO_LONDON = [
    # Day 1
    {'day': 1, 'title': 'Heathrow Express to Central London', 'type': 'transport', 'location': 'Heathrow Airport', 'lat': 51.4700, 'lng': -0.4543, 'start': '09:00', 'end': '10:15', 'cost': 25, 'tier': 'budget', 'notes': 'Fast 15-minute train to Paddington'},
    {'day': 1, 'title': 'Check-in at The Savoy London', 'type': 'hotel', 'location': 'The Strand, Covent Garden', 'lat': 51.5102, 'lng': -0.1198, 'start': '12:00', 'end': '13:00', 'cost': 450, 'tier': 'expensive', 'notes': 'Iconic Edwardian luxury hotel overlooking Thames'},
    {'day': 1, 'title': 'Trafalgar Square & National Gallery Walk', 'type': 'activity', 'location': 'Trafalgar Square', 'lat': 51.5080, 'lng': -0.1281, 'start': '15:00', 'end': '17:30', 'cost': 0, 'tier': 'free', 'notes': 'Nelson\'s Column and world-class master paintings'},
    # Day 2
    {'day': 2, 'title': 'British Museum Historic Antiquities', 'type': 'activity', 'location': 'Great Russell St, Bloomsbury', 'lat': 51.5194, 'lng': -0.1270, 'start': '09:30', 'end': '13:00', 'cost': 0, 'tier': 'free', 'notes': 'Free admission to Rosetta Stone & Parthenon Sculptures'},
    {'day': 2, 'title': 'West End Musical Theatre Ticket', 'type': 'activity', 'location': 'Victoria Palace Theatre', 'lat': 51.4965, 'lng': -0.1444, 'start': '19:30', 'end': '22:15', 'cost': 120, 'tier': 'expensive', 'notes': 'Stalls seats for award-winning production'},
    # Day 3
    {'day': 3, 'title': 'Tower of London & Crown Jewels', 'type': 'activity', 'location': 'Tower Hill, London', 'lat': 51.5081, 'lng': -0.0759, 'start': '09:00', 'end': '12:00', 'cost': 33, 'tier': 'expensive', 'notes': 'Yeoman Warder Beefeater tour and White Tower'},
    {'day': 3, 'title': 'Borough Market Artisanal Lunch', 'type': 'meal', 'location': 'Southwark Street', 'lat': 51.5055, 'lng': -0.0910, 'start': '12:30', 'end': '14:00', 'cost': 18, 'tier': 'budget', 'notes': 'Gourmet street food: salt beef bagels & wild mushroom risotto'},
    {'day': 3, 'title': 'Thames South Bank Promenade Walk', 'type': 'activity', 'location': 'Queen\'s Walk, South Bank', 'lat': 51.5045, 'lng': -0.1140, 'start': '15:00', 'end': '17:00', 'cost': 0, 'tier': 'free', 'notes': 'St Paul\'s views, Tate Modern exterior & street performers'},
    # Day 4
    {'day': 4, 'title': 'Buckingham Palace Changing of the Guard', 'type': 'activity', 'location': 'Buckingham Palace', 'lat': 51.5014, 'lng': -0.1419, 'start': '10:30', 'end': '12:00', 'cost': 0, 'tier': 'free', 'notes': 'Historic royal pageant with marching band'},
    {'day': 4, 'title': 'Hyde Park & Kensington Gardens Stroll', 'type': 'activity', 'location': 'Hyde Park', 'lat': 51.5073, 'lng': -0.1657, 'start': '14:00', 'end': '16:00', 'cost': 0, 'tier': 'free', 'notes': 'Serpentine lake and Albert Memorial'},
    {'day': 4, 'title': 'London Eye Champagne Capsule Flight', 'type': 'activity', 'location': 'Riverside Building, South Bank', 'lat': 51.5033, 'lng': -0.1195, 'start': '18:00', 'end': '19:30', 'cost': 55, 'tier': 'expensive', 'notes': 'Sunset bird\'s-eye view across Parliament and Big Ben'},
    # Day 5
    {'day': 5, 'title': 'Stonehenge & Roman Baths Day Excursion', 'type': 'activity', 'location': 'Stonehenge, Wiltshire', 'lat': 51.1789, 'lng': -1.8262, 'start': '08:00', 'end': '18:00', 'cost': 95, 'tier': 'expensive', 'notes': 'Full-day luxury coach tour with audio guide'},
    # Day 6
    {'day': 6, 'title': 'Natural History Museum & Earth Galleries', 'type': 'activity', 'location': 'Cromwell Rd, South Kensington', 'lat': 51.4967, 'lng': -0.1764, 'start': '10:00', 'end': '13:00', 'cost': 0, 'tier': 'free', 'notes': 'Free entry: Hope the Blue Whale & dinosaur fossils'},
    {'day': 6, 'title': 'Harrods Luxury Knightsbridge Shopping', 'type': 'activity', 'location': 'Brompton Rd, Knightsbridge', 'lat': 51.4994, 'lng': -0.1633, 'start': '14:30', 'end': '17:30', 'cost': 200, 'tier': 'expensive', 'notes': 'Food halls and designer floor'},
    # Day 7
    {'day': 7, 'title': 'Covent Garden Street Performers Walk', 'type': 'activity', 'location': 'Covent Garden Piazza', 'lat': 51.5117, 'lng': -0.1232, 'start': '09:00', 'end': '10:30', 'cost': 0, 'tier': 'free', 'notes': 'Apple market crafts and morning violinists'},
    {'day': 7, 'title': 'Airport Express Return Transfer', 'type': 'transport', 'location': 'Paddington Station', 'lat': 51.5154, 'lng': -0.1755, 'start': '11:00', 'end': '12:30', 'cost': 25, 'tier': 'budget', 'notes': 'Fast train connection for flight home'},
]

_DEMO_PARIS = [
    # Day 1
    {'day': 1, 'title': 'RER B Express from CDG Airport', 'type': 'transport', 'location': 'Charles de Gaulle Airport', 'lat': 49.0097, 'lng': 2.5479, 'start': '10:00', 'end': '11:30', 'cost': 12, 'tier': 'budget', 'notes': 'High-speed commuter train to Châtelet'},
    {'day': 1, 'title': 'Check-in Le Marais Boutique Hotel', 'type': 'hotel', 'location': 'Rue de Turenne, Le Marais', 'lat': 48.8566, 'lng': 2.3612, 'start': '12:30', 'end': '13:30', 'cost': 320, 'tier': 'expensive', 'notes': 'Chic 17th century Parisian design hotel'},
    {'day': 1, 'title': 'Place des Vosges & Square Louis XIII', 'type': 'activity', 'location': 'Place des Vosges', 'lat': 48.8554, 'lng': 2.3656, 'start': '15:00', 'end': '16:30', 'cost': 0, 'tier': 'free', 'notes': 'Oldest planned square in Paris, Victor Hugo house exterior'},
    {'day': 1, 'title': 'Seine River Cruise with Candlelit Dinner', 'type': 'activity', 'location': 'Pont de l\'Alma', 'lat': 48.8643, 'lng': 2.3020, 'start': '19:30', 'end': '22:00', 'cost': 110, 'tier': 'expensive', 'notes': 'Glass canopy boat with 3-course French wine dinner'},
    # Day 2
    {'day': 2, 'title': 'Musée du Louvre Masterpieces', 'type': 'activity', 'location': 'Rue de Rivoli', 'lat': 48.8606, 'lng': 2.3376, 'start': '09:00', 'end': '13:30', 'cost': 17, 'tier': 'budget', 'notes': 'Mona Lisa, Winged Victory of Samothrace & Venus de Milo'},
    {'day': 2, 'title': 'Tuileries Garden Stroll & Sculptures', 'type': 'activity', 'location': 'Jardin des Tuileries', 'lat': 48.8635, 'lng': 2.3275, 'start': '14:00', 'end': '15:30', 'cost': 0, 'tier': 'free', 'notes': 'Royal French garden between Louvre and Place de la Concorde'},
    # Day 3
    {'day': 3, 'title': 'Eiffel Tower Top Summit Access', 'type': 'activity', 'location': 'Champ de Mars', 'lat': 48.8584, 'lng': 2.2945, 'start': '09:30', 'end': '12:00', 'cost': 29, 'tier': 'budget', 'notes': 'Glass elevator to 276m summit with panoramic view'},
    {'day': 3, 'title': 'Champ de Mars Garden Picnic', 'type': 'activity', 'location': 'Champ de Mars Park', 'lat': 48.8556, 'lng': 2.2986, 'start': '12:30', 'end': '14:00', 'cost': 0, 'tier': 'free', 'notes': 'Baguette, brie and vineyard view beneath iron lady'},
    # Day 4
    {'day': 4, 'title': 'Montmartre Artists Quarter & Sacré-Cœur', 'type': 'activity', 'location': 'Place du Tertre, Montmartre', 'lat': 48.8867, 'lng': 2.3431, 'start': '10:00', 'end': '13:30', 'cost': 0, 'tier': 'free', 'notes': 'Bohemian hill, painters easel square and domed white basilica'},
    {'day': 4, 'title': 'Moulin Rouge Féerie Champagne Cabaret', 'type': 'activity', 'location': 'Boulevard de Clichy, Pigalle', 'lat': 48.8841, 'lng': 2.3322, 'start': '21:00', 'end': '23:30', 'cost': 145, 'tier': 'expensive', 'notes': 'World-famous French cancan show with half bottle of champagne'},
    # Day 5
    {'day': 5, 'title': 'Palace of Versailles Grand Tour & Fountains', 'type': 'activity', 'location': 'Place d\'Armes, Versailles', 'lat': 48.8049, 'lng': 2.1204, 'start': '08:30', 'end': '16:00', 'cost': 27, 'tier': 'budget', 'notes': 'Hall of Mirrors, Queen\'s Bedroom and musical water gardens'},
    # Day 6
    {'day': 6, 'title': 'Champs-Élysées & Arc de Triomphe Views', 'type': 'activity', 'location': 'Place Charles de Gaulle', 'lat': 48.8738, 'lng': 2.2950, 'start': '10:00', 'end': '12:30', 'cost': 16, 'tier': 'budget', 'notes': 'Rooftop vista down twelve grand radiating avenues'},
    {'day': 6, 'title': 'Gourmet Dinner at Jules Verne', 'type': 'meal', 'location': 'Eiffel Tower 2nd Floor', 'lat': 48.8584, 'lng': 2.2945, 'start': '19:30', 'end': '22:30', 'cost': 260, 'tier': 'expensive', 'notes': 'Michelin-starred gastronomy 125 meters above the city'},
    # Day 7
    {'day': 7, 'title': 'Shakespeare and Company Bookshop & Seine Quays', 'type': 'activity', 'location': 'Rue de la Bûcherie, Latin Quarter', 'lat': 48.8526, 'lng': 2.3471, 'start': '09:30', 'end': '11:00', 'cost': 0, 'tier': 'free', 'notes': 'Legendary literary haven across Notre-Dame'},
    {'day': 7, 'title': 'Airport Shuttle Transfer', 'type': 'transport', 'location': 'Gare du Nord', 'lat': 48.8809, 'lng': 2.3553, 'start': '12:30', 'end': '14:00', 'cost': 12, 'tier': 'budget', 'notes': 'Return train to airport'},
]

_DEMO_DUBAI = [
    # Day 1
    {'day': 1, 'title': 'Dubai Airport Taxi to Hotel', 'type': 'transport', 'location': 'Dubai International Airport', 'lat': 25.2532, 'lng': 55.3657, 'start': '16:00', 'end': '17:00', 'cost': 85, 'tier': 'budget', 'notes': 'Official RTA airport taxi transfer'},
    {'day': 1, 'title': 'Check-in Atlantis The Palm Resort', 'type': 'hotel', 'location': 'Crescent Rd, Palm Jumeirah', 'lat': 25.1303, 'lng': 55.1173, 'start': '17:30', 'end': '18:30', 'cost': 1800, 'tier': 'expensive', 'notes': 'Luxury Ocean suite on outer crescent of Palm'},
    {'day': 1, 'title': 'The Pointe Boardwalk Sunset View', 'type': 'activity', 'location': 'Palm Jumeirah Boardwalk', 'lat': 25.1160, 'lng': 55.1190, 'start': '19:00', 'end': '20:30', 'cost': 0, 'tier': 'free', 'notes': 'Scenic seafront walkway looking across Atlantis'},
    # Day 2
    {'day': 2, 'title': 'Burj Khalifa At The Top (124 & 125th Floor)', 'type': 'activity', 'location': 'Financial Center Rd, Downtown', 'lat': 25.1972, 'lng': 55.2744, 'start': '09:00', 'end': '11:30', 'cost': 190, 'tier': 'expensive', 'notes': 'Tallest skyscraper observatory deck in the world'},
    {'day': 2, 'title': 'Dubai Fountain Synchronised Music Show', 'type': 'activity', 'location': 'Burj Lake, Downtown Dubai', 'lat': 25.1960, 'lng': 55.2775, 'start': '18:00', 'end': '19:30', 'cost': 0, 'tier': 'free', 'notes': 'Spectacular dancing water fountain set to Arabic melodies'},
    # Day 3
    {'day': 3, 'title': 'Red Dune Desert Safari & BBQ Camp', 'type': 'activity', 'location': 'Lahbab Desert, Dubai', 'lat': 24.9840, 'lng': 55.4500, 'start': '14:30', 'end': '21:30', 'cost': 320, 'tier': 'expensive', 'notes': '4x4 dune bashing, sandboarding, camel ride & fire show'},
    # Day 4
    {'day': 4, 'title': 'Al Fahidi Historic Neighbourhood Walk', 'type': 'activity', 'location': 'Al Bastakiya, Bur Dubai', 'lat': 25.2631, 'lng': 55.2976, 'start': '09:00', 'end': '11:00', 'cost': 0, 'tier': 'free', 'notes': 'Traditional wind-tower architecture and art galleries'},
    {'day': 4, 'title': 'Traditional Abra Boat Across Dubai Creek', 'type': 'transport', 'location': 'Bur Dubai Abra Station', 'lat': 25.2670, 'lng': 55.2950, 'start': '11:15', 'end': '11:45', 'cost': 2, 'tier': 'budget', 'notes': 'Historical 1 AED wooden boat crossing over the saltwater creek'},
    {'day': 4, 'title': 'Gold & Spice Souk Walking Exploration', 'type': 'activity', 'location': 'Al Ras, Deira', 'lat': 25.2684, 'lng': 55.2981, 'start': '12:00', 'end': '14:00', 'cost': 0, 'tier': 'free', 'notes': 'Glittering jewellery bazaar and aromatic saffron sacks'},
    # Day 5
    {'day': 5, 'title': 'Aquaventure Waterpark Unlimited Pass', 'type': 'activity', 'location': 'Atlantis Palm Jumeirah', 'lat': 25.1303, 'lng': 55.1173, 'start': '10:00', 'end': '16:00', 'cost': 345, 'tier': 'expensive', 'notes': 'World\'s largest waterpark: 105 slides and private beach'},
    # Day 6
    {'day': 6, 'title': 'Dubai Marina Walk & Yacht Promenade', 'type': 'activity', 'location': 'Dubai Marina Walk', 'lat': 25.0780, 'lng': 55.1400, 'start': '16:30', 'end': '18:30', 'cost': 0, 'tier': 'free', 'notes': '7km palm-lined waterfront flanked by illuminated towers'},
    {'day': 6, 'title': 'Sunset Luxury Mega-Yacht Cruise & Dinner', 'type': 'activity', 'location': 'Pier 7, Dubai Marina', 'lat': 25.0805, 'lng': 55.1425, 'start': '19:00', 'end': '22:00', 'cost': 450, 'tier': 'expensive', 'notes': 'Live cooking stations, DJ and views of Ain Dubai'},
    # Day 7
    {'day': 7, 'title': 'Jumeirah Beach Sunrise Walk', 'type': 'activity', 'location': 'Umm Suqeim Beach', 'lat': 25.1412, 'lng': 55.1852, 'start': '07:30', 'end': '09:00', 'cost': 0, 'tier': 'free', 'notes': 'Unobstructed view of Burj Al Arab sail architecture'},
    {'day': 7, 'title': 'Airport Departure Cab', 'type': 'transport', 'location': 'DXB Terminal 3', 'lat': 25.2532, 'lng': 55.3657, 'start': '11:00', 'end': '12:30', 'cost': 85, 'tier': 'budget', 'notes': 'Direct transfer to departures'},
]

_DEMO_KASHMIR = [
    # Day 1
    {'day': 1, 'title': 'Airport Cab to Dal Lake Houseboat', 'type': 'transport', 'location': 'Sheikh ul-Alam Airport, Srinagar', 'lat': 33.9871, 'lng': 74.7742, 'start': '11:00', 'end': '12:15', 'cost': 2000, 'tier': 'expensive', 'notes': 'Scenic cab passing through chinars'},
    {'day': 1, 'title': 'Check-in Luxury Houseboat on Dal Lake', 'type': 'hotel', 'location': 'Boulevard Rd, Dal Lake', 'lat': 34.1118, 'lng': 74.8419, 'start': '13:00', 'end': '14:00', 'cost': 5500, 'tier': 'expensive', 'notes': 'Carved cedar heritage houseboat with butler service'},
    {'day': 1, 'title': 'Sunset Shikara Boat Ride on Dal Lake', 'type': 'activity', 'location': 'Ghat No 7, Dal Lake', 'lat': 34.1110, 'lng': 74.8400, 'start': '16:30', 'end': '18:30', 'cost': 800, 'tier': 'budget', 'notes': 'Floating flower markets and sunset over Zabarwan mountains'},
    # Day 2
    {'day': 2, 'title': 'Nishat Bagh & Shalimar Mughal Gardens', 'type': 'activity', 'location': 'Nishat Bagh, Srinagar', 'lat': 34.1244, 'lng': 74.8827, 'start': '09:30', 'end': '12:30', 'cost': 50, 'tier': 'budget', 'notes': '12-terraced garden of pleasure built in 1633'},
    {'day': 2, 'title': 'Hazratbal Shrine Exterior & Lake Walk', 'type': 'activity', 'location': 'Hazratbal, Srinagar', 'lat': 34.1275, 'lng': 74.8428, 'start': '14:00', 'end': '15:30', 'cost': 0, 'tier': 'free', 'notes': 'White marble lakeside shrine with serene mountain reflections'},
    {'day': 2, 'title': 'Authentic 7-Course Wazwan Dinner', 'type': 'meal', 'location': 'Ahdoos, Residency Rd', 'lat': 34.0735, 'lng': 74.8008, 'start': '19:30', 'end': '21:30', 'cost': 1500, 'tier': 'budget', 'notes': 'Rogan josh, rista, gushtaba, tabak maaz and saffron kehwa'},
    # Day 3
    {'day': 3, 'title': 'Gulmarg World\'s Second-Highest Gondola', 'type': 'activity', 'location': 'Kongdoori & Apharwat Peak, Gulmarg', 'lat': 34.0484, 'lng': 74.3805, 'start': '07:30', 'end': '17:00', 'cost': 3500, 'tier': 'expensive', 'notes': 'Phase 1 & Phase 2 cable car up to 4,390 meters altitude'},
    # Day 4
    {'day': 4, 'title': 'Saffron Fields of Pampore Scenic Stop', 'type': 'activity', 'location': 'Pampore Highway', 'lat': 34.0150, 'lng': 74.9300, 'start': '09:00', 'end': '10:00', 'cost': 0, 'tier': 'free', 'notes': 'Purple saffron blossom valleys and mountain panorama'},
    {'day': 4, 'title': 'Aru Valley Guided Horse Ride', 'type': 'activity', 'location': 'Aru Valley, Pahalgam', 'lat': 34.0900, 'lng': 75.2600, 'start': '13:00', 'end': '16:00', 'cost': 1400, 'tier': 'budget', 'notes': 'Pine forests and sparkling Lidder river tributaries'},
    # Day 5
    {'day': 5, 'title': 'Betaab Valley Bollywood Scenic Walk', 'type': 'activity', 'location': 'Betaab Valley, Pahalgam', 'lat': 34.0167, 'lng': 75.3333, 'start': '09:30', 'end': '12:30', 'cost': 100, 'tier': 'budget', 'notes': 'Lush meadows surrounded by snow-covered peaks'},
    {'day': 5, 'title': 'Lidder River Bank Relaxation & Photos', 'type': 'activity', 'location': 'Lidder Amusement Park Bank', 'lat': 34.0200, 'lng': 75.3200, 'start': '14:30', 'end': '16:30', 'cost': 0, 'tier': 'free', 'notes': 'Turquoise glacial river breeze and pine canopy'},
    # Day 6
    {'day': 6, 'title': 'Shankaracharya Ancient Temple Sunrise Climb', 'type': 'activity', 'location': 'Gopadari Hill, Srinagar', 'lat': 34.0780, 'lng': 74.8330, 'start': '06:00', 'end': '08:30', 'cost': 0, 'tier': 'free', 'notes': '200 stone steps to 9th-century Shiva temple with 360° Srinagar view'},
    {'day': 6, 'title': 'Heritage Pashmina & Silk Carpet Emporium', 'type': 'activity', 'location': 'Lal Chowk, Srinagar', 'lat': 34.0735, 'lng': 74.8008, 'start': '11:00', 'end': '14:30', 'cost': 8000, 'tier': 'expensive', 'notes': 'Hand-spun cashmere shawls and silk-on-silk carpets'},
    # Day 7
    {'day': 7, 'title': 'Dawn Floating Vegetable Market on Dal Lake', 'type': 'activity', 'location': 'Mir Behri, Dal Lake', 'lat': 34.1110, 'lng': 74.8400, 'start': '05:30', 'end': '07:30', 'cost': 0, 'tier': 'free', 'notes': 'Century-old early morning water trade among lotus pods'},
    {'day': 7, 'title': 'Airport Cab Transfer', 'type': 'transport', 'location': 'Srinagar Airport', 'lat': 33.9871, 'lng': 74.7742, 'start': '09:30', 'end': '11:00', 'cost': 2000, 'tier': 'expensive', 'notes': 'Farewell to paradise'},
]
