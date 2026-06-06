# FinnWise — End User Guide (Portfolio Builder + Portfolio Tracker)

**Version:** v1.0  
**Audience:** End users (non-admin)  
**Scope:** Onboarding, The Pulse, The Thread, The Map, The Mirror, The Lens, Account/Settings  

---

## How to use this guide

This guide is written as two things at once:

- **A “happy path” walkthrough**: what to do first, second, third.
- **A “where to look” map**: what parts of each screen carry the critical information.

If you are short on time, start at **§2 Happy paths** and then use the page sections as reference.

---

## 1) Key definitions (avoid overload)

### 1.1 Your “mode” (what FinnWise is optimizing for)

FinnWise routes you into one of two practical experiences:

- **Portfolio Builder**: you’re starting fresh (or don’t yet have a portfolio). FinnWise starts you in **The Map** first so you learn *how sectors work* before you read event cards.
- **Portfolio Tracker**: you already have investments and want to track what events could affect what you own. In the app and codebase, this is called **Portfolio Protector**. FinnWise starts you in **The Pulse** first so you see *implications now*.

> Important: Mode is not a “lock”. You can still use every surface; mode just picks your default starting surface.

### 1.2 The five “surfaces” (the only navigation you need to remember)

- **The Pulse** (`/pulse`): personalised event feed. “Implications first.”
- **The Thread** (`/thread/[cardId]`): deep-dive Event Intelligence Card (Insight/Context/Evidence + confidence and lifecycle).
- **The Map** (`/map`): sector learning layer. How the economy fits together.
- **The Mirror** (`/mirror`): your learning history and accuracy over time.
- **The Lens** (`/lens`): generate a fresh Event Intelligence Card on demand.

### 1.3 What an “Event Intelligence Card” is

A card is not a recommendation. It’s a structured explanation of how a real-world event could affect sectors/instruments, with:

- **Insight** (the implication)
- **Context** (why it’s happening)
- **Evidence** (what supports it)
- **Dissent / framework** (why it might be wrong, and how the reasoning was done)

### 1.4 Confidence (two different ideas)

You will see confidence information in two places:

- **ICE composition**: Measured / Modelled / Judged (how much of the reasoning is grounded vs inferred).
- **Confidence tier** (HIGH / MEDIUM / LOW): an event routing label based on the system’s effective confidence.

Do not confuse “Measured % is high” with “Tier is HIGH”. They are related but not the same.

---

## 2) Happy paths (what to do first)

### 2.1 Happy path — Portfolio Builder (start from zero)

1. Complete **Onboarding** (`/onboarding`) → you’ll land on **The Map**.
2. On **The Map**, open a sector and read 1–2 modules to build the mental model.
3. Move to **The Pulse** to browse current events.
4. When something looks important, open it in **The Thread** to read the full card.
5. Use **The Mirror** weekly to review what you’ve read and track prediction accuracy.

### 2.2 Happy path — Portfolio Tracker (Portfolio Protector)

1. Complete **Onboarding** (`/onboarding`) → you’ll land on **The Pulse**.
2. Add your **Session holdings** (optional but powerful) so the feed prioritises what touches your holdings.
3. On **The Pulse**, scan implications, then open important cards in **The Thread**.
4. Use **The Mirror** to track how your predictions and learning evolve.
5. Use **The Lens** when you want a deliberate deep dive on a specific question/event.

---

## 3) Onboarding (`/onboarding`)

### What this page is for

Onboarding asks three plain-English questions to determine:

- your mode (Builder vs Tracker/Protector)
- your starting surface (Map vs Pulse)

### What to do (happy path)

1. Pick your **investment status**.
2. Enter an **amount** and cadence (monthly / one-time).  
   - The amount is **session-only UI echo**; it is **not persisted server-side**.
3. Choose your **time horizon**.
4. Read the **Mode Result** and click **Go to The Map** or **Go to The Pulse**.

### Where to look for critical information

- **Mode headline**: “You’re Portfolio Builder / Portfolio Protector”.
- **Starting surface**: “Starts here” badge on the Map or Pulse tile.
- **Rationale sentence**: one line explaining why FinnWise picked that mode.

---

## 4) The Pulse — personalised event feed (`/pulse`)

### What this page is for

The Pulse is your “what matters now” screen. Each item is a card that starts with **implication**, not headline news.

### The mental model (how to read it fast)

1. Treat each card as a **claim**: “X is likely to affect Y.”
2. Use the **insight panel** (when present) to get the fast summary.
3. Open the **Thread** only when you want the full chain and evidence.

### Where to look for critical information

- **Top bar**
  - **Surface title**: confirms you’re on Pulse.
  - **Category filters**: the fastest way to narrow the feed.
- **Card list (main column)**
  - **Implication headline**: the most important sentence on the card preview.
  - **Category + timestamp**: helps you interpret relevance and recency.
  - **Instrument chips**: quick view of which instruments are affected (opportunity/headwind/watch).
  - **Resolved state** (if shown): indicates the lifecycle has moved on; resolved items may remain visible for track record credibility.
