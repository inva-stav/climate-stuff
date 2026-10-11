"""
Classify and filter items by relevance (climate/sustainability/energy)
and by type (event, job, opportunity, etc.).
"""

import re

# --- Relevance keywords (must match at least one to be included) ---
RELEVANCE_KEYWORDS = [
    r"\bclimate\b",
    r"\bsustainab",
    r"\benergy\b",
    r"\benvironment\w*\b",
    r"\bcarbon\b",
    r"\brenewable\b",
    r"\bsolar\b",
    r"\bcleantech\b",
    r"\bdecarboniz",
    r"\bnet.?zero\b",
    r"\bcircular economy\b",
    r"\besg\b",
    r"\bgreen\b",
    r"\bconservation\b",
    r"\bbiodiversity\b",
    r"\becolog",
    r"\bresilience\b",
    r"\bpollution\b",
    r"\bfossil fuel",
    r"\belectric vehicle",
    r"\b(?:ev|EV)\b",
    r"\bbatter(?:y|ies)\b",
    r"\bhydrogen\b",
    r"\bnuclear\b",
    r"\bwind (?:power|energy|farm)",
    r"\bgeothermal\b",
    r"\bemissions?\b",
    r"\bgreenhouse\b",
    r"\bclean air\b",
    r"\bclean water\b",
    r"\bwater(?:\s+)(?:quality|scarcity|security)\b",
    r"\bforest",
    r"\bdeforest",
    r"\bocean",
    r"\bmarine",
    r"\bwildlife\b",
    r"\beco-?system",
    r"\bnet.?positive\b",
    r"\bimpact invest",
    r"\bclimate justice",
    r"\benergy transition",
    r"\bgrid\b",
    r"\bmicrogrid\b",
    r"\bstorage\b.*\benergy\b",
    r"\benergy\b.*\bstorage\b",
    r"\bcarbon capture\b",
    r"\bCCS\b",
    r"\bCCUS\b",
]

# --- Type classification patterns ---
TYPE_PATTERNS = {
    "job": [
        r"\bjob\b",
        r"\bhiring\b",
        r"\bposition\b",
        r"\bopening\b",
        r"\bcareer\b",
        r"\bapply now\b",
        r"\bapplication deadline\b",
        r"\brecruiting\b",
        r"\bresume\b",
        r"\bfull.?time\b",
        r"\bpart.?time\b",
        r"\bintern(?:ship)?\b",
        r"\bfellow(?:ship)?\b",
        r"\bpostdoc\b",
        r"\bRA position\b",
        r"\bresearch assistant\b",
    ],
    "field_trip": [
        r"\bfield trip\b",
        r"\bsite visit\b",
        r"\btour\b",
        r"\bexcursion\b",
    ],
    "networking": [
        r"\bnetwork(?:ing)?\b",
        r"\bmixer\b",
        r"\bhappy hour\b",
        r"\bdinner with\b",
        r"\blunch with\b",
        r"\bcoffee chat\b",
        r"\bmeet(?:ing)?.*(?:VC|investor|founder)\b",
        r"\bfireside chat\b",
    ],
    "talk": [
        r"\btalk\b",
        r"\blecture\b",
        r"\bseminar\b",
        r"\bpresentation\b",
        r"\bkeynote\b",
        r"\bspeaker\b",
        r"\bwebinar\b",
        r"\bcolloquium\b",
    ],
    "workshop": [
        r"\bworkshop\b",
        r"\bhands.?on\b",
        r"\bbootcamp\b",
        r"\btraining\b",
        r"\bhackathon\b",
    ],
    "conference": [
        r"\bconference\b",
        r"\bsummit\b",
        r"\bsymposium\b",
        r"\bforum\b",
    ],
    "deadline": [
        r"\bdeadline\b",
        r"\bdue date\b",
        r"\bsubmission",
        r"\bgrant\b",
        r"\bRFP\b",
        r"\bfunding\b",
        r"\bscholarship\b",
    ],
    "event": [
        # Catch-all for general events
        r"\bevent\b",
        r"\bregistration\b",
        r"\bRSVP\b",
    ],
}


def is_relevant(item):
    """Return True if the item is climate/sustainability/energy related."""
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    for pattern in RELEVANCE_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def classify_type(item):
    """Assign a category type based on content. Returns the best-matching type."""
    text = f"{item.get('title', '')} {item.get('description', '')}".lower()
    scores = {}
    for type_name, patterns in TYPE_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
        if score > 0:
            scores[type_name] = score

    if not scores:
        return "event"  # default
    return max(scores, key=scores.get)


def classify_items(items):
    """Filter for relevance and assign types. Returns only relevant items."""
    results = []
    for item in items:
        source = item.get("source", "")
        # Stanford scraper results are already keyword-filtered.
        # Pre-extracted items (from Outlook via Claude) have source "outlook"
        # and are already curated, so skip relevance check for those too.
        needs_check = source.startswith("email:") and source != "outlook"
        if needs_check and not is_relevant(item):
            print(f"  Skipping (not relevant): {item['title'][:60]}")
            continue

        if not item.get("category"):
            item["category"] = classify_type(item)
        results.append(item)

    type_counts = {}
    for item in results:
        t = item["category"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"  Classified {len(results)} items: {type_counts}")
    return results
