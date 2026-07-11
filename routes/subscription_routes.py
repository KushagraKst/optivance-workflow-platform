from flask import Blueprint, request, jsonify, session
from services.subscription_service import create_subscription, get_subscription, is_subscription_valid

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/subscription', methods=['GET'])
def get_subscription_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    sub = get_subscription(user_id)
    plan = sub.get('tier') if sub else 'free'
    active = is_subscription_valid(user_id)
    return jsonify({"plan": plan, "active": bool(active)})

@subscription_bp.route('/subscription/checkout', methods=['POST'])
def checkout():
    # For now, mock checkout: automatically create a 'pro' subscription for 30 days
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    # In real implementation, here you'd integrate with Stripe/PayPal and get payment confirmation.
    create_subscription(user_id, tier='pro', duration_days=30)
    return jsonify({"message": "Subscription upgraded to pro for 30 days"})
