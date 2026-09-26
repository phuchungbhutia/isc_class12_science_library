#!/usr/bin/env python3
"""
Phase 5: Syllabus Mapping & Examination Analysis Engine (Steps 14, 15, 16)
- Maps questions to official CISCE Unit/Chapter taxonomy (Step 14)
- Classifies cognitive skill level and difficulty (Step 15)
- Computes topic weightage, frequency distribution, and analysis matrix (Step 16)
"""

import json
import os
import re
import sqlite3
from collections import defaultdict
from typing import Dict, List, Tuple

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")
REPORT_PATH = os.path.join(BASE_DIR, "00_manifests", "phase5_topic_analysis.json")

# 1. Official CISCE Syllabus Taxonomy & Keyword Signatures (Step 14)
TAXONOMY = {
    "861": {  # Physics
        "Electrostatics": ["gaussian", "flux", "charge", "capacitor", "capacitance", "coulomb", "potential difference", "electric field"],
        "Current Electricity": ["drift velocity", "relaxation time", "wheatstone", "kirchhoff", "ohm", "resistance", "potentiometer"],
        "Magnetism & EMI": ["transformer", "eddy current", "inductance", "magnetic field", "biot-savart", "ampere", "faraday", "lenz"],
        "Alternating Current": ["lcr", "resonance", "impedance", "power factor", "rms", "alternating voltage"],
        "Optics": ["telescope", "microscope", "huygens", "wavefront", "refraction", "interference", "diffraction", "lens", "prism"],
        "Modern Physics": ["bohr", "hydrogen atom", "photoelectric", "work function", "nucleus", "binding energy", "semiconductor", "diode"]
    },
    "860": {  # Mathematics
        "Algebra & Matrices": ["matrix", "matrices", "determinant", "det(a)", "singular", "inverse", "cramer"],
        "Calculus": ["integral", "derivative", "differential equation", "dy/dx", "continuous", "maxima", "minima", "limit"],
        "Probability": ["probability", "bayes", "cards", "dice", "independent events", "random variable", "distribution"],
        "Vectors & 3D Geometry": ["skew lines", "vector", "shortest distance", "plane", "direction cosines", "dot product", "cross product"],
        "Relations & Functions": ["equivalence", "bijective", "injective", "surjective", "relation", "function"]
    }
}

# 2. Cognitive Skill Classification Heuristics (Step 15)
def classify_cognitive_skill(question_text: str, marks: int) -> Tuple[str, str]:
    lower_q = question_text.lower()
    
    # Analysis / Evaluation
    if any(k in lower_q for k in ["assertion", "reason", "evaluate", "case", "interpret"]):
        return "Analysis & Evaluation", "hard" if (marks and marks >= 4) else "medium"
    
    # Application / Problem Solving
    if any(k in lower_q for k in ["calculate", "determine", "find the value", "solve", "evaluate the following"]):
        return "Application / Numerical", "hard" if (marks and marks >= 4) else "medium"
    
    # Understanding / Derivation
    if any(k in lower_q for k in ["derive", "explain", "with the help of", "construct", "prove"]):
        return "Understanding / Derivation", "medium" if (marks and marks <= 3) else "hard"
    
    # Recall / Knowledge
    if any(k in lower_q for k in ["state", "define", "depends only on", "name", "what is"]):
        return "Recall / Knowledge", "easy"
        
    return "Understanding", "medium"

def run_phase5_analysis():
    print("[PHASE 5] Initiating Syllabus Mapping & Topic Analysis...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT question_id, subject_code, marks, question_text 
        FROM questions;
    """)
    questions = cur.fetchall()

    if not questions:
        print(" -> No extracted questions found in database.")
        print(" -> Ensure Phase 4 parser has extracted records into SQLite first.")
        conn.close()
        return

    print(f" -> Mapping and classifying {len(questions)} extracted questions...")

    # Data structures for Phase 5 reporting (Step 16)
    topic_weights = defaultdict(lambda: {"count": 0, "total_marks": 0, "questions": []})
    skill_distribution = defaultdict(int)

    for q_id, sub_code, marks, q_text in questions:
        marks = marks or 0
        assigned_chapter = "Unclassified / General"
        subject_tax = TAXONOMY.get(sub_code, {})

        # Keyword-based taxonomy mapping
        lower_text = q_text.lower()
        matched_scores = {}
        for chapter, keywords in subject_tax.items():
            score = sum(1 for kw in keywords if kw in lower_text)
            if score > 0:
                matched_scores[chapter] = score

        if matched_scores:
            assigned_chapter = max(matched_scores, key=matched_scores.get)

        skill, difficulty = classify_cognitive_skill(q_text, marks)

        # Update database with Phase 5 classifications
        cur.execute("""
            UPDATE questions 
            SET chapter = ?, difficulty = ?, question_type = ?, mapping_confidence = 0.90
            WHERE question_id = ?;
        """, (assigned_chapter, difficulty, skill, q_id))

        # Tally metrics for Step 16
        group_key = f"{sub_code}:{assigned_chapter}"
        topic_weights[group_key]["count"] += 1
        topic_weights[group_key]["total_marks"] += marks
        topic_weights[group_key]["questions"].append(q_id)
        skill_distribution[skill] += 1

    conn.commit()
    conn.close()

    # Step 16: Render Topic Analysis Summary
    print("\n==================================================")
    print("PHASE 5 TOPIC WEIGHTAGE & FREQUENCY MATRIX")
    print("==================================================")
    print(f"{'Subject Code':<14} | {'Syllabus Unit':<25} | {'Questions':<10} | {'Marks Total':<12}")
    print("-" * 68)

    serialized_report = {}
    for group_key, data in sorted(topic_weights.items()):
        sub_code, unit = group_key.split(":")
        print(f"{sub_code:<14} | {unit:<25} | {data['count']:<10} | {data['total_marks']:<12}")
        serialized_report[group_key] = {
            "subject_code": sub_code,
            "unit": unit,
            "question_count": data["count"],
            "total_marks": data["total_marks"]
        }

    print("\n--- COGNITIVE SKILL DISTRIBUTION ---")
    for skill_name, tally in skill_distribution.items():
        pct = (tally / len(questions)) * 100
        print(f" -> {skill_name:<28}: {tally} questions ({pct:.1f}%)")

    with open(REPORT_PATH, "w", encoding="utf-8") as rf:
        json.dump(serialized_report, rf, indent=2)

    print(f"\n[PHASE 5 COMPLETE] Topic matrix saved to '{REPORT_PATH}'.")

if __name__ == "__main__":
    run_phase5_analysis()