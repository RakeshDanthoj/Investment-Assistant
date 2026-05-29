# FinnWise PRD 2 — Gap Brainstorm Workshop

> Working document. Companion to `FinnWise_PRD2_Intelligence_Architecture.md`.
> Goal: pressure-test the 15 gap resolutions in PRD 2 through structured multi-persona debate, surface alternatives, and let the Product Owner make the final calls before the Solutions Architect designs.

---

## Personas

| Role | Name | Mandate |
|------|------|---------|
| **SPM** — Senior Product Manager | Priya | Customer-obsessed. Pushes for the simplest, most trust-building, fully functional UX. Treats budget as "no constraint" *within* the agreed PRD2 environment. |
| **INT** — Senior Interrogator | Vikram | Devil's advocate. Stress-tests every SPM claim against solo-builder reality, Render free tier, no live data, SEBI exploratory posture. Keeps the build real. |
| **SSA** — Senior Solutions Architect | Arjun | Silent until PO decides. Translates the final decision into a concise solution design — schema, API, algorithm, files, sequencing. |
| **PO** — Senior Product Owner | *You* | Final decision on critical areas before SSA picks up. Resolves SPM ↔ INT trade-offs. |

## Workshop rules

1. SPM and INT debate each gap for **at least 4 rounds** before converging.
2. Each gap closes with a short "Options for PO" block listing 2–3 distinct paths.
3. PO answers the decision questions. SSA then writes the solution design.
4. Hybrid baseline: PRD2's proposed solution is treated as **one** known option; SPM must explore 2–3 alternatives before defending or rejecting it.

## Non-negotiable constraints (carry-forward from PRD2)

- Solo builder. One person, three-role context switching.
- Render free tier API + GitHub Actions batch jobs. No paid tier.
- No live tester data. Synthetic seed only until further notice.
- SEBI posture is exploratory research. No buy/sell/hold. No fees.
- All inherited non-negotiables in PRD2 Section 10 still hold.

---

## Layer 1 — Confidence Scoring

> Covers **G-01** (scorer methodology) and **G-02** (routing thresholds). These are the P0 blockers that everything downstream depends on.

---

### Gap G-01 — Confidence score methodology is a black box

**PRD2 baseline:** Rule-based weighted scorer with 4 inputs: source_count (35%), source_quality (30%), factor_db_match (25%), recency (10%). Stored in `confidence_config.py`.

#### Round 1

**SPM (Priya):** Customers don't trust algorithms — they trust *evidence they can see*. The mental model that builds trust is "this came from N reputable sources within the last few hours." I want three big moves: (a) keep a numeric score for internal routing, but expose it to users as a **5-dot "Sourcing Strength"** UI element fed by source count × source tier; (b) every card has a tap-to-expand panel showing the four input contributions and the full source list with retrieved-at timestamps; (c) treat the score as a *side effect of explainability*, not the headline. We're optimising for trust, not for a number.

**INT (Vikram):** Hiding the number behind dots doesn't hide the problem — something still has to route HIGH/MEDIUM/LOW downstream, and a UI prettification on top of an undefined formula is just dressing up a black box. Also "N reputable sources within M hours" is *literally* what PRD2 already proposes: source_count + source_quality + recency. Where's the novelty? And without a clean numeric cutoff, the editorial queue has no rule for what auto-drafts vs what queues. You've solved the perception problem and left the routing problem untouched.

#### Round 2

**SPM (Priya):** Fair. Then keep PRD2's numeric scorer and weights, and add the explainability surface on top: every card exposes the four input contributions inline. The actual methodology fix isn't a new formula — it's making the existing formula auditable per card. Without that, when a card is wrong, the user can't tell whether it was thin sourcing, stale data, or a Factor DB miss. They just lose trust in the whole system, which is the worse failure mode.

