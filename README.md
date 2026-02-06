# Climate & Sustainability Newsletter Generator

Automatically scrapes Stanford events and parses forwarded emails to generate a weekly digest of climate, sustainability, and energy events, jobs, and opportunities.

## How it works

```
emails/inbox/*.eml ──┐
                     ├──▶ Classifier ──▶ Newsletter (Markdown + HTML)
events.stanford.edu ─┘    (filter &      output/newsletter-YYYY-MM-DD.{md,html}
  (Localist API)          categorize)
```

**Sources:**
- **Stanford Events** — scrapes `events.stanford.edu/api/2/events` for ~25 climate-related keywords (climate, sustainability, energy, renewable, carbon, cleantech, etc.)
- **Emails** — parses `.eml` files you drop into `emails/inbox/`. Handles plain text and HTML emails, extracts dates/links/content.

**Classification** assigns each item a type: `event`, `talk`, `job`, `field_trip`, `networking`, `workshop`, `conference`, or `deadline`.

**Output** is grouped into sections: Events & Talks, Jobs & Fellowships, Networking & Social, Deadlines & Funding.

## Quick start

```bash
pip install -r requirements.txt

# Full pipeline: scrape Stanford + parse emails + generate newsletter
python generate.py

# Email-only (skip scraping)
python generate.py --no-scrape

# Scrape-only (skip emails)
python generate.py --no-emails

# Custom time window and paths
python generate.py --days 7 --inbox path/to/emails --output path/to/output
```

Output goes to `output/` as both Markdown and HTML files.

## Email workflow

1. When you receive a climate/sustainability email, forward it to yourself or save it as `.eml`
2. Drop the `.eml` file into `emails/inbox/`
3. Run `python generate.py`

Most email clients let you save as `.eml` via drag-and-drop or "Save As". In Gmail, you can use "Show original" → "Download Original".

Sample emails are in `emails/samples/` for reference.

## Project structure

```
generate.py              # CLI entry point
src/
  scraper.py             # Stanford events.stanford.edu Localist API scraper
  email_parser.py        # .eml file parser (plain text + HTML)
  classifier.py          # Relevance filter + type classification
  newsletter.py          # Markdown + HTML newsletter generation
templates/
  newsletter.html        # Jinja2 HTML template
emails/
  inbox/                 # Drop .eml files here (gitignored)
  samples/               # Example .eml files
output/                  # Generated newsletters (gitignored)
```

## Extending

**Add keywords**: Edit `SEARCH_KEYWORDS` in `src/scraper.py` and `RELEVANCE_KEYWORDS` in `src/classifier.py`.

**Add event types**: Add patterns to `TYPE_PATTERNS` in `src/classifier.py`.

**Change newsletter style**: Edit `templates/newsletter.html` (Jinja2) or tweak `render_markdown()` in `src/newsletter.py`.

**Automate weekly runs**: Add a cron job:
```bash
# Every Monday at 8am
0 8 * * 1 cd /path/to/climate-stuff && python generate.py >> /var/log/newsletter.log 2>&1
```
