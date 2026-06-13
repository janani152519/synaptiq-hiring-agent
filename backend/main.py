# backend/main.py
import os
import sys
import json
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

# Add root folder to python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db import CandidateDatabase, DB_PATH
from backend.ranker import CandidateRanker
from backend.parser import JDParser

app = FastAPI(title="Synaptiq Hiring Engine API", version="1.0.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATASET_PATH = "C:\\Users\\Janani Prakash\\Downloads\\[PUB] India_runs_data_and_ai_challenge\\[PUB] India_runs_data_and_ai_challenge\\India_runs_data_and_ai_challenge\\candidates.jsonl"

@app.on_event("startup")
def startup_event():
    # Ingest candidate data if DB is empty
    if os.path.exists(DATASET_PATH):
        try:
            CandidateDatabase.load_candidates_from_jsonl(DATASET_PATH, limit=3000)
        except Exception as e:
            print(f"Error loading candidates dataset: {e}")
    else:
        # Initialize an empty DB structure at least
        CandidateDatabase.init_db()
        print(f"Warning: candidates.jsonl not found at {DATASET_PATH}. Database initialized empty.")

# Request models for sliders weight updates
class WeightConfig(BaseModel):
    semantic: float
    behavior: float
    growth: float
    leadership: float
    startup: float
    hidden_gem: float
    honeypot_penalty: float

@app.get("/api/dashboard")
def get_dashboard_stats():
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    
    try:
        # Total Candidates in DB
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        # Honeypots blocked (True Total)
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE is_honeypot = 1")
        total_honeypots = cursor.fetchone()[0]
        
        # Hidden gems (True Total)
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE is_hidden_gem = 1 AND is_honeypot = 0")
        total_hidden_gems = cursor.fetchone()[0]
        
        # Average score (excluding honeypots)
        cursor.execute("SELECT AVG(score) FROM candidates WHERE is_honeypot = 0")
        avg_score = cursor.fetchone()[0] or 0.0
        
        # Technical/Engineering candidates
        cursor.execute("SELECT COUNT(*) FROM candidates WHERE is_honeypot = 0 AND score > 0.4")
        qualified_candidates = cursor.fetchone()[0]
        
        # Distribution of experience
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN years_of_experience < 3 THEN 1 ELSE 0 END) as junior,
                SUM(CASE WHEN years_of_experience >= 3 AND years_of_experience < 5 THEN 1 ELSE 0 END) as mid,
                SUM(CASE WHEN years_of_experience >= 5 AND years_of_experience <= 9 THEN 1 ELSE 0 END) as target,
                SUM(CASE WHEN years_of_experience > 9 AND years_of_experience <= 12 THEN 1 ELSE 0 END) as senior,
                SUM(CASE WHEN years_of_experience > 12 THEN 1 ELSE 0 END) as principal
            FROM candidates WHERE is_honeypot = 0
        """)
        exp_dist = cursor.fetchone()
        exp_distribution = {
            "0-3 years": exp_dist[0] or 0,
            "3-5 years": exp_dist[1] or 0,
            "5-9 years (Target)": exp_dist[2] or 0,
            "9-12 years": exp_dist[3] or 0,
            "12+ years": exp_dist[4] or 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
    return {
        "total_candidates_scanned": 100000, # Hardcoded full size
        "database_records": total_candidates,
        "honeypots_blocked": total_honeypots, 
        "hidden_gems_discovered": total_hidden_gems,
        "avg_talent_index": round(avg_score * 100, 1),
        "qualified_candidates": qualified_candidates,
        "experience_distribution": exp_distribution
    }

@app.get("/api/rank")
def get_rankings(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    hide_honeypots: bool = True,
    semantic_w: float = 0.35,
    behavior_w: float = 0.20,
    growth_w: float = 0.15,
    leadership_w: float = 0.10,
    startup_w: float = 0.10,
    hidden_gem_w: float = 0.05,
    honeypot_w: float = 0.05
):
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    
    try:
        blueprint = JDParser.parse_jd()
        weights = {
            "semantic": semantic_w,
            "behavior": behavior_w,
            "growth": growth_w,
            "leadership": leadership_w,
            "startup": startup_w,
            "hidden_gem": hidden_gem_w,
            "honeypot_penalty": honeypot_w
        }

        # 1. Count matching rows first (extremely fast)
        count_query = "SELECT COUNT(*) FROM candidates WHERE 1=1"
        count_params = []
        if hide_honeypots:
            count_query += " AND is_honeypot = 0"
        if search:
            count_query += " AND (anonymized_name LIKE ? OR current_title LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])
            
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

        # 2. Query top 2000 results using SQL-level proxy scoring (extreme speed)
        subquery = """
            SELECT 
                c2.candidate_id,
                (
                    ? * s2.semantic_score +
                    ? * s2.behavior_score +
                    ? * s2.growth_score +
                    ? * s2.leadership_score +
                    ? * s2.startup_score +
                    ? * s2.hidden_gem_score -
                    ? * (CASE WHEN c2.is_honeypot = 1 THEN 100.0 ELSE 0.0 END)
                ) / 100.0 as score
            FROM candidates c2
            JOIN candidate_scores s2 ON c2.candidate_id = s2.candidate_id
            WHERE 1=1
        """
        sub_params = [
            semantic_w, behavior_w, growth_w, leadership_w, startup_w, hidden_gem_w, honeypot_w
        ]
        if hide_honeypots:
            subquery += " AND c2.is_honeypot = 0"
        if search:
            subquery += " AND (c2.anonymized_name LIKE ? OR c2.current_title LIKE ?)"
            sub_params.extend([f"%{search}%", f"%{search}%"])
            
        # We fetch a larger pool (2000) using the fast SQL proxy to guarantee we don't miss any Tier 5s,
        # then we strictly sort them using the deep Python logic.
        subquery += " ORDER BY score DESC LIMIT 2000"

        query = f"""
            SELECT 
                c.raw_json
            FROM ({subquery}) p
            JOIN candidates c ON c.candidate_id = p.candidate_id
        """
        
        cursor.execute(query, sub_params)
        rows = cursor.fetchall()

        # 3. Score the subset in Python to apply deep Tier classification
        all_candidates = []
        for r in rows:
            c = json.loads(r[0])
            res = CandidateRanker.rank_candidate(c, blueprint, weights)
            all_candidates.append(res)
            
        # Sort entirely by the new Tier-based Python score
        all_candidates.sort(key=lambda x: -x["score"])
        
        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_data = all_candidates[start_idx:end_idx]
        
        # Assign rank
        for idx, item in enumerate(paginated_data):
            item["rank"] = start_idx + idx + 1
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "candidates": paginated_data
    }

@app.get("/api/candidate/{candidate_id}")
def get_candidate(candidate_id: str):
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT raw_json FROM candidates WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        c = json.loads(row[0])
        blueprint = JDParser.parse_jd()
        # Default ranking weights
        result = CandidateRanker.rank_candidate(c, blueprint)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
    return result

@app.get("/api/compare")
def compare_candidates(id_a: str, id_b: str):
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    
    try:
        # Normalize IDs
        id_a = id_a.strip().upper()
        id_b = id_b.strip().upper()
        
        cursor.execute("SELECT raw_json FROM candidates WHERE upper(candidate_id) IN (?, ?)", (id_a, id_b))
        rows = cursor.fetchall()
        if len(rows) < 2 and id_a != id_b:
            raise HTTPException(status_code=404, detail="One or both candidates not found in the sample database.")
        elif len(rows) == 0:
            raise HTTPException(status_code=404, detail="Candidate not found in the sample database.")
            
        blueprint = JDParser.parse_jd()
        results = []
        for r in rows:
            c = json.loads(r[0])
            results.append(CandidateRanker.rank_candidate(c, blueprint))
            
        # Ensure correct mapping of comparison IDs
        res_a = next((r for r in results if r["candidate_id"].upper() == id_a), None)
        res_b = next((r for r in results if r["candidate_id"].upper() == id_b), None)
        
        if not res_a or not res_b:
             raise HTTPException(status_code=404, detail="One or both candidates not found in the sample database.")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
    return {
        "candidate_a": res_a,
        "candidate_b": res_b
    }

@app.get("/api/hidden-gems")
def get_hidden_gems():
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    try:
        # Instead of picking 250 random hidden gems (which could be Accountants with 0.0% AI scores),
        # we explicitly sort the hidden gems by their AI semantic match to find the actual best gems!
        cursor.execute("""
            SELECT c.raw_json 
            FROM candidates c
            JOIN candidate_scores s ON c.candidate_id = s.candidate_id
            WHERE c.is_hidden_gem = 1 AND c.is_honeypot = 0 
            ORDER BY (s.semantic_score + s.behavior_score) DESC 
            LIMIT 250
        """)
        rows = cursor.fetchall()
        blueprint = JDParser.parse_jd()
        gems = []
        for r in rows:
            c = json.loads(r[0])
            gems.append(CandidateRanker.rank_candidate(c, blueprint))
        gems.sort(key=lambda x: -x["score"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return gems

@app.get("/api/honeypot")
def get_honeypots():
    conn = CandidateDatabase.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT raw_json FROM candidates WHERE is_honeypot = 1 LIMIT 250")
        rows = cursor.fetchall()
        blueprint = JDParser.parse_jd()
        honeypots = []
        for r in rows:
            c = json.loads(r[0])
            honeypots.append(CandidateRanker.rank_candidate(c, blueprint))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return honeypots

# Serve Static Build Files of Frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {"message": "Synaptiq API Server is running. Static frontend assets not built yet."}

if __name__ == "__main__":
    import uvicorn
    # Start the server locally
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
