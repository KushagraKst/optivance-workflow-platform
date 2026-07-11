from flask import Blueprint, request, jsonify
import sqlite3
import uuid

team_bp = Blueprint('team', __name__)

def _conn():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    return conn

# ── GET /team/members ─────────────────────────
@team_bp.route('/team/members', methods=['GET'])
def get_team_members():
    team_id = request.args.get("team_id")
    if not team_id:
        return jsonify({"message": "team_id required"}), 400

    conn = _conn()
    cur  = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM users WHERE team_id = ?", (team_id,))
    rows = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": r["id"], "name": r["name"], "email": r["email"], "role": r["role"]}
        for r in rows
    ])


# ── POST /team/invite ─────────────────────────
@team_bp.route('/team/invite', methods=['POST'])
def create_invite():
    data = request.json or {}
    company_id = data.get("company_id")
    team_id = data.get("team_id")
    user_role = data.get("user_role")

    if user_role != 'team_leader' and user_role != 'app_admin':
        return jsonify({"error": "Unauthorized"}), 403

    if not company_id or not team_id:
        return jsonify({"error": "company_id and team_id required"}), 400

    token = str(uuid.uuid4())

    conn = _conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO invites (token, company_id, team_id) VALUES (?, ?, ?)",
        (token, company_id, team_id)
    )
    conn.commit()
    conn.close()

    invite_url = f"/signup?token={token}"
    return jsonify({"message": "Invite generated", "url": invite_url}), 201
