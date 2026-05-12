"""
prepare_data.py
---------------
Reads:
  - assignments.json          (username -> [paper_ids])
  - reviews/raw-reviews/      (paper_id.json  -> list of raw reviewer dicts)
  - reviews/<model_dir>/      (paper_id.json  -> consolidated model output dict)

Produces:
  - data/<username>.json      (one bundle per annotator, consumed by app.py)

Run once (or re-run after any data change):
    python prepare_data.py
"""

import json
import random
import sys
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).resolve().parent
ASSIGNMENTS = BASE / "assignments.json"
REVIEWS_DIR = BASE / "reviews"
RAW_DIR     = REVIEWS_DIR / "raw-reviews"
DATA_DIR    = BASE / "data"

# ── model directories (real model IDs) ────────────────────────────────────────
# Add / remove entries here if models change.
MODEL_DIRS = [
    "con-llama_consolidated_inf_final",
    "con-llama_highconf_inf",
    "con-llama_inference_full_paper",
    "con-multiref_llama_inf_14000",
]

SECTIONS = ["summary", "strengths", "weaknesses", "questions"]


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(f"- {str(item).strip()}" for item in value if str(item).strip())
    return str(value).strip()


def load_raw_reviews(paper_id: str) -> list[dict]:
    path = RAW_DIR / f"{paper_id}.json"
    if not path.exists():
        print(f"  [WARN] Missing raw review: {path.name}")
        return []
    raw = read_json(path)
    if not isinstance(raw, list):
        raw = [raw]
    return [
        {sec: normalize(r.get(sec, "")) for sec in SECTIONS}
        for r in raw
    ]


def load_model_output(model_dir: str, paper_id: str) -> dict | None:
    path = REVIEWS_DIR / model_dir / f"{paper_id}.json"
    if not path.exists():
        return None
    data = read_json(path)
    return {sec: normalize(data.get(sec, "")) for sec in SECTIONS}


def build_bundle(username: str, paper_ids: list[str]) -> dict:
    """
    Bundle structure (matches what app.py expects):
    {
      "username": "...",
      "assigned_papers": [...],
      "papers": {
        "<paper_id>": {
          "paper_id": "...",
          "raw_reviews": [...],       # list of {section: text}
          "models": {
            "Model A": {section: text, ...},   # shuffled display labels
            ...
          },
          "model_ids": {
            "Model A": "<real_model_dir_id>",  # mapping display → real
            ...
          }
        }
      }
    }
    The shuffle is baked in at data-prep time so results are stable across
    re-runs of prepare_data.  Re-running prepare_data WILL re-shuffle, so
    only run it once per study cycle.
    """
    papers = {}
    display_letters = ["A", "B", "C", "D"]

    for paper_id in paper_ids:
        raw_reviews = load_raw_reviews(paper_id)

        # Load each model's output for this paper
        available_models: list[tuple[str, dict]] = []
        for model_dir in MODEL_DIRS:
            output = load_model_output(model_dir, paper_id)
            if output is not None:
                available_models.append((model_dir, output))
            else:
                print(f"  [WARN] {model_dir}/{paper_id}.json not found, skipping model.")

        if not available_models:
            print(f"  [ERROR] No model outputs found for {paper_id}. Skipping paper.")
            continue

        # Shuffle to remove position bias
        shuffled = available_models[:]
        random.shuffle(shuffled)

        models = {}
        model_ids = {}
        for i, (real_id, content) in enumerate(shuffled):
            label = f"Model {display_letters[i]}"
            models[label] = content
            model_ids[label] = real_id

        papers[paper_id] = {
            "paper_id": paper_id,
            "raw_reviews": raw_reviews,
            "models": models,
            "model_ids": model_ids,
        }

    return {
        "username": username,
        "assigned_papers": paper_ids,
        "papers": papers,
    }


def main():
    if not ASSIGNMENTS.exists():
        sys.exit(f"[ERROR] assignments.json not found at {ASSIGNMENTS}")

    assignments: dict[str, list[str]] = read_json(ASSIGNMENTS)
    print(f"Found {len(assignments)} annotators in assignments.json")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── Remove stale files not in current assignments ─────────────────────────
    expected_files = {f"{username}.json" for username in assignments}
    stale = [p for p in DATA_DIR.glob("*.json") if p.name not in expected_files]
    if stale:
        print(f"\nRemoving {len(stale)} stale file(s) from data/:")
        for p in stale:
            print(f"  - {p.name}")
            p.unlink()
    else:
        print("No stale files to remove.")

    # ── Write bundles (skip existing to preserve model shuffle) ──────────────
    print()
    skipped, created = 0, 0
    for username, paper_ids in assignments.items():
        out_path = DATA_DIR / f"{username}.json"
        if out_path.exists():
            print(f"  [SKIP]   {username}  — data file already exists, shuffle preserved.")
            skipped += 1
        else:
            print(f"  [CREATE] {username}  ({len(paper_ids)} papers)")
            bundle = build_bundle(username, paper_ids)
            write_json(out_path, bundle)
            created += 1

    print(f"\nSummary: {created} created, {skipped} skipped, {len(stale)} stale removed.")

    print(f"\nDone! Data files written to: {DATA_DIR}")
    print("You can now run the Streamlit app with:  streamlit run app.py")


if __name__ == "__main__":
    main()
