# 🇵🇰 GovGuide AI — Advanced FAQ Chatbot

> **Pakistan Government Services · Powered by Semantic NLP**

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-REST%20API-000000?style=flat-square&logo=flask&logoColor=white)
![SBERT](https://img.shields.io/badge/Sentence--BERT-all--MiniLM--L6--v2-FF6B35?style=flat-square)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)
![CodeAlpha](https://img.shields.io/badge/CodeAlpha-AI%20Internship%20Task%202-6366F1?style=flat-square)

---

## ✦ What Makes This Advanced

| Feature | Basic Level | This Project |
|---|---|---|
| **Matching** | TF-IDF cosine similarity | **Sentence-BERT** semantic embeddings |
| **Reranking** | None | **Hybrid reranker** — 0.75 × SBERT + 0.25 × TF-IDF |
| **Spell Check** | None | **pyspellchecker** auto-correction |
| **Memory** | None | **Conversation memory** (last 5 turns per session) |
| **Storage** | JSON file | **SQLite** — FAQs + chat logs + analytics + feedback |
| **Feedback** | None | **Thumbs up/down** per answer, stored in DB |
| **Analytics** | None | **Live dashboard** — Chart.js, KPIs, unanswered queries |
| **UI** | Basic HTML | **Category filters, confidence bar, related questions** |
| **API** | One endpoint | **7 REST endpoints** |

---

## ⚡ Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
python app.py
```

Visit `http://localhost:5000` for the chat UI and `http://localhost:5000/analytics` for the live dashboard.

---

## 🧠 NLP Pipeline

```
User Query
    │
    ▼
① Spell Correction
    pyspellchecker auto-corrects raw input
    │
    ▼
② NLTK Preprocessing
    lowercase → clean → tokenize → stopwords → lemmatize
    │
    ▼
③ Sentence-BERT Encoding
    all-MiniLM-L6-v2 → 384-dimensional semantic vector
    │
    ▼
④ Cosine Similarity Search
    Top-5 candidates selected from all FAQ embeddings
    │
    ▼
⑤ TF-IDF Hybrid Reranker
    Combined score = 0.75 × SBERT + 0.25 × TF-IDF
    │
    ▼
⑥ Threshold Check  (SBERT ≥ 0.35)
    Answer returned  OR  fallback message
    │
    ▼
⑦ Log to SQLite + Store in Conversation Memory
```

---

## 🔌 REST API — 7 Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Main chat — accepts `{message, category}` |
| `GET` | `/history/<session_id>` | Get conversation history |
| `POST` | `/feedback` | Record helpful/not helpful `{faq_id, helpful}` |
| `POST` | `/clear/<session_id>` | Clear conversation memory |
| `GET` | `/api/categories` | List all FAQ categories |
| `GET` | `/api/analytics` | Analytics JSON |
| `GET` | `/analytics` | Live analytics dashboard page |

---

## 📂 Project Structure

```
advanced_faq_chatbot/
│
├── app.py              ← Flask REST API (7 endpoints)
├── nlp_engine.py       ← SBERT + TF-IDF reranker + spell check + memory
├── database.py         ← SQLite layer (FAQs, chat logs, analytics, feedback)
├── requirements.txt    ← All dependencies
│
└── templates/
    ├── index.html      ← Chat UI (category filter, confidence bar, suggestions)
    └── analytics.html  ← Live analytics dashboard with Chart.js
```

---

## 🏛️ FAQ Coverage

| Domain | Topics |
|---|---|
| 🪪 **NADRA** | CNIC, NICOP, renewal |
| 🛂 **Passport** | New, renewal, tracking, fees |
| 🚗 **Driving License** | New, renewal, fees |
| 💡 **Utility Bills** | WAPDA, SNGPL, online payment |
| 🧾 **FBR Tax** | NTN, return filing, ATL |
| 💰 **BISP** | Application, payment status |
| 🏠 **Property** | Registration, stamp duty |
| 📋 **Birth Certificate** | Registration |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask |
| **NLP** | Sentence-Transformers (SBERT), NLTK, scikit-learn |
| **Spell Check** | pyspellchecker |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3, vanilla JavaScript |
| **Charts** | Chart.js |

---

*Built for the **CodeAlpha AI Internship** — Task 2: Advanced FAQ Chatbot*
