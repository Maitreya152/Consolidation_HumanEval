# Consolidated Review Human Evaluation — Annotator Guide

Thank you for participating in this study! This guide explains how to set up and run the annotation tool on your machine.

---

## Step 1 — Install Python dependencies

Open a terminal in this folder and run:

```bash
pip install -r requirements.txt
```

---

## Step 2 — Build your data bundle

```bash
python prepare_data.py
```

This prepares the review data for all annotators. You only need to run this **once**.

---

## Step 3 — Launch the app

```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## Step 4 — Log in

Enter the **username** you were assigned (e.g. `manav`, `ketaki`). If you are unsure of your username, contact Yash More or Maitreya Chitale.

---

## Step 5 — Annotate

You have **5 papers** to evaluate. For each paper, you will go through **4 sections** in order:

> **Summary → Strengths → Weaknesses → Questions**

For each section:

1. **Read all the original reviewer comments** shown at the top. These are the real reviews submitted by human reviewers for that paper.
2. **Compare the 4 model outputs** shown as tabs (Model A, B, C, D). These are AI-generated consolidated reviews — the model names are anonymized to avoid bias.
3. **Assign a rank** to each model using the dropdowns:
   - `1` = best, `4` = worst
   - **Ties are allowed** — give two models the same rank if you think they are equally good (e.g. both get `1`, and the next best gets `2`)
4. Click **💾 Save** to save your ranking for that section.

Repeat for all 4 sections, then move to the next paper.

---

## Step 6 — Final Submit

Once all 5 papers are fully saved, a **Final Submit** button will appear at the bottom of the page. Check the confirmation box and click it to lock your responses.

---

## Step 7 — Share your results

After submitting, please share your results file with **Yash More or Maitreya Chitale**. Your results file is located at:

```
results/<your-username>.json
```

---

## Tips

- **Progress is saved automatically** each time you click Save on a section. If you close the app and reopen it, your saved sections will be restored when you log back in.
- You do **not** need to complete everything in one sitting — save as you go and resume anytime.
- If you run into any issues, contact **Yash More or Maitreya Chitale**.
