#!/usr/bin/env python3
"""
Climate & Sustainability Newsletter Generator

Usage:
    python generate.py                  # scrape + parse emails + generate newsletter
    python generate.py --no-scrape      # skip Stanford events, only parse emails
    python generate.py --no-emails      # skip emails, only scrape Stanford events
    python generate.py --days 7         # look ahead 7 days instead of default 14
"""

import argparse
import sys
from src.scraper import scrape_stanford_events
from src.email_parser import parse_all_emails
from src.classifier import classify_items
from src.newsletter import generate_newsletter


def main():
    parser = argparse.ArgumentParser(
        description="Generate a climate/sustainability newsletter from Stanford events and emails."
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

    if args.no_scrape and args.no_emails:
        print("Error: can't skip both scraping and emails. Nothing to do.")
        sys.exit(1)

    all_items = []

    # 1. Scrape Stanford events
    if not args.no_scrape:
        print("[1/3] Scraping events.stanford.edu...")
        events = scrape_stanford_events(days=args.days)
        all_items.extend(events)
    else:
        print("[1/3] Skipping Stanford events scrape.")

    # 2. Parse emails
    if not args.no_emails:
        print("[2/3] Parsing emails...")
        email_items = parse_all_emails(args.inbox)
        all_items.extend(email_items)
    else:
        print("[2/3] Skipping email parsing.")

    if not all_items:
        print("No items found from any source. Nothing to generate.")
        sys.exit(0)

    # 3. Classify and filter
    print("[3/3] Classifying and generating newsletter...")
    classified = classify_items(all_items)

    if not classified:
        print("No relevant items after classification. Nothing to generate.")
        sys.exit(0)

    # 4. Generate
    md_path, html_path = generate_newsletter(classified, output_dir=args.output, days=args.days)
    print(f"\nDone! Newsletter files:")
    print(f"  Markdown: {md_path}")
    print(f"  HTML:     {html_path}")


if __name__ == "__main__":
    main()
