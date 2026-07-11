"""
Optivance AI Assistant — rule-based intelligence layer.
Queries the user's real data (tasks, analytics, data_points) to answer questions.
No external API needed — runs entirely on local data.
"""

import sqlite3
import re
from services.decision_service import get_analytics, get_decision


def _conn():
    conn = sqlite3.connect('database/optivance.db')
    conn.row_factory = sqlite3.Row
    return conn


def _get_tasks(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, status, priority, due_date FROM tasks WHERE assigned_to = ? OR assigned_by = ? ORDER BY id DESC",
        (user_id, user_id)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _get_team_info(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT role, team_id, company_id FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None

    info = dict(user)

    if user['team_id']:
        cur.execute("SELECT name FROM teams WHERE id = ?", (user['team_id'],))
        team = cur.fetchone()
        info['team_name'] = team['name'] if team else 'Unknown'

        cur.execute("SELECT COUNT(*) as cnt FROM users WHERE team_id = ?", (user['team_id'],))
        info['team_size'] = cur.fetchone()['cnt']

    if user['company_id']:
        cur.execute("SELECT name FROM companies WHERE id = ?", (user['company_id'],))
        company = cur.fetchone()
        info['company_name'] = company['name'] if company else 'Unknown'

    conn.close()
    return info


def _get_data_summary(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM data_points WHERE user_id = ?", (user_id,))
    count = cur.fetchone()['cnt']
    conn.close()
    return count


def ask(user_id: int, question: str) -> str:
    """Process a user question and return an intelligent response."""
    q = question.lower().strip()

    # ── Task queries ──────────────────────────────────────
    if any(kw in q for kw in ['task', 'todo', 'assignment', 'assigned']):
        tasks = _get_tasks(user_id)
        if not tasks:
            return "You currently have **no tasks** assigned. If you're a Team Leader, go to the Tasks page to create and assign some!"

        total = len(tasks)
        by_status = {}
        by_priority = {}
        for t in tasks:
            s = t.get('status', 'unknown')
            p = t.get('priority', 'medium')
            by_status[s] = by_status.get(s, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1

        # Specific queries
        if 'in progress' in q or 'pending' in q:
            # Count pending tasks (status 'todo' or 'in-progress')
            pending = by_status.get('todo', 0) + by_status.get('in-progress', 0)
            return f"You have **{pending}** task(s) currently in progress or pending out of {total} total."

        if 'done' in q or 'completed' in q or 'complete' in q:
            # Count completed tasks (status 'done')
            done = by_status.get('done', 0)
            return f"You have **{done}** completed task(s) out of {total} total. {'Great progress! 🎉' if done > total//2 else 'Keep going! 💪'}"

        if 'high priority' in q or 'urgent' in q or 'critical' in q:
            high = [t for t in tasks if t.get('priority') == 'high']
            if high:
                names = ', '.join([f"**{t['title']}**" for t in high[:5]])
                return f"You have **{len(high)}** high priority task(s): {names}. {'⚠️ Focus on these first!' if len(high) > 2 else ''}"
            return "✅ No high priority tasks right now. You're in good shape!"

        if 'how many' in q or 'count' in q or 'total' in q:
            status_str = ', '.join([f"{v} {k}" for k, v in by_status.items()])
            return f"You have **{total}** task(s) total — {status_str}."

        if 'overdue' in q or 'late' in q:
            from datetime import date
            today = str(date.today())
            overdue = [t for t in tasks if t.get('due_date') and t['due_date'] < today and t.get('status') != 'done']
            if overdue:
                names = ', '.join([f"**{t['title']}** (due {t['due_date']})" for t in overdue[:5]])
                return f"⚠️ You have **{len(overdue)}** overdue task(s): {names}."
            return "✅ No overdue tasks! You're on track."

        # General task summary
        status_str = ', '.join([f"{v} {k}" for k, v in by_status.items()])
        priority_str = ', '.join([f"{v} {k}" for k, v in by_priority.items()])
        recent = tasks[:3]
        recent_str = '\n'.join([f"• **{t['title']}** — {t.get('status', '?')} ({t.get('priority', 'medium')} priority)" for t in recent])
        return f"📋 **Task Summary**\n\nTotal: **{total}** — {status_str}\nPriority breakdown: {priority_str}\n\nRecent tasks:\n{recent_str}"

    # ── Analytics queries ──────────────────────────────────
    if any(kw in q for kw in ['analytics', 'data', 'insight', 'metric', 'stat', 'performance', 'number', 'volume']):
        analytics = get_analytics(user_id)
        dp_count = _get_data_summary(user_id)

        if dp_count == 0:
            return "📊 You don't have any data points uploaded yet. Head to the **Data** page to add some, then your analytics will light up!"

        trend_emoji = '📈' if analytics['trend'] == 'increasing' else ('📉' if analytics['trend'] == 'decreasing' else '➡️')

        return (
            f"📊 **Analytics Summary**\n\n"
            f"• Data points: **{analytics['count']}**\n"
            f"• Total volume: **{analytics['total']}**\n"
            f"• Average: **{analytics['average']}**\n"
            f"• Range: **{analytics['min_value']}** – **{analytics['max_value']}**\n"
            f"• Trend: {trend_emoji} **{analytics['trend']}**\n"
            f"• Growth rate: **{analytics['growth_rate']}%**\n"
            f"• Latest change: **{analytics['change']:+}** ({analytics['previous_value']} → {analytics['latest_value']})"
        )

    # ── Decision queries ──────────────────────────────────
    if any(kw in q for kw in ['decision', 'predict', 'recommend', 'advice', 'suggest', 'forecast', 'what should']):
        decision = get_decision(user_id)

        action_emoji = '📈' if decision['action'] == 'increase' else ('📉' if decision['action'] == 'decrease' else '⏸️')

        response = (
            f"🧠 **AI Decision Engine**\n\n"
            f"Action: {action_emoji} **{decision['action'].upper()}**\n"
            f"Confidence: **{decision['confidence'].title()}**\n"
            f"Reason: {decision['reason']}\n"
        )
        if decision.get('predicted_next') is not None:
            response += f"Predicted next value: **{decision['predicted_next']}**\n"
        response += f"Growth rate: **{decision['growth_rate']}%**"
        return response

    # ── Team queries ──────────────────────────────────────
    if any(kw in q for kw in ['team', 'member', 'company', 'role', 'who am i', 'my role']):
        info = _get_team_info(user_id)
        if not info:
            return "I couldn't find your profile information. Please try logging in again."

        role_display = info.get('role', 'user').replace('_', ' ').title()
        parts = [f"👤 **Your Profile**\n", f"• Role: **{role_display}**"]

        if info.get('company_name'):
            parts.append(f"• Company: **{info['company_name']}**")
        if info.get('team_name'):
            parts.append(f"• Team: **{info['team_name']}**")
        if info.get('team_size'):
            parts.append(f"• Team size: **{info['team_size']}** member(s)")

        if info.get('role') == 'team_leader':
            parts.append("\n💡 As a Team Leader, you can assign tasks, generate invite links, and monitor team productivity.")
        elif info.get('role') == 'app_admin':
            parts.append("\n💡 As App Admin, you have full platform access and can monitor all activity.")
        else:
            parts.append("\n💡 As a Team Member, you can view and work on tasks assigned to you by your Team Leader.")

        return '\n'.join(parts)

    # ── Productivity tips ──────────────────────────────────
    if any(kw in q for kw in ['productivity', 'improve', 'efficient', 'better', 'optimize', 'tip']):
        tasks = _get_tasks(user_id)
        tips = [
            "🚀 **Productivity Tips**\n",
            "1. **Prioritize ruthlessly** — Focus on high-priority tasks first. Use the priority filter on your Tasks page.",
            "2. **Track your data** — Upload data points regularly on the Data page to get better analytics and predictions.",
            "3. **Check the Decision Engine** — Visit the Decisions page for AI-powered recommendations based on your trends.",
            "4. **Review analytics weekly** — The Analytics page shows your growth patterns and can reveal bottlenecks.",
        ]
        if tasks:
            pending = [t for t in tasks if t.get('status') in ('pending', 'in_progress')]
            if len(pending) > 5:
                tips.append(f"\n⚠️ You currently have {len(pending)} pending tasks — consider breaking them down or delegating some.")
            high = [t for t in tasks if t.get('priority') == 'high']
            if high:
                tips.append(f"\n🔴 You have {len(high)} high priority task(s) — tackle these first!")
        return '\n'.join(tips)

    # ── Help / How-to ──────────────────────────────────────
    if any(kw in q for kw in ['help', 'how to', 'how do', 'what can', 'guide', 'tutorial']):
        return (
            "📚 **Optivance Guide**\n\n"
            "Here's what you can do on the platform:\n\n"
            "• **Dashboard** — Your overview hub with quick access cards and live insights.\n"
            "• **Tasks** — Create, assign, and track tasks. Team Leaders can assign to members.\n"
            "• **Data** — Upload numerical data points for analytics processing.\n"
            "• **Analytics** — View computed metrics, trends, growth rates, and sparkline charts from your data.\n"
            "• **Decisions** — Get AI-powered recommendations based on your data trends.\n"
            "• **Team** — (Leaders only) Generate invite links and manage team members.\n"
            "• **AI Assistant** — That's me! Ask me anything about your data, tasks, or the platform.\n\n"
            "💡 Try asking me: *How many tasks do I have?* or *What's my analytics summary?*"
        )

    # ── Greeting ──────────────────────────────────────────
    if any(kw in q for kw in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'sup', 'yo']):
        return "Hey there! 👋 I'm your Optivance AI assistant. I can help with tasks, analytics, decisions, and more. What would you like to know?"

    # ── Workflow query (legacy) ────────────────────────────
    if 'workflow' in q:
        return (
            "🔄 **Workflows**\n\n"
            "The Optivance workflow system is built around the task lifecycle:\n\n"
            "1. **Team Leader** creates and assigns tasks with priorities and deadlines\n"
            "2. **Team Members** work on assigned tasks and update their status\n"
            "3. **Analytics** automatically tracks your data trends\n"
            "4. **Decision Engine** provides AI recommendations based on patterns\n\n"
            "This creates a continuous feedback loop: assign → execute → measure → optimize."
        )

    # ── Fallback ──────────────────────────────────────────
    return (
        "🤔 I'm not sure I understand that question. Here are some things you can ask me:\n\n"
        "• **\"How many tasks do I have?\"** — Task overview\n"
        "• **\"Show high priority tasks\"** — Filter by priority\n"
        "• **\"What's my analytics summary?\"** — Data insights\n"
        "• **\"What does the AI recommend?\"** — Decision engine output\n"
        "• **\"Tell me about my team\"** — Team & role info\n"
        "• **\"How to improve productivity?\"** — Tips & advice\n"
        "• **\"Help\"** — Platform guide\n\n"
        "💡 Try rephrasing your question or use one of the quick questions on the right!"
    )
