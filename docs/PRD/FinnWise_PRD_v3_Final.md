# FinnWise — Product Requirements Document
## Version 3.0 · Final · Research Project · Indian Stock Market Focus

**Tagline:** Understand before you invest

| Attribute | Value |
|---|---|
| Target Users | Young Indian professionals, 22–35 |
| Market | NSE / BSE India |
| Project Type | Solo research project |
| Timeline | 3-month V1 build |
| Screens Designed | 5 of 5 — All Final |
| Document Status | Final — supersedes all previous versions |

> **⚠ SEBI DISCLAIMER:** This application generates AI-powered market analysis for educational and research purposes only. It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013. No fee is charged. No personalised investment advice is provided.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Target Users & Personas](#3-target-users--personas)
4. [Product Architecture — Five Surfaces](#4-product-architecture--five-surfaces)
5. [Screen Design Specifications — All Five Screens Final](#5-screen-design-specifications--all-five-screens-final)
   - [Screen 1 — Onboarding](#screen-1--onboarding--three-question-conversational-flow)
   - [Screen 2 — The Pulse](#screen-2--the-pulse--personalised-event-feed)
   - [Screen 3 — The Thread](#screen-3--the-thread--event-intelligence-card-living-card)
   - [Screen 4 — The Mirror](#screen-4--the-mirror--personal-learning-history--prediction-tracking)
   - [Screen 5 — The Lens](#screen-5--the-lens--on-demand-event-intelligence-card-generator)
6. [Intelligence Architecture](#6-intelligence-architecture)
7. [Data Architecture](#7-data-architecture)
8. [UI Design System — Final](#8-ui-design-system--final)
9. [Technology Stack](#9-technology-stack)
10. [Phased Roadmap](#10-phased-roadmap)
11. [Compliance & Legal Requirements](#11-compliance--legal-requirements)
12. [Risks & Mitigations](#12-risks--mitigations)
13. [Success Metrics for V1](#13-success-metrics-for-v1)
14. [Permanently Out of Scope](#14-permanently-out-of-scope)
- [Appendix A — Glossary](#appendix-a--glossary)

---

## 1. Executive Summary

FinnWise is a financial reasoning companion — not a recommendation engine and not a news aggregator. It connects world events to investment implications through a structured learning process, designed for intelligent young Indian professionals who are starting their investment journey and want to understand before they act.

> **Product Definition:** FinnWise connects world events to investment implications through a structured learning process. The recommendation is almost incidental. The real product is contextual financial intelligence for someone who pays attention to the world but does not yet have the mental models to connect what they see to what they should do.

### Three Differentiating Pillars

- **Reasoning transparency** — every Event Intelligence Card traces the causal chain from world event to specific instrument, with every assumption labelled as Measured, Modelled, or Judged
- **Bias honesty** — a full audit log tracks information biases in the data pipeline and recommendation engine, surfacing them prominently to the user before they read the analysis
- **Mental model transfer** — every card ends with a plain-English description of the reasoning framework used, so users can apply it independently to future events the app has not covered

---

## 2. Problem Statement

### 2.1 The Gap in the Market

Young Indian professionals entering the investment market face a fundamental trust problem. Existing tools either:
- Provide black-box recommendations with no reasoning
- Overwhelm with raw data without synthesis
- Deliver biased content through sponsored recommendations
- Assume prior financial literacy that first-time investors simply do not have

### 2.2 The Specific Problem FinnWise Solves

When a significant world event occurs — a geopolitical conflict, a central bank decision, a trade deal, a supply shock — a curious young investor hears about it and asks: *what does this mean for my money?* No tool in the Indian retail market answers that question honestly, completely, and educationally. FinnWise does.

The 19-question framework that inspired this product represents the natural reasoning process of an intelligent person trying to connect a world event to a financial decision. FinnWise carries the spirit of those questions — honest, causal, source-attributed reasoning — in every Event Intelligence Card it produces.

### 2.3 The Bias Problem Nobody Solves

AI and algorithm-driven financial tools suffer from systematic biases never disclosed to users:

- **Recency bias** — over-weighting the last 3–6 months of data
- **Sector concentration bias** — recommending whatever sectors have recent positive news cycles
- **Narrative bias** — over-indexing on compelling stories without fundamental support
- **Editorial bias** — invisible curation of which events are covered and which are not
- **Survivorship bias** — training on stocks that still exist, ignoring companies that failed

FinnWise surfaces all of these biases transparently, including its own editorial bias — a disclosure of which event categories are and are not being monitored in the current period.

---

## 3. Target Users & Personas

### 3.1 Design Target — The Middle of the Distribution

FinnWise is designed for the **40th–60th percentile of financial literacy** among young Indian professionals. Not the complete beginner who needs basic financial education. Not the expert who already has professional tools.

The person who:
- Understands that stocks go up and down
- Has heard of Sensex and Nifty
- Knows inflation is bad for savings
- Has probably done an SIP somewhere
- But cannot read a balance sheet and has never traced a geopolitical event to a specific stock

### 3.2 Three-Question Onboarding — Mode Detection

The app distinguishes between Portfolio Builders and Portfolio Protectors through three plain-English conversational questions — no forms, no sliders, no financial jargon:

1. **Are you starting fresh or do you already have investments?** → Starting fresh / I have some investments / Just curious for now
2. **How much are you thinking of investing?** → Free text amount with monthly / one-time toggle
3. **How long are you thinking of staying invested?** → Under 1 year / 1–3 years / 3–7 years / 7+ years

### 3.3 Personas

| Attribute | Priya Sharma — Portfolio Builder | Arjun Mehta — Portfolio Protector |
|---|---|---|
| Age / Role | 27, Software engineer | 31, Product manager |
| Income | ₹12–18L pa, ₹15–30K investable monthly | ₹25–35L pa, ₹40–80K investable monthly |
| Status | No portfolio — wants to start | Has SIPs and direct stocks — wants to protect & grow |
| Frustration | Hears world events, does not know what they mean for money | Overwhelmed by reading. Wants synthesised, event-driven view |
| Goal | Build ₹20L portfolio over 5 years. Understand what she owns and why | Understand how events affect existing holdings. Add positions intelligently |
| Fear | Making uninformed decisions. Being misled by overconfident tools | Missing a risk signal. Making emotionally driven decisions during volatile periods |
| First surface shown | **The Map** — learn sectors before selecting instruments | **The Pulse** — events affecting what is already at stake |

---

## 4. Product Architecture — Five Surfaces

FinnWise is a web application with five distinct surfaces. Navigation on desktop uses a persistent left sidebar (220px wide). On mobile, the sidebar collapses to a top navigation bar.

| # | Surface Name | Primary Purpose | Phase | Shown To First |
|---|---|---|---|---|
| 1 | **The Pulse** | Home screen. Personalised event feed. Financial implication leads, event is context. | Phase 1 | Portfolio Protectors |
| 2 | **The Thread** | Full Event Intelligence Card. Core product experience. ICE Stack — Insight, Context, Evidence. Living Card lifecycle. | Phase 1 | All users |
| 3 | **The Map** | Sector learning layer. Eight sectors of the Indian economy. Navigable. Preparation layer for event-driven learning. | Phase 1 | Portfolio Builders |
| 4 | **The Mirror** | Personal learning history. Prediction tracking. Reasoning gap analysis. No rupee performance shown. | Phase 2 | All users |
| 5 | **The Lens** | On-demand Event Intelligence Card generation. Deliberate research mode. 30–90 second response time. | Phase 2 | All users |

---

## 5. Screen Design Specifications — All Five Screens Final

All five screens have been designed, reviewed, and approved as interactive HTML/CSS/JS prototypes. The prototypes are the design specification for V1 development. This section documents every design decision made for each screen. These decisions are final and binding on the development build.

---

### Screen 1 — Onboarding — Three-Question Conversational Flow

**Phase:** Phase 1 | **Status:** ✅ Designed & Approved

> *"The first thing you see should feel like a question, not a form."*

#### Intent

Collect three data points to detect user mode (Portfolio Builder vs Portfolio Protector) and route them to the correct first surface. Establish that FinnWise is a companion that asks before it acts — not a tool that assumes.

#### Layout

Split-screen on desktop:
- **Left panel** — dark navy brand panel, 420px fixed width. Wordmark, manifesto quote, three product pillars, legal footer. Present on all four steps.
- **Right panel** — white onboarding panel. Progress dots, questions, inputs, CTA.
- **Mobile** — brand panel hidden. Onboarding panel full-width single column.

#### Components

| Component | Description |
|---|---|
| **Brand Panel (Left)** | Dark navy (#0F172A) background. Playfair Display 28px wordmark in white. Italic manifesto quote in Playfair Display 22px. Three product pillars as bullet items with blue (#1A4FCC) dots. Legal footer in DM Mono 10px. Radial gradient overlays for depth — no images. |
| **Progress Dots** | Three dots above each question. Active: blue (#1A4FCC), 1.2× scale. Completed: slate-400. Pending: slate-200. No percentage bar. Dots signal a conversation, not a form completion. |
| **Step 1 — Investment Status** | Three full-width option buttons. Left-aligned radio + label + description. Selected state: blue border (1.5px), blue-tinted background (#EEF3FF). Options: "Starting fresh" / "I have some investments" / "Just curious for now" |
| **Step 2 — Amount Input** | Rupee prefix box (₹) + free text input field. Monthly / One-time toggle below as two-segment control. No sliders. No preset amounts. User types their own number. |
| **Step 3 — Time Horizon** | 2×2 grid of horizon option cards. Under 1 year / 1–3 years / 3–7 years / 7+ years. Period in bold 14px, label below in DM Mono 10px. Selected: blue border + blue-tinted background. |
| **Step 4 — Mode Result** | Full-width result card. Detected mode (Portfolio Builder or Portfolio Protector) in Playfair Display 20px. One-sentence explanation of starting surface. Preview of all four surfaces with icons. Single CTA: "Enter FinnWise →" |
| **SEBI Bar** | Persistent red disclaimer footer across all four steps. DM Mono 10px. Red background (#FEF2F2), red top border (#FECACA). Never a popup. |

#### Design Decisions — Final

| Decision | Rationale |
|---|---|
| **No forms** | Questions are conversational — plain English with no financial jargon. "How much are you thinking of investing?" not "Investment amount (INR)". The framing signals that FinnWise is a companion, not a data-collection tool. |
| **No sliders** | Sliders imply precision that does not exist. Free text for amount. Discrete horizon options instead of a year slider. User commitment to the answer is higher when they type it themselves. |
| **Mode detection is transparent** | Step 4 tells the user which mode was detected and why. No hidden routing. The user sees the logic and can understand why they're being taken where they're going. |
| **Portfolio Builder → The Map first** | Users with no investments are shown sector learning before event cards. Understanding how sectors work is more valuable than reading event cards they cannot yet interpret. |
| **Portfolio Protector → The Pulse first** | Users with existing investments need to know what is happening right now that affects what they own. The event feed is the right first surface for them. |
| **Progress dots not a progress bar** | Three dots clearly signal three questions. A progress bar implies effort; three dots imply a quick conversation. |
| **Split layout brand panel** | The dark navy left panel establishes FinnWise's editorial identity immediately. First impression is Economist-like authority, not fintech brashness. |
| **SEBI disclaimer persistent across all steps** | The disclaimer is not a modal the user dismisses after onboarding. It is a footer element present on every step. Compliance by design, not by popup. |

---

### Screen 2 — The Pulse — Personalised Event Feed

**Phase:** Phase 1 | **Status:** ✅ Designed & Approved

> *"The financial implication leads. The event is context."*

#### Intent

The home screen for Portfolio Protectors and the entry point to event cards for all users. Shows a live feed of Event Intelligence Cards filtered by user profile. Communicates financial consequences first — never news headlines.

#### Layout

- Left sidebar navigation, 220px, persistent on desktop
- Two-column main area: feed column (~60% width, scrollable) + insight panel (~40% width, sticky, updates live on card selection)
- Category filter pills in topbar — not in the feed column
- Single column on mobile — insight panel hidden, tap-through to full Thread

#### Components

| Component | Description |
|---|---|
| **Left Sidebar** | White background, 220px. Wordmark + tagline at top (border-bottom). Nav group label "Surfaces" in DM Mono 9px uppercase. Five nav items. Active: blue-tinted background (#EEF3FF), blue text (#1A4FCC), medium weight. Phase 2 items show grey badge. User profile chip at bottom (border-top). |
| **Topbar** | White, 56px, sticky. "The Pulse" in Playfair Display 20px (left). Category filter pills in DM Mono 10px inline in topbar. Active pill: navy background, white text. Event count + last-updated timestamp (right, DM Mono 10px slate-400). |
| **Fog of War Banner** | Full-width amber warning banner below topbar. Visible only when 3+ major events are simultaneously active. Warning icon + "Fog of War" label + one-sentence explanation of why confidence is suppressed. User sees uncertainty first, analysis second. |
| **Event Card** | White card, 1px slate-200 border, rounded corners. Financial consequence headline in Playfair Display 15px bold. Event context in Inter 12px slate-500 italic. Category tag (colour-coded) + horizon tag + timestamp. Direction confidence dot (separate from magnitude). Magnitude confidence dot (separate from direction). 3–4 instrument chips (green/red/amber). Selected state: 3px blue left border, blue-tinted background. |
| **Insight Panel (Right)** | Sticky, white, 1px left border. Updates instantly on card selection (no page navigation). Event tag + headline + context text. Confidence trio grid (direction / magnitude / last reviewed). 4 mini instrument assessment cards with signal colour dots and verdict labels. Single CTA: "Read full analysis in The Thread →". Generation timestamp below CTA. |
| **Resolved Badge** | Green pill "Resolved" shown inline in card event-tag row. Resolved cards remain in feed — they are part of the track record. |

#### Design Decisions — Final

| Decision | Rationale |
|---|---|
| **Financial implication leads** | Not "Strait of Hormuz closes" but "Domestic oil producers stand to gain. Aviation, paint, and logistics face real margin pressure." The consequence is the headline. The event is the subordinate context. This is a language rule enforced on every card. |
| **Direction and magnitude are separate** | Direction confidence and magnitude confidence are displayed as two separately labelled dots. A model can be highly confident in the direction of impact while deeply uncertain about its magnitude. Conflating them into a single rating is dishonest. They are never combined. |
| **Two-column with live insight panel** | The right panel updates live as users scroll the feed, avoiding full-page navigation for quick card browsing. Deep reads go to The Thread. Shallow browsing stays in The Pulse. |
| **Fog of War as a first-class UI feature** | When multiple major events interact simultaneously and the model's confidence is suppressed, a banner declares this before any analysis is shown. Confidence before conclusion is a product philosophy decision, not a footnote. |
| **Category filter pills in topbar** | Filters are in the topbar to keep the feed column uncluttered. Pills are the minimum-friction interaction — one tap to filter, one tap to reset to All. |
| **Resolved cards stay in feed** | Hiding resolved cards would create survivorship bias in the visible feed. Resolved cards with their track record are part of the product's credibility — they are not removed. |

#### Language Rules

- Event cards never use "buy", "sell", or "hold" language
- Instrument chips use only: `opportunity signal` / `headwind signal` / `watch`
- No price targets or return expectations on any card
- Confidence levels always accompanied by their text label — never shown as bare numbers or stars

---

### Screen 3 — The Thread — Event Intelligence Card (Living Card)

**Phase:** Phase 1 | **Status:** ✅ Designed & Approved

> *"A living analytical document. Not a static article published once and forgotten."*

#### Intent

The core product experience. A complete Event Intelligence Card that evolves with the event it tracks through a defined lifecycle. Users choose how deep to go via the ICE tab structure. Every assumption is labelled. Every source is cited. The analysis evolves as the event develops.

#### Layout

- Left sidebar (same as Pulse)
- Topbar: breadcrumb navigation (← The Pulse / Event Name), lifecycle badge with pulsing dot (Active · Week N of 4), Current/Original view toggle (two-segment control, top right)
- Two-column content: article body (left, max 720px) + aside panel (right, 300px, sticky)
- Mobile: single column, aside hidden or stacked below article

#### ICE Stack Architecture

The Thread is built on a three-layer architecture. Users choose how deep they go.

| Layer | Name | Content | Access |
|---|---|---|---|
| **I** | Insight | Plain English summary. Instrument assessments with entry/exit conditions. Dissenting view. Prediction logger. Framework Behind This. | Always visible — no tap required |
| **C** | Context | Numbered step-by-step causal chain from event to sector to instrument. Each step labelled with MMJ confidence tag. | One tap to reveal |
| **E** | Evidence | Full source table. Every number with source name, date retrieved, freshness dot, and MMJ type. | Second tap to reveal |

#### Living Card Lifecycle

Every card progresses through a defined lifecycle, visible in the aside panel at all times:

1. **Draft** — being generated, not yet visible to users
2. **Published** — card live, all signals in Pending state, track record timestamp logged
3. **Active** — event ongoing, signals monitored, card updating
4. **Signal Triggered** — one or more signals have fired, instrument assessments updated
5. **Thesis Confirmed** — primary thesis validated by events, track record updated
6. **Thesis Weakened / Invalidated** — partial or full invalidation, stated explicitly, track record updated
7. **Resolved** — event concluded, Mirror notifies users whose predictions can be graded
8. **Archived** — historical record, Original View always accessible

#### Components

| Component | Description |
|---|---|
| **Article Header** | Event category tag + horizon tags + publication date. Playfair Display 28px bold title. Inter 16px light (font-weight 300) deck text. ICE tabs: I — Insight / C — Context / E — Evidence. DM Mono 11px, blue underline on active, 2px bottom border. |
| **I — Insight Tab** | Always visible, no tap required. Summary paragraphs in Inter 15px, slate-700, 1.7 line height. Instrument assessment cards (see below). Dissenting view block. Prediction Logger. Framework Behind This. |
| **Instrument Assessment Card** | Name (Inter 15px bold) + sector/exchange (DM Mono 10px). Signal pill (DM Mono 10px): `opportunity signal` green / `headwind signal` red / `watch` amber. Reasoning text (Inter 13px). Entry conditions (green background #F0FDF4, green border) and exit conditions (amber background #FFF7ED, amber border) in two-column grid. Conditions are observable facts about the world, never price targets. |
| **C — Context Tab** | Numbered causal chain. Each step: navy circle number (28px), step title (14px bold), body explanation (13px), MMJ badge inline. Connector line between steps. Steps have no fixed count — as many as the event requires. |
| **E — Evidence Tab** | Full source table: Claim / Source name / Date retrieved / Freshness dot / MMJ type. Freshness dot: green = within 6 months, amber = 6–18 months, red = over 18 months. LLM never appears in this table. All entries are human-sourced data. |
| **Aside — Lifecycle Tracker** | 7-step vertical tracker. Done steps: green dot. Current step: blue pulsing dot (animation: 1.5s ease-in-out infinite, opacity 1→0.3→1). Future steps: slate-200 dot. Step labels in DM Mono 12px. |
| **Aside — Signals to Watch** | Interactive signal items. State dots: Pending = grey static, Triggered = amber pulsing, Resolved = green static. Tap on signal reveals consequence map — how that signal changes each affected instrument's assessment. |
| **Aside — Confidence Composition** | Segmented horizontal bar showing proportion of claims that are Measured / Modelled / Judged. Colour-coded (blue / green / amber). Legend below. Helps users understand how much of the card is data-driven vs opinion. |
| **Aside — Bias Flags** | Amber block for flagged biases (recency, narrative). Grey block for monitored biases. Plain English description of each. Present on every card. |
| **Current / Original Toggle** | Two-segment control in topbar. Current View = live state of analysis including all updates. Original View = immutable Day 1 record, never edited. Both always accessible. Users can compare them to see where the analysis evolved and where early predictions proved correct or wrong. |
| **Dissenting View** | Amber tinted background (#FFFBEB), 1px amber border (#FDE68A). "dissenting view" pill label in DM Mono 9px. Playfair Display 16px title. Inter 13px body. Generated by a separate LLM call — structurally required on every card. |
| **Prediction Logger** | Blue-tinted box (#F0F4FF), 1px blue border (#BFDBFE). Appears before Context tab is revealed. Question asking user to form a view before seeing the causal chain. 4 discrete prediction options. "Log my prediction →" button. Disclaimer text: "This is tracked for your learning. It does not constitute an investment decision. Reviewed in The Mirror when the card resolves." |
| **Framework Behind This** | Dark gradient background (navy #0F172A to dark blue #1E3A5F). DM Mono 9px label. Playfair Display 18px title. White body text (rgba 0.75 opacity). Bulleted framework questions with blue arrow prefix. Final paragraph explains how the framework applies to future events. |

#### Design Decisions — Final

| Decision | Rationale |
|---|---|
| **ICE architecture — three layers, user chooses depth** | Insight is always visible. Context requires one tap. Evidence requires a second tap. Most users stop at Insight. Deep users can verify every number. The design respects both use patterns without penalising either. |
| **Dissenting view is structural, not optional** | A card without a dissenting view is not published. Separate LLM call with a separate prompt explicitly instructed to argue the strongest reasonable counter-case. Visually distinct treatment prevents it being read as part of the main thesis. |
| **MMJ badges on every quantitative claim** | Every number carries a MEASURED / MODELLED / JUDGED badge. This is the integrity mechanism of the product. Removing it would undermine the entire trust proposition. Cannot be made optional. |
| **Entry and exit conditions — not price targets** | Conditions are observable facts about the world — "Crude holds above $90/barrel", "Closure confirmed beyond 2 weeks". Not "buy above ₹230". This is both SEBI-compliant and more analytically honest — prices move; conditions persist. |
| **Living Card lifecycle visible to user** | The 7-state lifecycle is shown in the aside panel at all times. Users see where the card is in its life. They know whether they are reading a fresh take or a card that has been through signal triggers. |
| **Original View always accessible** | The immutable Day 1 record is one tap away, always. This is the track record mechanism — it prevents revisionism and creates accountability. Cards cannot be quietly updated to look more prescient after the fact. |
| **Prediction before analysis** | The prediction logger appears before the Context tab is revealed. Users form a view first. This teaches the habit of reasoning before reading conclusions — the opposite of most financial media. |
| **Freshness dots on every Evidence row** | Users see data staleness at a glance without reading metadata. Green / Amber / Red is instantly readable and creates appropriate scepticism about older data points. |
| **Bias flags in aside panel, not footnotes** | Bias flags appear alongside the analysis in the always-visible aside panel. Not buried in footnotes. Not accessible only after scrolling. Confidence before conclusion. |

#### Language Rules

- No "buy", "sell", "hold" language anywhere
- Entry conditions describe world facts, never price levels or percentage moves
- Exit conditions describe world facts, never portfolio stop-loss levels
- Instrument assessments use only: `opportunity signal` / `headwind signal` / `watch — long term`
- The dissenting view title must identify a specific mechanism, not a generic disclaimer like "markets are unpredictable"

---

### Screen 4 — The Mirror — Personal Learning History & Prediction Tracking

**Phase:** Phase 2 | **Status:** ✅ Designed & Approved

> *"Not what your portfolio is worth. What your reasoning was worth."*

#### Intent

The personal accountability layer. Shows users their prediction history, reasoning accuracy at three distinct levels, identified reasoning gaps, and a streak tracker. No rupee figures. No portfolio performance. Pure learning accountability.

#### Layout

- Left sidebar
- Topbar: "The Mirror" title + subtitle + notification badge (pulsing blue dot) when resolved cards are ready to grade
- Four-stat strip immediately below topbar
- Two-column layout below: prediction history list (left, ~65%) + right panel with three stacked cards (Ready to Grade / Reasoning Gap Analysis / Streak Tracker)

#### Components

| Component | Description |
|---|---|
| **Stats Strip** | Four cells in a horizontal grid separated by 1px borders. Each cell: Playfair Display 28px number + DM Mono 10px label + Inter 11px subtext. Stats shown: Total Predictions Made / Mechanism Accuracy % / Market Reaction Match % / Reasoning Gaps Found. Accuracy numbers coloured green (strong) or amber (developing). |
| **Notification Badge** | Blue badge in topbar with pulsing dot (animation same as signal dot). "N cards resolved — ready to grade". Appears when at least one card enters Resolved lifecycle state and the user has a logged prediction for it. |
| **Prediction Card** | White card, 1px slate-200 border. Expandable on click. Header: event category tag + event name + date logged. Financial consequence headline (Playfair Display 14px). "Your call: [user's prediction text in bold]". Status badge (Resolved green / Active amber / Pending grey). Three-level accuracy meter below. Expand state reveals Gap Insight paragraph and link to relevant Map module. |
| **Three-Level Accuracy Meter** | Three horizontal mini-bars per card, one per level. Each bar fills to reflect accuracy. Correct = green fill (#0A6644) + "✓ Correct" label. Partial = amber fill + "~ Partial". Incorrect = red fill + "✗ Incorrect". Pending = grey fill + "Monitoring" italic. Labels in DM Mono 10px. This is the key learning display of the whole surface. |
| **Gap Insight (Expanded State)** | Plain English paragraph explaining the gap between what the user predicted and what happened. Always names a specific reasoning error — not a generic "markets are unpredictable". Links to a Map module that addresses the identified gap. |
| **Ready to Grade Panel** | Green-tinted items (#F0FDF4, green border #BBF7D0). Each item: green dot + event name + resolution date + arrow. Clicking navigates to that card in the history list and expands it. |
| **Reasoning Gap Analysis Panel** | Three identified gap items derived from prediction history. Each: icon in coloured box + gap name (Inter 13px bold) + plain English explanation of the pattern + "🗺 The Map: [module name] →" link. Gaps are derived from actual patterns in the user's prediction history — not manually assigned. |
| **Streak Tracker** | 14-cell grid showing last 14 predictions. Each cell colour-coded: green = correct, amber = partial, red = incorrect, grey = pending/monitoring, transparent = no prediction logged. DM Mono letters inside cells (M/P/✗/·/–). Legend row below. Summary paragraph comparing mechanism accuracy % to market reaction accuracy % with explanation of why the gap is normal and what it means. |
| **Filter Pills** | Above prediction history: All / Resolved / Active / Pending. DM Mono 10px. Active pill: navy background. One tap to filter. |

#### Design Decisions — Final

| Decision | Rationale |
|---|---|
| **No rupee figures anywhere on this screen** | The Mirror shows zero portfolio performance data. No gains, no losses, no returns. FinnWise is not a portfolio tracker. Mixing learning accountability with financial performance would corrupt both measurements and the educational intent of the surface. |
| **Three-level accuracy, not one score** | Mechanism / Business Impact / Market Reaction are tracked and displayed separately. Being right at mechanism level and wrong at market reaction is the most important lesson in financial reasoning. A single accuracy score would hide this distinction entirely. |
| **Reasoning gaps link to Map modules** | When a gap is identified, The Mirror links directly to the relevant sector or framework module in The Map. The Mirror and The Map are designed to reinforce each other — the accountability surface feeds back into the learning surface. |
| **Resolved card notification in topbar** | The pulsing badge creates a specific reason to return to the app. When a card resolves, users who logged predictions are brought back to see the outcome. This closes the feedback loop that most financial tools leave permanently open. |
| **Streak tracker teaches pattern awareness** | The 14-cell grid makes patterns visible at a glance — consistent mechanism accuracy with inconsistent market reaction accuracy is the most common pattern for early investors. The summary paragraph explains the pattern explicitly rather than leaving the user to infer it. |
| **Prediction cards expandable, not navigating away** | Expanding a card inline preserves context. Users can see the gap insight alongside their other predictions without losing their place in the history list. The learning is comparative — seeing multiple gaps together is more valuable than seeing one in isolation. |

---

### Screen 5 — The Lens — On-Demand Event Intelligence Card Generator

**Phase:** Phase 2 | **Status:** ✅ Designed & Approved

> *"Ask about any event. Get the full causal chain in 30–90 seconds."*

#### Intent

The deliberate research mode for slow, deep users who want to investigate events or hypotheticals that The Pulse has not yet covered. Runs the same three-call LLM pipeline as event-triggered cards. Returns a full ICE card in the same structure as The Thread. Explicitly labelled as non-editorially-reviewed.

#### Layout — Three UI States

The Lens has three distinct states managed with show/hide (no page navigation):

1. **Query Input State** — centred layout, max 680px width, text area + selectors + example grid + history
2. **Loading State** — centred loading card showing animated six-step pipeline progress
3. **Result State** — full two-column layout: ICE card (left) + aside panel (right, 280px)

#### Components

| Component | Description |
|---|---|
| **Query Text Area** | Large free-text input, min 80px height. Placeholder: "Describe an event or ask a question — e.g. 'What would a US recession mean for Indian IT exporters?'". Font Inter 15px. Focused state: blue border (#1A4FCC), 3px shadow. Sector (optional) and Horizon (optional) dropdown selectors inline below in query box footer. "Generate card →" button: disabled until input exceeds 10 characters. |
| **Time Estimate Note** | DM Mono 10px, slate-400. "Cards take 30–90 seconds to generate." Shown below the query box. Sets expectation before the user clicks Generate. Users who need a fast answer know to check The Pulse instead. |
| **Example Query Grid** | 2×3 grid of example cards. Each: category tag + plain-English question. Clicking fills the text area. Six examples covering: Macro / RBI Policy / Regulatory / India-Specific / Geopolitical / Budget. Teaches users what The Lens is capable of. |
| **Recent Query History** | List below examples. Each item: document icon + query text + relative date + arrow. Clicking a history item navigates directly to the result state for that query. |
| **Loading Card** | Centred, max 560px. Query text displayed in Playfair Display italic with blue left border (the user's own question). Progress bar (0→100% animated over generation duration). Six pipeline step rows with live status animation. Steps: Factor DB queried / Macro signals retrieved / Synthesising ICE layers / Generating dissenting view / Articulating framework / Validating numbers against Evidence. Steps animate: pending (grey number) → active (blue, pulsing) → done (green ✓). Disclaimer at bottom: "Every number is validated against the Evidence layer before display." |
| **Result Topbar** | "← New query" button (returns to query state, preserves input). "The Lens — Generated card" label in DM Mono. Action buttons: "Save to Thread" + "Read full ICE card →" (primary, navy). |
| **Result Meta Row** | Event type tag (category) + horizon tag + "Generated in Xs · Date". Generation time shown for transparency. |
| **Result ICE Card** | Full ICE card identical in structure to The Thread. Playfair Display 24px title. Inter 15px light deck. ICE tabs (I / C / E). Instrument assessment cards with entry/exit conditions. Dissenting view block. Framework Behind This. Same component specs as Screen 3. |
| **Result Aside — Confidence Composition** | MMJ distribution bar + legend + explanatory note specific to Lens cards: "Higher Judged proportion than editorial cards. Hypothetical scenarios depend more on historical analogues than current measured data." |
| **Result Aside — Bias Flags** | Any applicable bias flags (recency, survivorship, narrative) with plain English descriptions specific to this query. |
| **Result Aside — Lens Limitations** | Surface background (#F8FAFC), 1px slate-200 border. Title: "This is a Lens-generated card, not an editorial card". Body: "This card has not gone through editorial review. Numbers are validated against the Evidence layer but the analytical framing has not been reviewed by a human editor. Treat with appropriate caution relative to The Thread cards which are editorially reviewed before publication." This block is mandatory on every Lens result. |
| **Phase 2 Badge** | Purple badge (#F3E8FF background, #6B21A8 text) in topbar. Prominent but not blocking. |

#### Design Decisions — Final

| Decision | Rationale |
|---|---|
| **Three UI states, not three pages** | Query → Loading → Result are three states of the same page managed with show/hide. No navigation. The back button in Result state returns to Query with the same text preserved. No page reload, no loss of context, no disrupted flow. |
| **Visible pipeline progress during loading** | Six named steps animate in sequence during the 30–90 second wait. Users see exactly what the system is doing — not a spinner. This reinforces the product's transparency promise during the highest-anxiety moment (waiting for a result). It also teaches users that the pipeline has multiple stages of rigour. |
| **Lens cards explicitly labelled non-editorial** | The aside limitations card clearly states this card has not been editorially reviewed. This is a trust mechanism. Users should weight Lens cards differently from Thread cards. The distinction is structural and visible — not buried in small print. |
| **Time estimate shown upfront** | The 30–90 second estimate is shown below the input box before the user clicks Generate. No surprise waits. Users who need a fast answer know to check The Pulse instead. Expectation management is part of the UX. |
| **Example queries teach capability, not just UI** | Six examples across all major event categories each have a coloured category tag. The grid teaches users what kinds of questions The Lens handles well — and implicitly, what kinds it does not (opinion pieces, market timing, price predictions). |
| **"Save to Thread" on result** | Users can save a Lens card to their personal Thread collection. This bridges the on-demand and editorial experiences. A Lens card that proves analytically useful becomes a persistent living card. The best user-generated analysis earns permanence. |
| **Phase 2 badge in topbar** | The purple badge is prominent. Users who discover The Lens early are correctly calibrated that it is a Phase 2 feature. The badge is informational and does not restrict access — it sets expectation. |

#### Language Rules

- Lens-generated cards carry identical language rules to Thread cards — no buy/sell/hold
- Entry and exit conditions are analytical observations, never investment instructions
- The Lens limitations card is mandatory on every generated result — cannot be removed
- SEBI disclaimer bar on Lens result explicitly notes the card is AI-generated without editorial review

---

## 6. Intelligence Architecture

### 6.1 ICE Card Generation Pipeline

| Step | Stage | Description | Phase |
|---|---|---|---|
| 1 | **Event Detection** | Automated monitor watches NewsAPI (4-hourly), RBI RSS (event-driven), NSE/BSE announcements (daily post-market), and manually maintained slow-burn watchlist (weekly). Events enter a queue with an AI-generated confidence score. | Phase 1 |
| 2 | **Draft Generation** | Structured LLM prompt takes the event, queries the Factor Exposure Database, pulls active macro signals, and generates a full draft ICE card: causal chain, instrument assessments, dissenting view, and Framework Behind This. Three separate LLM calls. | Phase 1 |
| 3 | **Editorial Review** | Product Owner reviews draft against a non-expert checklist — all numbers source-tagged, dissenting view present, confidence level consistent with data freshness, language accessible to a non-expert. Target: 30–45 minutes per card. | Phase 1 |
| 4 | **Publication** | Approved card published. Track record timestamp logged in append-only database. Signal monitoring begins. Users with relevant profile receive in-app notification on next login. | Phase 1 |

### 6.2 Quantification Standard — Measured, Modelled, Judged

Every quantitative claim in every Event Intelligence Card carries one of three tags. This is the integrity feature of the product. It cannot be removed or made optional.

| Tag | Definition | Display |
|---|---|---|
| `MEASURED` | Derived from historical data with a defined, documented methodology. Minimum 8 quarters of data required. | Blue badge. Highest user confidence. |
| `MODELLED` | Derived from a calibrated model with explicit, stated assumptions. Model methodology documented in Evidence layer. | Green badge. Medium user confidence. |
| `JUDGED` | A structured expert opinion with stated reasoning but no statistical foundation. Honest label for informed estimates. | Amber badge. User informed this is an opinion, not a measurement. |

### 6.3 LLM Architecture — Three Defined Roles

The LLM has three strictly defined roles. It does not operate outside them. The LLM **never touches the Evidence layer**. It **never generates numbers**. Any number in Insight or Context must be traceable to a specific Evidence layer data point.

| Role | Function | Key Constraint |
|---|---|---|
| **Role 1 — Card Synthesis** | Generates Insight and Context layers. Explains and connects structured inputs from the Factor DB and macro signals. | All numbers must reference Evidence layer data points. Output validated post-generation. |
| **Role 2 — Dissent Generation** | Generates the dissenting view via a separate LLM call with a separate prompt explicitly instructed to argue the strongest reasonable counter-case. | Separate call prevents anchoring. Dissent must identify a specific mechanism — not a generic disclaimer. |
| **Role 3 — Framework Articulation** | Generates the "Framework Behind This" section. Extracts and names the transferable reasoning pattern used in the card. | Must describe how the framework applies beyond this specific event. Must be actionable for a non-expert reader. |

**LLM Model:** Anthropic Claude API — Sonnet model. All three prompt templates are version-controlled in Git. Every prompt change is logged with date and reason. Cards are tagged with the prompt version that generated them.

### 6.4 Confidence-Gated Signal Detection

| Confidence Level | Trigger Criteria | System Action | Editorial Action |
|---|---|---|---|
| **High** | Signal confirmed by 3+ independent sources within 4 hours, directly matches signal definition | Auto-update card, notify Product Owner simultaneously | Override window: 2 hours. If no override, update stands. |
| **Medium** | Confirmed by 1–2 sources, partially matches signal definition, or context is ambiguous | Generate draft update, hold for review | Product Owner reviews AI draft, approves or rejects. Target: under 10 minutes. |
| **Low** | Possible signal match, single source, or source quality uncertain | Log internally, surface in daily editorial digest | No card update. Product Owner reviews digest and decides whether to escalate. |

### 6.5 Bias Audit Log

The bias audit log tracks six bias types across all active cards:

- **Recency bias** — flagged when more than 60% of Evidence sources are from the last 30 days
- **Sector concentration bias** — flagged when 3 consecutive cards cover the same sector
- **Narrative bias** — flagged when a card's direction confidence is high but Evidence layer has fewer than 3 sources
- **Editorial coverage bias** — logged weekly: which event categories were covered and which were not
- **Survivorship bias** — flagged on any historical analysis using only companies that currently exist
- **Anchoring bias** — monitored across the three LLM calls, mitigated by separate prompts for dissent generation

---

## 7. Data Architecture

### 7.1 Tier 1 — Factor Exposure Database

The analytical backbone of every Event Intelligence Card. A structured database of the top 150 NSE-listed stocks, each tagged with their sensitivity to 8 macro factors. Built as a parallel workstream to the application build.

**Phase 1 starting sector: Banking & Financial Services** — most event-sensitive sector, cleanest publicly available data. The first real application test happens when Banking sector data is complete, not when all 150 stocks are done.

| Factor | What It Captures | India-Specific Note |
|---|---|---|
| **Crude oil price** | Input cost sensitivity for downstream users. Realisation uplift for upstream producers. | India imports 80% of crude. Transmission to company P&Ls is fast and direct. |
| **Dollar-Rupee rate** | Revenue uplift for exporters. Input cost pressure for importers. | IT sector earns in USD. Importers of commodities and electronics are directly exposed. |
| **Domestic interest rates** | Cost of capital, NIM for banks, consumer demand sensitivity. | RBI repo rate is the primary driver. NIM transmission to stock price takes 1–2 quarters. |
| **Global risk sentiment** | FII flow direction, broader market beta. | FII activity reported daily on NSE. Used as confidence modifier only — not a primary signal. |
| **Monsoon index** | Agricultural output, rural consumption, food inflation. | India-specific. Critical for FMCG, fertilisers, consumer discretionary demand. |
| **Government capex** | Infrastructure demand, order books for capital goods companies. | Union Budget and quarterly capex data are primary sources. Budget cycle is February. |
| **GST collections trend** | Proxy for domestic consumption health. | Monthly data published by Ministry of Finance. High-frequency, reliable, public. |
| **Sector regulatory environment** | Pending policy changes, SEBI actions, sector-specific regulations. | Requires manual monitoring. Flags companies with active regulatory risk. |

### 7.2 Tier 2 — Event & Signal Database

PostgreSQL schema via Supabase. Core tables:

- **events** — event records with category, confidence score, lifecycle state, prompt version used
- **signals** — one row per signal per card, with state (pending/triggered/resolved) and trigger timestamp
- **instrument_assessments** — one row per instrument per card per version, with entry/exit conditions
- **track_record** — append-only table. No deletes. No updates. One row per card per prediction (system and user). Reviewable when cards resolve.
- **user_predictions** — one row per user per card, with prediction text, timestamp, and accuracy assessment at three levels when resolved

### 7.3 Tier 3 — Data Sources (Free Tier, Research Use)

| Data Type | Source | Refresh Cadence | Legal Status |
|---|---|---|---|
| Stock EOD prices | yfinance (Yahoo Finance) | Daily, post 6PM IST | Free, research use — unofficial, build source abstraction and fallback |
| Mutual Fund NAV | mfapi.in | Daily | Fully free, AMFI public data |
| FII/DII activity | NSE website public CSV | Daily post-market | Public data, research use |
| RBI policy data | RBI website RSS feed | Event-driven, checked 4-hourly | Public domain |
| INR/USD, Crude Oil | yfinance / investing.com | Daily | Free for research use |
| Market news | NewsAPI free tier (100 calls/day) | 4-hourly on market days | Free tier, research use |
| Fundamental data | Screener.in / Tickertape free tier | Weekly manual review | Grey area — research only, no redistribution |

> **⚠ DATA RISK:** yfinance is unofficial and can break without notice. NSE periodically blocks scrapers. Build the data layer with source abstraction and fallback sources from Day 1. Every data point carries a timestamp and source tag. Never assume data freshness. Freshness dots surface stale data to users immediately.

---

## 8. UI Design System — Final

### 8.1 Design Philosophy — Three Overriding Rules

FinnWise is designed to feel like **The Economist**, not like a fintech app. Calm authority. Generous whitespace. Typography that signals reading, not scanning.

1. **Meaning before metric** — every financial number is accompanied by its plain-English translation and context in the same display. The number is secondary to the meaning.
2. **Context before concept** — financial concepts are taught through current, real events the user already cares about, never in the abstract.
3. **Confidence before conclusion** — uncertainty is displayed before analysis, not buried in footnotes after recommendations.

### 8.2 Typography System

| Font | Use in FinnWise | Rationale |
|---|---|---|
| **Playfair Display** | Article titles (Thread, Lens results), Framework Behind This title, section headers where editorial weight is needed, brand wordmark | Signals reading and depth. Editorial authority. Used by serious financial publications. Italic variant used for manifesto quote and Lens query display. |
| **Inter** | All body text, UI elements, navigation labels, buttons, form inputs, insight summaries, instrument reasoning | Clean, highly legible at small sizes. Professional at the information density this app requires. |
| **DM Mono** | Data labels, MMJ badges, provenance tags, navigation group labels, card lifecycle status, confidence dots, timestamps, filter pills, phase badges | Mono treatment on data elements signals precision and verifiability. Creates clear visual separation between narrative content and analytical metadata. |

### 8.3 Colour System

| Name | Hex | Use |
|---|---|---|
| **Blue** | `#1A4FCC` | Primary trust colour. Nav active state, links, high-confidence dots, MEASURED badge background reference, primary CTAs, active ICE tab underline, prediction logger border |
| **Green** | `#0A6644` | Opportunity signals, positive instrument assessments, entry condition blocks, resolved signal dot, MODELLED badge reference, streak correct cells |
| **Amber** | `#8A5009` | Watch signals, moderate confidence dots, triggered signal dot (pulsing), JUDGED badge reference, Fog of War banner, dissenting view border |
| **Red** | `#9B2416` | Headwind signals, negative instrument assessments, exit condition blocks, SEBI disclaimer bar, streak incorrect cells |
| **Slate-900** | `#0F172A` | Primary ink. Article titles, nav items (active text), instrument names, primary button backgrounds |
| **Slate-700** | `#334155` | Body text, instrument reasoning, most readable prose |
| **Slate-500** | `#64748B` | Secondary text, event context paragraphs, subtext |
| **Slate-400** | `#94A3B8` | Labels, timestamps, nav group headings, caption text |
| **Slate-200** | `#E2E8F0` | Borders, separators, grid lines |
| **Slate-100** | `#F1F5F9` | Table row alternates, header backgrounds, pending state backgrounds |
| **Surface** | `#F8FAFC` | Page background. Warm white, not cold grey. |
| **White** | `#FFFFFF` | Card backgrounds, sidebar, topbar |

#### Background references for badge/block colours

| Badge/Block | Background Hex | Border/Text |
|---|---|---|
| MEASURED badge | `#DBEAFE` | Blue text (#1A4FCC) |
| MODELLED badge | `#D1FAE5` | Green text (#0A6644) |
| JUDGED badge | `#FEF3C7` | Amber text (#8A5009) |
| Opportunity chip | `#D1FAE5` | Green text |
| Headwind chip | `#FEE2E2` | Red text |
| Watch chip | `#FEF3C7` | Amber text |
| Entry conditions | `#F0FDF4` | `#BBF7D0` border |
| Exit conditions | `#FFF7ED` | `#FED7AA` border |
| Dissenting view | `#FFFBEB` | `#FDE68A` border |
| Prediction logger | `#F0F4FF` | `#BFDBFE` border |
| Nav active state | `#EEF3FF` | Blue text |
| SEBI bar | `#FEF2F2` | `#FECACA` top border |

### 8.4 Sidebar Navigation — Final Spec

| Element | Spec |
|---|---|
| Width | 220px, fixed, persistent on desktop |
| Background | White (#FFFFFF) |
| Right border | 1px solid slate-200 (#E2E8F0) |
| Logo area | 24px padding all sides. Playfair Display 18px bold wordmark. DM Mono 10px tagline below in slate-400. Border-bottom 1px. |
| Nav group label | DM Mono 9px, uppercase, letter-spacing 1px, slate-400, 8px horizontal padding |
| Nav item | 8px vertical, 10px horizontal padding, 6px border-radius. Inter 13px. Icon 16px, 10px gap to label. |
| Nav item — default | slate-500 text |
| Nav item — hover | slate-100 background, slate-900 text |
| Nav item — active | `#EEF3FF` background, `#1A4FCC` text, medium font weight |
| Phase 2 badge | DM Mono 9px, `#F3E8FF` background, `#6B21A8` text, pushed right with margin-left: auto |
| User chip | Bottom of sidebar, border-top 1px. 28px avatar circle (blue background, white initials, 11px bold). Name 13px medium. Sub-label DM Mono 10px slate-400. |

### 8.5 Responsive Behaviour

- **Desktop (>860px):** Left sidebar, two-column layouts, aside panels, full topbar
- **Tablet (600–860px):** Sidebar collapses to top navigation bar. Core surfaces accessible.
- **Mobile (<600px):** Top bar with wordmark. Aside panels hidden or stacked below content. Single-column articles. Full functionality preserved, aside panels traded for screen space.

### 8.6 Component Decisions — Final

| Component | Final Decision |
|---|---|
| **SEBI Disclaimer Bar** | Red background (#FEF2F2), red top border 1px (#FECACA). DM Mono 10px red text. Persistent footer on every screen showing instrument-specific analysis. Never a popup or modal. Never dismissable. Present on: Onboarding (all steps), Pulse, Thread, Mirror, Lens result. Standard text: "FinnWise generates AI-powered analysis for educational and research purposes only. It does not constitute registered investment advice under SEBI (Investment Advisers) Regulations 2013." |
| **Confidence Dots** | 8px filled circles. Blue = high, Amber = moderate, Grey = uncertain. Direction and magnitude always two separate dots with separate labels. Never combined into a single rating, percentage, or star count. |
| **Freshness Dots** | 8px circles. Green = within 6 months, Amber = 6–18 months, Red = over 18 months or unverifiable. Shown inline before source name in Evidence table. |
| **MMJ Badges** | DM Mono 9px pill. MEASURED blue, MODELLED green, JUDGED amber. Inline at end of every quantitative claim in Context and Evidence tabs. Never omitted. Applied uniformly, no exceptions for "obvious" numbers. |
| **Signal Dot Animation** | CSS keyframe: `0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; }` — 1.5s ease-in-out infinite loop. Applied only to Triggered signal dots and Active lifecycle dot. |
| **Hover/Transition States** | All interactive cards and buttons: `transition: all 0.15s ease`. No transitions over 0.3s on primary interactions. Card expand animation: `slideDown 0.3s ease` (`opacity: 0, translateY(-8px)` → `opacity: 1, translateY(0)`). |
| **Table Alternating Rows** | White (#FFFFFF) and Surface (#F8FAFC) alternating. Never zebra striping with strong colour. |
| **Border Radius** | Cards: 8px. Buttons: 6px. Badges/pills: 20px (rounded) or 4px (squared). Dots: 50%. Consistent — no mixing of sharp and rounded within the same component. |

---

## 9. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | React + Next.js + Tailwind CSS | Five-surface web app requiring SSR for fast initial load. Tailwind for consistent styling without a custom design system overhead. |
| **Backend** | Python + FastAPI | Analytical stack is Python-native. FastAPI for async LLM calls with 15–45 second response times. Automatic API documentation. |
| **LLM** | Anthropic Claude API — Sonnet | Best instruction-following for structured financial prompts. Cost-effective at moderate usage volumes. Confirmed provider. |
| **Database** | PostgreSQL via Supabase | Relational with free tier for V1. Append-only track record log enforced at database level via row-level security — cannot be edited or deleted. |
| **Auth** | Supabase Auth — magic link email | No password management. Product Owner invites testers by email. One-click access. |
| **Frontend Hosting** | Vercel | Native Next.js deployment. Free tier. One-click GitHub integration. Automatic preview deployments on every PR. |
| **Backend Hosting** | Railway | Free tier handles Python backend and scheduled jobs. Event detection monitor runs as a scheduled Python job every 4 hours. |
| **Event Detection** | Python scheduled job — 4-hour cadence | Watches NewsAPI, RBI RSS, NSE announcements. Generates confidence score. Routes to auto-update or editorial queue per confidence gate. |
| **Prompt Templates** | Version-controlled in Git | All three prompt templates (synthesis / dissent / framework) are version-controlled. Cards tagged with prompt version at generation. Track record interpretable when prompts change. |
| **Dev Tooling** | Cursor, Claude Code, GitHub Copilot, v0 | AI agents for all code generation. Product Owner role: factor database review, editorial card review, product decisions — not code. |

### 9.1 Budget Allocation

| Item | Estimated Cost/yr | Notes |
|---|---|---|
| Claude API — LLM reasoning and card generation | ₹8,000–10,000 | ~500–800 card generations and signal checks per month |
| Vercel — frontend hosting | ₹0 | Free tier sufficient for V1 with 10–15 testers |
| Railway — backend and scheduled jobs | ₹0–1,500 | Free tier or minimal paid tier |
| Supabase — database and auth | ₹0 | Free tier sufficient for V1 |
| NewsAPI — event detection | ₹0 | 100 requests/day free tier, sufficient for 4-hourly cadence |
| Domain name (optional) | ₹800–1,200 | Optional for research phase |
| Buffer and contingency | ₹2,000–4,000 | API overages, additional tools |
| **TOTAL** | **₹11,000–17,000/yr** | **Within ₹20,000 annual research budget** |

---

## 10. Phased Roadmap

### Phase 1 — Foundation (Months 1–3)

One sector of the factor database complete. Two or three sector knowledge modules built. The Pulse and The Thread surfaces live. Event detection and card generation pipeline operational. 10–15 invited testers. Track record logging from Day 1.

| Week | Milestone | Deliverable |
|---|---|---|
| 1–2 | Database schema | PostgreSQL schema live on Supabase. Factor, card, signal, track record, and user prediction tables with correct constraints and row-level security on track record. |
| 3–4 | LLM pipeline | Three prompt templates version-controlled. ICE card synthesis, dissent generation, framework articulation. Test runs producing structurally correct cards. |
| 5–6 | Event detection | Scheduled job running on Railway. NewsAPI and RBI RSS monitored. Events entering queue with confidence scores. Editorial review interface operational. |
| 7–8 | The Thread | Full Thread surface live. ICE tabs, Living Card status panel, signal consequence map, prediction logger, provenance dots, SEBI disclaimer, two-view toggle. |
| 9–10 | The Pulse + Onboarding | Full Pulse surface live. Two-column layout, card feed, insight panel, Fog of War mode, onboarding flow, tester access via magic link. |
| 11–12 | Tester launch | 5–10 testers invited. First real event card published. Track record timestamp logged. Feedback collection begins. |

### Phase 2 — Engagement Layer (Months 4–9)

- The Lens — on-demand Event Intelligence Card generation
- The Mirror — prediction history, reasoning gap analysis, resolved card notifications
- Portfolio Protector personalisation — Pulse and Thread personalised to existing holdings
- Email notifications when signals fire — triggered by confidence-gated detection
- Factor database expansion — all 8 sectors complete
- UI polish — Thread and Pulse refinement based on Phase 1 tester feedback

### Phase 3 — Intelligence Deepening (Months 10–18)

- Full NLP pipeline for factor database — automated extraction from quarterly filings replaces manual weekly review
- Compound event Fog of War automation — model detects interaction effects between simultaneous events and adjusts confidence automatically
- SEBI compliance audit — formal legal review before any public launch beyond tester group
- Productisation assessment — RA registration research, scalability review, pricing model if registration obtained

---

## 11. Compliance & Legal Requirements

### 11.1 SEBI Safe Harbour Framing — Non-Negotiable Constraints

These constraints apply to all phases and cannot be overridden by product decisions:

- No buy, sell, or hold language anywhere in the application — language is: `opportunity signal`, `headwind signal`, `watch`
- No instrument shall have a target price or return expectation stated or implied anywhere in the UI
- No personalised investment advice as defined under SEBI (Investment Advisers) Regulations 2013
- SEBI disclaimer hardcoded on every screen that shows instrument-specific analysis — not a popup, a persistent element
- Entry and exit conditions are analytical conditions framed as observations about the world — not investment instructions
- No fee charged for any recommendation output in V1
- No user financial data stored beyond the current session — investment amount, period, risk preference are session-only

> **⚠ LEGAL REVIEW:** Before any public launch beyond the invited tester group, all UI copy must be reviewed by a SEBI-specialised lawyer. The safe harbour framing in this PRD is based on best current understanding of SEBI (Investment Advisers) Regulations 2013 and SEBI (Research Analysts) Regulations 2014 but does not constitute legal advice.

### 11.2 Relevant Regulations

- **SEBI (Investment Advisers) Regulations 2013** — defines personalised investment advice requiring IA registration
- **SEBI (Research Analysts) Regulations 2014** — defines securities research reports requiring RA registration
- **SEBI Circular on Digital Platforms 2021** — guidelines for fintechs providing investment-related content
- **NSE/BSE Data Vendor Policy** — governs use of exchange data in commercial applications

---

## 12. Risks & Mitigations

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | LLM generates qualitatively wrong analysis that sounds authoritative — not numeric hallucination but contextually wrong sector reasoning | Critical | Mandatory uncertainty statement on every card. Evidence layer is LLM-free. All LLM outputs logged with exact prompt. Prompt templates version-controlled. Editorial review before publication. |
| 2 | Factor database sensitivity estimates are unvalidated — instrument assessments directionally wrong | Critical | All estimates carry MMJ labels. Cards labelled as educational analysis, not validated signals. Backtest methodology documented before tester launch. |
| 3 | SEBI compliance — app crosses into regulated advice territory | High | Legal review of all UI copy before tester launch. Mandatory signed disclaimer for testers. No rupee targets, no buy/sell language, no fees. |
| 4 | yfinance breaks or NSE blocks — data pipeline fails silently | High | Secondary data sources identified. Source abstraction layer in pipeline. Freshness dots surface stale data to users immediately. Fallback to last known good value with staleness declaration. |
| 5 | Testers interpret analysis as financial advice and make real investment decisions based on it | High | Mandatory tester briefing document signed before access. SEBI disclaimer on every screen. Onboarding explicitly states educational analysis only. |
| 6 | Factor database build falls behind — application cannot be tested meaningfully | Medium | Milestone design forces parallel progress. Banking sector data gates Week 10 application test. Solo builder time commitment: 1 hour per day for 3 months. |
| 7 | API cost overruns during testing | Low | Hard daily limit on LLM API calls — maximum 50 card generations per day in V1. Usage monitored weekly against budget. |

---

## 13. Success Metrics for V1

V1 is a research project. Success is measured on quality of intelligence output and user learning — not revenue, DAU, or engagement metrics.

### Quantitative Targets

| Metric | V1 Target | Measurement Method |
|---|---|---|
| Card accuracy — numbers match source data | 100% | Manual spot-check of all published V1 cards |
| Bias flag trigger rate | >60% of sessions | Bias audit log analysis |
| Tester comprehension — can explain why an instrument was flagged | >70% of testers | Short survey after first session |
| Data pipeline reliability | >95% | Pipeline run log — weekday EOD refreshes |
| Editorial review time per card | <45 minutes | Time log maintained by Product Owner |
| Signal detection false positive rate | <10% | Override log — high confidence auto-updates that were overridden |
| Tester sessions | 5–10 testers, 3+ sessions each | Session log in Month 3 |
| Direction prediction accuracy | >60% of resolved cards | Track record log |

### Qualitative Success Criteria

- Testers report understanding more about why an instrument is or is not an opportunity compared to other tools they have used
- The dissenting view generates at least one "I had not considered that" moment per tester
- No tester reports feeling misled or that the app made a definitive investment recommendation
- The Framework Behind This section is recalled and referenced by at least one tester when discussing a subsequent event the app did not cover
- The track record log shows direction predictions correct in over 60% of resolved cards in the first 3 months

---

## 14. Permanently Out of Scope

The following items are out of scope for **all phases** unless SEBI registration is obtained, significant budget is secured, or the project formally transitions from research to a regulated commercial product:

- Broker API integration — Zerodha Kite, Groww, Upstox — executing real trades
- Real-time or intraday tick data without a licensed data vendor agreement
- Personalised investment advice as defined under SEBI (Investment Advisers) Regulations 2013
- Portfolio management or discretionary fund management
- Derivatives, F&O, commodities, or cryptocurrency instruments
- Paid subscription model without SEBI Research Analyst registration
- User financial data storage — bank accounts, demat account numbers, PAN
- Social or community features — public portfolios, copy trading, leaderboards
- Price targets, return expectations, or holding period recommendations stated as advice

---

## Appendix A — Glossary

| Term | Definition |
|---|---|
| **ICE Stack** | Insight, Context, Evidence — the three-layer architecture of every Event Intelligence Card |
| **MMJ Tags** | Measured, Modelled, Judged — the three-level quantification standard applied to every quantitative claim in every card |
| **Living Card** | An Event Intelligence Card that evolves through a defined lifecycle as the event develops, as opposed to a static published article |
| **Signal Consequence Map** | The interactive display showing how each Signal to Watch changes the assessment of each affected instrument if it fires |
| **Entry Conditions** | The specific observable conditions that, when simultaneously true, confirm an opportunity thesis — not a price target |
| **Exit Conditions** | The specific observable conditions that, when true, indicate the opportunity thesis has weakened or been invalidated |
| **Framework Behind This** | The plain-English description of the reasoning pattern used in a card, designed for transfer to future events the app has not covered |
| **Fog of War Mode** | The UI state triggered when multiple major events are active simultaneously and their interaction effects exceed the model's reliable range |
| **Track Record Log** | An append-only database table logging every prediction made by the app and by users, reviewed against outcomes when events resolve. Cannot be edited or deleted. |
| **Factor Exposure DB** | The structured database of 150 NSE stocks tagged with their sensitivity to 8 macro factors, built as a parallel workstream |
| **Confidence-Gated Detection** | The signal trigger system routing auto-updates (high confidence), editorial review (medium), or logging only (low) based on source quality and corroboration count |
| **Portfolio Builder** | User mode for investors with no existing portfolio. Routed to The Map first. |
| **Portfolio Protector** | User mode for investors with existing holdings. Routed to The Pulse first. |
| **EOD** | End of Day — closing price and data snapshot after market close at 3:30 PM IST |
| **FII / DII** | Foreign / Domestic Institutional Investors — foreign and Indian institutional entities investing in Indian markets |
| **NIM** | Net Interest Margin — the difference between interest income and interest expense for banks |
| **ATF** | Aviation Turbine Fuel — jet fuel, typically 35–40% of operating cost for Indian airlines |
| **APM** | Administered Price Mechanism — government pricing control on domestic crude oil realisation for PSU producers |
| **NSE / BSE** | National Stock Exchange / Bombay Stock Exchange — India's two primary stock exchanges |
| **SEBI** | Securities and Exchange Board of India — the market regulator governing all securities activity in India |
| **LLM** | Large Language Model — the AI model (Anthropic Claude Sonnet) used for card synthesis, dissent generation, and framework articulation |
| **TCV** | Total Contract Value — the full value of an IT services contract including all years, used as a leading indicator for IT sector revenue |
| **GNPA** | Gross Non-Performing Assets — the total value of bad loans on a bank's books, a primary indicator of banking sector health |
| **PLI** | Production Linked Incentive — government scheme incentivising domestic manufacturing in targeted sectors |

---

*FinnWise PRD v3.0 — Final — Research Project — Indian Stock Market Focus*

*Five screens designed and approved. All design decisions recorded in Section 5 and Section 8. Not for distribution. SEBI Disclaimer applies to all content in this document.*
