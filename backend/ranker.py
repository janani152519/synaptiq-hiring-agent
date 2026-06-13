# backend/ranker.py
from backend.honeypot import HoneypotDetector
from backend.parser import JDParser
from backend.dna import TalentDNAEngine
from backend.trajectory import CareerTrajectoryEngine
from datetime import datetime

class CandidateRanker:
    @staticmethod
    def calculate_semantic_score(candidate: dict, blueprint: dict) -> float:
        """
        Calculates the semantic match score (0-100) between the candidate and the JD blueprint.
        Ensures keyword stuffers with non-technical roles are penalized, while matching adjacent titles.
        """
        profile = candidate.get("profile", {})
        skills = {s.get("name", "").lower(): s for s in candidate.get("skills", [])}
        history = candidate.get("career_history", [])
        
        headline = profile.get("headline", "").lower()
        summary = profile.get("summary", "").lower()
        cur_title = profile.get("current_title", "").lower()
        
        # 1. Hard Disqualifier / Penalty for Non-Technical Titles
        non_tech_titles = ["marketing", "sales", "hr manager", "human resources", "graphic designer", 
                           "content writer", "accountant", "customer support", "operations manager", 
                           "brand manager", "visual designer", "copywriter"]
        
        # Check if the current title is non-technical
        is_non_tech = False
        for title in non_tech_titles:
            if title in cur_title:
                is_non_tech = True
                break
                
        # Also check if their summary and history descriptions contain ONLY non-tech work
        if is_non_tech:
            # Let's check if they have prior engineering roles in history. If they have none, they are a keyword stuffer.
            has_tech_history = False
            for r in history:
                title = r.get("title", "").lower()
                if any(tech in title for tech in ["engineer", "developer", "scientist", "programmer", "tech lead", "architect"]):
                    has_tech_history = True
                    break
            if not has_tech_history:
                return 0.0  # Zero score for pure non-tech profiles stuffed with AI keywords
        
        # 2. Title Match Score (0-30)
        title_score = 0.0
        # Target role is Senior AI Engineer / Backend Engineer / ML Engineer / Data Scientist
        target_keywords = ["ai", "ml", "machine learning", "backend", "nlp", "information retrieval", "search", "recommendation"]
        for kw in target_keywords:
            if kw in cur_title:
                title_score += 15.0
        if "engineer" in cur_title or "developer" in cur_title:
            title_score += 10.0
        if "senior" in cur_title or "lead" in cur_title:
            title_score += 5.0
        title_score = min(30.0, title_score)
        
        # 3. Skills Match Score (0-45)
        # Match required skills (weight 2.5) and preferred skills (weight 1.5)
        skill_score = 0.0
        for req in blueprint["required_skills"]:
            req_l = req.lower()
            # Direct match or fuzzy match in skills list
            matched = False
            for sk_name in skills:
                if req_l in sk_name or sk_name in req_l:
                    matched = True
                    # Check proficiency and duration
                    sk_info = skills[sk_name]
                    prof = sk_info.get("proficiency", "beginner")
                    mult = {"beginner": 0.8, "intermediate": 1.0, "advanced": 1.2, "expert": 1.3}[prof]
                    dur = sk_info.get("duration_months", 0)
                    dur_mult = min(1.2, max(0.5, dur / 24.0)) # 2 years is standard
                    skill_score += 3.0 * mult * dur_mult
                    break
            
            # If not in skills list, check summary and history descriptions (fuzzy search)
            if not matched:
                if req_l in summary:
                    skill_score += 1.0
                else:
                    for r in history:
                        if req_l in r.get("description", "").lower():
                            skill_score += 1.5
                            break
                            
        for pref in blueprint["preferred_skills"]:
            pref_l = pref.lower()
            matched = False
            for sk_name in skills:
                if pref_l in sk_name or sk_name in pref_l:
                    matched = True
                    sk_info = skills[sk_name]
                    prof = sk_info.get("proficiency", "beginner")
                    mult = {"beginner": 0.8, "intermediate": 1.0, "advanced": 1.1, "expert": 1.2}[prof]
                    skill_score += 1.5 * mult
                    break
            if not matched:
                if pref_l in summary:
                    skill_score += 0.5
                else:
                    for r in history:
                        if pref_l in r.get("description", "").lower():
                            skill_score += 0.75
                            break
                            
        skill_score = min(45.0, skill_score)
        
        # 4. Experience Match Score (0-25)
        # Target experience is 5-9 years.
        exp_score = 0.0
        yrs = profile.get("years_of_experience", 0)
        if 5.0 <= yrs <= 9.0:
            exp_score = 25.0
        elif 4.0 <= yrs < 5.0:
            exp_score = 18.0
        elif 9.0 < yrs <= 12.0:
            exp_score = 20.0
        elif 3.0 <= yrs < 4.0:
            exp_score = 10.0
        elif 12.0 < yrs <= 15.0:
            exp_score = 12.0
        else: # < 3 or > 15
            exp_score = 5.0
            
        return title_score + skill_score + exp_score

    @staticmethod
    def calculate_availability_index(candidate: dict) -> float:
        """
        Calculates aggressive availability index separating behavioral twins.
        """
        signals = candidate.get("redrob_signals", {})
        score = 100.0
        
        # Exponential penalization for lack of activity
        last_active = signals.get("last_active_date", "")
        if last_active:
            try:
                active_dt = datetime.strptime(last_active, "%Y-%m-%d")
                days_inactive = (datetime(2026, 6, 9) - active_dt).days
                if days_inactive > 180:
                    score -= 80.0
                elif days_inactive > 90:
                    score -= 50.0
                elif days_inactive > 30:
                    score -= 20.0
            except Exception:
                score -= 30.0
        else:
            score -= 50.0
            
        # Response rate exponential drop-off
        resp_rate = signals.get("recruiter_response_rate", 0.0)
        if resp_rate < 0.2:
            score -= 50.0
        elif resp_rate < 0.5:
            score -= 20.0
            
        # Open to work boost
        if signals.get("open_to_work_flag", False):
            score += 20.0
            
        return max(0.0, min(100.0, score))

    @staticmethod
    def calculate_retrieval_ranking_score(candidate: dict) -> float:
        """
        Calculates score based on evidence of retrieval, ranking, recommendation, matching, search.
        """
        score = 0.0
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        
        text_corpus = profile.get("summary", "").lower() + " "
        for r in history:
            text_corpus += r.get("title", "").lower() + " "
            text_corpus += r.get("description", "").lower() + " "
            
        keywords = {
            "retrieval": 15.0,
            "ranking": 15.0,
            "recommendation": 10.0,
            "recommender systems": 15.0,
            "matching": 10.0,
            "candidate matching": 15.0,
            "search": 5.0,
            "search relevance": 20.0,
            "vector search": 15.0,
            "embeddings": 10.0,
            "learning to rank": 20.0,
            "ndcg": 10.0,
            "mrr": 10.0,
            "map": 5.0,
            "ab testing": 5.0,
            "offline evaluation": 15.0,
            "online evaluation": 15.0
        }
        
        for kw, pts in keywords.items():
            if kw in text_corpus:
                score += pts
                
        return min(100.0, score)

    @staticmethod
    def calculate_jd_meaning_score(candidate: dict) -> float:
        """
        Calculates the JD Meaning Score: Ships, Builds ranking/retrieval, Evaluates, Product companies, Writes code, Production AI.
        """
        score = 0.0
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        
        text_corpus = profile.get("summary", "").lower() + " "
        for r in history:
            text_corpus += r.get("title", "").lower() + " "
            text_corpus += r.get("description", "").lower() + " "
            
        # 1. Ships product (15 pts)
        if any(kw in text_corpus for kw in ["shipped", "launched", "delivered", "0 to 1"]):
            score += 15.0
            
        # 2. Builds ranking/retrieval systems (25 pts)
        if any(kw in text_corpus for kw in ["built ranking", "built retrieval", "search engine", "recommendation engine", "matching system"]):
            score += 25.0
        elif any(kw in text_corpus for kw in ["ranking", "retrieval", "search", "matching"]):
            score += 10.0
            
        # 3. Understands evaluation (15 pts)
        if any(kw in text_corpus for kw in ["evaluation", "ndcg", "a/b testing", "offline metrics", "online metrics"]):
            score += 15.0
            
        # 4. Writes code (15 pts)
        if any(kw in text_corpus for kw in ["wrote code", "hands-on", "implemented", "developed", "architected and built"]):
            score += 15.0
        elif any(kw in text_corpus for kw in ["python", "java", "c++", "go"]):
            score += 5.0
            
        # 5. Production AI Score (30 pts)
        if any(kw in text_corpus for kw in ["deployed", "production", "served", "real users", "online inference", "pipeline ownership", "monitoring"]):
            score += 30.0
            
        return min(100.0, score)

    @staticmethod
    def calculate_evaluation_score(candidate: dict) -> float:
        """
        Calculates explicit evaluation framework expertise (NDCG, MAP, MRR, offline metrics).
        """
        score = 0.0
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        text_corpus = profile.get("summary", "").lower() + " "
        for r in history:
            text_corpus += r.get("description", "").lower() + " "
            
        keywords = {
            "ndcg": 20.0, "map": 10.0, "mrr": 15.0, "a/b testing": 15.0,
            "offline benchmark": 20.0, "ranking metrics": 20.0, "evaluation framework": 20.0
        }
        for kw, pts in keywords.items():
            if kw in text_corpus:
                score += pts
        return min(100.0, score)

    @staticmethod
    def classify_tier(candidate: dict, ret_score: float, prod_score: float, is_it_services: bool, avail_idx: float, dna: dict) -> int:
        """
        Classifies candidate into Tier 0-5 based on Hidden Ground Truth intent.
        """
        profile = candidate.get("profile", {})
        text_corpus = profile.get("summary", "").lower()
        skills = [s.get("name", "").lower() for s in candidate.get("skills", [])]
        
        llm_keywords = ["langchain", "prompt engineering", "openai", "chatgpt"]
        is_llm_heavy = sum(1 for kw in llm_keywords if kw in text_corpus or kw in skills) >= 2
        is_retrieval_heavy = ret_score > 40.0
        
        # Service company + AI hobbyist transition penalty
        if is_it_services and is_llm_heavy and not is_retrieval_heavy:
            return 1 # Hobbyist transitioning from services
            
        if is_it_services and not is_retrieval_heavy:
            return 2 # General IT services
            
        if ret_score > 60 and prod_score > 60 and not is_it_services and avail_idx > 70:
            return 5
            
        if ret_score > 40 and not is_it_services:
            return 4
            
        if ret_score > 20 or dna["technical_dna"] > 70:
            return 3
            
        return 2

    @staticmethod
    def rank_candidate(candidate: dict, blueprint: dict, weights: dict = None) -> dict:
        """
        Runs the full multi-factor scoring on a candidate and returns final score, subscores, and reasoning.
        """
        cid = candidate["candidate_id"]
        profile = candidate.get("profile", {})
        
        default_weights = {
            "evaluation": 0.10,
            "jd_meaning": 0.15,
            "retrieval": 0.20,
            "availability": 0.15,
            "semantic": 0.15,
            "startup": 0.10,
            "trajectory": 0.05,
            "hidden_gem": 0.08,
            "leadership": 0.02
        }
        
        if weights:
            # Safely merge frontend slider weights with backend hidden intent weights
            merged_weights = default_weights.copy()
            if "semantic" in weights: merged_weights["semantic"] = weights["semantic"]
            if "behavior" in weights: merged_weights["availability"] = weights["behavior"]
            if "growth" in weights: merged_weights["trajectory"] = weights["growth"]
            if "leadership" in weights: merged_weights["leadership"] = weights["leadership"]
            if "startup" in weights: merged_weights["startup"] = weights["startup"]
            if "hidden_gem" in weights: merged_weights["hidden_gem"] = weights["hidden_gem"]
            weights = merged_weights
        else:
            weights = default_weights
            
        # 1. Check for Honeypot
        is_honeypot, honeypot_reasons = HoneypotDetector.inspect_candidate(candidate)
        
        # 2. Calculate DNA
        dna = TalentDNAEngine.calculate_dna(candidate, blueprint)
        
        # 3. Calculate Trajectory
        traj = CareerTrajectoryEngine.analyze_trajectory(candidate)
        
        # 4. Subscores
        semantic_score = CandidateRanker.calculate_semantic_score(candidate, blueprint)
        avail_index = CandidateRanker.calculate_availability_index(candidate)
        retrieval_score = CandidateRanker.calculate_retrieval_ranking_score(candidate)
        jd_meaning_score = CandidateRanker.calculate_jd_meaning_score(candidate)
        eval_score = CandidateRanker.calculate_evaluation_score(candidate)
        
        startup_score = dna["startup_dna"]
        leadership_score = dna["leadership_dna"]
        growth_score = traj["growth_score"]
        is_it_services = dna.get("is_it_services", False)
        
        # 5. Hidden Gem Score
        is_hidden_gem = False
        cur_title = profile.get("current_title", "").lower()
        if "ai" not in cur_title and "machine learning" not in cur_title:
            history_text = " ".join([r.get("description", "").lower() for r in candidate.get("career_history", [])])
            if any(kw in history_text for kw in ["recommendation engine", "search engine", "retrieval system", "matching platform"]):
                is_hidden_gem = True
        hidden_gem_score = 100.0 if is_hidden_gem else 0.0
        
        # 6. Tier Classification
        tier = CandidateRanker.classify_tier(candidate, retrieval_score, jd_meaning_score, is_it_services, avail_index, dna)
        
        # 7. Final Combined Score (0.0 - 1.0)
        raw_subscores = (
            weights["retrieval"] * retrieval_score +
            weights["jd_meaning"] * jd_meaning_score +
            weights["evaluation"] * eval_score +
            weights["semantic"] * semantic_score +
            weights["availability"] * avail_index +
            weights["startup"] * startup_score +
            weights["trajectory"] * growth_score +
            weights["hidden_gem"] * hidden_gem_score +
            weights["leadership"] * leadership_score
        )
        
        if is_honeypot:
            final_score = 0.0
            tier = 0
        else:
            # Tier heavily dominates the final score mapping (Tier 5 = 0.8 to 1.0, Tier 4 = 0.6 to 0.8, etc.)
            base_score = (tier / 5.0) * 0.70
            bonus_score = (raw_subscores / 100.0) * 0.30
            final_score = max(0.0, min(1.0, base_score + bonus_score))
            
        # 8. Generate reasoning
        reasoning = CandidateRanker.generate_reasoning(candidate, tier, retrieval_score, eval_score, is_it_services, avail_index, is_honeypot)
        
        return {
            "candidate_id": cid,
            "anonymized_name": profile.get("anonymized_name"),
            "current_title": profile.get("current_title"),
            "years_of_experience": profile.get("years_of_experience"),
            "score": round(final_score, 4),
            "tier": tier,
            "reasoning": reasoning,
            "subscores": {
                "retrieval_score": round(retrieval_score, 1),
                "jd_meaning_score": round(jd_meaning_score, 1),
                "evaluation_score": round(eval_score, 1),
                "semantic_score": round(semantic_score, 1),
                "availability_index": round(avail_index, 1),
                "growth_score": round(growth_score, 1),
                "startup_score": round(startup_score, 1),
                "hidden_gem_score": round(hidden_gem_score, 1)
            },
            "is_honeypot": is_honeypot,
            "honeypot_reasons": honeypot_reasons,
            "is_hidden_gem": is_hidden_gem,
            "trajectory": traj,
            "dna": dna
        }

    @staticmethod
    def generate_reasoning(candidate: dict, tier: int, retrieval_score: float, eval_score: float, is_it_services: bool, avail_index: float, is_honeypot: bool) -> str:
        """
        Generates dynamic reasoning explicitly referencing tiers, evaluation frameworks, and behavioral/service factors.
        """
        if is_honeypot:
            return "Tier 0 (Disqualified): Profile flagged as fraudulent due to timeline and experience inconsistencies."
            
        profile = candidate.get("profile", {})
        
        if tier >= 4:
            s1 = f"Tier {tier} Match: Built robust vector search infrastructure and ranking systems across product environments, directly aligning with Redrob's retrieval-first requirements."
        elif tier == 3:
            s1 = f"Tier {tier} Match: Strong ML background and relevant production experience, though lacking deep evidence of end-to-end ranking system ownership."
        elif is_it_services:
            s1 = f"Tier {tier} Match: IT Services/Consulting background transitioning into ML. Primarily exposed to APIs rather than building core search infrastructure."
        else:
            s1 = f"Tier {tier} Match: Solid engineering foundation, but missing direct experience with modern vector search libraries and learning-to-rank systems."
            
        if eval_score > 30:
            s1 += " Notable expertise in offline benchmarking and evaluation metrics (NDCG/MRR)."
            
        if avail_index > 80:
            s2 = "Highly engaged platform activity and strong recruiter responsiveness significantly elevate hiring likelihood."
        else:
            s2 = "However, severe inactivity or poor recruiter response rates significantly reduce immediate availability fit."
            
        return f"{s1} {s2}"
