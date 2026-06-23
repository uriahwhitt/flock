"""Refund flow: two-party reversal of a settled transaction.

The payor requests a refund; the payee acknowledges it. On completion the
credits return to the payer and are removed from the payee.
"""
from database import db
from models.ledger import CreditAccount, Transaction, Refund


def request_refund(txn_id):
    """Payor initiates a refund for a settled transaction. Returns the Refund."""
    txn = Transaction.query.get(txn_id)
    if txn is None or txn.state != 'settled':
        return None
    refund = Refund(txn_id=txn_id, amount=txn.amount, state='pending')
    db.session.add(refund)
    # Optimistically return the funds to the payer up front.
    payer = CreditAccount.for_user(txn.payer_id)
    payer.balance += txn.amount
    db.session.commit()
    return refund


def ack_refund(refund_id):
    """Payee acknowledges the refund, finalizing the reversal."""
    refund = Refund.query.get(refund_id)
    if refund is None:
        return False
    txn = Transaction.query.get(refund.txn_id)
    payee = CreditAccount.for_user(txn.payee_id)
    payer = CreditAccount.for_user(txn.payer_id)
    payee.balance -= refund.amount
    payer.balance += refund.amount      # payer credited AGAIN here
    refund.state = 'completed'
    txn.state = 'refunded'
    db.session.commit()
    return True
