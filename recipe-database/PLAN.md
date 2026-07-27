# Recipe Nook — Implementation Plan

Personal cookbook for laptop + phone. Store the **actual recipe** (ingredients + instructions), not just links. Import from websites, Instagram, Facebook, and YouTube. Edit in place with version history. Simple Just-The-Recipe–style cook view.

---

## Locked decisions (2026-07-27)

| Topic | Choice |
|-------|--------|
| Name | **Recipe Nook** |
| Budget | **Free** ($0 recurring; free-tier services only) |
| Users | Just you (email allowlist) |
| Ingredients | Structured: `rawText` + qty / unit / item |
| Modifications | Edit in place **+ version history** (not just one snapshot) |
| UI | Simple two-column cook view |
| Sources (v1+) | Websites, Instagram, Facebook, YouTube |
| Platform / hosting | **Still open — see discussion below** |

---

## What “F” meant (timing + step-ingredients)

Two **optional cook-mode helpers**, independent of import:

### 1. Start-time schedule
You optionally add a duration on each step (e.g. “bulk ferment — 4 hours”). When cooking, you tap **Start at 8:00am** and the app shows clock times:

```text
1. Mix dough       20m   8:00 – 8:20
2. Bulk ferment     4h   8:20 – 12:20
3. Shape           15m  12:20 – 12:35
4. Bake            35m  12:35 – 13:10
```

### 2. Ingredients per step
Link “butter”, “flour” to step 1 so the current step highlights only what you need now.

**Neither is required for a useful v1.** Both need a bit of extra data entry (or smart defaults). Recommendation: ship cook view first; add these once importing/editing feels good. Say if you want them in v1 anyway.

---

## Free platform & hosting — discussion

Constraint: **$0/month**. That rules out paid VPS-by-default and makes “LLM on every import” something we must design carefully (free API quotas or no LLM).

### What you need from a stack

1. **UI** that works on phone + laptop  
2. **Database** that syncs both devices  
3. **Login** so only you see recipes  
4. **Server-side fetch** for website HTML (browsers can’t reliably scrape arbitrary sites due to CORS)  
5. Optional: a **free** way to turn messy captions into structured recipes  

### Options compared

| Stack | Cost | Sync phone/laptop | Caveat for a personal cookbook |
|-------|------|-------------------|--------------------------------|
| **A. Cloudflare Pages + Workers + D1** | Free | Yes | Slightly more DIY auth; excellent free limits; **no inactivity pause** |
| **B. Vercel Hobby + Supabase Free** | Free | Yes | Easiest DX; **Supabase pauses after ~7 days low activity** (one-click restore) |
| **C. Firebase Spark (Auth + Firestore) + Firebase Hosting** | Free | Yes | Very generous free tier; NoSQL model; Google account ecosystem |
| **D. Local-first PWA (SQLite/OPFS) + optional sync later** | Free | Weak until sync added | Fastest “works on one device”; phone↔laptop sync is the hard part |
| **E. Self-host PocketBase/SQLite on free Oracle/Fly** | Free* | Yes | Free compute is flaky / card-on-file / sleep policies; more ops |

\*“Free” VPS tiers often need a credit card, sleep on idle, or disappear.

### Recommendation for Recipe Nook

**Prefer A (Cloudflare) or B (Vercel + Supabase).**

- Choose **B** if you want the smoothest path to auth + Postgres and accept occasional pause/restore when you haven’t cooked in a week.  
- Choose **A** if “always free and doesn’t pause” matters more than polished auth DX.  
- **C** is a strong third if you already live in Google’s world.  
- Avoid **E** unless you enjoy server babysitting.  
- **D** only if you’re OK starting phone-only or laptop-only, then adding sync.

**Still need your pick: A, B, or C?** (Or “you choose — optimize for least maintenance.”)

### Free LLM / parsing (applies to any stack)

Caption → structured recipe is nicer with an LLM, but paid OpenAI keys break the “free” rule if used heavily.

Practical free approaches:

1. **Heuristic + manual edit (always free)** — split lines, detect quantities with regex, you fix in the review UI. Good enough for many captions.  
2. **Free model APIs** — e.g. Google Gemini free tier / Groq free tier for parse-on-import, with hard rate limits and a fallback to heuristics if the key is missing.  
3. **No cloud LLM** — paste text, structure by hand in the editor (slowest UX, zero API dependency).

**Recommendation:** Heuristic parser always available; optional Gemini free-tier assist when configured. Website JSON-LD import needs **no** LLM.

---

## Automatic Instagram extract — effort

| Level | What you get | Effort | Reliability | Free? |
|-------|--------------|--------|-------------|-------|
| **L0 Paste caption** | You copy text from IG → app parses | Low | High | Yes |
| **L1 Paste URL, try fetch** | App requests `instagram.com/p/...` and looks for caption in HTML/meta | Medium | **Low–medium** — IG often login-walls or returns empty shells to servers | Yes (no API fees) but breaks often |
| **L2 Unofficial scrape / 3rd-party embed APIs** | Caption via scrapers or oEmbed-like services | Medium–high | Medium; **breaks when IG changes**; ToS grey area | Sometimes free, often rate-limited |
| **L3 Official Meta APIs** | Only works for accounts/content you formally have API access to | High setup | Not designed for “save any reel I liked” | Dev app free, but wrong product fit |
| **L4 Screenshot OCR** | You share a screenshot → OCR → same text parser | Medium | High for text-on-image carousels | Free OCR libs or free vision API tiers |
| **L5 Reel audio transcription** | Download/upload audio → Whisper → parse | High | Good when recipe is spoken | Local Whisper = free/slow; cloud = usually paid |

