"""Hotels and Journey Route API routes — Curated stays, recommendation engine, booking links, and transit routes."""
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from db.database import query_db, mutate_db, row_to_dict

hotels_bp = Blueprint('hotels', __name__)

# Ensure trips table has trp_origin column
try:
    mutate_db("ALTER TABLE trips ADD COLUMN trp_origin TEXT DEFAULT 'Mumbai, India'")
except Exception:
    pass


# ─── Curated Hotels Database for All Destinations ──────────────────────────────

_HOTELS_DB = {
    'goa': [
        {
            'id': 'htl_goa_taj',
            'name': 'Taj Holiday Village Resort & Spa',
            'destination': 'Goa, India',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 2180,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 8500,
            'currency': 'INR',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'Unbeatable beachfront cottage living at Sinquerim Beach. Includes complimentary multi-cuisine buffet breakfast, private beach access, top security, and highest value for group stays.',
            'image_url': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=700&q=80',
            'location': 'Sinquerim, Candolim, North Goa',
            'lat': 15.5015,
            'lng': 73.7690,
            'amenities': ['Beachfront', 'Private Pool', 'Free Breakfast', 'Luxury Spa', 'Free High-speed WiFi'],
            'booking_url': 'https://www.booking.com/hotel/in/taj-holiday-village-resort-spa-goa.html',
        },
        {
            'id': 'htl_goa_w',
            'name': 'W Goa Resort (Vagator Cliff)',
            'destination': 'Goa, India',
            'stars': 5,
            'rating': 4.85,
            'reviews_count': 1420,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 14500,
            'currency': 'INR',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'High-energy luxury perched dramatically over Vagator Beach. Features the iconic Rockpool sunset lounge, private plunge pool villas, and celebrity chef restaurants.',
            'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=700&q=80',
            'location': 'Vagator Beach, Bardez, North Goa',
            'lat': 15.6022,
            'lng': 73.7370,
            'amenities': ['Clifftop Ocean View', 'Plunge Pools', 'Rockpool Club', 'Spa by Clarins', 'Valet Parking'],
            'booking_url': 'https://www.booking.com/hotel/in/w-goa.html',
        },
        {
            'id': 'htl_goa_fairfield',
            'name': 'Fairfield by Marriott Calangute',
            'destination': 'Goa, India',
            'stars': 4,
            'rating': 4.6,
            'reviews_count': 1890,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 4200,
            'currency': 'INR',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'Superb mid-range Marriott quality in the heart of Calangute. Short walking distance to beaches and famous shacks with pristine outdoor pool and lavish breakfast.',
            'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=700&q=80',
            'location': 'Calangute, North Goa',
            'lat': 15.5410,
            'lng': 73.7620,
            'amenities': ['Swimming Pool', 'Buffet Breakfast', 'Fitness Center', 'Free WiFi', 'Close to Beach'],
            'booking_url': 'https://www.booking.com/hotel/in/fairfield-by-marriott-goa-calangute.html',
        },
        {
            'id': 'htl_goa_hosteller',
            'name': 'The Hosteller Goa (Candolim)',
            'destination': 'Goa, India',
            'stars': 3,
            'rating': 4.7,
            'reviews_count': 950,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 1200,
            'currency': 'INR',
            'recommended': False,
            'recommendation_badge': '🎒 Backpacker Choice',
            'recommendation_reason': 'High-vibe social hostel with private air-conditioned rooms and deluxe dorms, swimming pool, cafe, co-working spaces, and daily organized group outings.',
            'image_url': 'https://images.unsplash.com/photo-1555854877-bab0e564b8d5?auto=format&fit=crop&w=700&q=80',
            'location': 'Candolim Road, North Goa',
            'lat': 15.5170,
            'lng': 73.7660,
            'amenities': ['Social Pool', 'Co-working WiFi', 'Cafe & Bar', 'Air Conditioned', 'Bicycle Rentals'],
            'booking_url': 'https://www.booking.com/hotel/in/the-hosteller-goa-candolim.html',
        },
    ],

    'bali': [
        {
            'id': 'htl_bali_alila',
            'name': 'Alila Seminyak Beachfront Resort',
            'destination': 'Bali, Indonesia',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 3100,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 2500000,
            'currency': 'IDR',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'Eco-luxe beachfront resort right on Seminyak sands. World-renowned 5 infinity pools cascading towards the Indian Ocean with complimentary morning yoga.',
            'image_url': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=700&q=80',
            'location': 'Jalan Taman Ganesha, Seminyak, Bali',
            'lat': -8.6912,
            'lng': 115.1565,
            'amenities': ['Beachfront', '5 Infinity Pools', 'Seasalt Restaurant', 'Free Yoga', 'Kids Club'],
            'booking_url': 'https://www.booking.com/hotel/id/alila-seminyak.html',
        },
        {
            'id': 'htl_bali_viceroy',
            'name': 'Viceroy Bali Valley Villas (Ubud)',
            'destination': 'Bali, Indonesia',
            'stars': 5,
            'rating': 4.95,
            'reviews_count': 1250,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 5800000,
            'currency': 'IDR',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'Family-owned ultra-luxury retreat perched on the steep ridge of the Valley of the Kings. Every villa features private heated infinity pools and helipad access.',
            'image_url': 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=700&q=80',
            'location': 'Jln. Lanyahan, Br Nagi, Ubud, Bali',
            'lat': -8.4985,
            'lng': 115.2754,
            'amenities': ['Heated Private Pool', 'Helipad', 'Cascades Fine Dining', 'Lembah Spa', 'Valley Views'],
            'booking_url': 'https://www.booking.com/hotel/id/viceroy-bali.html',
        },
        {
            'id': 'htl_bali_maya',
            'name': 'Maya Ubud Resort & Spa',
            'destination': 'Bali, Indonesia',
            'stars': 4.5,
            'rating': 4.8,
            'reviews_count': 2400,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 1750000,
            'currency': 'IDR',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'Sprawling 10-hectare rainforest sanctuary between river valleys. Two gorgeous infinity pools, open-air riverside spa pavilions, and daily shuttle to Ubud Center.',
            'image_url': 'https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?auto=format&fit=crop&w=700&q=80',
            'location': 'Petanu River Valley, Ubud, Bali',
            'lat': -8.5080,
            'lng': 115.2720,
            'amenities': ['Rainforest Sanctuary', '2 Pools', 'Riverside Spa', 'Free Shuttle', 'Yoga Deck'],
            'booking_url': 'https://www.booking.com/hotel/id/maya-ubud-resort-and-spa.html',
        },
        {
            'id': 'htl_bali_kuta',
            'name': 'The Kuta Beach Heritage Hotel',
            'destination': 'Bali, Indonesia',
            'stars': 4,
            'rating': 4.5,
            'reviews_count': 1800,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 750000,
            'currency': 'IDR',
            'recommended': False,
            'recommendation_badge': '🎒 Budget Traveler',
            'recommendation_reason': 'Located directly opposite Kuta Beach sunset boardwalk. Rooftop saltwater pool overlooking the surf break, gym, and proximity to shopping bazaars.',
            'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=700&q=80',
            'location': 'Jalan Pantai Kuta, Badung, Bali',
            'lat': -8.7190,
            'lng': 115.1680,
            'amenities': ['Beachfront Opposite', 'Rooftop Pool', 'Breakfast Included', 'Surf Spot Proximity'],
            'booking_url': 'https://www.booking.com/hotel/id/the-kuta-beach-heritage-hotel.html',
        },
    ],

    'paris': [
        {
            'id': 'htl_paris_marais',
            'name': 'Le Marais Hôtel de Joséphine',
            'destination': 'Paris, France',
            'stars': 4,
            'rating': 4.85,
            'reviews_count': 1650,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 320,
            'currency': 'EUR',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'Quintessential Parisian charm in historic Le Marais. Steps from Place des Vosges and Saint-Paul Metro, with complimentary French bakery breakfast and boutique courtyard.',
            'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=700&q=80',
            'location': 'Rue de Turenne, Le Marais, 75004 Paris',
            'lat': 48.8566,
            'lng': 2.3612,
            'amenities': ['Historic Marais Center', 'Artisanal Breakfast', 'Courtyard Garden', 'Metro Saint-Paul 200m', 'Free WiFi'],
            'booking_url': 'https://www.booking.com/city/fr/paris.html',
        },
        {
            'id': 'htl_paris_plaza',
            'name': 'Hôtel Plaza Athénée (Avenue Montaigne)',
            'destination': 'Paris, France',
            'stars': 5,
            'rating': 4.95,
            'reviews_count': 980,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 1250,
            'currency': 'EUR',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'Legendary Haute Couture palace hotel adorned with signature red geraniums. Direct Eiffel Tower balcony vistas, Dior Institut spa, and Cour Jardin dining.',
            'image_url': 'https://images.unsplash.com/photo-1549144511-f099e773c147?auto=format&fit=crop&w=700&q=80',
            'location': '25 Avenue Montaigne, 75008 Paris',
            'lat': 48.8660,
            'lng': 2.3040,
            'amenities': ['Direct Eiffel Views', 'Dior Spa', 'Michelin Dining', 'Haute Couture District', 'Chauffeur Service'],
            'booking_url': 'https://www.dorchestercollection.com/paris/hotel-plaza-athenee',
        },
        {
            'id': 'htl_paris_citizenm',
            'name': 'citizenM Paris Gare de Lyon',
            'destination': 'Paris, France',
            'stars': 4,
            'rating': 4.7,
            'reviews_count': 3800,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 145,
            'currency': 'EUR',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'High-tech affordable boutique design with panoramic rooftop cocktail bar overlooking the Seine. iPad room mood lighting, power showers, and instant transit connectivity.',
            'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=700&q=80',
            'location': '8 Rue Van Gogh, 75012 Paris',
            'lat': 48.8445,
            'lng': 2.3710,
            'amenities': ['Rooftop Sky Bar', 'XL King Beds', 'Ultra-fast WiFi', 'Gare de Lyon Hub', 'Smart Controls'],
            'booking_url': 'https://www.citizenm.com/hotels/europe/paris/paris-gare-de-lyon-hotel',
        },
        {
            'id': 'htl_paris_generator',
            'name': 'Generator Paris (Canal Saint-Martin)',
            'destination': 'Paris, France',
            'stars': 3,
            'rating': 4.5,
            'reviews_count': 4500,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 55,
            'currency': 'EUR',
            'recommended': False,
            'recommendation_badge': '🎒 Budget Traveler',
            'recommendation_reason': 'Vibrant designer hostel/hotel with views of Sacré-Cœur from the 9th-floor rooftop bar. Private en-suite terrace rooms available at unbeatable prices.',
            'image_url': 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=700&q=80',
            'location': 'Place du Colonel Fabien, 75010 Paris',
            'lat': 48.8770,
            'lng': 2.3685,
            'amenities': ['Rooftop Bar with Views', 'Metro on Doorstep', 'Moroccan Cafe', 'Air Conditioned', 'Luggage Lockers'],
            'booking_url': 'https://staygenerator.com/hostels/paris',
        },
    ],

    'london': [
        {
            'id': 'htl_lon_savoy',
            'name': 'The Savoy London (Strand)',
            'destination': 'London, United Kingdom',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 2900,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 450,
            'currency': 'GBP',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'World-famous British landmark on the Strand with panoramic Thames river suites. Home to Gordon Ramsay\'s Savoy Grill, American Bar, and exceptional theater district location.',
            'image_url': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=700&q=80',
            'location': 'The Strand, Covent Garden, London WC2R 0EZ',
            'lat': 51.5102,
            'lng': -0.1198,
            'amenities': ['River Thames Views', 'Gordon Ramsay Grill', 'Butler Service', 'American Bar', 'Covent Garden 2min'],
            'booking_url': 'https://www.thesavoylondon.com',
        },
        {
            'id': 'htl_lon_ritz',
            'name': 'The Ritz London (Mayfair)',
            'destination': 'London, United Kingdom',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 1850,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 780,
            'currency': 'GBP',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'The gold standard of royal English luxury overlooking Green Park. Renowned Palm Court afternoon tea, Michelin dining, and lavish neoclassical Louis XVI interior suites.',
            'image_url': 'https://images.unsplash.com/photo-1587985064135-0366536eab42?auto=format&fit=crop&w=700&q=80',
            'location': '150 Piccadilly, St. James\'s, London W1J 9BR',
            'lat': 51.5072,
            'lng': -0.1416,
            'amenities': ['Michelin-Starred Dining', 'Palm Court Tea', 'Overlooking Green Park', 'Valet Parking', 'Concierge Keys'],
            'booking_url': 'https://www.theritzlondon.com',
        },
        {
            'id': 'htl_lon_hoxton',
            'name': 'The Hoxton Holborn',
            'destination': 'London, United Kingdom',
            'stars': 4,
            'rating': 4.7,
            'reviews_count': 3100,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 185,
            'currency': 'GBP',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'Chic industrial-aesthetic rooms with Roberts DAB radios and breakfast bags delivered to your door. Steps from the British Museum, Covent Garden, and Soho nightlife.',
            'image_url': 'https://images.unsplash.com/photo-1596394516093-501ba68a0ba6?auto=format&fit=crop&w=700&q=80',
            'location': '199-206 High Holborn, London WC1V 7BD',
            'lat': 51.5175,
            'lng': -0.1215,
            'amenities': ['Covent Garden Walk', 'Daily Breakfast Bag', 'Vibrant Lobby Cafe', 'Free Calls', 'Holborn Tube 100m'],
            'booking_url': 'https://thehoxton.com/london/holborn',
        },
        {
            'id': 'htl_lon_citizenm',
            'name': 'citizenM Tower of London',
            'destination': 'London, United Kingdom',
            'stars': 4,
            'rating': 4.7,
            'reviews_count': 4100,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 125,
            'currency': 'GBP',
            'recommended': False,
            'recommendation_badge': '🎒 Budget Traveler',
            'recommendation_reason': 'Directly atop Tower Hill Underground Station. Floor-to-ceiling panoramic views of Tower Bridge and Tower of London from the 7th-floor cloudM rooftop bar.',
            'image_url': 'https://images.unsplash.com/photo-1568495248636-6432b97bd949?auto=format&fit=crop&w=700&q=80',
            'location': '40 Trinity Square, London EC3N 4DJ',
            'lat': 51.5098,
            'lng': -0.0765,
            'amenities': ['Direct Tube Station Access', 'Tower Bridge Views', 'Rooftop Bar', 'High-pressure Showers'],
            'booking_url': 'https://www.citizenm.com/hotels/europe/london/tower-of-london-hotel',
        },
    ],

    'dubai': [
        {
            'id': 'htl_dxb_atlantis',
            'name': 'Atlantis The Palm Ocean Suites',
            'destination': 'Dubai, UAE',
            'stars': 5,
            'rating': 4.85,
            'reviews_count': 5200,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 1800,
            'currency': 'AED',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'Prime Palm Jumeirah landmark offering complimentary unlimited access to Aquaventure Waterpark and Lost Chambers Aquarium for all guests. Private pristine beach and 30+ restaurants.',
            'image_url': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=700&q=80',
            'location': 'Crescent Rd, The Palm Jumeirah, Dubai',
            'lat': 25.1303,
            'lng': 55.1173,
            'amenities': ['Free Waterpark Access', 'Private White Sand Beach', 'Aquarium Access', 'Nobu Restaurant', 'Luxury Spa'],
            'booking_url': 'https://www.atlantis.com/dubai/atlantis-the-palm',
        },
        {
            'id': 'htl_dxb_burj',
            'name': 'Burj Al Arab Jumeirah (Sail Icon)',
            'destination': 'Dubai, UAE',
            'stars': 7,
            'rating': 4.95,
            'reviews_count': 1100,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 5500,
            'currency': 'AED',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'The world\'s most famous 7-star sail icon on its own private island. Features 24-karat gold interiors, private duplex suites with personal butler, and helicopter transfers.',
            'image_url': 'https://images.unsplash.com/photo-1580674684081-7617fbf3d745?auto=format&fit=crop&w=700&q=80',
            'location': 'Jumeirah St, Umm Suqeim 3, Dubai',
            'lat': 25.1412,
            'lng': 55.1852,
            'amenities': ['Private Island', 'Personal Butler', 'Helipad', 'Hermès Toiletries', 'Submarine Seafood Restaurant'],
            'booking_url': 'https://www.jumeirah.com/en/stay/dubai/burj-al-arab-jumeirah',
        },
        {
            'id': 'htl_dxb_rove',
            'name': 'Rove Downtown Dubai',
            'destination': 'Dubai, UAE',
            'stars': 3.5,
            'rating': 4.7,
            'reviews_count': 4800,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 340,
            'currency': 'AED',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'Exceptional location directly opposite Dubai Mall and Burj Khalifa. Features outdoor saltwater pool with skyscraper views, 24-hour convenience store, and self-service laundromat.',
            'image_url': 'https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?auto=format&fit=crop&w=700&q=80',
            'location': 'Downtown Dubai, Behind Dubai Mall',
            'lat': 25.1972,
            'lng': 55.2810,
            'amenities': ['Burj Khalifa View Pool', 'Dubai Mall 5min Walk', '24h Gym & Laundromat', 'Free High-speed WiFi'],
            'booking_url': 'https://www.rovehotels.com/en/hotels/rove-downtown',
        },
        {
            'id': 'htl_dxb_citymax',
            'name': 'Citymax Hotel Bur Dubai',
            'destination': 'Dubai, UAE',
            'stars': 3,
            'rating': 4.4,
            'reviews_count': 3900,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 160,
            'currency': 'AED',
            'recommended': False,
            'recommendation_badge': '🎒 Budget Traveler',
            'recommendation_reason': 'Incredible affordability close to Dubai Creek, Gold & Spice Souks, and metro stations. Rooftop pool, modern air-conditioned rooms, and 24-hour dining.',
            'image_url': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=700&q=80',
            'location': 'Kuwait St, Al Mankhool, Bur Dubai',
            'lat': 25.2510,
            'lng': 55.2980,
            'amenities': ['Rooftop Swimming Pool', 'Metro 500m', '24-hour Coffee Shop', 'Free Parking', 'Fitness Center'],
            'booking_url': 'https://www.citymaxhotels.com',
        },
    ],

    'kashmir': [
        {
            'id': 'htl_kas_mascot',
            'name': 'Mascot Heritage Deluxe Houseboat',
            'destination': 'Kashmir, India',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 1340,
            'category': 'luxury',
            'price_tier': 'budget',
            'price_per_night': 5500,
            'currency': 'INR',
            'recommended': True,
            'recommendation_badge': '⭐ Recommended by CFO',
            'recommendation_reason': 'Authentic carved cedarwood heritage houseboat floating on Dal Lake. Includes personal butler, royal Wazwan feasts, wood-carved verandah overlooking Zabarwan peaks, and complimentary shikara transfers.',
            'image_url': 'https://images.unsplash.com/photo-1598091383021-15ddea10925d?auto=format&fit=crop&w=700&q=80',
            'location': 'Ghat No 7, Boulevard Rd, Dal Lake, Srinagar',
            'lat': 34.1118,
            'lng': 74.8419,
            'amenities': ['Floating Verandah', 'Personal Butler', 'Traditional Wazwan', 'Private Shikara Transfers', 'Heated Bedrooms'],
            'booking_url': 'https://www.booking.com/city/in/srinagar.html',
        },
        {
            'id': 'htl_kas_khyber',
            'name': 'The Khyber Himalayan Resort & Spa',
            'destination': 'Kashmir, India',
            'stars': 5,
            'rating': 4.9,
            'reviews_count': 2100,
            'category': 'luxury',
            'price_tier': 'expensive',
            'price_per_night': 18500,
            'currency': 'INR',
            'recommended': False,
            'recommendation_badge': '👑 Luxury Splurge',
            'recommendation_reason': 'Nestled 8,825 feet in Pir Panjal ranges of Gulmarg. Heated indoor swimming pool with floor-to-ceiling glass mountain views, L\'Occitane spa, and ski-in ski-out access to the world-famous Gondola.',
            'image_url': 'https://images.unsplash.com/photo-1548777123-e216912df7d8?auto=format&fit=crop&w=700&q=80',
            'location': 'Gulmarg, Baramulla, Kashmir 193403',
            'lat': 34.0484,
            'lng': 74.3805,
            'amenities': ['Heated Glass Pool', 'Ski-in Ski-out Access', 'L\'Occitane Spa', 'Pine Mountain Views', 'Fireplace Lounges'],
            'booking_url': 'https://www.khyberhotels.com',
        },
        {
            'id': 'htl_kas_hilltop',
            'name': 'Hotel Hilltop Gulmarg',
            'destination': 'Kashmir, India',
            'stars': 4,
            'rating': 4.6,
            'reviews_count': 1450,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 4800,
            'currency': 'INR',
            'recommended': True,
            'recommendation_badge': '🎒 Best Value Pick',
            'recommendation_reason': 'Warm alpine hotel minutes from Gulmarg ice-rink and Gondola Phase 1. Features central heating, multi-cuisine restaurant, and snowy valley panoramic views.',
            'image_url': 'https://images.unsplash.com/photo-1517840901100-8179e982acb7?auto=format&fit=crop&w=700&q=80',
            'location': 'Near Gondola Station, Gulmarg',
            'lat': 34.0505,
            'lng': 74.3840,
            'amenities': ['Central Heating', 'Gondola Proximity', 'Valley View Rooms', 'Buffet Dining', 'Ski Rental Desk'],
            'booking_url': 'https://www.booking.com/hotel/in/hilltop-gulmarg.html',
        },
        {
            'id': 'htl_kas_zostel',
            'name': 'Zostel Srinagar (Boulevard Road)',
            'destination': 'Kashmir, India',
            'stars': 3,
            'rating': 4.8,
            'reviews_count': 880,
            'category': 'budget',
            'price_tier': 'budget',
            'price_per_night': 1400,
            'currency': 'INR',
            'recommended': False,
            'recommendation_badge': '🎒 Budget Traveler',
            'recommendation_reason': 'Cozy traditional Kashmiri wooden villa located right along Boulevard Road opposite Dal Lake. Rooftop sunset cafe, high-speed WiFi, and vibrant community travelers.',
            'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=700&q=80',
            'location': 'Boulevard Road, Near Dal Lake, Srinagar',
            'lat': 34.0950,
            'lng': 74.8350,
            'amenities': ['Lakeside View', 'High-Speed WiFi', 'Rooftop Cafe', 'Tour Desk', 'Air Conditioned / Heated'],
            'booking_url': 'https://www.zostel.com/zostel/srinagar',
        },
    ]
}


