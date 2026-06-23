"""Verifier for flock-pay-ledger. Conservation-based, behavioral.

The invariant: sum(all account balances) + sum(open hold amounts) is constant
except through explicit issuance. Each test drives the live service flow and
asserts the invariant holds afterward. Four independent flaws each break it;
fixing any subset < 4 leaves at least one test red.
"""
import importlib
import os
import sys
import tempfile

APP_DIR = os.environ.get("APP_DIR", "/app")


def _purge():
    for name in list(sys.modules):
        if name.split(".")[0] in {
            "app", "config", "database", "models", "routes", "utils", "services"
        }:
            del sys.modules[name]


def _fresh():
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, "flock.db")
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    _purge()
    import config as cfg
    cfg.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    mod = importlib.import_module("app")
    importlib.reload(mod)
    with mod.app.app_context():
        from database import db
        db.create_all()
    return mod.app


def _seed(app, balances):
    """balances: dict user_id -> starting credits. Returns total issued."""
    with app.app_context():
        from database import db
        from models.ledger import CreditAccount
        total = 0
        for uid, bal in balances.items():
            db.session.add(CreditAccount(user_id=uid, balance=bal))
            total += bal
        db.session.commit()
        return total


def _total(app):
    with app.app_context():
        from models.ledger import CreditAccount, Hold
        bal = sum(a.balance for a in CreditAccount.query.all())
        held = sum(h.amount for h in Hold.query.filter(Hold.state.in_(('held','captured'))).all())
        return bal + held


# ---------- conservation under each flaw ----------

def test_capture_conserves():
    """Flaw 1: capturing a hold must not return funds to the payer."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100, 2: 0})
    with app.app_context():
        from services.authorization import authorize
        from services.capture import capture
        from services.settlement import settle
        h = authorize(1, 30)
        capture(h.id, 2)
        settle(h.id, 2)
    assert _total(app) == issued, \
        f"capture changed total: {_total(app)} != {issued}"


def test_settlement_no_reuse_conserves():
    """Flaw 2: a hold settled twice (reuse) must not create credits."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100, 2: 0, 3: 0})
    with app.app_context():
        from services.authorization import authorize
        from services.capture import capture
        from services.settlement import settle
        h = authorize(1, 40)
        capture(h.id, 2)
        settle(h.id, 2)
        settle(h.id, 3)           # reuse to a second payee
    assert _total(app) == issued, \
        f"hold reuse changed total: {_total(app)} != {issued}"


def test_fee_rounding_conserves():
    """Flaw 3: platform fee math must not create/destroy credits."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100000, 2: 0})
    with app.app_context():
        from services.fees import payer_fee, payee_fee
        # the two sides must agree for every amount, else conservation leaks
        for amt in (101, 103, 107, 109, 111, 113, 127):
            assert payer_fee(amt) == payee_fee(amt), \
                f"fee asymmetry at amount {amt}: payer={payer_fee(amt)} payee={payee_fee(amt)}"


def test_refund_conserves():
    """Flaw 4: a completed refund must return exactly the settled amount."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100, 2: 0})
    with app.app_context():
        from services.authorization import authorize
        from services.capture import capture
        from services.settlement import settle
        from services.refunds import request_refund, ack_refund
        h = authorize(1, 40)
        capture(h.id, 2)
        txn = settle(h.id, 2)
        rid = request_refund(txn.id)
        ack_refund(rid.id)
    assert _total(app) == issued, \
        f"refund changed total: {_total(app)} != {issued}"


# ---------- benign-path assertions ----------

def test_normal_payment_settles():
    """A single clean payment settles and conserves."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100, 2: 0})
    with app.app_context():
        from services.authorization import authorize
        from services.capture import capture
        from services.settlement import settle
        from models.ledger import CreditAccount
        h = authorize(1, 25)
        capture(h.id, 2)
        settle(h.id, 2)
        payee = CreditAccount.query.filter_by(user_id=2).first()
        assert payee.balance == 25, f"payee not credited correctly: {payee.balance}"
    assert _total(app) == issued


def test_normal_refund_restores():
    """A clean refund restores the payer to their pre-payment balance."""
    app = _fresh()
    issued = _seed(app, {0: 0, 1: 100, 2: 0})
    with app.app_context():
        from services.authorization import authorize
        from services.capture import capture
        from services.settlement import settle
        from services.refunds import request_refund, ack_refund
        from models.ledger import CreditAccount
        h = authorize(1, 40)
        capture(h.id, 2)
        txn = settle(h.id, 2)
        rid = request_refund(txn.id)
        ack_refund(rid.id)
        payer = CreditAccount.query.filter_by(user_id=1).first()
        assert payer.balance == 100, f"payer not restored: {payer.balance}"
    assert _total(app) == issued
