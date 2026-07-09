# Proving Instant AI Pavement Takeoff

PaveBench exists to answer one question with evidence instead of marketing: **can
an AI system produce an accurate pavement takeoff instantly, with no human in the
loop?** This document defines what "instant" and "accurate" mean here, what a
system must do to earn the **INSTANT badge**, why nobody in the market can
currently claim it, and the roadmap from one case to a publishable benchmark.

## The claim, and why it needs proof

The paving-takeoff market sells "AI measurement" but discloses no real accuracy
numbers and, with one exception, is not instant:

- **Attentive.ai / Beam AI** — the dominant incumbent ($48M raised, $30.5M
  Series B Nov 2025, 1,100+ companies). Aerial takeoffs turn around in **6-48 h**,
  blueprint takeoffs **24-72 h**, and their own product pages state **every
  takeoff is reviewed by a QA team** even while headlines say "100% automated."
- **SiteRecon** — "AI measurements in 10-15 minutes" for simple lots, plus a
  **24-48 h** expert-assist tier for complex jobs.
- **TruTec** — the lone vendor claiming genuine instant, no-human delivery
  ("under 60 seconds," "5 seconds" in a demo), but a small/opaque player with
  **no published accuracy numbers, no methodology, no third-party reviews**.

Across the entire market, **nobody publishes IoU, precision/recall, or a method.**
Accuracy is round-number marketing ("95%+", "98%+"). So "instant, verified-accurate,
self-serve" is not a settled capability — it is an unproven claim. A neutral,
reproducible benchmark that measures latency and accuracy together is therefore
itself the credibility asset. (Sources: research report `06-competitors.md`.)

## Latency is a first-class metric

Every prediction carries `latencyMs` (wall-clock) and `costUsd`. PaveBench
aggregates p50/p95 latency per system and assigns a **latency class**:

| Class | p95 wall-clock | Who lives here |
|-------|----------------|----------------|
| **INSTANT** | <= 10 s | the claim under test |
| **FAST** | <= 60 s | TruTec's "under 60s"; single Gemini calls |
| **BATCH** | > 60 s | Attentive.ai, SiteRecon (minutes to 72 h) |

p95 (not mean) is used so a system cannot hide a slow tail behind fast median cases.

## The INSTANT badge — all gates must hold

A system earns the INSTANT badge only when **every** condition below is met. The
conjunction is the point: fast-but-wrong, accurate-but-slow, and
human-in-the-loop systems all fail it.

1. **Latency class INSTANT** — p95 <= 10 s.
2. **Automation declared `full_auto`** — no human in the loop. Automation is a
   declared field in the run manifest (`full_auto` / `assisted` / `human_in_loop`
   / `oracle`), mirroring the `hybrid_production` track's declared-aids concept.
   `assisted` (cleaned imagery, user boxes, parcel vectors, ensembles) and
   `human_in_loop` (QA review, manual correction) never earn the badge.
3. **Accuracy floor across a real gold set** — pass rate **>= 90%** over
   **>= 20 `reviewed_gold` cases** spanning **>= 2 GSD tiers**. A case passes when
   IoU >= 0.86, area (sqft) delta <= 8%, cutout count within 2, and the target
   click is contained (see `pavebench/eval.py`).

These thresholds are constants in `pavebench/leaderboard.py`
(`INSTANT_MIN_CASES`, `INSTANT_MIN_GSD_TIERS`, `INSTANT_MIN_PASS_RATE`) and
`pavebench/reporting.py` (`LATENCY_INSTANT_MS`). Today, with one `needs_gold_review`
case, **no system can earn the badge** — which is the honest current state.

## Accuracy is reported per GSD tier, not as one number

Method rankings **flip** across imagery resolution (research exp-C/E): tiled VLM
counting wins on <= 10 cm/px imagery and is the *worst* choice at z19; the classical
stripe fitter wins on empty lots but only where stripes are physically resolvable.
So every case declares its imagery (`source`, native GSD, vintage, license) and
every report segments results into GSD tiers:

| Tier | Native GSD | Note |
|------|-----------|------|
| `<=8cm` | <= 8 cm/px | Nearmap-class, county ortho at full res — stripe-grade |
| `8-15cm` | 8-15 cm/px | usable for area, marginal for stalls |
| `>15cm` | > 15 cm/px | Esri z19, 6-inch county ortho — area-only, "estimate" for stalls |

A system that only clears the accuracy floor on easy `<=8cm` lots has not proven
instant takeoff; the `>= 2 GSD tiers` gate forces breadth. Honesty rule: the tier
is set from the imagery's **native** resolution, not an upsampled export GSD, so a
lot exported at 6 cm/px from 15 cm/px source imagery is still tiered `>15cm`.

## Tasks measured

- **Paved-area takeoff** (`click_connected_polygon`, `semantic_mask`) — IoU, sqft
  delta (median + p90 across cases), and **area-weighted cutout recovery**
  (found/expected, weighted by island area — the single weakest link found across
  every method in the research: islands go undetected).
- **Stall counting** (`stall_count`) — count error %, and where per-stall geometry
  and gold markers exist, **per-stall precision/recall at a 2.7 m match radius plus
  median location error**. This methodology was validated on a real marker-labeled
  lot (St Paul): 88% of fitted stalls within one stall-width, median 1.27 m
  (research exp-E).

## Anti-overfit: public-dev vs private-test split

A public benchmark that is also a marketing asset must resist overfitting.

- **Public dev split** (`split: dev`) — cases in this repo, imagery included, for
  iteration. Anyone can score against them.
- **Private test split** (`split: test`) — hold-out cases that live **outside** the
  repo (`dataset/private/`, gitignored). They are scored by pointing the same
  `score-manifest` command at a private manifest whose `metadataPath`s reference
  the external case files. Published INSTANT-badge numbers must come from the
  private test split so the leaderboard reflects generalization, not memorization.

The harness needs no special mode for this — a manifest is just a list of case
paths, so a private manifest outside the repo works today.

## Roadmap: 1 case -> publishable v1

**Where we are:** one real-imagery case (`pb_us_il_justice_testa_001`, Cook County
2025 public-domain ortho), `needs_gold_review`, `>15cm` tier. It proves the whole
pipeline runs on legal, reproducible imagery — but one guide case proves nothing
about a system.

**To a publishable v1 (target ~50-100 cases):**

1. **Reviewed gold, not guides.** Each ingested ProPaving trace lands
   `needs_gold_review`; a reviewer must check the ~2-3 m georegistration offset
   (Google-traced geometry vs. the ortho) and adjust or re-trace before marking
   `reviewed_gold`. Only reviewed-gold cases count toward the badge.
2. **>= 20 cases across >= 2 GSD tiers** to unlock badge eligibility; ~50-100 for a
   credible public claim.
3. **Regional + source diversity** — multiple county/state ortho programs (Cook,
   Ramsey, and the ~10-15 states with public ortho), plus USGS NAIP, so results
   are not one-vendor artifacts.
4. **Difficulty tiers** — vary cutout density (landscape islands), occupancy
   (empty/occupied for stalls), and lot complexity (simple rectangle vs. curved
   single-loaded rows vs. dense urban), because that is where methods diverge.
5. **Private test hold-out** carved from the same distribution for the headline
   numbers.

When a `full_auto` system clears the accuracy floor on that set within the INSTANT
latency class, the badge is earned — and it will be the first such claim backed by
a published, reproducible method rather than a marketing page.
