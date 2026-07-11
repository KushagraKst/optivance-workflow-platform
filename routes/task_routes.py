from flask import Blueprint, request, jsonify

import sqlite3

task_bp = Blueprint('task', __name__)


def _conn():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    return conn


# ── GET /tasks ─────────────────────────────────
@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    user_id = request.args.get("user_id")
    user_role = request.args.get("user_role")
    team_id = request.args.get("team_id")
    
    if not user_id:
        return jsonify({"message": "user_id required"}), 400

    conn = _conn()
    cur  = conn.cursor()
    
    if user_role == 'app_admin':
        cur.execute("SELECT t.id, t.title, t.status, t.priority, t.due_date, u.name as assignee FROM tasks t LEFT JOIN users u ON t.assigned_to = u.id ORDER BY t.due_date ASC")
    elif user_role == 'team_leader':
        cur.execute("SELECT t.id, t.title, t.status, t.priority, t.due_date, u.name as assignee FROM tasks t LEFT JOIN users u ON t.assigned_to = u.id WHERE t.team_id = ? ORDER BY t.due_date ASC", (team_id,))
    else:
        # team_member
        cur.execute("SELECT t.id, t.title, t.status, t.priority, t.due_date, u.name as assignee FROM tasks t LEFT JOIN users u ON t.assigned_to = u.id WHERE t.assigned_to = ? ORDER BY t.due_date ASC", (user_id,))
        
    rows = cur.fetchall()
    conn.close()

    return jsonify([
        {"id": r["id"], "title": r["title"], "status": r["status"],
         "priority": r["priority"] or "medium", "due_date": r["due_date"], "assignee": r["assignee"] or "Unassigned"}
        for r in rows
    ])


# ── POST /tasks/create ─────────────────────────
@task_bp.route('/tasks/create', methods=['POST'])
def create_task():
    data     = request.json or {}
    user_id  = data.get("user_id")
    user_role = data.get("user_role")
    team_id  = data.get("team_id")
    if team_id in (None, "", "None"):
        team_id = None
    assigned_to = data.get("assigned_to")
    if assigned_to in (None, "", "None"):
        assigned_to = None
    title    = (data.get("title") or "").strip()
    status   = data.get("status", "todo")
    priority = data.get("priority", "medium")
    due_date = data.get("due_date", "")

    if user_role != 'team_leader' and user_role != 'app_admin':
        return jsonify({"error": "Only team leaders can assign tasks"}), 403

    if not user_id or not title:
        return jsonify({"error": "user_id and title are required"}), 400

    conn = _conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (team_id, assigned_by, assigned_to, title, status, priority, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (team_id, user_id, assigned_to or None, title, status, priority, due_date or None)
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()

    return jsonify({"message": "Task created", "id": task_id}), 201


# ── PATCH /tasks/<id>/status ───────────────────
@task_bp.route('/tasks/<int:task_id>/status', methods=['PATCH'])
def update_task_status(task_id):
    data    = request.json or {}
    status  = data.get("status", "done")
    user_id = data.get("user_id")

    conn = _conn()
    cur  = conn.cursor()

    cur.execute("SELECT assigned_to, team_id FROM tasks WHERE id = ?", (task_id,))
    task = cur.fetchone()

    if not task:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    cur.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    
    is_authorized = (str(task['assigned_to']) == str(user_id)) or (user and user['role'] in ('team_leader', 'app_admin'))

    if not is_authorized:
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403

    # Let anyone assigned to it or the leader update the status
    cur.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (status, task_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Task {task_id} updated to '{status}'"})


# ── DELETE /tasks/<id> ─────────────────────────
@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user_id = request.args.get("user_id")
    user_role = request.args.get("user_role")
    
    if user_role != 'team_leader' and user_role != 'app_admin':
        return jsonify({"error": "Unauthorized"}), 403

    conn = _conn()
    cur  = conn.cursor()
    cur.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Task {task_id} deleted"})