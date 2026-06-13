import os

class JDParser:
    DEFAULT_BLUEPRINT = {
        "required_skills": [
            "embeddings", "sentence-transformers", "vector search", "dense retrieval",
            "vector database", "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss",
            "python", "ranking systems", "evaluation frameworks", "ndcg", "mrr", "map", "a/b testing"
        ],
        "preferred_skills": [
            "llm", "fine-tuning", "lora", "qlora", "peft", "learning to rank", "xgboost",
            "hr-tech", "recruiting tech", "distributed systems", "large-scale inference", "open-source"
        ],
        "experience_min": 5.0,
        "experience_max": 9.0,
        "leadership_keywords": ["mentor", "lead", "architect", "manager", "head", "principal", "founding"],
        "startup_keywords": ["startup", "product", "scale", "seed", "series a", "series b", "founding team"],
        "product_companies": [
            "Pied Piper", "Initech", "Wayne Enterprises", "Acme Corp", "Stark Industries", "Hooli", "Globex Inc", "Dunder Mifflin",
            "Swiggy", "Razorpay", "CRED", "Zomato", "Flipkart", "Meesho", "Nykaa", "InMobi", "BYJU'S", "PolicyBazaar",
            "Ola", "Zoho", "Vedantu", "Paytm", "Unacademy", "PharmEasy", "upGrad", "Freshworks", "PhonePe", "Dream11",
            "Genpact AI", "Glance", "Rephrase.ai", "Aganitha", "Niramai", "Saarthi.ai", "Sarvam AI", "Mad Street Den", "Observe.AI", "Krutrim", "Wysa", "Haptik"
        ],
        "consulting_firms": [
            "infosys", "wipro", "tcs", "tata consultancy services", "capgemini", "hcl", "accenture", "cognizant", "tech mahindra", "mphasis"
        ]
    }

    @staticmethod
    def parse_jd(jd_text: str = None) -> dict:
        """
        Parses JD text and extracts hiring criteria.
        Returns the Default Blueprint matching the Senior AI Engineer role if no text is provided,
        or performs light keyword parsing on provided text.
        """
        if not jd_text:
            return JDParser.DEFAULT_BLUEPRINT
        
        # Simple rule-based parsing for dynamic input
        text_lower = jd_text.lower()
        blueprint = {
            "required_skills": [],
            "preferred_skills": [],
            "experience_min": 5.0,
            "experience_max": 9.0,
            "leadership_keywords": JDParser.DEFAULT_BLUEPRINT["leadership_keywords"],
            "startup_keywords": JDParser.DEFAULT_BLUEPRINT["startup_keywords"],
            "product_companies": JDParser.DEFAULT_BLUEPRINT["product_companies"],
            "consulting_firms": JDParser.DEFAULT_BLUEPRINT["consulting_firms"]
        }
        
        # Extract skills using default lists as dictionary checks
        for skill in JDParser.DEFAULT_BLUEPRINT["required_skills"]:
            if skill.lower() in text_lower:
                blueprint["required_skills"].append(skill)
        for skill in JDParser.DEFAULT_BLUEPRINT["preferred_skills"]:
            if skill.lower() in text_lower:
                blueprint["preferred_skills"].append(skill)
                
        # Ensure we don't return empty sets
        if not blueprint["required_skills"]:
            blueprint["required_skills"] = JDParser.DEFAULT_BLUEPRINT["required_skills"]
        if not blueprint["preferred_skills"]:
            blueprint["preferred_skills"] = JDParser.DEFAULT_BLUEPRINT["preferred_skills"]
            
        return blueprint
