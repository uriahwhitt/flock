"""Capture layer: confirm an authorized hold.

Confirming a hold marks it captured and releases the reservation so the payer's
books reflect the completed authorization.
"""
from database import db
from models.ledger import CreditAccount, Hold


def capture(hold_id, payee_id):
    """Capture a hold to a payee. Returns True on success."""
    hold = Hold.query.get(hold_id)
    if hold is None:
        return False
    hold.payee_id = payee_id
    hold.state = 'captured'
    payer = CreditAccount.for_user(hold.payer_id)
    payer.balance += hold.amount
    db.session.commit()
    return True
