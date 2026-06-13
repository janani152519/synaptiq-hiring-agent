# backend/db.py
import sqlite3
import json
import os
from backend.parser import JDParser
from backend.ranker import CandidateRanker

DB_PATH = os.path.join(os.path.dirname(__file__), "synaptiq.db")

class CandidateDatabase:
    @staticmethod
    def get_connection():
        return sqlite3.connect(DB_PATH)

    @staticmethod
    def init_db():
        conn = CandidateDatabase.get_connection()
        cursor = conn.cursor()
        
        # Create Candidates table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            anonymized_name TEXT,
            current_title TEXT,
            years_of_experience REAL,
            location TEXT,
            country TEXT,
            score REAL,
            reasoning TEXT,
            is_honeypot INTEGER,
            is_hidden_gem INTEGER,
            ats_rank INTEGER,
            raw_json TEXT
        )
        """)
        
        # Create Candidate Scores table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_scores (
            candidate_id TEXT PRIMARY KEY,
            semantic_score REAL,
            behavior_score REAL,
            growth_score REAL,
            leadership_score REAL,
            startup_score REAL,
            hidden_gem_score REAL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
        )
        """)

        # Create Job Descriptions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            blueprint_json TEXT
        )
        """)
        
        # Create views hidden_gems and fraud_profiles
        cursor.execute("DROP VIEW IF EXISTS hidden_gems")
        cursor.execute("""
        CREATE VIEW hidden_gems AS
        SELECT * FROM (
            SELECT * FROM candidates 
            WHERE is_hidden_gem = 1 AND is_honeypot = 0 
            ORDER BY score DESC, candidate_id ASC
        ) LIMIT 385
        """)
        
        cursor.execute("DROP VIEW IF EXISTS fraud_profiles")
        cursor.execute("""
        CREATE VIEW fraud_profiles AS
        SELECT * FROM candidates WHERE is_honeypot = 1
        """)
        
        conn.commit()
        conn.close()

    @staticmethod
    def load_candidates_from_jsonl(jsonl_path, limit=100000):
        """
        Ingests the top 100 ranked candidates and first N candidates from candidates.jsonl into the database.
        """
        CandidateDatabase.init_db()
        conn = CandidateDatabase.get_connection()
        cursor = conn.cursor()
        
        # Check if we already have candidates in the DB
        cursor.execute("SELECT COUNT(*) FROM candidates")
        count = cursor.fetchone()[0]
        if count >= 100000:
            print("Database already populated with 100,000 candidates.")
            conn.close()
            return

        # Clear existing data if it's a partial import
        cursor.execute("DELETE FROM candidates")
        cursor.execute("DELETE FROM candidate_scores")
        cursor.execute("DELETE FROM job_descriptions")
        conn.commit()

        print(f"Populating database from {jsonl_path}...")
        blueprint = JDParser.parse_jd()
        
        # Load and score all candidates
        candidates_data = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    c = json.loads(line)
                    candidates_data.append(c)
                except Exception:
                    continue

        print(f"Scoring {len(candidates_data)} candidates...")
        scored_candidates = []
        for c in candidates_data:
            res = CandidateRanker.rank_candidate(c, blueprint)
            
            # Compute static ATS score (keyword matches)
            skills_list = [s.get("name", "").lower() for s in c.get("skills", [])]
            required_keywords = [
                "embeddings", "sentence-transformers", "vector search", "dense retrieval",
                "vector database", "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss",
                "python", "ranking systems", "evaluation frameworks", "ndcg", "mrr", "map", "a/b testing"
            ]
            ats_score = sum(1 for kw in required_keywords if any(kw in s for s in skills_list))
            
            scored_candidates.append({
                "candidate": c,
                "result": res,
                "ats_score": ats_score
            })
            
        # Sort by ATS score to assign ats_rank
        print("Sorting for ATS ranks...")
        scored_candidates.sort(key=lambda x: (-x["ats_score"], x["candidate"]["candidate_id"]))
        for idx, item in enumerate(scored_candidates):
            item["ats_rank"] = idx + 1
            
        # Save blueprint
        cursor.execute(
            "INSERT INTO job_descriptions (title, company, blueprint_json) VALUES (?, ?, ?)",
            ("Senior AI Engineer", "Redrob AI", json.dumps(blueprint))
        )
        
        # Insert in bulk using transaction
        print("Bulk inserting into candidates...")
        candidates_tuples = []
        scores_tuples = []
        
        for item in scored_candidates:
            c = item["candidate"]
            res = item["result"]
            profile = c["profile"]
            sub = res["subscores"]
            
            candidates_tuples.append((
                c["candidate_id"],
                profile.get("anonymized_name"),
                profile.get("current_title"),
                profile.get("years_of_experience"),
                profile.get("location"),
                profile.get("country"),
                res["score"],
                res["reasoning"],
                1 if res["is_honeypot"] else 0,
                1 if res["is_hidden_gem"] else 0,
                item["ats_rank"],
                json.dumps(c)
            ))
            
            scores_tuples.append((
                c["candidate_id"],
                sub["semantic_score"],
                sub["behavior_score"],
                sub["growth_score"],
                sub["leadership_score"],
                sub["startup_score"],
                sub["hidden_gem_score"]
            ))
            
        cursor.executemany(
            """
            INSERT OR REPLACE INTO candidates 
            (candidate_id, anonymized_name, current_title, years_of_experience, location, country, score, reasoning, is_honeypot, is_hidden_gem, ats_rank, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            candidates_tuples
        )
        
        cursor.executemany(
            """
            INSERT OR REPLACE INTO candidate_scores
            (candidate_id, semantic_score, behavior_score, growth_score, leadership_score, startup_score, hidden_gem_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            scores_tuples
        )
        
        conn.commit()
        conn.close()
        print("Database population complete!")

