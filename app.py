"""
app.py
------
Flask REST API for the Advanced FAQ Chatbot.

Endpoints:
  GET  /                    → chat UI
  GET  /analytics           → analytics dashboard
  POST /chat                → main chat endpoint
  GET  /history/<session>   → conversation history
  POST /feedback            → thumbs up/down on an answer
  POST /clear/<session>     → clear conversation memory
  GET  /api/categories      → list all FAQ categories
  GET  /api/analytics       → analytics JSON
"""

import uuid
from dotenv import load_dotenv
import os
import re
from flask import Flask, request, jsonify, render_template, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from database   import init_db, get_categories, record_feedback, get_analytics, \
                       save_session, get_all_sessions, get_session_messages, delete_session
from nlp_engine import AdvancedFAQEngine

load_dotenv()

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_dev_only")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)  # needed for session cookies

print("[App] Initialising database...")
init_db()

print("[App] Loading NLP engine...")
engine = AdvancedFAQEngine()


# ── Helper ────────────────────────────────────────────────────────────────────
def get_session_id(custom_sid: str = None) -> str:
    """Frontend sid ko priority do, fallback Flask session pe."""
    if custom_sid:
        session["sid"] = custom_sid  # sync kar do dono ko
        return custom_sid
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    categories = get_categories()
    return render_template("index.html", categories=categories)


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    data     = request.get_json(force=True)
    message  = data.get("message", "").strip()
    category = data.get("category") or None
    custom_sid = data.get("session_id") or None

    # Input sanitization
    message = re.sub(r'[<>{}\[\]\\]', '', message)  # harmful chars remove
    message = message[:500]  # max 500 characters

    if not message:
        return jsonify({"error": "Empty message"}), 400

    sid = get_session_id(custom_sid)
    result = engine.get_answer(message, session_id=sid, category_filter=category)
    print(f"[DEBUG] sid={sid}, custom={custom_sid}")
    return jsonify(result)


@app.route("/history/<session_id>", methods=["GET"])
def history(session_id):
    turns = engine.get_history(session_id)
    return jsonify({"session_id": session_id, "turns": turns})


@app.route("/feedback", methods=["POST"])
def feedback():
    """Body: { "faq_id": int, "helpful": bool }"""
    data    = request.get_json(force=True)
    faq_id  = data.get("faq_id")
    helpful = data.get("helpful", True)

    if faq_id is None:
        return jsonify({"error": "faq_id required"}), 400

    record_feedback(faq_id, helpful)
    return jsonify({"status": "recorded"})


@app.route("/clear/<session_id>", methods=["POST"])
def clear_session(session_id):
    engine.clear_session(session_id)
    return jsonify({"status": "cleared"})


@app.route("/api/sessions", methods=["GET"])
def api_sessions():
    return jsonify({"sessions": get_all_sessions()})


@app.route("/api/sessions", methods=["POST"])
def api_save_session():
    data  = request.get_json(force=True)
    sid   = data.get("session_id","")
    title = data.get("title","New Chat")
    if sid:
        save_session(sid, title)
    return jsonify({"status": "saved"})

@app.route("/api/sessions/<session_id>", methods=["GET"])
def api_session_messages(session_id):
    messages = get_session_messages(session_id)
    return jsonify({"session_id": session_id, "messages": messages})


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def api_delete_session(session_id):
    delete_session(session_id)
    return jsonify({"status": "deleted"})


@app.route("/api/categories", methods=["GET"])
def api_categories():
    return jsonify({"categories": get_categories()})


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    return jsonify(get_analytics())


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Advanced Govt FAQ Chatbot")
    print("  Chat UI  →  http://127.0.0.1:5000")
    print("  Analytics → http://127.0.0.1:5000/analytics")
    print("="*50 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
