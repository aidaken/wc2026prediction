# Setup

Full walkthrough from cloning the repo to having a live dashboard on GitHub Pages.

---

## Prerequisites

- Python 3.10 or higher — check with `python --version`
- Git — check with `git --version`
- A GitHub account
- A free API-Football account (takes 2 minutes to create)

---

## Step 1 — Fork and clone

Fork this repo on GitHub first (so you can push to your own copy), then clone:

```bash
git clone https://github.com/YOUR_USERNAME/wc2026prediction.git
cd wc2026prediction
```

---

## Step 2 — Python environment

Always use a virtual environment. This keeps project dependencies isolated from your system Python.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows (cmd)
venv\Scripts\Activate.ps1         # Windows (PowerShell)

# You should see (venv) at the start of your terminal prompt

# Install dependencies
pip install -r requirements.txt
```

To deactivate the virtual environment when you're done:
```bash
deactivate
```

---

## Step 3 — Get API keys

### API-Football (required)

1. Go to [api-football.com](https://www.api-football.com/)
2. Click "Sign Up Free" — no credit card needed
3. After signup, go to your dashboard and copy your API key
4. Free tier: **500 requests/day** — plenty for this project (~20 per update)

### The Odds API (optional but recommended)

1. Go to [the-odds-api.com](https://the-odds-api.com/)
2. Click "Get API Key" — no credit card needed
3. Copy your API key
4. Free tier: **500 requests/month** — we use ~6 per month

---

## Step 4 — Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in your keys:

```env
API_FOOTBALL_KEY=your_actual_key_here
ODDS_API_KEY=your_actual_key_here
```

**Never commit `.env` to Git.** It is already listed in `.gitignore`. If you accidentally commit it, rotate your API keys immediately.

---

## Step 5 — First run

```bash
python update.py
```

The first run does more work than subsequent runs:
- Fetches all group stage results (to seed Elo ratings and xG form)
- Builds `data/teams.json` with initial values for all 32 teams
- Fetches squad values from Transfermarkt (may take 30–40 seconds due to throttling)
- Fetches current betting odds
- Runs the first Monte Carlo simulation
- Writes `data/predictions.json`

You should see output like:

```
[INFO]  2026-06-30 20:00:01 | Fetching Round of 32 fixtures...
[INFO]  2026-06-30 20:00:03 | Fetched 32 fixtures (28 completed, 4 upcoming)
[INFO]  2026-06-30 20:00:05 | Fetching player stats for 32 teams...
[INFO]  2026-06-30 20:00:18 | Fetching squad values from Transfermarkt...
[INFO]  2026-06-30 20:00:52 | Fetching betting odds...
[INFO]  2026-06-30 20:00:53 | Updating Elo ratings...
[INFO]  2026-06-30 20:00:53 | Calculating xG form ratios...
[INFO]  2026-06-30 20:00:53 | Calculating injury multipliers...
[INFO]  2026-06-30 20:00:53 | Running 10,000 Monte Carlo simulations...
[INFO]  2026-06-30 20:00:54 | Simulation complete.
[INFO]  2026-06-30 20:00:54 | Writing data/teams.json
[INFO]  2026-06-30 20:00:54 | Writing data/bracket.json
[INFO]  2026-06-30 20:00:54 | Writing data/predictions.json
[INFO]  2026-06-30 20:00:54 | Done. Top prediction: Brazil 18.4%
```

---

## Step 6 — Preview the dashboard locally

Open `web/index.html` directly in your browser. Because it fetches `predictions.json` via the Fetch API, you may need to serve it over HTTP (browsers block local file fetches):

```bash
# Easiest option — Python's built-in server
python -m http.server 8000 --directory web
# Then open http://localhost:8000 in your browser
```

You should see the bracket with win percentages for each team.

---

## Step 7 — GitHub Pages setup

1. Push your repo to GitHub (make sure `data/predictions.json` is committed):

```bash
git add .
git commit -m "feat: initial setup with Round of 32 predictions"
git push origin main
```

2. On GitHub, go to your repo → **Settings** → **Pages**
3. Under "Source", select `Deploy from a branch`
4. Branch: `main`, Folder: `/ (root)` → **Save**

Wait ~60 seconds, then visit:

```
https://YOUR_USERNAME.github.io/wc2026prediction/web/
```

Your dashboard is now live. Any future push that includes an updated `predictions.json` will redeploy the site automatically within ~30 seconds.

---

## Updating after each round

After a round ends and all results are confirmed:

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run the update
python update.py

# Commit and push
git add data/predictions.json data/bracket.json data/teams.json
git commit -m "chore: Round of 16 predictions updated"
git push
```

The dashboard updates live after the push.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'requests'`

Your virtual environment is not activated. Run `source venv/bin/activate` first.

### `API_FOOTBALL_KEY not set`

Your `.env` file is missing or the key name is wrong. Check that `.env` exists in the project root and has `API_FOOTBALL_KEY=your_key`.

### `DataValidationError: Round not fully complete`

Not all matches in the current round have finished yet. Wait until every match has a result before running `update.py`.

### Transfermarkt scraper returns empty data

Transfermarkt may have changed their HTML structure. Check `src/value.py` and update the CSS selector. The pipeline will continue with the last known values.

### GitHub Pages shows old predictions

GitHub Pages can take up to 5 minutes to rebuild. Check the **Actions** tab on GitHub to see the deployment status.

### Dashboard shows blank / fetch error locally

You must serve `web/index.html` via HTTP, not open it as a file. Use `python -m http.server 8000 --directory web`.

---

## Environment variables reference

| Variable | Required | Description |
|---|---|---|
| `API_FOOTBALL_KEY` | Yes | API-Football API key |
| `ODDS_API_KEY` | No | The Odds API key (betting signals) |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |
| `N_SIMULATIONS` | No | Monte Carlo count (default: `10000`) |
