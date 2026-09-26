#!/usr/bin/env python3
"""
Phase 4: Resilient Extraction and Question Parsing Engine
Supports native binary PDFs and plain-text benchmark mockups.
"""

import json
import os
import re
import sqlite3
from typing import Dict, List, Any

BASE_DIR = "./isc_class12_science_library"
DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")
NATIVE_DIR = os.path.join(BASE_DIR, "05_extracted_question_bank", "native_text")
OCR_DIR = os.path.join(BASE_DIR, "05_extracted_question_bank", "ocr_processed")

QUESTION_START_PATTERN = re.compile(
    r'^(?:Question\s+(\d+)|Q(?:uestion)?\.?\s*(\d+)|\b(\d+)\.\s+)', 
    re.IGNORECASE
)
MARKS_PATTERN = re.compile(r'\[(\d{1,2})\]|\((\d{1,2})\s*marks?\)', re.IGNORECASE)
SECTION_PATTERN = re.compile(r'^\s*SECTION\s+([A-D])', re.IGNORECASE)

def extract_text_from_pdf(filepath: str) -> Dict[str, Any]:
    text_content = ""
    ocr_required = False

    # Attempt 1: Binary PDF extraction using pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages:
            t = page.extract_text() or ""
            if t:
                text_content += t + "\n"
    except Exception:
        pass

    # Attempt 2: Fallback for UTF-8 benchmark/mock documents
    if len(text_content.strip()) < 40:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                raw_lines = f.readlines()
                # Exclude the %PDF- header line
                text_content = "".join([l for l in raw_lines if not l.startswith("%PDF-")])
        except Exception as e:
            text_content = f"[EXTRACTION ERROR: {e}]"
            ocr_required = True

    return {
        "ocr_required": ocr_required,
        "combined_text": text_content
    }

def parse_questions_from_text(raw_text: str, doc_id: str, code: str, year: int) -> List[Dict[str, Any]]:
    lines = raw_text.splitlines()
    questions = []
    current_section = "General"
    current_q_num = None
    current_q_text = []
    current_marks = None

    def flush_question():
        nonlocal current_q_num, current_q_text, current_marks
        if current_q_num and current_q_text:
            text_block = " ".join(current_q_text).strip()
            q_id = f"Q-{doc_id}-{current_section}-Q{current_q_num}"
            questions.append({
                "question_id": q_id,
                "document_id": doc_id,
                "subject_code": code,
                "year": year,
                "section": current_section,
                "question_number": current_q_num,
                "question_text": text_block,
                "marks": current_marks or 2,
                "chapter": "Unassigned",
                "topic": "Unassigned",
                "question_type": "standard",
                "difficulty": "medium",
                "ocr_used": 0,
                "mapping_confidence": 0.85
            })
            current_q_num = None
            current_q_text = []
            current_marks = None

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        sec_match = SECTION_PATTERN.match(clean_line)
        if sec_match:
            flush_question()
            current_section = f"Section {sec_match.group(1).upper()}"
            continue

        q_match = QUESTION_START_PATTERN.match(clean_line)
        if q_match:
            flush_question()
            current_q_num = next(g for g in q_match.groups() if g is not None)
            current_q_text = [clean_line]
            m_match = MARKS_PATTERN.search(clean_line)
            if m_match:
                current_marks = int(m_match.group(1) or m_match.group(2))
        else:
            if current_q_num is not None:
                current_q_text.append(clean_line)
                if current_marks is None:
                    m_match = MARKS_PATTERN.search(clean_line)
                    if m_match:
                        current_marks = int(m_match.group(1) or m_match.group(2))

    flush_question()
    return questions

def run_phase4_extraction():
    print("[PHASE 4] Running Extraction and Question Parsing Pipeline...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT document_id, subject_code, year, file_path, document_type 
        FROM documents 
        WHERE verification_status = 'verified';
    """)
    verified_docs = cur.fetchall()

    if not verified_docs:
        print(" -> No verified PDF files found on disk yet.")
        conn.close()
        return

    total_parsed_questions = 0
    os.makedirs(NATIVE_DIR, exist_ok=True)
    os.makedirs(OCR_DIR, exist_ok=True)

    for doc_id, code, year, path, doc_type in verified_docs:
        ext_result = extract_text_from_pdf(path)
        
        target_dir = OCR_DIR if ext_result["ocr_required"] else NATIVE_DIR
        txt_path = os.path.join(target_dir, f"{doc_id}_extracted.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(ext_result["combined_text"])

        extracted_questions = parse_questions_from_text(
            ext_result["combined_text"], doc_id, code, year or 2026
        )

        for q in extracted_questions:
            cur.execute("""
                INSERT OR REPLACE INTO questions 
                (question_id, document_id, subject_code, year, section, question_number,
                 question_text, marks, chapter, topic, question_type, difficulty, ocr_used, mapping_confidence)
                VALUES (:question_id, :document_id, :subject_code, :year, :section, :question_number,
                        :question_text, :marks, :chapter, :topic, :question_type, :difficulty,
                        :ocr_used, :mapping_confidence)
            """, q)
            total_parsed_questions += 1

    conn.commit()
    conn.close()
    print(f"\n[PHASE 4 COMPLETE] Extracted and registered {total_parsed_questions} questions into SQLite.")

if __name__ == "__main__":
    run_phase4_extraction()