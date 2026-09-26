#!/usr/bin/env python3
"""
Step 4: Register and Ingest Official CISCE Syllabuses for Science Stream
"""

import json
import os
import sqlite3
import time
import urllib.request
import urllib.error
from initialize_repository import BASE_DIR, DB_PATH, compute_sha256

# Official CISCE publication registry for Class XII Science Syllabuses
SYLLABUS_TARGETS = [
    {
        "doc_id": "DOC-SYL-27-860",
        "subject": "Mathematics",
        "code": "860",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/860-Mathematics.pdf",
        "rel_path": "01_syllabus_and_regulations/860_mathematics/ISC_2027_Syllabus_Mathematics_860.pdf"
    },
    {
        "doc_id": "DOC-SYL-27-861",
        "subject": "Physics",
        "code": "861",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/861-Physics.pdf",
        "rel_path": "01_syllabus_and_regulations/861_physics/ISC_2027_Syllabus_Physics_861.pdf"
    },
    {
        "doc_id": "DOC-SYL-27-862",
        "subject": "Chemistry",
        "code": "862",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/862-Chemistry.pdf",
        "rel_path": "01_syllabus_and_regulations/862_chemistry/ISC_2027_Syllabus_Chemistry_862.pdf"
    },
    {
        "doc_id": "DOC-SYL-27-863",
        "subject": "Biology",
        "code": "863",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/863-Biology.pdf",
        "rel_path": "01_syllabus_and_regulations/863_biology/ISC_2027_Syllabus_Biology_863.pdf"
    },
    {
        "doc_id": "DOC-SYL-27-868",
        "subject": "Computer Science",
        "code": "868",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/868-Computer-Science.pdf",
        "rel_path": "01_syllabus_and_regulations/868_computer_science/ISC_2027_Syllabus_ComputerScience_868.pdf"
    },
    {
        "doc_id": "DOC-SYL-27-801",
        "subject": "English Language",
        "code": "801",
        "year": 2027,
        "url": "https://cisce.org/wp-content/uploads/2024/05/801-English-Language.pdf",
        "rel_path": "01_syllabus_and_regulations/801_english_language/ISC_2027_Syllabus_English_Language_801.pdf"
    }
]

def harvest_step4():
    print("[STEP 4] Initiating Tier 1 CISCE Syllabus Retrieval...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    headers = {"User-Agent": "ISC-Academic-Researcher/1.0 (Polite Local Academic Retrieval)"}

    for item in SYLLABUS_TARGETS:
        full_dest = os.path.join(BASE_DIR, item["rel_path"])
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)
        
        status = "unverified"
        sha256_hash = None
        file_size = 0
        notes = ""

        req = urllib.request.Request(item["url"], headers=headers)
        try:
            print(f" -> Fetching {item['subject']} ({item['code']})...")
            time.sleep(2.0)  # Rate limiting compliance
            with urllib.request.urlopen(req) as resp, open(full_dest, "wb") as out_file:
                out_file.write(resp.read())
            
            sha256_hash = compute_sha256(full_dest)
            file_size = os.path.getsize(full_dest)
            status = "verified"
            notes = "Official Tier 1 syllabus document acquired."
        except urllib.error.HTTPError as he:
            status = "inaccessible"
            notes = f"HTTP Error {he.code}: {he.reason}. Verify live endpoint under cisce.org/regulations-and-syllabuses-isc/"
        except Exception as e:
            status = "inaccessible"
            notes = f"Retrieval error: {str(e)}"

        # Upsert into audit SQLite
        cur.execute("""
            INSERT OR REPLACE INTO documents 
            (document_id, title, board, examination, class, stream, subject, subject_code,
             year, document_type, solved_status, source_tier, source_url, file_path,
             sha256, file_size_bytes, mime_type, download_date, verification_status, notes)
            VALUES (?, ?, 'CISCE', 'ISC', 'XII', 'Science', ?, ?, ?, 'official_syllabus',
                    'unsolved', 'Tier 1', ?, ?, ?, ?, 'application/pdf', ?, ?, ?)
        """, (
            item["doc_id"],
            f"ISC Class XII {item['subject']} Syllabus {item['year']}",
            item["subject"],
            item["code"],
            item["year"],
            item["url"],
            full_dest,
            sha256_hash,
            file_size,
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            status,
            notes
        ))
        conn.commit()
        print(f"    [{status.upper()}] Status recorded for {item['doc_id']}.")

    conn.close()
    print("[STEP 4 COMPLETE] All targets registered and audited.")

if __name__ == "__main__":
    harvest_step4()