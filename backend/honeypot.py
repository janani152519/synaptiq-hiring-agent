import json
from datetime import datetime

# Startups and their founding years in this synthetic dataset
FOUNDING_YEARS = {
    "Krutrim": 2023,
    "Sarvam AI": 2023,
    "Genpact AI": 2023,
    "Glance": 2019,
    "CRED": 2018,
    "Rephrase.ai": 2019,
    "Saarthi.ai": 2017,
    "Observe.AI": 2017,
    "Wysa": 2015,
    "Haptik": 2013,
    "Niramai": 2016,
    "Aganitha": 2017,
    "Mad Street Den": 2013,
}

class HoneypotDetector:
    @staticmethod
    def inspect_candidate(candidate: dict) -> tuple[bool, list[str]]:
        """
        Inspects a candidate profile for timeline/logical anomalies.
        Returns:
            is_honeypot (bool): True if any logical anomaly is detected
            reasons (list[str]): List of descriptions of the detected anomalies
        """
        reasons = []
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        edu = candidate.get("education", [])
        skills = candidate.get("skills", [])
        
        # 1. Check educational timeline consistency (start_year > end_year)
        for e in edu:
            start = e.get("start_year")
            end = e.get("end_year")
            if start and end and start > end:
                reasons.append(
                    f"Education at {e.get('institution')} has start year {start} > end year {end}."
                )

        # 2. Check career history start_date > end_date
        for r in history:
            start_str = r.get("start_date")
            end_str = r.get("end_date")
            if start_str and end_str:
                if start_str > end_str:
                    reasons.append(
                        f"Employment at {r.get('company')} has start date {start_str} > end date {end_str}."
                    )

        # 3. Check pre-founding startup work experience
        for r in history:
            company = r.get("company", "").strip()
            start_str = r.get("start_date")
            if not company or not start_str:
                continue
            try:
                start_year = int(start_str.split("-")[0])
                for name, f_year in FOUNDING_YEARS.items():
                    if name.lower() in company.lower():
                        if start_year < f_year:
                            reasons.append(
                                f"Claimed work experience at {company} starting {start_str}, but company was founded in {f_year}."
                            )
            except Exception:
                pass

        # 4. Check if role duration_months vastly exceeds calendar span
        for r in history:
            start_str = r.get("start_date")
            end_str = r.get("end_date")
            duration_months = r.get("duration_months", 0)
            if start_str and end_str and duration_months:
                try:
                    start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                    calendar_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                    if duration_months > calendar_months + 2:  # allow 2 months buffer
                        reasons.append(
                            f"Role duration ({duration_months} months) at {r.get('company')} exceeds chronological date span ({calendar_months} months)."
                        )
                except Exception:
                    pass

        # 5. Check if stated years of experience is much less than the sum of career history
        years_exp = profile.get("years_of_experience", 0)
        total_history_months = sum(r.get("duration_months", 0) for r in history)
        total_history_years = total_history_months / 12.0
        if years_exp > 0 and total_history_years > years_exp + 5.0:
            reasons.append(
                f"Stated years of experience is {years_exp} yrs, but career history sum is {total_history_years:.1f} yrs."
            )

        # 6. Check for expert skills with 0 duration / short duration
        expert_short_count = sum(
            1 for s in skills 
            if s.get("proficiency") == "expert" and s.get("duration_months", 0) < 12
        )
        if expert_short_count >= 1:
            reasons.append(
                f"Profile claims 'expert' proficiency in {expert_short_count} skills with < 12 months of experience."
            )

        # 7. Skill-Career Consistency
        cur_title = profile.get("current_title", "").lower()
        non_tech_titles = ["marketing", "sales", "hr", "human resources", "recruiter", "civil engineer", "accountant", "customer support"]
        is_non_tech = any(t in cur_title for t in non_tech_titles)
        if is_non_tech:
            ai_skills = ["rag", "pinecone", "langchain", "lora", "embeddings", "vector database", "pytorch", "tensorflow", "weaviate", "qdrant", "milvus"]
            has_ai_skills = any(s.get("name", "").lower() in ai_skills for s in skills)
            if has_ai_skills:
                reasons.append(f"Non-technical current title ({cur_title}) but claims highly specialized AI skills.")

        # 8. Summary-Career Consistency
        summary = profile.get("summary", "").lower()
        if "ai engineer" in summary or "machine learning" in summary:
            roles_non_tech = True
            for r in history:
                title = r.get("title", "").lower()
                if any(t in title for t in ["engineer", "developer", "scientist", "ai", "ml", "data", "programmer", "tech"]):
                    roles_non_tech = False
                    break
            if history and roles_non_tech:
                reasons.append(f"Summary claims AI Engineering, but career history consists of non-technical roles.")

        # 9. Impossible Experience (Years vs Grad Date)
        # e.g., 6.9 years experience but graduated 2024 (current year 2026 -> max 2 years)
        if edu:
            # Find the latest graduation year for a Bachelor's or higher
            latest_grad = 0
            for e in edu:
                end_yr = e.get("end_year")
                if end_yr and end_yr > latest_grad:
                    latest_grad = end_yr
            if latest_grad > 0:
                max_possible_exp = 2026 - latest_grad
                # Allow a small buffer for internships/part-time before grad
                if years_exp > max_possible_exp + 2:
                    reasons.append(f"Impossible experience: {years_exp} yrs, but latest degree completed in {latest_grad}.")

        # 10. Skill Inflation
        # e.g., 20 expert skills but endorsements near zero
        expert_skills_count = sum(1 for s in skills if s.get("proficiency") == "expert")
        total_endorsements = sum(s.get("endorsements", 0) for s in skills)
        if expert_skills_count >= 15 and total_endorsements < 5:
            reasons.append(f"Skill inflation: {expert_skills_count} 'expert' skills but only {total_endorsements} total endorsements.")

        # 11. Career Jump Detection
        # Junior -> Principal/Architect in under 3 years
        # Find earliest Junior/Intern role and latest Principal/Lead/Architect role
        first_junior_yr = None
        first_principal_yr = None
        for r in history:
            title = r.get("title", "").lower()
            start_str = r.get("start_date")
            if not start_str:
                continue
            try:
                start_yr = int(start_str.split("-")[0])
                if any(kw in title for kw in ["junior", "intern"]):
                    if first_junior_yr is None or start_yr < first_junior_yr:
                        first_junior_yr = start_yr
                if any(kw in title for kw in ["principal", "architect", "head", "director"]):
                    if first_principal_yr is None or start_yr < first_principal_yr:
                        first_principal_yr = start_yr
            except Exception:
                pass
                
        if first_junior_yr and first_principal_yr and first_principal_yr > first_junior_yr:
            if (first_principal_yr - first_junior_yr) < 3:
                reasons.append(f"Suspicious career jump: Junior to Principal/Architect in {first_principal_yr - first_junior_yr} years.")

        return len(reasons) > 0, reasons