def _normalize_key(text):
    s = (text or '').lower()
    for k in ('goa', 'bali', 'paris', 'london', 'dubai', 'kashmir'):
        if k in s:
            return k
    return 'goa'


def _compute_transit(origin, destination):
    """Compute flight and ground transit estimate for start_place and destination."""
    dest_key = _normalize_key(destination)
    orig_key = (origin or 'Mumbai, India').strip()

    routes = {
        'goa': {
            'flight_badge': '✈️ Flight: BOM → GOI (1h 15m)',
            'flight_fare': 'IndiGo / Air India · Approx ₹3,200',
            'transit_alt': '🚆 Vande Bharat Express (8h 20m) · 580 km',
            'distance': '580 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+from+Mumbai+to+Goa',
        },
        'bali': {
            'flight_badge': '✈️ Flight: BOM → DPS (7h 50m, 1-stop)',
            'flight_fare': 'Singapore Air / VietJet · Approx ₹18,500',
            'transit_alt': '🌊 Fast Ferry from Sanur to Islands · 35 min',
            'distance': '5,420 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+to+Bali',
        },
        'paris': {
            'flight_badge': '✈️ Flight: Direct (9h 30m) or 🚆 Eurostar (2h 16m)',
            'flight_fare': 'Air France / Eurostar · Approx €65 – €420',
            'transit_alt': '🚆 TGV High-Speed Train · 450 km',
            'distance': '6,950 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+to+Paris',
        },
        'london': {
            'flight_badge': '✈️ Flight: Direct BA / Virgin (9h 45m)',
            'flight_fare': 'British Airways / Virgin Atlantic · Approx £450',
            'transit_alt': '🚇 Heathrow Express to Paddington (15m)',
            'distance': '7,200 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+to+London',
        },
        'dubai': {
            'flight_badge': '✈️ Flight: Direct Emirates / Air India (3h 15m)',
            'flight_fare': 'Emirates / FlyDubai · Approx AED 550 (~₹12,400)',
            'transit_alt': '🚗 RTA Airport Metro Red Line Direct',
            'distance': '1,930 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+to+Dubai',
        },
        'kashmir': {
            'flight_badge': '✈️ Flight: DEL/BOM → SXR (1h 25m – 2h 45m)',
            'flight_fare': 'IndiGo / SpiceJet · Approx ₹4,500',
            'transit_alt': '🚗 Srinagar Highway Saffron Corridor · 280 km',
            'distance': '850 km',
            'booking_link': 'https://www.google.com/travel/flights?q=flights+to+Srinagar',
        },
    }

    info = routes.get(dest_key, routes['goa']).copy()
    info['origin'] = orig_key
    info['destination'] = destination or 'Goa, India'
    return info


