"""
app.py  —  Consolidated Review Human Evaluation
================================================
Run:  streamlit run app.py
Prereq: python prepare_data.py   (builds data/ from assignments.json + reviews/)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
DATA_DIR    = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"

SECTIONS = ["summary", "strengths", "weaknesses", "questions"]
SECTION_TITLES = {
    "summary":   "📝 Summary",
    "strengths": "✅ Strengths",
    "weaknesses":"⚠️ Weaknesses",
    "questions": "❓ Questions",
}

INSTRUCTION_CONTACT = "Yash More or Maitreya Chitale"


# ── helpers ───────────────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── data loading ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_available_usernames() -> list[str]:
    """Read all usernames from data/ directory (keys from assignments.json)."""
    if not DATA_DIR.exists():
        return []
    return sorted(
        p.stem for p in DATA_DIR.glob("*.json")
    )

@st.cache_data(show_spinner=False)
def load_bundle(username: str) -> dict:
    return read_json(DATA_DIR / f"{username}.json")


# ── results ───────────────────────────────────────────────────────────────────

def result_path(username: str) -> Path:
    return RESULTS_DIR / f"{username}.json"

def default_paper_result(paper_id: str) -> dict:
    return {
        "paper_id": paper_id,
        "section_rankings": {
            sec: {"ordering": [], "saved_at": None}
            for sec in SECTIONS
        },
        "last_saved_at": None,
    }

def load_result(username: str, assigned_papers: list[str]) -> dict:
    path = result_path(username)
    if path.exists():
        try:
            payload = read_json(path)
            if payload.get("username") == username:
                for pid in assigned_papers:
                    payload["responses"].setdefault(pid, default_paper_result(pid))
                payload.setdefault("current_paper_index", 0)
                payload.setdefault("completed", False)
                payload.setdefault("completed_at", None)
                return payload
        except Exception:
            pass
    payload = {
        "username": username,
        "assigned_papers": assigned_papers,
        "current_paper_index": 0,
        "responses": {pid: default_paper_result(pid) for pid in assigned_papers},
        "completed": False,
        "completed_at": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    save_result(payload)
    return payload

def save_result(payload: dict) -> None:
    payload["updated_at"] = utc_now()
    write_json(result_path(payload["username"]), payload)


# ── completion checks ─────────────────────────────────────────────────────────

def section_is_complete(sec_data: dict) -> bool:
    return bool(sec_data.get("ordering"))

def paper_sections_done(response: dict) -> int:
    return sum(1 for s in SECTIONS if section_is_complete(response["section_rankings"][s]))

def paper_is_complete(response: dict) -> bool:
    return paper_sections_done(response) == len(SECTIONS)

def completed_papers_count(result: dict) -> int:
    return sum(1 for pid in result["assigned_papers"] if paper_is_complete(result["responses"][pid]))


# ── ranking widget ────────────────────────────────────────────────────────────

def render_ranking_widget(
    result: dict,
    paper_id: str,
    section: str,
    display_labels: list[str],
    display_map: dict[str, str],   # display_label -> real_model_id
    read_only: bool,
) -> None:
    """
    Renders the drag-drop-style ranking UI using selectboxes in a chain.
    Annotator assigns each model a rank 1–N; ties are allowed.
    Stores the result as an ordered list of real model IDs (with ties as sub-lists).

    Result format stored:
        "ordering": [
            ["con-llama_consolidated_inf_final"],           # rank 1 (best)
            ["con-llama_highconf_inf", "con-multiref_..."], # rank 2 (tied)
            ["con-llama_inference_full_paper"]              # rank 3
        ]
    """
    username = result["username"]
    sec_data = result["responses"][paper_id]["section_rankings"][section]
    saved_ordering = sec_data.get("ordering", [])

    # Build a flat saved rank lookup: real_id -> rank int (1-based)
    saved_ranks: dict[str, int] = {}
    for rank_pos, group in enumerate(saved_ordering, 1):
        for rid in group:
            saved_ranks[rid] = rank_pos

    n = len(display_labels)
    rank_options = [str(i) for i in range(1, n + 1)]

    st.markdown("#### 🏆 Rank each model *(1 = best, ties allowed)*")
    st.caption(
        "Assign a rank to each model. Give two models the same rank to indicate a tie.\n"
        "Example: `Model A = 1, Model B = 1, Model C = 2, Model D = 3` means A and B are equally best."
    )

    header = st.columns([1, 1])
    header[0].markdown("**Model**")
    header[1].markdown("**Rank**")

    current_ranks: dict[str, int] = {}
    all_assigned = True

    for dl in display_labels:
        real_id = display_map[dl]
        key = f"rank_{username}_{paper_id}_{section}_{dl.replace(' ', '_')}"
        default_rank = str(saved_ranks.get(real_id, ""))
        if key not in st.session_state:
            st.session_state[key] = default_rank if default_rank else rank_options[0]

        col_label, col_rank = st.columns([1, 1])
        with col_label:
            st.markdown(f"**{dl}**")
        with col_rank:
            chosen = st.selectbox(
                "Rank",
                options=rank_options,
                key=key,
                disabled=read_only,
                label_visibility="collapsed",
            )
            current_ranks[real_id] = int(chosen)

    if read_only:
        st.info("Submission is locked — read only.")
        return

    # Build save button
    col_btn, col_status = st.columns([1, 2])
    with col_btn:
        if st.button(
            f"💾 Save {SECTION_TITLES[section]}",
            key=f"save_{paper_id}_{section}",
            type="primary",
        ):
            from collections import defaultdict
            groups: dict[int, list[str]] = defaultdict(list)
            for rid, r in current_ranks.items():
                groups[r].append(rid)
            ordering = [groups[r] for r in sorted(groups.keys())]

            sec_data["ordering"] = ordering
            sec_data["saved_at"] = utc_now()
            result["responses"][paper_id]["last_saved_at"] = utc_now()
            save_result(result)
            st.toast(f"✅ Saved {SECTION_TITLES[section]} for `{paper_id}`.", icon="✅")
            st.rerun()

    with col_status:
        if section_is_complete(sec_data):
            ts = sec_data.get("saved_at", "")
            st.success("✅ Saved" + (f" at {ts[:19]}" if ts else ""))
        else:
            st.info("Assign ranks then press Save.")


# ── section rendering (raw reviews + model outputs + ranking) ─────────────────

def render_section(
    result: dict,
    bundle: dict,
    paper_id: str,
    section: str,
    read_only: bool,
) -> None:
    paper   = bundle["papers"][paper_id]
    models  = paper["models"]           # display_label -> {section: text}
    model_ids = paper["model_ids"]      # display_label -> real_id
    display_labels = list(models.keys())
    display_map = {dl: model_ids[dl] for dl in display_labels}

    # ── 1. Raw reviews for this section ──────────────────────────────────────
    st.subheader(f"📰 Original Reviewer Feedback — {SECTION_TITLES[section]}")
    st.caption("Read *all* reviewer comments for this section before evaluating model outputs.")

    raw_reviews = paper.get("raw_reviews", [])
    if raw_reviews:
        for i, review in enumerate(raw_reviews, 1):
            with st.expander(f"Reviewer {i}", expanded=True):
                text = review.get(section, "")
                st.markdown(text if text else "*No content for this section.*")
    else:
        st.caption("*(No raw reviews available)*")

    st.divider()

    # ── 2. Model outputs for this section ─────────────────────────────────────
    st.subheader(f"🤖 Anonymized Model Outputs — {SECTION_TITLES[section]}")
    st.caption("Compare the model outputs below. Model names are anonymized to prevent bias.")

    tabs = st.tabs(display_labels)
    for tab, dl in zip(tabs, display_labels):
        with tab:
            text = models[dl].get(section, "")
            with st.container(border=True):
                st.markdown(text if text else "*No content provided.*")

    st.divider()

    # ── 3. Ranking widget ─────────────────────────────────────────────────────
    with st.container(border=True):
        render_ranking_widget(result, paper_id, section, display_labels, display_map, read_only)


# ── sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(result: dict) -> None:
    with st.sidebar:
        st.markdown("## 📋 Annotator Session")
        st.markdown(f"**Username:** `{result['username']}`")
        st.markdown(f"**Results file:** `results/{result['username']}.json`")

        st.markdown("---")
        done = completed_papers_count(result)
        total = len(result["assigned_papers"])
        st.progress(done / total)
        st.markdown(f"**{done} / {total}** papers fully complete")

        st.markdown("---")
        for pid in result["assigned_papers"]:
            resp = result["responses"][pid]
            secs_done = paper_sections_done(resp)
            icon = "✅" if paper_is_complete(resp) else ("🔄" if secs_done > 0 else "📄")
            st.markdown(f"{icon} `{pid}` — {secs_done}/{len(SECTIONS)} sections")

        st.markdown("---")
        if st.button("🚪 Log Out"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown(
            f"After final submit, please share your `results/{result['username']}.json` "
            f"file with **{INSTRUCTION_CONTACT}**."
        )


# ── instructions ──────────────────────────────────────────────────────────────

def render_instructions() -> None:
    st.markdown("""
