import sqlite3
import datetime
from functools import wraps
from flask import request, jsonify

# Helper to get DB connection
def _conn():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_subscription(user_id: int, tier: str, duration_days: int = 30, status: str = 'active') -> dict:
    """Create a new subscription record.

    Args:
        user_id: ID of the user.
        tier: Subscription tier name (e.g., 'free', 'pro').
        duration_days: Length of the subscription in days.
        status: 'active' or 'inactive'.
    Returns:
        Dict representing the created subscription.
    """
    start_date = datetime.date.today().isoformat()
    end_date = (datetime.date.today() + datetime.timedelta(days=duration_days)).isoformat() if duration_days else None
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO subscriptions (user_id, tier, start_date, end_date, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, tier, start_date, end_date, status)
    )
    conn.commit()
    sub_id = cur.lastrowid
    conn.close()
    return {
        "id": sub_id,
        "user_id": user_id,
        "tier": tier,
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
    }

def get_subscription(user_id: int) -> dict | None:
    """Fetch the latest subscription for a user, if any."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def is_subscription_valid(user_id: int, required_tier: str = 'free') -> bool:
    """Check if the user has a valid subscription for the required tier.

    The 'free' tier always passes. For paid tiers, the subscription must be active
    and the tier must be equal or higher (e.g., 'pro' >= 'free').
    """
    if required_tier == 'free':
        return True
    sub = get_subscription(user_id)
    if not sub:
        return False
    if sub.get('status') != 'active':
        return False
    hierarchy = ['free', 'pro', 'premium']
    try:
        user_index = hierarchy.index(sub.get('tier'))
        required_index = hierarchy.index(required_tier)
    except ValueError:
        return False
    return user_index >= required_index

def require_subscription(tier: str = 'free'):
    """Flask decorator to protect routes based on subscription tier.

    Expects a 'user_id' query param or JSON field. Returns 403 if check fails.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = request.args.get('user_id')
            if not user_id and request.is_json:
                user_id = request.json.get('user_id')
            if not user_id:
                return jsonify({"error": "user_id required for subscription check"}), 400
            try:
                uid = int(user_id)
            except ValueError:
                return jsonify({"error": "invalid user_id"}), 400
            if not is_subscription_valid(uid, tier):
                return jsonify({"error": f"Insufficient subscription level. Required: {tier}"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator
