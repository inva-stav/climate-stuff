"""
Scrape events.stanford.edu (Localist API) for climate/sustainability/energy events.
"""

import requests
from datetime import datetime, timedelta
from dateutil import parser as dateparser


# Keywords that indicate climate/sustainability/energy relevance
SEARCH_KEYWORDS = [
    "climate",
    "sustainability",
    "energy",
    "environment",
    "carbon",
    "renewable",
    "solar",
    "cleantech",
    "decarbonization",
    "net zero",
    "circular economy",
    "ESG",
    "green",
    "conservation",
    "biodiversity",
    "ecology",
    "resilience",
    "water",
    "pollution",
    "fossil fuel",
    "EV",
    "electric vehicle",
    "battery",
    "hydrogen",
    "nuclear",
    "wind power",
    "geothermal",
]

API_BASE = "https://events.stanford.edu/api/2/events"


def fetch_events_for_keyword(keyword, days=14, max_pages=3):
    """Fetch events matching a keyword from the Localist API."""
    all_events = []
    for page in range(1, max_pages + 1):
        params = {
            "keyword": keyword,
            "days": days,
            "pp": 100,
            "p": page,
        }
        try:
            resp = requests.get(API_BASE, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Warning: request failed for keyword '{keyword}' page {page}: {e}")
            break

        data = resp.json()
        events = data.get("events", [])
        if not events:
            break
        all_events.extend(events)
    return all_events


def normalize_event(raw):
    """Convert a raw Localist API event dict into a clean record."""
    event = raw.get("event", raw)
    # Parse dates
    start = event.get("event_instances", [{}])
    if start:
        start_str = start[0].get("event_instance", {}).get("start", "")
    else:
        start_str = event.get("first_date", "")

    try:
        start_dt = dateparser.parse(start_str) if start_str else None
    except (ValueError, TypeError):
        start_dt = None

    location_name = event.get("location_name", "") or ""
    location = event.get("location", "") or ""
    room = event.get("room_number", "") or ""
    full_location = ", ".join(filter(None, [location_name, location, room]))

    return {
        "title": event.get("title", "").strip(),
        "description": event.get("description_text", "").strip(),
        "url": event.get("localist_url", "") or event.get("url", ""),
        "start": start_dt,
        "location": full_location,
        "source": "events.stanford.edu",
        "category": None,  # filled in by classifier
        "raw_type": "event",
    }


def scrape_stanford_events(days=14):
    """Scrape Stanford events for all climate-related keywords. Returns deduplicated list."""
    seen_titles = set()
    results = []

    for kw in SEARCH_KEYWORDS:
        print(f"  Searching events.stanford.edu for: {kw}")
        raw_events = fetch_events_for_keyword(kw, days=days)
        for raw in raw_events:
            ev = normalize_event(raw)
            key = ev["title"].lower()
            if key and key not in seen_titles:
                seen_titles.add(key)
                results.append(ev)

    results.sort(key=lambda e: (e["start"] or datetime.max))
    print(f"  Found {len(results)} unique events from events.stanford.edu")
    return results
