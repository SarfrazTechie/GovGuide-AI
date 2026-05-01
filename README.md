# Advanced FAQ Chatbot — Pakistan Govt Services
### CodeAlpha AI Internship — Task 2

---

## What makes this ADVANCED (not basic)

| Feature | Basic level | This project |
|---|---|---|
| Matching | TF-IDF cosine similarity | **Sentence-BERT** semantic embeddings |
| Reranking | None | **TF-IDF hybrid reranker** (0.75 SBERT + 0.25 TF-IDF) |
| Spell check | None | **pyspellchecker** auto-correction |
| Memory | None | **Conversation memory** (last 5 turns per session) |
| Storage | JSON file | **SQLite database** (FAQs + chat logs + analytics) |
| Feedback | None | **Thumbs up/down** per answer, stored in DB |
| Analytics | None | **Live dashboard** — charts, KPIs, unanswered queries |
| UI | Basic HTML | **Category filters, confidence bar, related questions** |
| API | One endpoint | **REST API** with 7 endpoints |

---

## Project Structure

```
advanced_faq_chatbot/
│
├── app.py              ← Flask REST API (7 endpoints)
├── nlp_engine.py       ← Sentence-BERT + TF-IDF reranker + spell check + memory
├── database.py         ← SQLite layer (FAQs, chat logs, analytics, feedback)
├── requirements.txt    ← All dependencies
│
└── templates/
    ├── index.html      ← Chat UI (category filter, confidence bar, suggestions)
    └── analytics.html  ← Live analytics dashboard with Chart.js
```

---

## Setup Instructions

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

### 3. Open in browser

- Chat UI:   http://127.0.0.1:5000
- Analytics: http://127.0.0.1:5000/analytics

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Main chat — accepts `{message, category}` |
| GET | `/history/<session_id>` | Get conversation history |
| POST | `/feedback` | Record helpful/not helpful `{faq_id, helpful}` |
| POST | `/clear/<session_id>` | Clear conversation memory |
| GET | `/api/categories` | List all FAQ categories |
| GET | `/api/analytics` | Analytics JSON |
| GET | `/analytics` | Analytics dashboard page |

---

## NLP Pipeline (Technical Details)

```
User Query
    │
    ▼
Spell Correction (pyspellchecker)
    │
    ▼
NLTK Preprocessing
  → lowercase → clean → tokenize → stopwords → lemmatize
    │
    ▼
Sentence-BERT Encoding (all-MiniLM-L6-v2)
  → 384-dimensional semantic vector
    │
    ▼
Cosine Similarity against all FAQ embeddings
  → Top-5 candidates selected
    │
    ▼
TF-IDF Reranker (on top-5 only)
  → Combined score = 0.75 × SBERT + 0.25 × TF-IDF
    │
    ▼
Threshold Check (SBERT score ≥ 0.35)
  → Answer returned OR fallback message
    │
    ▼
Log to SQLite + Store in Conversation Memory
```

---

## FAQ Categories Covered

- NADRA (CNIC, NICOP, renewal)
- Passport (new, renewal, tracking, fees)
- Driving License (new, renewal, fees)
- Utility Bills (WAPDA, SNGPL, online payment)
- FBR Tax (NTN, return filing, ATL)
- BISP (application, payment status)
- Property (registration, stamp duty)
- Birth Certificate

---

## Tech Stack

- **Backend:** Python, Flask
- **NLP:** Sentence-Transformers (SBERT), NLTK, scikit-learn
- **Spell Check:** pyspellchecker
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **Charts:** Chart.js

---

*Built for CodeAlpha AI Internship — Task 2: FAQ Chatbot*
