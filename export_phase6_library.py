#!/usr/bin/env python3
"""
Step 18: Multi-Format Exporter for ISC Science Resource Library
Dumps SQLite contents into CSV, JSON, and Markdown summaries.
"""

import csv
import json
import os
import sqlite3
import time

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")
EXPORT_DIR = os.path.join(BASE_DIR, "00_manifests", "exports")

def export_all():
    print("[STEP 18] Starting Multi-Format Library Export...")
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. Export Documents Table to CSV
    csv_path = os.path.join(EXPORT_DIR, "document_catalog_export.csv")
    cur.execute("SELECT * FROM documents ORDER BY subject_code, year DESC;")
    docs = cur.fetchall()

    if docs:
        headers = docs[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in docs:
                writer.writerow(tuple(row))
        print(f" -> [CSV] Exported {len(docs)} document records to: {csv_path}")

    # 2. Export Questions Table to JSON
    json_path = os.path.join(EXPORT_DIR, "questions_database_export.json")
    cur.execute("SELECT * FROM questions ORDER BY subject_code, question_id;")
    questions = cur.fetchall()
    
    q_list = [dict(q) for q in questions]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(q_list, f, indent=2)
    print(f" -> [JSON] Exported {len(q_list)} question records to: {json_path}")

    # 3. Generate Human-Readable Markdown Summary Report
    md_path = os.path.join(EXPORT_DIR, "library_summary_report.md")
    
    # Query summary counts
    cur.execute("SELECT verification_status, COUNT(*) FROM documents GROUP BY verification_status;")
    doc_stats = cur.fetchall()

    cur.execute("SELECT subject_code, COUNT(*), SUM(marks) FROM questions GROUP BY subject_code;")
    q_stats = cur.fetchall()

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# ISC Class XII Science Resource Library Summary\n\n")
        f.write(f"*Exported at: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}*\n\n")
        f.write("## 1. Document Inventory Status\n\n")
        f.write("| Verification Status | Document Count |\n|---|---:|\n")
        for stat, count in doc_stats:
            f.write(f"| `{stat}` | {count} |\n")
        f.write(f"| **Total Registered** | **{len(docs)}** |\n\n")

        f.write("## 2. Extracted Question Bank Summary\n\n")
        f.write("| Subject Code | Extracted Questions | Total Marks Captured |\n|---|---:|---:|\n")
        for code, count, total_marks in q_stats:
            f.write(f"| Code `{code}` | {count} | {total_marks or 0} |\n")
        f.write(f"| **Total** | **{len(questions)}** | **{sum((q['marks'] or 0) for q in q_list)}** |\n\n")

        f.write("## 3. Operational Integrity Principles Enforced\n")
        f.write("- **Cryptographic Hashing:** SHA-256 block hashing on all local intake.\n")
        f.write("- **Non-Predictive Tagging:** No synthetic 'leaks' or guaranteed claims.\n")
        f.write("- **Strict Source Priority:** Tier 1 CISCE precedence across all taxonomy nodes.\n")

    print(f" -> [MARKDOWN] Executive summary generated at: {md_path}")
    conn.close()
    print("[STEP 18 COMPLETE] Multi-format export finished successfully.")

if __name__ == "__main__":
    export_all()