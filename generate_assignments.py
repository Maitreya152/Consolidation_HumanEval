"""
generate_assignments.py
-----------------------
Generates the annotator <-> paper assignment mapping.

Rules (from plan.md):
  - 60 annotators total
  - Each annotator reviews 3 papers  (2 unique + 1 calibration paper shared by all)
  - Each unique paper must be reviewed by at least 3 annotators
  - 1 common "calibration" paper is assigned to EVERY annotator

Outputs:
  - assignments.csv  : annotator_id, name, paper_ids (comma-separated list of 3)
  - paper_coverage.csv : paper_id, annotator_ids (for verification)
"""

import os
import csv
import random
import math
import glob

RANDOM_SEED = 42
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUT_DIR = os.path.dirname(__file__)

NUM_ANNOTATORS = 60
PAPERS_PER_ANNOTATOR = 10          # 9 unique + 1 calibration
MIN_COVERAGE = 3                   # each paper must be done by >= 3 people

# ---------------------------------------------------------------------------
# 1. Discover all paper IDs from the data directory
# ---------------------------------------------------------------------------
def get_all_paper_ids():
    consolidated_files = glob.glob(os.path.join(DATA_DIR, "*_consolidated.json"))
    paper_ids = []
    for f in consolidated_files:
        basename = os.path.basename(f)
        # e.g. iclr24_7OO8tTOgh4_consolidated.json -> iclr24_7OO8tTOgh4
        paper_id = basename.replace("_consolidated.json", "")
        paper_ids.append(paper_id)
    paper_ids.sort()
    return paper_ids

# ---------------------------------------------------------------------------
# 2. Choose one calibration paper (fixed, common to all annotators)
# ---------------------------------------------------------------------------
def pick_calibration_paper(paper_ids, seed=RANDOM_SEED):
    rng = random.Random(seed)
    return rng.choice(paper_ids)

# ---------------------------------------------------------------------------
# 3. Assign non-calibration papers to annotators
#    Each annotator gets 2 unique papers (+ 1 calibration = 3 total)
#    Each unique paper must be covered >= MIN_COVERAGE times
# ---------------------------------------------------------------------------
def assign_unique_papers(unique_papers, num_annotators, papers_per_unique=9, min_coverage=MIN_COVERAGE, seed=RANDOM_SEED):
    rng = random.Random(seed)

    # Total unique-paper "slots" needed
    total_slots = num_annotators * papers_per_unique   # 60 * 2 = 120

    # Minimum papers needed: total_slots / min_coverage (ceiling)
    # With 180 papers and 120 slots and min_cov=3 -> each paper gets exactly 120/180 < 1
    # BUT we only have 120 slots for up to 180 papers, so we use a SUBSET of papers.
    # Number of papers we can fully cover = total_slots // min_coverage = 40
    num_papers_to_use = total_slots // min_coverage   # 40

    # Pick a random subset of unique papers (excluding calibration paper)
    if len(unique_papers) < num_papers_to_use:
        raise ValueError(
            f"Not enough unique papers ({len(unique_papers)}) to fill {num_papers_to_use} slots "
            f"with min coverage {min_coverage}."
        )

    selected_papers = rng.sample(unique_papers, num_papers_to_use)
    rng.shuffle(selected_papers)

    assignments = {i: [] for i in range(num_annotators)}
    
    for pass_idx in range(min_coverage):
        # Shift the annotator assignment by pass_idx to ensure each paper gets completely distinct annotators
        for i, paper in enumerate(selected_papers):
            ann_idx = (i + pass_idx) % num_annotators
            assignments[ann_idx].append(paper)

    # Convert assignments dictionary keys back to list-like returned format
    # The current returns expect a dictionary of ann_idx -> list of papers, which matches.
    return assignments, selected_papers

# ---------------------------------------------------------------------------
# 4. Build annotator records
# ---------------------------------------------------------------------------
def build_annotator_records(num_annotators, unique_assignments, calibration_paper):
    records = []
    for i in range(1, num_annotators + 1):
        ann_id = f"ANN{i:03d}"
        name = f"Name{i}"
        unique_papers = unique_assignments[i - 1]
        papers = unique_papers + [calibration_paper]
        records.append({
            "annotator_id": ann_id,
            "name": name,
            "paper_ids": ",".join(papers),
            "calibration_paper": calibration_paper,
        })
    return records

# ---------------------------------------------------------------------------
# 5. Save CSVs
# ---------------------------------------------------------------------------
def save_assignments(records, out_path):
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["annotator_id", "name", "paper_ids", "calibration_paper"])
        writer.writeheader()
        writer.writerows(records)
    print(f"[✓] Saved assignments -> {out_path}")

def save_paper_coverage(records, calibration_paper, out_path):
    coverage = {}
    for rec in records:
        for pid in rec["paper_ids"].split(","):
            coverage.setdefault(pid, []).append(rec["annotator_id"])

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["paper_id", "is_calibration", "num_annotators", "annotator_ids"])
        for pid in sorted(coverage.keys()):
            ann_ids = coverage[pid]
            is_cal = "yes" if pid == calibration_paper else "no"
            writer.writerow([pid, is_cal, len(ann_ids), ",".join(ann_ids)])

    print(f"[✓] Saved paper coverage -> {out_path}")

    # Verify coverage
    non_cal = {pid: anns for pid, anns in coverage.items() if pid != calibration_paper}
    min_cov = min(len(v) for v in non_cal.values())
    max_cov = max(len(v) for v in non_cal.values())
    print(f"[✓] Unique papers used: {len(non_cal)}")
    print(f"[✓] Min coverage per unique paper: {min_cov}  (must be >= {MIN_COVERAGE})")
    print(f"[✓] Max coverage per unique paper: {max_cov}")
    print(f"[✓] Calibration paper '{calibration_paper}' covered by all {len(records)} annotators")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    all_paper_ids = get_all_paper_ids()
    print(f"[i] Total papers discovered: {len(all_paper_ids)}")

    calibration_paper = pick_calibration_paper(all_paper_ids)
    print(f"[i] Calibration paper: {calibration_paper}")

    unique_papers = [p for p in all_paper_ids if p != calibration_paper]

    unique_assignments, selected_papers = assign_unique_papers(
        unique_papers,
        num_annotators=NUM_ANNOTATORS,
        papers_per_unique=9,
        min_coverage=MIN_COVERAGE,
    )

    records = build_annotator_records(NUM_ANNOTATORS, unique_assignments, calibration_paper)

    assignments_path = os.path.join(OUT_DIR, "assignments.csv")
    coverage_path = os.path.join(OUT_DIR, "paper_coverage.csv")

    save_assignments(records, assignments_path)
    save_paper_coverage(records, calibration_paper, coverage_path)

    print("\n[✓] Done! Summary:")
    print(f"    Annotators       : {NUM_ANNOTATORS}")
    print(f"    Papers per person: {PAPERS_PER_ANNOTATOR} (9 unique + 1 calibration)")
    print(f"    Unique papers    : {len(selected_papers)}")
    print(f"    Calibration paper: {calibration_paper}")
