"""
database.py
-----------
SQLite database layer.
Tables: faqs, chat_logs, feedback, unanswered_queries
"""

import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables and seed FAQ data on first run."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS faqs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT    NOT NULL,
            question    TEXT    NOT NULL,
            answer      TEXT    NOT NULL,
            helpful_yes INTEGER DEFAULT 0,
            helpful_no  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chat_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT    NOT NULL,
            user_query   TEXT    NOT NULL,
            bot_answer   TEXT    NOT NULL,
            matched_faq  TEXT,
            score        REAL,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS unanswered_queries (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            query     TEXT    NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed FAQs only once
    c.execute("SELECT COUNT(*) FROM faqs")
    if c.fetchone()[0] == 0:
        _seed_faqs(c)

    conn.commit()
    conn.close()
    print("[DB] Initialized successfully.")


def _seed_faqs(cursor):
    faqs = [
        ("NADRA", "How to apply for a new CNIC?",
         "Visit your nearest NADRA Registration Center with birth certificate, parent's CNIC and proof of residence. Fill Form-4, submit biometrics and pay the fee. Normal delivery takes 30 days, urgent takes 7 days."),
        ("NADRA", "What documents are required for CNIC?",
         "Required: (1) Birth Certificate or Form-B, (2) Parent's CNIC, (3) Proof of residence (utility bill or domicile), (4) Two passport-size photographs. Married women also need nikah nama."),
        ("NADRA", "How to renew expired CNIC?",
         "Visit NADRA office with your old CNIC and fill renewal form. Fee: Normal Rs.750, Urgent Rs.1500, Executive Rs.3000. Online renewal available at id.nadra.gov.pk."),
        ("NADRA", "What is the CNIC fee?",
         "Normal delivery (30 days) = Rs.750, Urgent (7 days) = Rs.1500, Executive (2 days) = Rs.3000. Senior citizens above 60 get 50% discount."),
        ("NADRA", "How to get NICOP for overseas Pakistanis?",
         "NICOP can be applied at Pakistan missions abroad or online at id.nadra.gov.pk. Required: valid Pakistani passport, CNIC, and overseas residence proof. Fee varies by country."),

        ("Passport", "How to apply for a new Pakistani passport?",
         "Apply online at dgip.gov.pk or visit Passport Office. Required: original CNIC, photos, fee challan. Normal passport takes 30 days, urgent 7 days, executive 2 days."),
        ("Passport", "What is the passport fee in Pakistan?",
         "36-page normal (30 days) = Rs.3000, 72-page normal = Rs.5000. Urgent 36-page (7 days) = Rs.5000, 72-page = Rs.7500. Executive 36-page (2 days) = Rs.12000, 72-page = Rs.15000."),
        ("Passport", "How to renew Pakistani passport?",
         "Visit dgip.gov.pk or nearest passport office. Bring original old passport, CNIC, photos, and fee challan. Expired less than 2 years = straightforward renewal. Expired more = fresh application."),
        ("Passport", "How to track passport application status?",
         "Track your passport at dgip.gov.pk using your CNIC number. You can also call the helpline 051-9203258 or visit the passport office directly."),

        ("Driving License", "How to get a driving license in Pakistan?",
         "Step 1: Get learner permit from district Licensing Authority. Step 2: Practice for 6 weeks. Step 3: Give written and practical test. Step 4: Pay fee and collect license. Required: CNIC, photos, blood group card."),
        ("Driving License", "What is the driving license fee?",
         "Punjab: New = Rs.990, Renewal = Rs.790. Sindh: New = Rs.1000, Renewal = Rs.900. KPK: New = Rs.850. Fees vary slightly by district."),
        ("Driving License", "How to renew expired driving license?",
         "Visit district Licensing Authority with old license, CNIC, photos, and renewal fee. Expired under 1 year = no test required. Expired over 1 year = test may be required."),

        ("Utility Bills", "How to pay WAPDA electricity bill online?",
         "Pay via: (1) JazzCash app, (2) EasyPaisa app, (3) Bank mobile app, (4) ATM using 14-digit consumer reference number, (5) myapps.wapda.gov.pk."),
        ("Utility Bills", "How to pay SNGPL gas bill?",
         "Pay via: (1) billpay.sngpl.com.pk, (2) JazzCash or EasyPaisa, (3) Bank ATM or mobile app, (4) Pakistan Post offices. You need your 10-digit consumer number."),
        ("Utility Bills", "How to check electricity bill online?",
         "Check your WAPDA bill at myapps.wapda.gov.pk or LESCO/IESCO/MEPCO websites. Enter your 14-digit reference number. You can also check via JazzCash or EasyPaisa apps."),

        ("FBR Tax", "How to file income tax return in Pakistan?",
         "Use IRIS portal at iris.fbr.gov.pk. Register with CNIC, login, go to Declaration > Normal Return, fill income and deduction details, submit before the deadline."),
        ("FBR Tax", "What is the tax return filing deadline?",
         "Salaried individuals: September 30. Business individuals: December 31. FBR often extends deadlines — check iris.fbr.gov.pk for current dates."),
        ("FBR Tax", "How to get NTN number?",
         "Register online at iris.fbr.gov.pk or visit FBR facilitation center. Required: CNIC, mobile number, email, bank account. Business NTN also needs registration documents. NTN is free."),
        ("FBR Tax", "How to check if I am filer or non-filer?",
         "Check at Active Taxpayer List (ATL) on fbr.gov.pk or send your CNIC to 9966 via SMS. Filing returns on time keeps you on the Active Taxpayer List."),

        ("BISP", "How to apply for BISP Benazir Income Support Programme?",
         "Register at nearest BISP tehsil office with CNIC and household info. Poverty Score Card survey will be done at your home. If eligible (score below 32.97), you get enrolled. Payments come via Benazir Card every 3 months."),
        ("BISP", "How to check BISP payment status?",
         "SMS your CNIC to 8171, or visit bisp.gov.pk and click Eligibility Check, or visit Bank Al-Habib/HBL branch, or call 0800-26477 (toll-free)."),

        ("Property", "How to register property in Pakistan?",
         "Step 1: Get valuation from Stamp Duty office. Step 2: Pay stamp duty. Step 3: Submit sale deed to Sub-Registrar. Step 4: Both buyer and seller present with CNICs and two witnesses. Completed in 1-2 days."),
        ("Property", "What is stamp duty on property?",
         "Typically 2% stamp duty + 1% registration fee + local taxes. Rates vary by province and property type. In Punjab, total can be 6-8% of property value."),

        ("Birth Certificate", "How to get birth certificate in Pakistan?",
         "From NADRA: Parents bring CNICs to NADRA office. Online registration available at id.nadra.gov.pk for births within 60 days. For older births, visit Union Council with hospital record or affidavit."),
        ("Birth Certificate", "What documents are needed for birth certificate?",
         "Required: Parent's CNICs, hospital birth record or doctor's certificate, Form filled at Union Council or NADRA. Fee is nominal (Rs.100-200). Processing takes 1-3 days."),
    ]
    cursor.executemany(
        "INSERT INTO faqs (category, question, answer) VALUES (?,?,?)", faqs
    )


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def get_all_faqs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM faqs ORDER BY category, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT category FROM faqs ORDER BY category").fetchall()
    conn.close()
    return [r["category"] for r in rows]


def log_chat(session_id, user_query, bot_answer, matched_faq, score):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_logs (session_id,user_query,bot_answer,matched_faq,score) VALUES (?,?,?,?,?)",
        (session_id, user_query, bot_answer, matched_faq, round(score, 4))
    )
    conn.commit()
    conn.close()


