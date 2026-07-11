from flask import Blueprint, request, jsonify
import sqlite3

analytics_bp = Blueprint('analytics', __name__)


# ─────────────────────────────────────────────
# Helper: compute analytics from data_points
# ─────────────────────────────────────────────
def compute_analytics(user_id):
    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    cur.execute(
        "SELECT value FROM data_points WHERE user_id = ? ORDER BY date ASC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()

    values = [r[0] for r in rows]

    if not values:
        return {
            "total": 0, "average": 0, "count": 0,
            "trend": "no data", "growth_rate": 0,
            "max_value": 0, "min_value": 0,
            "latest_value": 0, "previous_value": 0, "change": 0,
            "series": []
        }

    total   = sum(values)
    count   = len(values)
    average = round(total / count, 2) if count else 0
    max_val = max(values)
    min_val = min(values)
    latest  = values[-1]
    prev    = values[-2] if count >= 2 else latest
    change  = latest - prev

    # Trend detection
    if count >= 2:
        first_half = sum(values[:count // 2]) / max(len(values[:count // 2]), 1)
        second_half = sum(values[count // 2:]) / max(len(values[count // 2:]), 1)
        if second_half > first_half * 1.05:
            trend = "increasing"
        elif second_half < first_half * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    # Growth rate
    growth_rate = round(((latest - values[0]) / values[0]) * 100, 2) if values[0] != 0 else 0

    return {
        "total": total,
        "average": average,
        "count": count,
        "trend": trend,
        "growth_rate": growth_rate,
        "max_value": max_val,
        "min_value": min_val,
        "latest_value": latest,
        "previous_value": prev,
        "change": change,
        "series": values
    }


# ─────────────────────────────────────────────
# GET /analytics?user_id=<id>
# ─────────────────────────────────────────────
@analytics_bp.route('/analytics', methods=['GET'])
def analytics():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    result = compute_analytics(int(user_id))
    # Remove internal series from API response
    result.pop("series", None)
    return jsonify(result)


# ─────────────────────────────────────────────
# GET /analytics/series?user_id=<id>
# ─────────────────────────────────────────────
@analytics_bp.route('/analytics/series', methods=['GET'])
def analytics_series():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    result = compute_analytics(int(user_id))
    return jsonify({"series": result.get("series", [])})


# ─────────────────────────────────────────────
# GET /decide?user_id=<id>
# ─────────────────────────────────────────────
@analytics_bp.route('/decide', methods=['GET'])
def decide():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    from services.decision_service import get_decision
    decision = get_decision(int(user_id))
    return jsonify(decision)
