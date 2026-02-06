"""
Generate a weekly newsletter from classified items.
Outputs Markdown and HTML.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


# Display order and grouping for sections
SECTION_ORDER = [
    ("Events & Talks", ["event", "talk", "conference", "workshop"]),
    ("Jobs & Fellowships", ["job"]),
    ("Networking & Social", ["networking", "field_trip"]),
    ("Deadlines & Funding", ["deadline"]),
]


def make_snippet(description, max_len=200):
    """Create a short plain-text snippet from description."""
    if not description:
        return ""
    # Collapse whitespace
    text = re.sub(r"\s+", " ", description).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def group_items(items):
    """Group items into newsletter sections. Returns list of (section_name, items)."""
    assigned = set()
    sections = []

    for section_name, types in SECTION_ORDER:
        section_items = [
            item for item in items
            if item.get("category") in types and id(item) not in assigned
        ]
        if section_items:
            for item in section_items:
                assigned.add(id(item))
                item["snippet"] = make_snippet(item.get("description", ""))
            sections.append((section_name, section_items))

    # Catch-all for anything not matched
    remaining = [item for item in items if id(item) not in assigned]
    if remaining:
        for item in remaining:
            item["snippet"] = make_snippet(item.get("description", ""))
        sections.append(("Other", remaining))

    return sections


def render_markdown(title, subtitle, sections):
    """Render newsletter as Markdown."""
    lines = [f"# {title}", f"*{subtitle}*", ""]

    for section_name, items in sections:
        lines.append(f"## {section_name} ({len(items)})")
        lines.append("")
        for item in items:
            badge = f"[{item['category'].replace('_', ' ').upper()}]"
            if item.get("url"):
                lines.append(f"### [{item['title']}]({item['url']}) {badge}")
            else:
                lines.append(f"### {item['title']} {badge}")

            meta_parts = []
            if item.get("start"):
                meta_parts.append(item["start"].strftime("%a, %b %-d"))
                if item["start"].hour:
                    meta_parts[-1] += item["start"].strftime(" at %-I:%M %p")
            if item.get("location"):
                meta_parts.append(item["location"])
            if meta_parts:
                lines.append(" | ".join(meta_parts))

            if item.get("snippet"):
                lines.append("")
                lines.append(f"> {item['snippet']}")
            lines.append("")

    if not sections:
        lines.append("*No events found for this period.*")

    lines.append("---")
    lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    return "\n".join(lines)


def render_html(title, subtitle, sections, template_dir="templates"):
    """Render newsletter as HTML using Jinja2 template."""
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("newsletter.html")
    return template.render(
        title=title,
        subtitle=subtitle,
        sections=sections,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


def generate_newsletter(items, output_dir="output", days=14):
    """Generate both Markdown and HTML newsletter files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    title = "Climate & Sustainability Weekly"
    subtitle = f"Events, jobs, and opportunities — Week of {now.strftime('%B %-d, %Y')}"

    sections = group_items(items)

    # Markdown
    md = render_markdown(title, subtitle, sections)
    md_path = output / f"newsletter-{date_str}.md"
    md_path.write_text(md)
    print(f"  Wrote: {md_path}")

    # HTML
    html = render_html(title, subtitle, sections)
    html_path = output / f"newsletter-{date_str}.html"
    html_path.write_text(html)
    print(f"  Wrote: {html_path}")

    total = sum(len(items) for _, items in sections)
    print(f"  Newsletter has {total} items across {len(sections)} sections.")
    return md_path, html_path