def log_unanswered(query):
    conn = get_conn()
    conn.execute("INSERT INTO unanswered_queries (query) VALUES (?)", (query,))
    conn.commit()
    conn.close()


def record_feedback(faq_id, helpful: bool):
    col = "helpful_yes" if helpful else "helpful_no"
    conn = get_conn()
    conn.execute(f"UPDATE faqs SET {col} = {col} + 1 WHERE id = ?", (faq_id,))
    conn.commit()
    conn.close()


def get_analytics():
    conn = get_conn()

    total_chats = conn.execute("SELECT COUNT(*) FROM chat_logs").fetchone()[0]
    answered = conn.execute("SELECT COUNT(*) FROM chat_logs WHERE score >= 0.35").fetchone()[0]
    unanswered = conn.execute("SELECT COUNT(*) FROM unanswered_queries").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(score) FROM chat_logs WHERE score > 0").fetchone()[0] or 0

    by_category = conn.execute("""
        SELECT f.category, COUNT(l.id) as hits
        FROM chat_logs l
        JOIN faqs f ON l.matched_faq = f.question
        GROUP BY f.category ORDER BY hits DESC LIMIT 6
    """).fetchall()

    recent_unanswered = conn.execute(
        "SELECT query, timestamp FROM unanswered_queries ORDER BY timestamp DESC LIMIT 5"
    ).fetchall()

    conn.close()
    return {
        "total_chats": total_chats,
        "answered": answered,
        "unanswered_count": unanswered,
        "avg_score": round(avg_score * 100, 1),
        "by_category": [dict(r) for r in by_category],
        "recent_unanswered": [dict(r) for r in recent_unanswered],
    }
