#!/usr/bin/env python3
"""
Step 7: Ingestion and Verification of CISCE Pupil Performance Analysis
Creates directory structure, registers document records into SQLite,
and computes SHA-256 hashes for placed PDFs.
"""

import hashlib
import os
import sqlite3
import time

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")

SUBJECTS = {
    "860": "mathematics",
    "861": "physics",
    "862": "chemistry",
    "863": "biology",
    "868": "computer_science",
    "801": "english_language"
}

# Principal recent analysis cycles released by CISCE RDCD
RECENT_CYCLES = [2023, 2024, 2025]

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_step7():
    print("[STEP 7] Initializing Pupil Performance Analysis Repository...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    total_registered = 0
    verified_count = 0

    for code, name in SUBJECTS.items():
        subject_dir = os.path.join(BASE_DIR, "04_pupil_performance_analysis", f"{code}_{name}")
        os.makedirs(subject_dir, exist_ok=True)

        for year in RECENT_CYCLES:
            doc_id = f"DOC-APP-{year}-{code}"
            filename = f"ISC_{year}_Pupil_Performance_Analysis_{name.capitalize()}_{code}.pdf"
            file_path = os.path.join(subject_dir, filename)

            file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 1000

            if file_exists:
                sha256_hash = compute_sha256(file_path)
                file_size = os.path.getsize(file_path)
                status = "verified"
                notes = f"Verified CISCE RDCD pupil performance report for {year}."
                verified_count += 1
            else:
                sha256_hash = None
                file_size = 0
                status = "unverified"
                notes = f"Awaiting file placement. Path: {file_path}"

            cur.execute("""
                INSERT OR REPLACE INTO documents 
                (document_id, title, board, examination, class, stream, subject, subject_code,
                 year, document_type, solved_status, source_tier, source_url, file_path,
                 sha256, file_size_bytes, mime_type, download_date, verification_status, notes)
                VALUES (?, ?, 'CISCE', 'ISC', 'XII', 'Science', ?, ?, ?, 'pupil_performance',
                        'solved', 'Tier 1', 'https://cisce.org/analysis-of-pupil-performance-isc/',
                        ?, ?, ?, 'application/pdf', ?, ?, ?)
            """, (
                doc_id,
                f"ISC Class XII {name.replace('_', ' ').title()} Pupil Performance Analysis {year}",
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

    print(f"[STEP 7 COMPLETE] {total_registered} Pupil Performance slots registered across {len(RECENT_CYCLES)} evaluation cycles.")
    print(f" -> Verified on disk: {verified_count}/{total_registered}")
    print(f" -> Drop downloaded reports into `./04_pupil_performance_analysis/[CODE]_[SUBJECT]/` and re-run.")

if __name__ == "__main__":
    run_step7()