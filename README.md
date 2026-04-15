# AutoPeer – Human Evaluation Tool

A local Streamlit application for claim-level human evaluation of consolidated peer reviews.

---

## Setup

**Requirements:** Python 3.9+

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Consolidation_HumanEval

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

---

## How to Use

### Guidelines
Please read the [Human Evaluation Guidelines](human_eval_guidelines.md) before you begin.

### Login
Enter your unique **Annotator ID** (e.g. `ANN001`) on the login page.  
Your ID and assigned papers were sent to you by the study coordinator.

### Dashboard
After login you will see:
- An overview of your **3 assigned papers**
- Progress per paper (claims completed + overall rating)

### Annotating a Paper
Click **▶ Start** / **▶ Continue** on any paper card.

The annotation page has three tabs:

| Tab | What to do |
|-----|-----------|
| 📰 Raw Reviews | Read all original reviewer texts first |
| 🔍 Claim Evaluation | Rate each claim on **Attribution** and **Synthesis** (1–5 scale) |
| 📊 Overall Evaluation | Rate the consolidated review as a whole (Q1–Q3) |

Ratings are **auto-saved** to `results/<YOUR_ID>_results.json` every time you change a value.

### Sending Results
When you have completed all three papers, email the file  
`HumanEval/results/<YOUR_ID>_results.json` to the study coordinator.

---

## Rating Scales (quick reference)

### Part 1 – Claim Level

| Score | Attribution & Support | Synthesis Quality |
|-------|-----------------------|-------------------|
| 5 | Accurately drawn from ≥1 raw review | Perfect multi-reviewer merge |
| 4 | Mostly accurate, slight tone shift | Good merge, minor nuances lost |
| 3 | Root idea exists, noticeable alteration | Generally merged, significant details lost |
| 2 | Severe distortion | False consensus / oversimplification |
| 1 | Fabricated or opposite | Completely misleads |
| N/A | — | From only one reviewer |

### Part 2 – Overall

| Q | What it measures |
|---|-----------------|
| Q1 Coverage | Were all important points captured? |
| Q2 Disagreement | Were reviewer conflicts handled properly? |
| Q3 Redundancy | Was the review concise and non-repetitive? |

---

## File Structure

```
HumanEval/
├── app.py                      # Main Streamlit application
├── generate_assignments.py     # Assignment generator (run once by coordinator)
├── assignments.csv             # Annotator ↔ paper mapping
├── paper_coverage.csv          # Coverage verification
├── requirements.txt
├── README.md
├── human_eval_guidelines_claim_based.md
├── data/                       # Paper JSON files (raw + consolidated)
│   ├── <paper_id>_consolidated.json
│   └── <paper_id>_raw.json
└── results/                    # Created automatically; one file per annotator
    └── ANN001_results.json
```
