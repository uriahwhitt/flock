from datetime import datetime
from database import db


class CreditAccount(db.Model):
    __tablename__ = 'credit_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, unique=True)
    balance = db.Column(db.Integer, default=0, nullable=False)

    @classmethod
    def for_user(cls, user_id):
        acct = cls.query.filter_by(user_id=user_id).first()
        if acct is None:
            acct = cls(user_id=user_id, balance=0)
            db.session.add(acct)
            db.session.commit()
        return acct


class Hold(db.Model):
    __tablename__ = 'holds'
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, nullable=False)
    payee_id = db.Column(db.Integer)
    amount = db.Column(db.Integer, nullable=False)
    # held | captured | settled | void
    state = db.Column(db.String(20), default='held', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LedgerEntry(db.Model):
    __tablename__ = 'ledger_entries'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False)
    direction = db.Column(db.String(6), nullable=False)  # debit | credit
    amount = db.Column(db.Integer, nullable=False)
    txn_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, nullable=False)
    payee_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    fee = db.Column(db.Integer, default=0)
    # pending | settled | refunded
    state = db.Column(db.String(20), default='pending')
    hold_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Refund(db.Model):
    __tablename__ = 'refunds'
    id = db.Column(db.Integer, primary_key=True)
    txn_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    # pending | acked | completed
    state = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
