javascript

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Footer, PageBreak
} = require('docx');
const fs = require('fs');

const NAVY = "0F172A";
const BLUE = "1A4FCC";
const BLUE_LIGHT = "DBEAFE";
const GREEN = "0A6644";
const GREEN_LIGHT = "D1FAE5";
const AMBER = "8A5009";
const AMBER_LIGHT = "FEF3C7";
const RED = "9B2416";
const RED_LIGHT = "FEE2E2";
const SLATE_200 = "E2E8F0";
const SLATE_400 = "94A3B8";
const SLATE_700 = "334155";
const WHITE = "FFFFFF";
const PURPLE = "6B21A8";
const PURPLE_LIGHT = "F3E8FF";

const border = { style: BorderStyle.SINGLE, size: 1, color: SLATE_200 };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorders = {
  top: { style: BorderStyle.NONE, size: 0, color: WHITE },
  bottom: { style: BorderStyle.NONE, size: 0, color: WHITE },
  left: { style: BorderStyle.NONE, size: 0, color: WHITE },
  right: { style: BorderStyle.NONE, size: 0, color: WHITE },
};
const cellMargins = { top: 100, bottom: 100, left: 150, right: 150 };

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, bold: true, size: 36, font: "Arial", color: NAVY })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 100 },
    children: [new TextRun({ text, bold: true, size: 28, font: "Arial", color: NAVY })]
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, font: "Arial", color: SLATE_700 })]
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: SLATE_700, ...opts })]
  });
}

function gap(text) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    indent: { left: 360 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: SLATE_700, italics: true })]
  });
}

function mono(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    shading: { fill: "F1F5F9", type: ShadingType.CLEAR },
    indent: { left: 360, right: 360 },
    children: [new TextRun({ text, size: 18, font: "Courier New", color: NAVY })]
  });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: SLATE_700, ...opts })]
  });
}

function subbullet(text) {
  return new Paragraph({
    numbering: { reference: "subbullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 20, font: "Arial", color: SLATE_700 })]
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: SLATE_700 })]
  });
}

function rule() {
  return new Paragraph({
    spacing: { before: 160, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: SLATE_200 } },
    children: []
  });
}

function space(n = 1) {
  return Array(n).fill(new Paragraph({ spacing: { before: 60, after: 60 }, children: [] }));
}

function labeledPara(label, text, labelColor = BLUE) {
  return new Paragraph({
    spacing: { before: 80, after: 80 },
    children: [
      new TextRun({ text: label + ": ", bold: true, size: 22, font: "Arial", color: labelColor }),
      new TextRun({ text, size: 22, font: "Arial", color: SLATE_700 })
    ]
  });
}

function bannerTable(text, fillColor, textColor, borderColor) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: {
          top: { style: BorderStyle.SINGLE, size: 4, color: borderColor },
          bottom: { style: BorderStyle.SINGLE, size: 1, color: borderColor },
          left: { style: BorderStyle.SINGLE, size: 1, color: borderColor },
          right: { style: BorderStyle.SINGLE, size: 1, color: borderColor },
        },
        shading: { fill: fillColor, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 160, right: 160 },
        children: [new Paragraph({
          children: [new TextRun({ text, size: 20, font: "Arial", color: textColor })]
        })]
      })]
    })]
  });
}

function gapTable(gapId, title, layer, description, priority, priorityColor, bgColor) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1000, 7160, 1200],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders, shading: { fill: bgColor, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: gapId, bold: true, size: 20, font: "Courier New", color: NAVY })] })]
          }),
          new TableCell({
            borders, shading: { fill: bgColor, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [
              new Paragraph({ children: [new TextRun({ text: title, bold: true, size: 22, font: "Arial", color: NAVY })] }),
              new Paragraph({ children: [new TextRun({ text: "Layer: " + layer, size: 18, font: "Courier New", color: SLATE_400 })] }),
              new Paragraph({ spacing: { before: 80 }, children: [new TextRun({ text: description, size: 20, font: "Arial", color: SLATE_700 })] }),
            ]
          }),
          new TableCell({
            borders, shading: { fill: priorityColor, type: ShadingType.CLEAR },
            margins: cellMargins,
            verticalAlign: "center",
            children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: priority, bold: true, size: 18, font: "Courier New", color: NAVY })] })]
          }),
        ]
      })
    ]
  });
}

function decisionTable(blockLabel, blockColor, decisions) {
  const rows = [
    new TableRow({
      children: [
        new TableCell({
          columnSpan: 3,
          borders,
          shading: { fill: blockColor, type: ShadingType.CLEAR },
          margins: cellMargins,
          children: [new Paragraph({ children: [new TextRun({ text: blockLabel, bold: true, size: 22, font: "Arial", color: NAVY })] })]
        })
      ]
    }),
    new TableRow({
      children: [
        new TableCell({ borders, shading: { fill: "F1F5F9", type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "#", bold: true, size: 20, font: "Arial", color: SLATE_700 })] })] }),
        new TableCell({ borders, shading: { fill: "F1F5F9", type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Decision", bold: true, size: 20, font: "Arial", color: SLATE_700 })] })] }),
        new TableCell({ borders, shading: { fill: "F1F5F9", type: ShadingType.CLEAR }, margins: cellMargins, width: { size: 4860, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Agreed answer", bold: true, size: 20, font: "Arial", color: SLATE_700 })] })] }),
      ]
    }),
    ...decisions.map((d, i) => new TableRow({
      children: [
        new TableCell({ borders, margins: cellMargins, width: { size: 500, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: String(i + 1), size: 20, font: "Arial", color: SLATE_400 })] })] }),
        new TableCell({ borders, margins: cellMargins, width: { size: 4000, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: d.question, size: 20, font: "Arial", color: SLATE_700 })] })] }),
        new TableCell({ borders, margins: cellMargins, width: { size: 4860, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: d.answer, size: 20, font: "Arial", color: GREEN, bold: true })] })] }),
      ]
    }))
  ];
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [500, 4000, 4860], rows });
}

