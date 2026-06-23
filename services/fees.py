"""Fee computation for platform transactions.

The platform takes a 2.9% fee on each settled transaction. The payer's side and
the payee's side each compute the fee for their own bookkeeping.
"""

FEE_RATE = 0.029


def payer_fee(amount):
    """Fee charged to the platform ledger from the payer side."""
    return int(amount * FEE_RATE)


def payee_fee(amount):
    """Fee deducted from the payee's received amount."""
    return round(amount * FEE_RATE)


def net_to_payee(amount):
    """Amount the payee receives after the platform fee."""
    return amount - payee_fee(amount)
