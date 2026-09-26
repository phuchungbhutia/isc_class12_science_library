#!/usr/bin/env python3
"""
Step 6: Previous-Year Question Papers (PYQ) Archival Pipeline (2017–2026)
Handles schema registration, directory partitioning, and automated SHA-256 ingestion.
"""

import hashlib
import os
import sqlite3
import time

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")

YEARS = list(range(2017, 2027))  # 2017 to 2026 inclusive

SUBJECTS = {
    "860": "mathematics",
    "861": "physics",
    "862": "chemistry",
    "863": "biology",
    "868": "computer_science",
    "801": "english_language"
}

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_step6():
    print("[STEP 6] Initializing Historical PYQ Archival Structure (2017–2026)...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_registered = 0
    verified_count = 0

    for year in YEARS:
        for code, name in SUBJECTS.items():
            year_folder = os.path.join(BASE_DIR, "03_previous_year_papers", str(year), f"{code}_{name}")
            os.makedirs(year_folder, exist_ok=True)

            filename = f"ISC_{year}_{name.capitalize()}_{code}.pdf"
            file_path = os.path.join(year_folder, filename)
            doc_id = f"DOC-PYQ-{year}-{code}"

            file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 1000
            
            if file_exists:
                sha256_hash = compute_sha256(file_path)
                file_size = os.path.getsize(file_path)
                status = "verified"
                notes = f"Verified offline archive paper for examination year {year}."
                verified_count += 1
            else:
                sha256_hash = None
                file_size = 0
                status = "unverified"
                notes = f"Awaiting intake. Target path: {file_path}"

            # Insert record into database
            cur.execute("""
                INSERT OR REPLACE INTO documents 
                (document_id, title, board, examination, class, stream, subject, subject_code,
                 year, document_type, solved_status, source_tier, source_url, file_path,
                 sha256, file_size_bytes, mime_type, download_date, verification_status, notes)
                VALUES (?, ?, 'CISCE', 'ISC', 'XII', 'Science', ?, ?, ?, 'previous_year_paper',
                        'unsolved', 'Tier 1', 'archive_catalog', ?, ?, ?, 'application/pdf', ?, ?, ?)
            """, (
                doc_id,
                f"ISC Class XII {name.replace('_', ' ').title()} Question Paper {year}",
                name.replace('_', ' ').title(),
                code,
                year,
                file_path,
                sha256_hash,
                file_size,
                time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                status,
                notes
            ))
            total_registered += 1

    conn.commit()
    conn.close()
    print(f"[STEP 6 COMPLETE] {total_registered} paper slots registered across {len(YEARS)} academic years.")
    print(f" -> Currently verified on disk: {verified_count}/{total_registered}")
    print(f" -> Drop downloaded PYQs into `./03_previous_year_papers/[YEAR]/[CODE]_[SUBJECT]/` and re-run to verify.")

if __name__ == "__main__":
    run_step6()