- **Right-side insight panel** (desktop / wide screens)
  - **“Read full analysis in The Thread →”**: the primary action when you want depth.

### Common tasks

- **Filter by category**: use the category pills/filters to cut noise.
- **Open a Thread**: click a card or “Read full analysis”.

### Troubleshooting

- **“Nothing is loading”**: sign in and refresh. Some surfaces require auth (e.g., Map).
- **“Feed doesn’t feel relevant”** (Tracker/Protector): add **Session holdings** (see §9).

---

## 5) The Thread — full card (`/thread/[cardId]`)

### What this page is for

The Thread is the deep read: you get the full Event Intelligence Card and the “why”.

### Where to look for critical information

- **ICE stack / sections**: Insight → Context → Evidence → (Dissent / Framework where available)
  - **Insight**: what the card claims will happen / what it means.
  - **Evidence**: the ground-truth anchors (look here if you’re skeptical).
  - **Dissent**: the counter-argument; read this to avoid overconfidence.
- **Confidence panel (“Why this confidence tier?”)**
  - **Tier**: HIGH / MEDIUM / LOW (routing confidence)
  - **Raw vs effective**: effective may be dampened when uncertainty is high (Fog of War situations)
- **Holdings callout** (Tracker/Protector, when holdings are set)
  - Look for a small callout like “What this means for your {holding}” when the card intersects your session holdings.

### Common tasks

- **Validate the claim**: jump to Evidence and check if the key numbers are grounded.
- **Understand uncertainty**: open the confidence tier breakdown before acting on the idea.

---

## 6) The Map — sector learning (`/map` and `/map/[slug]`)

### What this page is for

The Map is the preparation layer: it teaches sector structure so future Pulse/Thread cards make sense.

### What you can do here

- Browse **sectors** (index screen)
- Open a sector deep-dive (`/map/[slug]`)
- Jump to a highlighted module (some links route using `?module=...`)

### Where to look for critical information

- **Sector list / cards**: choose a sector to explore.
- **Highlighted module jump** (when present via URL): if you arrive with `?module=...`, the Map may redirect you into the right sector automatically.

### Troubleshooting

- **“Sign in to explore The Map.”**: Map requires authentication; sign in and retry.

---

## 7) The Mirror — learning history (`/mirror`)

### What this page is for

The Mirror helps you learn over time. It is not a rupee performance tracker; it is a reasoning and accuracy tracker.

### Where to look for critical information

- **Top stats strip / summary** (if present): your overall prediction history.
- **History list**: individual items, often filterable by status (e.g., `?status=...`).

### Common tasks

- **Review resolved outcomes**: look for what happened after your prediction.
- **Spot reasoning gaps**: use Mirror items to see where you over/under-estimated.

---

## 8) The Lens — on-demand card generation (`/lens`)

### What this page is for

Lens is research mode. Use it when you want to ask: “What does *this* event mean?” and you are willing to wait longer for an answer.

### Where to look for critical information

- **Top bar**: confirms you are in Lens (and may show helper copy).
- **Generated card output**: treat it like a Thread card—read Evidence and Dissent, not just Insight.

### Best practices (to get better results)

- Ask a **specific** question (event + instrument/sector + time horizon).
- If the output feels too generic, refine the question rather than re-running the same prompt.

---

## 9) Portfolio Tracker feature: Session holdings (optional but recommended)

### What it is (and what it is not)

**Session holdings** is a lightweight, privacy-first way to personalise Pulse ordering and Thread callouts.

- **Stored only in this browser tab** (session storage). Close the tab and holdings disappear.
- **Not stored on FinnWise servers**.
- Pulse uses an **opaque personalisation token** (hashed, no raw tickers in the URL).

### How to use it

1. Open the sidebar **User chip** (your profile area).
2. Choose **Session holdings**.
3. Search instruments (type at least 2 characters) and add the ones you own or track.
4. Save.

### What changes after you add holdings

- **The Pulse**: events that intersect your holdings can rise higher in the feed ordering.
- **The Thread**: you may see a callout linking the card to your holdings.

### Troubleshooting

- **“Holdings won’t save”**: you may not have a stored onboarding `session_id` yet. Re-run onboarding and try again.
- **“I don’t see any personalisation effect”**: personalisation is **ordering**, not filtering. Non-matching cards still appear.

---

## 10) Account (`/account`) and Email settings (`/settings/email`)

### What these pages are for

- **Account**: view your sign-in state / account basics.
- **Email settings**: configure email-related preferences (where enabled).

### Where to look for critical information

- **Current identity**: the email you are signed in with.
- **Delivery expectations**: if you enable emails, treat them as notifications, not trading signals.

---

## 11) Quick glossary (terms you’ll see)

- **Surface**: one of Pulse / Thread / Map / Mirror / Lens.
- **Card**: an Event Intelligence Card.
- **ICE**: Insight / Context / Evidence (core structure).
- **Tier**: HIGH/MEDIUM/LOW confidence routing.
- **Fog of War**: a state where multiple major events increase uncertainty; effective confidence may be dampened.
- **Resolved**: the card’s lifecycle has progressed; it may remain visible for track record.

