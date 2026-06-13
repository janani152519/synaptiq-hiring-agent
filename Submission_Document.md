# India.Runs Data & AI Challenge - Submission Document

**Team Name:** Team 1125 (or Redrob 1125)
**Team Leader Name:** Janani Prakash
**Problem Statement:** Traditional ATS systems rely on superficial keyword matching, producing hundreds of "maybe" candidates who know basic AI tools (like ChatGPT/LangChain), rather than finding the deeply technical engineers who have actually built complex production systems (Retrieval, Ranking, Recommendation). The challenge requires a system that discovers the "Hidden Ground Truth" of what makes a candidate truly elite.

---

## Solution Overview
**What is your proposed solution?**
Synaptiq is a high-speed, intent-driven candidate evaluation engine. Instead of a linear keyword-scoring model, Synaptiq uses a deeply engineered **Tier-Based Classification System (Tiers 0-5)** that mimics the exact cognitive process of an elite technical recruiter. It orchestrates a massive SQLite database through a high-performance FastAPI backend, surfaced via an interactive React glassmorphism dashboard that allows recruiters to dynamically adjust algorithm weights on the fly.

**What differentiates your approach from traditional candidate matching systems?**
1. **Tiered Truth Over Linear Scoring:** We abandon standard 0-100 scoring. We classify candidates into explicit Relevance Tiers (e.g., Tier 5 = Built Production Retrieval Systems; Tier 1 = Basic LLM Wrapper). 
2. **Behavioral Twin Separation:** When technical skills tie, we use an exponential **Availability Index** to rank candidates based on their recency (penalizing candidates inactive for >90 days).
3. **Anti-Fraud Honeypot:** Our `HoneypotDetector` algorithm actively hunts and blocks "Skill Inflation" and impossible chronological career jumps.

---

## JD Understanding & Candidate Evaluation
**What are the key requirements extracted from the JD?**
- **Primary Technical Intent:** Building Search, Retrieval, Ranking, Matching, and Recommendation systems.
- **Evaluation Metrics Mastery:** Practical knowledge of offline evaluation frameworks (NDCG, MAP, MRR, A/B Testing).
- **Cultural Fit & Background:** A strong preference for Product/Startup companies, accompanied by a harsh penalty for pure IT Service conglomerates (e.g., TCS, Infosys, Wipro).

**Which candidate signals are most important for determining relevance? / How does your solution evaluate candidate fit beyond keyword matching?**
We map candidates using a multi-dimensional "Talent DNA Vector." A candidate mentioning "AI" scores low; a candidate detailing "Implemented FAISS for vector retrieval improving NDCG by 12%" scores a Tier 5. We look for concrete architectural signals over generic tool names. 

---

## Ranking Methodology
**How does your system retrieve, score, and rank candidates?**
We use a highly optimized Two-Stage Funnel:
1. **Stage 1 (SQL Proxy Sort):** Using SQLite deferred joins, we instantly proxy-score and fetch the top 2,000 candidates out of 100,000 in <50ms.
2. **Stage 2 (Deep Python Orchestration):** The `CandidateRanker` ingests this curated subset, applies the rigid 0-5 Tier Classification, merges it with the dynamic recruiter weights from the frontend sliders, and sorts the final list.

**What models, algorithms, or heuristics are used?**
- **Cosine Similarity Vectors:** Used to calculate the `Talent DNA` match across 8 different dimensions (Technical, Leadership, Startup, etc.).
- **Exponential Decay Functions:** Used in the `Availability Index` to drastically drop scores for candidates who haven't responded to emails or been active recently.
- **Rule-Based Heuristic Classifiers:** Used for rigid Tier placement and Service Company penalization.

**How are multiple candidate signals combined into a final ranking?**
The final score is a hybrid fusion: **70% driven by the hard Tier Classification** (ensuring a Tier 4 candidate will always beat a Tier 3 candidate regardless of keyword density), and **30% driven by the dynamically weighted Subscores** (Semantic, Availability, Trajectory, Evaluation).

---

## Explainability & Data Validation
**How are ranking decisions explained?**
Our frontend features an interactive "Explainability Drawer." Clicking "Explain" on any candidate generates a deterministic breakdown of their exact Talent DNA via a dynamic Radar Chart, accompanied by a generated sentence detailing exactly *why* they were placed in their specific Tier.

**How do you prevent hallucinations or unsupported justifications?**
We DO NOT use Generative LLMs to write the justifications on the fly. Instead, our `Dynamic Reasoning Generator` algorithm pieces together text explicitly based on the boolean flags and metrics the candidate passed (e.g., "Placed in Tier 5 because candidate demonstrated Evaluation Metrics (NDCG) and Production Retrieval").

**How does your solution handle inconsistent, low-quality, or suspicious profiles?**
The `HoneypotDetector.py` module evaluates every candidate against strict logical boundaries. It flags:
1. **Skill Inflation:** Candidates listing 15+ "Expert" skills but having 0 endorsements.
2. **Title Jumping:** Candidates claiming to go from "Junior Engineer" to "Principal Architect" in 1 year.
These candidates are instantly given a `-100` penalty, removed from rankings, and isolated in a dedicated "Honeypots" dashboard tab.

---

## End-to-End Workflow
**What is the complete workflow from JD input to ranked candidate output?**
1. Data ingested and vectorized into `synaptiq.db`.
2. Recruiter opens the React Dashboard, viewing macro-analytics (Experience distribution, total gems found).
3. Recruiter accesses the **Talent Rankings** tab and adjusts the importance of "Behavioral Signals" vs "Startup Readiness".
4. The React app `fetch` calls the FastAPI backend.
5. The backend runs the Two-Stage Funnel (SQL Proxy -> Deep Python Tiering).
6. The frontend renders the paginated, explainable Top Candidates list instantly.

---

## System Architecture
- **Data Layer:** SQLite Database (`synaptiq.db`) pre-populated with 100,000 JSON blobs.
- **Compute / Backend Layer:** Python FastAPI running the custom `TalentDNAEngine`, `CandidateRanker`, and `HoneypotDetector`.
- **Presentation Layer:** React + TypeScript via Vite, styled with custom CSS for a premium Glassmorphism UI, utilizing `Chart.js` for data visualization.

---

## Results & Performance
**What results or insights demonstrate ranking quality?**
Our system successfully identified ~10,600 "Hidden Gems"—candidates lacking generic "AI Engineer" titles but possessing the deep underlying architectural skills the JD demanded. Our strict tiered approach ensures the Top 10 are exclusively candidates who have built production retrieval/ranking systems. 

**How does your solution meet the challenge's runtime and compute constraints?**
Instead of processing all 100k candidates sequentially in Python (which causes 30+ second timeouts), we engineered a Deferred Join SQL query. This offloads the heavy filtering to the C-based SQLite engine, retrieving the Top 2,000 in under **50ms**. The deep Python classification on the subset takes under **400ms**, delivering real-time UX to the frontend.

---

## Technologies Used
- **Backend:** Python 3, FastAPI (for async, high-performance API routing), Uvicorn.
- **Database:** SQLite (Lightweight, zero-config, highly performant for reads).
- **Frontend:** React, TypeScript, Vite (Lightning-fast HMR).
- **Data Viz:** Chart.js / `react-chartjs-2` (For complex multi-dimensional Radar charts).
- **Why?** This stack avoids expensive external API calls, requires no cloud GPU provisioning, and runs entirely locally in milliseconds, adhering strictly to the ideals of a reproducible hackathon submission.
