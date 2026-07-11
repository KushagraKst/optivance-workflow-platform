from flask import Blueprint, request, jsonify
import sqlite3

data_bp = Blueprint('data', __name__)

# UPLOAD DATA (USER-SPECIFIC)
@data_bp.route('/upload-data', methods=['POST'])
def upload_data():
    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    req = request.json

    user_id = req.get("user_id")
    data = req.get("data")

    # ❗ validation
    if not user_id or not data:
        return jsonify({"message": "user_id and data required"}), 400

    for item in data:
        cur.execute(
            "INSERT INTO data_points (user_id, value, date) VALUES (?, ?, ?)",
            (user_id, item['value'], item['date'])
        )

    conn.commit()
    conn.close()

    return jsonify({"message": "Data added for user", "user_id": user_id})


# GET DATA FOR A USER (OPTIONAL BUT USEFUL)
@data_bp.route('/get-data/<int:user_id>', methods=['GET'])
def get_data(user_id):
    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    cur.execute(
        "SELECT value, date FROM data_points WHERE user_id=?",
        (user_id,)
    )

    rows = cur.fetchall()
    conn.close()

    data = [{"value": r[0], "date": r[1]} for r in rows]

    return jsonify(data)