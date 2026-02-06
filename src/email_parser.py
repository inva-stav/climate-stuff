"""
Parse .eml files (forwarded emails) to extract event/opportunity information.

Workflow: drop .eml files into emails/inbox/, this module reads them.
"""

import email
import os
import re
from email import policy
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


def extract_text_from_email(msg):
    """Get the plain-text body from an email.Message, falling back to HTML→text."""
    # Try plain text first
    if msg.is_multipart():
        parts = list(msg.walk())
    else:
        parts = [msg]

    plain = ""
    html = ""
    for part in parts:
        ct = part.get_content_type()
        try:
            payload = part.get_content()
        except Exception:
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    payload = payload.decode("utf-8", errors="replace")
                else:
                    continue
            except Exception:
                continue

        if not isinstance(payload, str):
            continue

        if ct == "text/plain":
            plain += payload
        elif ct == "text/html":
            html += payload

    if plain.strip():
        return plain.strip()
    if html.strip():
        soup = BeautifulSoup(html, "lxml")
        # Remove script/style
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    return ""


def extract_links(msg):
    """Extract URLs from the email body."""
    text = extract_text_from_email(msg)
    # Also look in HTML parts for href
    urls = set(re.findall(r'https?://[^\s<>"\')\]]+', text))

    if msg.is_multipart():
        parts = list(msg.walk())
    else:
        parts = [msg]

    for part in parts:
        if part.get_content_type() == "text/html":
            try:
                payload = part.get_content()
            except Exception:
                payload = (part.get_payload(decode=True) or b"").decode("utf-8", errors="replace")
            if isinstance(payload, str):
                soup = BeautifulSoup(payload, "lxml")
                for a in soup.find_all("a", href=True):
                    urls.add(a["href"])

    return list(urls)


def extract_dates_from_text(text):
    """Try to find dates mentioned in the text body."""
    # Common patterns: "January 15, 2025", "Jan 15", "1/15/2025", "2025-01-15"
    date_patterns = [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,?\s*\d{4})?\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2}(?:,?\s*\d{4})?\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b',
    ]
    found = []
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                dt = dateparser.parse(match.group(), fuzzy=False)
                if dt and dt.year >= 2024:
                    found.append(dt)
            except (ValueError, TypeError):
                continue
    return found


def parse_eml_file(filepath):
    """Parse a single .eml file and return a structured record."""
    with open(filepath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    subject = msg.get("Subject", "(no subject)")
    sender = msg.get("From", "")
    date_sent = msg.get("Date", "")
    try:
        sent_dt = dateparser.parse(date_sent) if date_sent else None
    except (ValueError, TypeError):
        sent_dt = None

    body = extract_text_from_email(msg)
    links = extract_links(msg)
    mentioned_dates = extract_dates_from_text(body)

    # Pick the earliest future date mentioned, or fall back to sent date
    now = datetime.now()
    future_dates = [d for d in mentioned_dates if d >= now]
    event_date = min(future_dates) if future_dates else sent_dt

    return {
        "title": subject,
        "description": body[:2000],  # truncate very long bodies
        "url": links[0] if links else "",
        "all_links": links,
        "start": event_date,
        "location": "",  # hard to extract reliably; classifier can help
        "source": f"email:{sender}",
        "source_file": os.path.basename(filepath),
        "category": None,
        "raw_type": "email",
    }


def parse_all_emails(inbox_dir="emails/inbox"):
    """Parse all .eml files in the inbox directory."""
    inbox = Path(inbox_dir)
    if not inbox.exists():
        print(f"  No inbox directory at {inbox_dir}, skipping email parsing.")
        return []

    eml_files = sorted(inbox.glob("*.eml"))
    if not eml_files:
        print(f"  No .eml files found in {inbox_dir}.")
        return []

    results = []
    for eml_path in eml_files:
        print(f"  Parsing: {eml_path.name}")
        try:
            record = parse_eml_file(eml_path)
            results.append(record)
        except Exception as e:
            print(f"  Warning: failed to parse {eml_path.name}: {e}")

    print(f"  Parsed {len(results)} emails.")
    return results
