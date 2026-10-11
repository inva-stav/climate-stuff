#!/usr/bin/env python3
"""
Stanford Energy Club Newsletter Generator

Usage:
    python generate.py                        # scrape + parse emails + generate
    python generate.py --no-scrape            # skip Stanford events, only parse emails
    python generate.py --no-emails            # skip emails, only scrape Stanford events
    python generate.py --items items.json     # load pre-extracted items from JSON
    python generate.py --days 7               # look ahead 7 days instead of default 14
"""

import argparse
import json
import sys
from datetime import datetime
from dateutil import parser as dateparser
from src.scraper import scrape_stanford_events
from src.email_parser import parse_all_emails
from src.classifier import classify_items
from src.newsletter import generate_newsletter


def load_items_from_json(filepath):
    """Load pre-extracted items from a JSON file (e.g. from Outlook search)."""
    with open(filepath, "r") as f:
        items = json.load(f)

    for item in items:
        if item.get("start") and isinstance(item["start"], str):
            try:
                item["start"] = dateparser.parse(item["start"])
            except (ValueError, TypeError):
                item["start"] = None

    print(f"  Loaded {len(items)} items from {filepath}")
    return items


def main():
    parser = argparse.ArgumentParser(
        description="Generate SEC newsletter from Stanford events, emails, and pre-extracted items."
    )
    parser.add_argument(
        "--no-scrape", action="store_true",
        help="Skip scraping events.stanford.edu",
    )
    parser.add_argument(
        "--no-emails", action="store_true",
        help="Skip parsing emails from inbox",
    )
    parser.add_argument(
        "--items", type=str,
        help="Path to JSON file with pre-extracted items (e.g. from Outlook)",
    )
    parser.add_argument(
        "--days", type=int, default=14,
        help="Number of days to look ahead for events (default: 14)",
    )
    parser.add_argument(
        "--inbox", type=str, default="emails/inbox",
        help="Path to directory containing .eml files (default: emails/inbox)",
    )
    parser.add_argument(
        "--output", type=str, default="output",
        help="Output directory for generated newsletter (default: output)",
    )
    args = parser.parse_args()

    has_items = args.items is not None
    if args.no_scrape and args.no_emails and not has_items:
        print("Error: no sources enabled. Use --items, or enable scraping or email parsing.")
        sys.exit(1)

    all_items = []

    # 1. Load pre-extracted items (e.g. from Outlook via Claude)
    if has_items:
        print("[1/3] Loading pre-extracted items...")
        all_items.extend(load_items_from_json(args.items))
    else:
        print("[1/3] No pre-extracted items file.")

    # 2. Scrape Stanford events
    if not args.no_scrape:
        print("[2/3] Scraping events.stanford.edu...")
        events = scrape_stanford_events(days=args.days)
        all_items.extend(events)
    else:
        print("[2/3] Skipping Stanford events scrape.")

    # 3. Parse emails
    if not args.no_emails:
        print("[3/3] Parsing emails...")
        email_items = parse_all_emails(args.inbox)
        all_items.extend(email_items)
    else:
        print("[3/3] Skipping email parsing.")

    if not all_items:
        print("No items found from any source. Nothing to generate.")
        sys.exit(0)

    # Classify and filter
    print("Classifying and generating newsletter...")
    classified = classify_items(all_items)

    if not classified:
        print("No relevant items after classification. Nothing to generate.")
        sys.exit(0)

    # Load logo URL from config if available
    logo_url = None
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        logo_url = config.get("newsletter", {}).get("logo_url")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Generate
    md_path, html_path = generate_newsletter(
        classified, output_dir=args.output, days=args.days, logo_url=logo_url
    )
    print(f"\nDone! Newsletter files:")
    print(f"  Markdown: {md_path}")
    print(f"  HTML:     {html_path}")


if __name__ == "__main__":
    main()
