Build a full-stack web application called **PakkaHisaab** — a multimodal AI-powered
financial digitization and reconciliation platform for Indian microbusinesses (kirana
stores, MSMEs). This is a Next.js 14 App Router frontend with TailwindCSS and
Framer Motion used with restraint — motion must convey meaning, never decorate.

> **CHANGELOG vs v1 (why things changed):**
> 1. All colors converted to semantic tokens with a full light/dark theme table — no raw hex in components.
> 2. Contrast fixes: saffron fills now carry ink (near-black) text; white-on-orange uses orange-700. Muted text darkened one step.
> 3. Bilingual typography system added — Devanagari needs its own line-height, size adjustment, and fallback chains (JetBrains Mono has NO Devanagari glyphs; the terminal spec was a shipping bug).
> 4. Animation list rewritten to the "meaningful motion" bar: decorative effects removed or replaced, width/borderColor animations replaced with transforms, hover-only interactions given touch equivalents.
> 5. Per-page UI states (loading / empty / error / success) specified — every async page must define all four.
> 6. Touch targets, focus rings, color-not-alone, and chart accessibility rules made explicit.

---

## DESIGN SYSTEM — SEMANTIC TOKENS (dual theme)
No purple, no blue, no generic AI gradients. The palette is unchanged in spirit —
saffron/forest/turmeric on warm cream — but every color is now a **semantic CSS
variable** defined per theme. Components reference tokens only; raw hex anywhere
in a component file is a lint error.

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--bg` | `#FDF6EC` Warm Cream | `#1C1917` stone-900 | page background — never pure white, never pure black |
| `--surface` | `#FAFAF7` Off-White | `#292524` stone-800 | cards, panels |
| `--surface-raised` | `#FFFFFF` @ 60% over cream | `#33302C` | drawers, modals, sticky headers |
| `--ink` | `#292524` Charcoal | `#FAFAF7` | primary text |
| `--ink-muted` | `#57534E` stone-600 *(was stone-500 — failed 4.5:1 on cream)* | `#A8A29E` stone-400 | secondary text; secondary must still hit ≥3:1 |
| `--border` | `#E7E5E4` Sand | `#44403C` stone-700 | dividers must stay visible in BOTH themes |
| `--brand` | `#F97316` Saffron | `#FB923C` orange-400 | brand fills, accents |
| `--brand-strong` | `#C2410C` orange-700 | `#F97316` | fills that carry white/cream text (4.5:1+), focus rings |
| `--positive` | `#15803D` Forest | `#4ADE80` green-400 | credits, verified, success |
| `--positive-strong` | `#166534` Deep Green | `#22C55E` | success fills w/ white text |
| `--warning` | `#B45309` amber-700 *(was amber-600 — borderline on cream)* | `#FBBF24` amber-400 | pending, cautions |
| `--danger` | `#DC2626` Brick Red | `#F87171` red-400 | debits, errors, risk |
| `--terminal-bg` | `#1C1917` (both themes — the terminal is always dark) | same | AgentTerminal, codex-log |

