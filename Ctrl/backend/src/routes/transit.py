"""
Transit & Travel API routes — Flights, Trains, Metro, Cabs, Rentals, and Ferries.
Adheres strictly to the PS-08 data model (R1 Additive, R2 Opaque prefixed IDs, R3 Money decimal+ISO, R4 Timestamps, R7 WGS-84).
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, row_to_dict, rows_to_list

transit_bp = Blueprint('transit', __name__)

# Ensure trips table has trp_origin column
try:
    mutate_db("ALTER TABLE trips ADD COLUMN trp_origin TEXT DEFAULT 'Mumbai, India'")
except Exception:
    pass


# ─── Transit Dataset for All Destinations ──────────────────────────────────────

_TRANSIT_MODES_DB = {
    'goa': {
        'destination_label': 'Goa, India',
        'city_id': 'cty_goa',
        'currency': 'INR',
        'flights': [
            {
                'id': 'flt_goa_6e',
                'carrier': 'IndiGo Airlines',
                'carrier_code': '6E',
                'flight_no': '6E-2415',
                'origin_code': 'BOM',
                'origin_airport': 'Chhatrapati Shivaji Maharaj Intl (T2), Mumbai',
                'dest_code': 'GOI',
                'dest_airport': 'Dabolim International Airport, Goa',
                'dep_time': '11:20',
                'arr_time': '12:35',
                'duration': '1h 15m',
                'stops': 0,
                'class': 'Economy',
                'fare': 3200.00,
                'currency': 'INR',
                'carbon_kg': 78.4,
                'luggage': '15kg check-in + 7kg cabin',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Mumbai+to+Goa',
                'badge': '⚡ Fastest Option',
            },
            {
                'id': 'flt_goa_ai',
                'carrier': 'Air India',
                'carrier_code': 'AI',
                'flight_no': 'AI-883',
                'origin_code': 'DEL',
                'origin_airport': 'Indira Gandhi Intl (T3), New Delhi',
                'dest_code': 'GOX',
                'dest_airport': 'Manohar Intl Airport (Mopa), North Goa',
                'dep_time': '09:05',
                'arr_time': '11:35',
                'duration': '2h 30m',
                'stops': 0,
                'class': 'Premium Economy',
                'fare': 4850.00,
                'currency': 'INR',
                'carbon_kg': 112.0,
                'luggage': '25kg check-in + 7kg cabin · Hot meal included',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Delhi+to+Goa',
                'badge': '👑 Full Service',
            },
            {
                'id': 'flt_goa_qp',
                'carrier': 'Akasa Air',
                'carrier_code': 'QP',
                'flight_no': 'QP-1382',
                'origin_code': 'BLR',
                'origin_airport': 'Kempegowda Intl (T1), Bengaluru',
                'dest_code': 'GOX',
                'dest_airport': 'Manohar Intl Airport (Mopa), North Goa',
                'dep_time': '14:15',
                'arr_time': '15:35',
                'duration': '1h 20m',
                'stops': 0,
                'class': 'Economy',
                'fare': 2890.00,
                'currency': 'INR',
                'carbon_kg': 81.2,
                'luggage': '15kg check-in + 7kg cabin · USB charge at seat',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Bangalore+to+Goa',
                'badge': '🎒 Best Value Airfare',
            }
        ],
        'trains': [
            {
                'id': 'trn_goa_vb',
                'train_no': '20645',
                'name': 'Vande Bharat Express',
                'origin_station': 'Mumbai CSMT (Platform 18)',
                'dest_station': 'Madgaon Junction (MAO)',
                'dep_time': '05:25',
                'arr_time': '13:10',
                'duration': '7h 45m',
                'class': 'Executive Chair Car (EC)',
                'fare': 2450.00,
                'currency': 'INR',
                'seats_status': '✅ Available (48 seats)',
                'carbon_kg': 12.1,
                'catering': 'Gourmet breakfast, snacks & afternoon tea included',
                'speed': 'Up to 130 km/h · Scenic Konkan Western Ghats Viaducts',
                'booking_link': 'https://www.irctc.co.in/nget/train-search',
                'badge': '🌿 Eco-Champion (85% less carbon)',
            },
            {
                'id': 'trn_goa_tejas',
                'train_no': '82901',
                'name': 'Tejas Express Superfast',
                'origin_station': 'Mumbai CSMT',
                'dest_station': 'Karmali (KRMI, North Goa)',
                'dep_time': '05:50',
                'arr_time': '14:00',
                'duration': '8h 10m',
                'class': 'AC Chair Car (CC)',
                'fare': 1580.00,
                'currency': 'INR',
                'seats_status': '✅ Available (112 seats)',
                'carbon_kg': 13.5,
                'catering': 'Auto-vending coffee & packaged meals',
                'speed': 'Smart coaches with automatic sliding doors & infotainment',
                'booking_link': 'https://www.irctc.co.in/nget/train-search',
                'badge': '⭐ Most Convenient for North Goa',
            },
            {
                'id': 'trn_goa_mandovi',
                'train_no': '10103',
                'name': 'Mandovi Express',
                'origin_station': 'Mumbai CSMT',
                'dest_station': 'Madgaon Junction (MAO)',
                'dep_time': '07:10',
                'arr_time': '19:00',
                'duration': '11h 50m',
                'class': 'AC 2-Tier (2A)',
                'fare': 1850.00,
                'currency': 'INR',
                'seats_status': 'RAC-14 (Confirmed Berth likely)',
                'carbon_kg': 14.8,
                'catering': 'Pantry car hot thali & fried fish snacks',
                'speed': 'Day express through 91 Konkan tunnels',
                'booking_link': 'https://www.irctc.co.in/nget/train-search',
                'badge': '🎒 Scenic Daylight Rail',
            }
        ],
        'metro': [
            {
                'id': 'mtr_goa_airport_shuttle',
                'network': 'Kadamba Smart EV Rapid Transit',
                'line': 'Airport Express Corridor (Line EV-1)',
                'route': 'Manohar Intl Airport (Mopa) ➔ Panaji ➔ Calangute Beach',
                'frequency': 'Every 30 mins',
                'operating_hours': '05:00 AM – 23:30 PM',
                'fare_token': 200.00,
                'fare_day_pass': 450.00,
                'currency': 'INR',
                'carbon_kg': 1.2,
                'station_stops': 6,
                'features': 'Zero-emission electric luxury AC bus, luggage racks, free onboard Wi-Fi',
                'map_link': 'https://ktclgoa.com/',
                'portal_link': 'https://ktclgoa.com/airport-services',
                'badge': '🌱 Green Public Transit',
            },
            {
                'id': 'mtr_goa_city_feeder',
                'network': 'Panaji Smart City EV Ring',
                'line': 'Capital Heritage Loop',
                'route': 'Panaji Bus Terminus ➔ Miramar Beach ➔ Fontainhas Latin Quarter',
                'frequency': 'Every 12 mins',
                'operating_hours': '06:00 AM – 22:00 PM',
                'fare_token': 25.00,
                'fare_day_pass': 80.00,
                'currency': 'INR',
                'carbon_kg': 0.3,
                'station_stops': 14,
                'features': 'Low-floor AC electric micro-transit connecting heritage landmarks',
                'map_link': 'https://sprintgoa.com/',
                'portal_link': 'https://ktclgoa.com/',
                'badge': '🏛️ Heritage City Loop',
            }
        ],
        'cabs': [
            {
                'id': 'cab_goa_goamiles',
                'provider': 'GoaMiles (State Verified App Cab)',
                'vehicle_type': 'Maruti Ertiga / Dzire AC',
                'capacity': '4 Passengers · 3 Bags',
                'pickup_point': 'Official GoaMiles Kiosk at Terminal 1 / Terminal 2 Gate',
                'fare_min': 1250.00,
                'fare_max': 1450.00,
                'currency': 'INR',
                'est_duration': '45 mins',
                'surge_index': '1.0x (Fixed Govt Regulated Fare)',
                'features': 'No bargaining, GPS tracking, official state-backed safety button',
                'booking_link': 'https://www.goamiles.com/',
                'badge': '⭐ Most Reliable Airport Cab',
            },
            {
                'id': 'cab_goa_prepaid',
                'provider': 'Airport Pre-paid Taxi Union',
                'vehicle_type': 'Toyota Innova Crysta 7-Seater',
                'capacity': '6 Passengers · 6 Bags',
                'pickup_point': 'Arrival Exit Curb Stand #2',
                'fare_min': 1750.00,
                'fare_max': 2100.00,
                'currency': 'INR',
                'est_duration': '50 mins',
                'surge_index': '1.0x (Pre-paid counter slip)',
                'features': 'Pay at terminal booth inside baggage hall, receipt provided',
                'booking_link': 'https://www.goaairport.com/',
                'badge': '👥 Best for Group / Big Family',
            },
            {
                'id': 'cab_goa_uber',
                'provider': 'Uber Intercity / Premier',
                'vehicle_type': 'Premium Sedan (Honda City / Verna)',
                'capacity': '4 Passengers · 3 Bags',
                'pickup_point': 'Designated Rideshare Lane 3',
                'fare_min': 1400.00,
                'fare_max': 1850.00,
                'currency': 'INR',
                'est_duration': '45 mins',
                'surge_index': '1.1x Moderate Demand',
                'features': 'Cashless in-app billing, verified driver profile, live ETA sharing',
                'booking_link': 'https://m.uber.com/',
                'badge': '📱 One-Tap In-App Booking',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_goa_activa',
                'vehicle': 'Honda Activa 6G 125cc Scooter',
                'type': 'Two-Wheeler Scooter',
                'daily_rate': 400.00,
                'currency': 'INR',
                'deposit': 1000.00,
                'fuel_policy': 'Full-to-Full',
                'inclusions': '2 ISI Helmets, valid RC photocopy, mobile phone holder',
                'provider': 'Goa Beach Scooters Rental Co.',
                'booking_link': 'https://www.rentrip.in/rent-bike-in-goa',
                'badge': '🛵 Ultimate Freedom & Budget Choice',
            },
            {
                'id': 'rnt_goa_hunter',
                'vehicle': 'Royal Enfield Hunter 350 Retro Cruiser',
                'type': 'Motorbike',
                'daily_rate': 1100.00,
                'currency': 'INR',
                'deposit': 2000.00,
                'fuel_policy': 'Same-to-Same',
                'inclusions': 'Riding gloves, USB charger port, twin disc ABS',
                'provider': 'Konkan Bikers Club',
                'booking_link': 'https://www.rentrip.in/rent-bike-in-goa',
                'badge': '🏍️ Iconic Coastal Ride',
            },
            {
                'id': 'rnt_goa_thar',
                'vehicle': 'Mahindra Thar 4x4 Convertible Hardtop',
                'type': 'Self-Drive 4x4 SUV',
                'daily_rate': 3200.00,
                'currency': 'INR',
                'deposit': 5000.00,
                'fuel_policy': 'Full-to-Full',
                'inclusions': 'Unlimited km, zero-dep comprehensive insurance, 24/7 breakdown assist',
                'provider': 'Zoomcar Goa Fleet Hub',
                'booking_link': 'https://www.zoomcar.com/in/goa',
                'badge': '👑 Open-Air Beach Cruiser',
            }
        ],
        'ferries': [
            {
                'id': 'fer_goa_mandovi',
                'name': 'Panaji ➔ Betim River Ferry',
                'route': 'Panaji Ferry Wharf to Betim Jetty across Mandovi River',
                'duration': '10 mins',
                'frequency': 'Every 15 mins (Continuous from 06:00 to 22:00)',
                'fare': 10.00,
                'currency': 'INR',
                'free_pedestrians': True,
                'scenic_score': '9.2 / 10 (River sunset & passing casino ships)',
                'booking_link': 'https://ports.goa.gov.in/',
                'badge': '🌊 100% Free for Pedestrians',
            },
            {
                'id': 'fer_goa_cruise',
                'name': 'Santa Monica Luxury Mandovi Cruise',
                'route': 'Panaji Jetty along Miramar Bay and back',
                'duration': '1 hour',
                'frequency': 'Daily departures at 18:00, 19:15, 20:30',
                'fare': 600.00,
                'currency': 'INR',
                'free_pedestrians': False,
                'scenic_score': '9.6 / 10 (Live Goan folk dance & DJ onboard)',
                'booking_link': 'https://goa-tourism.com/',
                'badge': '🎭 Cultural Evening Experience',
            }
        ]
    },

    'bali': {
        'destination_label': 'Bali, Indonesia',
        'city_id': 'cty_dps',
        'currency': 'IDR',
        'flights': [
            {
                'id': 'flt_bali_sq',
                'carrier': 'Singapore Airlines',
                'carrier_code': 'SQ',
                'flight_no': 'SQ-944',
                'origin_code': 'SIN',
                'origin_airport': 'Changi Airport (T2), Singapore',
                'dest_code': 'DPS',
                'dest_airport': 'Ngurah Rai Intl Airport (Denpasar), Bali',
                'dep_time': '09:35',
                'arr_time': '12:15',
                'duration': '2h 40m',
                'stops': 0,
                'class': 'Economy',
                'fare': 2850000.00,
                'currency': 'IDR',
                'carbon_kg': 94.2,
                'luggage': '25kg check-in + 7kg cabin · Complimentary drinks & meal',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+to+Bali',
                'badge': '⭐ 5-Star International Carrier',
            },
            {
                'id': 'flt_bali_vj',
                'carrier': 'VietJet Air',
                'carrier_code': 'VJ',
                'flight_no': 'VJ-897',
                'origin_code': 'BOM',
                'origin_airport': 'Mumbai CSMT Intl (T2), India',
                'dest_code': 'DPS',
                'dest_airport': 'Ngurah Rai Intl Airport, Bali',
                'dep_time': '01:05',
                'arr_time': '11:45',
                'duration': '7h 40m',
                'stops': 1,
                'class': 'Eco Saver',
                'fare': 3450000.00,
                'currency': 'IDR',
                'carbon_kg': 168.0,
                'luggage': '20kg check-in included',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Mumbai+to+Bali',
                'badge': '🎒 Best Value Connecting Airfare',
            }
        ],
        'trains': [
            {
                'id': 'trn_bali_kai',
                'train_no': 'PL-18',
                'name': 'KAI Java-Bali Overland Express + Ketapang Ferry',
                'origin_station': 'Surabaya Gubeng Station (East Java)',
                'dest_station': 'Banyuwangi Ketapang ➔ Gilimanuk Bali Gateway',
                'dep_time': '06:15',
                'arr_time': '12:30',
                'duration': '6h 15m',
                'class': 'Executive Air-Conditioned',
                'fare': 280000.00,
                'currency': 'IDR',
                'seats_status': '✅ Available (34 seats)',
                'carbon_kg': 18.2,
                'catering': 'Nasi goreng & tropical tea served at seat',
                'speed': 'Scenic railway past Mount Ijen volcano',
                'booking_link': 'https://kai.id/',
                'badge': '🌋 Iconic Volcanic Overland Route',
            }
        ],
        'metro': [
            {
                'id': 'mtr_bali_transdewata',
                'network': 'Trans Metro Dewata BRT System',
                'line': 'Corridor K1B (Bandara Ngurah Rai ➔ Seminyak ➔ Ubud)',
                'route': 'DPS Airport Terminal ➔ Central Kuta ➔ Monkey Forest Ubud',
                'frequency': 'Every 15 mins',
                'operating_hours': '05:30 AM – 21:00 PM',
                'fare_token': 4400.00,
                'fare_day_pass': 20000.00,
                'currency': 'IDR',
                'carbon_kg': 0.4,
                'station_stops': 18,
                'features': 'Clean AC bus with cashless tap-in (E-Money / Flazz card)',
                'map_link': 'https://temantbus.com/',
                'portal_link': 'https://temantbus.com/',
                'badge': '🪙 Ridiculously Cheap (~$0.30)',
            }
        ],
        'cabs': [
            {
                'id': 'cab_bali_grab',
                'provider': 'GrabCar Airport Official (Air-conditioned MPV)',
                'vehicle_type': 'Toyota Avanza / Daihatsu Xenia',
                'capacity': '4 Passengers · 4 Bags',
                'pickup_point': 'Official Grab Lounge (DPS Arrival Hall right after Customs)',
                'fare_min': 180000.00,
                'fare_max': 240000.00,
                'currency': 'IDR',
                'est_duration': '35 mins',
                'surge_index': '1.0x Standard Rate',
                'features': 'Pre-booked inside AC lounge, free bottled water & cold towel',
                'booking_link': 'https://www.grab.com/id/en/',
                'badge': '⭐ Most Hassle-Free Arrival',
            },
            {
                'id': 'cab_bali_bluebird',
                'provider': 'Blue Bird Metered Taxi (Trusted Balinese Fleet)',
                'vehicle_type': 'Toyota Vios Sedan',
                'capacity': '3 Passengers · 2 Bags',
                'pickup_point': 'Blue Bird Service Kiosk outside Domestic/Intl exits',
                'fare_min': 150000.00,
                'fare_max': 210000.00,
                'currency': 'IDR',
                'est_duration': '35 mins',
                'surge_index': '1.0x Strictly Metered',
                'features': 'Tamper-proof calibrated meter, certified english-speaking driver',
                'booking_link': 'https://www.bluebirdgroup.com/',
                'badge': '🛡️ 100% Reliable Metered',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_bali_scoopy',
                'vehicle': 'Honda Scoopy 110cc Retro Scooter',
                'type': 'Two-Wheeler Scooter',
                'daily_rate': 85000.00,
                'currency': 'IDR',
                'deposit': 250000.00,
                'fuel_policy': 'Same-to-Same',
                'inclusions': '2 Clean Helmets, phone holder, surf-rack on request',
                'provider': 'Bikemind Seminyak Rental Hub',
                'booking_link': 'https://bikemind.id/',
                'badge': '🛵 Essential Bali Explorer (~$5.50/day)',
            },
            {
                'id': 'rnt_bali_driver',
                'vehicle': 'Private Toyota Innova with English-speaking Chauffeur',
                'type': 'Private Car with Driver (10 Hours)',
                'daily_rate': 650000.00,
                'currency': 'IDR',
                'deposit': 0.00,
                'fuel_policy': 'All fuel, parking & toll included in flat price',
                'inclusions': '10-hour customized itinerary anywhere in Bali (Ubud, Uluwatu, Tanah Lot)',
                'provider': 'Bali Sunshine Chauffeurs',
                'booking_link': 'https://www.balicab.com/',
                'badge': '👑 Pure Luxury & Zero Stress (~$40/day)',
            }
        ],
        'ferries': [
            {
                'id': 'fer_bali_penida',
                'name': 'Sanur Beach ➔ Nusa Penida Rocky Fast Cruise',
                'route': 'Sanur Harbor Pier to Banjar Nyuh Port (Nusa Penida)',
                'duration': '35 mins',
                'frequency': 'Departures at 08:30, 10:00, 14:00 daily',
                'fare': 175000.00,
                'currency': 'IDR',
                'free_pedestrians': False,
                'scenic_score': '9.8 / 10 (Dramatic ocean views of Mount Agung)',
                'booking_link': 'https://rockyfastcruise.com/',
                'badge': '🏝️ Direct Island Hopper',
            }
        ]
    },

    'paris': {
        'destination_label': 'Paris, France',
        'city_id': 'cty_cdg',
        'currency': 'EUR',
        'flights': [
            {
                'id': 'flt_paris_af',
                'carrier': 'Air France',
                'carrier_code': 'AF',
                'flight_no': 'AF-1681',
                'origin_code': 'LHR',
                'origin_airport': 'London Heathrow Airport (T4), UK',
                'dest_code': 'CDG',
                'dest_airport': 'Charles de Gaulle Airport (T2E), Paris',
                'dep_time': '10:30',
                'arr_time': '12:50',
                'duration': '1h 20m',
                'stops': 0,
                'class': 'Economy Standard',
                'fare': 110.00,
                'currency': 'EUR',
                'carbon_kg': 68.0,
                'luggage': '12kg cabin + 23kg checked bag',
                'booking_link': 'https://www.airfrance.com/',
                'badge': '✈️ Fast Air Shuttle',
            }
        ],
        'trains': [
            {
                'id': 'trn_paris_eurostar',
                'train_no': 'ES-9024',
                'name': 'Eurostar High-Speed (Undersea Channel Tunnel)',
                'origin_station': 'London St Pancras International',
                'dest_station': 'Paris Gare du Nord',
                'dep_time': '08:01',
                'arr_time': '11:17',
                'duration': '2h 16m',
                'class': 'Standard Premier',
                'fare': 89.00,
                'currency': 'EUR',
                'seats_status': '✅ Available (22 seats)',
                'carbon_kg': 4.1,
                'catering': 'Light meal and drinks served at spacious seat',
                'speed': '300 km/h (186 mph) · Center-to-center in 2h 16m',
                'booking_link': 'https://www.eurostar.com/',
                'badge': '🌿 Recommended: 93% Lower Carbon than Flying',
            },
            {
                'id': 'trn_paris_tgv',
                'train_no': 'TGV-6205',
                'name': 'TGV INOUI High-Speed Rail',
                'origin_station': 'Paris Gare de Lyon',
                'dest_station': 'Lyon Part-Dieu / Marseille',
                'dep_time': '09:28',
                'arr_time': '11:24',
                'duration': '1h 56m',
                'class': 'First Class (1ère)',
                'fare': 58.00,
                'currency': 'EUR',
                'seats_status': '✅ Available',
                'carbon_kg': 2.8,
                'catering': 'Café Procope on board with organic French pastries',
                'speed': '320 km/h world-class high-speed rail',
                'booking_link': 'https://www.sncf-connect.com/',
                'badge': '⚡ Premier European Rail',
            }
        ],
        'metro': [
            {
                'id': 'mtr_paris_rer_b',
                'network': 'RATP / Île-de-France Mobilités',
                'line': 'RER B Express Train (Direct Airport Link)',
                'route': 'CDG Airport Terminal 1/2 ➔ Gare du Nord ➔ Châtelet-Les Halles',
                'frequency': 'Every 6-8 mins',
                'operating_hours': '04:50 AM – 23:50 PM',
                'fare_token': 11.80,
                'fare_day_pass': 20.60,
                'currency': 'EUR',
                'carbon_kg': 0.6,
                'station_stops': 7,
                'features': 'Fastest transfer into heart of Paris, connects to all Métro lines',
                'map_link': 'https://www.ratp.fr/',
                'portal_link': 'https://www.ratp.fr/en/titres-et-tarifs',
                'badge': '⚡ Fastest Airport Connection',
            },
            {
                'id': 'mtr_paris_metro_1',
                'network': 'Paris Métro',
                'line': 'Line 1 (Fully Automated Driverless Line)',
                'route': 'La Défense ➔ Champs-Élysées ➔ Louvre-Rivoli ➔ Bastille ➔ Château de Vincennes',
                'frequency': 'Every 100 seconds peak',
                'operating_hours': '05:30 AM – 01:15 AM (02:15 on weekends)',
                'fare_token': 2.15,
                'fare_day_pass': 8.65,
                'currency': 'EUR',
                'carbon_kg': 0.05,
                'station_stops': 25,
                'features': 'Crosses all major monuments east-to-west, air-conditioned automated trains',
                'map_link': 'https://www.ratp.fr/plans-lignes/metro/1',
                'portal_link': 'https://www.ratp.fr/',
                'badge': '🏛️ The Landmark Line',
            }
        ],
        'cabs': [
            {
                'id': 'cab_paris_taxi_parisien',
                'provider': 'Official Taxis Parisiens (Regulated Flat Rate)',
                'vehicle_type': 'Peugeot 508 / Mercedes E-Class',
                'capacity': '4 Passengers · 4 Bags',
                'pickup_point': 'Official Taxi Stand at Terminal exit (Follow light sign)',
                'fare_min': 56.00,
                'fare_max': 65.00,
                'currency': 'EUR',
                'est_duration': '40 mins',
                'surge_index': '1.0x (Law-mandated fixed airport tariff)',
                'features': 'Strict flat fee: €56 to Right Bank, €65 to Left Bank. No surge ever.',
                'booking_link': 'https://www.taxisg7.fr/en/',
                'badge': '🛡️ Fixed Flat Tariff Guaranteed',
            },
            {
                'id': 'cab_paris_uber',
                'provider': 'Uber Green (100% Electric & Hybrid)',
                'vehicle_type': 'Tesla Model 3 / Toyota Camry Hybrid',
                'capacity': '4 Passengers · 3 Bags',
                'pickup_point': 'Designated VTC Parking Area P2',
                'fare_min': 48.00,
                'fare_max': 58.00,
                'currency': 'EUR',
                'est_duration': '42 mins',
                'surge_index': '1.05x Normal',
                'features': 'Silent zero-emission ride directly to your hotel address',
                'booking_link': 'https://m.uber.com/',
                'badge': '🌱 Eco-Friendly Rideshare',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_paris_velib',
                'vehicle': 'Vélib\' Métropole Electric Blue Bike',
                'type': 'Electric Assist Bicycle',
                'daily_rate': 5.00,
                'currency': 'EUR',
                'deposit': 0.00,
                'fuel_policy': 'Solar charging stations',
                'inclusions': 'Access to 1,400 docking stations and 20,000 bikes citywide',
                'provider': 'City of Paris Vélib\'',
                'booking_link': 'https://www.velib-metropole.fr/en',
                'badge': '🚲 Parisian Lifestyle (~€5/day)',
            }
        ],
        'ferries': [
            {
                'id': 'fer_paris_batobus',
                'name': 'Batobus Seine River Hop-On Hop-Off Shuttle',
                'route': 'Eiffel Tower ➔ Musée d\'Orsay ➔ Saint-Germain ➔ Notre-Dame ➔ Louvre',
                'duration': 'Full circuit 2h (Hop off anytime)',
                'frequency': 'Every 20 mins',
                'fare': 20.00,
                'currency': 'EUR',
                'free_pedestrians': False,
                'scenic_score': '9.9 / 10 (Unmatched views of illuminated Paris monuments)',
                'booking_link': 'https://www.batobus.com/en',
                'badge': '✨ Scenic Riverway Pass',
            }
        ]
    },

    'london': {
        'destination_label': 'London, United Kingdom',
        'city_id': 'cty_lhr',
        'currency': 'GBP',
        'flights': [
            {
                'id': 'flt_london_ba',
                'carrier': 'British Airways',
                'carrier_code': 'BA',
                'flight_no': 'BA-118',
                'origin_code': 'JFK',
                'origin_airport': 'John F. Kennedy Intl (T7), New York',
                'dest_code': 'LHR',
                'dest_airport': 'London Heathrow Airport (T5), London',
                'dep_time': '18:45',
                'arr_time': '06:50',
                'duration': '7h 05m',
                'stops': 0,
                'class': 'World Traveller (Economy)',
                'fare': 420.00,
                'currency': 'GBP',
                'carbon_kg': 390.0,
                'luggage': '23kg checked bag + cabin bag included',
                'booking_link': 'https://www.britishairways.com/',
                'badge': '👑 Flagship Transatlantic Service',
            }
        ],
        'trains': [
            {
                'id': 'trn_london_hex',
                'train_no': 'HEX-10',
                'name': 'Heathrow Express Non-Stop',
                'origin_station': 'Heathrow Central (Terminals 2 & 3)',
                'dest_station': 'London Paddington Station',
                'dep_time': '10:12',
                'arr_time': '10:27',
                'duration': '15m non-stop',
                'class': 'Express Class',
                'fare': 25.00,
                'currency': 'GBP',
                'seats_status': '✅ Frequent departures',
                'carbon_kg': 1.1,
                'catering': 'Free high-speed 5G Wi-Fi & USB charge ports',
                'speed': '15-minute non-stop sprint into central London',
                'booking_link': 'https://www.heathrowexpress.com/',
                'badge': '⚡ 15-Minute Airport Express',
            },
            {
                'id': 'trn_london_lner',
                'train_no': 'LNER-91',
                'name': 'LNER Azuma High-Speed Rail',
                'origin_station': 'London King\'s Cross Station',
                'dest_station': 'Edinburgh Waverley',
                'dep_time': '09:00',
                'arr_time': '13:20',
                'duration': '4h 20m',
                'class': 'First Class Lounge Access',
                'fare': 74.00,
                'currency': 'GBP',
                'seats_status': '✅ Available',
                'carbon_kg': 15.4,
                'catering': 'Chef-prepared hot British breakfast served at seat',
                'speed': '200 km/h along East Coast Main Line',
                'booking_link': 'https://www.lner.co.uk/',
                'badge': '🏴󠁧󠁢󠁳󠁣󠁴󠁿 British Countryside Journey',
            }
        ],
        'metro': [
            {
                'id': 'mtr_london_elizabeth',
                'network': 'Transport for London (TfL)',
                'line': 'Elizabeth Line (Purple Line)',
                'route': 'Heathrow Airport (T2/3/4/5) ➔ Paddington ➔ Tottenham Court Rd ➔ Liverpool St',
                'frequency': 'Every 5 mins',
                'operating_hours': '05:15 AM – 00:15 AM',
                'fare_token': 13.30,
                'fare_day_pass': 15.60,
                'currency': 'GBP',
                'carbon_kg': 0.3,
                'station_stops': 10,
                'features': 'Brand new air-conditioned trains, step-free access, 29 mins to Soho',
                'map_link': 'https://tfl.gov.uk/modes/elizabeth-line/',
                'portal_link': 'https://tfl.gov.uk/',
                'badge': '⭐ Most Recommended Airport Transit',
            },
            {
                'id': 'mtr_london_tube',
                'network': 'London Underground (The Tube)',
                'line': 'Piccadilly Line (Blue)',
                'route': 'Heathrow Airport ➔ Piccadilly Circus ➔ Covent Garden ➔ King\'s Cross',
                'frequency': 'Every 4 mins',
                'operating_hours': '24-hour Night Tube on weekends',
                'fare_token': 5.60,
                'fare_day_pass': 8.50,
                'currency': 'GBP',
                'carbon_kg': 0.2,
                'station_stops': 22,
                'features': 'Cheapest direct link into the West End, daily cap of £8.50 with contactless',
                'map_link': 'https://tfl.gov.uk/maps/track/tube',
                'portal_link': 'https://tfl.gov.uk/',
                'badge': '🎒 Budget Champion (£5.60)',
            }
        ],
        'cabs': [
            {
                'id': 'cab_london_blackcab',
                'provider': 'Official London Black Cab (LEVC Electric TX)',
                'vehicle_type': 'Iconic Black Cab (Zero Emission Capable)',
                'capacity': '6 Passengers · 6 Bags',
                'pickup_point': 'Official Black Cab Ranks outside every Heathrow terminal',
                'fare_min': 72.00,
                'fare_max': 95.00,
                'currency': 'GBP',
                'est_duration': '45 mins',
                'surge_index': '1.0x (Taximeter regulated by TfL)',
                'features': 'Drivers pass legendary "The Knowledge" test, panoramic sunroof, full wheelchair ramp',
                'booking_link': 'https://www.gett.com/uk/',
                'badge': '🎩 World Famous Iconic Ride',
            },
            {
                'id': 'cab_london_uber',
                'provider': 'UberX London',
                'vehicle_type': 'Toyota Prius / Corolla Hybrid',
                'capacity': '4 Passengers · 3 Bags',
                'pickup_point': 'Terminal Short Stay Car Park (Follow App Directions)',
                'fare_min': 48.00,
                'fare_max': 64.00,
                'currency': 'GBP',
                'est_duration': '50 mins',
                'surge_index': '1.0x',
                'features': 'Cashless automatic payment, instant in-app route tracking',
                'booking_link': 'https://m.uber.com/',
                'badge': '📱 One-Tap Pickup',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_london_santander',
                'vehicle': 'Santander Cycles (TfL Red Bicycle)',
                'type': 'City Bicycle',
                'daily_rate': 3.00,
                'currency': 'GBP',
                'deposit': 0.00,
                'fuel_policy': 'Human powered',
                'inclusions': '800 docking stations across Royal Parks and Thames waterfront',
                'provider': 'Transport for London',
                'booking_link': 'https://tfl.gov.uk/modes/cycling/santander-cycles',
                'badge': '🚲 Royal Parks Cruise',
            }
        ],
        'ferries': [
            {
                'id': 'fer_london_thames',
                'name': 'Uber Boat by Thames Clippers',
                'route': 'Westminster Pier ➔ London Bridge ➔ Tower Pier ➔ Greenwich Pier',
                'duration': '35 mins',
                'frequency': 'Every 15-20 mins',
                'fare': 9.40,
                'currency': 'GBP',
                'free_pedestrians': False,
                'scenic_score': '9.7 / 10 (Glides right under Tower Bridge)',
                'booking_link': 'https://www.thamesclippers.com/',
                'badge': '⛴️ Scenic Thames Commute',
            }
        ]
    },

    'dubai': {
        'destination_label': 'Dubai, UAE',
        'city_id': 'cty_dxb',
        'currency': 'AED',
        'flights': [
            {
                'id': 'flt_dubai_ek',
                'carrier': 'Emirates Airline',
                'carrier_code': 'EK',
                'flight_no': 'EK-501',
                'origin_code': 'BOM',
                'origin_airport': 'Mumbai CSMT Intl (T2), India',
                'dest_code': 'DXB',
                'dest_airport': 'Dubai International Airport (Terminal 3), Dubai',
                'dep_time': '04:30',
                'arr_time': '06:15',
                'duration': '3h 15m',
                'stops': 0,
                'class': 'Economy (A380 Superjumbo)',
                'fare': 980.00,
                'currency': 'AED',
                'carbon_kg': 195.0,
                'luggage': '30kg check-in + 7kg cabin · Gourmet multi-course dining',
                'booking_link': 'https://www.emirates.com/',
                'badge': '👑 World\'s Best In-Flight Entertainment',
            }
        ],
        'trains': [
            {
                'id': 'trn_dubai_palm',
                'train_no': 'MONO-01',
                'name': 'Palm Jumeirah Monorail',
                'origin_station': 'Palm Gateway Station (Al Sufouh)',
                'dest_station': 'Atlantis Aquaventure & The Pointe',
                'dep_time': '09:00',
                'arr_time': '09:12',
                'duration': '12 mins',
                'class': 'Panoramic Monorail Class',
                'fare': 20.00,
                'currency': 'AED',
                'seats_status': '✅ Every 15 mins',
                'carbon_kg': 0.8,
                'catering': 'Elevated panoramic views over the Palm archipelago',
                'speed': 'Glides 10 meters above turquoise gulf waters',
                'booking_link': 'https://www.palmmonorail.com/',
                'badge': '🌴 Palm Island Aerial Journey',
            }
        ],
        'metro': [
            {
                'id': 'mtr_dubai_redline',
                'network': 'Dubai Roads and Transport Authority (RTA)',
                'line': 'Red Line (World\'s Longest Driverless Metro)',
                'route': 'DXB Airport Terminal 1 & 3 ➔ Burj Khalifa/Dubai Mall ➔ Mall of Emirates ➔ Expo City',
                'frequency': 'Every 3 mins',
                'operating_hours': '05:00 AM – 00:00 Midnight',
                'fare_token': 7.50,
                'fare_day_pass': 20.00,
                'currency': 'AED',
                'carbon_kg': 0.15,
                'station_stops': 29,
                'features': 'Ultra-modern air-conditioned, dedicated Gold Class cabin, direct terminal access',
                'map_link': 'https://www.rta.ae/wps/portal/rta/ae/public-transport/metro/about-metro',
                'portal_link': 'https://www.rta.ae/',
                'badge': '⚡ Premier Air-Conditioned Rapid Transit',
            }
        ],
        'cabs': [
            {
                'id': 'cab_dubai_dtc',
                'provider': 'Dubai Taxi Corporation (DTC Airport Cream Taxi)',
                'vehicle_type': 'Toyota Camry Hybrid / Innova',
                'capacity': '4 Passengers · 4 Bags',
                'pickup_point': 'Official DTC Terminal 1, 2, 3 Arrival Forecourt',
                'fare_min': 75.00,
                'fare_max': 95.00,
                'currency': 'AED',
                'est_duration': '20 mins',
                'surge_index': '1.0x (AED 25 airport flagfall + meter)',
                'features': 'Credit card / Nol card accepted in every cab, free Wi-Fi, child seat on request',
                'booking_link': 'https://www.dubaitaxi.ae/',
                'badge': '🛡️ Official Airport Authority Fleet',
            },
            {
                'id': 'cab_dubai_uberblack',
                'provider': 'Uber Black / Careem Executive',
                'vehicle_type': 'Lexus ES300h / Tesla Model Y',
                'capacity': '4 Passengers · 3 Bags',
                'pickup_point': 'VIP Pick-up Curb Terminal 3',
                'fare_min': 110.00,
                'fare_max': 145.00,
                'currency': 'AED',
                'est_duration': '20 mins',
                'surge_index': '1.0x',
                'features': 'Suited chauffeur, chilled sparkling water, smartphone charger cables',
                'booking_link': 'https://m.uber.com/',
                'badge': '👑 Dubai Executive Chauffeur',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_dubai_ekar',
                'vehicle': 'Nissan Kicks / MG ZS Compact SUV',
                'type': 'Self-Drive Car (Pay Per Minute / Day)',
                'daily_rate': 140.00,
                'currency': 'AED',
                'deposit': 0.00,
                'fuel_policy': 'All fuel & RTA street parking included',
                'inclusions': 'Unlock car via smartphone app anywhere on street',
                'provider': 'Ekar Carshare Dubai',
                'booking_link': 'https://ekar.me/',
                'badge': '📱 Smartphone Keyless Rental',
            }
        ],
        'ferries': [
            {
                'id': 'fer_dubai_abra',
                'name': 'Traditional Wooden Abra Heritage Ferry',
                'route': 'Deira Old Souk Station ➔ Bur Dubai Abra Station (Creek Crossing)',
                'duration': '5 mins',
                'frequency': 'Continuous (Boats leave as soon as full, every 1 min)',
                'fare': 1.00,
                'currency': 'AED',
                'free_pedestrians': False,
                'scenic_score': '9.6 / 10 (Heart of old Arabia, gold and spice souks)',
                'booking_link': 'https://www.rta.ae/wps/portal/rta/ae/public-transport/marine/abra',
                'badge': '🪙 Most Charming 1 Dirham Ride on Earth',
            }
        ]
    },

    'kashmir': {
        'destination_label': 'Kashmir (Srinagar & Gulmarg), India',
        'city_id': 'cty_sxr',
        'currency': 'INR',
        'flights': [
            {
                'id': 'flt_kashmir_6e',
                'carrier': 'IndiGo Airlines',
                'carrier_code': '6E',
                'flight_no': '6E-2142',
                'origin_code': 'DEL',
                'origin_airport': 'Indira Gandhi Intl (T2), New Delhi',
                'dest_code': 'SXR',
                'dest_airport': 'Sheikh ul-Alam Intl Airport, Srinagar',
                'dep_time': '08:45',
                'arr_time': '10:15',
                'duration': '1h 30m',
                'stops': 0,
                'class': 'Economy',
                'fare': 3850.00,
                'currency': 'INR',
                'carbon_kg': 84.0,
                'luggage': '15kg check-in + 7kg cabin included',
                'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Delhi+to+Srinagar',
                'badge': '⚡ Direct Mountain Flight',
            }
        ],
        'trains': [
            {
                'id': 'trn_kashmir_vb',
                'train_no': '22477',
                'name': 'Vande Bharat Express (Kashmir Arch Corridor)',
                'origin_station': 'New Delhi Railway Station (NDLS)',
                'dest_station': 'Shri Mata Vaishno Devi Katra / Srinagar (USBRL)',
                'dep_time': '06:00',
                'arr_time': '14:00',
                'duration': '8h 00m',
                'class': 'Executive Chair Car (EC)',
                'fare': 2850.00,
                'currency': 'INR',
                'seats_status': '✅ Available (38 seats)',
                'carbon_kg': 14.2,
                'catering': 'Hot breakfast, Kashmiri kahwa tea & snacks',
                'speed': 'Traverses world\'s highest railway bridge over Chenab River (359m)',
                'booking_link': 'https://www.irctc.co.in/',
                'badge': '🌉 Engineering Wonder over Chenab Bridge',
            },
            {
                'id': 'trn_kashmir_vistadome',
                'train_no': '04687',
                'name': 'Kashmir Valley Vistadome Glass-Roof Express',
                'origin_station': 'Banihal Station',
                'dest_station': 'Srinagar Station ➔ Baramulla',
                'dep_time': '10:30',
                'arr_time': '12:05',
                'duration': '1h 35m',
                'class': 'Vistadome Glass Coach',
                'fare': 120.00,
                'currency': 'INR',
                'seats_status': '✅ Available (28 seats)',
                'carbon_kg': 2.1,
                'catering': 'Local snacks and saffron tea',
                'speed': 'Panoramic glass observation dome through snow-capped valleys',
                'booking_link': 'https://www.irctc.co.in/',
                'badge': '❄️ Spectacular Snow Panorama',
            }
        ],
        'metro': [
            {
                'id': 'mtr_kashmir_smartbus',
                'network': 'Srinagar Smart City Electric Bus',
                'line': 'Dal Lake Boulevard Express (Line E-1)',
                'route': 'Lal Chowk City Center ➔ Dal Lake Boulevard ➔ Nishat Bagh ➔ Shalimar Garden',
                'frequency': 'Every 15 mins',
                'operating_hours': '06:30 AM – 21:30 PM',
                'fare_token': 25.00,
                'fare_day_pass': 80.00,
                'currency': 'INR',
                'carbon_kg': 0.25,
                'station_stops': 12,
                'features': 'Silent zero-emission AC buses gliding alongside famous Dal Lake waters',
                'map_link': 'https://srinagarsmartcity.in/',
                'portal_link': 'https://srinagarsmartcity.in/',
                'badge': '🌿 Lake Boulevard Electric Transit',
            },
            {
                'id': 'mtr_kashmir_gondola',
                'network': 'Gulmarg Gondola Aerial Cable Transit',
                'line': 'Phase 1 & 2 Alpine Cableway (World\'s Highest, 3,980m)',
                'route': 'Gulmarg Resort Station (2,600m) ➔ Kongdoori (3,050m) ➔ Apharwat Peak (3,980m)',
                'frequency': 'Continuous panoramic cabins',
                'operating_hours': '09:00 AM – 17:00 PM',
                'fare_token': 800.00,
                'fare_day_pass': 1850.00,
                'currency': 'INR',
                'carbon_kg': 0.8,
                'station_stops': 3,
                'features': 'Highest operational cable car in the world, direct access to ski peaks',
                'map_link': 'https://www.jksccc.com/',
                'portal_link': 'https://www.jksccc.com/',
                'badge': '🚠 World\'s Highest Cable Transit',
            }
        ],
        'cabs': [
            {
                'id': 'cab_kashmir_prepaid',
                'provider': 'Srinagar Airport Taxi Drivers Union (Govt Regulated)',
                'vehicle_type': 'Toyota Innova / Mahindra Scorpio',
                'capacity': '6 Passengers · 6 Bags',
                'pickup_point': 'Prepaid Taxi Booth inside Srinagar Airport Arrival Terminal',
                'fare_min': 950.00,
                'fare_max': 1250.00,
                'currency': 'INR',
                'est_duration': '35 mins',
                'surge_index': '1.0x (Fixed Official Rate Slip)',
                'features': 'Police verified driver, heated cabin, handles mountain snow terrain',
                'booking_link': 'https://jktourism.jk.gov.in/',
                'badge': '🛡️ Official Fixed Tariff Counter',
            },
            {
                'id': 'cab_kashmir_chauffeur',
                'provider': 'Valley Luxury Chauffeur (Full Day Sightseeing)',
                'vehicle_type': 'Mahindra Scorpio 4x4 / Innova Crysta',
                'capacity': '6 Passengers · 4 Bags',
                'pickup_point': 'Houseboat / Hotel Doorstep Pickup',
                'fare_min': 2400.00,
                'fare_max': 2800.00,
                'currency': 'INR',
                'est_duration': '8 Hours (Full Day)',
                'surge_index': '1.0x Flat Day Rate',
                'features': 'Covers Shankaracharya Temple, Mughal Gardens, Pari Mahal & Local Bazaars',
                'booking_link': 'https://jktourism.jk.gov.in/',
                'badge': '🏔️ Full Day Mountain Tour Guide',
            }
        ],
        'rentals': [
            {
                'id': 'rnt_kashmir_himalayan',
                'vehicle': 'Royal Enfield Himalayan 450 Mountain Bike',
                'type': 'Adventure Touring Motorbike',
                'daily_rate': 1400.00,
                'currency': 'INR',
                'deposit': 3000.00,
                'fuel_policy': 'Same-to-Same',
                'inclusions': 'Pannier racks, heavy-duty crash guards, cold weather gloves',
                'provider': 'Kashmir Mountain Riders Club',
                'booking_link': 'https://www.rentrip.in/rent-bike-in-srinagar',
                'badge': '🏍️ Himalayan Pass Conqueror',
            }
        ],
        'ferries': [
            {
                'id': 'fer_kashmir_shikara',
                'name': 'Handcrafted Cedar Wood Dal Lake Shikara',
                'route': 'Ghat No. 1 ➔ Floating Vegetable Market ➔ Char Chinar Island ➔ Houseboats',
                'duration': '1 hour 30 mins',
                'frequency': 'Available on demand at all 28 Dal Lake Ghats',
                'fare': 500.00,
                'currency': 'INR',
                'free_pedestrians': False,
                'scenic_score': '10.0 / 10 (Most romantic water journey in India)',
                'booking_link': 'https://jktourism.jk.gov.in/',
                'badge': '🌸 Iconic Kashmiri Cultural Journey',
            }
        ]
    }
}


def _normalize_key(text):
    s = (text or '').lower()
    for k in ['goa', 'bali', 'paris', 'london', 'dubai', 'kashmir']:
        if k in s:
            return k
    return 'goa'


# ─── API Endpoints ─────────────────────────────────────────────────────────────

@transit_bp.route('', methods=['GET'])
@transit_bp.route('/', methods=['GET'])
def get_all_transit():
    """Fetch complete multi-modal travel options for a trip or route."""
    trip_id = request.args.get('trip_id')
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    mode_filter = request.args.get('mode', 'all').lower().strip()

    trip = None
    if trip_id:
        trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))

    if not origin:
        origin = trip.get('trp_origin') if trip and trip.get('trp_origin') else 'Mumbai, India'
    if not destination:
        destination = trip.get('trp_destination') if trip and trip.get('trp_destination') else 'Goa, India'

    dest_key = _normalize_key(destination)
    dataset = _TRANSIT_MODES_DB.get(dest_key, _TRANSIT_MODES_DB['goa'])

    # Read budget data if available for transport cap comparison
    transport_cap = 0
    transport_spent = 0
    currency = dataset['currency']

    if trip:
        currency = trip.get('trp_home_currency', dataset['currency'])
        budget = row_to_dict(query_db("SELECT * FROM budgets WHERE bud_trip_id = ?", (trip['trp_id'],), one=True))
        if budget:
            transport_cap = float(budget.get('bud_transport_cap') or 0)

        # Sum spent on transport
        spent_row = row_to_dict(query_db(
            "SELECT SUM(exp_home_amount) as total FROM expenses WHERE exp_trip_id = ? AND exp_category = 'transport' AND status = 'active'",
            (trip['trp_id'],), one=True
        ))
        if spent_row and spent_row.get('total'):
            transport_spent = float(spent_row['total'])

    # Filter by mode if specified
    flights = dataset['flights'] if mode_filter in ['all', 'flights'] else []
    trains = dataset['trains'] if mode_filter in ['all', 'trains'] else []
    metro = dataset['metro'] if mode_filter in ['all', 'metro'] else []
    cabs = dataset['cabs'] if mode_filter in ['all', 'cabs'] else []
    rentals = dataset['rentals'] if mode_filter in ['all', 'rentals'] else []
    ferries = dataset['ferries'] if mode_filter in ['all', 'ferries'] else []

    total_modes_count = len(dataset['flights']) + len(dataset['trains']) + len(dataset['metro']) + len(dataset['cabs']) + len(dataset['rentals']) + len(dataset['ferries'])

    return jsonify({
        'trip_id': trip_id,
        'origin': origin,
        'destination': destination,
        'dest_key': dest_key,
        'currency': currency,
        'budget_transport_cap': transport_cap,
        'budget_transport_spent': transport_spent,
        'budget_transport_remaining': max(0.0, transport_cap - transport_spent),
        'total_options_count': total_modes_count,
        'flights': flights,
        'trains': trains,
        'metro': metro,
        'cabs': cabs,
        'rentals': rentals,
        'ferries': ferries,
        'summary': {
            'fastest': dataset['flights'][0]['carrier'] + ' (' + dataset['flights'][0]['duration'] + ')' if dataset['flights'] else 'Flight',
            'cheapest': dataset['metro'][0]['line'] + ' (' + str(dataset['metro'][0]['fare_token']) + ' ' + dataset['currency'] + ')' if dataset['metro'] else 'Metro / Train',
            'eco_friendly': dataset['trains'][0]['name'] + ' (' + str(dataset['trains'][0]['carbon_kg']) + ' kg CO2)' if dataset['trains'] else 'Train',
        }
    })


@transit_bp.route('/book-or-plan', methods=['POST'])
def add_transit_to_itinerary():
    """Add a chosen travel option to the trip itinerary as an official itinerary item."""
    data = request.get_json(force=True)
    trip_id = data.get('trip_id')
    day_number = int(data.get('day_number', 1))
    title = data.get('title', 'Travel Transit')
    transit_type = data.get('transit_type', 'transport')  # 'flight' or 'transport'
    fare = float(data.get('fare', 0.0))
    currency = data.get('currency', 'INR')
    carbon_kg = float(data.get('carbon_kg', 12.0))
    duration = data.get('duration', '1h 30m')
    notes = data.get('notes', 'Transit booked')

    if not trip_id:
        return jsonify({'error': 'trip_id is required'}), 400

    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    # Ensure itinerary exists
    itn = row_to_dict(query_db("SELECT * FROM itineraries WHERE itn_trip_id = ? AND status = 'active'", (trip_id,), one=True))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    if not itn:
        itn_id = f"itn_{uuid.uuid4().hex[:12]}"
        mutate_db(
            "INSERT INTO itineraries (itn_id, itn_trip_id, itn_title, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (itn_id, trip_id, f"{trip['trp_name']} Itinerary", 'active', now, now)
        )
    else:
        itn_id = itn['itn_id']

    itm_id = f"itm_{uuid.uuid4().hex[:12]}"
    cost_tier = 'expensive' if fare > 2500 else ('free' if fare == 0 else 'budget')
    mutate_db(
        """INSERT INTO itinerary_items
        (itm_id, itm_itinerary_id, itm_day_number, itm_item_date, itm_title, itm_type,
         itm_start_time, itm_end_time, itm_estimated_cost, itm_currency, itm_notes, status, created_at, updated_at, itm_cost_tier)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (itm_id, itn_id, day_number, trip.get('trp_start_date', '2026-10-01'),
         title, transit_type, '08:00', '10:00', fare, currency,
         f"{notes} · Carbon: {carbon_kg} kg CO2 · Duration: {duration}",
         'active', now, now, cost_tier)
    )

    return jsonify({
        'item_id': itm_id,
        'title': title,
        'day_number': day_number,
        'message': f"Added '{title}' to Day {day_number} itinerary!"
    }), 201


