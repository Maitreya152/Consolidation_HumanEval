"""
AutoPeer Human Evaluation Tool
================================
Streamlit app for claim-level review evaluation.

Usage:
    streamlit run app.py

Results are saved to ./results/<annotator_id>_results.json
"""

import os
import json
import csv
import time
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Paths & constants
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSIGNMENTS_CSV = os.path.join(BASE_DIR, "assignments.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
GUIDELINES_MD = os.path.join(BASE_DIR, "human_eval_guidelines.md")

os.makedirs(RESULTS_DIR, exist_ok=True)

# Likert scale options
ATTRIBUTION_OPTIONS = {
    "– Select –": None,
    "5 – Excellent": 5,
    "4 – Good": 4,
    "3 – Fair": 3,
    "2 – Poor": 2,
    "1 – Very Poor": 1,
}

SYNTHESIS_OPTIONS = {
    "– Select –": None,
    "N/A – Single reviewer": "N/A",
    "5 – Excellent": 5,
    "4 – Good": 4,
    "3 – Fair": 3,
    "2 – Poor": 2,
    "1 – Very Poor": 1,
}

OVERALL_OPTIONS = {
    "– Select –": None,
    "5 – Excellent": 5,
    "4 – Good": 4,
    "3 – Fair": 3,
    "2 – Poor": 2,
    "1 – Very Poor": 1,
}

DISAGREEMENT_OPTIONS = {
    "– Select –": None,
    "N/A – No major disagreements": "N/A",
    "5 – Excellent": 5,
    "4 – Good": 4,
    "3 – Fair": 3,
    "2 – Poor": 2,
    "1 – Very Poor": 1,
}

# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_assignments():
    """Returns dict: annotator_id -> {name, paper_ids: list, calibration_paper}"""
    assignments = {}
    with open(ASSIGNMENTS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments[row["annotator_id"]] = {
                "name": row["name"],
                "paper_ids": row["paper_ids"].split(","),
                "calibration_paper": row["calibration_paper"],
            }
    return assignments


@st.cache_data
def load_paper_data(paper_id):
    """Returns (consolidated_data, raw_reviews_list)"""
    cons_path = os.path.join(DATA_DIR, f"{paper_id}_consolidated.json")
    raw_path = os.path.join(DATA_DIR, f"{paper_id}_raw.json")

    with open(cons_path) as f:
        consolidated = json.load(f)
    with open(raw_path) as f:
        raw = json.load(f)

    return consolidated, raw


@st.cache_data
def load_guidelines():
    with open(GUIDELINES_MD) as f:
        return f.read()


def results_path(annotator_id):
    return os.path.join(RESULTS_DIR, f"{annotator_id}_results.json")


def load_results(annotator_id):
    path = results_path(annotator_id)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_results(annotator_id, results):
    path = results_path(annotator_id)
    with open(path, "w") as f:
        json.dump(results, f, indent=2)


def extract_claims(consolidated):
    """Extract all claims from consolidated JSON into a flat list."""
    claims = []
    sections = ["summary", "strengths", "weaknesses", "questions", "divergent_perspectives"]
    for section in sections:
        val = consolidated.get(section)
        if val is None:
            continue
        if isinstance(val, str):
            claims.append({"section": section, "text": val})
        elif isinstance(val, list):
            for item in val:
                claims.append({"section": section, "text": str(item)})
    return claims


def paper_completion_status(annotator_id, paper_id, results):
    """Returns ('complete'|'in_progress'|'not_started', pct)"""
    if paper_id not in results:
        return "not_started", 0

    paper_res = results[paper_id]
    consolidated, _ = load_paper_data(paper_id)
    claims = extract_claims(consolidated)
    num_claims = len(claims)

    # Check claim annotations
    claim_anns = paper_res.get("claims", {})
    complete_claims = 0
    for ci in range(num_claims):
        c = claim_anns.get(str(ci), {})
        if c.get("attribution") is not None and c.get("synthesis") is not None:
            complete_claims += 1

    # Check overall
    overall = paper_res.get("overall", {})
    overall_done = all(
        overall.get(k) is not None for k in ["coverage", "disagreement", "redundancy"]
    )

    if num_claims == 0:
        pct = 100 if overall_done else 0
    else:
        claim_pct = complete_claims / num_claims
        overall_pct = 1.0 if overall_done else 0.0
        pct = int((claim_pct * 0.7 + overall_pct * 0.3) * 100)

    if complete_claims == num_claims and overall_done:
        return "complete", 100
    elif complete_claims > 0 or overall_done:
        return "in_progress", pct
    else:
        return "not_started", 0

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AutoRev – Human Evaluation",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Session state helpers
# ─────────────────────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "page": "login",           # login | dashboard | annotate
        "annotator_id": None,
        "annotator_info": None,
        "current_paper": None,
        "results": {},
        "claim_page": 0,
        "shuffled_papers": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar (visible after login)
# ─────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.title("🔬 AutoRev Eval")
        st.divider()
        if st.session_state.annotator_id:
            info = st.session_state.annotator_info
            st.markdown(f"**Annotator**")
            st.markdown(f"👤 {info['name']}")
            st.markdown(f"🔑 `{st.session_state.annotator_id}`")
            st.divider()

            results = st.session_state.results
            papers = info["paper_ids"]
            cal = info["calibration_paper"]

            st.markdown("**Your Papers**")
            # Use shuffled order from session state
            for pid in st.session_state.shuffled_papers:
                status, pct = paper_completion_status(
                    st.session_state.annotator_id, pid, st.session_state.results
                )
                icon = "✅" if status == "complete" else ("🔄" if status == "in_progress" else "📄")
                st.markdown(f"{icon} `{pid}` \n_{pct}% done_")

            st.divider()
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.session_state.current_paper = None
                st.rerun()

            if st.button("📖 Guidelines", use_container_width=True):
                st.session_state.page = "guidelines"
                st.rerun()

            st.divider()
            if st.button("🚪 Log Out", use_container_width=True):
                for k in ["annotator_id", "annotator_info", "current_paper", "results", "claim_page"]:
                    st.session_state[k] = None if k != "results" else {}
                st.session_state.page = "login"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Login
# ─────────────────────────────────────────────────────────────────────────────

def page_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔬 AutoRev")
        st.subheader("Human Evaluation Platform for Consolidated Review Quality")
        st.write("---")

        with st.container(border=True):
            st.markdown("### Enter Your Annotator ID")
            st.markdown("You should have received a unique ID in the format **ANN001**, **ANN002**, etc.")

            annotator_id = st.text_input(
                "Annotator ID", placeholder="e.g. ANN001", key="login_id_input"
            ).strip().upper()

            if st.button("🚀 Start Evaluation", type="primary", use_container_width=True):
                assignments = load_assignments()
                if annotator_id in assignments:
                    import random
                    st.session_state.annotator_id = annotator_id
                    st.session_state.annotator_info = assignments[annotator_id]
                    st.session_state.results = load_results(annotator_id)
                    
                    # Randomize papers for this session
                    papers = list(set(st.session_state.annotator_info["paper_ids"]))
                    random.shuffle(papers)
                    st.session_state.shuffled_papers = papers
                    
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error(f"❌ ID **{annotator_id}** not found. Please check your ID and try again.")

        # Info section
        with st.container(border=True):
            st.markdown("#### 📋 What to expect")
            st.markdown("""
- You have been assigned **10 papers** to evaluate
- Your papers are shared across multiple annotators to ensure quality
- For each paper you will evaluate **individual claims** from the consolidated review
- Then give an **overall rating** of the consolidated review
- Your progress is **auto-saved** to a local file after each submission
            """)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    info = st.session_state.annotator_info
    results = st.session_state.results
    papers = info["paper_ids"]
    cal = info["calibration_paper"]

    # ── Header ──────────────────────────────────────────────
    st.header(f"👋 Welcome, {info['name']}")
    st.markdown(f"ID: **{st.session_state.annotator_id}** | Papers assigned: **{len(papers)}**")
    st.divider()

    # ── Overall progress ─────────────────────────────────────
    completed = sum(
        1 for pid in papers
        if paper_completion_status(st.session_state.annotator_id, pid, results)[0] == "complete"
    )
    overall_pct = int(completed / len(papers) * 100)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Papers Assigned", len(papers))
    col_b.metric("Completed", completed)
    col_c.metric("Remaining", len(papers) - completed)

    st.progress(overall_pct / 100.0, text=f"Overall progress: {overall_pct}%")

    # ── Paper cards ───────────────────────────────────────────
    st.markdown("### Your Papers")

    for pid in st.session_state.shuffled_papers:
        status, pct = paper_completion_status(st.session_state.annotator_id, pid, results)

        badge_txt = "Completed" if status == "complete" else ("In Progress" if status == "in_progress" else "Not Started")

        consolidated, _ = load_paper_data(pid)
        claims = extract_claims(consolidated)
        num_claims = len(claims)

        with st.container(border=True):
            cols = st.columns([4, 1])
            with cols[0]:
                st.subheader(f"📄 {pid}")
                st.markdown(f"**Status:** {badge_txt} | **Conference:** {consolidated.get('conference','N/A')} | **Claims:** {num_claims}")
                st.progress(pct / 100.0, text=f"{pct}% complete")
            
            with cols[1]:
                btn_label = "✅ Review Again" if status == "complete" else ("▶ Continue" if status == "in_progress" else "▶ Start")
                # Use a more specific key to avoid any potential collision
                if st.button(btn_label, key=f"btn_paper_{st.session_state.annotator_id}_{pid}", use_container_width=True):
                    st.session_state.current_paper = pid
                    st.session_state.claim_page = 0
                    st.session_state.page = "annotate"
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Guidelines
# ─────────────────────────────────────────────────────────────────────────────

def page_guidelines():
    st.header("📖 Evaluation Guidelines")
    st.markdown("Read carefully before starting annotations")
    st.divider()

    guidelines = load_guidelines()
    st.markdown(guidelines)

    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Annotation
# ─────────────────────────────────────────────────────────────────────────────

def page_annotate():
    paper_id = st.session_state.current_paper
    if not paper_id:
        st.session_state.page = "dashboard"
        st.rerun()

    consolidated, raw_reviews = load_paper_data(paper_id)
    claims = extract_claims(consolidated)
    num_claims = len(claims)
    results = st.session_state.results
    paper_res = results.get(paper_id, {})
    claim_anns = paper_res.get("claims", {})
    overall_res = paper_res.get("overall", {})
    info = st.session_state.annotator_info
    cal = info["calibration_paper"]
    is_cal = paper_id == cal

    # ── Header ──────────────────────────────────────────────
    status, pct = paper_completion_status(st.session_state.annotator_id, paper_id, results)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.current_paper = None
            st.rerun()
            
    with col2:
        st.header(f"Paper: {paper_id}")
        st.markdown(f"**Conference:** {consolidated.get('conference','N/A')} | **Claims:** {num_claims} | **Progress:** {pct}%")
    st.divider()

    # ── Tabs ─────────────────────────────────────────────────
    tab_raw, tab_claims, tab_overall = st.tabs(
        ["📰 Raw Reviews", "🔍 Claim Evaluation", "📊 Overall Evaluation"]
    )

    # ── TAB 1: Raw Reviews ──────────────────────────────────
    with tab_raw:
        st.subheader("Raw Reviews")
        st.info("💡 Read these reviews carefully before evaluating the consolidated claims below.")

        if isinstance(raw_reviews, list):
            for i, review in enumerate(raw_reviews):
                with st.expander(f"Reviewer {i+1}", expanded=(i == 0)):
                    if isinstance(review, dict):
                        for field, val in review.items():
                            st.markdown(f"**{field.capitalize()}**")
                            st.markdown(val)
                    else:
                        st.markdown(review)
        elif isinstance(raw_reviews, dict):
            for field, val in raw_reviews.items():
                st.markdown(f"**{field.capitalize()}**")
                st.markdown(val)

    # ── TAB 2: Claim Evaluation ─────────────────────────────
    with tab_claims:
        st.subheader("Part 1: Claim-Level Evaluation")
        st.markdown(
            "For **each claim** in the consolidated review, rate it on Attribution & Support (A) "
            "and Synthesis Quality (B). [1 = Very Poor → 5 = Excellent]"
        )

        if num_claims == 0:
            st.warning("No claims found in this paper's consolidated review.")
        else:
            # Section grouping
            sections = list(dict.fromkeys(c["section"] for c in claims))

            for section in sections:
                section_claims = [(i, c) for i, c in enumerate(claims) if c["section"] == section]
                with st.expander(f"📌 {section.replace('_',' ').title()} ({len(section_claims)} claims)", expanded=True):
                    for claim_idx, claim in section_claims:
                        ann = claim_anns.get(str(claim_idx), {})
                        saved_attr = ann.get("attribution")
                        saved_syn  = ann.get("synthesis")
                        saved_note = ann.get("note", "")

                        with st.container(border=True):
                            # Claim text
                            st.info(f"**Claim {claim_idx+1}:** {claim['text']}")

                            col1, col2 = st.columns(2)

                            # Attribution
                            with col1:
                                attr_idx = list(ATTRIBUTION_OPTIONS.values()).index(saved_attr) \
                                    if saved_attr in ATTRIBUTION_OPTIONS.values() else 0
                                attr_label = list(ATTRIBUTION_OPTIONS.keys())[attr_idx]
                                new_attr_label = st.selectbox(
                                    "**A) Attribution & Support**",
                                    options=list(ATTRIBUTION_OPTIONS.keys()),
                                    index=list(ATTRIBUTION_OPTIONS.keys()).index(attr_label),
                                    key=f"attr_{paper_id}_{claim_idx}",
                                )
                                new_attr = ATTRIBUTION_OPTIONS[new_attr_label]

                            # Synthesis
                            with col2:
                                syn_idx = list(SYNTHESIS_OPTIONS.values()).index(saved_syn) \
                                    if saved_syn in SYNTHESIS_OPTIONS.values() else 0
                                syn_label = list(SYNTHESIS_OPTIONS.keys())[syn_idx]
                                new_syn_label = st.selectbox(
                                    "**B) Synthesis Quality**",
                                    options=list(SYNTHESIS_OPTIONS.keys()),
                                    index=list(SYNTHESIS_OPTIONS.keys()).index(syn_label),
                                    key=f"syn_{paper_id}_{claim_idx}",
                                )
                                new_syn = SYNTHESIS_OPTIONS[new_syn_label]

                            # Optional note
                            new_note = st.text_input(
                                "Optional note / justification",
                                value=saved_note,
                                key=f"note_{paper_id}_{claim_idx}",
                                placeholder="Any extra observations about this claim…",
                            )

                            # Auto-save on change
                            if new_attr != saved_attr or new_syn != saved_syn or new_note != saved_note:
                                if paper_id not in st.session_state.results:
                                    st.session_state.results[paper_id] = {}
                                if "claims" not in st.session_state.results[paper_id]:
                                    st.session_state.results[paper_id]["claims"] = {}
                                st.session_state.results[paper_id]["claims"][str(claim_idx)] = {
                                    "attribution": new_attr,
                                    "synthesis": new_syn,
                                    "note": new_note,
                                    "claim_text": claim["text"],
                                    "section": claim["section"],
                                }
                                save_results(st.session_state.annotator_id, st.session_state.results)

                            # Inline completion tick
                            if new_attr is not None and new_syn is not None:
                                st.success("✅ Saved successfully.")
                            else:
                                st.warning("⚠ Incomplete – please select both ratings")

    # ── TAB 3: Overall Evaluation ───────────────────────────
    with tab_overall:
        st.subheader("Part 2: Overall Consolidated Review Evaluation")
        st.markdown("After reviewing all claims, provide an overall assessment of the consolidated review.")

        with st.container(border=True):
            # Q1 Coverage
            saved_cov = overall_res.get("coverage")
            cov_idx = list(OVERALL_OPTIONS.values()).index(saved_cov) \
                if saved_cov in OVERALL_OPTIONS.values() else 0
            new_cov_label = st.selectbox(
                "**Q1: Coverage & Omission** – Did the consolidated review capture all substantive points?",
                options=list(OVERALL_OPTIONS.keys()),
                index=list(OVERALL_OPTIONS.keys()).index(list(OVERALL_OPTIONS.keys())[cov_idx]),
                key=f"cov_{paper_id}",
            )
            new_cov = OVERALL_OPTIONS[new_cov_label]

            # Q2 Disagreement
            saved_dis = overall_res.get("disagreement")
            dis_idx = list(DISAGREEMENT_OPTIONS.values()).index(saved_dis) \
                if saved_dis in DISAGREEMENT_OPTIONS.values() else 0
            new_dis_label = st.selectbox(
                "**Q2: Handling of Disagreement** – Did it handle conflicts between reviewers well?",
                options=list(DISAGREEMENT_OPTIONS.keys()),
                index=list(DISAGREEMENT_OPTIONS.keys()).index(list(DISAGREEMENT_OPTIONS.keys())[dis_idx]),
                key=f"dis_{paper_id}",
            )
            new_dis = DISAGREEMENT_OPTIONS[new_dis_label]

            # Q3 Redundancy
            saved_red = overall_res.get("redundancy")
            red_idx = list(OVERALL_OPTIONS.values()).index(saved_red) \
                if saved_red in OVERALL_OPTIONS.values() else 0
            new_red_label = st.selectbox(
                "**Q3: Redundancy & Flow** – Was the review efficient with minimal repetition?",
                options=list(OVERALL_OPTIONS.keys()),
                index=list(OVERALL_OPTIONS.keys()).index(list(OVERALL_OPTIONS.keys())[red_idx]),
                key=f"red_{paper_id}",
            )
            new_red = OVERALL_OPTIONS[new_red_label]

            # Free text
            saved_notes = st.text_area(
                "**General Notes** (optional)",
                value=overall_res.get("general_notes", ""),
                height=100,
                key=f"gnotes_{paper_id}",
                placeholder="Any additional comments about this consolidated review as a whole…",
            )
            new_notes = saved_notes

            all_overall_done = all(v is not None for v in [new_cov, new_dis, new_red])

            if st.button("💾 Save Overall Ratings", type="primary"):
                if not all_overall_done:
                    st.error("Please fill in all three overall rating questions before saving.")
                else:
                    if paper_id not in st.session_state.results:
                        st.session_state.results[paper_id] = {}
                    st.session_state.results[paper_id]["overall"] = {
                        "coverage": new_cov,
                        "disagreement": new_dis,
                        "redundancy": new_red,
                        "general_notes": new_notes,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                    save_results(st.session_state.annotator_id, st.session_state.results)
                    st.success("✅ Overall ratings saved!")
                    st.rerun()

            if all_overall_done:
                st.info("💡 Overall ratings have been filled. Don't forget to save!")

        # Completion summary
        st.markdown("---")
        st.subheader("Paper Completion Status")
        final_status, final_pct = paper_completion_status(
            st.session_state.annotator_id, paper_id, st.session_state.results
        )
        claims_done = sum(
            1 for ci in range(num_claims)
            if st.session_state.results.get(paper_id, {}).get("claims", {}).get(str(ci), {}).get("attribution") is not None
            and st.session_state.results.get(paper_id, {}).get("claims", {}).get(str(ci), {}).get("synthesis") is not None
        )
        
        st.progress(final_pct / 100.0, text=f"{final_pct}% complete | Claims: {claims_done}/{num_claims} | Overall: {'✅' if all_overall_done and overall_res.get('coverage') is not None else '⏳'}")

        if final_status == "complete":
            st.success("🎉 This paper is fully annotated! You can go back to the dashboard.")
            if st.button("← Back to Dashboard", key="done_back_btn"):
                st.session_state.page = "dashboard"
                st.session_state.current_paper = None
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

render_sidebar()

page = st.session_state.page

if page == "login":
    page_login()
elif page == "dashboard":
    if not st.session_state.annotator_id:
        st.session_state.page = "login"
        st.rerun()
    page_dashboard()
elif page == "annotate":
    if not st.session_state.annotator_id:
        st.session_state.page = "login"
        st.rerun()
    page_annotate()
elif page == "guidelines":
    if not st.session_state.annotator_id:
        st.session_state.page = "login"
        st.rerun()
    page_guidelines()
