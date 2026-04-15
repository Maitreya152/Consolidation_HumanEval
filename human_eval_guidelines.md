# Human Evaluation Guidelines: Consolidated vs. Raw Reviews

## Task Description

Evaluators will read the all the individual raw reviews provided. Then, they will rate each of the claims in the consolidated reviews based on the criteria as mentioned in Part-1. For Part-2, they will rate the consolidated review as a whole based on the criteria in Part-2.

---

## Part 1: Individual Claim Evaluation

**Step 1:** Read the Raw Reviews to familiarize yourself with the context.
**Step 2:** The consolidated review is already decomposed into distinct "claims". A claim is a single identifiable statement of a strength, weakness, question, or summary point.

*Examples of claims:*
- *Claim 1:* "The design of the test is done by health professionals, and the evaluation of answers is performed manually by at least two psychiatrists independently." (Strength)
- *Claim 2:* "The models used in the study are not domain adapted for mental health, which means the conclusions need to be re-assessed." (Weakness)
- *Claim 3:* "Would it be possible to test some fine-tuning of the systems, and if so, how can it be performed?" (Question)

For **each claim**, evaluate it along the following dimensions:

### Dimension A: Attribution & Support Level (Hallucination)
Where did this claim come from, and is it accurate based on the raw reviews?

- **[5] Excellent:** The claim is accurately drawn from at least one of the original raw reviews with no distortion.
  - *Example:*
    - *Raw review:* "The study should consider models which have been tailored to mental health ... Thus, the conclusions need to be re-assessed."
    - *Claim:* "The models used in the study are not domain adapted for mental health, which means the conclusions need to be re-assessed."
- **[4] Good:** The claim is mostly accurate but introduces a very slight alteration in tone or emphasis.
  - *Example:*
    - *Raw review:* "The models you have used are not domain adapted for mental health; useful to reconsider your evaluation results."
    - *Claim:* "The evaluation results are less reliable because the models used are not domain adapted for mental health." (Slight shift from 'useful to reconsider' to 'less reliable').
- **[3] Fair:** The root idea exists, but the claim noticeably alters the scope or nuance.
  - *Example:*
    - *Raw review:* "The improvements of the systems are based on improving the systems prompts but no fine-tuning of the systems have been performed."
    - *Claim:* "The authors completely ignored fine-tuning in favor of simple prompting." (Introduces a harsher, exaggerated tone).
- **[2] Poor:** The claim severely exaggerates, downplays, or distorts the original point.
  - *Example:*
    - *Raw review:* "It is not clear to me how others can reproduce the results. The LLM used is not described in detail."
    - *Claim:* "The paper is fundamentally flawed and useless due to un-reproducibility and missing model descriptions." (Forces a minor critique into a destructive flaw).
- **[1] Very Poor:** The claim is entirely fabricated or states the exact opposite of the raw reviews.
  - *Example:*
    - *Raw review:* "The evaluation has been performed manually labeling it by at least two psychiatrists independently."
    - *Claim:* "The evaluation lacked any human oversight and relied entirely on automated LLM metrics."

### Dimension B: Synthesis Quality (If applicable)
If the claim attempts to summarize a point discussed by multiple reviewers, how well does it capture the nuance?
- **[N/A]** Not applicable (point came from only one reviewer).
- **[5] Excellent:** Accurately merges points, perfectly capturing any differences in degree of concern.
  - *Example:* 
    - *Individual Point 1:* "The design of the test is done by health professionals, and so it is the evaluation of answers."
    - *Individual Point 2:* "The evaluation has been performed manually labeling it by at least two psychiatrists independently."
    - *Consolidated Claim:* "The design of the test is done by health professionals, and the evaluation of answers is performed manually by at least two psychiatrists independently." (Flawlessly combines the general professional design with the specific independent labeling).
