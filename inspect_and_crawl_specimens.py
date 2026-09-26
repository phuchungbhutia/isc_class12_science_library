#!/usr/bin/env python3
"""
Diagnostic Deep Link Harvester for CISCE Specimen Papers
Dumps all PDF and subpage links matching Science subjects.
"""

from html.parser import HTMLParser
import os
import urllib.request
import urllib.error

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://cisce.org/"
}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            text = ""
            self.links.append(href)

def inspect_links():
    url = "https://cisce.org/specimen-question-papers-isc/"
    print(f"Connecting to {url}...")
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
        
        parser = LinkParser()
        parser.feed(content)
        
        keywords = ["physics", "chemistry", "mathematics", "maths", "biology", "computer", "english", "860", "861", "862", "863", "868", "801"]
        print("\n--- Discovered Subject Links ---")
        found = 0
        for l in set(parser.links):
            lower_l = l.lower()
            if any(k in lower_l for k in keywords):
                print(f"Found: {l}")
                found += 1
        
        if found == 0:
            print("No direct anchor links matched keyword filters. The page links may be stored under yearly archive sub-URLs or rendered dynamically via JavaScript.")
    except Exception as e:
        print(f"Inspection error: {e}")

if __name__ == "__main__":
    inspect_links()