### How to Annotate

1. **Log in** using your assigned username (e.g. `person-7` or a real name if provided).
2. You have **5 papers** to evaluate. Each paper has **4 sections**:
   `Summary → Strengths → Weaknesses → Questions`.
3. For **each section**:
   - First read **all original reviewer comments** (expanded at the top).
   - Then compare the **4 anonymized model outputs** (shown as tabs).
   - **Assign a rank** to each model (1 = best). Equal ranks are allowed — use the same number to indicate a tie.
   - **Note:** The best reviews are those which cover most of the points from the original reviewer comments.
4. Press **Save** after ranking each section. All 4 sections must be saved per paper.
5. Once all 5 papers are complete, press **Final Submit**.
6. Share your result file with **Yash More or Maitreya Chitale**.

> **Important:** Model names (Model A, B, C, D) are randomized per paper to prevent bias. 
> Your results are stored with the real model names for analysis.
""")


# ── login ─────────────────────────────────────────────────────────────────────

def render_login(available_usernames: list[str]) -> None:
    st.title("📄 Human Evaluation — Consolidated Paper Reviews")
    st.markdown("Welcome! Log in with your assigned username to begin your evaluation.")

    col1, col2 = st.columns([2, 3])
    with col1:
        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="e.g. person-7",
                help="Enter the username that was assigned to you."
            ).strip()
            submitted = st.form_submit_button("▶ Start Evaluating", type="primary")

        if submitted:
            if not username:
                st.error("Please enter your username.")
            elif username not in available_usernames:
                st.error(
                    f"Username `{username}` not found. "
                    "Please check your username or contact the study coordinator."
                )
            else:
                st.session_state["username"] = username
                st.rerun()

    with col2:
        render_instructions()


# ── completion panel ──────────────────────────────────────────────────────────

def render_completion_panel(result: dict) -> None:
    is_all_done = completed_papers_count(result) == len(result["assigned_papers"])

    with st.container(border=True):
        st.markdown("### 🎯 Final Submission")
        st.caption("You can edit any section until you submit. Submission locks your assignment.")

        if result["completed"]:
            st.success("✅ Submission received! This assignment is now read-only.")
            st.markdown(
                f"Please share your `results/{result['username']}.json` "
                f"file with **{INSTRUCTION_CONTACT}**."
            )
            return

        if not is_all_done:
            remaining = len(result["assigned_papers"]) - completed_papers_count(result)
            st.info(f"Please complete all sections for all papers first. ({remaining} paper(s) remaining)")
            return

        confirm = st.checkbox(
            "I have reviewed all five papers and am ready to lock my final submission.",
            key="final_submit_confirm",
        )
        if st.button("🔒 Final Submit", type="primary", disabled=not confirm):
            result["completed"] = True
            result["completed_at"] = utc_now()
            save_result(result)
            st.toast("🔒 Submission locked! Please share your results file.", icon="🔒")
            st.success("✅ Submission received! This assignment is now read-only.")


# ── main app ──────────────────────────────────────────────────────────────────

def render_app() -> None:
    username = st.session_state.get("username")
    available = load_available_usernames()

    if not username or username not in available:
        render_login(available)
        return

    bundle = load_bundle(username)
    result = load_result(username, bundle["assigned_papers"])
    render_sidebar(result)

    assigned_papers = bundle["assigned_papers"]

    st.title("📄 Human Evaluation — Consolidated Paper Reviews")


    eval_tab, instructions_tab = st.tabs(["📊 Evaluation", "📖 Instructions"])

    with instructions_tab:
        render_instructions()

    with eval_tab:
        done_papers = completed_papers_count(result)
        st.progress(
            done_papers / len(assigned_papers),
            text=f"{done_papers}/{len(assigned_papers)} papers complete"
        )

        paper_labels = [f"Paper {i+1}" for i in range(len(assigned_papers))]
        paper_tabs = st.tabs(paper_labels)

        for p_idx, paper_id in enumerate(assigned_papers):
            with paper_tabs[p_idx]:
                response = result["responses"][paper_id]
                secs_done = paper_sections_done(response)
                complete  = paper_is_complete(response)

                st.markdown(f"### Paper {p_idx + 1} of {len(assigned_papers)}")
                st.markdown(f"**Paper ID:** `{paper_id}`")
                st.progress(
                    secs_done / len(SECTIONS),
                    text="✅ All sections complete" if complete else f"{secs_done}/{len(SECTIONS)} sections saved"
                )

                sec_labels = [SECTION_TITLES[s] for s in SECTIONS]
                sec_tabs = st.tabs(sec_labels)

                for s_idx, section in enumerate(SECTIONS):
                    with sec_tabs[s_idx]:
                        render_section(
                            result, bundle, paper_id, section,
                            read_only=result["completed"],
                        )

        st.divider()
        render_completion_panel(result)


def main() -> None:
    st.set_page_config(
        page_title="Human Evaluation — Consolidated Reviews",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
    /* Widen main content area slightly */
    .block-container { max-width: 1200px; padding-top: 2rem; }
    /* Subtle highlight on expanders */
    .streamlit-expanderHeader { font-weight: 600; }
    /* Section divider spacing */
    hr { margin: 1.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

    available = load_available_usernames()

    if not available:
        st.error(
            "No annotator data files found in `data/`. "
            "Please run `python prepare_data.py` first."
        )
        return

    render_app()


if __name__ == "__main__":
    main()
