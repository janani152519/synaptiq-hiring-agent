# Synaptiq: Hidden Ground Truth Hiring Engine

An ultra-fast, intent-driven candidate evaluation engine designed to surpass traditional ATS keyword matchers. Developed for the India.Runs Data & AI Challenge.

## 🚀 Overview
Traditional Applicant Tracking Systems (ATS) rely on superficial keyword matching, producing hundreds of "maybe" candidates who know basic AI tools. The Synaptiq Hiring Engine abandons linear scoring for a **Tiered Classification System (Tiers 0-5)** mimicking an elite technical recruiter's "Hidden Ground Truth." It actively penalizes generic backgrounds while hunting for deeply technical engineers who have built production-level Retrieval, Ranking, and Recommendation systems.

## ✨ Key Differentiators
- **Tiered Truth Over Linear Scoring:** Classifies candidates into rigid Relevance Tiers (e.g., Tier 5 = Built Production Retrieval Systems; Tier 1 = Basic LLM Wrapper).
- **Behavioral Twin Separation:** When technical skills tie, an exponential **Availability Index** ranks candidates based on recent activity (penalizing candidates inactive for >90 days).
- **Anti-Fraud Honeypot Detection:** Actively hunts and blocks "Skill Inflation" and impossible chronological career jumps.
- **Deterministic Explainability:** Generates verifiable textual proof explicitly tying evaluation metrics (NDCG, MAP) to the candidate's tier placement without LLM hallucination.

## 🏗 System Architecture
- **Data Layer:** SQLite Database pre-populated with 100,000 JSON resume blobs.
- **Backend:** Python FastAPI running a custom `TalentDNAEngine`, `CandidateRanker`, and `HoneypotDetector`.
- **Frontend:** React + TypeScript (Vite), styled with Glassmorphism UI and Chart.js data visualizations.
- **Performance Engine:** Uses a blazing fast Deferred Join SQL Proxy to fetch and sort the top 2,000 candidates in `<50ms` before running deep Python classification on the subset.

## 🛠 Tech Stack
* Python 3 & FastAPI
* SQLite (for massive local concurrency)
* React & Vite (for lightning-fast HMR)
* Chart.js (for Talent Genome Radar Charts)

## ⚡ Getting Started
### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
### 2. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Core Features
1. **Recruiter Command Center:** Real-time metrics on candidates scanned, honeypots blocked, and hidden gems discovered.
2. **Dynamic Rankings:** A live leaderboard with interactive sliders to instantly adjust algorithm weights (Semantic, Startup Readiness, Leadership) and re-rank the DB on the fly.
3. **Hidden Talent Discovery:** Curated top 250 Hidden Gems who lack standard titles but possess elite architectural intent.
4. **Explainability Drawer:** Side-drawer overlay generating a visual "Talent Genome" and explicit reasoning string for why the candidate was placed in their tier.