**Bottom line:**  
Fully automatic “paste IG link → perfect recipe” is **disproportionate effort for unreliable results**. The caption is often not even in the HTML a server can see.

**Sensible plan:**
- **v1:** L0 paste caption (+ store the IG URL as `sourceUrl`).  
- **v1.5 if you hate copying:** L4 screenshot share (especially Stories/carousels).  
- **Experiment:** L1 best-effort URL fetch that falls back to “paste the caption” when it fails — small code, no promises.

Same story for **Facebook** posts (login walls). **YouTube** is easier: video description is usually fetchable; chapters/comments vary. Spoken-only recipes still need transcript (YouTube captions API or paste).

---

## Sources

| Source | v1 approach | Notes |
|--------|-------------|-------|
| **Websites** | URL → JSON-LD `Recipe` | Highest value; Just-The-Recipe pattern |
| **Instagram** | Paste caption (+ optional URL) | Auto-URL extract is best-effort only |
| **Facebook** | Paste post text (+ optional URL) | Same parser as IG |
| **YouTube** | URL → fetch description (and captions if available) | Fallback: paste description |

All paths land on the same Review/Edit screen → Save.

---

## Version history (edit in place)

Not just one “original snapshot.” Every save can create a version:

```text
Recipe (current canonical row you cook from)
RecipeVersion
  id, recipeId
  versionNumber
  createdAt
  label?              // "Imported", "Halved sugar", "After first bake"
  snapshot JSON       // full title + ingredients + steps + notes at that moment
```

UX:
- Edit freely; each Save appends a version (or debounce: version on explicit “Save version” / every Nth save — **decide later**).  
- History panel: browse past versions, diff summary, **Restore** (writes a new version; doesn’t destroy history).  
- Import creates version 1 labeled “Imported”.

---

## Data model (updated)

```text
Recipe
  id, userId
  title
  sourceType: website | instagram | facebook | youtube | manual
  sourceUrl?
  servings?
  prepMinutes?, cookMinutes?, totalMinutes?
  notes?
  tags[]
  createdAt, updatedAt

Ingredient
  id, recipeId, position
  rawText                 // "1/4 cup sugar"
  quantity?               // 0.25
  unit?                   // cup
  item?                   // sugar
  group?                  // "Dough", "Glaze"
  optional: boolean

Step
  id, recipeId, position
  text
  durationMinutes?        // for schedule (phase 2)
  group?

RecipeVersion
  id, recipeId, versionNumber, createdAt, label?, snapshot

StepIngredient            // phase 2
  stepId, ingredientId
```

---

## Architecture (pending hosting pick)

Once you choose A / B / C:

| Concern | Approach |
|---------|----------|
| App | TypeScript web app (Next.js **or** Vite+React on Cloudflare — depends on host) |
| UI | Simple, mobile-first; ingredients \| steps |
| Auth | Magic link or Google OAuth; allowlist your email |
| Import web | Server/edge function: fetch HTML → JSON-LD |
| Import social text | Heuristics (+ optional free Gemini) → structured draft |
| History | `RecipeVersion` rows on save |

### High-level flow

```text
Phone / laptop
  ├─ website URL ──► import/url ──► JSON-LD ──► Review ──► Save (+ version)
  ├─ paste text ───► import/text ─► parse ────► Review ──► Save (+ version)
  ├─ YouTube URL ──► import/youtube ► description ► Review ──► Save
  └─ cook / edit ──► DB (your user only)
```

---

## MVP scope

- Auth (solo allowlist)  
- Library: search / tags  
- Manual create + edit with **structured ingredients**  
- **Version history** on save + restore  
- Website URL import  
- Paste-text import (IG / Facebook / generic)  
- YouTube description import (best-effort)  
- Simple cook view (ingredients + steps)  

### Phase 2
- Start-time schedule + step durations  
- Step ↔ ingredient links  
- PWA install / offline  
- Best-effort social URL fetch + screenshot OCR  

### Out of scope for free v1
- Paid LLM dependency as a hard requirement  
- Reliable automatic Instagram scraping  
- Multi-user / household sharing  

---

## Build order

1. Scaffold + auth + recipe CRUD + structured ingredients editor  
2. Cook view (simple two-pane)  
3. Version history  
4. Website JSON-LD import  
5. Paste-text parser (IG/FB)  
6. YouTube description import  
7. Phase 2 extras  

---

## Remaining open questions

1. **Hosting:** A Cloudflare / B Vercel+Supabase / C Firebase / “pick least maintenance”?  
2. **Parse assist:** Heuristics only, or optional free Gemini key when available?  
3. **Feature F:** Phase 2 (recommended), or want schedule / step-ingredients in v1?  
4. **Versioning cadence:** New version on every save, or explicit “Save version” button?  
5. **Auth preference:** Magic link email, or “Sign in with Google”?  

---

## What “done” looks like for v1

From phone or laptop, for $0:
1. Sign in as you.  
2. Paste a recipe website URL → ingredients + steps → save.  
3. Paste an IG/FB caption → structured draft → change 1/2 cup sugar to 1/4 → save (history kept).  
4. Open cook view and cook without reopening the original post.
