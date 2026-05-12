import json
import collections

def main():
    with open('assignments.json', 'r') as f:
        data = json.load(f)
    
    print("--- Verifying Assignments ---")
    
    # 1. Check total number of people
    num_people = len(data)
    print(f"Total number of people (target: 30): {num_people}")
    if num_people != 30:
        print(f"  [ERROR] Expected 30 people, found {num_people}")
    else:
        print("  [OK] Exactly 30 people found.")
    
    # Collect data for further checks
    paper_counts = collections.Counter()
    conf_counts = collections.Counter()
    all_papers = set()
    
    person_paper_errors = False
    duplicate_paper_errors = False

    for person, papers in data.items():
        # 2. Check papers per person
        if len(papers) != 5:
            print(f"  [ERROR] {person} does not have exactly 5 papers. They have {len(papers)}.")
            person_paper_errors = True
            
        # 3. Check for duplicates per person
        if len(papers) != len(set(papers)):
            print(f"  [ERROR] {person} has duplicate papers assigned!")
            duplicate_paper_errors = True
            
        for paper in papers:
            paper_counts[paper] += 1
            all_papers.add(paper)
            
            # Extract conf_id
            conf_id = paper.split('_')[0]
            conf_counts[conf_id] += 1

    if not person_paper_errors:
        print("  [OK] Every person has exactly 5 papers.")
    if not duplicate_paper_errors:
        print("  [OK] No person has duplicate papers assigned.")
            
    # 4. Check total unique papers
    total_papers = len(all_papers)
    print(f"Total unique papers (target: 50): {total_papers}")
    if total_papers != 50:
        print(f"  [ERROR] Expected 50 unique papers, found {total_papers}")
    else:
        print("  [OK] Exactly 50 unique papers found.")
        
    # 5. Check 3 annotators per paper
    papers_not_3 = {paper: count for paper, count in paper_counts.items() if count != 3}
    if not papers_not_3:
        print("  [OK] All papers are assigned to exactly 3 annotators.")
    else:
        print(f"  [ERROR] The following papers do not have exactly 3 annotators:")
        for paper, count in papers_not_3.items():
            print(f"    - {paper}: {count} annotators")
            
    # 6. Conference distribution
    print("\n--- Conference Distribution (Unique Papers) ---")
    unique_conf_counts = collections.Counter()
    for paper in all_papers:
        conf_id = paper.split('_')[0]
        unique_conf_counts[conf_id] += 1
    
    for conf, count in unique_conf_counts.most_common():
        print(f"  - {conf}: {count} papers")
        
    print("\n--- Conference Distribution (Total Assignments) ---")
    for conf, count in conf_counts.most_common():
        print(f"  - {conf}: {count} assignments")
        
    print("\nVerification Complete.")

if __name__ == '__main__':
    main()
