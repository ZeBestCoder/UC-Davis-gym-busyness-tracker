# UC Davis gym busyness tracker

Collects the live occupancy numbers from <https://rec.ucdavis.edu/facilityoccupancy>
once an hour (ARC, Recreation Pool, Rock Wall) and shows them on a dashboard.

| File | What it does |
|---|---|
| `scrape.py` | Fetches the page once, appends one row per facility to `data/occupancy.csv` |
| `.github/workflows/collect.yml` | Runs `scrape.py` every hour at :17 and commits the CSV |
| `index.html` | Dashboard (heatmap, hourly averages, quietest/busiest times, daily trend) |
| `data/occupancy.csv` | The collected data (created on the first run) |

## Setup

1. Create a new **public** repository on github.com (e.g. `ucd-gym-occupancy`). Leave it empty.
   Public is recommended: Actions minutes are unlimited and GitHub Pages is free.
2. Push this folder to it:
   ```
   git init -b main
   git add .
   git commit -m "Gym occupancy collector"
   git remote add origin https://github.com/<your-username>/ucd-gym-occupancy.git
   git push -u origin main
   ```
3. **Test the collector:** repo → **Actions** tab → *Collect occupancy* → **Run workflow**.
   After ~30 seconds a commit "data: ..." should appear and `data/occupancy.csv` will exist.
4. **Turn on the dashboard:** repo → **Settings → Pages** → Source: *Deploy from a branch*,
   Branch: `main`, folder `/ (root)` → Save. The site appears at
   `https://<your-username>.github.io/ucd-gym-occupancy/` within a minute or two.

From then on it runs by itself every hour, even with your computer off.

## Stopping

`COLLECT_UNTIL` in `collect.yml` is set to `2026-11-03` (4 weeks). After that date the job
makes no more requests. When you're done, disable the workflow entirely:
**Actions → Collect occupancy → ⋯ → Disable workflow**.

## Notes on the data

- Times are Davis local time (`timestamp_local`, `weekday`, `hour`). GitHub's scheduler
  sometimes starts runs late or skips one during busy periods, so expect a few gaps.
- Only open hours are collected: Mon–Fri 5 AM–midnight, Sat–Sun 8 AM–11 PM (`OPEN_HOURS` in
  `scrape.py`, `OPEN` in `index.html`). The workflow still wakes every hour but exits without
  a request when the gym is closed. Manual "Run workflow" clicks always fetch, for testing.
- If the site is down or shows a waiting-room page, that hour is skipped (no row), not
  recorded as 0. Check the Actions run log for yellow warnings.
- The site's `robots.txt` asks automated tools not to crawl it. This collector makes one
  request per hour, identifies itself in its User-Agent, and never retries.
- Analyse the CSV in Excel, Google Sheets, or pandas: `pd.read_csv("data/occupancy.csv")`.
- Preview the dashboard layout with fake data by adding `?demo` to its URL.
