# Decisions

Architecture Decision Records (ADRs) for `wc2026prediction`. Each record explains a key technical choice, the context around it, the alternatives we considered, and the reasons for the decision.

ADRs are written once and not updated — they capture thinking at a point in time. If a decision is reversed, a new ADR is added rather than editing the old one.

---

## ADR-001 — JSON files instead of a database

**Date:** 2026-06-01  
**Status:** Accepted

### Context

The system needs to store team ratings, match results, and win probabilities between pipeline runs. A storage layer is required.

### Decision

Use plain JSON files (`data/teams.json`, `data/bracket.json`, `data/predictions.json`) as the storage layer.

### Alternatives considered

| Option | Rejected reason |
|---|---|
| SQLite | Requires schema management, migrations, and a DB client. Overkill for three flat objects. |
| Supabase / Firebase | Requires an account, project setup, API keys, network dependency, and monthly cost past free limits. Adds operational complexity with no benefit for a project this size. |
| PostgreSQL | Massively over-engineered. |

### Reasoning

- The data is small (three files, under 100 KB total)
- The write pattern is simple: once per round, the whole file is overwritten
- JSON files are human-readable — you can inspect `predictions.json` directly
- JSON files are Git-versionable — every round's state is in version history automatically
- No setup required — works on any machine with Python installed

### Consequences

- No concurrent writes (fine — there is only one writer: `update.py`)
- No query language (fine — we load the full file into memory; it's tiny)
- Must be careful not to corrupt JSON mid-write (mitigated by writing to a temp file and atomically renaming)

---

## ADR-002 — Elo as the base team rating

**Date:** 2026-06-01  
**Status:** Accepted

### Context

We need a baseline strength measure for each team that can be updated after each match and used to calculate win probabilities.

### Decision

Use the Elo rating system, seeded from [World Football Elo Ratings](https://www.eloratings.net/), updated in-place as the tournament progresses.

### Alternatives considered

| Option | Rejected reason |
|---|---|
| FIFA ranking points | Not designed for win probability calculation. Rankings reflect cumulative points, not head-to-head probability. |
| FiveThirtyEight SPI (Soccer Power Index) | SPI is not publicly available for calculation — only the output scores are published. We cannot update it ourselves. |
| Pure betting odds | Strong signal but can be biased toward big-name teams. Better as a supplementary signal than a base. |
| Custom trained ML model | Requires large historical dataset, training pipeline, and ongoing maintenance. Elo achieves similar accuracy with no infrastructure. |

### Reasoning

- Elo is mathematically sound and well-understood
- The win probability formula is simple and interpretable
- Can be updated with a single formula after each match
- The [World Football Elo](https://www.eloratings.net/) dataset gives reliable starting values
- Well-documented and widely used in sports prediction

---

## ADR-003 — Manual update trigger instead of automation

**Date:** 2026-06-01  
**Status:** Accepted

### Context

The pipeline needs to run after each round completes. We could automate this with a cron job (GitHub Actions) or keep it manual.

### Decision

Manual trigger only: `python update.py` run by the developer after confirming all round results are in.

### Alternatives considered

| Option | Rejected reason |
|---|---|
| GitHub Actions cron (e.g., run every 6 hours) | Wastes API calls on rounds not yet complete. Runs when all results may not be in. Requires extra logic to detect round completion. |
| Webhook from API-Football (when match ends) | API-Football webhooks require a paid plan. |
| Fully automated nightly run | Same problem as cron — round boundaries don't align neatly with midnight. |

### Reasoning

- The WC 2026 knockout stage has one round every 3–4 days. Manual trigger is not burdensome.
- Manual trigger guarantees we only update when data is complete and verified.
- Simpler codebase — no CI secrets to manage, no scheduled workflow to debug.
- Easy to upgrade later: the entire pipeline is one function call in `update.py`, so wrapping it in a GitHub Actions workflow is trivial if desired.

---

## ADR-004 — GitHub Pages for hosting

**Date:** 2026-06-01  
**Status:** Accepted

### Context

The prediction dashboard needs to be publicly accessible. A hosting solution is required.

### Decision

Host the static dashboard on GitHub Pages, served from the `/web` folder of the `main` branch.

### Alternatives considered

| Option | Rejected reason |
|---|---|
| Vercel | Free tier is generous but requires account setup, project linking, and Vercel-specific config. More steps than necessary. |
| Netlify | Similar to Vercel. Overkill for a single HTML file. |
| Render / Railway | Require a running process. We have no backend. |
| Self-hosted VPS | Operational cost and maintenance. Unnecessary for a static file. |

### Reasoning

- GitHub Pages is built into GitHub — zero additional accounts or config
- Automatically rebuilds on every push to `main`
- Free, permanently, with no usage caps for a static site
- The site is a single HTML file — GitHub Pages is perfectly suited
- The URL is predictable: `yourusername.github.io/wc2026prediction/web/`

---

## ADR-005 — Monte Carlo simulation over analytical probability

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Given team strength scores, we need to convert them into tournament win probabilities. Two approaches exist: analytical calculation (multiply path probabilities) and Monte Carlo simulation (random sampling).

### Decision

Use Monte Carlo simulation with N = 10,000 iterations.

### Alternatives considered

| Option | Notes |
|---|---|
| Analytical probability | Exact, but becomes complex when accounting for the bracket structure (different paths to the final, variable opponents). The math works out to 6+ nested loops and is harder to read and extend. |
| Monte Carlo | Slightly less precise (sampling error ~0.4pp at N=10,000) but far simpler code, easy to extend (add penalty shootout randomness, extra time, etc.), and finishes in <1 second. |

### Reasoning

- At N=10,000, the error is ~0.4 percentage points — negligible for our use case
- The simulation code is easy to read and reason about
- Adding new match outcome complexity (penalties, extra time luck) requires only local changes to `simulate_match()`, not a rearchitected formula
- Runs in under 1 second on any modern laptop

---

## ADR-006 — Five signals combined with fixed weights

**Date:** 2026-06-01  
**Status:** Accepted

### Context

Multiple data signals are available (Elo, xG, squad value, odds, injuries). We need a way to combine them.

### Decision

Weighted linear combination with fixed weights defined in `config.py`. Weights: Elo 0.35, xG 0.30, squad value 0.15, betting odds 0.20. Injury as a multiplicative modifier.

### Alternatives considered

| Option | Notes |
|---|---|
| ML regression to learn weights | Requires historical labeled data and a training pipeline. The gain in accuracy for a 7-round tournament is marginal. |
| Equal weights | Simpler but ignores known differences in signal quality. Elo is a stronger long-term signal than squad value. |
| Single signal (Elo only) | Much faster to build but significantly less accurate, especially mid-tournament when recent form diverges from historical ratings. |

### Reasoning

- Fixed weights are transparent — you can reason about why the model gives a team a certain probability
- Weights are empirically informed by research on football prediction models
- Easy to tune in `config.py` without touching any model logic
- Starting simple with the option to move to a learned weighting later is lower risk
