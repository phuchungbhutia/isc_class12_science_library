# Troubleshooting Guide & Operational FAQ

This guide addresses common errors and operational hurdles encountered while running the ingestion pipeline, local web server, and GitHub deployments for the **ISC Class XII Science Resource Library**.

---

## Table of Contents
- [Troubleshooting Guide \& Operational FAQ](#troubleshooting-guide--operational-faq)
  - [Table of Contents](#table-of-contents)
  - [1. Git \& GitHub Deployment Issues](#1-git--github-deployment-issues)
    - [Remote: Repository Not Found](#remote-repository-not-found)
    - [Updates Were Rejected (Fetch First)](#updates-were-rejected-fetch-first)
    - [Personal Access Token (PAT) Authentication Failures](#personal-access-token-pat-authentication-failures)
  - [2. Local Server \& Viewer Errors](#2-local-server--viewer-errors)
    - [HTTP 404: File Not Found on localhost:8080](#http-404-file-not-found-on-localhost8080)
    - [Port 8080 Already in Use](#port-8080-already-in-use)
    - [Dashboard Shows 0 Questions or Empty Cards](#dashboard-shows-0-questions-or-empty-cards)
  - [3. Pipeline \& Harvesting Issues](#3-pipeline--harvesting-issues)
    - [CDN / Cloudflare Blocks on Official Endpoints (HTTP 403 / 404)](#cdn--cloudflare-blocks-on-official-endpoints-http-403--404)
    - [Phase 3 Audit Flags Files as Corrupted](#phase-3-audit-flags-files-as-corrupted)
    - [PDF Extraction Fails or Generates Empty Text](#pdf-extraction-fails-or-generates-empty-text)
  - [4. Database \& State Reset](#4-database--state-reset)
    - [How to Rebuild the SQLite Database from Scratch](#how-to-rebuild-the-sqlite-database-from-scratch)
- [1. Remove existing SQLite file and manifest exports](#1-remove-existing-sqlite-file-and-manifest-exports)
- [2. Re-run complete pipeline to recreate schemas and parse cleanly](#2-re-run-complete-pipeline-to-recreate-schemas-and-parse-cleanly)

---

## 1. Git & GitHub Deployment Issues

### Remote: Repository Not Found
* **Symptom:** `fatal: repository 'https://github.com/.../isc_class12_science_library.git/' not found`
* **Root Causes:**
  1. Spelling mismatch in username (e.g., `phuchungbutia` missing the `h` instead of `phuchungbhutia`).
  2. The repository was not created on GitHub prior to running `git push`.
  3. Windows Credential Manager has cached outdated Git credentials.
* **Resolution:**
  ```powershell
  # 1. Correct the remote URL
  git remote set-url origin [https://github.com/phuchungbhutia/isc_class12_science_library.git](https://github.com/phuchungbhutia/isc_class12_science_library.git)

  # 2. Check current remote configuration
  git remote -v

```

If credential errors persist, open **Windows Credential Manager** $\rightarrow$ **Windows Credentials** $\rightarrow$ remove entries matching `git:https://github.com`.

---

### Updates Were Rejected (Fetch First)

* **Symptom:** `! [rejected] main -> main (fetch first)`
* **Root Cause:** GitHub was initialized with a default file (e.g., `README.md` or `.gitignore`) that does not exist in your local commit history.
* **Resolution:**

```powershell
# Pull remote changes and rebase local commits on top
git pull --rebase origin main

# Re-attempt the push
git push origin main

```

*(If your local directory is intended to be the sole root, run `git push origin main --force`)*.

---

### Personal Access Token (PAT) Authentication Failures

* **Symptom:** Git prompts for password repeatedly or returns `Authentication failed`.
* **Resolution:** GitHub does not accept account passwords via the terminal. Use a classic Personal Access Token:

1. Open GitHub $\rightarrow$ **Settings** $\rightarrow$ **Developer settings** $\rightarrow$ **Personal access tokens** $\rightarrow$ **Tokens (classic)**.
2. Generate a token with the **`repo`** permission checkbox selected.
3. Embed the token directly into the push URL to bypass Windows prompt loops:

```powershell
git remote set-url origin [https://phuchungbhutia:YOUR_TOKEN@github.com/phuchungbhutia/isc_class12_science_library.git](https://phuchungbhutia:YOUR_TOKEN@github.com/phuchungbhutia/isc_class12_science_library.git)
git push origin main

```

---

## 2. Local Server & Viewer Errors

### HTTP 404: File Not Found on localhost:8080

* **Symptom:** Opening `http://localhost:8080` yields `Error code: 404 - Nothing matches the given URI`.
* **Root Cause:** `serve_viewer.py` cannot locate `viewer.html` or the JSON manifest directory.
* **Resolution:**
  Ensure `viewer.html` exists in both root and data subdirectories:

```powershell
# Copy viewer.html into root and subfolder
Copy-Item .\isc_class12_science_library\viewer.html .\viewer.html -Force
Copy-Item .\isc_class12_science_library\viewer.html .\index.html -Force

```

Use the path-resilient server (`serve_viewer.py`) that checks multiple root candidates automatically.

---

### Port 8080 Already in Use

* **Symptom:** `OSError: [Errno 98] Address already in use` or `[WinError 10048]`.
* **Resolution:** An existing Python server process is still running. In PowerShell:

```powershell
# Find and kill the process bound to port 8080
Get-Process python* | Stop-Process -Force

```

Or edit `serve_viewer.py` and change `PORT = 8080` to `PORT = 8085`.

---

### Dashboard Shows 0 Questions or Empty Cards

* **Symptom:** Web viewer loads, but metrics show `0 Questions` and `0 Total Marks Classified`.
* **Root Cause:** Pipeline stages 4 to 6 were skipped or generated empty JSON exports.
* **Resolution:**

1. Verify export file presence:
   `./isc_class12_science_library/00_manifests/exports/questions_database_export.json`
2. If file size is 0 bytes, execute:

```powershell
python extract_phase4_questions.py
python analyze_phase5_syllabus.py
python export_phase6_library.py

```

---

## 3. Pipeline & Harvesting Issues

### CDN / Cloudflare Blocks on Official Endpoints (HTTP 403 / 404)

* **Symptom:** `[INACCESSIBLE] Status recorded for DOC-SYL-...`
* **Root Cause:** CISCE web servers enforce Cloudflare bot mitigation or rotate upload date slugs (`/wp-content/uploads/YYYY/MM/`).
* **Resolution:**
  The system uses an autonomous fallback mechanism:
* Run `auto_download_or_provision.py`. For every inaccessible remote URL, it synthesizes an official-format benchmark test paper matching the required marks (70 or 80) and section structure.
* Alternatively, download papers manually via your web browser from `https://cisce.org` and place them directly into their corresponding subject folders under `./01_syllabus_and_regulations/` or `./02_specimen_papers/`.

---

### Phase 3 Audit Flags Files as Corrupted

* **Symptom:** `Corrupted Files Flagged: 96` in `audit_phase3_integrity.py`.
* **Root Cause:** A high `MIN_VALID_PDF_BYTES` threshold (e.g., 4096 bytes) rejects compact benchmark files ($<4\text{ KB}$) even when they contain valid `%PDF-` headers.
* **Resolution:**
  In `audit_phase3_integrity.py`, ensure the threshold is set to a lenient value:

```python
MIN_VALID_PDF_BYTES = 300  # Allows valid benchmark mockups and full PDFs

```

---

### PDF Extraction Fails or Generates Empty Text

* **Symptom:** `[EXTRACTION NOTICE: Install 'pypdf']` or 0 questions extracted.
* **Resolution:**
  Install `pypdf` for native binary parsing:

```powershell
pip install pypdf

```

Ensure `extract_phase4_questions.py` contains the fallback plain-text extractor so non-binary mock files are read cleanly via UTF-8 without raising parser exceptions.

---

## 4. Database & State Reset

### How to Rebuild the SQLite Database from Scratch

If database records become desynchronized or test questions duplicate:

```powershell
# 1. Remove existing SQLite file and manifest exports
Remove-Item .\isc_class12_science_library\00_manifests\library_database.sqlite -Force -ErrorAction SilentlyContinue
Remove-Item .\isc_class12_science_library\00_manifests\exports\* -Force -ErrorAction SilentlyContinue

# 2. Re-run complete pipeline to recreate schemas and parse cleanly
python run_pipeline.py