- **[4] Good:** Merges points well, missing only very subtle nuances, but keeping the overall impression highly accurate.
  - *Example:* 
    - *Individual Point 1:* "The design of the test is done by health professionals, and so it is the evaluation of answers."
    - *Individual Point 2:* "The evaluation has been performed manually labeling it by at least two psychiatrists independently."
    - *Consolidated Claim:* "The evaluation was performed manually by two psychiatrists." (Merges them logically but loses the nuance that it was done *independently*).
- **[3] Fair:** Generally merges points, but some significant details or nuances among reviewers are lost.
  - *Example:* 
    - *Individual Point 1:* "The design of the test is done by health professionals, and so it is the evaluation of answers."
    - *Individual Point 2:* "The evaluation has been performed manually labeling it by at least two psychiatrists independently."
    - *Consolidated Claim:* "The evaluation was done manually by human mental health experts." (Loses the fact that it was *two* psychiatrists acting *independently*).
- **[2] Poor:** Oversimplifies or forces a "false consensus" where reviewers actually had subtly conflicting perspectives.
  - *Example:* 
    - *Individual Point 1:* "The paper provides the first steps towards an ethical framework and a way to evaluate how safe the LLMs are..."
    - *Individual Point 2:* "There is no previous work on how AI may augment the mental healthcare system... In the Discussion, the authors mention 'first of its kind framework' - similar suggestions have been made in the past (e.g. Stade et al. 2024)."
    - *Consolidated Claim:* "Reviewers had mixed feelings about the quality of the ethical framework." (Completely misses and fails to highlight the actual conflict regarding the *originality* of the framework vs past work).
- **[1] Very Poor:** Creates a completely incorrect impression of consensus that misleads the reader.
  - *Example:* 
    - *Individual Point 1:* "The paper provides the first steps towards an ethical framework..."
    - *Individual Point 2:* "In the Discussion, the authors mention 'first of its kind' - similar suggestions have been made in the past."
    - *Consolidated Claim:* "Reviewers unanimously praised the paper for introducing the first ethical framework of its kind." (Forces consensus and completely misleads the reader on a point of contention).

---

## Part 2: Overall Consolidated Review Evaluation

After evaluating all individual claims in the consolidated review, answer these common overarching questions using numerical scores to assess the general quality of the summary.

**Q1: Coverage & Omission**
Did the consolidated review capture all the substantive strengths, weaknesses, or questions that were raised in the raw reviews?
- **[5] Excellent:** All major and minor points were captured perfectly.
- **[4] Good:** All major points were captured, and nearly all minor points were captured.
- **[3] Fair:** All major points were captured, but several minor ones were missed.
- **[2] Poor:** Missed 1-2 key important points.
- **[1] Very Poor:** Missed multiple crucial strengths, weaknesses, or questions.

**Q2: Handling of Disagreement (If Applicable)**
If original reviewers fundamentally disagreed on a specific aspect (e.g., "R1 loved the novelty, R2 thought it was completely derivative"), how well did the consolidated review handle this conflict?
- **[N/A]** Reviewers generally had consensus; no major disagreements.
- **[5] Excellent:** The disagreement was explicitly captured, highlighted, and perfectly summarized.
- **[4] Good:** The disagreement was captured but the contrasting nature could have been made slightly clearer.
- **[3] Fair:** Mentioned the differing points but didn't clearly highlight that there was a conflict.
- **[2] Poor:** Attempted to blend the views into a vague compromise that misrepresents the strength of the divergence.
- **[1] Very Poor:** The summary ignored the conflict entirely, picking a side arbitrarily or acting as if everyone agreed.

**Q3: Redundancy & Flow**
Did the consolidated review combine repeating concepts efficiently, or does it feel like a repetitive list of copy-pasted sentences?
- **[5] Excellent:** Smooth, efficient, and well-grouped with effectively zero repetition.
- **[4] Good:** Reads very well but contains one or two very minor instances of repetition.
- **[3] Fair:** Reads decently, but contains some noticeable repetition of minor concepts.
- **[2] Poor:** Attempts to merge overlapping claims, but larger noticeable overlaps remain.
- **[1] Very Poor:** Fails to merge redundant claims entirely (e.g., states the exact same weakness three times).

---
