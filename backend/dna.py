# backend/dna.py
class TalentDNAEngine:
    @staticmethod
    def calculate_dna(candidate: dict, blueprint: dict) -> dict:
        """
        Generates a talent genome score on seven key dimensions (0-100).
        """
        profile = candidate.get("profile", {})
        skills = candidate.get("skills", [])
        history = candidate.get("career_history", [])
        signals = candidate.get("redrob_signals", {})
        edu = candidate.get("education", [])
        
        # 1. Technical DNA
        # Based on skills count, endorsements, proficiency levels, and assessments
        tech_score = 40.0
        matching_skills = 0
        total_endorsements = 0
        for s in skills:
            name = s.get("name", "").lower()
            # Check matching against blueprint
            is_match = False
            for req in blueprint["required_skills"] + blueprint["preferred_skills"]:
                if req.lower() in name or name in req.lower():
                    is_match = True
            
            if is_match:
                matching_skills += 1
                prof = s.get("proficiency", "beginner")
                prof_weight = {"beginner": 1.0, "intermediate": 1.2, "advanced": 1.4, "expert": 1.6}[prof]
                tech_score += 4.0 * prof_weight
                total_endorsements += s.get("endorsements", 0)
        
        # Add assessments bonus
        assessments = signals.get("skill_assessment_scores", {})
        if assessments:
            avg_assess = sum(assessments.values()) / len(assessments)
            tech_score += avg_assess * 0.15
        
        # Limit to 100
        tech_score = min(100.0, tech_score + min(10.0, total_endorsements * 0.05))

        # 2. Leadership DNA
        # Titles like lead, architect, manager, or description text matches
        lead_score = 45.0
        lead_terms = blueprint["leadership_keywords"]
        for r in history:
            title = r.get("title", "").lower()
            desc = r.get("description", "").lower()
            for term in lead_terms:
                if term in title:
                    lead_score += 15.0
                elif term in desc:
                    lead_score += 3.0
        
        # Experience factor
        yrs = profile.get("years_of_experience", 0)
        if yrs > 8:
            lead_score += 10.0
        elif yrs >= 5:
            lead_score += 5.0
        lead_score = min(100.0, lead_score)

        # 3. Innovation DNA
        # Based on github score, open-source keywords, and certifications
        inno_score = 40.0
        gh = signals.get("github_activity_score", -1)
        if gh > 0:
            inno_score += gh * 0.4
        
        # Project keywords in history description
        for r in history:
            desc = r.get("description", "").lower()
            if any(term in desc for term in ["innovation", "patents", "open-source", "research", "shipped new", "designed"]):
                inno_score += 4.0
        
        inno_score = min(100.0, inno_score)

        # 4. Communication DNA
        # Languages, connections, profile completeness
        comm_score = 50.0
        completeness = signals.get("profile_completeness_score", 50.0)
        comm_score += (completeness - 50.0) * 0.3
        
        connections = signals.get("connection_count", 0)
        comm_score += min(15.0, connections * 0.03)
        
        languages = candidate.get("languages", [])
        comm_score += len(languages) * 4.0
        comm_score = min(100.0, comm_score)

        # 5. Learning DNA
        # Degrees, Tier of education, and certifications
        learn_score = 50.0
        for e in edu:
            tier = e.get("tier", "unknown")
            tier_bonus = {"tier_1": 20.0, "tier_2": 10.0, "tier_3": 5.0}.get(tier, 0.0)
            learn_score += tier_bonus
            
            degree = e.get("degree", "").lower()
            if "phd" in degree or "doctor" in degree:
                learn_score += 15.0
            elif "m" in degree or "master" in degree: # M.Tech, M.S.
                learn_score += 8.0
        
        certifications = candidate.get("certifications", [])
        learn_score += len(certifications) * 5.0
        learn_score = min(100.0, learn_score)

        # 6. Startup DNA
        # Product startups vs consulting tenure
        startup_score = 50.0
        total_months = sum(r.get("duration_months", 0) for r in history)
        if total_months > 0:
            startup_months = 0
            consulting_months = 0
            for r in history:
                comp = r.get("company", "").lower()
                dur = r.get("duration_months", 0)
                is_prod = any(prod.lower() in comp for prod in blueprint["product_companies"])
                is_cons = any(cons.lower() in comp for cons in blueprint["consulting_firms"])
                
                if is_prod:
                    startup_months += dur
                elif is_cons:
                    consulting_months += dur
                    
            startup_ratio = startup_months / total_months
            consulting_ratio = consulting_months / total_months
            startup_score += startup_ratio * 40.0
            startup_score -= consulting_ratio * 60.0  # Massive penalty for pure IT services
            
            # Check company size sweet spot for Startups
            cur_size = profile.get("current_company_size", "")
            if cur_size in ["1-10", "11-50"]:
                startup_score += 15.0
            elif cur_size in ["51-200"]:
                startup_score += 10.0
                
            # Check for ownership and shipped products in descriptions
            for r in history:
                desc = r.get("description", "").lower()
                if any(kw in desc for kw in ["ownership", "owned", "shipped", "built from scratch", "0 to 1", "fast-paced"]):
                    startup_score += 5.0
        
        startup_score = max(0.0, min(100.0, startup_score))
        
        # Determine if profile is predominantly IT services
        is_it_services = False
        if total_months > 0 and (consulting_months / total_months) > 0.6:
            is_it_services = True

        # 7. Domain DNA
        # HR-Tech / NLP / Vector search relevance
        domain_score = 30.0
        for r in history:
            desc = r.get("description", "").lower()
            title = r.get("title", "").lower()
            for keyword in ["search", "nlp", "ranking", "matching", "hr-tech", "recruiting", "talent", "recommendation", "embeddings", "vector"]:
                if keyword in desc:
                    domain_score += 8.0
                if keyword in title:
                    domain_score += 15.0
        domain_score = min(100.0, domain_score)

        # Overall Index
        overall = (
            tech_score * 0.30 +
            startup_score * 0.15 +
            lead_score * 0.15 +
            domain_score * 0.15 +
            inno_score * 0.10 +
            learn_score * 0.08 +
            comm_score * 0.07
        )

        # 8. Career DNA Vector Matching (Reverse-engineered JD Intent)
        jd_dna = {
            "retrieval": 1.0,
            "ranking": 1.0,
            "evaluation": 1.0,
            "production": 1.0,
            "product_company": 1.0,
            "startup": 0.8,
            "leadership": 0.5,
            "llm": 0.3
        }
        
        full_text = profile.get("summary", "").lower() + " " + " ".join([r.get("description", "").lower() + " " + r.get("title", "").lower() for r in history])
        skills_text = " ".join([s.get("name", "").lower() for s in skills])
        all_text = full_text + " " + skills_text
        
        def term_freq(terms, text):
            return min(1.0, sum(text.count(t) for t in terms) / 3.0)

        candidate_dna = {
            "retrieval": term_freq(["retrieval", "rag", "search", "vector database"], all_text),
            "ranking": term_freq(["ranking", "learning to rank", "recommendation"], all_text),
            "evaluation": term_freq(["evaluation", "ndcg", "mrr", "map", "a/b testing"], all_text),
            "production": term_freq(["production", "deployed", "scale", "inference"], all_text),
            "product_company": min(1.0, all_text.count("product") / 2.0),
            "startup": startup_score / 100.0,
            "leadership": lead_score / 100.0,
            "llm": term_freq(["llm", "langchain", "prompt engineering", "openai"], all_text)
        }
        
        # Compute Cosine Similarity
        vec_a = list(candidate_dna.values())
        vec_b = list(jd_dna.values())
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        dna_similarity = (dot_product / (norm_a * norm_b)) if norm_a and norm_b else 0.0

        return {
            "technical_dna": round(tech_score, 1),
            "leadership_dna": round(lead_score, 1),
            "innovation_dna": round(inno_score, 1),
            "communication_dna": round(comm_score, 1),
            "learning_dna": round(learn_score, 1),
            "startup_dna": round(startup_score, 1),
            "domain_dna": round(domain_score, 1),
            "overall_talent_index": round(overall, 1),
            "career_dna_vector": candidate_dna,
            "dna_similarity": round(dna_similarity * 100.0, 1),
            "is_it_services": is_it_services
        }
