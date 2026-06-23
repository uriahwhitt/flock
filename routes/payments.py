import logging
from flask import Blueprint, request, jsonify

from database import db
from utils.auth import login_required, get_current_user
from models.ledger import CreditAccount, Hold, Transaction, Refund
from services.authorization import authorize, void_hold
from services.capture import capture
from services.settlement import settle
from services.fees import payer_fee, net_to_payee
from services.refunds import request_refund, ack_refund

logger = logging.getLogger(__name__)
payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/balance')
@login_required
def balance():
    user = get_current_user()
    acct = CreditAccount.for_user(user.id)
    return jsonify({'balance': acct.balance})


@payments_bp.route('/pay', methods=['POST'])
@login_required
def pay():
    """Full pay flow: authorize -> capture -> settle, applying platform fee."""
    user = get_current_user()
    payee_id = int(request.form.get('payee_id'))
    amount = int(request.form.get('amount'))

    hold = authorize(user.id, amount)
    if hold is None:
        return jsonify({'error': 'insufficient funds'}), 400

    capture(hold.id, payee_id)
    fee = payer_fee(amount)
    txn = settle(hold.id, payee_id, fee=fee)

    # platform takes its fee; payee receives net
    platform = CreditAccount.for_user(0)
    platform.balance += fee
    payee = CreditAccount.for_user(payee_id)
    # settle credited the gross amount; adjust payee down to net
    payee.balance -= (amount - net_to_payee(amount))
    db.session.commit()

    return jsonify({'transaction_id': txn.id, 'state': txn.state})


@payments_bp.route('/capture', methods=['POST'])
@login_required
def capture_endpoint():
    """Separate capture endpoint (used by the deferred-capture flow)."""
    hold_id = int(request.form.get('hold_id'))
    payee_id = int(request.form.get('payee_id'))
    ok = capture(hold_id, payee_id)
    return jsonify({'captured': ok})


@payments_bp.route('/settle', methods=['POST'])
@login_required
def settle_endpoint():
    hold_id = int(request.form.get('hold_id'))
    payee_id = int(request.form.get('payee_id'))
    txn = settle(hold_id, payee_id)
    return jsonify({'transaction_id': txn.id if txn else None})


@payments_bp.route('/refund/request', methods=['POST'])
@login_required
def refund_request_endpoint():
    txn_id = int(request.form.get('txn_id'))
    refund = request_refund(txn_id)
    if refund is None:
        return jsonify({'error': 'cannot refund'}), 400
    return jsonify({'refund_id': refund.id, 'state': refund.state})


@payments_bp.route('/refund/ack', methods=['POST'])
@login_required
def refund_ack_endpoint():
    refund_id = int(request.form.get('refund_id'))
    ok = ack_refund(refund_id)
    return jsonify({'completed': ok})
