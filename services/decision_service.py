import sqlite3


def _fetch_values(user_id: int):
    """Single DB call — returns list of values ordered by date ASC."""
    conn = sqlite3.connect('database/optivance.db')
    cur  = conn.cursor()
    cur.execute(
        "SELECT value FROM data_points WHERE user_id = ? ORDER BY date ASC",
        (user_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def _fetch_tasks(user_id: int):
    """Fetch tasks visible to the user (assigned to them or assigned by them)."""
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, status, priority, due_date FROM tasks WHERE assigned_to = ? OR assigned_by = ? ORDER BY id DESC",
        (user_id, user_id)
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _classify(growth_rate: float):
    """Map growth % → action + confidence."""
    if growth_rate > 15:
        return {"action": "increase", "confidence": "high",
                "reason": f"Strong growth ({growth_rate:.1f}%) — consider scaling operations."}
    elif growth_rate > 5:
        return {"action": "increase", "confidence": "moderate",
                "reason": f"Positive trend ({growth_rate:.1f}%) — a good time to invest."}
    elif growth_rate > -5:
        return {"action": "hold", "confidence": "stable",
                "reason": f"Flat trend ({growth_rate:.1f}%) — maintain current strategy."}
    elif growth_rate > -15:
        return {"action": "decrease", "confidence": "moderate",
                "reason": f"Declining trend ({growth_rate:.1f}%) — review and optimize."}
    else:
        return {"action": "decrease", "confidence": "high",
                "reason": f"Sharp decline ({growth_rate:.1f}%) — immediate action recommended."}


def get_analytics(user_id: int):
    """Compute analytics from data_points for the given user."""
    values = _fetch_values(user_id)

    if not values:
        return {
            "total": 0, "average": 0, "count": 0,
            "trend": "no data", "growth_rate": 0,
            "max_value": 0, "min_value": 0,
            "latest_value": 0, "previous_value": 0, "change": 0,
            "_series": []
        }

    total   = sum(values)
    count   = len(values)
    average = round(total / count, 2) if count else 0
    max_val = max(values)
    min_val = min(values)
    latest  = values[-1]
    prev    = values[-2] if count >= 2 else latest
    change  = latest - prev

    # Trend
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
        "_series": values
    }


def get_decision(user_id: int):
    """Combine analytics + linear prediction → actionable decision."""
    values = _fetch_values(user_id)

    if not values or len(values) < 2:
        return {
            "action": "hold",
            "confidence": "low",
            "reason": "Not enough data to make a prediction. Add more data points.",
            "predicted_next": None,
            "growth_rate": 0
        }

    # Simple linear prediction
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator   = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    predicted = round(slope * n + intercept, 2)

    # Growth rate
    growth_rate = round(((values[-1] - values[0]) / values[0]) * 100, 2) if values[0] != 0 else 0

    decision = _classify(growth_rate)
    decision["predicted_next"] = predicted
    decision["growth_rate"] = growth_rate

    return decision
