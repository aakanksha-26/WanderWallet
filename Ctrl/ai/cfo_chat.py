"""CFO Chat — standalone rule-based budget advisory engine."""
import re
from decimal import Decimal

def answer_budget_question(question: str, context: dict) -> dict:
    """
    Answer a budget question grounded in trip data.

    context keys: remaining, total_spent, total_budget, currency,
                  category_summary, breaches
    """
    q = question.lower()
    remaining = Decimal(str(context.get('remaining', 0)))
    spent = Decimal(str(context.get('total_spent', 0)))
    budget = Decimal(str(context.get('total_budget', 0)))
    cur = context.get('currency', 'INR')
    sym = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£'}.get(cur, cur + ' ')
    pct_used = float((spent / budget * 100)) if budget > 0 else 0

    if any(w in q for w in ['afford', 'can i', 'have enough']):
        m = re.search(r'[\d,]+(?:\.\d+)?', q)
        if m:
            ask = Decimal(m.group().replace(',',''))
            if remaining >= ask:
                return {'answer': f"✅ Yes! You have {sym}{remaining:,.2f} remaining — enough for {sym}{ask:,.2f}. Remaining after: {sym}{remaining - ask:,.2f}.", 'confidence': 0.92}
            else:
                return {'answer': f"⚠️ Short by {sym}{ask - remaining:,.2f}. Only {sym}{remaining:,.2f} left.", 'confidence': 0.92}

    if any(w in q for w in ['remaining', 'left', 'balance', 'how much']):
        return {'answer': f"💰 Spent {sym}{spent:,.2f} of {sym}{budget:,.2f} ({pct_used:.1f}%). Remaining: {sym}{remaining:,.2f}.", 'confidence': 0.98}

    breaches = context.get('breaches', [])
    if any(w in q for w in ['breach', 'alert', 'overspend', 'exceeded']):
        if breaches:
            return {'answer': f"🚨 {len(breaches)} alert(s): {breaches[0].get('message', '')}", 'confidence': 0.97}
        return {'answer': "✅ No budget breaches! All categories within caps.", 'confidence': 0.97}

    return {'answer': f"📊 {sym}{spent:,.2f} spent / {sym}{budget:,.2f} total ({pct_used:.1f}%). Remaining: {sym}{remaining:,.2f}.", 'confidence': 0.75}
