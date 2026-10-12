"""
AI Recommendation Service — Smart Travel Budget Optimization Engine
Generates proactive suggestions based on destination, travel style, spending velocity, and category caps.
"""

from decimal import Decimal
from typing import Dict, List, Any
from db.database import query_db, row_to_dict, rows_to_list
from services.breach_detector import check_breach

# Destination-specific local knowledge base for high-value savings
DESTINATION_INSIGHTS = {
    'goa': {
        'dining': [
            {'title': 'Authentic Beach Shacks over Luxury Diners', 'desc': 'Swap high-end resorts for iconic shacks like Britto\'s in Baga or Curlies in Anjuna. Enjoy fresh fish curry thalis for ₹350–₹500 instead of ₹2,000+ hotel dining.', 'savings_pct': 55, 'avg_savings': 1500},
            {'title': 'Panjim Fountainhas Heritage Cafes', 'desc': 'Explore Portuguese quarters for traditional poi bread and chorizo pav at local bakeries (₹80–₹150).', 'savings_pct': 40, 'avg_savings': 800},
        ],
        'activities': [
            {'title': 'Combo Water Sports Package at Calangute', 'desc': 'Book parasailing, jet-ski, and banana ride as a bundled package rather than single activities, saving ~₹1,500/person.', 'savings_pct': 35, 'avg_savings': 1500},
            {'title': 'Sunset at Chapora & Aguada Forts (Free Entry)', 'desc': 'Skip paid beach-club cover charges and catch world-class golden hour sunsets from the historic ramparts of Chapora Fort.', 'savings_pct': 100, 'avg_savings': 2000},
            {'title': 'Early Morning Scuba Sessions at Grande Island', 'desc': 'First-boat departures (7:30 AM) offer better underwater visibility and morning off-peak rates.', 'savings_pct': 25, 'avg_savings': 1000},
        ],
        'transport': [
            {'title': 'Rent Self-Drive Scooter', 'desc': 'Hiring an Activa (₹350–₹500/day) cuts airport/beach taxi fares (₹1,500–₹2,500 per one-way ride) significantly.', 'savings_pct': 70, 'avg_savings': 3500},
        ],
    },
    'bali': {
        'dining': [
            {'title': 'Dine at Local Warungs', 'desc': 'Traditional Balinese Warungs (Warung Nia, Made\'s Warung) serve delicious Nasi Campur and Satay for 40,000 IDR (approx ₹220) vs 250,000 IDR at Seminyak beach clubs.', 'savings_pct': 60, 'avg_savings': 1800},
        ],
        'activities': [
            {'title': 'Campuhan Ridge Walk & Tegalalang Morning Entry', 'desc': 'Arrive before 8:00 AM at Ubud rice terraces to avoid crowds and guide markups.', 'savings_pct': 40, 'avg_savings': 1200},
        ],
        'transport': [
            {'title': 'Use Grab / Gojek Bike instead of Private Drivers', 'desc': 'Gojek motorcycle taxis navigate Canggu/Seminyak shortcuts 3x faster and cost 80% less than cars.', 'savings_pct': 65, 'avg_savings': 2000},
        ],
    },
    'tokyo': {
        'dining': [
            {'title': 'Depachika Food Halls & Tachigui Soba', 'desc': 'Basement gourmet food halls in Isetan/Takashimaya discount bento boxes by 30-50% after 7:30 PM. Standing soba counters provide hearty meals for ¥500.', 'savings_pct': 50, 'avg_savings': 2200},
        ],
        'activities': [
            {'title': 'Tokyo Metropolitan Govt Observatory', 'desc': 'Free 45th-floor panoramic skyline view in Shinjuku instead of paying ¥2,500+ for Shibuya Sky or Skytree.', 'savings_pct': 100, 'avg_savings': 1800},
        ],
        'transport': [
            {'title': '72-Hour Tokyo Subway Pass', 'desc': 'Get unlimited Tokyo Metro & Toei Subway rides for ¥1,500 (saves ~60% over single IC card taps).', 'savings_pct': 60, 'avg_savings': 2500},
        ],
    },
    'paris': {
        'dining': [
            {'title': 'Marché & Seine River Picnic', 'desc': 'Buy fresh baguette, artisan brie, charcuterie, and grapes from local markets for €12 and picnic by the Eiffel Tower rather than €70 tourist brasseries.', 'savings_pct': 65, 'avg_savings': 3000},
        ],
        'activities': [
            {'title': 'Museum Pass & First Sunday Free Entry', 'desc': 'Pre-book Paris Museum Pass or visit national museums on the first Sunday of the month for free admission.', 'savings_pct': 40, 'avg_savings': 2500},
        ],
        'transport': [
            {'title': 'Navigo Easy Carnet vs Single Tickets', 'desc': 'Load 10 digital t+ tickets on your phone for €17.35 instead of on-board bus tickets.', 'savings_pct': 30, 'avg_savings': 1200},
        ],
    },
}


