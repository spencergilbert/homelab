#!/usr/bin/env python3
"""
RFD (Request for Discussion) management tool.
Generates new RFD documents and maintains an index in docs/README.md.
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"
RFDS_DIR = DOCS_DIR / "rfds"
TEMPLATE_FILE = RFDS_DIR / "_template.md.tpl"
README_FILE = DOCS_DIR / "README.md"
INDEX_START_MARKER = "<!-- BEGIN RFD INDEX -->"
INDEX_END_MARKER = "<!-- END RFD INDEX -->"

TITLE_RE = re.compile(r"^# RFD (?P<number>\d+): (?P<title>.+)", re.MULTILINE)
META_RE = re.compile(
    r"<!-- RFD-META\s*"
    r"Status:\s*(?P<status>\w+)\s*"
    r"Date:\s*(?P<date>.+?)\s*"
    r"Author:\s*(?P<author>.+?)\s*-->",
    re.DOTALL,
)


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9-]+", "-", slug)
    # Collapse multiple dashes to avoid ugly filenames like "foo--bar"
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _next_rfd_number() -> int:
    max_number = 0

    if not RFDS_DIR.exists():
        return 1

    for file in RFDS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"):
        match = re.match(r"^(\d{4})-", file.name)
        if match:
            num = int(match.group(1))
            max_number = max(max_number, num)

    return max_number + 1


def _replace_placeholders(template: str, mapping: dict) -> str:
    result = template
    for key, value in mapping.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result


def _update_file_section(path: Path, start: str, end: str, new_content: str) -> None:
    if not path.exists():
        print(f"❌ Error: {path} does not exist", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    start_idx = content.find(start)
    end_idx = content.find(end)

    if start_idx == -1 or end_idx == -1:
        print(f"❌ Error: Could not find markers in {path}", file=sys.stderr)
        sys.exit(1)

    # Preserve markers on their own lines for clean diffs
    before = content[: start_idx + len(start)]
    after = content[end_idx:]
    updated = f"{before}\n{new_content}\n{after}"

    with open(path, "w") as f:
        f.write(updated)


# TODO(human): Implement metadata extraction
def _extract_rfd_metadata(rfd_file: Path) -> dict:
    """
    Extract metadata from an RFD file.

    Returns a dict with keys: number, title, status, date, author

    Args:
        rfd_file: Path to the RFD markdown file

    Returns:
        dict with 'number', 'title', 'status', 'date', 'author' keys
    """
    # TODO(human): Read the file and extract:
    # - number: from filename (e.g., "0001" from "0001-foo.md")
    # - title: from first # heading, strip "RFD XXXX: " prefix if present
    # - status, date, author: from HTML comment block after heading
    #   Format: <!-- Status: Draft\nDate: 2025-10-05\nAuthor: user -->
    #   Default to "Draft", "Unknown", "Unknown" respectively if not found
    number_from_path = rfd_file.stem.split("-")[0]

    text = rfd_file.read_text()

    match = TITLE_RE.search(text)
    if not match:
        raise ValueError(f"❌ Error: No RFD title found in {rfd_file}")
    number_from_title = match.group("number")
    title = match.group("title").strip()
    if number_from_path != number_from_title:
        raise ValueError(
            f"❌ Error: Mismatch in {rfd_file}: filename has {number_from_path}, "
            f"title has {number_from_title}"
        )

    match = META_RE.search(text)
    if not match:
        raise ValueError(f"❌ Error: No RFD-META found in {rfd_file}")
    status = match.group("status")
    date = match.group("date")
    author = match.group("author")

    return dict(
        number=number_from_title, title=title, status=status, date=date, author=author
    )


def create_new_rfd(title: str) -> None:
    number = _next_rfd_number()
    number_str = f"{number:04d}"
    slug = _slugify(title)
    filename = f"{number_str}-{slug}.md"
    output_path = RFDS_DIR / filename

    if output_path.exists():
        print(f"❌ Error: {output_path} already exists", file=sys.stderr)
        sys.exit(1)

    if not TEMPLATE_FILE.exists():
        print(f"❌ Error: Template not found at {TEMPLATE_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_FILE, "r") as f:
        template = f.read()

    # Pull from environment to match git commit author
    author = os.environ.get("USER", "unknown")
    today = date.today().isoformat()

    mapping = {
        "NUMBER": number_str,
        "TITLE": title,
        "DATE": today,
        "AUTHOR": author,
    }

    content = _replace_placeholders(template, mapping)

    with open(output_path, "w") as f:
        f.write(content)

    print(f" Created {output_path}")


def update_index() -> None:
    # Exclude template file from RFD list
    rfd_files = sorted(
        [f for f in RFDS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md")], key=lambda x: x.name
    )

    if not rfd_files:
        print("�  No RFD files found", file=sys.stderr)
        return

    rows = []
    for rfd_file in rfd_files:
        metadata = _extract_rfd_metadata(rfd_file)
        rel_path = f"rfds/{rfd_file.name}"
        row = f"| [{metadata['number']}]({rel_path}) | {metadata['title']} | {metadata['status']} | {metadata['date']} |"
        rows.append(row)

    table_header = "| RFD | Title | Status | Date |\n|-----|-------|---------|------|"
    table_content = table_header + "\n" + "\n".join(rows)

    _update_file_section(
        README_FILE, INDEX_START_MARKER, INDEX_END_MARKER, table_content
    )

    print(f" Updated RFD index in {README_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="RFD (Request for Discussion) management tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    new_parser = subparsers.add_parser("new", help="Create a new RFD")
    new_parser.add_argument("title", help="Title of the new RFD")

    subparsers.add_parser("index", help="Update the RFD index in README.md")

    args = parser.parse_args()

    if args.command == "new":
        create_new_rfd(args.title)
    elif args.command == "index":
        update_index()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
