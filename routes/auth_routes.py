from flask import Blueprint, request, jsonify
import sqlite3

auth_bp = Blueprint('auth', __name__)

# SIGNUP
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data['email']
    password = data['password']

    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        return jsonify({"message": "User created"})
    except:
        return jsonify({"message": "User already exists"})
    finally:
        conn.close()

# LOGIN
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    conn = sqlite3.connect('database/optivance.db')
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
    user = cur.fetchone()

    conn.close()

    if user:
        return jsonify({"message": "Login success", "user_id": user[0]})
    else:
        return jsonify({"message": "Invalid credentials"})