**INT (Vikram):** Better, but you've now described a UI feature, not a methodology fix. G-01's actual question is "what are the inputs, weights, and output format" — PRD2 answers all three. The unanswered risk isn't the formula; it's that the four weights (0.35/0.30/0.25/0.10) are pulled from thin air. Worse: if source_count is 35% of the score and three NewsAPI results all parrot the same PTI wire story, we score that 1.0 — but it's really *one* source. You haven't fixed wire-story inflation. Fix that before touching UI.

#### Round 3

**SPM (Priya):** Good catch. Two ways to fix wire inflation: (a) add a "unique_provenance_count" input that uses a publisher-graph to collapse wire-pickups into the originator, or (b) lean harder on G-03's dedup_key so the same real-world event is one row regardless of how many outlets carried it, and source_count is counted *post-dedup*. Option (b) is far cheaper for a solo builder — no new parser, no new graph. The four weights stay the same; the input feeding source_count just gets cleaner.

**INT (Vikram):** Accepted — (b) is the right answer and it's free because G-03 is being built anyway. But you've created a hidden dependency: G-01's correctness now relies on G-03 being live first. If dedup breaks or misses an event, the scorer silently inflates. Need a guardrail: log every source_count > 5 as suspicious and route to editorial review regardless of computed score. Cheap insurance.

#### Round 4

**SPM (Priya):** Agreed. So G-01's converged shape: (1) keep PRD2's rule-based scorer formula and four-weight split; (2) source_count is counted **after** G-03 dedup, so wire inflation is handled upstream; (3) weights stay in `confidence_config.py`, tunable without redeploy; (4) every card exposes a "Why this confidence?" breakdown showing the four input contributions and the source list; (5) a `source_count > 5` flag escalates to editorial review even if the score is LOW — defensive guardrail. That's PRD2 + one dependency note + one UI hook + one guardrail. Cheap and trust-building.

**INT (Vikram):** I can live with that. Two open nits for PO: first, the initial weights (0.35/0.30/0.25/0.10) still need a defensible starting point before Week 2 calibration — right now they're vibes. Second, who decides when to *re-calibrate* weights after launch? If the solo builder eyeballs scores and tweaks weights manually, the system becomes unreproducible. Need a calibration *trigger*, not just a calibration *capability*.

#### Convergence — options for PO

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline as-is: rule-based scorer, fixed weights, Week 2 calibration. | Fastest. Wire-inflation risk unaddressed. |
| **B** (SPM+INT consensus) | PRD2 + post-dedup source counting + "Why this confidence?" UI breakdown + `source_count > 5` guardrail + defined re-calibration trigger. | Slightly more build. Significantly more auditable. |
| **C** | Replace rule-based scorer with Gemini Pro one-shot rating against a structured rubric (LLM-as-judge). | Abandons PRD2's debuggability principle. Adds LLM cost per event. |

#### 🔴 PO decision required — G-01

1. **Option A, B, or C?** (SPM and INT converged on B.)
2. **Re-calibration trigger** — what fires a weight-tuning ritual?
   - Time-based (monthly)
   - Event-count-based (every N new events)
   - Drift-based (override-rate from G-11 exceeds threshold)
3. **"Why this confidence?" UI breakdown** — Phase 3 must-have, or Phase 4 polish?

---

### Gap G-02 — HIGH/MEDIUM/LOW threshold values are arbitrary

**PRD2 baseline:** HIGH ≥ 0.75, MEDIUM ≥ 0.45 and < 0.75, LOW < 0.45. Calibrated against 10 historical events in Week 2.

#### Round 1

**SPM (Priya):** Three tiers is right, but the numbers shouldn't be hand-picked — they should be *outcomes of a target operational load*. Frame it as: "How many cards per day can the solo editor review without burning out?" If the answer is 8 HIGH cards/day, set the HIGH threshold so ~8/day cross it on average. Same logic for MEDIUM. The threshold serves the workload, not the math.

**INT (Vikram):** That's load-shedding dressed up as routing. You're saying we'd downgrade a genuinely high-confidence event from HIGH to MEDIUM because the editor is tired this week. That's a quality regression — the whole point of HIGH is "auto-draft + 2-hour override window" because the event is important enough to justify a fast path. Tying it to editor capacity inverts the user contract.

