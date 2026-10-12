"""
Generate the SEC weekly newsletter from classified items.
Outputs Markdown (for editing) and HTML (Mailchimp-ready).
"""

import json
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


SECTION_ORDER = [
    ("Events", ["event", "talk", "conference", "workshop", "networking", "field_trip"]),
    ("Opportunities", ["job", "deadline"]),
]

DAYS_OF_WEEK = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]


def format_when(item):
    """Format the WHEN line from item data."""
    dt = item.get("start")
    if not dt:
        return item.get("when", "")
    parts = [dt.strftime("%A, %B %-d")]
    if dt.hour or dt.minute:
        parts[0] += dt.strftime(", %-I:%M")
        end = item.get("end")
        if end and (end.hour or end.minute):
            parts[0] += end.strftime("–%-I:%M %p")
        else:
            parts[0] += dt.strftime(" %p")
    return parts[0]


def format_who(item):
    """Format the WHO line. Falls back to a sensible default."""
    if item.get("who"):
        return item["who"]
    if item.get("speaker"):
        return item["speaker"]
    return ""


BOILERPLATE_PATTERNS = [
    re.compile(
        r"The Stanford Energy Seminar has been a mainstay.*?About the talk\s*",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"About the speaker\s*$",
        re.IGNORECASE,
    ),
]


def clean_description(desc):
    """Strip recurring boilerplate preambles from event descriptions."""
    for pattern in BOILERPLATE_PATTERNS:
        desc = pattern.sub("", desc)
    return desc.strip()


def prepare_item(item):
    """Enrich an item with formatted fields for the template."""
    item["when"] = item.get("when") or format_when(item)
    item["who"] = format_who(item)
    item["where"] = item.get("location") or item.get("where", "")
    item["is_opportunity"] = item.get("category") in ("job", "deadline")

    desc = item.get("description", "")
    desc = re.sub(r"\s+", " ", desc).strip()
    desc = clean_description(desc)
    item["description"] = desc
    return item


def group_items(items):
    """Group items into Events and Opportunities sections."""
    assigned = set()
    sections = []

    for section_name, types in SECTION_ORDER:
        section_items = [
            prepare_item(item) for item in items
            if item.get("category") in types and id(item) not in assigned
        ]
        for item in section_items:
            assigned.add(id(item))
        if section_items:
            sections.append({"name": section_name, "items": section_items})

    remaining = [prepare_item(item) for item in items if id(item) not in assigned]
    if remaining:
        sections.append({"name": "More", "items": remaining})

    return sections


def render_markdown(greeting, intro, sections):
    """Render newsletter as Markdown for easy editing."""
    lines = [f"**{greeting}**", "", intro, ""]

    for section in sections:
        lines.append(f"---")
        lines.append(f"## {section['name']}")
        lines.append("")
        for item in section["items"]:
            lines.append(f"**{item['title']}**")
            lines.append("")
            if item.get("who"):
                lines.append(f"**WHO:** {item['who']}  ")
            if item.get("when"):
                lines.append(f"**WHEN:** {item['when']}  ")
            if item.get("where"):
                lines.append(f"**WHERE:** {item['where']}  ")
            if item.get("url"):
                label = "Apply" if item.get("is_opportunity") else "RSVP"
                lines.append(f"**{label}:** [{label} here]({item['url']})  ")
            lines.append("")
            if item.get("description"):
                lines.append(item["description"])
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Want to stay updated on all the energy events and projects happening on campus? "
                 "Sign up for our [mailing list](https://mailman.stanford.edu/mailman/listinfo/energyclub-members) "
                 "and follow us on [Instagram](https://www.instagram.com/stanford.energy.club/).")
    return "\n".join(lines)


def render_html(greeting, intro, sections, template_dir="templates"):
    """Render newsletter as Mailchimp-ready HTML."""
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("newsletter.html")
    return template.render(
        greeting=greeting,
        intro=intro,
        sections=sections,
    )


def generate_newsletter(items, output_dir="output", days=14):
    """Generate both Markdown and HTML newsletter files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    day_name = DAYS_OF_WEEK[now.weekday()]

    greeting = f"Happy {day_name}, Energy Enthusiasts."
    intro = ("Read on for a curated set of events this week alongside "
             "our pick of exciting opportunities.")

    sections = group_items(items)

    md = render_markdown(greeting, intro, sections)
    md_path = output / f"newsletter-{date_str}.md"
    md_path.write_text(md)
    print(f"  Wrote: {md_path}")

    html = render_html(greeting, intro, sections)
    html_path = output / f"newsletter-{date_str}.html"
    html_path.write_text(html)
    print(f"  Wrote: {html_path}")

    total = sum(len(s["items"]) for s in sections)
    print(f"  Newsletter has {total} items across {len(sections)} sections.")
    return md_path, html_path