function codeBlock(lines) {
  return lines.map(l => mono(l));
}

const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "subbullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2013", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }] },
      { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 36, bold: true, font: "Arial", color: NAVY }, paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, font: "Arial", color: NAVY }, paragraph: { spacing: { before: 280, after: 100 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 24, bold: true, font: "Arial", color: SLATE_700 }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "FinnWise PRD 2 \u2014 Intelligence Architecture Redesign \u2014 CONFIDENTIAL \u2014 Page ", size: 18, font: "Arial", color: SLATE_400 }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, font: "Arial", color: SLATE_400 }),
          ]
        })]
      })
    },
    children: [

      // ── COVER ──────────────────────────────────────────────────────────────
      new Paragraph({ spacing: { before: 1440, after: 240 }, children: [new TextRun({ text: "FinnWise", bold: true, size: 64, font: "Arial", color: NAVY })] }),
      new Paragraph({ spacing: { before: 0, after: 120 }, children: [new TextRun({ text: "Product Requirements Document \u2014 Volume 2", size: 36, font: "Arial", color: SLATE_700 })] }),
      new Paragraph({ spacing: { before: 0, after: 480 }, children: [new TextRun({ text: "Intelligence Architecture Redesign", bold: true, size: 32, font: "Arial", color: BLUE })] }),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 6960],
        rows: [
          ["Status", "Final — supersedes all event-detection and confidence-scoring decisions in PRD v3"],
          ["Scope", "Phase 3 intelligence layer: confidence scoring, de-duplication, LLM validation, Fog of War, NLP pipeline, hosting architecture"],
          ["Solo builder", "Three roles (Jordan / Sam / Riley) played by one person with role-switching"],
          ["LLM in prod", "Google Gemini (Phase 1/2). Phase 3 NLP: Gemini Flash."],
          ["Hosting", "Render free tier (API server) + GitHub Actions (batch jobs). No tier upgrade required."],
          ["SEBI posture", "Exploratory research. P3-S6 (marketing) and P3-S7 (billing) formally deferred."],
          ["Phase 2 status", "Complete and clean. All Phase 2 stories ticked."],
          ["Live tester data", "None yet. Synthetic seed strategy defined in Section 7."],
          ["Date", new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })],
        ].map(([k, v]) => new TableRow({
          children: [
            new TableCell({ borders, shading: { fill: "F1F5F9", type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: k, bold: true, size: 20, font: "Arial", color: NAVY })] })] }),
            new TableCell({ borders, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: v, size: 20, font: "Arial", color: SLATE_700 })] })] }),
          ]
        }))
      }),

      ...space(2),
      bannerTable(
        "SEBI DISCLAIMER: This document describes analytical infrastructure for an educational research application. It does not constitute investment advice under SEBI (Investment Advisers) Regulations 2013. No fee is charged. No personalised investment advice is provided.",
        "FEF2F2", RED, "FECACA"
      ),

      new Paragraph({ children: [new PageBreak()] }),

      // ── SECTION 1: PURPOSE ────────────────────────────────────────────────
      h1("1. Purpose and Scope"),
      body("This document resolves fifteen gaps in the FinnWise intelligence architecture that were identified across the PRD v3 event detection journey, the Phase 1/2 task audit, and the Phase 3 prerequisite review. These gaps were unspecified at the time Phase 1 and Phase 2 were built, meaning the implementations that exist in production may be producing outputs against undefined specifications."),
      ...space(1),
      body("PRD 2 does two things:"),
      bullet("Closes every open architectural decision with a definitive, implementable answer so Phase 3 build starts on solid ground."),
      bullet("Replaces the Phase 3 task list with a scope-corrected, solo-sequenced build plan that reflects the actual constraints: one builder, Render free tier, no live tester data, SEBI exploratory posture."),
      ...space(1),
      body("This document supersedes all confidence scoring, de-duplication, LLM validation, Fog of War trigger, and hosting architecture decisions from PRD v3. Where PRD v3 and PRD 2 conflict, PRD 2 governs for Phase 3 build."),

      rule(),

      // ── SECTION 2: GAP REGISTER ──────────────────────────────────────────
      h1("2. Gap Register \u2014 All Layers"),
      body("Fifteen gaps identified across five architectural layers, rated by criticality. P0 = build blocker. P1 = high risk. P2 = medium, manageable during build. All P0 and P1 gaps are resolved in Sections 3\u20137."),
      ...space(1),

      h2("2.1 Layer 1 \u2014 Confidence Scoring (blocks everything downstream)"),
      gapTable("G-01", "Confidence score methodology is a black box", "Event detection \u2192 confidence gate \u2192 signal monitoring",
        "PRD v3 says score is AI-generated but defines no inputs, model, thresholds, or output format. Every routing decision downstream (High/Medium/Low) depends on this. The Phase 1 scorer was built against an undefined spec and may produce arbitrary outputs.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-02", "High/Medium/Low threshold values are arbitrary", "Confidence gate routing",
        "Even if the scorer exists, the numeric thresholds that determine routing tier were never defined. Phase 3 interaction model (P3-S2) builds on top of these \u2014 compounding undefined on undefined.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),

      ...space(1),
      h2("2.2 Layer 2 \u2014 Data Pipeline Integrity"),
      gapTable("G-03", "De-duplication logic undefined \u2014 same event hits multiple sources", "Raw event queue \u2192 deduplication \u2192 persistence",
        "RBI rate announcements appear in NewsAPI, RBI RSS, and NSE feed simultaneously. Phase 1 task 6.6 was ticked done but the deduplication key was never specified. Wrong key = missed events or duplicate editorial reviews.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-04", "NewsAPI keyword filters never defined", "Source monitoring \u2014 NewsAPI adapter",
        "100 calls/day cap. Without defined keyword filters the adapter returns noise or misses events. No keyword list was ever documented against the 8 Factor DB macro factors.",
        "P1 \u2013 HIGH", AMBER_LIGHT, "FFFDF5"),
      ...space(1),
      gapTable("G-05", "Slow-burn watchlist completely unspecified", "Source monitoring \u2014 manual watchlist",
        "PRD v3 mentions it as a source but gives no format, owner process, escalation trigger, or DB table. As a solo builder, this is the highest-risk item to be skipped. Slow-burn events (monsoon deficit, regulatory reviews, budget cycle) require the most lead time.",
        "P1 \u2013 HIGH", AMBER_LIGHT, "FFFDF5"),
      ...space(1),
      gapTable("G-06", "yfinance and NSE scraper fragility \u2014 no tested fallback", "Macro data sources \u2192 Factor DB refresh",
        "PRD v3 flags this risk. Phase 1 built source abstraction but fallback sources were never named or integrated. Phase 3 NLP pipeline adds a nightly filings job that will exacerbate scraper exposure.",
        "P1 \u2013 HIGH", AMBER_LIGHT, "FFFDF5"),

      ...space(1),
      h2("2.3 Layer 3 \u2014 LLM Pipeline Integrity"),
      gapTable("G-07", "Post-generation validation \u2014 no defined automated checks that block publication", "Draft generation \u2192 editorial queue",
        "The LLM must never generate numbers \u2014 all numbers must trace to the Evidence layer. Whether the Phase 1 number_validator enforces this as a hard publish gate or a soft warning is unknown. As solo builder reviewing your own AI output, a soft warning is not sufficient.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-08", "Gemini vs smaller model for Phase 3 NLP extraction", "LLM architecture \u2014 Phase 3 P3-S1a",
        "Phase 3 NLP filings extraction uses an LLM but which model was never specified. Gemini Pro is overkill for JSON-strict extraction from a bounded source excerpt. Gemini Flash is 10x cheaper and sufficient.",
        "P1 \u2013 HIGH", AMBER_LIGHT, "FFFDF5"),
      ...space(1),
      gapTable("G-09", "Editorial rejection loop \u2014 full re-run vs targeted section regen", "Editorial review \u2192 draft revision",
        "When a draft card fails review, no return path is defined. Full 3-call re-run wastes cost and ignores specific editor feedback. Targeted section regen preserves the editor's annotation.",
        "P2 \u2013 MEDIUM", BLUE_LIGHT, "F8FAFF"),

      ...space(1),
      h2("2.4 Layer 4 \u2014 Fog of War and Signal Model"),
      gapTable("G-10", "Fog of War major event trigger has no implementable definition", "Fog of War banner \u2192 confidence suppression \u2192 Phase 3 interaction model",
        "PRD v3 says fires at 3+ major events simultaneously active. Neither the definition of major nor the transition between Phase 1 heuristic and Phase 3 model is defined. The 6-month backtest has no real data to run against.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-11", "Signal false-positive rate \u2014 measurement mechanism never implemented", "Confidence-gated signal detection \u2192 override log",
        "PRD v3 sets a V1 target of less than 10% false positive rate. The override log was mentioned but never specified as a DB table. Without measurement the target is unmeasurable.",
        "P1 \u2013 HIGH", AMBER_LIGHT, "FFFDF5"),

      ...space(1),
      h2("2.5 Layer 5 \u2014 Phase 3 Specific Gaps"),
      gapTable("G-12", "Render free tier cold-start kills nightly NLP job", "P3-S1a NLP pipeline \u2014 hosting constraint",
        "Render free tier spins down after 15 minutes of inactivity. A nightly PDF-processing job will cold-start from zero every night. spaCy model load alone takes 10\u201330 seconds. The job will appear to run but silently fail or timeout.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-13", "No live Mirror/Lens data \u2014 Phase 3 ML prerequisites unmet", "Phase 3 prerequisite \u2014 tester data",
        "Phase 3 requires Mirror + Lens live data for 3+ months. Fog of War backtest, reasoning gap detector, and NLP Factor DB comparison all need historical ground truth. Starting Phase 3 ML work without this means building blind.",
        "P0 \u2013 CRITICAL", RED_LIGHT, "FFFAFA"),
      ...space(1),
      gapTable("G-14", "P3-S6/S7 marketing and billing are dead weight until SEBI gate", "Phase 3 scope \u2014 SEBI posture",
        "SEBI stays exploratory. P3-S8 gate will not go green without RA registration decision. Building marketing and billing infrastructure before the gate wastes solo effort and creates decision fatigue.",
        "P2 \u2013 MEDIUM", BLUE_LIGHT, "F8FAFF"),
      ...space(1),
      gapTable("G-15", "Editorial checklist never formalised as a hard pass/fail gate", "Editorial review \u2014 ongoing quality control",
        "Phase 1 built a ChecklistPanel but acceptance criteria were never defined per item. As solo builder reviewing own AI output, unchecked items must block publish \u2014 not be soft reminders.",
        "P2 \u2013 MEDIUM", BLUE_LIGHT, "F8FAFF"),

      new Paragraph({ children: [new PageBreak()] }),

      // ── SECTION 3: BLOCK A — CONFIDENCE SCORING ──────────────────────────
      h1("3. Block A \u2014 Confidence Scoring Decisions"),
      bannerTable("P0 blocker. Every routing decision in the pipeline depends on this. Resolve before any Phase 3 build begins.", AMBER_LIGHT, AMBER, "FED7AA"),
      ...space(1),

      h2("3.1 Decision: Rule-based scorer replaces AI-generated score"),
      body("The PRD v3 description of an AI-generated confidence score is replaced. Rationale: a rule-based weighted scorer is debuggable, reproducible, requires no LLM call, and produces an auditable numeric basis for every routing decision. Reserve Gemini for the three card synthesis roles where it genuinely adds value."),
      ...space(1),
      h3("Scorer specification"),
      ...codeBlock([
        "confidence_score(event) -> float (0.0 to 1.0):",
        "",
        "  source_count_score   = min(event.source_count / 3, 1.0)  x 0.35",
        "  source_quality_score = QUALITY_MAP[event.primary_source]  x 0.30",
        "  factor_db_match      = factor_db.match_strength(event)    x 0.25",
        "  recency_score        = decay_fn(event.first_seen_at)      x 0.10",
        "",
        "  raw = sum(above)   # 0.0 - 1.0",
        "",
        "  if fog_of_war_active:",
        "    raw = raw * FOG_DAMPENER   # default 0.6, see Section 6",
        "",
        "  store raw on events.confidence_raw",
        "  return raw",
      ]),
      ...space(1),
      h3("Source quality map \u2014 Indian financial sources"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [4680, 2340, 2340],
        rows: [
          ["Source tier", "Examples", "Quality weight"],
          ["Official government / exchange feed", "RBI website, NSE official, BSE official, Ministry of Finance", "1.0"],
          ["Major news wire", "PTI, Reuters India, Bloomberg India, IANS", "0.8"],
          ["Financial press", "Economic Times, Mint, Business Standard, Hindu Business Line", "0.65"],
          ["General news", "Times of India financial desk, NDTV Business, Moneycontrol", "0.50"],
          ["Aggregator / blog / social", "Twitter/X, Substack, Reddit IndiaInvestments", "0.30"],
        ].map((row, i) => new TableRow({
          children: row.map((cell, j) => new TableCell({
            borders,
            shading: { fill: i === 0 ? "F1F5F9" : WHITE, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 20, font: "Arial", color: i === 0 ? NAVY : SLATE_700 })] })]
          }))
        }))
      }),
      ...space(1),
      h3("Factor DB match strength"),
      body("factor_db.match_strength(event) returns 0.0 to 1.0 based on how many of the 8 macro factors the event touches, weighted by event category:"),
      bullet("Direct match to 2+ factors: 1.0 (e.g. RBI rate decision touches domestic interest rates + bank NIM directly)"),
      bullet("Direct match to 1 factor: 0.7"),
      bullet("Indirect / sector match only: 0.4"),
      bullet("No Factor DB match: 0.0"),
      ...space(1),
      h3("Recency decay function"),
      ...codeBlock([
        "decay_fn(first_seen_at):",
        "  age_hours = (now - first_seen_at).total_seconds() / 3600",
        "  if age_hours <= 4:   return 1.0   # within one detection cycle",
        "  if age_hours <= 12:  return 0.7",
        "  if age_hours <= 24:  return 0.4",
        "  return 0.1                         # stale event",
      ]),

      ...space(1),
      h2("3.2 Decision: Routing thresholds"),
      body("Calibrated against 10 historical Indian financial events (manual calibration exercise required in Week 2 of the Phase 3 build, see Section 9):"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2000, 2500, 4860],
        rows: [
          ["Tier", "Raw score threshold", "System action"],
          ["HIGH", ">= 0.75", "Auto-generate draft card. Notify editor. 2-hour override window."],
          ["MEDIUM", ">= 0.45 and < 0.75", "Generate draft. Hold in editorial queue. Editor reviews within 10 minutes."],
          ["LOW", "< 0.45", "Log to events table. Surface in daily editorial digest. No card generated."],
        ].map((row, i) => new TableRow({
          children: row.map(cell => new TableCell({
            borders,
            shading: { fill: i === 0 ? "F1F5F9" : WHITE, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 20, font: "Arial", color: i === 0 ? NAVY : SLATE_700 })] })]
          }))
        }))
      }),
      body("These thresholds are stored in a config file (backend/app/core/confidence_config.py), not hardcoded. They are tunable without a code change after calibration."),

      rule(),

      // ── SECTION 4: BLOCK B — DATA PIPELINE ───────────────────────────────
      h1("4. Block B \u2014 Data Pipeline Decisions"),
      ...space(1),

      h2("4.1 Decision: De-duplication key"),
      body("A composite SHA-256 key prevents the same real-world event from generating multiple queue entries when it appears in multiple sources simultaneously."),
      ...codeBlock([
        "dedup_key = sha256(",
        "  event_category       +   # 'RBI_POLICY' / 'CRUDE' / 'GEOPOLITICAL' / etc.",
        "  normalise(entity)    +   # see entity normalisation dict below",
        "  date_floor_4h(detected_at)  # floor to nearest 4-hour window",
        ")",
        "",
        "INSERT INTO events (..., dedup_key, source_count, sources)",
        "ON CONFLICT (dedup_key)",
        "DO UPDATE SET",
        "  source_count = events.source_count + 1,",
        "  sources      = array_append(events.sources, EXCLUDED.sources[1]),",
        "  confidence_raw = recompute_score(events.id)   # score improves as sources accumulate",
      ]),
      ...space(1),
      body("Entity normalisation dictionary \u2014 top 30 Indian financial entities (extend as needed):"),
      ...codeBlock([
        "ENTITY_MAP = {",
        "  'Reserve Bank of India': 'rbi', 'RBI': 'rbi',",
        "  'National Stock Exchange': 'nse', 'NSE': 'nse',",
        "  'Bombay Stock Exchange': 'bse', 'BSE': 'bse',",
        "  'SEBI': 'sebi', 'Securities and Exchange Board': 'sebi',",
        "  'ONGC': 'ongc', 'Oil and Natural Gas': 'ongc',",
        "  'State Bank of India': 'sbi', 'SBI': 'sbi',",
        "  'HDFC Bank': 'hdfc_bank', 'ICICI Bank': 'icici_bank',",
        "  'Infosys': 'infosys', 'TCS': 'tcs', 'Tata Consultancy': 'tcs',",
        "  'Reliance Industries': 'ril', 'Reliance': 'ril',",
        "  'OPEC': 'opec', 'Federal Reserve': 'fed', 'US Fed': 'fed',",
        "  # ... extend to 50+ entities over Phase 3",
        "}",
      ]),

      ...space(1),
      h2("4.2 Decision: NewsAPI keyword filters per Factor DB macro factor"),
      body("Each of the 8 Factor DB macro factors maps to a keyword set. The NewsAPI adapter cycles through these sets across its 100 daily calls, allocating calls proportionally to factor volatility:"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 1500, 5460],
        rows: [
          ["Factor", "Daily calls", "Keyword set"],
          ["Crude oil price", "15", "crude oil, brent, WTI, OPEC, oil price India, petroleum, ATF price, ONGC, oil ministry"],
          ["Dollar-Rupee rate", "15", "rupee dollar, INR USD, RBI forex, currency India, dollar rate, foreign exchange India"],
          ["Domestic interest rates", "20", "RBI rate, repo rate, monetary policy, MPC meeting, inflation India, CPI India, RBI circular"],
          ["Global risk sentiment", "10", "FII outflow, FII inflow, foreign institutional, risk off, global selloff, emerging markets"],
          ["Monsoon index", "10", "monsoon India, IMD forecast, rainfall deficit, kharif, rabi, food inflation India"],
          ["Government capex", "10", "union budget, capex India, infrastructure spending, PLI scheme, government spending"],
          ["GST collections", "10", "GST collection, goods services tax, ministry of finance monthly, consumption India"],
          ["Regulatory environment", "10", "SEBI circular, NSE regulation, RBI regulation, sector policy India, new regulation"],
        ].map((row, i) => new TableRow({
          children: row.map(cell => new TableCell({
            borders,
            shading: { fill: i === 0 ? "F1F5F9" : WHITE, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 19, font: "Arial", color: i === 0 ? NAVY : SLATE_700 })] })]
          }))
        }))
      }),
      body("Total: 100 calls/day exactly. Adjust allocation based on Phase 3 event frequency data."),

      ...space(1),
      h2("4.3 Decision: Slow-burn watchlist format and process"),
      body("A DB table replaces the undefined manual watchlist. The solo builder reviews it every Sunday morning as a calendar-blocked 30-minute session."),
      ...codeBlock([
        "CREATE TABLE watchlist_items (",
        "  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),",
        "  event_description text NOT NULL,",
        "  category          text NOT NULL,  -- same enum as events.category",
        "  added_at          timestamptz DEFAULT now(),",
        "  review_frequency  text DEFAULT 'weekly',  -- 'daily'/'weekly'/'monthly'",
        "  last_reviewed_at  timestamptz,",
        "  escalation_trigger text,  -- condition that moves this to active event",
        "  status            text DEFAULT 'watching'  -- 'watching'/'escalated'/'closed'",
        ");",
      ]),
      body("Qualifying slow-burn categories for Phase 3 seed:"),
      bullet("Electoral calendar \u2014 state elections with market-sensitive outcomes (e.g. UP, Maharashtra)"),
      bullet("Regulatory reviews in progress \u2014 pending SEBI circulars, RBI consultation papers"),
      bullet("Monsoon outlook \u2014 IMD seasonal forecast updates (April, June, August windows)"),
      bullet("Union Budget cycle \u2014 pre-budget expectations, interim budget, full budget"),
      bullet("Geopolitical slow burns \u2014 India-Pakistan tensions, India-China trade disputes, sanctions affecting Indian imports"),

      ...space(1),
      h2("4.4 Decision: Data source fallback chain"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [2400, 3500, 3460],
        rows: [
          ["Data type", "Primary source", "Fallback chain"],
          ["Stock EOD prices", "yfinance (Yahoo Finance)", "1. investing.com scrape  2. Manual entry + staleness flag  3. Freshness dot turns red"],
          ["Currency rates", "yfinance INR/USD", "1. Open Exchange Rates free API  2. RBI reference rate page scrape"],
          ["NSE FII/DII data", "NSE public CSV", "1. CDSL data portal  2. NSE website table scrape with retry  3. Stale + flag"],
          ["RBI policy data", "RBI RSS feed", "1. RBI website direct scrape  2. Manual entry (events rarely missed)"],
          ["Market news", "NewsAPI free tier", "1. GNews API free tier (100/day)  2. RSS feeds: ET Markets, Mint"],
          ["Fundamental data", "Screener.in / Tickertape", "Manual weekly review only. No automated fallback. Grey area."],
        ].map((row, i) => new TableRow({
          children: row.map(cell => new TableCell({
            borders,
            shading: { fill: i === 0 ? "F1F5F9" : WHITE, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 19, font: "Arial", color: i === 0 ? NAVY : SLATE_700 })] })]
          }))
        }))
      }),

      rule(),

      // ── SECTION 5: BLOCK C — LLM PIPELINE ────────────────────────────────
      h1("5. Block C \u2014 LLM Pipeline Decisions"),
      ...space(1),

      h2("5.1 Decision: Number validator is a hard publish gate, not a warning"),
      body("This is the most important integrity mechanism in the product. The Publish button in the editorial interface is disabled until number_validator.check(card) returns PASS. There is no override. There is no per-card exception."),
      ...codeBlock([
        "number_validator.check(card) -> PASS | FAIL(reasons):",
        "",
        "  # Step 1: Extract all numeric tokens from Insight + Context text",
        "  numbers = extract_numerics(card.insight_text + card.context_text)",
        "  # regex: [0-9]+([.,][0-9]+)?\\s*(%|bps|Cr|L|K|bn|mn|$/Rs/INR)?",
        "",
        "  # Step 2: Every number must appear in at least one Evidence row",
        "  ungrounded = []",
        "  for num in numbers:",
        "    if not any(num_appears_in(num, row.source_excerpt) for row in card.evidence):",
        "      ungrounded.append(num)",
        "",
        "  # Step 3: Every Evidence row must have required fields",
        "  missing_provenance = [",
        "    row for row in card.evidence",
        "    if not (row.source_url and row.retrieved_at and row.mmj_tag)",
        "  ]",
        "",
        "  if ungrounded or missing_provenance:",
        "    return FAIL(ungrounded=ungrounded, missing=missing_provenance)",
        "  return PASS",
      ]),
      body("The editorial interface shows a structured diff when FAIL is returned: which numbers in the narrative have no Evidence backing, listed by sentence. The editor either adds an Evidence row with the source or rewrites the narrative sentence to remove the unsupported number."),

      ...space(1),
      h2("5.2 Decision: LLM model for Phase 3 NLP filings extraction"),
      body("Gemini Flash (gemini-1.5-flash or gemini-2.0-flash-lite, whichever is active in Gemini API at Phase 3 build time) for the P3-S1a NLP filings extraction job. Rationale:"),
      bullet("The task is JSON-strict extraction from a bounded source excerpt \u2014 Gemini Pro is overkill."),
      bullet("Gemini Flash is approximately 10x cheaper per token at comparable JSON-extraction quality."),
      bullet("The source_guard hallucination check (G-01a in Phase 3) catches any model errors programmatically."),
      bullet("Same provider as production card synthesis (Gemini Pro) \u2014 no new API keys, no new billing account."),
      body("The three-call card synthesis pipeline (Role 1/2/3) continues to use Gemini Pro. Only the NLP extraction job uses Flash."),

      ...space(1),
      h2("5.3 Decision: Editorial rejection loop \u2014 targeted section regen"),
      body("When a draft card fails editorial review, the editor annotates which ICE section failed and why. A targeted regen call re-runs only the failing section's LLM call with the editor's annotation appended to the prompt. Full re-runs are not permitted in the standard flow."),
      ...codeBlock([
        "POST /api/cards/{id}/regenerate-section",
        "Body: {",
        "  section: 'insight' | 'context' | 'evidence' | 'dissent' | 'framework',",
        "  editor_note: string  // editor's specific objection, max 500 chars",
        "}",
        "",
        "# The regeneration prompt appends:",
        "# 'EDITOR FEEDBACK: {editor_note}. Revise this section only.",
        "#  All other sections are approved. Do not alter them.'",
      ]),
      body("The full 3-call re-run is available as a separate button (POST /api/cards/{id}/regenerate-full) for cases where the card is fundamentally wrong, but it requires a separate confirmation and logs a full_regen_count on the card row. A card with full_regen_count > 2 gets flagged in the editorial queue for Product Owner review before publish."),

      rule(),

      // ── SECTION 6: BLOCK D — FOG OF WAR ──────────────────────────────────
      h1("6. Block D \u2014 Fog of War and Signal Model Decisions"),
      ...space(1),

      h2("6.1 Decision: Formalise the is_major attribute on the events table"),
      body("The word major is given a concrete, storable definition. This attribute is the shared foundation that both the Phase 1 heuristic and the Phase 3 interaction model reference."),
      ...codeBlock([
        "ALTER TABLE events ADD COLUMN is_major BOOLEAN DEFAULT FALSE;",
        "",
        "-- is_major = TRUE when ALL three conditions are met:",
        "--   1. confidence_raw >= 0.75 (HIGH tier)",
        "--   2. factor_db_match_count >= 2  (touches 2+ of the 8 macro factors)",
        "--   3. category IN ('RBI_POLICY','GEOPOLITICAL','BUDGET','GLOBAL_MACRO','CRUDE_SHOCK')",
        "",
        "-- Set automatically by the confidence scorer after each event upsert.",
        "-- Can be manually overridden by Product Owner via editorial interface.",
        "",
        "-- Fog of War heuristic (Phase 1 fallback):",
        "--   SELECT COUNT(*) FROM events",
        "--   WHERE is_major = TRUE AND lifecycle_state = 'active'",
        "--   >= 3  -->  fog_of_war_active = TRUE",
      ]),

      ...space(1),
      h2("6.2 Decision: Fog of War confidence dampener"),
      body("When Fog of War is active, the confidence scorer applies a 0.6 multiplier to all raw scores. This means:"),
      bullet("An event that would score 0.80 (HIGH) during normal conditions scores 0.48 (MEDIUM) during Fog of War."),
      bullet("An event that would score 0.70 (HIGH) scores 0.42 (LOW) during Fog of War."),
      bullet("The dampener is stored as a config constant FOG_DAMPENER = 0.6 \u2014 tunable after Phase 3 backtest."),
      body("The Fog of War banner in the Pulse shows the reason string: which is_major events are currently active and their factor overlaps. This replaces the generic banner from Phase 1."),

      ...space(1),
      h2("6.3 Decision: Phase 3 interaction model deferred until synthetic data is in place"),
      body("The P3-S2 interaction model (factor-overlap detection replacing the is_major count heuristic) requires 6 months of historical confidence data to backtest against. With no live tester data, that data does not exist. The model is deferred until the synthetic seed strategy (Section 7) is in place and has been live for at least 30 days."),
      body("Build order for P3-S2: synthetic seed first (Week 3) \u2192 let heuristic run against synthetic data for 30 days \u2192 build interaction model against the resulting card_confidence_history \u2192 backtest \u2192 feature-flag deployment."),

      ...space(1),
      h2("6.4 Decision: Signal override log \u2014 schema for false positive measurement"),
      ...codeBlock([
        "CREATE TABLE signal_override_log (",
        "  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),",
        "  signal_id       uuid REFERENCES signals(id),",
        "  card_id         uuid REFERENCES events(id),",
        "  auto_triggered_at  timestamptz NOT NULL,",
        "  overridden_at      timestamptz,",
        "  override_reason    text,",
        "  override_by        uuid REFERENCES auth.users(id),",
        "  final_outcome      text  -- 'confirmed'/'incorrect'/'ambiguous'",
        ");",
        "",
        "-- False positive rate = COUNT(override_reason IS NOT NULL AND final_outcome='incorrect')",
        "--                      / COUNT(*) WHERE auto_triggered_at IS NOT NULL",
        "-- Target: < 10% (PRD v3 Section 13)",
        "-- Measured monthly. Logged in notes/signal-override-log-monthly.md",
      ]),

      rule(),

      // ── SECTION 7: BLOCK E — HOSTING AND DATA ─────────────────────────────
      h1("7. Block E \u2014 Hosting, Infrastructure, and Data Decisions"),
      ...space(1),

      h2("7.1 Decision: GitHub Actions as Phase 3 NLP job runner"),
      body("The nightly filings extraction job (P3-S1a) runs as a GitHub Actions scheduled workflow, not on Render. This resolves the cold-start problem (G-12) at zero additional cost."),
      ...codeBlock([
        "# .github/workflows/nlp_filings_extract.yml",
        "on:",
        "  schedule:",
        "    - cron: '0 1 * * *'   # 1am IST = 7:30pm UTC, after NSE close",
        "  workflow_dispatch:       # manual trigger for testing",
        "",
        "jobs:",
        "  extract:",
        "    runs-on: ubuntu-latest",
        "    timeout-minutes: 50    # well within GH Actions 6hr limit",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "      - uses: actions/setup-python@v5",
        "        with: { python-version: '3.11' }",
        "      - run: pip install -r backend/requirements-nlp.txt",
        "      - run: python backend/app/jobs/nlp_filings_extract.py",
        "        env:",
        "          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}",
        "          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}",
        "          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}",
      ]),
      body("The existing 4-hour event detection cron stays on Render. A GH Actions ping workflow keeps the Render container warm:"),
      ...codeBlock([
        "# .github/workflows/render_keepalive.yml",
        "on:",
        "  schedule:",
        "    - cron: '*/10 4-14 * * 1-5'  # every 10min, 9:30am-8pm IST, weekdays",
        "jobs:",
        "  ping:",
        "    runs-on: ubuntu-latest",
        "    steps:",
        "      - run: curl -f ${{ secrets.BACKEND_URL }}/health || exit 0",
      ]),
      body("Total additional infrastructure cost: zero. GH Actions free tier provides 2,000 minutes/month. The nightly NLP job runs approximately 30 minutes per night = 900 minutes/month, well within the free allowance."),

      ...space(1),
      h2("7.2 Decision: Synthetic data seeding strategy"),
      body("Phase 3 ML work starts immediately using synthetic historical data seeded into the production DB tables, marked with is_synthetic = TRUE. Synthetic rows are excluded from all user-facing track record displays and from the real accuracy statistics in The Mirror."),
      ...space(1),
      h3("Seed scope"),
      bullet("20 historical Indian financial events from January to June 2025."),
      bullet("Each event seeded with: confidence scores, lifecycle transitions, signals fired, system predictions, and simulated user predictions with accuracy grades."),
      bullet("7 events designated is_major = TRUE to generate Fog of War trigger history for the backtest."),
      ...space(1),
      h3("Seed event list (20 events)"),
      body("Events to seed \u2014 all publicly verifiable from news archives:"),
      ...["RBI MPC rate hold (February 2025)", "Union Budget 2025-26 (February 1)", "RBI rate cut 25bps (April 2025)", "Pahalgam attack market reaction (April 2025)", "India-Pakistan tensions escalation (May 2025)", "RBI MPC (June 2025)", "Monsoon onset Kerala (June 2025)", "FII outflow spike (March 2025)", "Crude oil price spike on OPEC cut (March 2025)", "INR/USD move to 87+ (January 2025)", "IT sector TCS / Infosys quarterly results (January 2025)", "HDFC Bank quarterly results (January 2025)", "SBI quarterly results (February 2025)", "Nifty Bank index circuit event (April 2025)", "US tariff announcement India impact (April 2025)", "Gold price ATH India (April 2025)", "Pharma sector USFDA action (February 2025)", "PLI scheme auto sector announcement (March 2025)", "NSE F&O expiry anomaly (March 2025)", "RBI liquidity injection announcement (January 2025)"].map(e => bullet(e)),
      ...space(1),
      h3("is_synthetic flag migration"),
      ...codeBlock([
        "-- Add to: events, signals, track_record, user_predictions, card_confidence_history",
        "ALTER TABLE events ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE track_record ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE user_predictions ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE;",
        "",
        "-- RLS: synthetic rows never appear in user-facing queries",
        "-- All existing queries append: AND is_synthetic = FALSE",
        "-- Synthetic rows accessible only via service role key (admin/job use)",
      ]),

      rule(),

      // ── SECTION 8: SCOPE DECISIONS ────────────────────────────────────────
      h1("8. Phase 3 Scope Decisions"),
      ...space(1),

      h2("8.1 Formal deferral of P3-S6 and P3-S7"),
      bannerTable("P3-S6 (public marketing site + waitlist) and P3-S7 (pricing + paywall infrastructure) are formally deferred from active Phase 3 scope. They remain as a gated appendix. No build work begins on either story until P3-S8 go/no-go returns green AND a SEBI Research Analyst registration path is confirmed.", PURPLE_LIGHT, PURPLE, "DDD6FE"),
      ...space(1),
      body("Rationale: SEBI posture is exploratory. The P3-S8 gate requires RA registration decision as a precondition. Building marketing and billing infrastructure before the gate is wasted solo effort. Removing these two stories from active scope frees approximately 11 story points and eliminates billing provider selection as a current decision."),
      body("Active Phase 3 scope after deferral: P3-S1a, P3-S1b, P3-S2, P3-S3, P3-S4, P3-S5, P3-S8, P3-S9. Total: 43 story points."),

      ...space(1),
      h2("8.2 Editorial checklist \u2014 hard gate specification"),
      body("The Phase 1 ChecklistPanel is upgraded to a hard gate. Each checklist item must be explicitly marked PASS before the Publish button activates. The five items and their pass criteria:"),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [3000, 6360],
        rows: [
          ["Checklist item", "Hard pass criterion"],
          ["All numbers source-tagged", "number_validator.check() returns PASS (automated \u2014 auto-checked on card load)"],
          ["Dissenting view present", "card.dissent_text is not null and len > 100 chars (automated check)"],
          ["Confidence consistent with data freshness", "Manual tick. Editor confirms no MEASURED claim has a source older than 18 months."],
          ["Language accessible to non-expert", "Manual tick. Editor has read the Insight layer for jargon and confirmed plain English."],
          ["SEBI language compliance", "Manual tick. No buy/sell/hold. No price targets. No return expectations. All instrument chips use approved signal vocabulary."],
        ].map((row, i) => new TableRow({
          children: row.map(cell => new TableCell({
            borders,
            shading: { fill: i === 0 ? "F1F5F9" : WHITE, type: ShadingType.CLEAR },
            margins: cellMargins,
            children: [new Paragraph({ children: [new TextRun({ text: cell, bold: i === 0, size: 20, font: "Arial", color: i === 0 ? NAVY : SLATE_700 })] })]
          }))
        }))
      }),
      body("Items 1 and 2 are automated checks run on card load. Items 3, 4, and 5 require manual ticks. All five must show PASS state before Publish activates."),

      rule(),

      // ── SECTION 9: DECISION SUMMARY TABLE ────────────────────────────────
      h1("9. Decision Summary \u2014 All 15 Blocks"),
      body("Consolidated reference. Each decision is traceable to its gap ID and section."),
      ...space(1),

      decisionTable("Block A \u2014 Confidence scoring", BLUE_LIGHT, [
        { question: "AI-generated vs rule-based scorer?", answer: "Rule-based weighted scorer. 4 inputs: source_count (35%), source_quality (30%), factor_db_match (25%), recency (10%). Stored in confidence_config.py." },
        { question: "Source quality map?", answer: "5 tiers: Official feed 1.0 / Major wire 0.8 / Financial press 0.65 / General news 0.50 / Blog-social 0.30." },
        { question: "Routing thresholds?", answer: "HIGH >= 0.75 / MEDIUM >= 0.45 / LOW < 0.45. Calibrate against 10 historical events in Week 2." },
        { question: "Fog of War score dampener?", answer: "0.6x multiplier on raw score when fog_of_war_active = TRUE." },
      ]),
      ...space(1),

      decisionTable("Block B \u2014 Data pipeline", GREEN_LIGHT, [
        { question: "De-duplication key?", answer: "SHA-256 of event_category + normalised entity name + 4-hour time window floor. Source count accumulates on conflict." },
        { question: "NewsAPI keyword filters?", answer: "8 factor sets, 100 calls/day allocated proportionally. Full keyword list in Section 4.2." },
        { question: "Slow-burn watchlist format?", answer: "watchlist_items DB table. 5 categories. Weekly Sunday 30-min review session." },
        { question: "Fallback source chain?", answer: "Defined per data type in Section 4.4. Source abstraction layer tries fallbacks in order before setting staleness flag." },
      ]),
      ...space(1),

      decisionTable("Block C \u2014 LLM pipeline", AMBER_LIGHT, [
        { question: "NLP extraction model?", answer: "Gemini Flash. Same provider as prod. 10x cheaper than Pro for JSON-strict extraction. source_guard catches hallucinations." },
        { question: "Number validator gate type?", answer: "Hard gate. Publish button disabled until PASS. No per-card override. Editorial interface shows structured diff of ungrounded numbers." },
        { question: "Rejection loop design?", answer: "Targeted section regen by default. Editor annotates failing section + reason. Full re-run available but logged; card flagged if full_regen_count > 2." },
      ]),
      ...space(1),

      decisionTable("Block D \u2014 Fog of War and signals", RED_LIGHT, [
        { question: "Define major event?", answer: "is_major = TRUE when: confidence_raw >= 0.75 AND factor_db_match_count >= 2 AND category IN qualifying set. Stored as boolean column on events table." },
        { question: "Synthetic data before ML work?", answer: "Seed 20 historical events (Jan-Jun 2025) as is_synthetic rows. Unblocks Fog of War backtest and gap detector. Week 3 of Phase 3." },
        { question: "Defer P3-S6 and P3-S7?", answer: "Yes. Formally deferred. Not in active Phase 3 scope. Gated appendix only. Revisit when SEBI posture changes." },
      ]),
      ...space(1),

      decisionTable("Block E \u2014 Hosting and infrastructure", BLUE_LIGHT, [
        { question: "NLP job runner?", answer: "GitHub Actions scheduled workflow (1am IST). Render API server stays on free tier with GH Actions keep-alive ping every 10 minutes on market day hours." },
        { question: "Override log schema?", answer: "signal_override_log table defined in Section 6.4. False positive rate = overrides with final_outcome=incorrect / total auto-triggers. Measured monthly." },
      ]),

      rule(),

      // ── SECTION 10: CONSTRAINTS ───────────────────────────────────────────
      h1("10. Non-Negotiable Constraints (Inherited from PRD v3)"),
      body("These constraints carry forward unchanged into Phase 3. No build decision in PRD 2 relaxes them."),
      ...space(1),
      bullet("No buy, sell, or hold language anywhere in the application. Instruments use only: opportunity signal / headwind signal / watch."),
      bullet("SEBI disclaimer hardcoded on every screen that shows instrument-specific analysis \u2014 persistent footer, never a popup."),
      bullet("MMJ badges on every quantitative claim. MEASURED / MODELLED / JUDGED. Never omitted. Never optional."),
      bullet("Direction and magnitude confidence are always two separate dots with separate labels. Never combined."),
      bullet("Original View is always accessible. Track record is append-only at DB level \u2014 no deletes, no updates."),
      bullet("LLM never generates numbers. Every number in Insight and Context must trace to a specific Evidence layer data point."),
      bullet("Compound Fog of War confidence dampener must never mutate original confidence values in place. Writes to card_confidence_history, not to the events row."),
      bullet("No user financial data stored beyond session \u2014 investment amount, period, risk preference are session-only."),

      rule(),
      body("FinnWise PRD 2 \u2014 Intelligence Architecture Redesign \u2014 " + new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' }), { italics: true, color: SLATE_400 }),
      body("Document status: Final \u2014 supersedes all confidence scoring, de-duplication, LLM validation, Fog of War, and hosting architecture decisions from PRD v3.", { italics: true, color: SLATE_400 }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/claude/finnwise_docs/FinnWise_PRD2_Intelligence_Architecture.docx', buffer);
  console.log('PRD 2 written successfully');
});