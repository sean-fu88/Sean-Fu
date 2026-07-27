# Personal Recipe Database — Implementation Plan

## Goal

A personal cookbook you can open on laptop and phone that stores the **actual recipe content** (ingredients + instructions), not just links. Sources include Instagram posts/reels and website URLs. You can edit quantities/methods for yourself, and (bonus) see step timing relative to a start time, with ingredients tied to steps.

Inspiration: [Just The Recipe](https://www.justtherecipe.com/) — paste a URL → clean ingredients + instructions side by side → save/edit.

---

## Product shape (recommended)

**A mobile-first Progressive Web App (PWA)** with account sync.

| Option | Pros | Cons |
|--------|------|------|
| **PWA (recommended)** | One codebase; installable on phone; works in browser on laptop; Share Target can catch Instagram/web shares | Slightly less native feel; iOS PWA quirks |
| Native apps (iOS/Android) | Best share-sheet UX | Two platforms + backend; heavy for a personal tool |
| Notion / Airtable / Google Sheets | Fast to start | Weak cook-mode UX; poor Instagram import; timing/step linking awkward |
| Local-only (SQLite on device) | Simple, private | Sync across laptop + phone is painful |

**Recommendation:** Build a small authenticated web app (PWA). Treat “native apps” as out of scope unless Share Target on iOS proves insufficient.

---

## User journeys

### 1. Import from a website
1. Paste URL (or Share → app).
2. Server fetches page, extracts Recipe schema (`schema.org/Recipe` / JSON-LD).
3. Show clean cook view: ingredients | instructions.
4. You edit anything wrong, then Save.

### 2. Import from Instagram
Instagram is the hard part. Reels often put the recipe in the caption *or* only in the video/audio.

**MVP path (reliable):**
1. On Instagram: Copy caption (or transcript) → paste into app as text, optionally attach the Instagram URL as source.
2. App (LLM-assisted or rules) parses into title / ingredients / steps.
3. You correct in an editor, then Save.

**Later:**
- Share sheet → open app with Instagram URL.
- Attempt caption fetch where possible (often blocked without login/scraping risk).
- Optional: paste a screenshot → OCR; or upload reel audio → transcription → parse.

Do **not** depend on unofficial Instagram scraping for v1 — it breaks often and can violate ToS.

### 3. Cook mode
- Side-by-side (desktop) or stacked (mobile): ingredients + steps.
- Check off ingredients / steps.
- Optional: set **Start time** → each timed step shows absolute clock time (“Proof until 12:00pm”).
- Optional: highlight ingredients used in the current step.

### 4. Personal modifications
- Edit any field after import.
- Keep `sourceUrl` + optional “Original” snapshot so you can compare or revert.
- Store your tweaks as the canonical recipe you cook from (not a fragile link).

---

## Feature tiers

### MVP (ship first)
- Auth + sync (login on phone and laptop)
- Manual recipe create/edit
- Website URL import via Recipe schema
- Instagram/text paste → structured recipe (LLM parse with editable review)
- Cook view: ingredients + instructions
- Tags / search / basic list
- Persist personal edits

### Phase 2
- Step ↔ ingredient linking
- Per-step duration + start-time schedule
- Servings scaler + unit conversion
- Collections (e.g. “Bread”, “Weeknight”)
- PWA install + Share Target
- Offline read of saved recipes

### Phase 3 (nice-to-have)
- Shopping list from checked/selected recipes
- Image upload / hero photo
- Nutrition (usually skip — noisy)
- Family sharing
- OCR from screenshots; whisper transcription for reels

---

## UX outline

### Screens
1. **Library** — searchable list/grid of recipes (title, tags, source type badge).
2. **Import** — tabs: Website URL | Paste text (IG) | Blank recipe.
3. **Review/Edit** — structured form before save (critical for IG imports).
4. **Cook view** — the Just-The-Recipe moment:
   - Desktop: two columns (ingredients | steps)
   - Mobile: sticky ingredient drawer or split with toggle; large tap targets; keep screen awake option
5. **Schedule bar** (phase 2) — “Start at [time]” → computed finish times per step

### Cook view principles
- No ads, no blog life story, no cards cluttering the hero of the cook screen.
- One job: cook from ingredients + steps.
- Modifications visible as the recipe text itself (not a separate sticky-note dump), with an optional Notes field for freeform tips.

---

## Data model (core)

```text
User
  id, email, ...

Recipe
  id, userId
  title
  description?
  sourceType: website | instagram | manual
  sourceUrl?
  servings?
  prepMinutes?, cookMinutes?, totalMinutes?
  notes?                  // freeform personal notes
  tags[]
  originalSnapshot?       // JSON of first import (optional)
  createdAt, updatedAt

Ingredient
  id, recipeId
  position
  rawText                 // "1/4 cup sugar"
  quantity?               // 0.25
  unit?                   // cup
  item?                   // sugar
  group?                  // "Dough", "Glaze"
  optional: boolean

Step
  id, recipeId
  position
  text
  durationMinutes?        // for schedule
  group?                  // "Day 1", "Bake"

StepIngredient            // phase 2
  stepId, ingredientId
```

**Why structured quantity/unit/item?**  
Needed later for scaling and cleaner editing. MVP can store `rawText` only and parse lazily; structuring on import (especially with LLM) is worth doing early if you care about scaling.

**Modifications:**  
Editing `Ingredient.rawText` / quantities *is* the personalization model. Keep `originalSnapshot` if you want “show original amounts.”

---

## Architecture (recommended stack)

Personal project, one maintainer, laptop + phone:

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js (App Router) + TypeScript | One deployable app; great PWA path; good mobile layout control |
| UI | Tailwind + simple custom components | Fast; avoid overbuilt design systems |
| Auth + DB | Supabase (Auth + Postgres) **or** Clerk + Postgres | Sync across devices with minimal ops |
| Hosting | Vercel | Fits Next.js |
| Import (web) | Server route: fetch HTML → parse JSON-LD Recipe | Same approach Just-The-Recipe-style tools use |
| Import (text/IG) | LLM parse (OpenAI/Anthropic) → JSON schema → review UI | Captions are messy; LLM is the pragmatic parser |
| Files (optional) | Supabase Storage | Photos later |

### Alternative lighter stack
- **Firebase** (Auth + Firestore) + Vite/React PWA — also fine.
- **SQLite + Turso/LibSQL** — good if you want SQL without heavy backend.

**Recommendation:** Next.js + Supabase. Fastest path to authenticated sync.

### High-level flow

```text
Phone/Laptop PWA
    │
    ├─ paste URL ──────────► /api/import/url ──► fetch + JSON-LD parse
    ├─ paste IG caption ───► /api/import/text ─► LLM → structured recipe
    └─ CRUD recipes ───────► Supabase (RLS: user owns rows)
```

---

## Code you would need (work breakdown)

### 1. Project scaffold
- Next.js app under e.g. `recipe-database/app`
- Supabase project, env vars, RLS policies
- Auth pages (magic link or OAuth)

### 2. Database + API
- Migrations for `recipes`, `ingredients`, `steps` (+ join table later)
- Server actions or route handlers for CRUD
- Row Level Security so only your user reads/writes your rows

### 3. Website importer (`/api/import/url`)
- Fetch HTML (handle basic bot blocks; timeout; size limits)
- Extract `application/ld+json` blocks
- Find `@type: Recipe` (or array/`@graph`)
- Map: `name`, `recipeIngredient[]`, `recipeInstructions` (string, HowToStep, or HowToSection), yields, times, image
- Fallback: readable-article extract + LLM structure (phase 2)
- Return draft recipe JSON for the Review screen (do not auto-save)

### 4. Text / Instagram importer (`/api/import/text`)
- Input: caption/transcript + optional source URL
- Prompt model to return strict JSON matching Ingredient/Step schema
- Review UI always required before save

### 5. Editor
- Editable title, tags, ingredients list, steps list
- Add/remove/reorder rows
- Notes field for personal tips
- “Reset to original import” if snapshot exists

### 6. Cook view
- Responsive two-pane layout
- Checkbox state (local or persisted per cook session)
- Phase 2: start time input; `step.absoluteTime = start + sum(previous durations)`
- Phase 2: selecting a step highlights linked ingredients

### 7. Library
- List + search by title/tags
- Filter by source type
- Delete / edit entry points

### 8. PWA (phase 2)
- Manifest, service worker, offline cache for saved recipes
- Android Share Target; iOS: Instructions to use Share → Safari / Add to Home Screen limitations documented

---

## Timing feature (design detail)

For each step with `durationMinutes`:

```text
Start = 08:00
1. Mix dough          (20m)  → 08:00–08:20
2. Bulk ferment       (4h)   → 08:20–12:20
3. Shape              (15m)  → 12:20–12:35
4. Final proof        (1h)   → 12:35–13:35
5. Bake               (35m)  → 13:35–14:10
```

Open product choices:
- Are durations **active work** or **wait time**? (Both — label them, or use `durationMinutes` + `isWaiting`.)
- Parallel steps? (e.g. sauce while pasta boils) — skip in v1; linear timeline only.
- Timezone: use device local time.

---

## Instagram reality check

| Approach | Feasibility | Notes |
|----------|-------------|-------|
| Paste caption manually | ✅ High | Best MVP |
| Share URL into app | ⚠️ Medium | Easy UX; fetching caption server-side is unreliable |
| Official Instagram API | ❌ Poor fit | Not meant for arbitrary personal saves |
| Scrape instagram.com | ⚠️ Fragile / ToS risk | Avoid as core dependency |
| OCR screenshot | ✅ Later | Good for carousel text posts |
| Transcribe reel audio | ✅ Later | Whisper/etc.; then same text parser |

**Plan assumption:** v1 = paste caption/text (+ store IG link as reference). Automate later if painful.

---

## Privacy & cost

- Personal use: single-user or allowlist your email in auth.
- LLM imports: small cost per paste; cache results; never re-parse unless asked.
- Store recipe text in your DB so you never need the original link at cook time (links rot; IG posts disappear).

---

## Suggested build order

1. Auth + empty recipe CRUD + cook view (manual entry only)  
2. Website JSON-LD import + review screen  
3. Text/IG paste import + review screen  
4. Polish mobile cook UX + tags/search  
5. Step durations + start-time schedule  
6. Step–ingredient linking  
7. PWA / offline / share target  

---

## Open questions (please decide)

Reply with choices; recommended defaults are marked ★.

### A. Platform
1. ★ PWA web app (Next.js) synced via cloud  
2. Local-only files (markdown/JSON in git or iCloud) — simpler, weaker phone UX  
3. Start in Notion/Airtable, custom app later  

### B. Account / hosting comfort
1. ★ Supabase + Vercel (free tiers likely enough)  
2. Fully self-hosted (Docker on a VPS)  
3. No cloud account — device sync another way (what?)  

### C. Instagram import for v1
1. ★ Paste caption/text only  
2. Must accept IG URL and auto-extract caption  
3. Also want screenshot OCR in v1  

### D. Personal modifications model
1. ★ Edit the recipe in place; keep optional original snapshot  
2. Explicit “variants” (Original / My version) as separate recipes  
3. Per-ingredient override layer on top of immutable original  

### E. Structured ingredients
1. ★ Store raw line + best-effort qty/unit/item on import  
2. Raw text only until scaling is needed  

### F. Timing / step-ingredients
1. ★ MVP without; phase 2 immediately after cook view feels good  
2. Required in v1  
3. Never needed  

### G. Multi-user
1. ★ Just you (email allowlist)  
2. Household sharing later  
3. Public recipes / social — out of scope unless you say otherwise  

### H. Must-have sources beyond IG + websites?
- TikTok, YouTube description, PDF cookbooks, handwritten photos?

### I. Design preference for cook mode
1. ★ Minimal two-column “just the recipe”  
2. More notebook/scrapbook aesthetic  
3. Match a specific site/app you like (besides JTR)?  

### J. Name?
Working title: **Pantry** / **Mise** / **Recipe Box** / yours?

---

## Decision log

| Date | Decision | Choice |
|------|----------|--------|
| TBD | Platform | |
| TBD | Backend | |
| TBD | IG v1 import | |
| TBD | Mods model | |
| TBD | Timing in MVP? | |

---

## What “done” looks like for v1

You can, from your phone or laptop:
1. Log in.
2. Paste a Serious Eats / Allrecipes-style URL → get ingredients + steps → save.
3. Paste an Instagram caption → get a draft recipe → fix sugar 1/2 → 1/4 → save.
4. Open cook view offline-ish/online and follow the recipe without reopening the source link.

Everything else (schedule, step ingredients, OCR) stacks on that foundation.
