import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSIGNMENTS_CSV = os.path.join(BASE_DIR, "assignments.csv")

def verify():
    unique_papers = set()
    anchor_paper = None
    coverage = {}
    
    with open(ASSIGNMENTS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        total_rows = 0
        for row in reader:
            total_rows += 1
            pids = row['paper_ids'].split(',')
            anchor = row['calibration_paper']
            
            if anchor_paper is None:
                anchor_paper = anchor
            elif anchor_paper != anchor:
                print(f"Warning: Mixed anchor papers found! {anchor_paper} vs {anchor}")
            
            for pid in pids:
                unique_papers.add(pid)
                coverage[pid] = coverage.get(pid, 0) + 1
    
    print("--- Assignment Verification Report ---")
    print(f"Total Annotators: {total_rows}")
    print(f"Total Unique Paper IDs (including anchor): {len(unique_papers)}")
    
    # Analyze Coverage
    print("\nCoverage Analysis:")
    counts = {}
    for pid, count in coverage.items():
        counts[count] = counts.get(count, 0) + 1
    
    for count in sorted(counts.keys()):
        print(f"  Papers with {count:2} annotators: {counts[count]}")
    
    print(f"\nAnchor Paper: {anchor_paper}")
    print(f"Anchor Paper Coverage: {coverage.get(anchor_paper, 0)}")
    
    # Logic check
    expected_unique = 181 # 180 unique + 1 anchor
    if len(unique_papers) == expected_unique:
        print("\n[PASSED] Unique count is exactly 181.")
    else:
        print(f"\n[FAILED] Expected 181 unique papers, found {len(unique_papers)}.")

if __name__ == "__main__":
    verify()
