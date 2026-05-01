"""
nlp_engine.py
-------------
Advanced NLP engine combining:
  - Sentence-BERT for semantic embeddings  (primary scorer)
  - TF-IDF cosine similarity               (secondary / reranker boost)
  - NLTK preprocessing pipeline
  - Spell correction via pyspellchecker
  - Conversation memory (last N turns)
"""

import re
import nltk
import numpy as np
from collections import deque
from typing import Optional

nltk.download("punkt",      quiet=True)
nltk.download("stopwords",  quiet=True)
nltk.download("wordnet",    quiet=True)
nltk.download("punkt_tab",  quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus   import stopwords
from nltk.stem     import WordNetLemmatizer
from spellchecker  import SpellChecker
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise         import cosine_similarity
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from sentence_transformers import SentenceTransformer, util

from database import get_all_faqs, log_chat, log_unanswered


# ── Constants ────────────────────────────────────────────────────────────────

SBERT_MODEL   = "all-MiniLM-L6-v2"   # fast 384-dim model, works offline
SBERT_THRESH  = 0.35                  # minimum SBERT score to accept
TFIDF_WEIGHT  = 0.25                  # how much TF-IDF boosts the final score
MEMORY_TURNS  = 5                     # conversation turns to remember

STOP_WORDS = set(stopwords.words("english"))
STOP_WORDS.update({"pakistan", "pakistani", "please", "want", "need",
                   "tell", "know", "hello", "hi", "hey"})


# ── Preprocessor ─────────────────────────────────────────────────────────────

class Preprocessor:
    def __init__(self):
        self.lemmatizer  = WordNetLemmatizer()
        self.spell       = SpellChecker()

    def clean(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def correct_spelling(self, text: str) -> str:
        words     = text.split()
        corrected = []
        for w in words:
            fixed = self.spell.correction(w)
            corrected.append(fixed if fixed else w)
        return " ".join(corrected)

    def preprocess(self, text: str, spell_check: bool = True) -> str:
        text = self.clean(text)
        if spell_check:
            text = self.correct_spelling(text)
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens]
        return " ".join(tokens)


# ── Conversation Memory ───────────────────────────────────────────────────────

class ConversationMemory:
    """Stores last N (query, answer) pairs per session."""

    def __init__(self, max_turns: int = MEMORY_TURNS):
        self._sessions: dict[str, deque] = {}
        self.max_turns = max_turns

    def add(self, session_id: str, query: str, answer: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=self.max_turns)
        self._sessions[session_id].append({"query": query, "answer": answer})

    def get_context(self, session_id: str) -> list[dict]:
        return list(self._sessions.get(session_id, []))

    def build_context_string(self, session_id: str) -> str:
        history = self.get_context(session_id)
        if not history:
            return ""
        lines = []
        for turn in history[-3:]:          # use only last 3 turns as context
            lines.append(f"User: {turn['query']}")
            lines.append(f"Bot: {turn['answer'][:120]}...")
        return "\n".join(lines)

    def clear(self, session_id: str):
        self._sessions.pop(session_id, None)


# ── Main NLP Engine ───────────────────────────────────────────────────────────

class AdvancedFAQEngine:
    """
    Two-stage retrieval:
      Stage 1 — Sentence-BERT: dense semantic search, returns top-5 candidates
      Stage 2 — TF-IDF reranker: sparse keyword boost on top-5, picks best
    Final score = 0.75 * sbert_score + 0.25 * tfidf_score
    """

    def __init__(self):
        print("[Engine] Loading Sentence-BERT model...")
        self.sbert       = SentenceTransformer(SBERT_MODEL)
        self.preprocessor = Preprocessor()
        self.memory       = ConversationMemory()

        self.faqs           = []
        self.faq_embeddings = None   # SBERT embeddings  (N × 384)
        self.tfidf_matrix   = None   # TF-IDF matrix     (N × vocab)
        self.vectorizer     = TfidfVectorizer(ngram_range=(1, 2))

        self._build_index()

    # ── Index building ────────────────────────────────────────────────────────

    def _build_index(self):
        self.faqs = get_all_faqs()
        questions = [f["question"] for f in self.faqs]

        # SBERT embeddings (raw questions — SBERT handles its own tokenization)
        print(f"[Engine] Encoding {len(questions)} FAQs with SBERT...")
        self.faq_embeddings = self.sbert.encode(questions, convert_to_tensor=True)

        # TF-IDF on preprocessed questions
        preprocessed = [self.preprocessor.preprocess(q) for q in questions]
        self.tfidf_matrix = self.vectorizer.fit_transform(preprocessed)
        print("[Engine] Index built successfully.")

    def rebuild_index(self):
        """Call this if FAQs are updated at runtime."""
        self._build_index()

    # ── Core retrieval ─────────────────────────────────────────────────────────

    def get_answer(self, user_query: str, session_id: str = "default",
                   category_filter: Optional[str] = None) -> dict:
        """
        Full pipeline:
          1. Preprocess + spell-correct query
          2. SBERT semantic search → top-5 candidates
          3. TF-IDF rerank → best match
          4. Threshold check → answer or fallback
          5. Log to DB + store in memory
        """
        # Step 1: Preprocess
        corrected_query = self.preprocessor.correct_spelling(user_query)
        processed       = self.preprocessor.preprocess(corrected_query)

        if not processed.strip():
            return self._fallback(user_query, session_id, "Please add more details to your question.")

        # Step 2: Apply category filter (filter self.faqs indices)
        if category_filter:
            indices = [i for i, f in enumerate(self.faqs)
                       if f["category"].lower() == category_filter.lower()]
        else:
            indices = list(range(len(self.faqs)))

        if not indices:
            return self._fallback(user_query, session_id, f"No FAQs found for category '{category_filter}'.")

        # Step 3: SBERT search on filtered indices
        query_emb   = self.sbert.encode(corrected_query, convert_to_tensor=True)
        subset_embs = self.faq_embeddings[indices]
        sbert_scores = util.cos_sim(query_emb, subset_embs)[0].cpu().numpy()

        # Top-5 candidates from SBERT
        top5_local = np.argsort(sbert_scores)[::-1][:5]
        top5_global = [indices[i] for i in top5_local]

        # Step 4: TF-IDF rerank on top-5
        user_vec    = self.vectorizer.transform([processed])
        tfidf_sub   = self.tfidf_matrix[top5_global]
        tfidf_scores = cosine_similarity(user_vec, tfidf_sub).flatten()

        # Combined score
        combined = np.array([
            (1 - TFIDF_WEIGHT) * sbert_scores[top5_local[k]] + TFIDF_WEIGHT * tfidf_scores[k]
            for k in range(len(top5_local))
        ])

        best_k      = int(np.argmax(combined))
        best_idx    = top5_global[best_k]
        best_score  = float(combined[best_k])
        best_sbert  = float(sbert_scores[top5_local[best_k]])

        matched_faq = self.faqs[best_idx]

        # Step 5: Threshold check
        if best_sbert < SBERT_THRESH:
            log_unanswered(user_query)
            return self._fallback(
                user_query, session_id,
                "I couldn't find a relevant answer. Please rephrase your question "
                "or contact the relevant government office directly."
            )

        # Build top-3 suggestions list
        suggestions = []
        for k in range(min(3, len(top5_global))):
            gi = top5_global[k]
            suggestions.append({
                "question": self.faqs[gi]["question"],
                "category": self.faqs[gi]["category"],
                "score":    round(float(combined[k]), 3),
            })

        # Step 6: Context from conversation memory
        context = self.memory.build_context_string(session_id)

        # Step 7: Log & store
        log_chat(session_id, user_query, matched_faq["answer"],
                 matched_faq["question"], best_score)
        self.memory.add(session_id, user_query, matched_faq["answer"])

        return {
            "found":            True,
            "answer":           matched_faq["answer"],
            "category":         matched_faq["category"],
            "matched_question": matched_faq["question"],
            "faq_id":           matched_faq["id"],
            "score":            round(best_score, 4),
            "sbert_score":      round(best_sbert, 4),
            "corrected_query":  corrected_query if corrected_query != user_query else None,
            "suggestions":      suggestions[1:],   # exclude best itself
            "context_used":     bool(context),
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _fallback(self, query: str, session_id: str, message: str) -> dict:
        self.memory.add(session_id, query, message)
        return {
            "found":            False,
            "answer":           message,
            "category":         None,
            "matched_question": None,
            "faq_id":           None,
            "score":            0.0,
            "sbert_score":      0.0,
            "corrected_query":  None,
            "suggestions":      [],
            "context_used":     False,
        }

    def get_history(self, session_id: str) -> list[dict]:
        return self.memory.get_context(session_id)

    def clear_session(self, session_id: str):
        self.memory.clear(session_id)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from database import init_db
    init_db()
    engine = AdvancedFAQEngine()

    tests = [
        ("How do I get my CNIC?",             None),
        ("paaspot apply krna hai",             "Passport"),
        ("tax return ki last date?",           None),
        ("bijli ka bill online kaise bharon?", "Utility Bills"),
        ("what is the weather today?",         None),
    ]

    print("\n" + "="*65)
    for q, cat in tests:
        r = engine.get_answer(q, session_id="test", category_filter=cat)
        status = "✓" if r["found"] else "✗"
        print(f"\n{status}  Query   : {q}")
        if r["corrected_query"]:
            print(f"   Corrected: {r['corrected_query']}")
        print(f"   Category : {r['category']}  |  Score: {r['score']}  |  SBERT: {r['sbert_score']}")
        print(f"   Answer   : {r['answer'][:90]}...")
    print("="*65)
