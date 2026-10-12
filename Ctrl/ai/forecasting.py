"""Spend Forecasting — standalone module."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

MONEY_DP = Decimal('0.01')

def forecast_spend(daily_data: list, start_date: str, end_date: str, total_budget: float) -> dict:
    """
    Recency-weighted burn rate forecasting.

    Args:
        daily_data: list of {date: str, total: float} sorted by date
        start_date: trip start date ISO string
        end_date: trip end date ISO string
        total_budget: total budget in home currency

    Returns dict with projected_total, burn_rate, risk, etc.
    """
    if not daily_data:
        return {'projected_total': 0, 'daily_burn_rate': 0, 'risk': 'unknown'}

    today = date.today()
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    trip_days = max(1, (end - start).days + 1)
    remaining_days = max(0, (end - today).days)
    budget = Decimal(str(total_budget))

    # Recency-weighted average
    weights_sum = Decimal('0')
    weighted_total = Decimal('0')
    for i, d in enumerate(daily_data):
        w = Decimal(str(i + 1))
        weighted_total += w * Decimal(str(d.get('total', d.get('day_total', 0))))
        weights_sum += w

    burn_rate = (weighted_total / weights_sum).quantize(MONEY_DP) if weights_sum else Decimal('0')
    total_spent = sum(Decimal(str(d.get('total', d.get('day_total', 0)))) for d in daily_data)
    projected_remaining = burn_rate * Decimal(str(remaining_days))
    projected_total = (total_spent + projected_remaining).quantize(MONEY_DP)
    overshoot = max(Decimal('0'), projected_total - budget)

    risk_pct = float((projected_total / budget) * 100) if budget > 0 else 0
    risk = 'critical' if risk_pct > 110 else 'high' if risk_pct > 95 else 'medium' if risk_pct > 80 else 'low'

    return {
        'burn_rate': float(burn_rate),
        'projected_total': float(projected_total),
        'projected_overshoot': float(overshoot),
        'risk': risk,
        'risk_pct': round(risk_pct, 1),
        'remaining_days': remaining_days,
    }
