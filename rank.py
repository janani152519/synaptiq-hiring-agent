import sys
import argparse
import json
import csv
from backend.parser import JDParser
from backend.ranker import CandidateRanker

from backend.dna import TalentDNAEngine

def run_ranking(candidates_path, output_path):
    print(f"Loading job description blueprint...")
    blueprint = JDParser.parse_jd()
    
    print(f"Stage 1: Fast Rule Scoring (Semantic Match)...")
    candidates_list = []
    
    # Process line-by-line for high performance and low memory
    count = 0
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            try:
                candidate = json.loads(line)
            except Exception as e:
                continue
                
            # Stage 1: Fast rule scoring
            sem_score = CandidateRanker.calculate_semantic_score(candidate, blueprint)
            candidates_list.append({"candidate": candidate, "stage1_score": sem_score})
                
            count += 1
            if count % 20000 == 0:
                print(f"  Processed {count} candidates in Stage 1...")
                
    print(f"Filtering 100000 -> Top 5000...")
    candidates_list.sort(key=lambda x: x["stage1_score"], reverse=True)
    top_5000 = candidates_list[:5000]
    
    print(f"Stage 2: Dense Keyword Vector Approximation (Embeddings)...")
    for c_obj in top_5000:
        dna = TalentDNAEngine.calculate_dna(c_obj["candidate"], blueprint)
        c_obj["stage2_score"] = dna["dna_similarity"]
        
    print(f"Filtering 5000 -> Top 500...")
    top_5000.sort(key=lambda x: x["stage2_score"], reverse=True)
    top_500 = top_5000[:500]
    
    print(f"Stage 3: Deep Evidence Scoring...")
    final_results = []
    for c_obj in top_500:
        result = CandidateRanker.rank_candidate(c_obj["candidate"], blueprint)
        if not result["is_honeypot"]:
            final_results.append(result)
            
    print(f"Sorting and selecting Top 100...")
    final_results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    top_100 = final_results[:100]
    
    print(f"Writing output submission to: {output_path}")
    with open(output_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Required columns: candidate_id, rank, score, reasoning
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for idx, result in enumerate(top_100):
            rank = idx + 1
            writer.writerow([
                result["candidate_id"],
                rank,
                result["score"],
                result["reasoning"]
            ])
            
    print(f"Ranking complete! Output written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Synaptiq Hiring Engine - Challenge Candidate Ranker")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl file")
    parser.add_argument("--out", required=True, help="Path to write the submission CSV")
    
    args = parser.parse_args()
    
    run_ranking(args.candidates, args.out)

if __name__ == "__main__":
    main()