# ─── API Routes ───────────────────────────────────────────────────────────────

@hotels_bp.route('', methods=['GET'])
@hotels_bp.route('/', methods=['GET'])
def get_hotels():
    """Get curated hotels, prices, recommendations, booking links, and route transit for destination."""
    dest = request.args.get('destination') or request.args.get('dest') or ''
    origin = request.args.get('origin') or request.args.get('start_place') or 'Mumbai, India'
    trip_id = request.args.get('trip_id')

    if trip_id:
        trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
        if trip:
            if not dest:
                dest = trip.get('trp_destination', 'Goa, India')
            if 'trp_origin' in trip and trip['trp_origin']:
                origin = trip['trp_origin']

    dest_key = _normalize_key(dest)
    hotels = _HOTELS_DB.get(dest_key, _HOTELS_DB['goa'])
    route_info = _compute_transit(origin, dest)

    return jsonify({
        'destination': dest or 'Goa, India',
        'origin': origin,
        'dest_key': dest_key,
        'count': len(hotels),
        'route': route_info,
        'hotels': hotels,
    })


@hotels_bp.route('/add-to-itinerary', methods=['POST'])
def add_hotel_to_itinerary():
    """Add a chosen hotel stay to the trip itinerary as an accommodation item."""
    data = request.get_json(force=True)
    trip_id = data.get('trip_id')
    hotel_id = data.get('hotel_id')
    day_number = int(data.get('day_number', 1))

    if not trip_id:
        return jsonify({'error': 'trip_id is required'}), 400

    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404

    # Find hotel data
    dest_key = _normalize_key(trip.get('trp_destination'))
    candidates = _HOTELS_DB.get(dest_key, _HOTELS_DB['goa'])
    hotel = next((h for h in candidates if h['id'] == hotel_id), None)
    if not hotel:
        hotel = candidates[0]  # fallback

    # Ensure itinerary exists
    itn = row_to_dict(query_db(
        "SELECT * FROM itineraries WHERE itn_trip_id = ? AND status = 'active'",
        (trip_id,), one=True
    ))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    if not itn:
        itn_id = f"itn_{uuid.uuid4().hex[:12]}"
        mutate_db(
            "INSERT INTO itineraries (itn_id, itn_trip_id, itn_title, itn_notes, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (itn_id, trip_id, f"{trip['trp_name']} Itinerary", None, 'active', now, now)
        )
    else:
        itn_id = itn['itn_id']

    # Date calculation
    try:
        from datetime import datetime as dt, timedelta
        start = dt.strptime(trip['trp_start_date'], '%Y-%m-%d')
        item_date = (start + timedelta(days=day_number - 1)).strftime('%Y-%m-%d')
    except Exception:
        item_date = trip.get('trp_start_date', '')

    itm_id = f"itm_{uuid.uuid4().hex[:12]}"
    mutate_db(
        """INSERT INTO itinerary_items
        (itm_id, itm_itinerary_id, itm_day_number, itm_item_date, itm_title, itm_type,
         itm_location, itm_lat, itm_lng, itm_start_time, itm_end_time,
         itm_estimated_cost, itm_currency, itm_notes, status, created_at, updated_at, itm_cost_tier)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (itm_id, itn_id, day_number, item_date,
         f"Check-in at {hotel['name']}",
         'hotel',
         hotel['location'],
         hotel['lat'], hotel['lng'],
         '14:00', '15:30',
         hotel['price_per_night'],
         hotel['currency'],
         f"Stay booked at {hotel['name']} ({hotel['recommendation_badge']})",
         'active', now, now, hotel['price_tier'])
    )

    return jsonify({
        'item_id': itm_id,
        'hotel_name': hotel['name'],
        'day_number': day_number,
        'message': f"Added '{hotel['name']}' to Day {day_number} itinerary!",
    }), 201


@hotels_bp.route('/update-route', methods=['POST'])
def update_trip_route():
    """Update start place and destination for the trip."""
    data = request.get_json(force=True)
    trip_id = data.get('trip_id')
    origin = data.get('origin', 'Mumbai, India').strip()
    destination = data.get('destination', '').strip()

    if not trip_id:
        return jsonify({'error': 'trip_id is required'}), 400

    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    try:
        if destination:
            mutate_db("UPDATE trips SET trp_origin = ?, trp_destination = ?, updated_at = ? WHERE trp_id = ?", (origin, destination, now, trip_id))
        else:
            mutate_db("UPDATE trips SET trp_origin = ?, updated_at = ? WHERE trp_id = ?", (origin, now, trip_id))
    except Exception as e:
        print("Note on update route db:", e)

    dest_key = _normalize_key(destination)
    hotels = _HOTELS_DB.get(dest_key, _HOTELS_DB['goa'])
    route_info = _compute_transit(origin, destination)

    return jsonify({
        'message': 'Trip journey route updated',
        'origin': origin,
        'destination': destination,
        'route': route_info,
        'hotels': hotels,
    })
