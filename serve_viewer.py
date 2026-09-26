#!/usr/bin/env python3
"""
Path-Resilient Web Server for the ISC Science Study Resource Library Viewer.
"""

import http.server
import json
import os
import socketserver
import sqlite3
import sys

PORT = 8080

# Determine absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if the folder is nested or self-referential
if os.path.exists(os.path.join(SCRIPT_DIR, "00_manifests")):
    BASE_DIR = SCRIPT_DIR
elif os.path.exists(os.path.join(SCRIPT_DIR, "isc_class12_science_library", "00_manifests")):
    BASE_DIR = os.path.join(SCRIPT_DIR, "isc_class12_science_library")
else:
    BASE_DIR = SCRIPT_DIR

DB_PATH = os.path.join(BASE_DIR, "00_manifests", "library_database.sqlite")

# Ensure viewer.html is in BASE_DIR
viewer_src = os.path.join(SCRIPT_DIR, "viewer.html")
viewer_dst = os.path.join(BASE_DIR, "viewer.html")
if os.path.exists(viewer_src) and not os.path.exists(viewer_dst):
    import shutil
    shutil.copy2(viewer_src, viewer_dst)

class LibraryHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        # Dynamic API route to query documents table
        if self.path == "/api/documents":
            if not os.path.exists(DB_PATH):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"[]")
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT document_id, subject, subject_code, year,
                       document_type, verification_status, sha256 
                FROM documents 
                ORDER BY subject_code, year DESC;
            """)
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

            self.wfile.write(json.dumps(rows).encode("utf-8"))
            return

        # Default root serves viewer.html
        if self.path in ("/", "/index.html"):
            self.path = "/viewer.html"

        return super().do_GET()

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LibraryHTTPRequestHandler) as httpd:
        print("=" * 65)
        print("ISC SCIENCE RESOURCE LIBRARY VIEWER READY")
        print(f"Serving directory: {BASE_DIR}")
        print(f"Open in your browser: http://localhost:{PORT}")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    start_server()