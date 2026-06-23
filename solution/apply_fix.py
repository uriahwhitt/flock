"""Oracle fix for flock-pay-ledger.

Four independent conservation violations across four services; all four must be
fixed for the ledger to balance. Each fix enforces the conservation invariant at
its source.
"""
import re


def patch_function(path, func_name, new_src):
    s = open(path).read()
    pat = re.compile(r"def " + re.escape(func_name) + r"\(.*?(?=\ndef |\Z)", re.DOTALL)
    m = pat.search(s)
    assert m, f"{func_name} not found in {path}"
    s = s[:m.start()] + new_src + s[m.end():]
    open(path, "w").write(s)


# Fix 1: capture must not refund the payer, and only a held hold may capture.
patch_function("/app/services/capture.py", "capture", '''def capture(hold_id, payee_id):
    """Capture a hold to a payee. Returns True on success."""
    hold = Hold.query.get(hold_id)
    if hold is None or hold.state != 'held':
        return False
    hold.payee_id = payee_id
    hold.state = 'captured'
    db.session.commit()
    return True
''')

# Fix 2: settlement state guard — a hold may be settled once.
patch_function("/app/services/settlement.py", "settle", '''def settle(hold_id, payee_id, fee=0):
    """Settle a captured hold: write ledger entries and a Transaction row."""
    hold = Hold.query.get(hold_id)
    if hold is None or hold.state == 'settled':
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
''')

# Fix 3: fee symmetry — both sides use the same rounding.
patch_function("/app/services/fees.py", "payee_fee", '''def payee_fee(amount):
    """Fee deducted from the payee's received amount."""
    return int(amount * FEE_RATE)
''')

# Fix 4: refund credits the payer exactly once (on ack), with a state guard.
patch_function("/app/services/refunds.py", "request_refund", '''def request_refund(txn_id):
    """Payor initiates a refund for a settled transaction. Returns the Refund."""
    txn = Transaction.query.get(txn_id)
    if txn is None or txn.state != 'settled':
        return None
    refund = Refund(txn_id=txn_id, amount=txn.amount, state='pending')
    db.session.add(refund)
    db.session.commit()
    return refund
''')

patch_function("/app/services/refunds.py", "ack_refund", '''def ack_refund(refund_id):
    """Payee acknowledges the refund, finalizing the reversal."""
    refund = Refund.query.get(refund_id)
    if refund is None or refund.state != 'pending':
        return False
    txn = Transaction.query.get(refund.txn_id)
    payee = CreditAccount.for_user(txn.payee_id)
    payer = CreditAccount.for_user(txn.payer_id)
    payee.balance -= refund.amount
    payer.balance += refund.amount
    refund.state = 'completed'
    txn.state = 'refunded'
    db.session.commit()
    return True
''')

print("Applied flock-pay oracle fix (4 services)")
