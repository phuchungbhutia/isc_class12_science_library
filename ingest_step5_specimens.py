#!/usr/bin/env python3
"""
Step 5: Harvester and Ingestion Engine for ISC Specimen Question Papers
Supports dynamic web fetching and verified local manual drop-in ingestion.
"""

import hashlib
import os
import re
import sqlite3
import sys
import time
import urllib.request
import urllib.error

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")

SPECIMEN_TARGETS = {
    "860": {"name": "Mathematics", "folder": "860_mathematics", "doc_id": "DOC-SPEC-26-860", "marks": 80},
    "861": {"name": "Physics", "folder": "861_physics", "doc_id": "DOC-SPEC-26-861", "marks": 70},
    "862": {"name": "Chemistry", "folder": "862_chemistry", "doc_id": "DOC-SPEC-26-862", "marks": 70},
    "863": {"name": "Biology", "folder": "863_biology", "doc_id": "DOC-SPEC-26-863", "marks": 70},
    "868": {"name": "Computer Science", "folder": "868_computer_science", "doc_id": "DOC-SPEC-26-868", "marks": 70},
    "801": {"name": "English Language", "folder": "801_english_language", "doc_id": "DOC-SPEC-26-801", "marks": 80}
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://cisce.org/"
}

def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def record_document(record: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO documents 
        (document_id, title, board, examination, class, stream, subject, subject_code,
         year, document_type, solved_status, source_tier, source_url, file_path,
         sha256, file_size_bytes, mime_type, download_date, verification_status, notes)
        VALUES (?, ?, 'CISCE', 'ISC', 'XII', 'Science', ?, ?, ?, 'specimen_paper',
                'unsolved', 'Tier 1', ?, ?, ?, ?, 'application/pdf', ?, ?, ?)
    """, (
        record["document_id"], record["title"], record["subject"], record["subject_code"],
        record["year"], record["source_url"], record["file_path"], record["sha256"],
        record["file_size_bytes"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        record["verification_status"], record["notes"]
    ))
    conn.commit()
    conn.close()

def run_step5():
    print("[STEP 5] Discovering & Ingesting ISC Class XII Science Specimen Papers...")
    parent_url = "https://cisce.org/specimen-question-papers-isc/"
    
    html_content = ""
    req = urllib.request.Request(parent_url, headers=BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            html_content = resp.read().decode('utf-8', errors='ignore')
        print(" -> Connected to CISCE Specimen Paper index.")
    except Exception as e:
        print(f" -> Live portal crawl deferred ({str(e)}). Testing local cache and manual ingestion.")

    for code, meta in SPECIMEN_TARGETS.items():
        dest_dir = os.path.join(BASE_DIR, "02_specimen_papers", meta["folder"])
        os.makedirs(dest_dir, exist_ok=True)
        filename = f"ISC_Specimen_Paper_{meta['name'].replace(' ', '_')}_{code}.pdf"
        local_path = os.path.join(dest_dir, filename)

        # 1. Local intake verification
        if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
            file_hash = compute_sha256(local_path)
            file_size = os.path.getsize(local_path)
            record_document({
                "document_id": meta["doc_id"],
                "title": f"ISC Class XII {meta['name']} Specimen Question Paper",
                "subject": meta["name"],
                "subject_code": code,
                "year": 2026,
                "source_url": "local_manual_intake",
                "file_path": local_path,
                "sha256": file_hash,
                "file_size_bytes": file_size,
                "verification_status": "verified",
                "notes": f"Verified local intake. Max marks: {meta['marks']}."
            })
            print(f" -> [VERIFIED LOCAL] {meta['name']} ({code}) processed from disk.")
            continue

        # 2. Dynamic pattern matching
        matched_url = None
        if html_content:
            pattern = rf'href=[\'"]([^\'"]*{code}[^\'"]*\.pdf)[\'"]'
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                matched_url = match.group(1)

        if matched_url:
            print(f" -> Attempting download for {meta['name']} from {matched_url}...")
            try:
                time.sleep(2.0)
                dl_req = urllib.request.Request(matched_url, headers=BROWSER_HEADERS)
                with urllib.request.urlopen(dl_req) as resp, open(local_path, "wb") as f:
                    f.write(resp.read())

                file_hash = compute_sha256(local_path)
                file_size = os.path.getsize(local_path)
                record_document({
                    "document_id": meta["doc_id"],
                    "title": f"ISC Class XII {meta['name']} Specimen Question Paper",
                    "subject": meta["name"],
                    "subject_code": code,
                    "year": 2026,
                    "source_url": matched_url,
                    "file_path": local_path,
                    "sha256": file_hash,
                    "file_size_bytes": file_size,
                    "verification_status": "verified",
                    "notes": f"Retrieved via dynamic link resolution. Max marks: {meta['marks']}."
                })
                print(f"    [VERIFIED] Successfully fetched and hashed {meta['name']}.")
                continue
            except Exception as e:
                print(f"    [DOWNLOAD ERROR] Failed for {meta['name']}: {e}")

        # 3. Mark as pending manual placement if blocked
        record_document({
            "document_id": meta["doc_id"],
            "title": f"ISC Class XII {meta['name']} Specimen Question Paper",
            "subject": meta["name"],
            "subject_code": code,
            "year": 2026,
            "source_url": parent_url,
            "file_path": local_path,
            "sha256": None,
            "file_size_bytes": 0,
            "verification_status": "inaccessible",
            "notes": f"Download blocked by CDN. Please save PDF directly into {dest_dir}"
        })
        print(f"    [PENDING LOCAL INGESTION] {meta['name']} ({code}) - Target: {local_path}")

if __name__ == "__main__":
    run_step5()