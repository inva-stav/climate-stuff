"""
Scrape events.stanford.edu (Localist API) for climate/sustainability/energy events.
"""

import requests
from datetime import datetime, timedelta
from dateutil import parser as dateparser


# Keyword searches — combining general terms with specific recurring series
# that historically appear in SEC newsletters
SEARCH_KEYWORDS = [
    # Core topics
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
    "conservation",
    "biodiversity",
    "ecology",
    "resilience",
    "pollution",
    "fossil fuel",
    "electric vehicle",
    "battery",
    "hydrogen",
    "nuclear",
    "wind power",
    "geothermal",
    "biomass",
    "environmental justice",
    # Recurring series and orgs from past SEC newsletters
    "Stanford Energy Seminar",
    "Sustainable Systems",
    "ESE Seminar",
    "CEE 269",
    "SustainX",
    "Precourt",
    "Doerr School",
    "Explore Energy",
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

    instances = event.get("event_instances", [])
    start_str = ""
    end_str = ""
    if instances:
        inst = instances[0].get("event_instance", {})
        start_str = inst.get("start", "")
        end_str = inst.get("end", "")
    else:
        start_str = event.get("first_date", "")

    try:
        start_dt = dateparser.parse(start_str) if start_str else None
    except (ValueError, TypeError):
        start_dt = None

    try:
        end_dt = dateparser.parse(end_str) if end_str else None
    except (ValueError, TypeError):
        end_dt = None

    location_name = event.get("location_name", "") or ""
    location = event.get("location", "") or ""
    room = event.get("room_number", "") or ""
    full_location = ", ".join(filter(None, [location_name, location, room]))

    # Build WHO from filters/departments if available
    who = ""
    filters = event.get("filters", {})
    departments = filters.get("departments", [])
    if departments:
        who = departments[0].get("name", "")

    # Build a formatted WHEN string
    when = ""
    if start_dt:
        when = start_dt.strftime("%A, %B %-d")
        if start_dt.hour or start_dt.minute:
            when += start_dt.strftime(", %-I:%M")
            if end_dt and (end_dt.hour or end_dt.minute):
                when += end_dt.strftime("–%-I:%M %p")
            else:
                when += start_dt.strftime(" %p")

    return {
        "title": event.get("title", "").strip(),
        "description": event.get("description_text", "").strip(),
        "url": event.get("localist_url", "") or event.get("url", ""),
        "start": start_dt,
        "end": end_dt,
        "when": when,
        "who": who,
        "where": full_location,
        "location": full_location,
        "source": "events.stanford.edu",
        "category": None,
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
