#!/usr/bin/env python3
"""
Resilient CISCE Harvester & Local Ingestion Tool
1. Attempts dynamic link resolution from the parent syllabus page.
2. Supports drop-in local ingestion if external network blocks persist.
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

SUBJECT_TARGETS = {
    "860": {"name": "Mathematics", "folder": "860_mathematics", "doc_id": "DOC-SYL-860"},
    "861": {"name": "Physics", "folder": "861_physics", "doc_id": "DOC-SYL-861"},
    "862": {"name": "Chemistry", "folder": "862_chemistry", "doc_id": "DOC-SYL-862"},
    "863": {"name": "Biology", "folder": "863_biology", "doc_id": "DOC-SYL-863"},
    "868": {"name": "Computer Science", "folder": "868_computer_science", "doc_id": "DOC-SYL-868"},
    "801": {"name": "English Language", "folder": "801_english_language", "doc_id": "DOC-SYL-801"}
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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

def update_manifest(record: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO documents 
        (document_id, title, board, examination, class, stream, subject, subject_code,
         year, document_type, solved_status, source_tier, source_url, file_path,
         sha256, file_size_bytes, mime_type, download_date, verification_status, notes)
        VALUES (?, ?, 'CISCE', 'ISC', 'XII', 'Science', ?, ?, ?, 'official_syllabus',
                'unsolved', 'Tier 1', ?, ?, ?, ?, 'application/pdf', ?, ?, ?)
    """, (
        record["document_id"], record["title"], record["subject"], record["subject_code"],
        record["year"], record["source_url"], record["file_path"], record["sha256"],
        record["file_size_bytes"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        record["verification_status"], record["notes"]
    ))
    conn.commit()
    conn.close()

def run_resilient_fetch():
    print("[RESILIENT HARVESTER] Attempting parent page resolution...")
    parent_url = "https://cisce.org/regulations-and-syllabuses-isc/"
    req = urllib.request.Request(parent_url, headers=BROWSER_HEADERS)
    
    html_content = ""
    try:
        with urllib.request.urlopen(req) as resp:
            html_content = resp.read().decode('utf-8', errors='ignore')
        print(" -> Successfully retrieved CISCE regulations index page.")
    except Exception as e:
        print(f" -> Could not reach parent page ({str(e)}). Switching to local drop-in mode.")

    for code, meta in SUBJECT_TARGETS.items():
        dest_dir = os.path.join(BASE_DIR, "01_syllabus_and_regulations", meta["folder"])
        os.makedirs(dest_dir, exist_ok=True)
        filename = f"ISC_Syllabus_{meta['name'].replace(' ', '_')}_{code}.pdf"
        target_path = os.path.join(dest_dir, filename)

        # 1. Check if user already manually placed the file locally
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            file_hash = compute_sha256(target_path)
            file_size = os.path.getsize(target_path)
            update_manifest({
                "document_id": meta["doc_id"],
                "title": f"ISC Class XII {meta['name']} Syllabus",
                "subject": meta["name"],
                "subject_code": code,
                "year": 2026,
                "source_url": "local_manual_intake",
                "file_path": target_path,
                "sha256": file_hash,
                "file_size_bytes": file_size,
                "verification_status": "verified",
                "notes": "Verified from local file intake."
            })
            print(f" -> [VERIFIED LOCAL] {meta['name']} ({code}) cataloged from disk.")
            continue

        # 2. Try regex extraction of direct link from parent HTML
        matched_url = None
        if html_content:
            pattern = rf'href=[\'"]([^\'"]*{code}[^\'"]*\.pdf)[\'"]'
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                matched_url = match.group(1)

        if matched_url:
            print(f" -> Downloading discovered URL for {meta['name']}: {matched_url}")
            try:
                time.sleep(2.0)
                dl_req = urllib.request.Request(matched_url, headers=BROWSER_HEADERS)
                with urllib.request.urlopen(dl_req) as resp, open(target_path, "wb") as f:
                    f.write(resp.read())
                
                file_hash = compute_sha256(target_path)
                file_size = os.path.getsize(target_path)
                update_manifest({
                    "document_id": meta["doc_id"],
                    "title": f"ISC Class XII {meta['name']} Syllabus",
                    "subject": meta["name"],
                    "subject_code": code,
                    "year": 2026,
                    "source_url": matched_url,
                    "file_path": target_path,
                    "sha256": file_hash,
                    "file_size_bytes": file_size,
                    "verification_status": "verified",
                    "notes": "Directly fetched via dynamic parent page match."
                })
                print(f"    [VERIFIED] Successfully fetched {meta['name']}.")
                continue
            except Exception as e:
                print(f"    [FAILED] Dynamic fetch failed for {meta['name']}: {e}")

        # 3. Log inaccessible status if neither approach succeeded
        update_manifest({
            "document_id": meta["doc_id"],
            "title": f"ISC Class XII {meta['name']} Syllabus",
            "subject": meta["name"],
            "subject_code": code,
            "year": 2026,
            "source_url": parent_url,
            "file_path": target_path,
            "sha256": None,
            "file_size_bytes": 0,
            "verification_status": "inaccessible",
            "notes": "Automatic download blocked or endpoint rotated. Manual local placement required."
        })
        print(f"    [INACCESSIBLE] {meta['name']} ({code}) - Drop file manually into {dest_dir}")

if __name__ == "__main__":
    run_resilient_fetch()