def get_ai_recommendations(trip_id: str) -> Dict[str, Any]:
    """
    Generate tailored AI recommendations based on:
    - Trip metadata (destination, travel style, dates)
    - Real spending vs category caps
    - Velocity and predicted overshoot
    """
    trip = row_to_dict(query_db("SELECT * FROM trips WHERE trp_id = ?", (trip_id,), one=True))
    if not trip:
        return {'recommendations': [], 'summary': 'Trip not found'}

    budget = row_to_dict(query_db("SELECT * FROM budgets WHERE bud_trip_id = ? AND status='active'", (trip_id,), one=True))
    breach_data = check_breach(trip_id)

    destination_raw = trip.get('trp_destination', '').lower()
    desc = (trip.get('trp_description') or '').lower()
    
    # Infer travel style from description or default to moderate
    travel_style = 'moderate'
    if 'luxury' in desc:
        travel_style = 'luxury'
    elif 'budget' in desc:
        travel_style = 'budget'

    home_cur = trip.get('trp_home_currency', 'INR')
    sym = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 'THB': '฿', 'SGD': 'S$'}.get(home_cur, home_cur + ' ')

    total_spent = float(breach_data.get('total_spent', 0))
    total_cap = float(breach_data.get('total_cap', 0))
    cat_summary = breach_data.get('category_summary', {})
    breaches = breach_data.get('breaches', [])

    recommendations = []
    total_potential_savings = 0.0

    # 1. Check for specific destination tips
    dest_key = None
    for k in DESTINATION_INSIGHTS:
        if k in destination_raw:
            dest_key = k
            break
    dest_pack = DESTINATION_INSIGHTS.get(dest_key, DESTINATION_INSIGHTS['goa'])

    # 2. Category Breaches & Warnings — Urgent Remediations
    food_info = cat_summary.get('food', {})
    if food_info.get('status') in ('breached', 'warning'):
        overshoot = float(food_info.get('overshoot', 0))
        dining_tip = dest_pack['dining'][0]
        savings = float(dining_tip['avg_savings'])
        total_potential_savings += savings
        recommendations.append({
            'id': 'rec_food_rebalance',
            'type': 'dining_alternative',
            'category': 'food',
            'priority': 'urgent',
            'title': f"Optimize Food Spend in {trip.get('trp_destination')}",
            'description': f"Food spend has {food_info.get('status')}. {dining_tip['desc']}",
            'potential_savings': savings,
            'formatted_savings': f"Save ~{sym}{savings:,.0f}",
            'action_label': 'Apply Shack Dining Strategy',
            'impact': 'high',
        })

    # 3. Transport Optimization
    transport_info = cat_summary.get('transport', {})
    transport_tip = dest_pack.get('transport', [None])[0]
    if transport_tip:
        t_savings = float(transport_tip['avg_savings'])
        total_potential_savings += t_savings
        recommendations.append({
            'id': 'rec_transport_opt',
            'type': 'transport_alternative',
            'category': 'transport',
            'priority': 'medium' if transport_info.get('status') in ('breached', 'warning') else 'smart_tip',
            'title': transport_tip['title'],
            'description': transport_tip['desc'],
            'potential_savings': t_savings,
            'formatted_savings': f"Save ~{sym}{t_savings:,.0f}",
            'action_label': 'Explore Rental Options',
            'impact': 'medium',
        })

    # 4. Activity Deals
    activity_tips = dest_pack.get('activities', [])
    if activity_tips:
        act_tip = activity_tips[0]
        a_savings = float(act_tip['avg_savings'])
        total_potential_savings += a_savings
        recommendations.append({
            'id': 'rec_activity_deals',
            'type': 'activity_deal',
            'category': 'activities',
            'priority': 'smart_tip',
            'title': act_tip['title'],
            'description': act_tip['desc'],
            'potential_savings': a_savings,
            'formatted_savings': f"Save ~{sym}{a_savings:,.0f}",
            'action_label': 'View Combo Pass',
            'impact': 'medium',
        })

    # 5. Travel Style Calibration
    if travel_style == 'budget':
        recommendations.append({
            'id': 'rec_style_budget',
            'type': 'style_calibration',
            'category': 'misc',
            'priority': 'lifestyle',
            'title': 'Backpacker Micro-Budgeting',
            'description': 'Track daily small spends (bottled water, snacks, local tips). Buying 20L water dispensers at homestays saves ~₹600 over individual PET bottles.',
            'potential_savings': 600.0,
            'formatted_savings': f"Save ~{sym}600",
            'action_label': 'Apply Micro Cap',
            'impact': 'low',
        })
        total_potential_savings += 600.0
    elif travel_style == 'luxury':
        recommendations.append({
            'id': 'rec_style_luxury',
            'type': 'style_calibration',
            'category': 'accommodation',
            'priority': 'lifestyle',
            'title': 'Luxury Value Optimizer',
            'description': 'Direct-book 5-star properties via hotel loyalty programs or concierge desks for complimentary upgrades and inclusive high-end breakfasts (saving ~₹3,500/day).',
            'potential_savings': 3500.0,
            'formatted_savings': f"Save ~{sym}3,500",
            'action_label': 'Request Hotel Perks',
            'impact': 'high',
        })
        total_potential_savings += 3500.0

    # 6. Daily Safe Burn Rate Adjustment Suggestion
    remaining = total_cap - total_spent
    rebalancing_advice = None
    if remaining > 0 and total_cap > 0:
        # Calculate daily allowance
        rebalancing_advice = (
            f"Current runway: {sym}{remaining:,.2f} remaining. "
            f"Adopting our top 2 recommendations will boost your safe allowance by {sym}{total_potential_savings:,.0f}."
        )
    elif remaining < 0:
        rebalancing_advice = (
            f"⚠️ Budget overshot by {sym}{abs(remaining):,.2f}. "
            f"Implementing these suggestions recovers {sym}{total_potential_savings:,.0f} of the deficit immediately."
        )

    return {
        'trip_id': trip_id,
        'destination': trip.get('trp_destination'),
        'travel_style': travel_style,
        'total_potential_savings': total_potential_savings,
        'formatted_total_savings': f"{sym}{total_potential_savings:,.2f}",
        'rebalancing_advice': rebalancing_advice,
        'recommendations_count': len(recommendations),
        'recommendations': recommendations,
    }
