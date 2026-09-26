#!/usr/bin/env python3
"""
ISC Class XII Science Resource Library - Setup & Orchestrator
Executes:
  - Step 1: Directory Tree Creation
  - Step 2: SQLite Manifest & Audit DB Initialization
  - Step 3: Polite Harvester & Hashing Engine Setup
"""

import hashlib
import json
import os
import sqlite3
import sys
import time
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

# Root configuration
BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")
CATALOG_JSON_PATH = os.path.join(BASE_DIR, "00_manifests", "document_catalog.json")

SCIENCE_SUBJECTS = {
    "801": "english_language",
    "802": "literature_in_english",
    "860": "mathematics",
    "861": "physics",
    "862": "chemistry",
    "863": "biology",
    "868": "computer_science",
    "864": "biotechnology",
    "866": "environmental_science"
}

CATEGORY_FOLDERS = [
    "01_syllabus_and_regulations",
    "02_specimen_papers",
    "03_previous_year_papers",
    "04_pupil_performance_analysis",
    "05_extracted_question_bank/native_text",
    "05_extracted_question_bank/ocr_processed"
]

def step_1_create_directories() -> None:
    """Creates the structured folder hierarchy."""
    print("[STEP 1] Generating repository directory tree...")
    os.makedirs(os.path.join(BASE_DIR, "00_manifests"), exist_ok=True)
    
    for category in CATEGORY_FOLDERS:
        for code, name in SCIENCE_SUBJECTS.items():
            folder_path = os.path.join(BASE_DIR, category, f"{code}_{name}")
            os.makedirs(folder_path, exist_ok=True)
            
    print(f" -> Directory structure successfully initialized under '{BASE_DIR}'.")

def step_2_init_sqlite_db() -> None:
    """Initializes the relational schema with audit and integrity constraints."""
    print("[STEP 2] Creating SQLite manifest database...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    # Documents table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        board TEXT DEFAULT 'CISCE',
        examination TEXT DEFAULT 'ISC',
        class TEXT DEFAULT 'XII',
        stream TEXT DEFAULT 'Science',
        subject TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        year INTEGER,
        document_type TEXT NOT NULL,
        solved_status TEXT CHECK(solved_status IN ('solved', 'unsolved', 'partial', 'unknown')),
        source_tier TEXT CHECK(source_tier IN ('Tier 1', 'Tier 2', 'Tier 3', 'Tier 4')),
        source_url TEXT NOT NULL,
        file_path TEXT NOT NULL,
        sha256 TEXT,
        file_size_bytes INTEGER,
        mime_type TEXT DEFAULT 'application/pdf',
        download_date TEXT,
        verification_status TEXT CHECK(verification_status IN ('verified', 'partially_verified', 'unverified', 'inaccessible')),
        notes TEXT
    );
    """)

    # Questions table (for Phase 4/5)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        question_id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        year INTEGER,
        section TEXT,
        question_number TEXT,
        question_text TEXT NOT NULL,
        marks INTEGER,
        chapter TEXT,
        topic TEXT,
        question_type TEXT,
        difficulty TEXT CHECK(difficulty IN ('easy', 'medium', 'hard', 'unknown')),
        ocr_used BOOLEAN DEFAULT 0,
        mapping_confidence REAL,
        FOREIGN KEY(document_id) REFERENCES documents(document_id) ON DELETE CASCADE
    );
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_doc_lookup ON documents(subject_code, year, document_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sha256 ON documents(sha256);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_q_topic ON questions(subject_code, chapter, topic);")
    
    conn.commit()
    conn.close()
    print(f" -> Database initialized with foreign keys and indexes at '{DB_PATH}'.")

def compute_sha256(filepath: str) -> str:
    """Computes SHA-256 hash in 64KB blocks."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def step_3_ingest_file(
    doc_id: str,
    title: str,
    subject: str,
    subject_code: str,
    year: Optional[int],
    doc_type: str,
    source_url: str,
    relative_save_path: str,
    source_tier: str = "Tier 1",
    solved_status: str = "unsolved"
) -> Dict[str, Any]:
    """Polite, verifiable ingestion routine."""
    target_path = os.path.join(BASE_DIR, relative_save_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    record = {
        "document_id": doc_id,
        "title": title,
        "board": "CISCE",
        "examination": "ISC",
        "class": "XII",
        "stream": "Science",
        "subject": subject,
        "subject_code": subject_code,
        "year": year,
        "document_type": doc_type,
        "solved_status": solved_status,
        "source_tier": source_tier,
        "source_url": source_url,
        "file_path": target_path,
        "sha256": None,
        "file_size_bytes": 0,
        "mime_type": "application/pdf",
        "download_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verification_status": "unverified",
        "notes": ""
    }

    headers = {"User-Agent": "ISC-Science-Curriculum-Research/1.0 (Polite Local Academic Retrieval)"}
    req = urllib.request.Request(source_url, headers=headers)

    try:
        # Respectful rate limiting: 2.0s delay between calls
        time.sleep(2.0)
        with urllib.request.urlopen(req) as response, open(target_path, "wb") as out_file:
            content = response.read()
            out_file.write(content)

        file_hash = compute_sha256(target_path)
        file_size = os.path.getsize(target_path)

        record["sha256"] = file_hash
        record["file_size_bytes"] = file_size
        record["verification_status"] = "verified"

    except urllib.error.URLError as err:
        record["verification_status"] = "inaccessible"
        record["notes"] = f"HTTP/Network Error: {str(err)}"
    except Exception as err:
        record["verification_status"] = "inaccessible"
        record["notes"] = f"General Error: {str(err)}"

    # Record to SQLite
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO documents 
        VALUES (:document_id, :title, :board, :examination, :class, :stream,
                :subject, :subject_code, :year, :document_type, :solved_status,
                :source_tier, :source_url, :file_path, :sha256, :file_size_bytes,
                :mime_type, :download_date, :verification_status, :notes)
    """, record)
    conn.commit()
    conn.close()

    return record

if __name__ == "__main__":
    step_1_create_directories()
    step_2_init_sqlite_db()
    print("[STEP 3 READY] The ingestion engine and verification hooks are active.")