@transit_bp.route('/log-expense', methods=['POST'])
def log_transit_expense():
    """Log transit ticket or cab ride directly into the expenses table as category 'transport'."""
    data = request.get_json(force=True)
    trip_id = data.get('trip_id')
    description = data.get('description', 'Transit Fare')
    amount = float(data.get('amount', 0.0))
    currency = data.get('currency', 'INR')

    if not trip_id:
        return jsonify({'error': 'trip_id is required'}), 400

    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    payer = row_to_dict(query_db("SELECT * FROM users LIMIT 1", one=True))
    payer_id = payer['usr_id'] if payer else 'usr_anil_001'

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    exp_id = f"exp_{uuid.uuid4().hex[:12]}"

    mutate_db(
        """INSERT INTO expenses
        (exp_id, exp_trip_id, exp_payer_id, exp_title, exp_category, exp_amount, exp_currency, exp_home_amount, exp_home_currency, exp_date, exp_split_type, exp_entered_via, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (exp_id, trip_id, payer_id, description, 'transport', amount, currency, amount, trip.get('trp_home_currency', currency), today, 'equal', 'manual', 'active', now, now)
    )

    return jsonify({
        'expense_id': exp_id,
        'description': description,
        'amount': amount,
        'currency': currency,
        'category': 'transport',
        'message': f"Logged '{description}' ({currency} {amount:,.2f}) under Transport expenses!"
    }), 201
