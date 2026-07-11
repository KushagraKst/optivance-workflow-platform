from flask import Flask, render_template, request, redirect, url_for, session

# CREATE APP FIRST (VERY IMPORTANT)
app = Flask(__name__)
app.secret_key = 'super_secret_premium_key'

# IMPORT ROUTES AFTER APP (safe order)
from routes.data_routes import data_bp
from routes.task_routes import task_bp
from routes.team_routes import team_bp
from routes.user_routes import user_bp

app.register_blueprint(data_bp)
app.register_blueprint(task_bp)
app.register_blueprint(team_bp)
app.register_blueprint(user_bp)

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    return conn

# AUTHENTICATION & DASHBOARD
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    token = request.args.get('token')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            error = 'Email already registered. Please log in.'
        else:
            if token:
                # Handle invite signup
                cur.execute("SELECT company_id, team_id, is_used FROM invites WHERE token = ?", (token,))
                invite = cur.fetchone()
                if invite and not invite['is_used']:
                    cur.execute("INSERT INTO users (name, email, password, role, company_id, team_id) VALUES (?, ?, ?, 'team_member', ?, ?)", 
                                (name, email, password, invite['company_id'], invite['team_id']))
                    cur.execute("UPDATE invites SET is_used = 1 WHERE token = ?", (token,))
                    conn.commit()
                else:
                    error = 'Invalid or expired invite token.'
            else:
                # Handle team leader signup
                company_name = request.form.get('company_name')
                team_name = request.form.get('team_name')
                
                if not company_name or not team_name:
                    error = 'Company and Team names are required for new registration.'
                else:
                    # Create company
                    cur.execute("INSERT INTO companies (name) VALUES (?)", (company_name,))
                    company_id = cur.lastrowid
                    
                    # Create team
                    cur.execute("INSERT INTO teams (company_id, name) VALUES (?, ?)", (company_id, team_name))
                    team_id = cur.lastrowid
                    
                    # Create user
                    cur.execute("INSERT INTO users (name, email, password, role, company_id, team_id) VALUES (?, ?, ?, 'team_leader', ?, ?)", 
                                (name, email, password, company_id, team_id))
                    user_id = cur.lastrowid
                    
                    # Update team with leader_id
                    cur.execute("UPDATE teams SET leader_id = ? WHERE id = ?", (user_id, team_id))
                    conn.commit()

            if not error:
                cur.execute("SELECT id, name, email, role, company_id, team_id FROM users WHERE email = ?", (email,))
                user = cur.fetchone()
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['user_role'] = user['role']
                session['company_id'] = user['company_id']
                session['team_id'] = user['team_id']
                conn.close()
                return redirect(url_for('dashboard'))
        
        conn.close()
    return render_template('signup.html', error=error, token=token)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, role, company_id, team_id FROM users WHERE email = ? AND password = ?", (email, password))
        user = cur.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['company_id'] = user['company_id']
            session['team_id'] = user['team_id']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    session.pop('team_id', None)
    return redirect(url_for('login'))

from services.decision_service import get_decision, get_analytics, _fetch_tasks

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('index.html', user_email=session.get('user_email'), user_id=session.get('user_id'))

@app.route('/analytics_view')
def analytics_view():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('analytics.html', user_email=session.get('user_email'), user_id=session.get('user_id'))

@app.route('/decisions')
def decisions():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    uid = session.get('user_id')
    analytics = get_analytics(uid)
    decision  = get_decision(uid)
    tasks     = _fetch_tasks(uid)
    return render_template('decisions.html',
                           user_email=session.get('user_email'),
                           user_id=uid,
                           analytics=analytics,
                           decision=decision,
                           tasks=tasks)

@app.route('/team_view')
def team_view():
    if not session.get('user_id') or session.get('user_role') not in ['team_leader', 'app_admin']:
        return redirect(url_for('dashboard'))
    return render_template('team.html', user_email=session.get('user_email'), user_id=session.get('user_id'))
@app.route('/data_view')
def data_view():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('data.html', user_email=session.get('user_email'), user_id=session.get('user_id'))

@app.route('/tasks_view')
def tasks_view():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('tasks.html', user_email=session.get('user_email'), user_id=session.get('user_id'))



@app.route('/api/assistant/ask', methods=['POST'])
def assistant_ask():
    from flask import jsonify as jf
    if not session.get('user_id'):
        return jf({"error": "Not authenticated"}), 401
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jf({"error": "No question provided"}), 400
    from services.assistant_service import ask
    answer = ask(session['user_id'], question)
    return jf({"answer": answer})

@app.route('/assistant_view')
def assistant_view():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('assistant.html', user_email=session.get('user_email'), user_id=session.get('user_id'))

@app.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# AUTOMATION
from apscheduler.schedulers.background import BackgroundScheduler
from services.automation_service import check_overdue_tasks

scheduler = BackgroundScheduler()
scheduler.add_job(check_overdue_tasks, 'interval', days=1)
scheduler.start()

# RUN
if __name__ == '__main__':
    app.run(debug=True)