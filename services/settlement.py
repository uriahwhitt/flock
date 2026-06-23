"""Settlement layer: write durable ledger entries for a captured hold.

Settlement records the double-entry ledger rows (debit payer, credit payee) and
finalizes the transaction.
"""
from database import db
from models.ledger import CreditAccount, Hold, LedgerEntry, Transaction


def settle(hold_id, payee_id, fee=0):
    """Settle a captured hold: write ledger entries and a Transaction row."""
    hold = Hold.query.get(hold_id)
    if hold is None:
        return None

    payee = CreditAccount.for_user(payee_id)
    payee.balance += hold.amount

    txn = Transaction(
        payer_id=hold.payer_id,
        payee_id=payee_id,
        amount=hold.amount,
        fee=fee,
        state='settled',
        hold_id=hold.id,
    )
    db.session.add(txn)
    db.session.flush()

    db.session.add(LedgerEntry(account_id=hold.payer_id, direction='debit',
                               amount=hold.amount, txn_id=txn.id))
    db.session.add(LedgerEntry(account_id=payee_id, direction='credit',
                               amount=hold.amount, txn_id=txn.id))

    hold.state = 'settled'
    db.session.commit()
    return txn
