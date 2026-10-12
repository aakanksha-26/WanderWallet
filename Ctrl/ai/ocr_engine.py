"""OCR Engine — standalone module wrapping ai_routes extract logic."""
import re
from datetime import date

CATEGORY_KEYWORDS = {
    'food':          ['restaurant','cafe','food','dinner','lunch','breakfast','coffee','bar','grill'],
    'transport':     ['taxi','uber','cab','fuel','petrol','bus','train','flight','airline','metro'],
    'accommodation': ['hotel','resort','hostel','airbnb','inn','lodge','room'],
    'activities':    ['diving','tour','ticket','museum','spa','adventure','trekking','safari'],
    'shopping':      ['shop','mall','market','store','boutique','duty free','souvenir'],
    'health':        ['pharmacy','medical','clinic','hospital','medicine','doctor'],
}

def extract_from_text(text: str) -> dict:
    """Extract expense fields from raw OCR text."""
    text_lower = text.lower()
    result = {'merchant': None, 'amount': None, 'currency': 'INR', 'date': str(date.today()), 'category': 'misc'}

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines: result['merchant'] = lines[0][:60]

    for pattern in [
        r'(?:total|amount|grand total)[:\s]*[₹$€£]?\s*([\d,]+\.?\d*)',
        r'[₹$€£]\s*([\d,]+\.?\d*)',
        r'([\d,]+\.\d{2})',
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try: result['amount'] = float(m.group(1).replace(',','')); break
            except: pass

    for cur, syms in [('USD',['$','USD']),('EUR',['€','EUR']),('GBP',['£','GBP']),('THB',['฿','THB'])]:
        if any(s in text for s in syms): result['currency'] = cur; break

    for p in [r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'(\d{4}-\d{2}-\d{2})']:
        m = re.search(p, text)
        if m: result['date'] = m.group(1); break

    best = 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        n = sum(1 for k in kws if k in text_lower)
        if n > best: best = n; result['category'] = cat

    result['confidence'] = min(100.0, 20 + 30*bool(result['amount']) + 20*bool(result['merchant']) + 15*(result['date'] != str(date.today())) + 15*(best>0))
    return result
