# Climate & Sustainability Newsletter Generator

Automatically scrapes Stanford events and parses forwarded emails to generate a weekly digest of climate, sustainability, and energy events, jobs, and opportunities.

## How it works

```
Outlook (via Claude) ─┐
emails/inbox/*.eml ───┤
                      ├──▶ Classifier ──▶ Newsletter (Markdown + HTML)
events.stanford.edu ──┘    (filter &      output/newsletter-YYYY-MM-DD.{md,html}
  (Localist API)           categorize)
```

**Sources:**
- **Outlook** — Claude searches your Outlook mailbox for climate/energy emails, extracts structured items, and writes them to a JSON file
- **Stanford Events** — scrapes `events.stanford.edu/api/2/events` for ~25 climate-related keywords
- **Emails** — parses `.eml` files you drop into `emails/inbox/`

**Output** matches the SEC Mailchimp newsletter format with green `#89D085` dividers, WHO/WHEN/WHERE/RSVP structure, and Events + Opportunities sections.

## Quick start

### With Claude Code (recommended)
Ask Claude: *"Generate this week's SEC newsletter"* — it will search your Outlook, scrape Stanford events, and produce the newsletter.

### Standalone
```bash
pip install -r requirements.txt

# Full pipeline: scrape + parse emails + generate
python generate.py

# With pre-extracted items from Outlook
python generate.py --items items.json --no-emails

# Scrape-only
python generate.py --no-emails

# Custom time window
python generate.py --days 7
```

### Items JSON format
When Claude extracts items from Outlook, it writes a JSON file like:
```json
[
  {
    "title": "Stanford Energy Seminar | Battery Innovation",
    "who": "Tim Holme, CTO of QuantumScape",
    "when": "Monday, May 12, 4:30–5:20 p.m.",
    "where": "Jen-Hsun Huang Building, NVIDIA Auditorium",
    "url": "https://events.stanford.edu/...",
    "description": "Work on solid electrolytes for rechargeable lithium-based batteries...",
    "source": "outlook",
    "category": "talk",
    "start": "2025-05-12T16:30:00"
  }
]
```

## Project structure

```
generate.py              # CLI entry point
src/
  scraper.py             # Stanford events.stanford.edu Localist API scraper
  email_parser.py        # .eml file parser (plain text + HTML)
  classifier.py          # Relevance filter + type classification
  newsletter.py          # Markdown + HTML newsletter generation (SEC style)
templates/
  newsletter.html        # Mailchimp-compatible Jinja2 template
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
