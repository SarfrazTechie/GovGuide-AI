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
from flask import Flask, request, jsonify, render_template, session

from database   import init_db, get_categories, record_feedback, get_analytics, \
                       save_session, get_all_sessions, get_session_messages, delete_session
from nlp_engine import AdvancedFAQEngine

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "govt_faq_secret_2025"   # needed for session cookies

print("[App] Initialising database...")
init_db()

print("[App] Loading NLP engine...")
engine = AdvancedFAQEngine()


# ── Helper ────────────────────────────────────────────────────────────────────
def get_session_id() -> str:
    """Return or create a persistent session ID in the browser cookie."""
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
def chat():
    """
    Body: { "message": str, "category": str|null }
    Returns: { answer, category, matched_question, score, found,
               suggestions, corrected_query, faq_id }
    """
    data     = request.get_json(force=True)
    message  = data.get("message", "").strip()
    category = data.get("category") or None
    custom_sid = data.get("session_id") or None

    if not message:
        return jsonify({"error": "Empty message"}), 400

    sid = custom_sid if custom_sid else get_session_id()
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