#### Round 2

**SPM (Priya):** Reframed: keep PRD2's 0.75 / 0.45 defaults but make them living numbers anchored to *override rate*, not to gut. Every month, look at the last 30 days of cards: how many crossed HIGH? How many got overridden as wrong? Tune the thresholds to keep override rate below 10% (which is PRD2's own V1 target in G-11). The threshold becomes data-driven, not workload-driven, not vibes.

**INT (Vikram):** Now we're talking — but you've made G-02 depend on G-11's measurement infrastructure being live. Without `signal_override_log` populated for at least 30 days, there's nothing to re-calibrate against. That means the first 30 to 60 days run on the original arbitrary 0.75 / 0.45 numbers — which is *exactly* the gap we're supposed to be closing. Are you comfortable telling PO: "the gap closes after 60 days of running with the gap open"?

#### Round 3

**SPM (Priya):** Yes, with one addition: anchor the *initial* 0.75 / 0.45 to a defensible starting point, not gut. Run the scorer against the 20 synthetic events from Section 7 — these have known historical outcomes I can hand-grade — and pick thresholds that correctly classify 16+ of 20 (80% on the seed). That's the Week 2 calibration exercise PRD2 already mentions, but with a concrete success metric. After Day 60, live override-rate from G-11 takes over.

**INT (Vikram):** Synthetic events don't have *real* override data — there's no real editor decision yet. You'd be hand-grading "should-have-been-HIGH" yourself, which is gut feel in costume. The 80% accuracy claim is meaningless if the ground truth is your own opinion. The honest framing: "thresholds are author-classified against 20 synthetic events as a sanity check, locked for 60 days, then driven by real override rate." Don't dress it up as data-driven when it's not yet.

#### Round 4

**SPM (Priya):** Accepted. So G-02 converges to: (1) initial defaults 0.75 / 0.45, labelled in code comments and in the monthly notes file as "author-classified provisional — not yet data-driven"; (2) `confidence_config.py` is the single source of truth, tunable without a deploy; (3) at Day 30 and Day 60, re-calibrate using real override-rate from G-11's log; (4) target stable override-rate ≤ 10%. Arbitrariness is acknowledged, not hidden.

**INT (Vikram):** Accepted. One more lever to put in front of PO: the MEDIUM band is 0.45–0.75 — that's 30 percentage points of ambiguous middle ground, and every event in that band lands in the editorial queue. A narrower MEDIUM (say 0.55–0.75) sends more events to LOW (silent log, daily digest only) and saves editor cycles, at the cost of missing borderline-but-real events. PO should pick how aggressive the silent-log zone is.

#### Convergence — options for PO

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | PRD2 baseline: 0.75 / 0.45 calibrated Week 2, then locked. | Simplest. Thresholds frozen on Day 0 author opinion. |
| **B** (SPM+INT consensus) | 0.75 / 0.45 provisional Day 0; re-calibrate Day 30 and Day 60 from override rate; target ≤ 10%. | Honest about uncertainty. Real data drives the numbers after 60 days. |
| **C** | Same as B, but narrower MEDIUM (0.55 / 0.75) — bigger LOW silent-log zone. | Reduces editor load. Risk of missing borderline-real events. |

#### 🔴 PO decision required — G-02

1. **Option A, B, or C?**
2. **Override-rate target** — confirm ≤ 10% (PRD2 V1) or pick a different number?
3. **MEDIUM band width** — wide (0.45–0.75, more editor work) or narrow (0.55–0.75, more silent logging)?
4. **Tie to G-01 question 2** — same re-calibration trigger for both scorer weights *and* thresholds, or separate?

---

> **⏸ Workshop paused.**
> Please answer the PO decision blocks for **G-01** and **G-02** above.
> Once answered, SSA (Arjun) will write the solution design for Layer 1, and we'll move to Layer 2 — Data Pipeline Integrity (G-03 through G-06).

---

*Document status: Layer 1 SPM ↔ INT rounds complete. Awaiting PO decisions before SSA design and Layer 2.*
