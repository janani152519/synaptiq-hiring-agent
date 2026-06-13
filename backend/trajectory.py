# backend/trajectory.py
class CareerTrajectoryEngine:
    @staticmethod
    def analyze_trajectory(candidate: dict) -> dict:
        """
        Analyzes growth speed, promotions, role tenure, and predicts next career steps.
        """
        profile = candidate.get("profile", {})
        history = candidate.get("career_history", [])
        
        yrs = profile.get("years_of_experience", 0)
        num_roles = len(history)
        
        # 1. Growth Score (Velocity of experience accumulation & tenure stability)
        # Slower switches are better, but some switches show growth. 
        # Title chases (switching every 1-1.5 years) are penalized.
        growth_score = 60.0
        if num_roles > 0:
            avg_duration_months = sum(r.get("duration_months", 0) for r in history) / num_roles
            
            # Penalize switching too fast
            if avg_duration_months < 18:
                growth_score -= (18 - avg_duration_months) * 3.0
            # Reward steady growth (24-48 months average role duration)
            elif 24 <= avg_duration_months <= 48:
                growth_score += 15.0
            
            # Promotion detection (Promotion Velocity)
            # Engineer -> Senior Engineer -> Lead Engineer
            seniority_levels = {
                "junior": 1,
                "intern": 0,
                "mid": 2,
                "senior": 3,
                "lead": 4,
                "principal": 5,
                "architect": 5,
                "manager": 5,
                "director": 6,
                "head": 7
            }
            
            # Group roles by company
            roles_by_comp = {}
            for r in history:
                comp = r.get("company", "").lower()
                if comp not in roles_by_comp:
                    roles_by_comp[comp] = []
                roles_by_comp[comp].append(r)
                
            promotions = 0
            for comp, comp_roles in roles_by_comp.items():
                if len(comp_roles) > 1:
                    # Sort by start date
                    sorted_roles = sorted(comp_roles, key=lambda x: x.get("start_date", ""))
                    prev_lvl = -1
                    for r in sorted_roles:
                        title = r.get("title", "").lower()
                        lvl = 2 # default mid
                        for keyword, kw_lvl in seniority_levels.items():
                            if keyword in title:
                                lvl = kw_lvl
                                break
                        if prev_lvl != -1 and lvl > prev_lvl:
                            promotions += 1
                        prev_lvl = lvl
                        
            growth_score += promotions * 15.0
        
        # Adjust based on total experience
        if yrs >= 5 and yrs <= 9:
            growth_score += 10.0
        
        growth_score = max(0.0, min(100.0, growth_score))

        # 2. Trajectory Score (Direction of role titles and company tiers)
        trajectory_score = 50.0
        
        # Check title progression
        # Reverse history to read oldest to newest
        sorted_history = sorted(history, key=lambda x: x.get("start_date", ""))
        
        seniority_levels = {
            "junior": 1,
            "mid": 2,
            "senior": 3,
            "lead": 4,
            "principal": 5,
            "architect": 5,
            "manager": 5,
            "director": 6
        }
        
        prev_level = 0
        upward_moves = 0
        for r in sorted_history:
            title = r.get("title", "").lower()
            level = 2 # default mid
            for keyword, lvl in seniority_levels.items():
                if keyword in title:
                    level = lvl
                    break
            
            if prev_level > 0 and level > prev_level:
                upward_moves += 1
            prev_level = level
            
        trajectory_score += upward_moves * 15.0
        
        # Check current title vs average historical title
        cur_title = profile.get("current_title", "").lower()
        if any(keyword in cur_title for keyword in ["senior", "lead", "architect", "manager", "head"]):
            trajectory_score += 10.0
            
        trajectory_score = max(0.0, min(100.0, trajectory_score))

        # 3. Career Forecast prediction
        forecast = "Stable career trajectory."
        if yrs < 3:
            forecast = "Early career stage, building foundation skills."
        elif upward_moves > 0 and "lead" in cur_title:
            forecast = "Strong upward velocity; ready for staff/principal engineering or engineering management."
        elif yrs >= 5 and yrs <= 9:
            if "senior" in cur_title or "lead" in cur_title:
                forecast = "Peak engineering impact phase; ideal founding team profile."
            else:
                forecast = "Senior practitioner phase; technical depth is strong, leadership potential is developing."
        elif yrs > 10:
            forecast = "Highly seasoned expert; suitable for high-level architecture or director-level leadership."

        return {
            "growth_score": round(growth_score, 1),
            "trajectory_score": round(trajectory_score, 1),
            "career_forecast": forecast,
            "promotions_detected": promotions if num_roles > 0 else 0,
            "average_tenure_months": round(avg_duration_months, 1) if num_roles > 0 else 0
        }
