"""
Settlement Service — Minimize transactions using net balance algorithm.
Uses decimal.Decimal throughout (R3).
"""

from decimal import Decimal, ROUND_HALF_UP
from db.database import query_db, rows_to_list

MONEY_DP = Decimal('0.01')


def compute_settlement(trip_id: str) -> dict:
    """
    Calculate who owes whom for a trip.
    
    Algorithm:
    1. For each expense, compute each member's share.
    2. Calculate net balance: (amount paid) - (share owed).
    3. Use greedy creditor-debtor matching to minimize transactions.
    
    Returns dict with:
      - balances: per-user net balance
      - transactions: minimal list of {from, to, amount}
    """
    # Get all trip members
    members = rows_to_list(query_db(
        """SELECT u.usr_id, u.usr_name
           FROM trip_members tm
           JOIN users u ON u.usr_id = tm.tmb_user_id
           WHERE tm.tmb_trip_id = ? AND tm.status = 'active'""",
        (trip_id,)
    ))

    member_map = {m['usr_id']: m['usr_name'] for m in members}
    paid: dict[str, Decimal] = {m['usr_id']: Decimal('0.00') for m in members}
    owed: dict[str, Decimal] = {m['usr_id']: Decimal('0.00') for m in members}

    # Get expenses with splits
    expenses = rows_to_list(query_db(
        """SELECT exp_id, exp_payer_id, exp_home_amount
           FROM expenses
           WHERE exp_trip_id = ? AND status = 'active'""",
        (trip_id,)
    ))

    for exp in expenses:
        payer_id = exp['exp_payer_id']
        amount = Decimal(str(exp['exp_home_amount'])).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
        
        if payer_id in paid:
            paid[payer_id] += amount

        # Get splits for this expense
        splits = rows_to_list(query_db(
            """SELECT spl_user_id, spl_share_amount
               FROM expense_splits
               WHERE spl_expense_id = ? AND status = 'active'""",
            (exp['exp_id'],)
        ))

        if splits:
            for split in splits:
                uid = split['spl_user_id']
                share = Decimal(str(split['spl_share_amount'])).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
                if uid in owed:
                    owed[uid] += share
        else:
            # No splits recorded — assume equal split
            if members:
                per_person = (amount / Decimal(str(len(members)))).quantize(MONEY_DP, rounding=ROUND_HALF_UP)
                for m in members:
                    owed[m['usr_id']] += per_person

    # Net balance = paid - owed
    net: dict[str, Decimal] = {}
    for uid in member_map:
        net[uid] = (paid.get(uid, Decimal('0')) - owed.get(uid, Decimal('0'))).quantize(MONEY_DP)

    # Minimize transactions
    transactions = _minimize_transactions(net, member_map)

    return {
        'trip_id': trip_id,
        'balances': [
            {
                'user_id': uid,
                'user_name': member_map[uid],
                'paid': float(paid.get(uid, Decimal('0'))),
                'owed': float(owed.get(uid, Decimal('0'))),
                'net': float(net[uid]),
                'status': 'creditor' if net[uid] > 0 else ('debtor' if net[uid] < 0 else 'settled'),
            }
            for uid in member_map
        ],
        'transactions': transactions,
        'currency': _get_trip_currency(trip_id),
    }


def _minimize_transactions(net: dict[str, Decimal], member_map: dict) -> list:
    """Greedy algorithm: repeatedly match largest creditor with largest debtor."""
    creditors = sorted(
        [(uid, bal) for uid, bal in net.items() if bal > 0],
        key=lambda x: x[1], reverse=True
    )
    debtors = sorted(
        [(uid, -bal) for uid, bal in net.items() if bal < 0],
        key=lambda x: x[1], reverse=True
    )

    transactions = []
    creditors = list(creditors)
    debtors = list(debtors)
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        c_uid, c_bal = creditors[i]
        d_uid, d_bal = debtors[j]

        amount = min(c_bal, d_bal).quantize(MONEY_DP)
        if amount > Decimal('0.01'):
            transactions.append({
                'from_user_id': d_uid,
                'from_user_name': member_map[d_uid],
                'to_user_id': c_uid,
                'to_user_name': member_map[c_uid],
                'amount': float(amount),
            })

        if c_bal > d_bal:
            creditors[i] = (c_uid, (c_bal - d_bal).quantize(MONEY_DP))
            j += 1
        elif d_bal > c_bal:
            debtors[j] = (d_uid, (d_bal - c_bal).quantize(MONEY_DP))
            i += 1
        else:
            i += 1
            j += 1

    return transactions


def _get_trip_currency(trip_id: str) -> str:
    row = query_db(
        "SELECT trp_home_currency FROM trips WHERE trp_id = ?",
        (trip_id,), one=True
    )
    return row['trp_home_currency'] if row else 'INR'


# Module alias
calculate_settlement = compute_settlement

