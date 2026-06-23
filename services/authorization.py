"""Authorization layer: place a hold reserving payer funds.

A hold moves credits out of the payer's available balance into a reserved
state. The credits still exist in the system (counted as held) until the hold
is captured and settled, or voided.
"""
from database import db
from models.ledger import CreditAccount, Hold


def authorize(payer_id, amount):
    """Reserve `amount` from payer by opening a hold. Returns the Hold."""
    payer = CreditAccount.for_user(payer_id)
    if payer.balance < amount:
        return None
    payer.balance -= amount
    hold = Hold(payer_id=payer_id, amount=amount, state='held')
    db.session.add(hold)
    db.session.commit()
    return hold


def void_hold(hold_id):
    """Cancel an open hold and return reserved funds to the payer."""
    hold = Hold.query.get(hold_id)
    if hold is None or hold.state != 'held':
        return False
    payer = CreditAccount.for_user(hold.payer_id)
    payer.balance += hold.amount
    hold.state = 'void'
    db.session.commit()
    return True