**Contrast rules (non-negotiable, WCAG AA):**
- Saffron `--brand` fill → text on it is ALWAYS `--ink`-dark (`#1C1917`), never white. (#F97316 + white ≈ 2.8:1 — fails.)
- Any fill carrying white/cream text uses the `-strong` variant (orange-700, green-800, red-600).
- Body text ≥ 4.5:1, secondary text ≥ 3:1, verified in BOTH themes before delivery.
- Modal/drawer scrim: 50% black — strong enough to isolate the foreground in both themes.
- Color is never the only signal: credits show `+` prefix and debits `−` alongside green/red; every exception accent border pairs with a text label; chart series get direct labels or a legend, not color-coding alone.

Dark mode ships as a real theme (toggle in top bar, `class` strategy), not an afterthought:
every component states both values via tokens, and pressed/focus/disabled states are
tested in both themes.

---

## FRAMER MOTION — RESTRAINED, MEANINGFUL MOTION

Install: framer-motion@latest

Global rules before the list:
- Wrap the app in `MotionConfig reducedMotion="user"` — every animation below must
  degrade to opacity-only or none under prefers-reduced-motion.
- Micro-interactions live in 150–300ms. Nothing infinite except the recording
  indicator (it conveys live state).
- Animate transforms and opacity only (x, y, scale, rotate). Never animate `width`,
  `height`, `left`, `top`, or `borderColor` — they trigger layout/paint.
- One orchestrated signature moment per page maximum; everything else stays quiet.
  Scattered effects read as AI-generated.

The revised set (same 10 slots, each now justified or replaced):

1. **Page transitions** — fade + slide up (y: 12 → 0, opacity 0 → 1, 0.3s,
   ease [0.22, 1, 0.36, 1]). *Meaning: spatial continuity between routes.* Reduced
   from y:20/0.4s — subtler is more professional.
2. **AgentTerminal log lines** — opacity 0 → 1 with x: -8 → 0, staggerChildren 0.05s,
   via a container variant + AnimatePresence. *Meaning: conveys real-time streaming —
   this is the demo's hero animation; it earns the motion budget.*
3. **ExceptionCard** — enter with spring (stiffness 260, damping 20); on resolve:
   scale 1 → 0.96 + opacity → 0 via AnimatePresence exit, then `layout="position"`
   on siblings so the list closes the gap smoothly. *Meaning: the problem is leaving.*
4. **EvidencePassport drawer** — slide from right (x: "100%" → 0, spring 300/30)
   inside AnimatePresence with a fading 50% scrim. *Meaning: evidence slides in
   beside the number it proves.* Focus moves into the drawer on open, returns on
   close; Esc closes (escape-route rule).
5. **RiskRadar gauge needle** — useSpring from 0 to score on mount (stiffness 80,
   damping 18), animating SVG `rotate` transform only. *Meaning: the score being
   computed.* Under reduced motion: render at final angle instantly.
6. **Upload zone drag-over** — REPLACED (was infinite borderColor pulse — paint-heavy
   and decorative). Now: on drag-over, background token shifts to orange-50/stone-800
   and the border switches solid → the zone scales 1 → 1.01 once (0.2s). State change,
   not ambient loop. The dashed saffron border is static CSS.
7. **LangToggle (hi/en)** — pill slides with `layoutId="lang-pill"` (kept — layout
   animation is the right tool here, and it's the one shared-layout element on screen).
8. **Ledger table rows** — staggered fade-in ONLY on first load (staggerChildren
   0.03s, y: 6 → 0, `initial={false}` on subsequent data refreshes so refetches don't
   re-animate). *Meaning: the ledger materializing from sources — once.*
9. **Status badges (verified/pending)** — scale pop [1, 1.15, 1] over 0.25s fires
   ONLY on an actual status transition (keyed to status value), never on mount.
   *Meaning: state changed.*
10. **Nav sidebar** — REPLACED (icon rotate on hover was purely decorative). Active
    item now gets a `layoutId="nav-indicator"` saffron rail that slides between items.
    *Meaning: you are here.* Hover/press feedback is an 80–150ms background-token
    shift — stable bounds, no layout jitter.

Additional replacements for former width animations:
- **Confidence bars & upload progress** — `scaleX: 0 → value` with
  `transformOrigin: "left"` (hardware-accelerated), not width.
- **"How is this computed?" expander** — Radix Collapsible with
  AnimatePresence height auto via `motion.div` + `overflow-hidden`; 0.25s; this is
  the one sanctioned height animation because content height is unknown, and it's
  user-initiated.

---

## PAGES & COMPONENTS

Every async page defines FOUR states — loading, empty, error, success — before any
visual polish. Loading = layout-matched skeletons (animate-pulse on `--border`-tone
bars) that reserve final dimensions (CLS < 0.1: no layout shift when data lands).
Empty = an invitation to act, not a mood ("No documents yet — upload a khaata photo
to begin" + primary action), never a blank panel. Error = what went wrong + how to
fix, near the problem, with a retry action; errors don't apologize and are never
vague. Success = the specs below.

### Root Layout (app/layout.tsx)
- `--bg` body background (cream light / stone-900 dark)
- Sidebar: `--terminal-bg`, 64px icon rail. CHANGED: expansion to 220px is triggered
  by click on a pin/expand control (chevron at bottom), with hover-expand as a
  desktop-only enhancement — hover cannot be the sole path (touch devices). Expansion
  animates via the sidebar's own transform/`layout`, and the content area reserves
  space so main content never reflows mid-animation.
- Sidebar icons (lucide only, 24px, consistent 2px stroke, one style — outline —
  across all five): Digitize (upload), Hisaab (ledger), Kavach (shield),
  Evals (chart), Codex Log (terminal). Every icon-only control has an
  `aria-label` and a tooltip on focus/hover. Rail items are 44×44px minimum hit area.
- Top bar: PakkaHisaab wordmark in `--brand` + tagline "Five ways in, one truth out"
  in `--ink-muted`; right side: theme toggle, LangToggle, demo store badge.
- Skip-to-content link as first focusable element.

### app/page.tsx — Landing
- Full-viewport hero on `--bg`: large Hindi heading "अपना हिसाब, पक्का करो"
  (Noto Sans Devanagari, weight 700) with the saffron underline drawing in
  (scaleX 0 → 1, transformOrigin left, 0.6s, once).
- English subtitle below in `--ink-muted`.
- "Open Demo Store" CTA — `--brand` fill with `--ink`-dark text (contrast rule),
  hover: shifts to `--brand-strong` with cream text + scale 1.02; whileTap scale
  0.98; visible focus ring in `--brand-strong`; min height 44px.
- Three feature cards (Digitize / Reconcile / Protect) with `--positive` icon accent,
  whileHover y: -4 + shadow (desktop); on touch, press feedback via background shift.
  Each card's copy says what it does in plain verbs, no selling.
- **The page's single signature moment:** the animated SVG khaata notebook that
  "writes itself" via pathLength (1.2s on mount, once, skipped under reduced motion).
  Because this is the signature, the rest of the landing stays quiet — no other
  entrance animations on this page beyond the underline.

### app/store/[id]/digitize/page.tsx
UploadZone component:
- Dashed `--brand` border card on `--bg` fill, static; drag-over per Motion rule #6.
- Accepts: images, PDFs, CSVs, audio (m4a/webm). The accepted-types list is written
  out in the zone's helper text (don't make users guess).
- After upload: document card with kind badge — each badge is icon + text label
  (khaata = amber, invoice = green, csv = orange, voice = red — color plus word,
  never color alone).
- VoiceRecorder: `--danger` record button (44px+), pulsing ring while recording
  (scale 1 → 1.25, opacity fade, repeat Infinity — sanctioned: it signals "live",
  and reduced-motion swaps it for a static "REC •" label). States: idle / recording /
  processing / done, each visually distinct and announced via aria-live.
- Processing status: skeleton shimmer bars in `--border` tone, dimensions reserved.
- Empty state: "No documents yet — try a khaata photo" + sample-file quick-load
  buttons (demo store).
- Upload errors (wrong type, too large) appear inline under the zone, specific:
  "PDF is 22 MB — the limit is 10 MB."

### app/store/[id]/hisaab/page.tsx (default tab)
Left panel (60%): Ledger table
- Sticky header row: `--terminal-bg` bg, cream text (contrast verified).
- Alternating rows: `--surface` / `--bg`.
- Amount column: `+` prefix + `--positive` for credits, `−` prefix + `--danger`
  for debits (prefix carries the meaning; color reinforces).
- "Verified" badge: `--positive-strong` pill, white text; "Pending" badge:
  `--warning` pill with `--ink`-dark text. Both pills contain the word, 12px
  minimum, sentence case.
- Row click → EvidencePassport drawer (Motion rule #4). Rows are real buttons
  (role, keyboard-activatable, focus-visible ring), not clickable divs.
- "Run Reconciliation" button: `--brand` fill + ink text, full width; during the
  async run it disables, swaps label to "Reconciling…" with an inline spinner, and
  cannot be double-fired. Same name through the flow: the button says
  "Run reconciliation", the success toast says "Reconciliation complete".
- First-load stagger per Motion rule #8; refetches update in place.

Right panel (40%): AgentTerminal (collapsible)
- `--terminal-bg`, ALWAYS dark in both themes.
- **Font stack (bug fix): `"JetBrains Mono", "Noto Sans Devanagari", monospace`.**
  JetBrains Mono contains no Devanagari glyphs — without the explicit fallback,
  Hindi log lines render in an uncontrolled system font. Accept that Devanagari
  segments render proportionally inside the mono layout; align log lines with a
  fixed-width timestamp/level gutter so mixed-script lines still read as a table.
- Log levels: INFO = stone-300, WARN = amber-400, SUCCESS = green-400,
  ERROR = red-400 — AND each line starts with its level word in the gutter
  (color-not-alone rule): `[OK]`, `[WARN]`, `[ERR]`, `[INFO]`.
- Hindi text primary, English in parentheses (or per LangToggle).
- Auto-scroll to bottom; if the user scrolls up, lock and show a "↓ N new" chip
  (44px target) that jumps back down.
- Staggered entry per Motion rule #2.

ExceptionCard (below ledger):
- Card with 4px left border accent PLUS a kind label chip in the header:
  unmatched = amber, duplicate = orange, arithmetic = red, personal = turmeric —
  the chip text ("Unmatched invoice", "Possible duplicate"…) carries the meaning.
- "Resolve" button per card: `--brand` fill + ink text, 44px height, disables with
  spinner during the resolve call.
- Enter/exit per Motion rule #3.
- Empty state (all resolved): a quiet `--positive` check + "All exceptions resolved —
  your hisaab is pakka." (the one place the product voice gets to smile).

EvidencePassport drawer (right):
- Built on Radix Dialog/Drawer for focus trap, Esc-to-close, and scroll lock.
- Header: ledger amount + party name large (`--ink`), date small (`--ink-muted`).
- Source cards stacked: kind badge (icon+word), filename, extracted fields vs ledger
  fields in two columns — match rows get a green check + the word "match",
  divergent rows a red ✕ + the word "differs" (icons never alone).
- Confidence bar: scaleX 0 → value on mount (transformOrigin left);
  >0.8 = `--positive`, 0.5–0.8 = `--warning`, <0.5 = `--danger`, with the numeric
  value printed beside it.
- Model badge: "gpt-4o" or "deterministic_parser" in a stone-700 pill, cream text.
- Match rule in plain language, italic `--ink-muted` — written from the user's side:
  "Matched because the amount and date are identical", not engine jargon.
- Timeline of actions at bottom.

### app/store/[id]/kavach/page.tsx
- RiskRadar gauge: semicircle SVG, needle per Motion rule #5.
  Score zones 0–40 / 40–70 / 70–100 rendered as labeled arc segments
  ("Low / Watch / High") — zone words visible, not color-only. The numeric score
  sits center in display type.
- Recharts bar chart (received vs declared by month): `--brand` (received) and
  `--positive` (declared) with a text legend, axis labels, and tooltips; chart
  container uses ResponsiveContainer + a ResizeObserver-safe wrapper; series also
  distinguishable by label, not hue alone.
- Warning list: each warning as a card with left `--danger` border + a severity word.
- "How is this computed?" collapsible per the sanctioned expander — the formula in
  plain sentences.
- Notice drafter: textarea on `--terminal-bg` with cream text (dark input in both
  themes), labeled visibly ("Paste your GST notice") — label above the field, not
  placeholder-only. "Draft reply" button in `--positive-strong` + white text;
  output in a scrollable markdown card.
- CA disclaimer: `--warning`-toned banner with an alert icon + bold text — pinned
  visible above the draft output at all times, not only inside the draft text.
- Error state (draft fails): inline under the button — "Couldn't draft the reply.
  Your notice text is saved — try again." + retry.

### app/store/[id]/evals/page.tsx
- Accuracy category cards: 4 stat cards with count-up (custom useCountUp driven by
  a Motion value; renders final number instantly under reduced motion).
- Cost-vs-accuracy scatter: Recharts ScatterChart, dots in brand/positive/warning
  tokens, each series named in a legend and dot tooltips carrying the case id.
- Headline stat: "−X% cost vs all-GPT-4o" as a large `--brand` display number with
  its explanatory sentence in body type beside it (a big number never floats alone).
- Per-case accordion: pass = green + "Pass", fail = red + "Fail",
  partial = amber + "Partial" — word + color, chevron affordance on each row.

### app/codex-log/page.tsx
- Renders docs/codex-log.md as formatted markdown.
- `--terminal-bg` bg, cream text — terminal aesthetic; same Devanagari-safe mono
  stack as AgentTerminal.
- Single fade-in for the page (no per-section stagger — reading surface, keep still).

---

## COMPONENT SPECS

### AgentTerminal.tsx
- Fixed bottom-right launcher button (terminal icon, `--terminal-bg` bg, `--brand`
  icon, 48×48px, aria-label "Open agent terminal").
- Click → slide-up panel (y: "100%" → 0 in AnimatePresence, spring 300/30).
- Connect to WS /ws/stores/{id}/agent-log; reconnect with exponential backoff and
  a visible connection-state chip ("Reconnecting…" in amber) — never fail silently.
- Props: storeId, lang.

### LangToggle.tsx
- Two options: "हिं" and "EN" — each option a 44px-min target.
- Animated pill via `layoutId="lang-pill"` (`--brand` fill, ink text).
- State in React + URL param ?lang=hi|en. No localStorage.
- The control is a proper radiogroup with keyboard arrow support.

### UploadZone.tsx
- react-dropzone + manual file input fallback (the button is the primary affordance;
  drag is the enhancement — never drag-only).
- Kind-aware lucide icon (camera / file / table / mic), one stroke style.
- Progress: scaleX bar, value announced via aria-live polite.

### VoiceRecorder.tsx
- MediaRecorder API → webm → POST /uploads?kind=voice_note.
- States: idle / recording / processing / done; recording state shows elapsed time
  text alongside the pulsing ring (time = the accessible signal).
- Mic-permission-denied error: instructive, not apologetic — "Microphone access is
  blocked. Enable it in your browser's site settings, then try again."

---

## API INTEGRATION (connect after build)
Backend: Python FastAPI on Render
Base URL: env NEXT_PUBLIC_API_URL · WebSocket: env NEXT_PUBLIC_WS_URL

Endpoints (all defined — connect post-build):
- POST /api/stores/demo
- POST /api/stores/{id}/uploads
- WS   /ws/stores/{id}/agent-log
- POST /api/stores/{id}/reconcile
- GET  /api/stores/{id}/ledger
- GET  /api/stores/{id}/exceptions
- POST /api/exceptions/{id}/resolve
- GET  /api/ledger-entries/{id}/evidence
- POST /api/stores/{id}/query
- GET  /api/stores/{id}/risk
- POST /api/stores/{id}/notices
- GET  /api/stores/{id}/export?fmt=csv|pdf
- GET  /api/evals/run
- GET  /api/model-usage

All fetch calls typed with zod schemas; error boundaries per page; layout-matched
loading skeletons during fetch (per the four-state rule); toast notifications via
sonner using semantic tokens (success = positive-strong, error = danger,
info = brand) — toasts name the action they confirm with the same verb the button
used ("Reconciliation complete", "Reply drafted").

---

## i18n (lib/i18n.ts)
All UI strings in {en, hi}:
export const t = {
  upload: { en: "Upload documents", hi: "दस्तावेज़ अपलोड करें" },
  reconcile: { en: "Run reconciliation", hi: "मिलान चलाएं" },
  // ...every string — including every empty-state, error, aria-label, and toast.
}
Default lang: "hi" for demo store. Sentence case in English. An action keeps the
same name across button → toast → log line in both languages.

---

## TYPOGRAPHY — BILINGUAL SYSTEM
- **Fallback chains everywhere (this is the core bilingual rule):**
  - Body/UI: `Inter, "Noto Sans Devanagari", system-ui, sans-serif`
  - Display: `"Fraunces", "Noto Serif Devanagari", serif` (characterful serif for
    the hero + big stats only — used with restraint; body never uses it)
  - Mono: `"JetBrains Mono", "Noto Sans Devanagari", monospace`
  Load Noto Sans/Serif Devanagari from Google Fonts with `font-display: swap` and
  subset `devanagari`.
- **Devanagari sizing:** Devanagari has taller vertical metrics (matras above/below
  the headline) — set `line-height: 1.7` for Hindi-primary blocks (vs 1.5 English)
  or clipped matras will make text look broken. Hindi body renders visually smaller
  at equal px: when lang=hi, bump body one step (16 → 17px via a `[lang="hi"]`
  rule or size-adjust in @font-face).
- Set `lang="hi"` / `lang="en"` on the html element per toggle (screen readers pick
  the right voice; browsers pick correct font shaping).
- Scale: 12 / 14 / 16 / 20 / 24 / 32 / 48px — 12px is captions/labels ONLY, never
  body; body minimum 16px (17px Hindi); line length for long-form text capped
  ~70ch.
- Headings sequential h1→h6, no level skipped; letter-spacing tight on display
  sizes only, never on Devanagari (tight tracking breaks conjunct legibility).

---

## PACKAGE LIST
next@14, react, framer-motion, tailwindcss,
recharts, react-dropzone, sonner (toasts),
zod (API validation), swr (data fetching),
@radix-ui/react-dialog (EvidencePassport drawer base — focus trap + Esc for free),
@radix-ui/react-collapsible (expanders),
lucide-react (icons — the ONLY icon source; no emoji as icons anywhere)

---

## QUALITY BAR
- No layout shift on page load (skeletons reserve final dimensions; CLS < 0.1)
- All interactive elements: visible :focus-visible ring in `--brand-strong`
  (2px ring + 2px offset — orange-700 passes the 3:1 non-text contrast bar on cream;
  raw saffron does not)
- Touch targets ≥ 44×44px with ≥ 8px spacing between adjacent targets
- Mobile-responsive: sidebar collapses to bottom nav on <768px (exactly the 5 items —
  at the bottom-nav ceiling, add nothing more); bottom nav respects safe-area-inset
- Recharts charts resize via ResponsiveContainer; no horizontal page scroll at any
  breakpoint; viewport meta present, zoom never disabled
- Every Framer animation respects prefers-reduced-motion (MotionConfig
  reducedMotion="user" + the per-animation fallbacks specified above)
- Both themes tested before delivery — text, borders, and interaction states
  verified in light AND dark, not inferred from one
- Icon-only buttons all carry aria-labels; images meaningful to content carry alt
  text; tab order matches visual order; drawer focus is trapped and returned
- TypeScript strict mode, no `any` types
- Error boundaries on every async page; all four UI states implemented per page