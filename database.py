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

        CREATE TABLE IF NOT EXISTS chat_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL UNIQUE,
            title      TEXT    NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        # ── NADRA ──────────────────────────────────────────
        ("NADRA", "How to apply for a new CNIC?",
         "Visit your nearest NADRA Registration Center (NRC) with: (1) Birth Certificate or Form-B, (2) Father's/Mother's CNIC, (3) Proof of residence (utility bill or domicile), (4) Two passport-size photographs. Fill Form-4, submit biometrics and pay the fee. Normal delivery (30 days) = Rs.750, Urgent (7 days) = Rs.1500, Executive (2 days) = Rs.3000."),

        ("NADRA", "What documents are required for CNIC?",
         "Required documents for CNIC: (1) Birth Certificate or Form-B, (2) Father's or Mother's CNIC, (3) Proof of residence such as utility bill or domicile certificate, (4) Two passport-size photographs. For married women, nikah nama is also required. For minors, school certificate may be accepted."),

        ("NADRA", "How to renew expired CNIC?",
         "To renew expired CNIC: Visit any NADRA office with your old CNIC. Fill renewal form, submit fresh biometrics. Fee: Normal Rs.750, Urgent Rs.1500, Executive Rs.3000. Online renewal also available at id.nadra.gov.pk. Senior citizens above 60 get 50% discount."),

        ("NADRA", "What is the CNIC fee?",
         "CNIC fees: Normal delivery (30 days) = Rs.750, Urgent delivery (7 days) = Rs.1500, Executive delivery (2 days) = Rs.3000. Senior citizens above 60 years get 50% discount. Renewal fee is same as new CNIC fee."),

        ("NADRA", "How to get NICOP for overseas Pakistanis?",
         "NICOP (National Identity Card for Overseas Pakistanis) can be applied at Pakistan missions abroad or online at id.nadra.gov.pk. Required: valid Pakistani passport, CNIC copy, overseas residence proof, passport-size photos. Processing takes 4-6 weeks. Fee varies by country."),

        ("NADRA", "How to get CNIC for first time?",
         "For first-time CNIC (age 18+): Visit NADRA office with birth certificate or Form-B, parent's CNIC, school/college certificate, proof of residence. Fill Form-4, give biometrics (fingerprints + photo). Pay fee and collect within mentioned time. Minimum age is 18 years."),

        ("NADRA", "How to check CNIC status online?",
         "Check CNIC status online at id.nadra.gov.pk using your tracking ID received at time of application. You can also SMS your CNIC number to 7000 to check status. Or call NADRA helpline 051-111-786-100."),

        # ── PASSPORT ───────────────────────────────────────
        ("Passport", "How to apply for a new Pakistani passport?",
         "Apply online at dgip.gov.pk or visit nearest Passport Office. Required: original CNIC, 2 passport-size photos (white background), fee challan from designated bank. Steps: (1) Fill online form, (2) Pay fee at bank, (3) Visit passport office with original documents, (4) Give biometrics, (5) Collect passport on due date."),

        ("Passport", "What is the passport fee in Pakistan?",
         "Pakistani passport fees 2024: 36-page Normal (30 days) = Rs.3000, 72-page Normal = Rs.5000. Urgent 36-page (7 days) = Rs.5000, Urgent 72-page = Rs.7500. Executive 36-page (2 days) = Rs.12000, Executive 72-page = Rs.15000. Fee paid at HBL, MCB, or Allied Bank."),

        ("Passport", "How to renew Pakistani passport?",
         "Passport renewal: Visit dgip.gov.pk or nearest passport office. Bring original old passport, CNIC, photos, and fee challan. If expired less than 2 years ago, simple renewal process. If expired more than 2 years, fresh application required. Renewal fee is same as new passport fee."),

        ("Passport", "How to track passport application status?",
         "Track passport status at dgip.gov.pk using your CNIC number or token number. You can also call helpline 051-9203258. SMS tracking: send CNIC number to 9988. You will receive SMS notification when passport is ready for collection."),

        ("Passport", "What documents are needed for child passport?",
         "For child passport (under 18): Original birth certificate, Form-B or B-Form, both parents' CNICs, parents' nikah nama, child's recent photos, fee challan. Both parents must be present or provide affidavit. Child passport is valid for 5 years."),

        ("Passport", "How long is Pakistani passport valid?",
         "Pakistani passport validity: Adult passport (18+) is valid for 10 years. Child passport (under 18) is valid for 5 years. Machine Readable Passport (MRP) is being replaced by e-Passport. Always renew 6 months before expiry for international travel."),

        # ── DRIVING LICENSE ────────────────────────────────
        ("Driving License", "How to get a driving license in Pakistan?",
         "Steps to get driving license: (1) Visit district Licensing Authority with CNIC, photos, blood group card, (2) Apply for Learner Permit (valid 6 weeks), (3) Practice driving, (4) Return for written test (traffic rules), (5) Give practical driving test, (6) Pay fee and collect license. Total process takes 6-8 weeks."),

        ("Driving License", "What is the driving license fee? How much does license cost?",
         "Driving license fee by province: (1) Punjab: New = Rs.990, Renewal = Rs.790, (2) Sindh: New = Rs.1000, Renewal = Rs.900, (3) KPK: New = Rs.850, Renewal = Rs.750, (4) Balochistan: New = Rs.800, (5) International Driving Permit = Rs.1500 extra. Fees may vary slightly by district."),

        ("Driving License", "How to renew expired driving license?",
         "Driving license renewal steps: (1) Visit district Licensing Authority with old license, CNIC, photos and renewal fee, (2) Expired less than 1 year = no test required, direct renewal, (3) Expired 1-3 years = written test only, (4) Expired more than 3 years = full test required again, (5) Online renewal available in some districts. Fee: Punjab Rs.790, Sindh Rs.900."),

        ("Driving License", "What are the types and categories of driving license in Pakistan?",
         "Pakistani driving license categories: Motorcycle (LTV-M), Car/Jeep (LTV), Light Commercial Vehicle, Heavy Transport Vehicle (HTV), PSV (Public Service Vehicle for buses). Each category requires separate test. You can apply for multiple categories on same license."),

        ("Driving License", "How to get international driving permit?",
         "International Driving Permit (IDP): Apply at district Licensing Authority with valid Pakistani license, CNIC, photos, fee of Rs.1500. IDP is valid for 1 year and recognized in 150+ countries. Must carry both IDP and original Pakistani license while driving abroad."),

        # ── UTILITY BILLS ──────────────────────────────────
        ("Utility Bills", "How to pay WAPDA electricity bill online?",
         "Pay electricity bill online via: (1) JazzCash app — go to Bills > Electricity > enter 14-digit reference number, (2) Easypaisa app — same process, (3) Your bank mobile app — bill payment section, (4) ATM machine — use bill payment option, (5) myapps.wapda.gov.pk website. You need your 14-digit consumer reference number printed on bill."),

        ("Utility Bills", "How to pay SNGPL gas bill?",
         "Pay SNGPL gas bill via: (1) Online at billpay.sngpl.com.pk, (2) JazzCash or Easypaisa apps, (3) Any bank branch or ATM, (4) Pakistan Post offices, (5) Authorized franchises. You need your 10-digit consumer number on the bill. Late payment surcharge applies after due date."),

        ("Utility Bills", "How to check electricity bill online?",
         "Check electricity bill online: LESCO area: lesco.gov.pk, IESCO area: iesco.com.pk, MEPCO area: mepco.com.pk, PESCO area: pesco.gov.pk, QESCO area: qesco.com.pk. Enter your 14-digit reference number. You can also check via JazzCash or Easypaisa apps under bill inquiry."),

        ("Utility Bills", "How to pay PTCL telephone bill?",
         "Pay PTCL bill via: (1) ptcl.com.pk website, (2) JazzCash or Easypaisa, (3) Bank mobile apps, (4) ATM, (5) Any bank branch, (6) PTCL franchises and customer service centers. You need your PTCL account number or phone number. Postpaid bills due by 20th of each month."),

        ("Utility Bills", "How to get duplicate electricity bill?",
         "Get duplicate electricity bill: Visit your electricity company's website (LESCO, IESCO, MEPCO etc.), enter your reference number, download and print bill. Or visit nearest electricity company office with CNIC and reference number. Duplicate bill is free of cost."),

        # ── FBR TAX ────────────────────────────────────────
        ("FBR Tax", "How to file income tax return in Pakistan?",
         "File income tax return on IRIS portal (iris.fbr.gov.pk): (1) Register with CNIC and mobile number, (2) Login to IRIS, (3) Go to Declaration > Normal Return, (4) Select tax year, (5) Fill income details (salary, business, property), (6) Add deductions and tax already paid, (7) Calculate tax, (8) Submit before deadline. Keep salary slips and bank statements ready."),

        ("FBR Tax", "What is the tax return filing deadline?",
         "Income tax return deadlines: Salaried individuals = September 30 each year. Business individuals = December 31. Companies = December 31. AOPs (Association of Persons) = December 31. FBR often extends these deadlines — always check iris.fbr.gov.pk for current deadline. Late filing attracts penalty."),

        ("FBR Tax", "How to get NTN number in Pakistan?",
         "Get NTN (National Tax Number): (1) Online at iris.fbr.gov.pk > Registration > New Registration, (2) Enter CNIC, mobile, email, bank account details, (3) For business NTN, also need business registration documents, (4) NTN issued instantly online. NTN is free of cost. Salaried persons NTN is same as their CNIC number."),

        ("FBR Tax", "How to check if I am filer or non-filer?",
         "Check Active Taxpayer status: (1) Visit fbr.gov.pk > Active Taxpayer List, (2) Enter your CNIC number, (3) SMS your CNIC to 9966, (4) Check on ATL (Active Taxpayer List) portal. Filers get lower withholding tax rates on banking, property, vehicles. File returns by deadline to maintain filer status."),

        ("FBR Tax", "What are the benefits of being a tax filer?",
         "Benefits of tax filer in Pakistan: (1) Lower withholding tax on bank transactions, (2) Lower tax on property purchase/sale, (3) Lower tax on vehicle purchase, (4) No higher tax deductions on cash withdrawals, (5) Can claim tax refunds, (6) Required for government jobs and contracts, (7) Lower advance tax on imports."),

        ("FBR Tax", "How to pay income tax online?",
         "Pay income tax online: (1) Login to iris.fbr.gov.pk, (2) Go to Payment > Create Payment, (3) Select tax head and year, (4) Generate Payment Slip ID (PSID), (5) Pay via 1-Link, JazzCash, Easypaisa, or any bank using PSID, (6) Tax payment reflects in 1-2 working days. Keep payment receipt for records."),

        # ── BISP ───────────────────────────────────────────
        ("BISP", "How to apply for BISP Benazir Income Support Programme?",
         "Apply for BISP: (1) Visit nearest BISP tehsil/district office with original CNIC, (2) Provide household information (family members, income, assets), (3) Poverty Score Card (PSC) survey conducted at your home, (4) If poverty score below 32.97, you are eligible, (5) Enrolled in program and Benazir Card issued, (6) Payments every 3 months via card. Registration is free."),

        ("BISP", "How to check BISP payment status?",
         "Check BISP payment: (1) SMS your CNIC number to 8171 (free), (2) Visit bisp.gov.pk > Eligibility Check > enter CNIC, (3) Visit Bank Al-Habib or HBL branch with CNIC, (4) Call toll-free helpline 0800-26477, (5) Visit nearest BISP office. You will be informed if payment is released and amount."),

        ("BISP", "What is BISP eligibility criteria?",
         "BISP eligibility: Poverty Score Card (PSC) score must be below 32.97. Factors considered: household income, assets (land, house, vehicle), education level, number of dependents. Government employees, income tax filers, and those with vehicles or large land holdings are generally not eligible. Survey done by BISP team at your home."),

        ("BISP", "How much money does BISP give?",
         "BISP payment amounts (2024): Benazir Kafaalat = Rs.10500 per quarter (every 3 months). Benazir Taleemi Wazaif for children: Primary = Rs.2000/quarter per child, Middle = Rs.3000/quarter, Matric = Rs.4000/quarter. Benazir Nashonuma for children under 2 years = Rs.2000/month. Amounts may change — check bisp.gov.pk for latest."),

        ("BISP", "How to update information in BISP?",
         "Update BISP information: Visit nearest BISP office with original CNIC and supporting documents. You can update: mobile number, bank account, family members, address. For complaints or issues with payment, call 0800-26477 or visit bisp.gov.pk. Bring old and new documents for any changes."),

        # ── PROPERTY ───────────────────────────────────────
        ("Property", "How to register property in Pakistan?",
         "Property registration steps: (1) Agree on sale price and prepare sale deed with lawyer, (2) Get property valuation from Stamp Duty office, (3) Pay stamp duty at designated bank, (4) Visit Sub-Registrar office with: sale deed, CNICs of buyer and seller, two witnesses, paid stamp duty receipt, (5) Both parties sign deed, (6) Sub-Registrar registers and stamps document. Process takes 1-3 days."),

        ("Property", "What is stamp duty on property in Pakistan?",
         "Property stamp duty rates (Punjab): Stamp duty = 2% of property value, CVT (Capital Value Tax) = 2%, Registration fee = 1%, TMA fee = 0.5%, Total = approx 5.5-7% of property value. Rates vary by province: Sindh and KPK have different rates. Calculated on DC rate or actual price, whichever is higher."),

        ("Property", "How to transfer property in Pakistan?",
         "Property transfer process: (1) Both parties visit Sub-Registrar office, (2) Bring original sale deed, CNICs, photos, witnesses, (3) Pay transfer fee and applicable taxes, (4) Mutation (Intiqal) filed at Patwari office, (5) After mutation approved, property officially transferred in government records. Hire a property lawyer for smooth process."),

        ("Property", "What is Fard Malkiat in Pakistan?",
         "Fard Malkiat is official ownership document of land/property in Punjab. Get it from: (1) Visit Arazi Record Center or PLRA (Punjab Land Records Authority) office, (2) Apply online at punjab-zameen.gov.pk, (3) Bring CNIC and property details, (4) Fee is nominal Rs.200-500. Fard confirms you are legal owner in government records."),

        # ── BIRTH CERTIFICATE ──────────────────────────────
        ("Birth Certificate", "How to get birth certificate in Pakistan?",
         "Get birth certificate: For newborns (within 60 days): Register at Union Council or online at id.nadra.gov.pk. For older children: Visit NADRA office with parents' CNICs, hospital birth record or doctor certificate. For adults: Visit Union Council with affidavit from parents and witnesses. Fee is Rs.100-200. Processing 1-3 days."),

        ("Birth Certificate", "What documents are needed for birth certificate?",
         "Documents for birth certificate: (1) Both parents' original CNICs, (2) Hospital birth record or doctor's certificate, (3) Nikah nama of parents, (4) Filled application form from Union Council or NADRA, (5) For late registration (after 1 year): affidavit required. Fee: Rs.100-300 depending on urgency."),

        ("Birth Certificate", "How to get birth certificate online in Pakistan?",
         "Online birth registration at id.nadra.gov.pk: Available for births within 60 days. Create account, enter child details, parents' CNIC numbers, hospital information. Upload hospital birth certificate. After verification, official birth certificate mailed or collected from NADRA office. Fee paid online."),

        ("Birth Certificate", "How to get computerized birth certificate from NADRA?",
         "NADRA computerized birth certificate: Visit any NADRA office with parents' CNICs and existing birth certificate from Union Council. NADRA issues computerized version with QR code. Fee: Normal = Rs.100, Urgent = Rs.300. This is accepted for passport, school admission, and all official purposes."),

        # ── POLICE CHARACTER CERTIFICATE ───────────────────
        ("Police Character Certificate", "How to get police character certificate in Pakistan?",
         "Police Character Certificate (PCC) process: (1) Visit nearest Police Station or District Police Office with CNIC, (2) Fill application form, (3) Pay fee at designated bank (Rs.200-500), (4) Police verification done at your address within 7-15 days, (5) Certificate issued after verification. Required for jobs, visa applications, and overseas travel."),

        ("Police Character Certificate", "What documents are required for police character certificate?",
         "Documents for Police Character Certificate: (1) Original CNIC and photocopy, (2) Two passport-size photographs, (3) Fee payment receipt, (4) Application form (available at police station), (5) For overseas PCC: passport copy also required, (6) Proof of residence (utility bill). Some districts may require additional documents."),

        ("Police Character Certificate", "How long does police character certificate take?",
         "Police Character Certificate timeline: Local PCC (for jobs): 7-15 working days after police verification. PCC for overseas/visa: 15-30 days. Online PCC (available in some provinces): 7-10 days via e-sahulat or police portal. You can follow up at your local police station using your application number."),

        ("Police Character Certificate", "What is the fee for police character certificate?",
         "Police Character Certificate fee: Punjab: Rs.200-300. Sindh: Rs.500. KPK: Rs.200. Islamabad (ICT): Rs.300. For overseas/visa PCC, additional embassy attestation fee may apply. Fee paid at designated bank branch or via online banking. Keep receipt as proof of payment."),

        ("Police Character Certificate", "How to get police character certificate for visa?",
         "PCC for visa application: (1) Visit District Police Office (not local station), (2) Bring CNIC, passport copy, photos, visa application details, (3) Pay fee, (4) Police verification at home address, (5) Certificate issued with official stamp and DPO signature, (6) Get attested from Ministry of Interior if required by embassy. Process takes 2-4 weeks."),

        # ── DOMICILE CERTIFICATE ───────────────────────────
        ("Domicile Certificate", "How to get domicile certificate in Pakistan?",
         "Domicile Certificate process: (1) Visit District Commissioner (DC) office or Deputy Commissioner office in your district, (2) Get application form, (3) Attach required documents, (4) Pay fee at bank, (5) Submit application, (6) Verification done by local patwari/tehsildar, (7) Certificate issued after verification. Takes 7-30 days depending on district."),

        ("Domicile Certificate", "What documents are required for domicile certificate?",
         "Documents for Domicile Certificate: (1) Original CNIC, (2) Birth certificate, (3) Father's CNIC and domicile certificate, (4) Proof of residence (utility bill, property documents, or rental agreement), (5) Two passport-size photographs, (6) Affidavit on stamp paper (Rs.50-100), (7) Application form. For students: school/college certificate of same district."),

        ("Domicile Certificate", "What is the fee for domicile certificate?",
         "Domicile certificate fee: Punjab: Rs.200-500. Sindh: Rs.300-600. KPK: Rs.200-400. Balochistan: Rs.200. Fee paid at designated bank or via online banking. Some districts charge additional verification fee. Stamp paper for affidavit costs Rs.50-100 extra. Total cost usually Rs.300-700."),

        ("Domicile Certificate", "How long is domicile certificate valid?",
         "Domicile certificate is valid for lifetime — it does not expire. However, some institutions may ask for a fresh certificate issued within last 6 months or 1 year. If you move permanently to another district, you need to apply for new domicile from that district. Domicile of a district is proof of permanent residence."),

        ("Domicile Certificate", "Why is domicile certificate required?",
         "Domicile certificate is required for: (1) Government job applications (quota system), (2) University admissions (local/provincial quota), (3) CNIC application as proof of residence, (4) Court cases and legal matters, (5) Passport application, (6) Property registration, (7) Scholarships and government benefits. It proves you are permanent resident of that district."),

        ("Domicile Certificate", "How to get domicile certificate online?",
         "Online domicile certificate: Available in Punjab at punjab.gov.pk or e-sahulat centers. In Sindh via sindh.gov.pk portal. Steps: Create account, fill form, upload documents, pay fee online, track application. Physical verification still required. Certificate sent by post or collected from DC office. Check your provincial government website for availability."),
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


def save_session(session_id: str, title: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO chat_sessions (session_id, title)
        VALUES (?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            title = excluded.title,
            updated_at = CURRENT_TIMESTAMP
    """, (session_id, title[:60]))
    conn.commit()
    conn.close()


def get_all_sessions():
    conn = get_conn()
    rows = conn.execute("""
        SELECT session_id, title, updated_at
        FROM chat_sessions
        ORDER BY updated_at DESC
        LIMIT 20
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_messages(session_id: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT user_query, bot_answer, timestamp
        FROM chat_logs
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_session(session_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM chat_logs WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
