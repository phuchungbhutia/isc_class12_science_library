#!/usr/bin/env python3
"""
Master Workflow Orchestrator for ISC Class XII Science Library
Chains all operational steps: Setup -> Ingestion -> Audit -> Extraction -> Analysis -> Export.
"""

import subprocess
import sys
import time

PIPELINE_STEPS = [
    ("Step 1-3: Repository & DB Setup", "initialize_repository.py"),
    ("Step 4: Syllabus Registry", "ingest_step4_syllabuses.py"),
    ("Step 5: Specimen Papers Registry", "ingest_step5_specimens.py"),
    ("Step 6: Historical PYQ Registry", "ingest_step6_pyqs.py"),
    ("Step 7: Pupil Performance Registry", "ingest_step7_pupil_analysis.py"),
    ("Auto-Provisioning Missing Files", "auto_download_or_provision.py"),
    ("Step 8-10: Phase 3 Integrity Audit", "audit_phase3_integrity.py"),
    ("Step 11-13: Phase 4 Text & Question Extraction", "extract_phase4_questions.py"),
    ("Step 14-16: Phase 5 Syllabus Mapping & Topic Analysis", "analyze_phase5_syllabus.py"),
    ("Step 17-18: Phase 6 Multi-Format Exporter", "export_phase6_library.py")
]

def run_all():
    print("=" * 70)
    print("STARTING COMPLETE ISC CLASS XII SCIENCE DATA PIPELINE")
    print("=" * 70)
    start_total = time.time()

    for idx, (label, script) in enumerate(PIPELINE_STEPS, 1):
        print(f"\n[{idx}/{len(PIPELINE_STEPS)}] EXECUTING: {label} ({script})")
        start_step = time.time()
        result = subprocess.run([sys.executable, script], capture_output=False)
        if result.returncode != 0:
            print(f"[ERROR] Pipeline interrupted at {script}. Return code: {result.returncode}")
            sys.exit(result.returncode)
        print(f" -> Completed in {time.time() - start_step:.2f}s")

    print("\n" + "=" * 70)
    print(f"ALL PIPELINE STAGES COMPLETED SUCCESSFULLY IN {time.time() - start_total:.2f}s")
    print("=" * 70)
    print("\nNext step: Start the web viewer to browse all papers and questions.")

if __name__ == "__main__":
    run_all()